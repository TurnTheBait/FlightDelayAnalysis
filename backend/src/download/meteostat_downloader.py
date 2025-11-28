import os
import pandas as pd
from datetime import datetime
from meteostat import Hourly, Stations

CURRENT_FILE = os.path.abspath(__file__)
SCRIPTS_DIR = os.path.dirname(CURRENT_FILE)
PROJECT_ROOT = os.path.abspath(os.path.join(SCRIPTS_DIR, "..", ".."))

AIRPORT_CSV_PATH = os.path.join(PROJECT_ROOT, "data", "raw", "airports", "airports.csv")
WEATHER_OUTPUT_DIR = os.path.join(PROJECT_ROOT, "data", "raw", "weather")

os.makedirs(WEATHER_OUTPUT_DIR, exist_ok=True)

def load_european_large_airports():
    df = pd.read_csv(AIRPORT_CSV_PATH)

    df = df[
        (df["type"] == "large_airport") &
        (df["continent"] == "EU") &
        (df["latitude_deg"].notna()) &
        (df["longitude_deg"].notna())
    ]

    print(f"Found {len(df)} large European airports")
    return df

def get_nearest_meteostat_station(lat: float, lon: float):
    try:
        stations = Stations()
        stations = stations.nearby(lat, lon)
        station = stations.fetch(1)

        if len(station) == 0:
            return None

        return station.index[0]  # Meteostat station ID
    except Exception:
        return None

def download_weather(station_id: str, start: datetime, end: datetime):
    try:
        data = Hourly(station_id, start, end).fetch()
        return data
    except Exception:
        return None

def main():

    airports = load_european_large_airports()

    start = datetime(2023, 1, 1)
    end = datetime(2024, 12, 31, 23, 59)

    for _, row in airports.iterrows():
        name = row["name"]
        ident = row["ident"]
        lat = row["latitude_deg"]
        lon = row["longitude_deg"]

        output_file = os.path.join(WEATHER_OUTPUT_DIR, f"{ident}.parquet")

        if os.path.exists(output_file):
            print(f"✔ Skipping {ident}, already downloaded")
            continue

        print(f"\n🌤 Processing airport {name} ({ident})")

        station_id = get_nearest_meteostat_station(lat, lon)

        if station_id is None:
            print(f"⚠ No Meteostat station found for {ident}")
            continue

        print(f"📡 Using nearest Meteostat station → {station_id}")

        weather = download_weather(station_id, start, end)

        if weather is None or weather.empty:
            print(f"⚠ No weather data for {ident}")
            continue

        weather.to_parquet(output_file)
        print(f"✔ Saved → {output_file}")

if __name__ == "__main__":
    main()
