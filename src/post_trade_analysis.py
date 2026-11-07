
from pathlib import Path
import pandas as pd


BASE_DIR = Path(__file__).resolve().parent.parent
RAW_DIR = BASE_DIR / "data" / "raw"
REPORT_DIR = BASE_DIR / "outputs" / "reports"

REPORT_DIR.mkdir(parents=True, exist_ok=True)


def main():
    print("Loading portfolio and recommendation data...")

    portfolios = pd.read_csv(RAW_DIR / "portfolios.csv")
    holdings = pd.read_csv(RAW_DIR / "holdings.csv")
    instruments = pd.read_csv(RAW_DIR / "instruments.csv")
    prices = pd.read_csv(RAW_DIR / "market_prices.csv")
    targets = pd.read_csv(RAW_DIR / "target_allocations.csv")
    constraints = pd.read_csv(RAW_DIR / "constraints.csv")
    recommendations = pd.read_csv(
        REPORT_DIR / "rebalance_recommendations.csv"
    )

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

    constraint_lookup = constraints.set_index(
        "portfolio_id"
    ).to_dict("index")

    print("Datasets loaded successfully.")
    print("Calculating post-trade allocations...")

    allocation_results = []
    summary_results = []

    for _, portfolio in portfolios.iterrows():

        portfolio_id = portfolio["portfolio_id"]

        if portfolio["portfolio_status"] != "Active":
            continue

        cash_before = float(portfolio["total_cash"])

        portfolio_holdings = holdings[
            holdings["portfolio_id"] == portfolio_id
        ]

        portfolio_targets = targets[
            targets["portfolio_id"] == portfolio_id
        ]

        portfolio_trades = recommendations[
            (recommendations["portfolio_id"] == portfolio_id)
            & (recommendations["status"] == "RECOMMENDED")
        ]

        constraint = constraint_lookup[portfolio_id]

        reserve_pct = float(
            constraint["minimum_cash_reserve_pct"]
        )

        current_values = {}
        post_trade_values = {}

        total_current_holdings_value = 0.0

        # Calculate current and post-trade holding quantities.
        instrument_ids = set(
            portfolio_holdings["instrument_id"].tolist()
        )

        instrument_ids.update(
            portfolio_targets["instrument_id"].tolist()
        )

        for instrument_id in instrument_ids:

            matching_holding = portfolio_holdings[
                portfolio_holdings["instrument_id"]
                == instrument_id
            ]

            current_quantity = (
                float(matching_holding["quantity"].sum())
                if not matching_holding.empty
                else 0.0
            )

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

            current_value = current_quantity * price

            total_current_holdings_value += current_value

            matching_trades = portfolio_trades[
                portfolio_trades["instrument_id"]
                == instrument_id
            ]

            buy_quantity = matching_trades[
                matching_trades["action"] == "BUY"
            ]["quantity"].sum()

            sell_quantity = matching_trades[
                matching_trades["action"] == "SELL"
            ]["quantity"].sum()

            post_quantity = (
                current_quantity
                + float(buy_quantity)
                - float(sell_quantity)
            )

            post_value = post_quantity * price

            current_values[instrument_id] = current_value
            post_trade_values[instrument_id] = post_value

        # Calculate trade cash flows.
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

        total_fees = portfolio_trades[
            "estimated_fee"
        ].sum()

        cash_after = cash_before + sell_proceeds - buy_cost

        post_holdings_value = sum(
            post_trade_values.values()
        )

        post_portfolio_value = (
            post_holdings_value + cash_after
        )

        required_cash_reserve = (
            post_portfolio_value * reserve_pct / 100
        )

        cash_reserve_pass = (
            cash_after >= required_cash_reserve - 0.02
        )

        investable_value = (
            post_portfolio_value - required_cash_reserve
        )

        # Save allocation details for each instrument.
        for instrument_id in instrument_ids:

            matching_target = portfolio_targets[
                portfolio_targets["instrument_id"]
                == instrument_id
            ]

            target_weight = (
                float(matching_target.iloc[0]["target_weight_pct"])
                if not matching_target.empty
                else 0.0
            )

            current_value = current_values[instrument_id]
            post_value = post_trade_values[instrument_id]

            current_weight = (
                current_value / (total_current_holdings_value + cash_before) * 100
                if total_current_holdings_value + cash_before > 0
                else 0.0
            )

            post_weight = (
                post_value / post_portfolio_value * 100
                if post_portfolio_value > 0
                else 0.0
            )

            target_value = (
                investable_value * target_weight / 100
            )

            target_total_weight = (
                target_value / post_portfolio_value * 100
                if post_portfolio_value > 0
                else 0.0
            )

            allocation_results.append({
                "portfolio_id": portfolio_id,
                "instrument_id": instrument_id,
                "current_value": round(current_value, 2),
                "current_weight_pct": round(current_weight, 2),
                "target_weight_pct": round(target_weight, 2),
                "target_value": round(target_value, 2),
                "post_trade_value": round(post_value, 2),
                "post_trade_weight_pct": round(post_weight, 2),
                "target_weight_of_total_pct": round(
                    target_total_weight, 2
                ),
                "allocation_drift_pct": round(
                    post_weight - target_total_weight, 2
                )
            })

        summary_results.append({
            "portfolio_id": portfolio_id,
            "current_portfolio_value": round(
                total_current_holdings_value + cash_before, 2
            ),
            "post_trade_holdings_value": round(
                post_holdings_value, 2
            ),
            "cash_before": round(cash_before, 2),
            "cash_after": round(cash_after, 2),
            "required_cash_reserve": round(
                required_cash_reserve, 2
            ),
            "total_estimated_fees": round(total_fees, 2),
            "buy_count": int(
                (portfolio_trades["action"] == "BUY").sum()
            ),
            "sell_count": int(
                (portfolio_trades["action"] == "SELL").sum()
            ),
            "post_trade_portfolio_value": round(
                post_portfolio_value, 2
            ),
            "cash_reserve_status": (
                "PASS" if cash_reserve_pass else "FAIL"
            )
        })

    allocation_report = pd.DataFrame(allocation_results)
    summary_report = pd.DataFrame(summary_results)

    allocation_report.to_csv(
        REPORT_DIR / "post_trade_allocations.csv",
        index=False
    )

    summary_report.to_csv(
        REPORT_DIR / "portfolio_summary.csv",
        index=False
    )

    print("\nPOST-TRADE ANALYSIS COMPLETED")
    print("=" * 45)

    print("Portfolios analysed:", len(summary_report))
    print("Allocation rows:", len(allocation_report))

    print("\nCash reserve status:")
    print(
        summary_report["cash_reserve_status"].value_counts()
    )

    print("\nTotal estimated fees across portfolios:")
    print(
        round(summary_report["total_estimated_fees"].sum(), 2)
    )

    print("\nReports saved:")
    print("outputs/reports/post_trade_allocations.csv")
    print("outputs/reports/portfolio_summary.csv")


if __name__ == "__main__":
    main()
