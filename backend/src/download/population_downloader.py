import pandas as pd
import os
import requests
import gzip
import shutil

CURRENT_FILE = os.path.abspath(__file__)
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(CURRENT_FILE)))
RAW_DATA_DIR = os.path.join(BASE_DIR, 'data', 'raw')
PROCESSED_DATA_DIR = os.path.join(BASE_DIR, 'data', 'processed', 'population')
RAW_FILE_PATH = os.path.join(RAW_DATA_DIR, 'population_data.csv')
RAW_GZ_PATH = os.path.join(RAW_DATA_DIR, 'population_data.csv.gz')
OUTPUT_FILE_PATH = os.path.join(PROCESSED_DATA_DIR, 'city_population.csv')

EUROSTAT_URL = "https://ec.europa.eu/eurostat/api/dissemination/sdmx/3.0/data/dataflow/ESTAT/urb_cpop1/1.0?compress=true&format=csvdata&formatVersion=2.0&lang=en&labels=name"

def download_data():
    if os.path.exists(RAW_FILE_PATH):
        print(f"Raw file already exists at {RAW_FILE_PATH}")
        return

    print("Downloading population data from Eurostat...")
    try:
        response = requests.get(EUROSTAT_URL, stream=True)
        if response.status_code == 200:
            with open(RAW_GZ_PATH, 'wb') as f:
                f.write(response.content)
            print("Download complete. Decompressing...")
            
            with gzip.open(RAW_GZ_PATH, 'rb') as f_in:
                with open(RAW_FILE_PATH, 'wb') as f_out:
                    shutil.copyfileobj(f_in, f_out)    
            os.remove(RAW_GZ_PATH)
            print("Decompression complete.")
        else:
            print(f"Failed to download data. Status code: {response.status_code}")
    except Exception as e:
        print(f"Error downloading data: {e}")

def process_data():
    if not os.path.exists(RAW_FILE_PATH):
        print("Raw data file not found.")
        return

    print("Loading data...")
    df = pd.read_csv(RAW_FILE_PATH)
    
    df = df[df['indic_ur'] == 'DE1001V']
    
    df = df[df['cities'].str.len() > 2]
    
    df['OBS_VALUE'] = pd.to_numeric(df['OBS_VALUE'], errors='coerce')
    df = df.dropna(subset=['OBS_VALUE'])

    print(f"Found {len(df)} population records for cities.")
    
    df = df.sort_values(by=['cities', 'TIME_PERIOD'], ascending=[True, False])
    df_latest = df.drop_duplicates(subset=['cities'], keep='first')
    
    print(f"Unique cities found: {len(df_latest)}")
    
    def clean_name(name):
        if pd.isna(name): return ""
        n = str(name)
        n = n.replace("(greater city)", "")
        n = n.replace(" (greater city)", "")
        n = n.replace(" greater city", "")
        return n.strip()
        
    df_latest['city_name_clean'] = df_latest['Geopolitical entity (declaring)'].apply(clean_name)
    
    final_df = df_latest[['cities', 'city_name_clean', 'OBS_VALUE', 'TIME_PERIOD']]
    final_df.columns = ['city_code', 'city_name', 'population', 'year']
    
    os.makedirs(PROCESSED_DATA_DIR, exist_ok=True)
    final_df.to_csv(OUTPUT_FILE_PATH, index=False)
    print(f"Saved processed data to {OUTPUT_FILE_PATH}")
    print(final_df.head())

if __name__ == "__main__":
    download_data()
    process_data()
