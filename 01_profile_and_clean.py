"""Profile and clean the fraud CSV before loading it.
Usage: python src/01_profile_and_clean.py --input Fraud.csv --output cleaned_fraud.csv --profile docs/profile_summary.json
"""
import argparse, json
import pandas as pd

EXPECTED_COLUMNS = [
    'step','type','amount','nameOrig','oldbalanceOrg','newbalanceOrig',
    'nameDest','oldbalanceDest','newbalanceDest','isFraud','isFlaggedFraud'
]

def account_category(code: str) -> str:
    if isinstance(code, str) and code.startswith('C'):
        return 'CUSTOMER'
    if isinstance(code, str) and code.startswith('M'):
        return 'MERCHANT'
    return 'UNKNOWN'

def amount_band(x: float) -> str:
    if x < 1000: return '0-999'
    if x < 10000: return '1k-9.9k'
    if x < 100000: return '10k-99.9k'
    if x < 1000000: return '100k-999.9k'
    return '1M+'

def clean_chunk(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    df.columns = [c.strip() for c in df.columns]
    if list(df.columns) != EXPECTED_COLUMNS:
        raise ValueError(f'Unexpected columns: {list(df.columns)}')

    # Standardization
    df['type'] = df['type'].str.strip().str.upper()
    df['nameOrig'] = df['nameOrig'].str.strip()
    df['nameDest'] = df['nameDest'].str.strip()

    # Type enforcement
    int_cols = ['step','isFraud','isFlaggedFraud']
    num_cols = ['amount','oldbalanceOrg','newbalanceOrig','oldbalanceDest','newbalanceDest']
    for c in int_cols:
        df[c] = pd.to_numeric(df[c], errors='coerce').astype('Int64')
    for c in num_cols:
        df[c] = pd.to_numeric(df[c], errors='coerce')

    # Derived quality attributes
    df['origin_balance_delta'] = df['oldbalanceOrg'] - df['newbalanceOrig']
    df['destination_balance_delta'] = df['newbalanceDest'] - df['oldbalanceDest']
    df['origin_balance_error'] = df['origin_balance_delta'] - df['amount']
    df['destination_balance_error'] = df['destination_balance_delta'] - df['amount']
    df['amount_band'] = df['amount'].map(amount_band)
    df['origin_account_category'] = df['nameOrig'].map(account_category)
    df['destination_account_category'] = df['nameDest'].map(account_category)

    invalid = (
        df[EXPECTED_COLUMNS].isna().any(axis=1) |
        (df['step'] < 1) |
        (df['amount'] < 0) |
        (~df['isFraud'].isin([0,1])) |
        (~df['isFlaggedFraud'].isin([0,1])) |
        (df[['oldbalanceOrg','newbalanceOrig','oldbalanceDest','newbalanceDest']] < 0).any(axis=1)
    )
    df['quality_status'] = invalid.map({True: 'REJECT', False: 'ACCEPT'})
    return df

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--input', required=True)
    ap.add_argument('--output', required=True)
    ap.add_argument('--profile', required=True)
    ap.add_argument('--chunksize', type=int, default=500_000)
    args = ap.parse_args()

    profile = {'rows': 0, 'rejected_rows': 0, 'type_counts': {}, 'fraud_counts': {}, 'flag_counts': {}}
    first = True
    for chunk in pd.read_csv(args.input, chunksize=args.chunksize):
        clean = clean_chunk(chunk)
        profile['rows'] += len(clean)
        profile['rejected_rows'] += int((clean['quality_status'] == 'REJECT').sum())
        for key, val in clean['type'].value_counts().items():
            profile['type_counts'][key] = profile['type_counts'].get(key, 0) + int(val)
        for key, val in clean['isFraud'].value_counts().items():
            profile['fraud_counts'][str(int(key))] = profile['fraud_counts'].get(str(int(key)), 0) + int(val)
        for key, val in clean['isFlaggedFraud'].value_counts().items():
            profile['flag_counts'][str(int(key))] = profile['flag_counts'].get(str(int(key)), 0) + int(val)
        clean.to_csv(args.output, index=False, mode='w' if first else 'a', header=first)
        first = False

    with open(args.profile, 'w') as f:
        json.dump(profile, f, indent=2)

if __name__ == '__main__':
    main()
