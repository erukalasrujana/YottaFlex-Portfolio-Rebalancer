
from pathlib import Path
import sqlite3
import pandas as pd
import streamlit as st
import plotly.express as px

# --------------------------------------------------
# 1. CONFIGURATION
# --------------------------------------------------

BASE_DIR = Path(__file__).resolve().parent
DB_PATH = BASE_DIR / "database" / "portfolio.db"
REPORT_DIR = BASE_DIR / "outputs" / "reports"

RECOMMENDATION_FILE = REPORT_DIR / "rebalance_recommendations.csv"

st.set_page_config(
    page_title="YottaFlex Portfolio Rebalancer",
    page_icon="📊",
    layout="wide"
)


# --------------------------------------------------
# 2. HELPER FUNCTIONS
# --------------------------------------------------

@st.cache_data
def load_table(table_name):
    allowed_tables = {
        "portfolios",
        "investors",
        "holdings",
        "instruments",
        "trades",
        "constraints"
    }

    if table_name not in allowed_tables:
        raise ValueError("Invalid table name")

    with sqlite3.connect(DB_PATH) as connection:
        return pd.read_sql_query(
            f"SELECT * FROM {table_name}",
            connection
        )


def load_report(filename):
    file_path = REPORT_DIR / filename

    if file_path.exists():
        return pd.read_csv(file_path)

    return None


def get_database_validation():
    """
    Runs 14 database checks directly against SQLite.
    These results are calculated from the current database.
    """

    checks = []

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

    def add_check(name, passed, details):
        checks.append({
            "check": name,
            "failed_records": 0 if passed else 1,
            "result": "PASS" if passed else "FAIL",
            "details": details
        })

    with sqlite3.connect(DB_PATH) as connection:

        # 10 table record-count checks
        for table, expected in expected_counts.items():

            actual = pd.read_sql_query(
                f"SELECT COUNT(*) AS total FROM {table}",
                connection
            )["total"].iloc[0]

            add_check(
                f"{table} record count",
                actual == expected,
                f"Expected {expected:,}; found {actual:,}."
            )

        # Foreign-key integrity
        fk_result = pd.read_sql_query(
            "PRAGMA foreign_key_check",
            connection
        )

        add_check(
            "Foreign key integrity",
            fk_result.empty,
            f"Foreign-key violations: {len(fk_result)}."
        )

        # Target allocation totals
        target_result = pd.read_sql_query(
            """
            SELECT portfolio_id, SUM(target_weight_pct) AS total_weight
            FROM target_allocations
            GROUP BY portfolio_id
            """,
            connection
        )

        invalid_targets = target_result[
            (target_result["total_weight"] - 100).abs() > 0.01
        ]

        add_check(
            "Target allocations total 100%",
            invalid_targets.empty,
            f"Invalid portfolios: {len(invalid_targets)}."
        )

        # Five holdings per portfolio
        holding_result = pd.read_sql_query(
            """
            SELECT portfolio_id, COUNT(*) AS holding_count
            FROM holdings
            GROUP BY portfolio_id
            """,
            connection
        )

        invalid_holdings = holding_result[
            holding_result["holding_count"] != 5
        ]

        add_check(
            "Five holdings per portfolio",
            invalid_holdings.empty and len(holding_result) == 1000,
            f"Portfolios with incorrect holding counts: {len(invalid_holdings)}."
        )

        # 250 market price records per instrument
        price_result = pd.read_sql_query(
            """
            SELECT instrument_id, COUNT(*) AS price_count
            FROM market_prices
            GROUP BY instrument_id
            """,
            connection
        )

        invalid_prices = price_result[
            price_result["price_count"] != 250
        ]

        add_check(
            "250 price records per instrument",
            invalid_prices.empty and len(price_result) == 5000,
            f"Instruments with incorrect price counts: {len(invalid_prices)}."
        )

    return pd.DataFrame(checks)


def show_validation_report(title, filename, result_columns):
    df = load_report(filename)

    with st.expander(title, expanded=True):

        if df is None:
            st.warning(f"Report not found: {filename}")
            return

        result_column = next(
            (col for col in result_columns if col in df.columns),
            None
        )

        if result_column is None:
            st.warning(
                "No recognized validation result column found. "
                "Showing the available report."
            )
            st.dataframe(
                df,
                use_container_width=True,
                hide_index=True
            )
            return

        results = df[result_column].astype(str).str.upper().str.strip()

        passed = int((results == "PASS").sum())
        failed = int((results == "FAIL").sum())
        other = len(df) - passed - failed

        c1, c2, c3 = st.columns(3)

        c1.metric("Passed", passed)
        c2.metric("Failed", failed)
        c3.metric("Other", other)

        st.dataframe(
            df,
            use_container_width=True,
            hide_index=True
        )

        if failed == 0 and passed > 0:
            st.success("All reported checks passed.")
        elif failed > 0:
            st.error(f"{failed} failed checks detected.")
        else:
            st.info("Review the report results.")


# --------------------------------------------------
# 3. HEADER
# --------------------------------------------------

st.title("YottaFlex Portfolio Rebalancing System")

st.markdown(
    "Explainable, constraint-aware portfolio rebalancing"
)

st.divider()


# --------------------------------------------------
# 4. DATABASE CONNECTION
# --------------------------------------------------

if not DB_PATH.exists():
    st.error("Database not found.")
    st.code("python -m database.seed_data")
    st.stop()

try:
    portfolios = load_table("portfolios")
    investors = load_table("investors")
    holdings = load_table("holdings")
    instruments = load_table("instruments")
    trades = load_table("trades")
    constraints = load_table("constraints")

except Exception as error:
    st.error(f"Database error: {error}")
    st.stop()


# --------------------------------------------------
# 5. LOAD RECOMMENDATIONS
# --------------------------------------------------

if not RECOMMENDATION_FILE.exists():
    st.error("Recommendation report not found.")
    st.code("python -m src.recommendation_engine")
    st.stop()

recommendations = pd.read_csv(RECOMMENDATION_FILE)


# --------------------------------------------------
# 6. SYSTEM OVERVIEW
# --------------------------------------------------

st.subheader("System Overview")

c1, c2, c3, c4 = st.columns(4)

c1.metric("Total Portfolios", f"{len(portfolios):,}")
c2.metric("Total Investors", f"{len(investors):,}")
c3.metric("Total Instruments", f"{len(instruments):,}")
c4.metric("Recorded Trades", f"{len(trades):,}")

st.divider()


# --------------------------------------------------
# 7. PORTFOLIO SELECTION
# --------------------------------------------------

st.subheader("Portfolio Explorer")

selected_portfolio = st.selectbox(
    "Select a Portfolio",
    portfolios["portfolio_id"].tolist()
)

portfolio = portfolios[
    portfolios["portfolio_id"] == selected_portfolio
].iloc[0]

currency = portfolio["base_currency"]

c1, c2, c3 = st.columns(3)

c1.metric("Portfolio ID", selected_portfolio)
c2.metric("Investor ID", portfolio["investor_id"])
c3.metric(
    "Available Cash",
    f"{currency} {portfolio['total_cash']:,.2f}"
)

st.write("**Portfolio Name:**", portfolio["portfolio_name"])
st.write("**Portfolio Status:**", portfolio["portfolio_status"])


# --------------------------------------------------
# 8. CURRENT HOLDINGS
# --------------------------------------------------

st.divider()
st.subheader("Current Holdings")

portfolio_holdings = holdings[
    holdings["portfolio_id"] == selected_portfolio
].merge(
    instruments[
        ["instrument_id", "instrument_name", "current_price"]
    ],
    on="instrument_id",
    how="left"
)

portfolio_holdings["market_value"] = (
    portfolio_holdings["quantity"]
    * portfolio_holdings["current_price"]
)

if not portfolio_holdings.empty:

    display_holdings = portfolio_holdings[
        [
            "instrument_id",
            "instrument_name",
            "quantity",
            "current_price",
            "market_value"
        ]
    ].copy()

    display_holdings.columns = [
        "Instrument ID",
        "Instrument Name",
        "Quantity",
        "Current Price",
        "Market Value"
    ]

    st.dataframe(
        display_holdings,
        use_container_width=True,
        hide_index=True
    )

    total_holdings_value = portfolio_holdings[
        "market_value"
    ].sum()

    st.metric(
        "Total Current Holdings Value",
        f"{currency} {total_holdings_value:,.2f}"
    )

else:
    st.info("No holdings available.")


# --------------------------------------------------
# 9. REBALANCING RECOMMENDATIONS
# --------------------------------------------------

st.divider()
st.subheader("Rebalancing Recommendations")

portfolio_recommendations = recommendations[
    recommendations["portfolio_id"] == selected_portfolio
].copy()

if portfolio_recommendations.empty:

    st.info("No recommendations for this portfolio.")

else:

    status_counts = portfolio_recommendations[
        "status"
    ].value_counts()

    c1, c2, c3, c4 = st.columns(4)

    c1.metric(
        "Recommended",
        int(status_counts.get("RECOMMENDED", 0))
    )

    c2.metric(
        "Blocked",
        int(status_counts.get("BLOCKED", 0))
    )

    c3.metric(
        "No Trade",
        int(status_counts.get("NO_TRADE", 0))
    )

    c4.metric(
        "Needs Review",
        int(status_counts.get("NEEDS_REVIEW", 0))
    )

    st.markdown("#### Trade Action Distribution")

    action_counts = (
        portfolio_recommendations["action"]
        .value_counts()
        .rename_axis("Action")
        .reset_index(name="Count")
    )

    fig = px.bar(
        action_counts,
        x="Action",
        y="Count",
        color="Action",
        title="BUY / SELL / HOLD Distribution",
        text="Count"
    )

    st.plotly_chart(fig, use_container_width=True)

    total_fees = portfolio_recommendations[
        "estimated_fee"
    ].sum()

    total_trade_value = portfolio_recommendations[
        "trade_value"
    ].sum()

    c1, c2 = st.columns(2)

    c1.metric(
        "Total Estimated Trade Value",
        f"{currency} {total_trade_value:,.2f}"
    )

    c2.metric(
        "Total Estimated Fees",
        f"{currency} {total_fees:,.2f}"
    )

    st.markdown("#### Filter Recommendations")

    c1, c2 = st.columns(2)

    selected_status = c1.selectbox(
        "Filter by Status",
        ["ALL"] + sorted(
            portfolio_recommendations["status"].dropna().unique().tolist()
        )
    )

    selected_action = c2.selectbox(
        "Filter by Action",
        ["ALL"] + sorted(
            portfolio_recommendations["action"].dropna().unique().tolist()
        )
    )

    filtered = portfolio_recommendations.copy()

    if selected_status != "ALL":
        filtered = filtered[
            filtered["status"] == selected_status
        ]

    if selected_action != "ALL":
        filtered = filtered[
            filtered["action"] == selected_action
        ]

    st.dataframe(
        filtered,
        use_container_width=True,
        hide_index=True
    )

    st.markdown("#### Why Did the System Make This Recommendation?")

    for _, row in filtered.iterrows():

        with st.expander(
            f"{row['instrument_id']} | "
            f"{row['action']} | {row['status']}"
        ):

            st.write("**Action:**", row["action"])
            st.write("**Quantity:**", row["quantity"])

            st.write(
                "**Estimated Trade Value:**",
                f"{currency} {row['trade_value']:,.2f}"
            )

            st.write(
                "**Estimated Fee:**",
                f"{currency} {row['estimated_fee']:,.2f}"
            )

            st.write("**Decision Explanation:**")
            st.info(str(row["reason"]))

    st.download_button(
        label="Download Recommendations CSV",
        data=portfolio_recommendations.to_csv(
            index=False
        ).encode("utf-8"),
        file_name=f"{selected_portfolio}_recommendations.csv",
        mime="text/csv"
    )


# --------------------------------------------------
# 10. CONSTRAINT MONITORING
# --------------------------------------------------

st.divider()
st.subheader("Portfolio Constraints")

portfolio_constraint = constraints[
    constraints["portfolio_id"] == selected_portfolio
]

if not portfolio_constraint.empty:

    rule = portfolio_constraint.iloc[0]

    c1, c2, c3 = st.columns(3)

    c1.metric(
        "Maximum Position Weight",
        f"{rule['max_position_weight_pct']}%"
    )

    c2.metric(
        "Maximum Trade Value",
        f"{rule['max_trade_value_pct']}%"
    )

    c3.metric(
        "Minimum Cash Reserve",
        f"{rule['minimum_cash_reserve_pct']}%"
    )

    st.write(
        "**Short Selling Allowed:**",
        "Yes" if rule["allow_short_selling"] else "No"
    )

else:
    st.warning("No constraint record found.")


# --------------------------------------------------
# 11. VALIDATION & RISK MONITORING
# --------------------------------------------------

st.divider()
st.header("Validation & Risk Monitoring")

st.write(
    "Monitor database quality, recommendation rules, "
    "trade validation, post-trade reconciliation and "
    "deliberately injected edge cases."
)


# --------------------------------------------------
# 11A. DATABASE VALIDATION
# --------------------------------------------------

st.subheader("Database Quality Checks")

try:
    database_validation = get_database_validation()

    db_passed = int(
        (database_validation["result"] == "PASS").sum()
    )

    db_failed = int(
        (database_validation["result"] == "FAIL").sum()
    )

    c1, c2, c3 = st.columns(3)

    c1.metric("Passed", db_passed)
    c2.metric("Failed", db_failed)
    c3.metric("Total Checks", len(database_validation))

    st.dataframe(
        database_validation,
        use_container_width=True,
        hide_index=True
    )

    if db_failed == 0:
        st.success("All database quality checks passed.")
    else:
        st.error(f"{db_failed} database checks failed.")

except Exception as error:
    st.error(f"Database validation could not run: {error}")


# --------------------------------------------------
# 11B. RECOMMENDATION VALIDATION
# --------------------------------------------------

st.subheader("Recommendation Validation")

show_validation_report(
    "Recommendation Validation Report",
    "recommendation_validation.csv",
    ["result", "validation"]
)


# --------------------------------------------------
# 11C. TRADE VALIDATION
# --------------------------------------------------

st.subheader("Trade Validation")

trade_report = load_report("trade_validation_report.csv")

if trade_report is None:

    st.warning("Trade validation report not found.")

else:

    st.write("Trade-level validation results")

    status_column = next(
        (
            col for col in [
                "result",
                "validation",
                "status",
                "validation_status",
                "trade_status"
            ]
            if col in trade_report.columns
        ),
        None
    )

    if status_column:

        trade_status = (
            trade_report[status_column]
            .astype(str)
            .str.upper()
            .str.strip()
        )

        passed_trades = int((trade_status == "PASS").sum())
        failed_trades = int((trade_status == "FAIL").sum())

        c1, c2, c3 = st.columns(3)

        c1.metric("Passed Trades", passed_trades)
        c2.metric("Failed Trades", failed_trades)
        c3.metric("Total Trade Records", len(trade_report))

    elif "errors" in trade_report.columns:

        errors = trade_report["errors"].fillna("").astype(str)

        failed_trades = int(
            errors.str.strip().ne("").sum()
        )

        c1, c2 = st.columns(2)

        c1.metric(
            "Failed Trade Records",
            failed_trades
        )

        c2.metric(
            "Total Trade Records",
            len(trade_report)
        )

    st.dataframe(
        trade_report,
        use_container_width=True,
        hide_index=True
    )

    if status_column and failed_trades > 0:
        st.warning(
            "Some trade records failed validation. "
            "Review the records above."
        )
    elif "errors" in trade_report.columns and failed_trades > 0:
        st.warning(
            "Some trade records contain validation errors."
        )
    else:
        st.info(
            "Review the trade validation records and their error details."
        )


# --------------------------------------------------
# 11D. POST-TRADE VALIDATION
# --------------------------------------------------

st.subheader("Post-Trade Reconciliation")

show_validation_report(
    "Post-Trade Validation Report",
    "post_trade_validation_report.csv",
    ["result", "validation"]
)


# --------------------------------------------------
# 11E. GROUND-TRUTH EDGE-CASE VALIDATION
# --------------------------------------------------

st.subheader("Edge-Case Testing")

ground_truth = load_report("ground_truth_comparison.csv")

if ground_truth is None:

    st.warning("Ground-truth comparison report not found.")

else:

    if "validation" in ground_truth.columns:

        validation_results = (
            ground_truth["validation"]
            .astype(str)
            .str.upper()
            .str.strip()
        )

        edge_passed = int(
            (validation_results == "PASS").sum()
        )

        edge_failed = int(
            (validation_results == "FAIL").sum()
        )

        c1, c2, c3 = st.columns(3)

        c1.metric("Passed Edge Cases", edge_passed)
        c2.metric("Failed Edge Cases", edge_failed)
        c3.metric("Total Edge Cases", len(ground_truth))

        st.dataframe(
            ground_truth,
            use_container_width=True,
            hide_index=True
        )

        if edge_failed == 0 and edge_passed == 5:
            st.success(
                "All five deliberately injected edge cases "
                "matched their expected results."
            )
        elif edge_failed > 0:
            st.error(
                f"{edge_failed} edge-case tests did not match "
                "their expected results."
            )
        else:
            st.warning("Review the edge-case validation results.")

    else:

        st.dataframe(
            ground_truth,
            use_container_width=True,
            hide_index=True
        )


# --------------------------------------------------
# 12. SYSTEM INFORMATION
# --------------------------------------------------

st.divider()
st.subheader("System Information")

c1, c2 = st.columns(2)

with c1:
    st.write("**Database:** SQLite")
    st.write("**Database Location:** database/portfolio.db")
    st.write("**Data Source:** Synthetic datasets")

with c2:
    st.write("**Recommendation Engine:** Python")
    st.write("**Dashboard:** Streamlit")
    st.write("**Visualization:** Plotly")

st.divider()

st.caption(
    "YottaFlex Portfolio Rebalancing System | "
    "Synthetic Demonstration Environment"
)
