
from pathlib import Path
import pandas as pd

BASE_DIR = Path(__file__).resolve().parent.parent

RAW_DIR = BASE_DIR / "data" / "raw"
PROCESSED_DIR = BASE_DIR / "data" / "processed"
GROUND_TRUTH_DIR = BASE_DIR / "data" / "ground_truth"

PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
GROUND_TRUTH_DIR.mkdir(parents=True, exist_ok=True)


def main():
    print("Loading baseline datasets...")

    targets = pd.read_csv(RAW_DIR / "target_allocations.csv")
    trades = pd.read_csv(RAW_DIR / "trades.csv")
    holdings = pd.read_csv(RAW_DIR / "holdings.csv")
    instruments = pd.read_csv(RAW_DIR / "instruments.csv")
    prices = pd.read_csv(RAW_DIR / "market_prices.csv")

    print("All baseline datasets loaded successfully.")

    edge_targets = targets.copy()
    edge_trades = trades.copy()
    edge_holdings = holdings.copy()
    edge_instruments = instruments.copy()
    edge_prices = prices.copy()

    print("Test copies created successfully.")

    # EDGE CASE 1: Target allocation totals 90%, not 100%.
    portfolio_targets = edge_targets[
        edge_targets["portfolio_id"] == "PORT00001"
    ].index

    edge_targets.loc[
        portfolio_targets, "target_weight_pct"
    ] = 18.0

    print("Edge case 1 created: target allocation totals 90%.")

    # EDGE CASE 2: SELL quantity exceeds available holding.
    trade_index = edge_trades.index[0]

    portfolio_id = edge_trades.loc[trade_index, "portfolio_id"]
    instrument_id = edge_trades.loc[trade_index, "instrument_id"]

    matching_holding = edge_holdings[
        (edge_holdings["portfolio_id"] == portfolio_id)
        & (edge_holdings["instrument_id"] == instrument_id)
    ]

    if not matching_holding.empty:
        edge_trades.loc[trade_index, "side"] = "SELL"
        edge_trades.loc[trade_index, "quantity"] = (
            matching_holding.iloc[0]["quantity"] + 100
        )

    print("Edge case 2 created: sell quantity exceeds holding.")

    # EDGE CASE 3: Exclude the exact instrument used in ground truth.
    excluded_id = "INS03099"

    edge_instruments.loc[
        edge_instruments["instrument_id"] == excluded_id,
        "is_excluded"
    ] = True

    print(f"Edge case 3 created: {excluded_id} is excluded.")

    # EDGE CASE 4: One trade has a missing fee.
    edge_trades.loc[
        edge_trades.index[1], "fee_amount"
    ] = float("nan")

    print("Edge case 4 created: one trade has a missing fee.")

    # EDGE CASE 5: Make the exact instrument's price history stale.
    stale_id = "INS03845"

    instrument_prices = edge_prices[
        edge_prices["instrument_id"] == stale_id
    ]

    if instrument_prices.empty:
        raise ValueError(
            f"Instrument {stale_id} not found in market prices."
        )

    # Shift all its price dates back by 730 days.
    edge_prices.loc[instrument_prices.index, "price_date"] = (
        pd.to_datetime(
            edge_prices.loc[instrument_prices.index, "price_date"]
        )
        - pd.Timedelta(days=730)
    ).dt.strftime("%Y-%m-%d")

    # Keep the stale flag false to test date-based stale detection.
    edge_prices.loc[
        instrument_prices.index, "is_stale"
    ] = False

    print(f"Edge case 5 created: {stale_id} has stale price history.")

    # Save all edge-case datasets.
    edge_targets.to_csv(
        PROCESSED_DIR / "edge_target_allocations.csv",
        index=False
    )

    edge_trades.to_csv(
        PROCESSED_DIR / "edge_trades.csv",
        index=False
    )

    edge_holdings.to_csv(
        PROCESSED_DIR / "edge_holdings.csv",
        index=False
    )

    edge_instruments.to_csv(
        PROCESSED_DIR / "edge_instruments.csv",
        index=False
    )

    edge_prices.to_csv(
        PROCESSED_DIR / "edge_market_prices.csv",
        index=False
    )

    print("\nAll five edge cases created successfully.")
    print("Files saved in data/processed/.")


if __name__ == "__main__":
    main()
