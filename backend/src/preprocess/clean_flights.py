import os
import pandas as pd
from pathlib import Path

RAW_FLIGHTS = Path("backend/data/raw/flights")
RAW_AIRPORTS = Path("backend/data/raw/airports/airports.csv")
WEATHER_DIR = Path("backend/data/raw/weather")

OUTPUT_DIR = Path("backend/data/processed/flights_filtered")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

OUTPUT_FILE = OUTPUT_DIR / "flight_list_filtered_2024.csv"

COLUMNS_TO_DROP = ["ades_p", "adep_p", "version"]

def load_weather_airports():
    
    return {
        file.stem.upper()
        for file in WEATHER_DIR.glob("*.parquet")
        if file.is_file()
    }

def load_european_airports():

    df_air = pd.read_csv(RAW_AIRPORTS)

    df_air = df_air[
        (df_air["type"] == "large_airport") &
        (df_air["continent"] == "EU")
    ]

    return df_air[["ident", "name", "continent"]].rename(columns={"ident": "icao"})

def filter_and_merge_flights():
    
    european_airports = load_european_airports()
    valid_icao_eu = set(european_airports["icao"].unique())

    weather_airports = load_weather_airports()
    print(f"Meteo disponibili per: {len(weather_airports)} aeroporti")

    valid_icao = valid_icao_eu & weather_airports
    print(f"ICAO utilizzabili dopo filtro meteo: {len(valid_icao)}")

    all_flights = []

    for file in RAW_FLIGHTS.glob("flight_list_2024*.parquet"):
        print(f"Loading {file}...")
        df = pd.read_parquet(file)

        required = {"adep", "ades"}
        missing = required - set(df.columns)
        if missing:
            raise ValueError(f"Missing columns in {file}: {missing}")

        df = df[(df["adep"].notna()) & (df["ades"].notna())]

        df = df[df["adep"].isin(valid_icao) & df["ades"].isin(valid_icao)]

        df = df.drop(columns=[c for c in COLUMNS_TO_DROP if c in df.columns])

        all_flights.append(df)

    if not all_flights:
        raise RuntimeError("No flights loaded for 2024.")

    df_all = pd.concat(all_flights, ignore_index=True)
    print(f"Total flights after filtering: {len(df_all)}")

    df_all.to_csv(OUTPUT_FILE, index=False)
    print(f"Saved merged file → {OUTPUT_FILE}")

if __name__ == "__main__":
    filter_and_merge_flights()