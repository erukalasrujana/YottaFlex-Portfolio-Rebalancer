# 1. IMPORT REQUIRED LIBRARIES
import pandas as pd
import numpy as np
import random

from pathlib import Path


# 2. PROJECT CONFIGURATION

SEED = 42

random.seed(SEED)
np.random.seed(SEED)

BASE_DIR = Path(__file__).resolve().parent.parent

RAW_DATA_DIR = BASE_DIR / "data" / "raw"
PROCESSED_DATA_DIR = BASE_DIR / "data" / "processed"

NUM_INVESTORS = 1000
NUM_PORTFOLIOS = 1000
NUM_INSTRUMENTS = 5000
NUM_HOLDINGS = 5000
NUM_TRADING_DAYS = 250

RAW_DATA_DIR.mkdir(parents=True, exist_ok=True)
PROCESSED_DATA_DIR.mkdir(parents=True, exist_ok=True)


# 3. GENERATE INVESTOR PROFILES

def generate_investors():

    investor_ids = [
        f"INV{str(i).zfill(5)}"
        for i in range(1, NUM_INVESTORS + 1)
    ]

    risk_levels = ["Conservative", "Moderate", "Aggressive"]
    investment_horizons = ["Short-term", "Medium-term", "Long-term"]

    investors = pd.DataFrame({
        "investor_id": investor_ids,
        "investor_name": [
            f"Investor_{i}" for i in range(1, NUM_INVESTORS + 1)
        ],
        "risk_tolerance": np.random.choice(
            risk_levels, NUM_INVESTORS, p=[0.3, 0.5, 0.2]
        ),
        "investment_horizon": np.random.choice(
            investment_horizons, NUM_INVESTORS
        ),
        "base_currency": ["USD"] * NUM_INVESTORS,
        "is_active": [True] * NUM_INVESTORS
    })

    return investors


# 4. GENERATE PORTFOLIOS

def generate_portfolios():

    portfolio_ids = [
        f"PORT{str(i).zfill(5)}"
        for i in range(1, NUM_PORTFOLIOS + 1)
    ]

    portfolios = pd.DataFrame({
        "portfolio_id": portfolio_ids,
        "investor_id": [
            f"INV{str(i).zfill(5)}"
            for i in range(1, NUM_PORTFOLIOS + 1)
        ],
        "portfolio_name": [
            f"Portfolio_{i}"
            for i in range(1, NUM_PORTFOLIOS + 1)
        ],
        "total_cash": np.random.uniform(
            1000, 10000, NUM_PORTFOLIOS
        ).round(2),
        "base_currency": ["USD"] * NUM_PORTFOLIOS,
        "portfolio_status": ["Active"] * NUM_PORTFOLIOS
    })

    return portfolios

#GENERATE FINANCIAL INSTRUMENTS

def generate_instruments():

    instrument_ids = [
        f"INS{str(i).zfill(5)}"
        for i in range(1, NUM_INSTRUMENTS + 1)
    ]

    instrument_types = [
        "Stock",
        "Bond",
        "ETF",
        "Mutual Fund"
    ]

    sectors = [
        "Technology",
        "Healthcare",
        "Finance",
        "Energy",
        "Consumer Goods",
        "Government",
        "Diversified"
    ]

    instruments = pd.DataFrame({

        "instrument_id": instrument_ids,

        "instrument_name": [
            f"Instrument_{i}"
            for i in range(1, NUM_INSTRUMENTS + 1)
        ],

        "instrument_type": np.random.choice(
            instrument_types, NUM_INSTRUMENTS
        ),

        "sector": np.random.choice(
            sectors, NUM_INSTRUMENTS
        ),

        "current_price": np.random.uniform(
            10, 1000, NUM_INSTRUMENTS
        ).round(2),

        "currency": ["USD"] * NUM_INSTRUMENTS,

        "is_tradable": [True] * NUM_INSTRUMENTS,

        "is_excluded": [False] * NUM_INSTRUMENTS

    })

    return instruments

# GENERATE PORTFOLIO HOLDINGS

def generate_holdings(instruments):

    holdings = []

    instrument_ids = instruments["instrument_id"].to_numpy()

    holding_number = 1

    for portfolio_number in range(1, NUM_PORTFOLIOS + 1):

        portfolio_id = f"PORT{str(portfolio_number).zfill(5)}"

        # Select five different instruments for each portfolio
        selected_instruments = np.random.choice(
            instrument_ids,
            size=5,
            replace=False
        )

        for instrument_id in selected_instruments:

            instrument_price = instruments.loc[
                instruments["instrument_id"] == instrument_id,
                "current_price"
            ].iloc[0]

            quantity = np.random.randint(1, 101)

            average_cost_basis = round(
                instrument_price * np.random.uniform(0.85, 1.15), 2
            )

            holdings.append({
                "holding_id": f"HLD{str(holding_number).zfill(6)}",
                "portfolio_id": portfolio_id,
                "instrument_id": instrument_id,
                "quantity": quantity,
                "average_cost_basis": average_cost_basis,
                "acquisition_date": (
                    pd.Timestamp("2025-01-01")
                    + pd.Timedelta(days=int(np.random.randint(0, 300)))
                ).date().isoformat()
            })

            holding_number += 1

    return pd.DataFrame(holdings)
# GENERATE HISTORICAL MARKET PRICES
def generate_market_prices(instruments):

    market_prices = []

    trading_dates = pd.bdate_range(
        end="2026-11-06",
        periods=NUM_TRADING_DAYS
    )

    for _, instrument in instruments.iterrows():

        instrument_id = instrument["instrument_id"]

        initial_price = instrument["current_price"]

        # Simulate daily market price changes
        daily_returns = np.random.normal(
            loc=0.0003,
            scale=0.015,
            size=NUM_TRADING_DAYS
        )

        prices = initial_price * np.cumprod(
            1 + daily_returns
        )

        for date, price in zip(trading_dates, prices):

            market_prices.append({
                "instrument_id": instrument_id,
                "price_date": date.date().isoformat(),
                "market_price": round(float(price), 2),
                "currency": instrument["currency"],
                "is_stale": False
            })

    return pd.DataFrame(market_prices)

# GENERATE TARGET ALLOCATIONS

def generate_target_allocations(holdings):

    target_allocations = []

    allocation_number = 1

    # Process each portfolio separately
    for portfolio_id, portfolio_holdings in holdings.groupby("portfolio_id"):

        instrument_ids = portfolio_holdings["instrument_id"].tolist()

        number_of_instruments = len(instrument_ids)

        # Generate random allocation weights
        weights = np.random.dirichlet(
            np.ones(number_of_instruments)
        ) * 100

        # Round weights while ensuring the total is exactly 100%
        rounded_weights = [
            round(weight, 2) for weight in weights[:-1]
        ]

        last_weight = round(
            100 - sum(rounded_weights), 2
        )

        rounded_weights.append(last_weight)

        # Store target allocation records
        for instrument_id, weight in zip(
            instrument_ids, rounded_weights
        ):

            target_allocations.append({

                "target_allocation_id": (
                    f"TGT{str(allocation_number).zfill(6)}"
                ),

                "portfolio_id": portfolio_id,

                "instrument_id": instrument_id,

                "target_weight_pct": weight

            })

            allocation_number += 1

    return pd.DataFrame(target_allocations)

#  GENERATE FEE SCHEDULES

def generate_fee_schedules():

    fee_schedules = pd.DataFrame({

        "fee_schedule_id": [
            "FEE001",
            "FEE002",
            "FEE003",
            "FEE004"
        ],

        "instrument_type": [
            "Stock",
            "Bond",
            "ETF",
            "Mutual Fund"
        ],

        "commission_rate_pct": [
            0.15,
            0.10,
            0.12,
            0.20
        ],

        "fixed_fee": [
            1.00,
            1.50,
            1.00,
            2.00
        ],

        "minimum_fee": [
            0.50,
            0.50,
            0.50,
            1.00
        ],

        "maximum_fee": [
            25.00,
            20.00,
            25.00,
            30.00
        ],

        "currency": ["USD"] * 4

    })

    return fee_schedules

def generate_constraints():
    constraints = pd.DataFrame({
        "constraint_id": [
            f"CON{str(i).zfill(5)}"
            for i in range(1, NUM_PORTFOLIOS + 1)
        ],
        "portfolio_id": [
            f"PORT{str(i).zfill(5)}"
            for i in range(1, NUM_PORTFOLIOS + 1)
        ],
        "max_position_weight_pct": np.random.choice(
            [40.0, 50.0, 60.0], NUM_PORTFOLIOS
        ),
        "max_trade_value_pct": np.random.choice(
            [20.0, 25.0, 30.0], NUM_PORTFOLIOS
        ),
        "minimum_cash_reserve_pct": np.random.choice(
            [2.0, 3.0, 5.0], NUM_PORTFOLIOS
        ),
        "allow_short_selling": [False] * NUM_PORTFOLIOS
    })

    return constraints

def generate_trades(holdings, instruments, fee_schedules):

    rng = np.random.default_rng(SEED + 8)

    trades = []

    instrument_lookup = (
        instruments.set_index("instrument_id").to_dict("index")
    )

    fee_lookup = (
        fee_schedules.set_index("instrument_type").to_dict("index")
    )

    holdings_by_portfolio = holdings.groupby("portfolio_id")

    trading_dates = pd.bdate_range(
        end="2026-11-06",
        periods=30
    )

    for portfolio_number in range(1, NUM_PORTFOLIOS + 1):

        portfolio_id = f"PORT{str(portfolio_number).zfill(5)}"

        portfolio_holdings = holdings_by_portfolio.get_group(
            portfolio_id
        )

        selected_holding = portfolio_holdings.iloc[
            rng.integers(0, len(portfolio_holdings))
        ]

        instrument_id = selected_holding["instrument_id"]

        instrument = instrument_lookup[instrument_id]

        fee_schedule = fee_lookup[instrument["instrument_type"]]

        trade_side = rng.choice(["BUY", "SELL"])

        if trade_side == "SELL":
            quantity = int(
                rng.integers(
                    1,
                    int(selected_holding["quantity"]) + 1
                )
            )
        else:
            quantity = int(rng.integers(1, 21))

        execution_price = float(instrument["current_price"])

        trade_value = round(
            quantity * execution_price, 2
        )

        commission = (
            trade_value
            * fee_schedule["commission_rate_pct"]
            / 100
        )

        calculated_fee = (
            fee_schedule["fixed_fee"] + commission
        )

        fee_amount = round(
            min(
                max(
                    calculated_fee,
                    fee_schedule["minimum_fee"]
                ),
                fee_schedule["maximum_fee"]
            ),
            2
        )

        trade_date = pd.Timestamp(
            rng.choice(trading_dates)
        ).date().isoformat()

        trades.append({
            "trade_id": f"TRD{str(portfolio_number).zfill(5)}",
            "portfolio_id": portfolio_id,
            "instrument_id": instrument_id,
            "trade_side": trade_side,
            "quantity": quantity,
            "execution_price": round(execution_price, 2),
            "trade_value": trade_value,
            "fee_amount": fee_amount,
            "fee_schedule_id": fee_schedule["fee_schedule_id"],
            "trade_date": trade_date,
            "trade_status": "Executed",
            "currency": instrument["currency"]
        })

    return pd.DataFrame(trades)

def generate_rebalance_proposals(
    holdings,
    instruments,
    target_allocations,
    constraints
):
    proposals = []

    # Attach current instrument prices to each holding
    valued_holdings = holdings.merge(
        instruments[["instrument_id", "current_price"]],
        on="instrument_id",
        how="left"
    )

    valued_holdings["market_value"] = (
        valued_holdings["quantity"]
        * valued_holdings["current_price"]
    )

    # Calculate total holdings value per portfolio
    portfolio_values = (
        valued_holdings.groupby("portfolio_id")["market_value"]
        .sum()
    )

    # Attach constraints to target allocations
    targets = target_allocations.merge(
        constraints[
            [
                "portfolio_id",
                "max_position_weight_pct"
            ]
        ],
        on="portfolio_id",
        how="left"
    )

    for portfolio_number in range(1, NUM_PORTFOLIOS + 1):

        portfolio_id = f"PORT{str(portfolio_number).zfill(5)}"

        current_value = float(portfolio_values[portfolio_id])

        portfolio_targets = targets[
            targets["portfolio_id"] == portfolio_id
        ]

        target_total = float(
            portfolio_targets["target_weight_pct"].sum()
        )

        # Calculate current allocation percentages
        portfolio_holdings = valued_holdings[
            valued_holdings["portfolio_id"] == portfolio_id
        ].copy()

        portfolio_holdings["current_weight_pct"] = (
            portfolio_holdings["market_value"]
            / current_value
            * 100
        )

        # Compare current and target weights
        comparison = portfolio_holdings.merge(
            portfolio_targets[
                ["instrument_id", "target_weight_pct"]
            ],
            on="instrument_id",
            how="left"
        )

        comparison["allocation_drift"] = (
            comparison["current_weight_pct"]
            - comparison["target_weight_pct"]
        ).abs()

        max_drift = float(
            comparison["allocation_drift"].max()
        )

        # Check whether target allocations exceed position limits
        exceeds_limit = (
            portfolio_targets["target_weight_pct"]
            > portfolio_targets["max_position_weight_pct"]
        ).any()

        allocation_valid = np.isclose(
            target_total, 100.0, atol=0.01
        )

        if not allocation_valid or exceeds_limit:
            status = "Needs Review"
            explanation = (
                "Target allocation validation requires review."
            )
        else:
            status = "Ready for Review"
            explanation = (
                "Allocation totals and position limits passed "
                "initial checks."
            )

        proposals.append({
            "proposal_id": (
                f"PROP{str(portfolio_number).zfill(5)}"
            ),
            "portfolio_id": portfolio_id,
            "current_holdings_value": round(current_value, 2),
            "target_weight_total_pct": round(target_total, 2),
            "maximum_allocation_drift_pct": round(max_drift, 2),
            "proposal_status": status,
            "explanation": explanation
        })

    return pd.DataFrame(proposals)

def main():

    print("Starting YottaFlex Portfolio Data Generation...")

    # 1. Generate investors
    investors = generate_investors()
    print("Investors generated:", len(investors))

    # 2. Generate portfolios
    portfolios = generate_portfolios()
    print("Portfolios generated:", len(portfolios))

    # 3. Generate instruments
    instruments = generate_instruments()
    print("Instruments generated:", len(instruments))

    # 4. Generate holdings
    holdings = generate_holdings(instruments)
    print("Holdings generated:", len(holdings))

    # 5. Generate market prices
    market_prices = generate_market_prices(instruments)
    print("Market prices generated:", len(market_prices))

    # 6. Generate target allocations
    target_allocations = generate_target_allocations(holdings)
    print("Target allocations generated:", len(target_allocations))

    # 7. Generate fee schedules
    fee_schedules = generate_fee_schedules()
    print("Fee schedules generated:", len(fee_schedules))

    # 8. Generate constraints
    constraints = generate_constraints()
    print("Constraints generated:", len(constraints))

    # 9. Generate trades
    trades = generate_trades(
        holdings, instruments, fee_schedules
    )
    print("Trades generated:", len(trades))

    # 10. Generate rebalance proposals
    proposals = generate_rebalance_proposals(
        holdings,
        instruments,
        target_allocations,
        constraints
    )
    print("Rebalance proposals generated:", len(proposals))

    # Save all datasets
    datasets = {
        "investors": investors,
        "portfolios": portfolios,
        "instruments": instruments,
        "holdings": holdings,
        "market_prices": market_prices,
        "target_allocations": target_allocations,
        "fee_schedules": fee_schedules,
        "constraints": constraints,
        "trades": trades,
        "rebalance_proposals": proposals
    }

    for name, dataframe in datasets.items():

        output_path = RAW_DATA_DIR / f"{name}.csv"

        dataframe.to_csv(output_path, index=False)

        print(f"Saved {name}.csv")

    print("\nAll datasets generated successfully!")


if __name__ == "__main__":
    main()
