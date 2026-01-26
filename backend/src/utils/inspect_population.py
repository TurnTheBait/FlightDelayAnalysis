import pandas as pd

CSV_PATH = "backend/data/raw/population_data.csv"

def inspect():
    print("Loading CSV...")
    df = pd.read_csv(CSV_PATH)
    
    print("Columns:", df.columns.tolist())
    
    df_pop = df[df['indic_ur'] == 'DE1001V']
    
    print(f"\nTotal rows for DE1001V: {len(df_pop)}")
    
    print(f"Years available: {sorted(df_pop['TIME_PERIOD'].unique())}")
    
    latest_year = df_pop['TIME_PERIOD'].max()
    print(f"\nLatest year: {latest_year}")
    
    df_latest = df_pop[df_pop['TIME_PERIOD'] == latest_year]
    
    print("\nSample entries from latest year:")
    print(df_latest[['cities', 'Geopolitical entity (declaring)', 'OBS_VALUE']].head(10))
    
    print("\nUnique Geopolitical entities (sample):")
    print(df_pop['Geopolitical entity (declaring)'].unique()[:10])
    print("\nUnique Geopolitical entities (sample):")
    print(df_pop['Geopolitical entity (declaring)'].unique()[:10])
    
    df_cities = df_pop[df_pop['cities'].str.len() > 2]
    print(f"\nRows with city code length > 2: {len(df_cities)}")
    if not df_cities.empty:
         print(df_cities[['cities', 'Geopolitical entity (declaring)', 'OBS_VALUE']].head())

if __name__ == "__main__":
    inspect()
