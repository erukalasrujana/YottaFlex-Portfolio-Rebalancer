
from pathlib import Path
import pandas as pd

BASE_DIR = Path(__file__).resolve().parent.parent
REPORT_DIR = BASE_DIR / "outputs" / "reports"

allocations = pd.read_csv(
    REPORT_DIR / "post_trade_allocations.csv"
)

summary = pd.read_csv(
    REPORT_DIR / "portfolio_summary.csv"
)

checks = []

def add_check(name, failed_records):
    checks.append({
        "check": name,
        "failed_records": int(failed_records),
        "result": "PASS" if failed_records == 0 else "FAIL"
    })

print("Validating post-trade calculations...")

# 1. Duplicate allocation records
duplicates = allocations.duplicated(
    subset=["portfolio_id", "instrument_id"]
).sum()

add_check("No duplicate portfolio-instrument rows", duplicates)

# 2. Missing values
required_columns = [
    "portfolio_id",
    "instrument_id",
    "post_trade_value",
    "post_trade_weight_pct"
]

missing = allocations[required_columns].isna().any(axis=1).sum()

add_check("No missing allocation values", missing)

# 3. No negative instrument values
negative_values = (
    allocations["post_trade_value"] < -0.01
).sum()

add_check("No negative post-trade instrument values", negative_values)

# 4. Post-trade weights are mathematically correct
merged = allocations.merge(
    summary[["portfolio_id", "post_trade_portfolio_value"]],
    on="portfolio_id",
    how="left"
)

expected_weights = (
    merged["post_trade_value"]
    / merged["post_trade_portfolio_value"]
    * 100
)

weight_errors = (
    merged["post_trade_weight_pct"] - expected_weights
).abs().gt(0.05).sum()

add_check("Post-trade instrument weights are correct", weight_errors)

# 5. Instrument values reconcile with post-trade holdings value
instrument_totals = allocations.groupby(
    "portfolio_id"
)["post_trade_value"].sum()

reconciliation = summary.set_index("portfolio_id").copy()

reconciliation["calculated_holdings_value"] = instrument_totals

holdings_errors = (
    reconciliation["calculated_holdings_value"]
    - reconciliation["post_trade_holdings_value"]
).abs().gt(0.05).sum()

add_check(
    "Instrument values reconcile with post-trade holdings",
    holdings_errors
)

# 6. Holdings plus cash reconcile with total portfolio value
calculated_total = (
    summary["post_trade_holdings_value"]
    + summary["cash_after"]
)

portfolio_errors = (
    calculated_total - summary["post_trade_portfolio_value"]
).abs().gt(0.05).sum()

add_check(
    "Holdings plus cash reconcile with portfolio value",
    portfolio_errors
)

# 7. Minimum cash reserve is maintained
reserve_errors = (
    summary["cash_after"] + 0.01
    < summary["required_cash_reserve"]
).sum()

add_check(
    "Minimum cash reserve is maintained",
    reserve_errors
)

# 8. No negative allocation percentages
negative_weights = (
    allocations["post_trade_weight_pct"] < -0.01
).sum()

add_check(
    "No negative allocation percentages",
    negative_weights
)

# 9. Every portfolio has allocation records
allocation_portfolios = set(allocations["portfolio_id"])
summary_portfolios = set(summary["portfolio_id"])

missing_portfolios = len(
    summary_portfolios - allocation_portfolios
)

add_check(
    "Every portfolio has allocation records",
    missing_portfolios
)

# Display results
results = pd.DataFrame(checks)

print("\nPOST-TRADE VALIDATION RESULTS")
print("=" * 65)
print(results.to_string(index=False))

print("\nTotal checks:", len(results))
print("Passed checks:", (results["result"] == "PASS").sum())
print("Failed checks:", (results["result"] == "FAIL").sum())

results.to_csv(
    REPORT_DIR / "post_trade_validation_report.csv",
    index=False
)

if (results["result"] == "PASS").all():
    print("\nAll post-trade validation checks passed!")
else:
    print("\nSome actual validation checks failed. Investigation required.")

print("\nValidation report saved in outputs/reports/.")
