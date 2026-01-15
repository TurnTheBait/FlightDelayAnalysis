import pandas as pd
import os
import sys

current_script_dir = os.path.dirname(os.path.abspath(__file__))
src_dir = os.path.dirname(current_script_dir)
backend_dir = os.path.dirname(src_dir)

INPUT_FILE = os.path.join(backend_dir, 'data', 'processed', 'delays', 'delays_consolidated_filtered.csv')

def analyze_delays(file_path):
    print(f"Loading data from {file_path}...")
    try:
        df = pd.read_csv(file_path, low_memory=False)
    except FileNotFoundError:
        print(f"Error: File not found at {file_path}")
        return

    total_flights = len(df)
    print(f"\n--- General Stats ---")
    print(f"Total Flights (Scheduled): {total_flights}")

    if 'Cancelled' in df.columns:
        cancelled_numeric = pd.to_numeric(df['Cancelled'], errors='coerce').fillna(0)
        df_operated = df[cancelled_numeric == 0].copy()
        cancelled_count = total_flights - len(df_operated)
        print(f"Cancelled Flights: {cancelled_count} ({cancelled_count/total_flights*100:.2f}%)")
    else:
        df_operated = df.copy()
        print("Warning: 'Cancelled' column not found. Assuming all flights operated.")

    print(f"Operated Flights: {len(df_operated)}")

    if 'MinLateDeparted' not in df_operated.columns or 'MinLateArrived' not in df_operated.columns:
        print("Error: Delay columns 'MinLateDeparted' or 'MinLateArrived' not found.")
        return

    df_operated['MinLateDeparted'] = pd.to_numeric(df_operated['MinLateDeparted'], errors='coerce').fillna(0)
    df_operated['MinLateArrived'] = pd.to_numeric(df_operated['MinLateArrived'], errors='coerce').fillna(0)

    def get_delay_buckets(series):
        total = len(series)
        if total == 0:
            return {}
        on_time = (series < 15).sum()
        delay_15_30 = ((series >= 15) & (series < 30)).sum()
        delay_30_60 = ((series >= 30) & (series < 60)).sum()
        delay_60_plus = (series >= 60).sum()
        
        return {
            'On Time (<15m)': (on_time, on_time/total*100),
            'Delay 15-30m': (delay_15_30, delay_15_30/total*100),
            'Delay 30-60m': (delay_30_60, delay_30_60/total*100),
            'Delay >60m': (delay_60_plus, delay_60_plus/total*100)
        }

    print("\n--- Departure Delay Stats (Operated Flights) ---")
    dep_stats = get_delay_buckets(df_operated['MinLateDeparted'])
    for bucket, (count, pct) in dep_stats.items():
        print(f"{bucket}: {count} ({pct:.2f}%)")

    print("\n--- Arrival Delay Stats (Operated Flights) ---")
    arr_stats = get_delay_buckets(df_operated['MinLateArrived'])
    for bucket, (count, pct) in arr_stats.items():
        print(f"{bucket}: {count} ({pct:.2f}%)")

    print("\n--- Punctuality Rankings ---")

    print("\nTop 10 Most Punctual Airports (Departures):")
    if 'SchedDepApt' in df_operated.columns:
        apt_dep_stats = df_operated.groupby('SchedDepApt')['MinLateDeparted'].agg(['count', lambda x: (x < 15).mean() * 100])
        apt_dep_stats.columns = ['Flights', 'OnTimePct']
        apt_dep_stats = apt_dep_stats[apt_dep_stats['Flights'] > 100].sort_values('OnTimePct', ascending=False)
        print(apt_dep_stats.head(10).to_string(formatters={'OnTimePct': '{:.2f}%'.format}))
    else:
        print("Column 'SchedDepApt' not found.")

    print("\nTop 10 Most Punctual Airports (Arrivals):")
    if 'SchedArrApt' in df_operated.columns:
        apt_arr_stats = df_operated.groupby('SchedArrApt')['MinLateArrived'].agg(['count', lambda x: (x < 15).mean() * 100])
        apt_arr_stats.columns = ['Flights', 'OnTimePct']
        apt_arr_stats = apt_arr_stats[apt_arr_stats['Flights'] > 100].sort_values('OnTimePct', ascending=False)
        print(apt_arr_stats.head(10).to_string(formatters={'OnTimePct': '{:.2f}%'.format}))
    else:
        print("Column 'SchedArrApt' not found.")

if __name__ == "__main__":
    analyze_delays(INPUT_FILE)