import pandas as pd
import glob
import os
from pathlib import Path

def load_airports_mapping(airports_file):
    print(f"Loading airport mapping from {airports_file}...")
    df = pd.read_csv(airports_file)
    if 'iata_code' not in df.columns or 'icao_code' not in df.columns:
        raise ValueError("Airports file must contain 'iata_code' and 'icao_code' columns.")
    
    mapping = df.set_index('iata_code')['icao_code'].to_dict()
    print(f"Loaded {len(mapping)} airport mappings.")
    return mapping

def load_weather_data(weather_dir):
    print(f"Loading weather data from {weather_dir}...")
    weather_files = glob.glob(os.path.join(weather_dir, "*.parquet"))
    
    weather_dfs = []
    for f in weather_files:
        icao = Path(f).stem
        try:
            df = pd.read_parquet(f)
            if 'time' in df.columns:
                df['time'] = pd.to_datetime(df['time'])
                df = df.set_index('time')
            elif not isinstance(df.index, pd.DatetimeIndex):
                 df.index = pd.to_datetime(df.index)
            
            df['ICAO'] = icao
            weather_dfs.append(df)
        except Exception as e:
            print(f"Error loading {f}: {e}")

    if not weather_dfs:
        raise ValueError("No weather data loaded.")

    combined_weather = pd.concat(weather_dfs)
    combined_weather = combined_weather.reset_index()
    
    if 'index' in combined_weather.columns and 'time' not in combined_weather.columns:
        combined_weather.rename(columns={'index': 'time'}, inplace=True)

    if combined_weather['time'].dt.tz is not None:
        combined_weather['time'] = combined_weather['time'].dt.tz_convert(None)

    print(f"Loaded consolidated weather data with {len(combined_weather)} records.")
    return combined_weather

def merge_data(flights_file, airports_file, weather_dir, output_file):
    iata_to_icao = load_airports_mapping(airports_file)

    print(f"Loading flight data from {flights_file}...")
    flights = pd.read_csv(flights_file)
    print(f"Loaded {len(flights)} flights.")
    
    flights['SchedDepUtc'] = pd.to_datetime(flights['SchedDepUtc'])
    flights['SchedArrUtc'] = pd.to_datetime(flights['SchedArrUtc'])

    flights['DepHour'] = flights['SchedDepUtc'].dt.round('H')
    flights['ArrHour'] = flights['SchedArrUtc'].dt.round('H')

    if flights['DepHour'].dt.tz is not None:
        flights['DepHour'] = flights['DepHour'].dt.tz_convert(None)
    if flights['ArrHour'].dt.tz is not None:
        flights['ArrHour'] = flights['ArrHour'].dt.tz_convert(None)

    flights['DepICAO'] = flights['SchedDepApt'].map(iata_to_icao)
    flights['ArrICAO'] = flights['SchedArrApt'].map(iata_to_icao)

    weather_df = load_weather_data(weather_dir)
    
    print("Merging departure weather...")
    dep_weather = weather_df.copy()
    dep_weather.columns = ['Dep_' + col if col not in ['ICAO', 'time'] else col for col in dep_weather.columns]
    
    flights = pd.merge(
        flights,
        dep_weather,
        left_on=['DepICAO', 'DepHour'],
        right_on=['ICAO', 'time'],
        how='left',
        suffixes=('', '_dep_weather_dup')
    )
    flights.drop(columns=['ICAO', 'time'], inplace=True, errors='ignore')

    print("Merging arrival weather...")
    arr_weather = weather_df.copy()
    arr_weather.columns = ['Arr_' + col if col not in ['ICAO', 'time'] else col for col in arr_weather.columns]

    flights = pd.merge(
        flights,
        arr_weather,
        left_on=['ArrICAO', 'ArrHour'],
        right_on=['ICAO', 'time'],
        how='left',
        suffixes=('', '_arr_weather_dup')
    )
    flights.drop(columns=['ICAO', 'time'], inplace=True, errors='ignore')
    
    print(f"Saving enriched data to {output_file}...")
    output_path = Path(output_file)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    flights.to_csv(output_file, index=False)
    print("Done.")

    print(f"Flights with Dep Weather: {flights['Dep_temp'].notnull().sum()} / {len(flights)}")
    print(f"Flights with Arr Weather: {flights['Arr_temp'].notnull().sum()} / {len(flights)}")

if __name__ == "__main__":
    BASE_DIR = Path(__file__).resolve().parents[3]
    AIRPORTS_FILE = BASE_DIR / "backend" / "data" / "processed" / "airports" / "airports_filtered.csv"
    FLIGHTS_FILE = BASE_DIR / "backend" / "data" / "processed" / "delays" / "delays_consolidated_filtered.csv"
    WEATHER_DIR = BASE_DIR / "backend" / "data" / "raw" / "weather"
    OUTPUT_FILE = BASE_DIR / "backend" / "data" / "merged" / "flights_with_weather.csv"

    merge_data(FLIGHTS_FILE, AIRPORTS_FILE, WEATHER_DIR, OUTPUT_FILE)
