
from pathlib import Path
import math
import pandas as pd


BASE_DIR = Path(__file__).resolve().parent.parent
RAW_DIR = BASE_DIR / "data" / "raw"
PROCESSED_DIR = BASE_DIR / "data" / "processed"
OUTPUT_DIR = BASE_DIR / "outputs" / "reports"

OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


def calculate_fee(trade_value, fee_schedule):
    commission = (
        trade_value
        * float(fee_schedule["commission_rate_pct"])
        / 100
    )

    fee = commission + float(fee_schedule["fixed_fee"])
    fee = max(fee, float(fee_schedule["minimum_fee"]))
    fee = min(fee, float(fee_schedule["maximum_fee"]))

    return round(fee, 2)


def load_datasets(use_edge_cases=False):

    if use_edge_cases:
        data_dir = PROCESSED_DIR

        print("Loading edge-case datasets...")

        portfolios = pd.read_csv(RAW_DIR / "portfolios.csv")
        holdings = pd.read_csv(data_dir / "edge_holdings.csv")
        instruments = pd.read_csv(data_dir / "edge_instruments.csv")
        prices = pd.read_csv(data_dir / "edge_market_prices.csv")
        targets = pd.read_csv(data_dir / "edge_target_allocations.csv")
        constraints = pd.read_csv(RAW_DIR / "constraints.csv")
        fees = pd.read_csv(RAW_DIR / "fee_schedules.csv")

    else:
        print("Loading baseline datasets...")

        portfolios = pd.read_csv(RAW_DIR / "portfolios.csv")
        holdings = pd.read_csv(RAW_DIR / "holdings.csv")
        instruments = pd.read_csv(RAW_DIR / "instruments.csv")
        prices = pd.read_csv(RAW_DIR / "market_prices.csv")
        targets = pd.read_csv(RAW_DIR / "target_allocations.csv")
        constraints = pd.read_csv(RAW_DIR / "constraints.csv")
        fees = pd.read_csv(RAW_DIR / "fee_schedules.csv")

    return (
        portfolios,
        holdings,
        instruments,
        prices,
        targets,
        constraints,
        fees
    )


def generate_recommendations(use_edge_cases=False):

    (
        portfolios,
        holdings,
        instruments,
        prices,
        targets,
        constraints,
        fees
    ) = load_datasets(use_edge_cases)

    print("Datasets loaded successfully.")

    prices["price_date"] = pd.to_datetime(prices["price_date"])

    latest_prices = (
        prices.sort_values("price_date")
        .groupby("instrument_id")
        .tail(1)
    )

    latest_market_date = prices["price_date"].max()

    price_lookup = latest_prices.set_index(
        "instrument_id"
    ).to_dict("index")

    instrument_lookup = instruments.set_index(
        "instrument_id"
    ).to_dict("index")

    fee_lookup = fees.set_index(
        "instrument_type"
    ).to_dict("index")

    constraint_lookup = constraints.set_index(
        "portfolio_id"
    ).to_dict("index")

    holding_lookup = {
        key: group
        for key, group in holdings.groupby("portfolio_id")
    }

    target_lookup = {
        key: group
        for key, group in targets.groupby("portfolio_id")
    }

    portfolio_lookup = portfolios.set_index(
        "portfolio_id"
    ).to_dict("index")

    recommendations = []

    print("Calculating portfolio allocations...")

    for portfolio_id, portfolio in portfolio_lookup.items():

        if portfolio["portfolio_status"] != "Active":
            continue

        portfolio_targets = target_lookup.get(portfolio_id)

        if portfolio_targets is None:
            continue

        portfolio_holdings = holding_lookup.get(
            portfolio_id,
            pd.DataFrame()
        )

        constraint = constraint_lookup.get(portfolio_id)

        if constraint is None:
            continue

        cash = float(portfolio["total_cash"])

        reserve_pct = float(
            constraint["minimum_cash_reserve_pct"]
        )

        max_position_pct = float(
            constraint["max_position_weight_pct"]
        )

        max_trade_pct = float(
            constraint["max_trade_value_pct"]
        )

        current_holdings_value = 0.0

        for _, holding in portfolio_holdings.iterrows():

            instrument_id = holding["instrument_id"]
            price_data = price_lookup.get(instrument_id)

            if price_data is not None:
                current_price = float(
                    price_data["market_price"]
                )
            else:
                instrument = instrument_lookup.get(instrument_id)

                if instrument is None:
                    continue

                current_price = float(
                    instrument["current_price"]
                )

            current_holdings_value += (
                float(holding["quantity"]) * current_price
            )

        portfolio_value = current_holdings_value + cash

        if portfolio_value <= 0:
            continue

        reserve_cash = portfolio_value * reserve_pct / 100
        investable_value = portfolio_value - reserve_cash
        max_trade_value = portfolio_value * max_trade_pct / 100

        target_total = portfolio_targets[
            "target_weight_pct"
        ].sum()

        # Edge case 1: Target allocation does not equal 100%.
        if abs(target_total - 100.0) > 0.01:

            for _, target in portfolio_targets.iterrows():

                recommendations.append({
                    "portfolio_id": portfolio_id,
                    "instrument_id": target["instrument_id"],
                    "action": "NONE",
                    "quantity": 0,
                    "trade_value": 0,
                    "estimated_fee": 0,
                    "status": "NEEDS_REVIEW",
                    "reason": (
                        f"Target weights total {target_total:.2f}%, "
                        "not 100%."
                    )
                })

            continue

        candidates = []

        for _, target in portfolio_targets.iterrows():

            instrument_id = target["instrument_id"]
            target_weight = float(target["target_weight_pct"])

            instrument = instrument_lookup.get(instrument_id)
            price_data = price_lookup.get(instrument_id)

            if instrument is None or price_data is None:

                candidates.append({
                    "portfolio_id": portfolio_id,
                    "instrument_id": instrument_id,
                    "action": "NONE",
                    "quantity": 0,
                    "trade_value": 0,
                    "estimated_fee": 0,
                    "status": "BLOCKED",
                    "reason": "Instrument or market price is missing."
                })

                continue

            price = float(price_data["market_price"])

            if price <= 0:

                candidates.append({
                    "portfolio_id": portfolio_id,
                    "instrument_id": instrument_id,
                    "action": "NONE",
                    "quantity": 0,
                    "trade_value": 0,
                    "estimated_fee": 0,
                    "status": "BLOCKED",
                    "reason": "Invalid market price."
                })

                continue

            holding_match = portfolio_holdings[
                portfolio_holdings["instrument_id"] == instrument_id
            ]

            current_quantity = (
                float(holding_match.iloc[0]["quantity"])
                if not holding_match.empty
                else 0.0
            )

            current_value = current_quantity * price

            desired_value = (
                investable_value * target_weight / 100
            )

            difference = desired_value - current_value

            target_position_pct = (
                desired_value / portfolio_value * 100
            )

            reason = None

            if bool(instrument["is_excluded"]):
                reason = "Instrument is excluded by policy."

            elif not bool(instrument["is_tradable"]):
                reason = "Instrument is not tradable."

            elif bool(price_data["is_stale"]):
                reason = "Market price is flagged as stale."

            elif (
                latest_market_date - price_data["price_date"]
            ).days > 7:
                reason = "Market price is more than 7 days old."

            elif target_position_pct > max_position_pct:
                reason = (
                    "Target position exceeds maximum position weight."
                )

            if reason:

                candidates.append({
                    "portfolio_id": portfolio_id,
                    "instrument_id": instrument_id,
                    "action": "NONE",
                    "quantity": 0,
                    "trade_value": 0,
                    "estimated_fee": 0,
                    "status": "BLOCKED",
                    "reason": reason
                })

                continue

            instrument_type = instrument["instrument_type"]

            if instrument_type not in fee_lookup:

                candidates.append({
                    "portfolio_id": portfolio_id,
                    "instrument_id": instrument_id,
                    "action": "NONE",
                    "quantity": 0,
                    "trade_value": 0,
                    "estimated_fee": 0,
                    "status": "BLOCKED",
                    "reason": "Fee schedule is missing."
                })

                continue

            if abs(difference) < price:

                candidates.append({
                    "portfolio_id": portfolio_id,
                    "instrument_id": instrument_id,
                    "action": "HOLD",
                    "quantity": 0,
                    "trade_value": 0,
                    "estimated_fee": 0,
                    "status": "NO_TRADE",
                    "reason": "Allocation difference is less than one unit."
                })

                continue

            action = "BUY" if difference > 0 else "SELL"

            requested_quantity = math.floor(
                abs(difference) / price
            )

            trade_quantity_limit = math.floor(
                max_trade_value / price
            )

            quantity = min(
                requested_quantity,
                trade_quantity_limit
            )

            # Never recommend selling more than available holdings.
            if action == "SELL":
                quantity = min(
                    quantity,
                    math.floor(current_quantity)
                )

            if quantity <= 0:

                candidates.append({
                    "portfolio_id": portfolio_id,
                    "instrument_id": instrument_id,
                    "action": action,
                    "quantity": 0,
                    "trade_value": 0,
                    "estimated_fee": 0,
                    "status": "BLOCKED",
                    "reason": "Trade limits prevent a valid order."
                })

                continue

            trade_value = quantity * price

            fee = calculate_fee(
                trade_value,
                fee_lookup[instrument_type]
            )

            candidates.append({
                "portfolio_id": portfolio_id,
                "instrument_id": instrument_id,
                "action": action,
                "quantity": quantity,
                "trade_value": round(trade_value, 2),
                "estimated_fee": fee,
                "status": "RECOMMENDED",
                "reason": (
                    f"Current value: ${current_value:.2f}; "
                    f"target value: ${desired_value:.2f}."
                ),
                "price": price,
                "current_quantity": current_quantity
            })

        # Process sells before buys.
        sell_candidates = [
            item for item in candidates
            if item["action"] == "SELL"
            and item["status"] == "RECOMMENDED"
        ]

        buy_candidates = [
            item for item in candidates
            if item["action"] == "BUY"
            and item["status"] == "RECOMMENDED"
        ]

        sell_proceeds = sum(
            item["trade_value"] - item["estimated_fee"]
            for item in sell_candidates
        )

        available_buy_cash = max(
            0,
            cash - reserve_cash + sell_proceeds
        )

        # Limit buys to available cash.
        for item in buy_candidates:

            instrument = instrument_lookup[
                item["instrument_id"]
            ]

            schedule = fee_lookup[
                instrument["instrument_type"]
            ]

            quantity = item["quantity"]
            price = item["price"]

            while quantity > 0:

                trade_value = quantity * price

                fee = calculate_fee(
                    trade_value,
                    schedule
                )

                if trade_value + fee <= available_buy_cash:
                    break

                quantity -= 1

            if quantity <= 0:

                item["quantity"] = 0
                item["trade_value"] = 0
                item["estimated_fee"] = 0
                item["status"] = "BLOCKED"

                item["reason"] = (
                    "Insufficient cash after maintaining "
                    "the minimum cash reserve."
                )

            else:

                trade_value = quantity * price

                fee = calculate_fee(
                    trade_value,
                    schedule
                )

                available_buy_cash -= trade_value + fee

                item["quantity"] = quantity
                item["trade_value"] = round(trade_value, 2)
                item["estimated_fee"] = fee

                item["reason"] += (
                    " Purchase fits within available cash."
                )

        for item in candidates:

            item.pop("price", None)
            item.pop("current_quantity", None)

            recommendations.append(item)

    result = pd.DataFrame(recommendations)

    output_filename = (
        "edge_case_recommendations.csv"
        if use_edge_cases
        else "rebalance_recommendations.csv"
    )

    output_file = OUTPUT_DIR / output_filename

    result.to_csv(output_file, index=False)

    print("\nRecommendation engine completed.")
    print("Total recommendations:", len(result))

    if not result.empty:

        print("\nRecommendation status:")
        print(result["status"].value_counts())

        print("\nBUY and SELL summary:")
        print(result["action"].value_counts())

    print("\nSaved results to:")
    print(output_file)


if __name__ == "__main__":

    import sys

    use_edge_cases = (
        len(sys.argv) > 1
        and sys.argv[1].lower() == "edge"
    )

    generate_recommendations(
        use_edge_cases=use_edge_cases
    )
