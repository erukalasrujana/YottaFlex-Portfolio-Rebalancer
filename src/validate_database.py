
from pathlib import Path
import sqlite3

PROJECT_ROOT = Path(__file__).resolve().parent.parent
DB_PATH = PROJECT_ROOT / "database" / "portfolio.db"

EXPECTED_COUNTS = {
    "investors": 1000,
    "portfolios": 1000,
    "instruments": 5000,
    "holdings": 5000,
    "market_prices": 1250000,
    "target_allocations": 5000,
    "fee_schedules": 4,
    "constraints": 1000,
    "trades": 1000,
    "rebalance_proposals": 1000,
}


def main():
    if not DB_PATH.exists():
        raise FileNotFoundError("Database not found. Run database.seed_data first.")

    connection = sqlite3.connect(DB_PATH)
    checks = []

    try:
        print("DATABASE QUALITY VALIDATION")
        print("=" * 45)

        # Check expected table record counts
        for table, expected in EXPECTED_COUNTS.items():
            actual = connection.execute(
                f"SELECT COUNT(*) FROM {table}"
            ).fetchone()[0]

            passed = actual == expected
            checks.append(passed)

            print(
                f"{'PASS' if passed else 'FAIL'}: "
                f"{table} record count = {actual:,}"
            )

        # Check foreign-key integrity
        fk_errors = connection.execute(
            "PRAGMA foreign_key_check"
        ).fetchall()

        passed = len(fk_errors) == 0
        checks.append(passed)

        print(
            f"{'PASS' if passed else 'FAIL'}: "
            "Foreign-key integrity"
        )

        # Check target allocations total 100% per portfolio
        invalid_targets = connection.execute("""
            SELECT portfolio_id, SUM(target_weight_pct)
            FROM target_allocations
            GROUP BY portfolio_id
            HAVING ABS(SUM(target_weight_pct) - 100) > 0.01
        """).fetchall()

        passed = len(invalid_targets) == 0
        checks.append(passed)

        print(
            f"{'PASS' if passed else 'FAIL'}: "
            f"Target allocations total 100% "
            f"({len(invalid_targets)} invalid portfolios)"
        )

        # Check five holdings per portfolio
        invalid_holdings = connection.execute("""
            SELECT portfolio_id
            FROM holdings
            GROUP BY portfolio_id
            HAVING COUNT(*) != 5
        """).fetchall()

        passed = len(invalid_holdings) == 0
        checks.append(passed)

        print(
            f"{'PASS' if passed else 'FAIL'}: "
            f"Five holdings per portfolio "
            f"({len(invalid_holdings)} invalid portfolios)"
        )

        # Check 250 price records per instrument
        invalid_prices = connection.execute("""
            SELECT instrument_id
            FROM market_prices
            GROUP BY instrument_id
            HAVING COUNT(*) != 250
        """).fetchall()

        passed = len(invalid_prices) == 0
        checks.append(passed)

        print(
            f"{'PASS' if passed else 'FAIL'}: "
            f"250 market-price records per instrument "
            f"({len(invalid_prices)} invalid instruments)"
        )

        print("\n" + "=" * 45)
        print(f"Total checks: {len(checks)}")
        print(f"Passed: {sum(checks)}")
        print(f"Failed: {len(checks) - sum(checks)}")

        if all(checks):
            print("\nAll database quality checks passed!")
        else:
            print("\nDatabase quality validation failed.")

    finally:
        connection.close()


if __name__ == "__main__":
    main()
