import os
import pandas as pd
from datetime import datetime
from meteostat import Hourly, Stations

CURRENT_FILE = os.path.abspath(__file__)
SCRIPTS_DIR = os.path.dirname(CURRENT_FILE)
PROJECT_ROOT = os.path.abspath(os.path.join(SCRIPTS_DIR, "..", ".."))

AIRPORT_CSV_PATH = os.path.join(PROJECT_ROOT, "data", "processed", "airports", "airports_filtered.csv")
WEATHER_OUTPUT_DIR = os.path.join(PROJECT_ROOT, "data", "raw", "weather")

os.makedirs(WEATHER_OUTPUT_DIR, exist_ok=True)

def get_best_meteostat_stations(ident: str, lat: float, lon: float):
    stns = Stations()
    nearby_stations = stns.nearby(lat, lon).fetch(5)
    
    if nearby_stations.empty:
        return []
        
    station_ids = []
    
    icao_matches = nearby_stations[nearby_stations['icao'] == ident]
    if not icao_matches.empty:
        station_ids.append(icao_matches.index[0])
        
    for sid in nearby_stations.index:
        if sid not in station_ids:
            station_ids.append(sid)
            
    return station_ids

def download_weather(station_id: str, start: datetime, end: datetime):
    try:
        data = Hourly(station_id, start, end)
        return data.fetch()
    except Exception as e:
        print(f"Error downloading weather for {station_id}: {e}")
        return None

def main():
    airports = pd.read_csv(AIRPORT_CSV_PATH)

    start = datetime(2015, 1, 1, 0, 0)
    end = datetime.now()

    for _, row in airports.iterrows():
        name = row["name"]
        ident = row["ident"]
        lat = row["latitude_deg"]
        lon = row["longitude_deg"]

        output_file = os.path.join(WEATHER_OUTPUT_DIR, f"{ident}.parquet")

        if os.path.exists(output_file):
            print(f"Skipping {ident}, already downloaded")
            continue

        print(f"\nProcessing airport {name} ({ident})")

        station_ids = get_best_meteostat_stations(ident, lat, lon)

        if not station_ids:
            print(f"No Meteostat stations found for {ident}")
            continue

        weather = None
        used_station = None

        for sid in station_ids:
            print(f"Trying Meteostat station -> {sid}")
            w = download_weather(sid, start, end)
            
            if w is not None and not w.empty:
                weather = w
                used_station = sid
                break
            else:
                print(f"Station {sid} returned no data, trying next...")

        if weather is None or weather.empty:
            print(f"No weather data found for {ident} across all nearby stations")
            continue

        weather.to_parquet(output_file)
        print(f"Saved -> {output_file} (using station {used_station})")

if __name__ == "__main__":
    main()