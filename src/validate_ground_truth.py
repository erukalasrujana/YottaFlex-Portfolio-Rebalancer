
import pandas as pd
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent

GROUND_TRUTH = BASE_DIR / "data/ground_truth/edge_case_ground_truth.csv"
RECOMMENDATIONS = BASE_DIR / "outputs/reports/edge_case_recommendations.csv"
TRADE_REPORT = BASE_DIR / "outputs/reports/trade_validation_report.csv"

OUTPUT_DIR = BASE_DIR / "outputs/reports"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


def validate_ground_truth():

    print("Loading ground truth and actual results...")

    truth = pd.read_csv(GROUND_TRUTH)
    recommendations = pd.read_csv(RECOMMENDATIONS)
    trades = pd.read_csv(TRADE_REPORT)

    results = []

    for _, test in truth.iterrows():

        case_id = test["test_case_id"]
        case_name = test["edge_case"]
        record = test["affected_record"]
        expected = test["expected_result"]
        expected_reason = test["expected_reason"]

        actual = "NOT_DETECTED"
        details = ""

        # EC001: Invalid target allocation
        if case_id == "EC001":

            rows = recommendations[
                recommendations["portfolio_id"] == record
            ]

            detected = rows[
                (rows["status"] == "NEEDS_REVIEW")
                & rows["reason"].str.contains(
                    "Target weights total", case=False, na=False
                )
            ]

            if len(detected) > 0:
                actual = "NEEDS_REVIEW"
                details = detected.iloc[0]["reason"]

        # EC002: Excessive sell quantity
        elif case_id == "EC002":

            rows = trades[trades["trade_id"] == record]

            if len(rows) > 0:
                failed = rows[
                    (rows["validation_status"] == "FAIL")
                    & rows["validation_errors"].str.contains(
                        "Sell quantity", case=False, na=False
                    )
                ]

                if len(failed) > 0:
                    actual = "FAIL"
                    details = failed.iloc[0]["validation_errors"]

        # EC003: Excluded instrument
        elif case_id == "EC003":

            rows = recommendations[
                recommendations["instrument_id"] == record
            ]

            detected = rows[
                (rows["status"] == "BLOCKED")
                & rows["reason"].str.contains(
                    "excluded", case=False, na=False
                )
            ]

            if len(detected) > 0:
                actual = "BLOCKED"
                details = detected.iloc[0]["reason"]

        # EC004: Missing transaction fee
        elif case_id == "EC004":

            rows = trades[trades["trade_id"] == record]

            if len(rows) > 0:
                failed = rows[
                    (rows["validation_status"] == "FAIL")
                    & rows["validation_errors"].str.contains(
                        "Missing transaction fee",
                        case=False,
                        na=False
                    )
                ]

                if len(failed) > 0:
                    actual = "FAIL"
                    details = failed.iloc[0]["validation_errors"]

        # EC005: Stale market price
        elif case_id == "EC005":

            rows = recommendations[
                recommendations["instrument_id"] == record
            ]

            detected = rows[
                (rows["status"] == "BLOCKED")
                & rows["reason"].str.contains(
                    "more than 7 days old",
                    case=False,
                    na=False
                )
            ]

            if len(detected) > 0:
                actual = "BLOCKED"
                details = detected.iloc[0]["reason"]

        result = "PASS" if actual == expected else "FAIL"

        results.append({
            "test_case_id": case_id,
            "edge_case": case_name,
            "expected_result": expected,
            "actual_result": actual,
            "validation": result,
            "details": details
        })

    report = pd.DataFrame(results)

    report.to_csv(
        OUTPUT_DIR / "ground_truth_comparison.csv",
        index=False
    )

    print("\nGROUND TRUTH COMPARISON")
    print("-----------------------")
    print(report.to_string(index=False))

    passed = (report["validation"] == "PASS").sum()
    failed = (report["validation"] == "FAIL").sum()

    print("\nTotal test cases:", len(report))
    print("Passed:", passed)
    print("Failed:", failed)

    if failed == 0:
        print("\nAll ground-truth comparisons passed!")
    else:
        print("\nSome ground-truth comparisons failed. Review the report.")

    print("\nReport saved to outputs/reports/ground_truth_comparison.csv")


if __name__ == "__main__":
    validate_ground_truth()
