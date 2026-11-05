Clinical Benefits and Denials Management - Capstone
Analyzes pharmacy claims data to identify denial and payment trends.

Input:  CSV file with pharmacy claims records
Output: Cleaned dataset + summary reports (console + CSV)


import pandas as pd
import numpy as np

# ------------------------------------------------------------------
# 1. LOAD DATA
# ------------------------------------------------------------------
def load_claims(filepath: str) -> pd.DataFrame:
    """Load pharmacy claims data from CSV."""
    df = pd.read_csv(filepath)
    print(f"Loaded {len(df):,} claim records from {filepath}")
    return df

# ------------------------------------------------------------------
# 2. STANDARDIZE FIELDS
# ------------------------------------------------------------------
def standardize_fields(df: pd.DataFrame) -> pd.DataFrame:
    """Standardize payer, provider, and NDC fields for consistent reporting."""
    # Payer: uppercase + strip whitespace for consistent grouping
    if 'payer' in df.columns:
        df['payer'] = df['payer'].str.upper().str.strip()

    # Provider: uppercase + strip whitespace
    if 'provider' in df.columns:
        df['provider'] = df['provider'].str.upper().str.strip()

    # NDC: normalize to 11-digit format (strip dashes, zero-pad)
    if 'ndc' in df.columns:
        df['ndc'] = (df['ndc']
                     .astype(str)
                     .str.replace('-', '', regex=False)
                     .str.zfill(11))

    # Standardize denial status values
    if 'claim_status' in df.columns:
        df['claim_status'] = (df['claim_status']
                              .str.upper()
                              .str.strip()
                              .replace({'DENIED': 'DENIED',
                                        'REJECTED': 'DENIED',
                                        'PAID': 'PAID',
                                        'APPROVED': 'PAID'}))

    print("Standardized payer, provider, NDC, and claim status fields.")
    return df

# ------------------------------------------------------------------
# 3. CLEAN DATA (duplicates & nulls)
# ------------------------------------------------------------------
def clean_data(df: pd.DataFrame) -> pd.DataFrame:
    """Remove duplicates and handle null records."""
    before = len(df)

    # Drop exact duplicate rows
    df = df.drop_duplicates()

    # Drop rows missing critical fields (claim id, ndc, amount)
    critical_cols = [c for c in ['claim_id', 'ndc', 'claim_amount'] if c in df.columns]
    if critical_cols:
        df = df.dropna(subset=critical_cols)

    # Fill remaining nulls with placeholders where safe
    df = dffillna({'denial_reason': 'UNKNOWN',
                    'denial_code': 'N/A'})

    removed = before - len(df)
    print(f"Removed {removed:,} duplicate/null records ({removed/before:.1%} of data).")
    return df

# ------------------------------------------------------------------
# 4. ANALYSIS
# ------------------------------------------------------------------
def analyze_denials(df: pd.DataFrame) -> pd.DataFrame:
    """ Summarize denial rates and top denial reasons by payer."""
    if 'claim_status' not in df.columns:
        print("No claim_status column found - skipping denial analysis.")
        return pd.DataFrame()

    # Overall denial rate
    denial_rate = (df['claim_status'] == 'DENIED').mean()
    print(f"\nOverall denial rate: {denial_rate:.1%}")

    # Denial rate by payer
    by_payer = (df.groupby('payer')['claim_status']
                .apply(lambda s: (s == 'DENIED').mean())
                .sort_values(ascending=False)
                .reset_index())
    by_payer.columns = ['payer', 'denial_rate']
    print("\nDenial rate by payer (top 5):")
    print(by_payer.head().to_string(index=False))

    # Top denial reasons
    if 'denial_reason' in df.columns:
        denied = df[df['claim_status'] == 'DENIED']
        top_reasons = (denied['denial_reason']
                       .value_counts()
                       .head(10)
                       .reset_index())
        top_reasons.columns = ['denial_reason', 'count']
        print("\nTop 10 denial reasons:")
        print(top_reasons.to_string(index=False))

    return by_payer

def analyze_payments(df: pd.DataFrame) -> pd.DataFrame:
    """ Summarize payment trends by month."""
    if 'paid_amount' not in df.columns or 'service_date' not in df.columns:
        print("No paid_amount/service_date columns found - skipping payment analysis.")
        return pd.DataFrame()

    df['service_date'] = pd.to_datetime(df['service_date'], errors='coerce')
    df['month'] = df['service_date'].dt.to_period('M')

    monthly = (df.groupby('month')['paid_amount']
               .agg(['sum', 'count', 'mean'])
               .reset_index())
    monthly.columns = ['month', 'total_paid', 'claim_count', 'avg_payment']
    print("\nMonthly payment trends:")
    print(monthly.to_string(index=False))
    return monthly

# ------------------------------------------------------------------
# 5. EXPORT
# ------------------------------------------------------------------
def export_results(df: pd.DataFrame, output_path: str = "cleaned_claims.csv"):
    """Save the cleaned dataset for downstream reporting."""
    df.to_csv(output_path, index=False)
    print(f"\nCleaned dataset saved to: {output_path}")

# ------------------------------------------------------------------
# MAIN
# ------------------------------------------------------------------
def main():
    # Update this path to your actual claims data file
    filepath = "pharmacy_claims.csv"

    df = load_claims(filepath)
    df = standardize_fields(df)
    df = clean_data(df)

    denial_summary = analyze_denials(df)
    payment_summary = analyze_payments(df)

    export_results(df)

if __name__ == "__main__":
    main()
