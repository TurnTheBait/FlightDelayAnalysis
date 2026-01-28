import os
import glob
import pandas as pd
from pathlib import Path

def analyze_delays():
    base_dir = Path(__file__).resolve().parent.parent.parent
    raw_delays_dir = base_dir / "data" / "raw" / "delays"
    processed_dir = base_dir / "data" / "processed" / "delays"
    airports_path = base_dir / "data" / "processed" / "airports" / "airports_filtered.csv"
    output_csv = processed_dir / "delays_consolidated_filtered.csv"
    processed_dir.mkdir(parents=True, exist_ok=True)

    if not airports_path.exists():
        print(f"Error: Airports file not found at {airports_path}")
        return
    
    print(f"Loading airports from {airports_path}...")
    airports_df = pd.read_csv(airports_path)
    if 'iata_code' not in airports_df.columns:
        print("Error: 'iata_code' column not found in airports file.")
        print(airports_df.columns)
        return
    
    euro_airports = set(airports_df['iata_code'].dropna().unique())
    print(f"Loaded {len(euro_airports)} European airports.")

    txt_files = list(raw_delays_dir.glob("*.txt"))
    if not txt_files:
        print(f"No .txt files found in {raw_delays_dir}")
        return

    print(f"Found {len(txt_files)} delay files to process.")

    all_dfs = []
    for file_path in txt_files:
        try:
            df = pd.read_csv(file_path, sep='\t', low_memory=False)
            all_dfs.append(df)
        except Exception as e:
            print(f"Error reading {file_path}: {e}")

    if not all_dfs:
        print("No delay data could be read.")
        return

    full_df = pd.concat(all_dfs, ignore_index=True)
    print(f"Total raw flights loaded: {len(full_df)}")

    if 'SchedDepApt' not in full_df.columns or 'SchedArrApt' not in full_df.columns:
        print("Error: 'SchedDepApt' or 'SchedArrApt' columns missing in delay data.")
        return

    filtered_df = full_df[
        full_df['SchedDepApt'].isin(euro_airports) & 
        full_df['SchedArrApt'].isin(euro_airports)
    ].copy()

    print(f"Filtered European flights: {len(filtered_df)} ({(len(filtered_df)/len(full_df))*100:.2f}% of original)")

    try:
        filtered_df.to_csv(output_csv, index=False)
        print(f"Successfully saved filtered consolidated data to {output_csv}")
    except Exception as e:
        print(f"Error saving CSV: {e}")
        return

    print("\n--- Quick Data Analysis (Filtered European Flights) ---")

    total_flights = len(filtered_df)
    print(f"Number of European Flights: {total_flights}")
    if total_flights == 0:
        print("No flights matched the filter criteria.")
        return

    date_col = 'SchedDepLocal'
    if date_col in filtered_df.columns:
        filtered_df[date_col] = pd.to_datetime(filtered_df[date_col], errors='coerce')
        min_date = filtered_df[date_col].min()
        max_date = filtered_df[date_col].max()
        print(f"Date Range: {min_date} to {max_date}")
    delay_dep_col = 'MinLateDeparted'
    delay_arr_col = 'MinLateArrived'
    
    if delay_dep_col in filtered_df.columns:
        filtered_df[delay_dep_col] = pd.to_numeric(filtered_df[delay_dep_col], errors='coerce').fillna(0)
        avg_dep_delay = filtered_df[delay_dep_col].mean()
        print(f"Average Departure Delay: {avg_dep_delay:.2f} minutes")
    
    if delay_arr_col in filtered_df.columns:
        filtered_df[delay_arr_col] = pd.to_numeric(filtered_df[delay_arr_col], errors='coerce').fillna(0)
        avg_arr_delay = filtered_df[delay_arr_col].mean()
        print(f"Average Arrival Delay: {avg_arr_delay:.2f} minutes")
        
        delayed_15 = filtered_df[filtered_df[delay_arr_col] > 15]
        pct_delayed = (len(delayed_15) / total_flights) * 100
        print(f"Flights Delayed >15 mins (Arrival): {len(delayed_15)} ({pct_delayed:.2f}%)")

    if 'AirlineCode' in filtered_df.columns and delay_arr_col in filtered_df.columns:
        print("\nTop 5 Airlines with Highest Average Arrival Delay:")
        airline_delays = filtered_df.groupby('AirlineCode')[delay_arr_col].mean().sort_values(ascending=False).head(5)
        print(airline_delays)

    if 'SchedDepApt' in filtered_df.columns and delay_dep_col in filtered_df.columns:
        print("\nTop 5 Departure Airports with Highest Average Departure Delay:")
        apt_delays = filtered_df.groupby('SchedDepApt')[delay_dep_col].mean().sort_values(ascending=False).head(5)
        print(apt_delays)

if __name__ == "__main__":
    analyze_delays()
