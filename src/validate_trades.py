
import pandas as pd
from pathlib import Path

# Project paths
BASE_DIR = Path(__file__).resolve().parent.parent

TRADES_FILE = BASE_DIR / "data/processed/edge_trades.csv"
HOLDINGS_FILE = BASE_DIR / "data/raw/holdings.csv"
FEES_FILE = BASE_DIR / "data/raw/fee_schedules.csv"

OUTPUT_DIR = BASE_DIR / "outputs/reports"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


def validate_trades():

    print("Loading trade validation datasets...")

    trades = pd.read_csv(TRADES_FILE)
    holdings = pd.read_csv(HOLDINGS_FILE)
    fees = pd.read_csv(FEES_FILE)

    # Normalize text columns
    trades["trade_side"] = (
        trades["trade_side"].fillna(trades["side"]).astype(str).str.upper()
    )

    trades["trade_status"] = (
        trades["trade_status"].astype(str).str.lower()
    )

    # Aggregate available holdings
    holding_lookup = (
        holdings.groupby(["portfolio_id", "instrument_id"])["quantity"]
        .sum()
        .to_dict()
    )

    fee_lookup = fees.set_index("fee_schedule_id").to_dict("index")

    results = []

    for _, trade in trades.iterrows():

        errors = []

        trade_id = trade["trade_id"]
        portfolio_id = trade["portfolio_id"]
        instrument_id = trade["instrument_id"]
        quantity = trade["quantity"]
        side = trade["trade_side"]
        trade_value = trade["trade_value"]
        fee_amount = trade["fee_amount"]
        fee_schedule_id = trade["fee_schedule_id"]

        is_executed = trade["trade_status"] == "executed"

        # 1. Validate quantity
        if pd.isna(quantity) or quantity <= 0:
            errors.append("Invalid trade quantity.")

        # 2. Validate execution price
        if pd.isna(trade["execution_price"]) or trade["execution_price"] <= 0:
            errors.append("Invalid execution price.")

        # 3. Validate trade value
        if (
            pd.isna(trade_value)
            or pd.isna(quantity)
            or pd.isna(trade["execution_price"])
            or abs(
                trade_value - quantity * trade["execution_price"]
            ) > 0.02
        ):
            errors.append("Trade value does not match quantity and price.")

        # 4. Validate SELL quantity against holdings
        if is_executed and side == "SELL" and not pd.isna(quantity):

            available = holding_lookup.get(
                (portfolio_id, instrument_id), 0
            )

            if quantity > available:
                errors.append(
                    f"Sell quantity {quantity} exceeds available "
                    f"holding {available}."
                )

        # 5. Validate fee presence
        if is_executed and pd.isna(fee_amount):
            errors.append("Missing transaction fee.")

        # 6. Validate fee schedule and fee calculation
        if is_executed and not pd.isna(fee_amount):

            if fee_schedule_id not in fee_lookup:
                errors.append("Invalid fee schedule reference.")

            elif not pd.isna(trade_value):

                schedule = fee_lookup[fee_schedule_id]

                expected_fee = (
                    schedule["fixed_fee"]
                    + trade_value * schedule["commission_rate_pct"] / 100
                )

                expected_fee = max(
                    schedule["minimum_fee"],
                    min(expected_fee, schedule["maximum_fee"])
                )

                if abs(fee_amount - expected_fee) > 0.02:
                    errors.append("Transaction fee does not match fee schedule.")

        # Store validation result
        results.append({
            "trade_id": trade_id,
            "portfolio_id": portfolio_id,
            "instrument_id": instrument_id,
            "trade_side": side,
            "quantity": quantity,
            "fee_amount": fee_amount,
            "validation_status": "FAIL" if errors else "PASS",
            "validation_errors": " | ".join(errors)
        })

    # Create report
    report = pd.DataFrame(results)

    report_path = OUTPUT_DIR / "trade_validation_report.csv"
    report.to_csv(report_path, index=False)

    # Summary
    passed = (report["validation_status"] == "PASS").sum()
    failed = (report["validation_status"] == "FAIL").sum()

    print("\nTRADE VALIDATION RESULTS")
    print("------------------------")
    print("Total trades:", len(report))
    print("Passed trades:", passed)
    print("Failed trades:", failed)

    print("\nFailed trade records:")
    print(
        report[report["validation_status"] == "FAIL"]
        .to_string(index=False)
    )

    print("\nValidation report saved to:")
    print(report_path)


if __name__ == "__main__":
    validate_trades()
