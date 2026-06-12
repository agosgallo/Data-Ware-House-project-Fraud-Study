"""Create and populate the star-schema data warehouse from the reconciled SQLite DB.
Usage: python src/03_etl_to_star.py --reconciled reconciled.db --dw fraud_dw.db
"""
import argparse, sqlite3
from pathlib import Path

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--reconciled', required=True)
    ap.add_argument('--dw', required=True)
    ap.add_argument('--schema', default='sql/02_star_schema.sql')
    args = ap.parse_args()

    dw = sqlite3.connect(args.dw)
    dw.executescript(Path(args.schema).read_text())
    dw.execute("ATTACH DATABASE ? AS r", (args.reconciled,))

    dw.executescript('''
    INSERT INTO dim_time(time_key, step, day_number, hour_of_day, week_number, day_phase)
    SELECT step, step,
           ((step - 1) / 24) + 1 AS day_number,
           ((step - 1) % 24) AS hour_of_day,
           ((step - 1) / 168) + 1 AS week_number,
           CASE WHEN ((step - 1) % 24) BETWEEN 6 AND 11 THEN 'MORNING'
                WHEN ((step - 1) % 24) BETWEEN 12 AND 17 THEN 'AFTERNOON'
                WHEN ((step - 1) % 24) BETWEEN 18 AND 22 THEN 'EVENING'
                ELSE 'NIGHT' END AS day_phase
    FROM (SELECT DISTINCT step FROM r.transaction_clean);

    INSERT INTO dim_transaction_type(transaction_type_key, type_name, flow_family)
    SELECT type_id, type_name,
           CASE WHEN type_name IN ('TRANSFER','CASH_OUT') THEN 'HIGH_RISK_FLOW'
                WHEN type_name IN ('PAYMENT','DEBIT') THEN 'PAYMENT_FLOW'
                WHEN type_name = 'CASH_IN' THEN 'INCOMING_FLOW'
                ELSE 'OTHER' END
    FROM r.transaction_type;

    INSERT INTO dim_origin_account(origin_account_key, account_code, account_category)
    SELECT account_id, account_code, account_category FROM r.account;

    INSERT INTO dim_destination_account(destination_account_key, account_code, account_category)
    SELECT account_id, account_code, account_category FROM r.account;

    INSERT INTO dim_fraud_status(fraud_status_key, is_fraud, is_flagged_fraud, fraud_label, flag_label)
    VALUES (1,0,0,'Legitimate','Not flagged'),
           (2,1,0,'Fraud','Not flagged'),
           (3,0,1,'Legitimate','Flagged'),
           (4,1,1,'Fraud','Flagged');

    INSERT INTO fact_transaction(
        transaction_key, time_key, transaction_type_key, origin_account_key, destination_account_key,
        fraud_status_key, transaction_count, amount, origin_old_balance, origin_new_balance,
        destination_old_balance, destination_new_balance, origin_balance_delta, destination_balance_delta,
        origin_balance_error, destination_balance_error, fraud_count, flagged_fraud_count
    )
    SELECT t.transaction_id, t.step, t.type_id, t.origin_account_id, t.destination_account_id,
           fs.fraud_status_key, 1, t.amount, t.oldbalance_org, t.newbalance_orig,
           t.oldbalance_dest, t.newbalance_dest, t.origin_balance_delta, t.destination_balance_delta,
           t.origin_balance_error, t.destination_balance_error, t.is_fraud, t.is_flagged_fraud
    FROM r.transaction_clean t
    JOIN dim_fraud_status fs ON fs.is_fraud=t.is_fraud AND fs.is_flagged_fraud=t.is_flagged_fraud;
    ''')
    dw.commit()
    dw.close()

if __name__ == '__main__':
    main()
