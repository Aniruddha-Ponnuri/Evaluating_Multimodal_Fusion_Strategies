import pandas as pd
import ast

# Load the CSV
df = pd.read_csv("sensor_data.csv")

# Helper to safely parse stringified dictionaries
def parse_dict_column(series):
    return series.apply(lambda x: ast.literal_eval(x) if isinstance(x, str) else {})

# Parse and expand the nested fields
moisture_df = parse_dict_column(df['moisture']).apply(pd.Series).add_prefix('moisture_')
ph_df = parse_dict_column(df['ph_sensor']).apply(pd.Series).add_prefix('ph_')
npk_df = parse_dict_column(df['npk_sensor']).apply(pd.Series).add_prefix('npk_')

# Combine all into one DataFrame
df_flat = pd.concat([
    df['timestamp'],
    moisture_df,
    ph_df,
    npk_df,
    df['image_filename']
], axis=1)

# Save to new CSV
df_flat.to_csv("sensor_data_cleaned.csv", index=False)
print("✅ Cleaned data saved as sensor_data_cleaned.csv")
