# YottaFlex Portfolio Rebalancing System

## About the Project

This project is a portfolio rebalancing system developed using Python. Its main purpose is to check the current portfolio holdings against target allocations and generate suitable rebalancing recommendations.

The system also checks portfolio constraints and validates trade records to identify issues before considering a trade.

I used synthetic datasets to build and test the workflow.

## What the System Does

- Loads portfolio, investor, instrument, and market price data.
- Compares current holdings with target allocations.
- Generates BUY, SELL, HOLD, BLOCKED, or NEEDS_REVIEW recommendations based on the applicable rules.
- Checks constraints such as maximum position weight, maximum trade value, and minimum cash reserve.
- Validates trade records, including available holdings and transaction fees.
- Checks portfolio allocations after simulated trades.
- Tests different edge cases to verify how the system handles invalid or restricted situations.
- Displays the results through a Streamlit dashboard.

## Technologies Used

- Python
- Pandas and NumPy
- SQLite
- Streamlit
- Plotly

## Project Validation

I ran the validation modules to check the generated data and system outputs.

| Validation | Result |
|---|---:|
| Database quality checks | 14 passed |
| Recommendation checks | 10 passed |
| Post-trade checks | 9 passed |
| Edge-case tests | 5 passed |
| Trade records | 998 passed, 2 failed |

The two failed trade records are intentionally included to test whether the system can identify invalid trade information. The edge-case validation confirmed all five expected outcomes.

## How to Run the Project

1. Download or clone the project.
2. Open the project folder in a terminal.
3. Install the required packages:

   `pip install -r requirements.txt`

4. Start the dashboard:

   `python -m streamlit run main.py`

5. Open the local address displayed in the terminal.

## Project Limitations

This is a demonstration project built with synthetic data. It does not connect to live financial markets, provide live investment advice, or execute actual trades.

## Project Structure

- `main.py` – Streamlit dashboard
- `src/` – Data processing, recommendation, and validation modules
- `data/` – Input datasets and test data
- `database/` – SQLite database and database setup files
- `outputs/` – Generated recommendations and validation reports
- `docs/` – Project documentation

## Conclusion

This project helped me understand how portfolio data, investment constraints, trade validation, and post-trade checks can work together in a single workflow.