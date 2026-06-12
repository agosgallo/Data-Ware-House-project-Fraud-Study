"""Build the reconciled SQLite database from the cleaned CSV.
Usage: python src/02_build_sqlite_reconciled.py --cleaned cleaned_fraud.csv --db reconciled.db
"""
import argparse, sqlite3
import pandas as pd
from pathlib import Path

def run_sql(conn, path):
    conn.executescript(Path(path).read_text())
    conn.commit()

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--cleaned', required=True)
    ap.add_argument('--db', required=True)
    ap.add_argument('--schema', default='sql/01_reconciled_schema.sql')
    ap.add_argument('--chunksize', type=int, default=200_000)
    args = ap.parse_args()

    conn = sqlite3.connect(args.db)
    run_sql(conn, args.schema)

    # Transaction types
    for t in pd.read_csv(args.cleaned, usecols=['type'])['type'].drop_duplicates():
        conn.execute('INSERT OR IGNORE INTO transaction_type(type_name) VALUES (?)', (t,))
    conn.commit()

    # Accounts
    for cols in [('nameOrig','origin_account_category'), ('nameDest','destination_account_category')]:
        for chunk in pd.read_csv(args.cleaned, usecols=list(cols), chunksize=args.chunksize):
            chunk = chunk.drop_duplicates().rename(columns={cols[0]:'account_code', cols[1]:'account_category'})
            conn.executemany('INSERT OR IGNORE INTO account(account_code, account_category) VALUES (?,?)', chunk.values.tolist())
            conn.commit()

    type_map = dict(conn.execute('SELECT type_name, type_id FROM transaction_type').fetchall())
    acc_map = dict(conn.execute('SELECT account_code, account_id FROM account').fetchall())

    source_row = 1
    for chunk in pd.read_csv(args.cleaned, chunksize=args.chunksize):
        chunk = chunk[chunk['quality_status'] == 'ACCEPT'].copy()
        chunk['source_row_number'] = range(source_row, source_row + len(chunk))
        source_row += len(chunk)
        chunk['type_id'] = chunk['type'].map(type_map)
        chunk['origin_account_id'] = chunk['nameOrig'].map(acc_map)
        chunk['destination_account_id'] = chunk['nameDest'].map(acc_map)
        out = chunk[[
            'source_row_number','step','type_id','amount','origin_account_id','destination_account_id',
            'oldbalanceOrg','newbalanceOrig','oldbalanceDest','newbalanceDest','isFraud','isFlaggedFraud',
            'origin_balance_delta','destination_balance_delta','origin_balance_error','destination_balance_error',
            'amount_band','quality_status'
        ]]
        out.columns = [
            'source_row_number','step','type_id','amount','origin_account_id','destination_account_id',
            'oldbalance_org','newbalance_orig','oldbalance_dest','newbalance_dest','is_fraud','is_flagged_fraud',
            'origin_balance_delta','destination_balance_delta','origin_balance_error','destination_balance_error',
            'amount_band','quality_status'
        ]
        out.to_sql('transaction_clean', conn, if_exists='append', index=False)
    conn.close()

if __name__ == '__main__':
    main()
