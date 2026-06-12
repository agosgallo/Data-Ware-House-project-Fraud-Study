"""Export star schema tables or denormalized extracts for Tableau Public.
Usage: python src/04_export_for_tableau.py --dw fraud_dw.db --outdir tableau_exports
"""
import argparse, sqlite3, os
import pandas as pd

TABLES = ['dim_time','dim_transaction_type','dim_origin_account','dim_destination_account','dim_fraud_status','fact_transaction']

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--dw', required=True)
    ap.add_argument('--outdir', required=True)
    args = ap.parse_args()
    os.makedirs(args.outdir, exist_ok=True)
    conn = sqlite3.connect(args.dw)
    for table in TABLES:
        pd.read_sql_query(f'SELECT * FROM {table}', conn).to_csv(os.path.join(args.outdir, f'{table}.csv'), index=False)
    # Aggregated extract is recommended for Tableau Public because fact_transaction has 6.36M rows.
    q = '''
    SELECT dt.day_number, dt.week_number, dt.hour_of_day, dt.day_phase,
           dtt.type_name, dtt.flow_family, dfs.fraud_label, dfs.flag_label,
           COUNT(*) AS transaction_count,
           SUM(f.amount) AS total_amount,
           AVG(f.amount) AS avg_amount,
           SUM(f.fraud_count) AS fraud_count,
           SUM(f.flagged_fraud_count) AS flagged_fraud_count,
           AVG(ABS(f.origin_balance_error)) AS avg_abs_origin_balance_error,
           AVG(ABS(f.destination_balance_error)) AS avg_abs_destination_balance_error
    FROM fact_transaction f
    JOIN dim_time dt ON dt.time_key=f.time_key
    JOIN dim_transaction_type dtt ON dtt.transaction_type_key=f.transaction_type_key
    JOIN dim_fraud_status dfs ON dfs.fraud_status_key=f.fraud_status_key
    GROUP BY dt.day_number, dt.week_number, dt.hour_of_day, dt.day_phase,
             dtt.type_name, dtt.flow_family, dfs.fraud_label, dfs.flag_label
    '''
    pd.read_sql_query(q, conn).to_csv(os.path.join(args.outdir, 'tableau_aggregated_extract.csv'), index=False)
    conn.close()

if __name__ == '__main__':
    main()
