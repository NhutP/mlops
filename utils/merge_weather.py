import os
import pandas as pd

# Directory where your 16 CSV files are stored
data_dir = "/mnt/c/Users/quang/Desktop/project/stuff/rossmann-store-sales/weather"  # Replace with your actual path

# Mapping rules for state name to abbreviation
state_map = {
    'BadenWuerttemberg': 'BW', 
    'Bayern': 'BY',
    'Berlin': 'BE',
    'Brandenburg': 'BB',  # Not used in store_state
    'Bremen': 'HB',  # Will be merged under Niedersachsen (HB,NI)
    'Hamburg': 'HH',
    'Hessen': 'HE',
    'MecklenburgVorpommern': 'MV',  # Not used in store_state
    'Niedersachsen': 'HB,NI',  # Covers Bremen
    'NordrheinWestfalen': 'NW',
    'RheinlandPfalz': 'RP',
    'Saarland': 'SL',
    'Sachsen': 'SN',
    'SachsenAnhalt': 'ST',
    'SchleswigHolstein': 'SH',
    'Thueringen': 'TH'
}

# Initialize list to collect all dataframes
df_list = []

# Iterate over all .csv files
for filename in os.listdir(data_dir):
    if filename.endswith(".csv"):
        state_name = filename.replace(".csv", "")
        
        # Skip Brandenburg and MecklenburgVorpommern as specified
        if state_name in ['Brandenburg', 'MecklenburgVorpommern']:
            continue
        
        # Treat Bremen as Niedersachsen
        if state_name == 'Bremen':
            state_name = 'Niedersachsen'
        
        filepath = os.path.join(data_dir, filename)
        df = pd.read_csv(filepath)
        
        # Add 'state' column using the mapping
        df['state'] = state_map[state_name]
        df_list.append(df)

# Merge all dataframes
merged_weather_df = pd.concat(df_list, ignore_index=True)

# Save to CSV
merged_weather_df.to_csv("/mnt/c/Users/quang/Desktop/project/stuff/rossmann-store-sales/merged_weather_with_state.csv", index=False)

print("✅ Merged weather dataset saved as 'merged_weather_with_state.csv'")
