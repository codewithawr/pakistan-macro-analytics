import wbgapi as wb
import pandas as pd

# 1. THE MAPPING DICTIONARY
# This maps the specific WDI API Code to OUR Master Internal Keys
# Format: 'WDI_Code': ('Master_Indicator_ID', 'Master_Indicator_Name')
master_mapping = {
    'NY.GDP.MKTP.CD':       ('IND_GDP_USD',         'GDP (current US$)'),
    'FP.CPI.TOTL.ZG':       ('IND_INFLATION_CPI',   'Inflation, consumer prices (%)'),
    'PA.NUS.FCRF':          ('IND_EXCHANGE_RATE',   'Official exchange rate (LCU per US$)'),
    'NV.AGR.TOTL.ZS':       ('IND_AGRI_PCT_GDP',    'Agriculture, value added (% GDP)'),
    'NV.IND.TOTL.ZS':       ('IND_IND_PCT_GDP',     'Industry, value added (% GDP)'),
    'BX.TRF.PWKR.CD.DT':    ('IND_REMITTANCES_USD', 'Personal remittances (US$)'),
    'SP.POP.TOTL':          ('IND_POP_TOTAL',       'Population, total'),
    'SL.TLF.TOTL.IN':       ('IND_LABOR_TOTAL',     'Labor force, total'),
    'BX.KLT.DINV.CD.WD':    ('IND_FDI_USD',         'FDI, net inflows (current US$)'),
    'BX.KLT.DINV.WD.GD.ZS': ('IND_FDI_PCT_GDP',     'FDI, net inflows (% of GDP)')
}

# Extract just the WDI codes to pass to the API
wdi_codes = list(master_mapping.keys())

print("Fetching standardized data from World Bank API...")
# We use 'PAK' here because WDI natively accepts it, but we will hardcode
# 'PAK' later to ensure it doesn't change based on the API's whim.
raw_data = wb.data.DataFrame(wdi_codes, 'PAK', time=range(2000, 2024))

# 2. THE TRANSFORMATION PHASE
# Reshape the data
fact_table = raw_data.reset_index().melt(
    id_vars=['series'], 
    var_name='DIM_TIME_year', 
    value_name='FACT_value'
)

# Clean the year (WDI returns 'YR2000' -> '2000')
fact_table['DIM_TIME_year'] = fact_table['DIM_TIME_year'].str.replace('YR', '').astype(int)

# 3. APPLYING THE MASTER CONVENTIONS
# Map the raw 'series' code to our standardized ID and Name
fact_table['DIM_INDICATOR_id'] = fact_table['series'].apply(lambda x: master_mapping[x][0])
fact_table['DIM_INDICATOR_name'] = fact_table['series'].apply(lambda x: master_mapping[x][1])

# Drop the old, API-specific column
fact_table.drop(columns=['series'], inplace=True)

# Enforce Master Location and Source Keys
fact_table['DIM_LOCATION_id'] = 'PAK'
fact_table['DIM_SOURCE_id'] = 'WorldBank_WDI'

# Clean up the data (drop nulls and sort for a clean file)
fact_table = fact_table.dropna(subset=['FACT_value'])
fact_table = fact_table.sort_values(by=['DIM_INDICATOR_id', 'DIM_TIME_year'])

# Reorder columns to match the Snowflake schema logically
final_columns = [
    'DIM_INDICATOR_id', 
    'DIM_INDICATOR_name',
    'DIM_TIME_year', 
    'DIM_LOCATION_id', 
    'DIM_SOURCE_id', 
    'FACT_value'
]
fact_table = fact_table[final_columns]

# 4. LOAD
csv_filename = "FACT_ECONOMIC_MEASUREMENT_WDI.csv"
fact_table.to_csv(csv_filename, index=False)

print(f"\nExtraction complete! Saved to {csv_filename}")
print("\n--- Standardized Fact Table Preview ---")
print(fact_table.head())