-- Reconciled database schema for the Fraud transaction dataset
-- Target DBMS: SQLite

PRAGMA foreign_keys = ON;

DROP TABLE IF EXISTS transaction_raw;
DROP TABLE IF EXISTS transaction_clean;
DROP TABLE IF EXISTS account;
DROP TABLE IF EXISTS transaction_type;

CREATE TABLE transaction_type (
    type_id INTEGER PRIMARY KEY,
    type_name TEXT NOT NULL UNIQUE
);

CREATE TABLE account (
    account_id INTEGER PRIMARY KEY,
    account_code TEXT NOT NULL UNIQUE,
    account_category TEXT NOT NULL CHECK (account_category IN ('CUSTOMER','MERCHANT','UNKNOWN'))
);

CREATE TABLE transaction_clean (
    transaction_id INTEGER PRIMARY KEY,
    source_row_number INTEGER NOT NULL UNIQUE,
    step INTEGER NOT NULL CHECK (step >= 1),
    type_id INTEGER NOT NULL,
    amount REAL NOT NULL CHECK (amount >= 0),
    origin_account_id INTEGER NOT NULL,
    destination_account_id INTEGER NOT NULL,
    oldbalance_org REAL NOT NULL CHECK (oldbalance_org >= 0),
    newbalance_orig REAL NOT NULL CHECK (newbalance_orig >= 0),
    oldbalance_dest REAL NOT NULL CHECK (oldbalance_dest >= 0),
    newbalance_dest REAL NOT NULL CHECK (newbalance_dest >= 0),
    is_fraud INTEGER NOT NULL CHECK (is_fraud IN (0,1)),
    is_flagged_fraud INTEGER NOT NULL CHECK (is_flagged_fraud IN (0,1)),
    origin_balance_delta REAL NOT NULL,
    destination_balance_delta REAL NOT NULL,
    origin_balance_error REAL NOT NULL,
    destination_balance_error REAL NOT NULL,
    amount_band TEXT NOT NULL,
    quality_status TEXT NOT NULL,
    FOREIGN KEY (type_id) REFERENCES transaction_type(type_id),
    FOREIGN KEY (origin_account_id) REFERENCES account(account_id),
    FOREIGN KEY (destination_account_id) REFERENCES account(account_id)
);

CREATE INDEX idx_transaction_clean_step ON transaction_clean(step);
CREATE INDEX idx_transaction_clean_type ON transaction_clean(type_id);
CREATE INDEX idx_transaction_clean_fraud ON transaction_clean(is_fraud);
CREATE INDEX idx_transaction_clean_origin ON transaction_clean(origin_account_id);
CREATE INDEX idx_transaction_clean_dest ON transaction_clean(destination_account_id);
