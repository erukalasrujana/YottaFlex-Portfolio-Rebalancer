# YottaFlex Portfolio Rebalancing System

An explainable, constraint-aware portfolio rebalancing prototype built with Python, Pandas, SQLite and Streamlit.

## 1. Project Overview

The YottaFlex Portfolio Rebalancing System analyses synthetic investment portfolio data and generates proposed BUY, SELL, HOLD or blocked recommendations based on target allocations, available cash, instrument eligibility, transaction fees and portfolio constraints.

The system also validates proposed trades, evaluates post-trade allocations and detects deliberately injected data and policy edge cases.

**This is a demonstration prototype using synthetic data. It is not connected to live financial markets and does not execute real trades.**

## 2. Business Problem

Portfolio rebalancing requires comparing current holdings with target allocations while respecting investment restrictions, cash reserves, transaction costs and instrument eligibility.

Manual processes can overlook invalid allocation weights, excessive trade quantities, excluded instruments, missing fees or outdated prices.

This project demonstrates an automated workflow that:

- Generates portfolio-level recommendations.
- Explains why each recommendation was produced or blocked.
- Applies portfolio and instrument constraints.
- Validates trade quantities, values and transaction fees.
- Recalculates portfolio allocations after proposed trades.
- Identifies and reports edge cases.

## 3. Project Objectives

1. Generate reproducible synthetic portfolio datasets.
2. Build a constraint-aware recommendation engine.
3. Provide explainable recommendations.
4. Validate proposed trades and transaction fees.
5. Recalculate post-trade portfolio allocations.
6. Test the system against known edge cases.
7. Store structured data in a relational SQLite database.
8. Present results through an interactive dashboard.

## 4. Technology Stack

| Technology | Purpose |
|---|---|
| Python | Core application logic |
| Pandas | Data processing and analysis |
| NumPy | Numerical operations and synthetic data |
| SQLite | Relational database |
| Streamlit | Interactive dashboard |
| Plotly | Data visualization |
| Pytest | Testing framework |

## 5. Dataset Overview

The project uses deterministic synthetic datasets generated with a fixed random seed.

| Dataset | Records |
|---|---:|
| Investors | 1,000 |
| Portfolios | 1,000 |
| Instruments | 5,000 |
| Holdings | 5,000 |
| Market prices | 1,250,000 |
| Target allocations | 5,000 |
| Fee schedules | 4 |
| Constraints | 1,000 |
| Trades | 1,000 |
| Rebalance proposals | 1,000 |

The SQLite database contains **1,270,004 records** across ten relational tables.

The datasets are synthetic and do not represent actual customers, investors or market transactions.

## 6. System Workflow

1. Generate synthetic datasets.
2. Validate the generated input data.
3. Create deliberately modified edge-case datasets.
4. Load portfolio, holding, price, allocation and constraint information.
5. Generate rebalancing recommendations.
6. Validate recommendation rules and transaction fees.
7. Perform post-trade allocation analysis.
8. Validate executed-trade records against available holdings and fee rules.
9. Compare edge-case outcomes against expected ground-truth results.
10. Seed and validate the SQLite database.
11. Display portfolio information and validation results in Streamlit.

## 7. Recommendation Logic

The recommendation engine evaluates portfolio holdings against their target allocations.

It considers:

- Current holding values.
- Portfolio cash.
- Target allocation percentages.
- Minimum cash reserve.
- Maximum position weight.
- Maximum trade value.
- Instrument exclusion and tradability.
- Market-price freshness.
- Transaction fee schedules.

The engine produces a recommendation status and an explanation for each portfolio-instrument combination.

Possible statuses include:

- `RECOMMENDED`
- `BLOCKED`
- `NO_TRADE`
- `NEEDS_REVIEW`

The recommendation is a proposed action, not an instruction to execute a real transaction.

## 8. Edge-Case Testing

Five deliberately injected edge cases are used to test the system.

| Test | Scenario | Expected outcome |
|---|---|---|
| EC001 | Target weights total only 90% | NEEDS_REVIEW |
| EC002 | Sell quantity exceeds available holding | FAIL |
| EC003 | Instrument is excluded by policy | BLOCKED |
| EC004 | Transaction fee is missing | FAIL |
| EC005 | Market price is more than seven days old without a stale flag | BLOCKED |

The ground-truth comparison report checks actual results against expected outcomes.

**Latest recorded result: 5 out of 5 edge-case tests passed.**

## 9. Validation Results

The current project validation reports show:

| Validation stage | Passed | Failed |
|---|---:|---:|
| Database quality | 14 | 0 |
| Recommendation validation | 10 | 0 |
| Trade validation | 998 | 2 |
| Post-trade validation | 9 | 0 |
| Ground-truth comparison | 5 | 0 |

The two failed trade records are intentional test records detected by the trade validator:

- TRD00001: Sell quantity exceeds available holdings and trade value does not match quantity multiplied by price.
- TRD00002: Transaction fee is missing.

These are detected validation failures, not successful trades.

## 10. Project Structure

```text
YottaFlex_Portfolio_Rebalancer/
│
├── data/
│   ├── raw/
│   ├── processed/
│   └── ground_truth/
│
├── database/
│   ├── schema.sql
│   ├── seed_data.py
│   └── portfolio.db
│
├── src/
│   ├── generate_data.py
│   ├── validate_data.py
│   ├── create_edge_cases.py
│   ├── recommendation_engine.py
│   ├── validate_recommendations.py
│   ├── validate_trades.py
│   ├── post_trade_analysis.py
│   ├── validate_post_trade.py
│   ├── validate_ground_truth.py
│   └── validate_database.py
│
├── tests/
├── docs/
├── outputs/
│   └── reports/
│
├── main.py
├── requirements.txt
├── README.md
└── .gitignore
```

## 11. Installation

### Prerequisites

- Python 3.10 or later
- pip
- Git (for repository setup)

### Clone the repository

```bash
git clone YOUR_GITHUB_REPOSITORY_URL
cd YottaFlex_Portfolio_Rebalancer
```

Replace `YOUR_GITHUB_REPOSITORY_URL` with the actual public repository URL.

### Create a virtual environment

Windows PowerShell:

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
```

### Install dependencies

```powershell
python -m pip install -r requirements.txt
```

## 12. Running the Project

Run the following commands from the project root, with the virtual environment activated.

### Step 1: Generate synthetic datasets

```powershell
python -m src.generate_data
```

### Step 2: Validate input datasets

```powershell
python -m src.validate_data
```

### Step 3: Generate edge-case datasets

```powershell
python -m src.create_edge_cases
```

### Step 4: Generate baseline recommendations

```powershell
python -m src.recommendation_engine
```

### Step 5: Validate recommendations

```powershell
python -m src.validate_recommendations
```

### Step 6: Perform post-trade analysis

```powershell
python -m src.post_trade_analysis
```

### Step 7: Validate post-trade results

```powershell
python -m src.validate_post_trade
```

### Step 8: Generate edge-case recommendations

```powershell
python -m src.recommendation_engine edge
```

### Step 9: Validate trade records

```powershell
python -m src.validate_trades
```

### Step 10: Compare results with ground truth

```powershell
python -m src.validate_ground_truth
```

### Step 11: Create the SQLite database

```powershell
python -m database.seed_data
```

### Step 12: Validate the database

```powershell
python -m src.validate_database
```

### Step 13: Launch the dashboard

```powershell
streamlit run main.py
```

Streamlit will provide a local browser address, usually:

```text
http://localhost:8501
```

## 13. Dashboard Features

The interactive dashboard provides:

- System-wide portfolio, investor and instrument counts.
- Portfolio selection and individual portfolio details.
- Current holdings and estimated market values.
- Rebalancing recommendations.
- BUY/SELL action visualization.
- Estimated trade values and fees.
- Recommendation filters and decision explanations.
- Portfolio constraint monitoring.
- Database quality checks.
- Recommendation validation results.
- Trade validation records.
- Post-trade reconciliation results.
- Ground-truth edge-case testing results.
- Recommendation CSV downloads.

## 14. Generated Reports

Reports are saved under:

```text
outputs/reports/
```

Important reports include:

- `rebalance_recommendations.csv`
- `edge_case_recommendations.csv`
- `recommendation_validation.csv`
- `trade_validation_report.csv`
- `post_trade_allocations.csv`
- `portfolio_summary.csv`
- `post_trade_validation_report.csv`
- `ground_truth_comparison.csv`

## 15. Assumptions and Limitations

- All datasets are synthetic.
- The market-price history is generated for demonstration purposes.
- The recommendation engine produces proposals and does not execute trades.
- Recommendations are based on the available portfolio holdings and configured target allocations.
- The current implementation does not establish live brokerage connectivity.
- The project does not provide personalized financial advice.
- Synthetic validation results do not establish production suitability.
- Real-world deployment would require additional security, compliance, performance, market-data and execution controls.

## 16. AI-Assisted Development

AI assistance was used during development for guidance on project structure, Python implementation, debugging, validation logic, documentation and dashboard development.

The generated code was integrated and tested within the local project environment. Validation scripts and execution results were used to check the implementation.

AI assistance does not replace code review, testing or independent verification. The developer remains responsible for understanding and explaining the implementation.

## 17. Future Improvements

Potential future enhancements include:

- Live market-data integration.
- Brokerage or trading-system integration.
- More advanced portfolio optimization.
- Risk and performance analytics.
- Automated alerts for policy violations.
- Authentication and role-based access.
- More extensive automated unit and integration tests.
- Improved support for new instrument purchase candidates.

## 18. Project Status

The current prototype includes synthetic data generation, recommendation logic, trade validation, post-trade analysis, edge-case testing, SQLite storage and a Streamlit dashboard.

It is intended as a demonstration of an explainable, constraint-aware portfolio rebalancing workflow.
