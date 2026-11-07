# Data Dictionary — YottaFlex Portfolio Rebalancing System

## 1. Overview

This document describes the 10 raw CSV datasets used by the YottaFlex Portfolio Rebalancing System. It records their columns, expected data types, business meaning, and relationships.

The data is synthetic and generated for this project.

## 2. Dataset descriptions

### 2.1 investors.csv

Stores investor information and investment preferences.

| Column | Expected data type | Description |
|---|---|---|
| investor_id | String | Unique identifier for each investor. |
| investor_name | String | Name assigned to the investor. |
| risk_tolerance | String | Investor's risk preference. |
| investment_horizon | String | Expected investment time horizon. |
| base_currency | String | Investor's primary currency. |
| is_active | Boolean | Indicates whether the investor is active. |

**Primary key:** `investor_id`

### 2.2 portfolios.csv

Contains portfolio details associated with investors.

| Column | Expected data type | Description |
|---|---|---|
| portfolio_id | String | Unique identifier for each portfolio. |
| investor_id | String | Investor associated with the portfolio. |
| portfolio_name | String | Name of the portfolio. |
| total_cash | Numeric | Available cash held in the portfolio. |
| base_currency | String | Portfolio's base currency. |
| portfolio_status | String | Current status of the portfolio. |

**Primary key:** `portfolio_id`

**Foreign key:** `investor_id` references `investors.investor_id`.

### 2.3 instruments.csv

Stores information about investment instruments.

| Column | Expected data type | Description |
|---|---|---|
| instrument_id | String | Unique identifier for an instrument. |
| instrument_name | String | Name of the instrument. |
| instrument_type | String | Category or type of instrument. |
| sector | String | Sector associated with the instrument. |
| current_price | Numeric | Current reference price of the instrument. |
| currency | String | Currency in which the instrument is priced. |
| is_tradable | Boolean | Indicates whether the instrument can be traded. |
| is_excluded | Boolean | Indicates whether the instrument is excluded by policy. |

**Primary key:** `instrument_id`

### 2.4 holdings.csv

Records the instruments currently held in each portfolio.

| Column | Expected data type | Description |
|---|---|---|
| holding_id | String | Unique identifier for a holding record. |
| portfolio_id | String | Portfolio containing the holding. |
| instrument_id | String | Instrument held in the portfolio. |
| quantity | Numeric | Number of units currently held. |
| average_cost_basis | Numeric | Average acquisition cost per unit. |
| acquisition_date | Date | Date on which the holding was acquired. |

**Primary key:** `holding_id`

**Foreign keys:**
- `portfolio_id` references `portfolios.portfolio_id`.
- `instrument_id` references `instruments.instrument_id`.

### 2.5 market_prices.csv

Stores historical market prices for investment instruments.

| Column | Expected data type | Description |
|---|---|---|
| instrument_id | String | Instrument associated with the price record. |
| price_date | Date | Date of the recorded market price. |
| market_price | Numeric | Recorded market price. |
| currency | String | Currency of the recorded price. |
| is_stale | Boolean | Indicates whether the price is marked as stale. |

**Relationship:** `instrument_id` references `instruments.instrument_id`.

**Note:** Multiple price records can exist for the same instrument across different dates.

### 2.6 target_allocations.csv

Defines the desired allocation of each instrument within a portfolio.

| Column | Expected data type | Description |
|---|---|---|
| target_allocation_id | String | Unique identifier for a target allocation record. |
| portfolio_id | String | Portfolio for which the allocation is defined. |
| instrument_id | String | Instrument receiving the target allocation. |
| target_weight_pct | Numeric | Desired portfolio allocation percentage for the instrument. |

**Primary key:** `target_allocation_id`

**Foreign keys:**
- `portfolio_id` references `portfolios.portfolio_id`.
- `instrument_id` references `instruments.instrument_id`.

**Business rule:** Target allocation percentages for a portfolio are expected to total 100%.

### 2.7 constraints.csv

Contains portfolio-level trading and allocation constraints.

| Column | Expected data type | Description |
|---|---|---|
| constraint_id | String | Unique identifier for a constraint record. |
| portfolio_id | String | Portfolio to which the constraints apply. |
| max_position_weight_pct | Numeric | Maximum permitted weight for an individual position. |
| max_trade_value_pct | Numeric | Maximum permitted trade value percentage. |
| minimum_cash_reserve_pct | Numeric | Minimum cash reserve percentage to maintain. |
| allow_short_selling | Boolean | Indicates whether short selling is permitted. |

**Primary key:** `constraint_id`

**Foreign key:** `portfolio_id` references `portfolios.portfolio_id`.

### 2.8 fee_schedules.csv

Defines transaction fee rules based on instrument type.

| Column | Expected data type | Description |
|---|---|---|
| fee_schedule_id | String | Unique identifier for a fee schedule. |
| instrument_type | String | Instrument category to which the fee applies. |
| commission_rate_pct | Numeric | Commission rate applied to the trade value. |
| fixed_fee | Numeric | Fixed transaction fee. |
| minimum_fee | Numeric | Minimum transaction fee permitted. |
| maximum_fee | Numeric | Maximum transaction fee permitted. |
| currency | String | Currency used for fee calculations. |

**Primary key:** `fee_schedule_id`

### 2.9 trades.csv

Contains recorded trade information.

| Column | Expected data type | Description |
|---|---|---|
| trade_id | String | Unique identifier for a trade. |
| portfolio_id | String | Portfolio associated with the trade. |
| instrument_id | String | Instrument being traded. |
| trade_side | String | Indicates whether the trade is a BUY or SELL. |
| quantity | Numeric | Number of units traded. |
| execution_price | Numeric | Price at which the trade was recorded. |
| trade_value | Numeric | Recorded total trade value. |
| fee_amount | Numeric | Transaction fee associated with the trade. |
| fee_schedule_id | String | Fee schedule applied to the trade. |
| trade_date | Date | Date of the trade. |
| trade_status | String | Current status of the trade. |
| currency | String | Currency used for the trade. |

**Primary key:** `trade_id`

**Foreign keys:**
- `portfolio_id` references `portfolios.portfolio_id`.
- `instrument_id` references `instruments.instrument_id`.
- `fee_schedule_id` references `fee_schedules.fee_schedule_id`.

### 2.10 rebalance_proposals.csv

Stores portfolio rebalancing proposal information and explanations.

| Column | Expected data type | Description |
|---|---|---|
| proposal_id | String | Unique identifier for a proposal. |
| portfolio_id | String | Portfolio associated with the proposal. |
| current_holdings_value | Numeric | Recorded value of current holdings. |
| target_weight_total_pct | Numeric | Total target allocation percentage. |
| maximum_allocation_drift_pct | Numeric | Maximum recorded allocation drift percentage. |
| proposal_status | String | Current status of the proposal. |
| explanation | String | Explanation associated with the proposal. |

**Primary key:** `proposal_id`

**Foreign key:** `portfolio_id` references `portfolios.portfolio_id`.

## 3. Dataset relationships

The datasets are connected through identifiers to maintain consistency and traceability.

| Parent dataset | Child dataset | Relationship |
|---|---|---|
| investors | portfolios | One investor can have multiple portfolios. |
| portfolios | holdings | A portfolio can contain multiple holdings. |
| instruments | holdings | An instrument can appear in multiple portfolios. |
| instruments | market_prices | An instrument can have multiple historical price records. |
| portfolios | target_allocations | A portfolio can have multiple target allocations. |
| instruments | target_allocations | An instrument can be assigned to multiple portfolios. |
| portfolios | constraints | Constraints are associated with portfolios. |
| fee_schedules | trades | A fee schedule can be referenced by multiple trades. |
| portfolios | trades | A portfolio can have multiple recorded trades. |
| instruments | trades | An instrument can appear in multiple trades. |
| portfolios | rebalance_proposals | A portfolio can have multiple proposals. |

## 4. Data integrity considerations

The system uses validation checks to identify data quality and business-rule issues, including:

- Duplicate identifiers and records.
- Missing required values.
- Invalid target allocation totals.
- Negative or invalid quantities and values.
- Trades exceeding available holdings.
- Trade values that do not reconcile with quantity and execution price.
- Missing transaction fees.
- Excluded or non-tradable instruments.
- Stale market prices.
- Violations of portfolio cash reserve and trading constraints.

## 5. Data type notes

The expected data types in this document are descriptive. Actual CSV values may be loaded as strings, integers, floating-point numbers, dates, or Boolean representations depending on the data-loading process.

The implementation should validate and convert these values before calculations.

## 6. Scope and limitations

- The datasets are synthetically generated for demonstration and testing.
- The data dictionary documents the raw CSV files, not every intermediate or output dataset.
- The exact allowed values for categorical fields are determined by the generated data and application logic.
- Currency conversion rules are not specified by these column definitions.
- This document does not imply that every possible financial-market or regulatory constraint is implemented.