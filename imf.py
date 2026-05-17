import pandas as pd
import os

# ==============================================================================
# 1. STRUCTURAL SOURCE SEPARATION MAPPINGS
# ==============================================================================

# Indicators whose ultimate source/authority is traditionally the IMF
imf_proxy_mapping = {
    'forex_reserves_usd_bn':  ('IND_FOREX_RESERVES_USD_BN', 'Foreign exchange reserves (Billion US$)'),
    'policy_rate_pct':        ('IND_POLICY_RATE_PCT',       'Central bank policy rate (%)'),
    'exports_usd_bn':         ('IND_EXPORTS_USD_BN',        'Exports of goods and services (Billion US$)'),
    'imports_usd_bn':         ('IND_IMPORTS_USD_BN',        'Imports of goods and services (Billion US$)'),
    'trade_balance_usd_bn':   ('IND_TRADE_BALANCE_USD_BN',  'Trade balance (Billion US$)'),
    'current_account_usd_bn': ('IND_CURRENT_ACCOUNT_USD_BN', 'Current account balance (Billion US$)'),
    'public_debt_gdp_pct':    ('IND_PUBLIC_DEBT_GDP_PCT',   'Public debt (% of GDP)'),
    'imf_program_active':     ('IND_IMF_PROGRAM_ACTIVE',    'IMF program active flag (1=Active, 0=Inactive)')
}

# General economic and social indicators tracked by other national/global bodies
kaggle_other_mapping = {
    'gdp_growth_pct':         ('IND_GDP_GROWTH_PCT',        'GDP growth (annual %)'),
    'unemployment_pct':       ('IND_UNEMPLOYMENT_PCT',      'Unemployment, total (% of total labor force)'),
    'literacy_rate_pct':      ('IND_LITERACY_RATE_PCT',     'Literacy rate, adult total (% of people ages 15+)'),
    'services_gdp_pct':       ('IND_SERVICES_GDP_PCT',      'Services, value added (% of GDP)'),
    'tax_revenue_gdp_pct':    ('IND_TAX_REVENUE_GDP_PCT',   'Tax revenue (% of GDP)'),
    'mobile_per_100':         ('IND_MOBILE_PER_100',        'Mobile cellular subscriptions (per 100 people)'),
    'exports_gdp_pct':        ('IND_EXPORTS_GDP_PCT',       'Exports of goods and services (% of GDP)'),
    'imports_gdp_pct':        ('IND_IMPORTS_GDP_PCT',       'Imports of goods and services (% of GDP)')
}

input_filename = "pakistan_economic_indicators_2000_2025.csv"
imf_output_file = "FACT_ECONOMIC_MEASUREMENT_IMF_PROXY.csv"
kaggle_output_file = "FACT_ECONOMIC_MEASUREMENT_KAGGLE_OTHER.csv"

# Strict column order definition to match your database star schema layout
final_columns = [
    'DIM_INDICATOR_id', 
    'DIM_INDICATOR_name', 
    'DIM_TIME_year', 
    'DIM_TIME_month', 
    'DIM_LOCATION_id', 
    'DIM_SOURCE_id', 
    'FACT_value'
]

# ==============================================================================
# 2. RUN PIPELINE
# ==============================================================================
print("--- STARTING KAGGLE FIXED DUAL-FILE SEPARATION PIPELINE ---")
print(f"Reading Base Data: {input_filename}\n")

if not os.path.exists(input_filename):
    print(f"[!] ERROR: '{input_filename}' not found. Verify file placement.")
else:
    try:
        # Load raw dataset
        df_raw = pd.read_csv(input_filename)
        
        imf_rows = []
        kaggle_rows = []
        
        # 3. TRANSFORM AND ROUTE DATA POINTS
        for index, row in df_raw.iterrows():
            try:
                year = int(row['year'])
                month = 12 # Default to December for annual tracking consistency
            except Exception:
                continue # Skip corrupted rows safely
            
            # Route to the IMF Proxy Collection
            for kag_col, (master_id, master_name) in imf_proxy_mapping.items():
                if kag_col in row and not pd.isna(row[kag_col]):
                    try:
                        val = float(str(row[kag_col]).replace(',', ''))
                        imf_rows.append({
                            'DIM_INDICATOR_id': master_id,
                            'DIM_INDICATOR_name': master_name,
                            'DIM_TIME_year': year,
                            'DIM_TIME_month': month,
                            'DIM_LOCATION_id': 'PAK',
                            'DIM_SOURCE_id': 'IMF_VIA_KAGGLE', # Clear data attribution
                            'FACT_value': val
                        })
                    except ValueError:
                        continue

            # Route to the Kaggle General Collection (FIXED VARIABLE NAME HERE)
            for kag_col, (master_id, master_name) in kaggle_other_mapping.items():
                if kag_col in row and not pd.isna(row[kag_col]):
                    try:
                        val = float(str(row[kag_col]).replace(',', ''))
                        kaggle_rows.append({
                            'DIM_INDICATOR_id': master_id,
                            'DIM_INDICATOR_name': master_name,
                            'DIM_TIME_year': year,
                            'DIM_TIME_month': month,
                            'DIM_LOCATION_id': 'PAK',
                            'DIM_SOURCE_id': 'KAGGLE_PAK_ECONOMY',
                            'FACT_value': val
                        })
                    except ValueError:
                        continue

        # 4. LOAD & EXPORT FILE 1: IMF PROXY DATA
        if imf_rows:
            df_imf = pd.DataFrame(imf_rows)[final_columns]
            df_imf = df_imf.sort_values(by=['DIM_INDICATOR_id', 'DIM_TIME_year'])
            df_imf.to_csv(imf_output_file, index=False)
            print(f"[PASS] Saved IMF-derived indicators to: {imf_output_file}")
            print(f"       Total Records: {len(df_imf)} | Unique Indicators: {df_imf['DIM_INDICATOR_id'].nunique()}")
        else:
            print("[Warning] No rows generated for the IMF proxy collection.")

        # 5. LOAD & EXPORT FILE 2: KAGGLE OTHER DATA
        if kaggle_rows:
            df_kag = pd.DataFrame(kaggle_rows)[final_columns]
            df_kag = df_kag.sort_values(by=['DIM_INDICATOR_id', 'DIM_TIME_year'])
            df_kag.to_csv(kaggle_output_file, index=False)
            print(f"[PASS] Saved General Kaggle indicators to: {kaggle_output_file}")
            print(f"       Total Records: {len(df_kag)} | Unique Indicators: {df_kag['DIM_INDICATOR_id'].nunique()}")
        else:
            print("[Warning] No rows generated for the general Kaggle collection.")
            
        print("\n--- PIPELINE EXECUTION COMPLETE ---")
        
        if imf_rows:
            print(f"\nPreview of IMF Proxy File ({imf_output_file}):")
            print(df_imf.head(5))
            
        if kaggle_rows:
            print(f"\nPreview of Kaggle General File ({kaggle_output_file}):")
            print(df_kag.head(5))

    except Exception as e:
        print(f"\n[!] Critical Ingestion Error: {e}")