
from pathlib import Path

import pandas as pd
import numpy as np

BASE_DIR = Path(__file__).resolve().parent.parent
RAW_DIR = BASE_DIR / "data" / "raw"

def main():

    print("Starting data validation...\n")

    datasets = {}

    filenames = [
        "investors",
        "portfolios",
        "instruments",
        "holdings",
        "market_prices",
        "target_allocations",
        "fee_schedules",
        "constraints",
        "trades",
        "rebalance_proposals"
    ]

    for name in filenames:
        datasets[name] = pd.read_csv(
            RAW_DIR / f"{name}.csv"
        )

    errors = []
    total_checks = 0
 
    def check(condition, message):
        nonlocal total_checks
        total_checks += 1

        if condition:
            print("PASS:", message)
        else:
            print("FAIL:", message)
            errors.append(message)

    #  Check expected record counts
    expected_counts = {
        "investors": 1000,
        "portfolios": 1000,
        "instruments": 5000,
        "holdings": 5000,
        "market_prices": 1250000,
        "target_allocations": 5000,
        "fee_schedules": 4,
        "constraints": 1000,
        "trades": 1000,
        "rebalance_proposals": 1000
    }

    for name, expected in expected_counts.items():
        check(
            len(datasets[name]) == expected,
            f"{name}: expected {expected} records"
        )

    #  Check unique primary IDs
    primary_keys = {
        "investors": "investor_id",
        "portfolios": "portfolio_id",
        "instruments": "instrument_id",
        "holdings": "holding_id",
        "target_allocations": "target_allocation_id",
        "fee_schedules": "fee_schedule_id",
        "constraints": "constraint_id",
        "trades": "trade_id",
        "rebalance_proposals": "proposal_id"
    }

    for name, column in primary_keys.items():
        check(
            datasets[name][column].is_unique,
            f"{name}: unique {column}"
        )

    #  Check missing values
    for name, dataframe in datasets.items():
        check(
            dataframe.isnull().sum().sum() == 0,
            f"{name}: no missing values"
        )

    #  Check portfolio relationships
    investors = datasets["investors"]
    portfolios = datasets["portfolios"]
    instruments = datasets["instruments"]
    holdings = datasets["holdings"]
    prices = datasets["market_prices"]
    targets = datasets["target_allocations"]
    fees = datasets["fee_schedules"]
    constraints = datasets["constraints"]
    trades = datasets["trades"]
    proposals = datasets["rebalance_proposals"]

    check(
        portfolios["investor_id"].isin(
            investors["investor_id"]
        ).all(),
        "Every portfolio has a valid investor"
    )

    check(
        holdings["portfolio_id"].isin(
            portfolios["portfolio_id"]
        ).all(),
        "Every holding has a valid portfolio"
    )

    check(
        holdings["instrument_id"].isin(
            instruments["instrument_id"]
        ).all(),
        "Every holding has a valid instrument"
    )

    check(
        prices["instrument_id"].isin(
            instruments["instrument_id"]
        ).all(),
        "Every market price has a valid instrument"
    )

    check(
        targets["portfolio_id"].isin(
            portfolios["portfolio_id"]
        ).all(),
        "Every target has a valid portfolio"
    )

    check(
        targets["instrument_id"].isin(
            instruments["instrument_id"]
        ).all(),
        "Every target has a valid instrument"
    )

    check(
        constraints["portfolio_id"].isin(
            portfolios["portfolio_id"]
        ).all(),
        "Every constraint has a valid portfolio"
    )

    check(
        trades["fee_schedule_id"].isin(
            fees["fee_schedule_id"]
        ).all(),
        "Every trade has a valid fee schedule"
    )

    check(
        proposals["portfolio_id"].isin(
            portfolios["portfolio_id"]
        ).all(),
        "Every proposal has a valid portfolio"
    )

    #  Check five holdings per portfolio
    holding_counts = holdings.groupby(
        "portfolio_id"
    ).size()

    check(
        (holding_counts == 5).all()
        and len(holding_counts) == 1000,
        "Every portfolio has exactly 5 holdings"
    )

    #  Check 250 market prices per instrument
    price_counts = prices.groupby(
        "instrument_id"
    ).size()

    check(
        (price_counts == 250).all()
        and len(price_counts) == 5000,
        "Every instrument has 250 market-price records"
    )

    #  Check target allocations total 100%
    allocation_totals = targets.groupby(
        "portfolio_id"
    )["target_weight_pct"].sum()

    check(
        len(allocation_totals) == 1000
        and np.allclose(
            allocation_totals.values,
            100.0,
            atol=0.01
        ),
        "Target allocations total 100% per portfolio"
    )

    print("\n--------------------------------")
    print("DATA VALIDATION SUMMARY")
    print("--------------------------------")

    print("Total checks:", total_checks)
    print("Failed checks:", len(errors))

    if errors:
        print("\nValidation completed with errors.")
    else:
        print("\nAll data validation checks passed!")


if __name__ == "__main__":
    main()
