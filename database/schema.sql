
PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS investors (
    investor_id TEXT PRIMARY KEY,
    investor_name TEXT NOT NULL,
    risk_tolerance TEXT,
    investment_horizon TEXT,
    base_currency TEXT,
    is_active INTEGER
);

CREATE TABLE IF NOT EXISTS portfolios (
    portfolio_id TEXT PRIMARY KEY,
    investor_id TEXT NOT NULL,
    portfolio_name TEXT,
    total_cash REAL,
    base_currency TEXT,
    portfolio_status TEXT,
    FOREIGN KEY (investor_id) REFERENCES investors(investor_id)
);

CREATE TABLE IF NOT EXISTS instruments (
    instrument_id TEXT PRIMARY KEY,
    instrument_name TEXT NOT NULL,
    instrument_type TEXT,
    sector TEXT,
    current_price REAL,
    currency TEXT,
    is_tradable INTEGER,
    is_excluded INTEGER
);

CREATE TABLE IF NOT EXISTS holdings (
    holding_id TEXT PRIMARY KEY,
    portfolio_id TEXT NOT NULL,
    instrument_id TEXT NOT NULL,
    quantity REAL NOT NULL,
    average_cost_basis REAL,
    acquisition_date TEXT,
    FOREIGN KEY (portfolio_id) REFERENCES portfolios(portfolio_id),
    FOREIGN KEY (instrument_id) REFERENCES instruments(instrument_id)
);

CREATE TABLE IF NOT EXISTS market_prices (
    instrument_id TEXT NOT NULL,
    price_date TEXT NOT NULL,
    market_price REAL NOT NULL,
    currency TEXT,
    is_stale INTEGER,
    PRIMARY KEY (instrument_id, price_date),
    FOREIGN KEY (instrument_id) REFERENCES instruments(instrument_id)
);

CREATE TABLE IF NOT EXISTS target_allocations (
    target_allocation_id TEXT PRIMARY KEY,
    portfolio_id TEXT NOT NULL,
    instrument_id TEXT NOT NULL,
    target_weight_pct REAL NOT NULL,
    FOREIGN KEY (portfolio_id) REFERENCES portfolios(portfolio_id),
    FOREIGN KEY (instrument_id) REFERENCES instruments(instrument_id),
    UNIQUE (portfolio_id, instrument_id)
);

CREATE TABLE IF NOT EXISTS fee_schedules (
    fee_schedule_id TEXT PRIMARY KEY,
    instrument_type TEXT,
    commission_rate_pct REAL,
    fixed_fee REAL,
    minimum_fee REAL,
    maximum_fee REAL,
    currency TEXT
);

CREATE TABLE IF NOT EXISTS constraints (
    constraint_id TEXT PRIMARY KEY,
    portfolio_id TEXT NOT NULL,
    max_position_weight_pct REAL,
    max_trade_value_pct REAL,
    minimum_cash_reserve_pct REAL,
    allow_short_selling INTEGER,
    FOREIGN KEY (portfolio_id) REFERENCES portfolios(portfolio_id)
);

CREATE TABLE IF NOT EXISTS trades (
    trade_id TEXT PRIMARY KEY,
    portfolio_id TEXT NOT NULL,
    instrument_id TEXT NOT NULL,
    trade_side TEXT,
    quantity REAL,
    execution_price REAL,
    trade_value REAL,
    fee_amount REAL,
    fee_schedule_id TEXT,
    trade_date TEXT,
    trade_status TEXT,
    currency TEXT,
    FOREIGN KEY (portfolio_id) REFERENCES portfolios(portfolio_id),
    FOREIGN KEY (instrument_id) REFERENCES instruments(instrument_id),
    FOREIGN KEY (fee_schedule_id) REFERENCES fee_schedules(fee_schedule_id)
);

CREATE TABLE IF NOT EXISTS rebalance_proposals (
    proposal_id TEXT PRIMARY KEY,
    portfolio_id TEXT NOT NULL,
    current_holdings_value REAL,
    target_weight_total_pct REAL,
    maximum_allocation_drift_pct REAL,
    proposal_status TEXT,
    explanation TEXT,
    FOREIGN KEY (portfolio_id) REFERENCES portfolios(portfolio_id)
);

-- Useful indexes for portfolio queries

CREATE INDEX IF NOT EXISTS idx_holdings_portfolio
ON holdings(portfolio_id);

CREATE INDEX IF NOT EXISTS idx_holdings_instrument
ON holdings(instrument_id);

CREATE INDEX IF NOT EXISTS idx_market_prices_date
ON market_prices(price_date);

CREATE INDEX IF NOT EXISTS idx_targets_portfolio
ON target_allocations(portfolio_id);

CREATE INDEX IF NOT EXISTS idx_trades_portfolio
ON trades(portfolio_id);
