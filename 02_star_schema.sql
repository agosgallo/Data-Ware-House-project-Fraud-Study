-- Logical data warehouse star schema
PRAGMA foreign_keys = ON;

DROP TABLE IF EXISTS fact_transaction;
DROP TABLE IF EXISTS dim_time;
DROP TABLE IF EXISTS dim_transaction_type;
DROP TABLE IF EXISTS dim_origin_account;
DROP TABLE IF EXISTS dim_destination_account;
DROP TABLE IF EXISTS dim_fraud_status;

CREATE TABLE dim_time (
    time_key INTEGER PRIMARY KEY,
    step INTEGER NOT NULL UNIQUE,
    day_number INTEGER NOT NULL,
    hour_of_day INTEGER NOT NULL,
    week_number INTEGER NOT NULL,
    day_phase TEXT NOT NULL
);

CREATE TABLE dim_transaction_type (
    transaction_type_key INTEGER PRIMARY KEY,
    type_name TEXT NOT NULL UNIQUE,
    flow_family TEXT NOT NULL
);

CREATE TABLE dim_origin_account (
    origin_account_key INTEGER PRIMARY KEY,
    account_code TEXT NOT NULL UNIQUE,
    account_category TEXT NOT NULL
);

CREATE TABLE dim_destination_account (
    destination_account_key INTEGER PRIMARY KEY,
    account_code TEXT NOT NULL UNIQUE,
    account_category TEXT NOT NULL
);

CREATE TABLE dim_fraud_status (
    fraud_status_key INTEGER PRIMARY KEY,
    is_fraud INTEGER NOT NULL,
    is_flagged_fraud INTEGER NOT NULL,
    fraud_label TEXT NOT NULL,
    flag_label TEXT NOT NULL,
    UNIQUE(is_fraud, is_flagged_fraud)
);

CREATE TABLE fact_transaction (
    transaction_key INTEGER PRIMARY KEY,
    time_key INTEGER NOT NULL,
    transaction_type_key INTEGER NOT NULL,
    origin_account_key INTEGER NOT NULL,
    destination_account_key INTEGER NOT NULL,
    fraud_status_key INTEGER NOT NULL,
    transaction_count INTEGER NOT NULL DEFAULT 1,
    amount REAL NOT NULL,
    origin_old_balance REAL NOT NULL,
    origin_new_balance REAL NOT NULL,
    destination_old_balance REAL NOT NULL,
    destination_new_balance REAL NOT NULL,
    origin_balance_delta REAL NOT NULL,
    destination_balance_delta REAL NOT NULL,
    origin_balance_error REAL NOT NULL,
    destination_balance_error REAL NOT NULL,
    fraud_count INTEGER NOT NULL,
    flagged_fraud_count INTEGER NOT NULL,
    FOREIGN KEY (time_key) REFERENCES dim_time(time_key),
    FOREIGN KEY (transaction_type_key) REFERENCES dim_transaction_type(transaction_type_key),
    FOREIGN KEY (origin_account_key) REFERENCES dim_origin_account(origin_account_key),
    FOREIGN KEY (destination_account_key) REFERENCES dim_destination_account(destination_account_key),
    FOREIGN KEY (fraud_status_key) REFERENCES dim_fraud_status(fraud_status_key)
);

CREATE INDEX idx_fact_time ON fact_transaction(time_key);
CREATE INDEX idx_fact_type ON fact_transaction(transaction_type_key);
CREATE INDEX idx_fact_fraud ON fact_transaction(fraud_status_key);
