
from pathlib import Path
import pandas as pd

BASE_DIR = Path(__file__).resolve().parent.parent
RAW_DIR = BASE_DIR / "data" / "raw"
REPORT_DIR = BASE_DIR / "outputs" / "reports"


def calculate_fee(trade_value, schedule):
    commission = (
        trade_value * schedule["commission_rate_pct"] / 100
    )
    fee = commission + schedule["fixed_fee"]
    fee = max(fee, schedule["minimum_fee"])
    fee = min(fee, schedule["maximum_fee"])
    return round(fee, 2)


def main():
    print("Loading recommendation and baseline data...")

    recommendations = pd.read_csv(
        REPORT_DIR / "rebalance_recommendations.csv"
    )
    portfolios = pd.read_csv(RAW_DIR / "portfolios.csv")
    holdings = pd.read_csv(RAW_DIR / "holdings.csv")
    instruments = pd.read_csv(RAW_DIR / "instruments.csv")
    prices = pd.read_csv(RAW_DIR / "market_prices.csv")
    constraints = pd.read_csv(RAW_DIR / "constraints.csv")
    fees = pd.read_csv(RAW_DIR / "fee_schedules.csv")

    prices["price_date"] = pd.to_datetime(prices["price_date"])

    latest_prices = (
        prices.sort_values("price_date")
        .groupby("instrument_id")
        .tail(1)
        .set_index("instrument_id")
    )

    instrument_lookup = instruments.set_index(
        "instrument_id"
    ).to_dict("index")

    fee_lookup = fees.set_index(
        "instrument_type"
    ).to_dict("index")

    constraint_lookup = constraints.set_index(
        "portfolio_id"
    ).to_dict("index")

    portfolio_lookup = portfolios.set_index(
        "portfolio_id"
    ).to_dict("index")

    holding_lookup = {
        key: group
        for key, group in holdings.groupby("portfolio_id")
    }

    # Calculate each portfolio's total current value.
    portfolio_values = {}

    for portfolio_id, portfolio in portfolio_lookup.items():
        cash = float(portfolio["total_cash"])
        total_holdings_value = 0.0

        portfolio_holdings = holding_lookup.get(
            portfolio_id,
            pd.DataFrame()
        )

        for _, holding in portfolio_holdings.iterrows():
            instrument_id = holding["instrument_id"]

            if instrument_id in latest_prices.index:
                price = float(
                    latest_prices.loc[
                        instrument_id, "market_price"
                    ]
                )
            else:
                price = float(
                    instrument_lookup[instrument_id]["current_price"]
                )

            total_holdings_value += (
                float(holding["quantity"]) * price
            )

        portfolio_values[portfolio_id] = (
            total_holdings_value + cash
        )

    recommended = recommendations[
        recommendations["status"] == "RECOMMENDED"
    ].copy()

    checks = []

    def record_check(name, failed_count):
        passed = failed_count == 0
        checks.append({
            "check": name,
            "failed_records": int(failed_count),
            "result": "PASS" if passed else "FAIL"
        })

    # CHECK 1: Unique portfolio and instrument combinations.
    duplicates = recommendations.duplicated(
        ["portfolio_id", "instrument_id"]
    ).sum()

    record_check("No duplicate portfolio-instrument rows", duplicates)

    # CHECK 2: No missing recommendation fields.
    missing = recommendations.isna().sum().sum()

    record_check("No missing recommendation fields", missing)

    # CHECK 3: Recommended quantities must be positive.
    invalid_quantity = (
        (recommended["quantity"] <= 0).sum()
    )

    record_check("Recommended quantities are positive", invalid_quantity)

    # CHECK 4: Recommended trades must not exceed holdings.
    sell_violations = 0

    for _, trade in recommended[
        recommended["action"] == "SELL"
    ].iterrows():

        matching = holdings[
            (holdings["portfolio_id"] == trade["portfolio_id"])
            & (holdings["instrument_id"] == trade["instrument_id"])
        ]

        available = (
            matching["quantity"].sum()
            if not matching.empty
            else 0
        )

        if trade["quantity"] > available:
            sell_violations += 1

    record_check("SELL quantity does not exceed holdings", sell_violations)

    # CHECK 5: Trade value matches quantity multiplied by price.
    value_violations = 0

    for _, trade in recommended.iterrows():
        instrument_id = trade["instrument_id"]

        price = float(
            latest_prices.loc[
                instrument_id, "market_price"
            ]
        )

        expected_value = float(trade["quantity"]) * price

        if abs(expected_value - float(trade["trade_value"])) > 0.02:
            value_violations += 1

    record_check("Trade values match market prices", value_violations)

    # CHECK 6: Trades respect maximum trade value.
    trade_limit_violations = 0

    for _, trade in recommended.iterrows():
        portfolio_id = trade["portfolio_id"]

        max_trade_pct = float(
            constraint_lookup[portfolio_id]["max_trade_value_pct"]
        )

        max_trade_value = (
            portfolio_values[portfolio_id] * max_trade_pct / 100
        )

        if float(trade["trade_value"]) > max_trade_value + 0.02:
            trade_limit_violations += 1

    record_check("Trades respect maximum trade value", trade_limit_violations)

    # CHECK 7: Excluded and non-tradable instruments are not recommended.
    policy_violations = 0

    for _, trade in recommended.iterrows():
        instrument = instrument_lookup[trade["instrument_id"]]

        if bool(instrument["is_excluded"]) or not bool(instrument["is_tradable"]):
            policy_violations += 1

    record_check("No excluded or non-tradable instruments recommended", policy_violations)

    # CHECK 8: Stale prices are not recommended.
    stale_violations = 0

    for _, trade in recommended.iterrows():
        price_data = latest_prices.loc[trade["instrument_id"]]

        if bool(price_data["is_stale"]):
            stale_violations += 1

    record_check("No explicitly stale prices recommended", stale_violations)

    # CHECK 9: Fees match the applicable fee schedule.
    fee_violations = 0

    for _, trade in recommended.iterrows():
        instrument_type = instrument_lookup[
            trade["instrument_id"]
        ]["instrument_type"]

        schedule = fee_lookup[instrument_type]

        expected_fee = calculate_fee(
            float(trade["trade_value"]),
            schedule
        )

        if abs(expected_fee - float(trade["estimated_fee"])) > 0.02:
            fee_violations += 1

    record_check("Fees match fee schedules", fee_violations)

    # CHECK 10: Cash reserve is maintained after all proposed trades.
    reserve_violations = 0

    for portfolio_id, portfolio in portfolio_lookup.items():
        cash = float(portfolio["total_cash"])

        reserve_pct = float(
            constraint_lookup[portfolio_id]["minimum_cash_reserve_pct"]
        )

        reserve_amount = (
            portfolio_values[portfolio_id] * reserve_pct / 100
        )

        portfolio_trades = recommended[
            recommended["portfolio_id"] == portfolio_id
        ]

        sell_proceeds = portfolio_trades[
            portfolio_trades["action"] == "SELL"
        ].apply(
            lambda row: row["trade_value"] - row["estimated_fee"],
            axis=1
        ).sum()

        buy_cost = portfolio_trades[
            portfolio_trades["action"] == "BUY"
        ].apply(
            lambda row: row["trade_value"] + row["estimated_fee"],
            axis=1
        ).sum()

        ending_cash = cash + sell_proceeds - buy_cost

        if ending_cash < reserve_amount - 0.02:
            reserve_violations += 1

    record_check("Minimum cash reserve is maintained", reserve_violations)

    # Display validation results.
    results = pd.DataFrame(checks)

    print("\nRECOMMENDATION VALIDATION RESULTS")
    print("=" * 55)
    print(results.to_string(index=False))

    total_failed = results["failed_records"].sum()
    passed_checks = (results["result"] == "PASS").sum()

    print("\nTotal checks:", len(results))
    print("Passed checks:", passed_checks)
    print("Failed records:", int(total_failed))

    results.to_csv(
        REPORT_DIR / "recommendation_validation.csv",
        index=False
    )

    if total_failed == 0:
        print("\nAll recommendation validation checks passed!")
    else:
        print("\nSome checks failed. We need to investigate them.")

    print("\nValidation report saved in outputs/reports/.")


if __name__ == "__main__":
    main()
