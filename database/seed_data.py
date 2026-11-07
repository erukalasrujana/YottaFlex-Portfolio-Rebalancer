
from pathlib import Path
import sqlite3
import pandas as pd

# Project paths
PROJECT_ROOT = Path(__file__).resolve().parent.parent
RAW_DATA_DIR = PROJECT_ROOT / "data" / "raw"
DATABASE_DIR = PROJECT_ROOT / "database"

DB_PATH = DATABASE_DIR / "portfolio.db"
SCHEMA_PATH = DATABASE_DIR / "schema.sql"

# Load tables in foreign-key dependency order
TABLES = [
    "investors",
    "portfolios",
    "instruments",
    "fee_schedules",
    "holdings",
    "market_prices",
    "target_allocations",
    "constraints",
    "trades",
    "rebalance_proposals",
]


def main():
    print("Starting database creation...")

    if not SCHEMA_PATH.exists():
        raise FileNotFoundError(f"Schema file not found: {SCHEMA_PATH}")

    if not RAW_DATA_DIR.exists():
        raise FileNotFoundError(f"Raw data folder not found: {RAW_DATA_DIR}")

    # Rebuild the database from the original CSV files
    if DB_PATH.exists():
        DB_PATH.unlink()

    connection = sqlite3.connect(DB_PATH)

    try:
        connection.execute("PRAGMA foreign_keys = ON")

        # Create database tables
        schema = SCHEMA_PATH.read_text(encoding="utf-8")
        connection.executescript(schema)

        print("Database schema created.")

        total_records = 0

        # Insert CSV records into SQLite tables
        for table in TABLES:
            csv_path = RAW_DATA_DIR / f"{table}.csv"

            if not csv_path.exists():
                raise FileNotFoundError(f"Dataset not found: {csv_path}")

            print(f"Loading {table}...")

            df = pd.read_csv(csv_path)

            # Convert Boolean columns to SQLite-compatible integers
            for column in df.columns:
                if pd.api.types.is_bool_dtype(df[column]):
                    df[column] = df[column].astype(int)

            df.to_sql(
                table,
                connection,
                if_exists="append",
                index=False
            )

            row_count = len(df)
            total_records += row_count

            print(f"  Inserted {row_count:,} records.")

        # Verify record counts
        print("\nDATABASE VERIFICATION")
        print("-" * 40)

        for table in TABLES:
            count = connection.execute(
                f"SELECT COUNT(*) FROM {table}"
            ).fetchone()[0]

            print(f"{table}: {count:,} records")

        # Check foreign-key integrity
        foreign_key_errors = connection.execute(
            "PRAGMA foreign_key_check"
        ).fetchall()

        if foreign_key_errors:
            print("\nForeign-key validation FAILED:")
            for error in foreign_key_errors[:10]:
                print(error)
            raise RuntimeError("Database contains foreign-key violations.")

        print("\nForeign-key validation: PASSED")
        print(f"Total records inserted: {total_records:,}")
        print(f"Database saved at: {DB_PATH}")
        print("\nDatabase creation completed successfully!")

    finally:
        connection.close()


if __name__ == "__main__":
    main()
