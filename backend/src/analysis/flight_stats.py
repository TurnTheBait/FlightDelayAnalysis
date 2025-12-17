import pandas as pd
import os
import glob

BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

FILES = {
    "airports_filtered": os.path.join(BASE_DIR, "data", "processed", "airports", "airports_filtered.csv"),
    "flight_events_full": os.path.join(BASE_DIR, "data", "processed", "flight_events_processed", "flight_events_full.csv"),
    "flight_list_filtered": os.path.join(BASE_DIR, "data", "processed", "flights_filtered", "flight_list_filtered_2023_2024.csv"),
    "clean_schedule": os.path.join(BASE_DIR, "data", "processed", "schedule", "clean_schedule_23-24.csv"),
    "merged_schedule_flight": os.path.join(BASE_DIR, "data", "merged", "schedule_flight_list_localized.csv"),
}

def analyze_general(df, name):
    """Provides a general overview of the dataset."""
    print(f"\n{'='*20} {name} {'='*20}")
    print(f"Shape: {df.shape}")
    print(f"Columns: {list(df.columns)}")
    print("-" * 30)
    print("Basic Statistics:")
    print(df.describe().to_string())
    print("-" * 30)
    print("Missing Values:")
    print(df.isnull().sum().to_string())

def analyze_merged_detailed(df):
    """Performs detailed analysis on the merged schedule and flight list dataset."""
    print(f"\n{'='*20} DETAILED ANALYSIS: Merged Schedule Flight List {'='*20}")
    
    if 'date' in df.columns:
        df['date'] = pd.to_datetime(df['date'])
    elif 'STD' in df.columns:
         try:
             df['date'] = pd.to_datetime(df['STD']).dt.date
             df['date'] = pd.to_datetime(df['date'])
         except:
             pass

    total_flights = len(df)
    print(f"\nTotal Flights: {total_flights}")

    if 'year' in df.columns:
        print("\nFlights per Year:")
        print(df['year'].value_counts().sort_index().to_string())
    elif 'date' in df.columns:
        df['year'] = df['date'].dt.year
        print("\nFlights per Year:")
        print(df['year'].value_counts().sort_index().to_string())

    if 'date' in df.columns:
        daily_counts = df.groupby('date').size()
        avg_daily_flights = daily_counts.mean()
        print(f"\nAverage Daily Flights: {avg_daily_flights:.2f}")
    
    delay_col = 'delay_minutes'
    if delay_col not in df.columns:
         if 'dep_delay' in df.columns:
             delay_col = 'dep_delay'
         elif 'arr_delay' in df.columns:
             delay_col = 'arr_delay'
         else:
             print(f"\n[WARN] No delay column found (looked for 'delay_minutes', 'dep_delay', 'arr_delay'). skipping delay analysis.")
             return

    df_delay = df.dropna(subset=[delay_col])

    if 'date' in df.columns:
        daily_avg_delay = df_delay.groupby('date')[delay_col].mean()
        print(f"\nAverage Daily Delay (minutes): {daily_avg_delay.mean():.2f}")
    
    print("\nDelay Buckets Analysis:")
    
    total_delayed_ops = len(df_delay)
    
    on_time = df_delay[df_delay[delay_col] <= 0]
    delay_15 = df_delay[(df_delay[delay_col] > 0) & (df_delay[delay_col] <= 15)]
    delay_30 = df_delay[(df_delay[delay_col] > 15) & (df_delay[delay_col] <= 30)]
    delay_60 = df_delay[(df_delay[delay_col] > 30) & (df_delay[delay_col] <= 60)]
    delay_120 = df_delay[(df_delay[delay_col] > 60) & (df_delay[delay_col] <= 120)]
    delay_240 = df_delay[(df_delay[delay_col] > 120) & (df_delay[delay_col] <= 240)]
    delay_above_240 = df_delay[df_delay[delay_col] > 240]

    buckets = [
        ("On Time (<= 0 min)", len(on_time)),
        ("0 < x <= 15 min", len(delay_15)),
        ("15 < x <= 30 min", len(delay_30)),
        ("30 < x <= 60 min", len(delay_60)),
        ("60 < x <= 120 min (2h)", len(delay_120)),
        ("120 < x <= 240 min (4h)", len(delay_240)),
        ("> 240 min (> 4h)", len(delay_above_240))
    ]

    print(f"{'Bucket':<25} | {'Count':<10} | {'Percentage':<10}")
    print("-" * 50)
    for name, count in buckets:
        pct = (count / total_delayed_ops * 100) if total_delayed_ops > 0 else 0
        print(f"{name:<25} | {count:<10} | {pct:<10.2f}%")


def main():
    for name, path in FILES.items():
        if os.path.exists(path):
            print(f"Loading {name} from {path}...")
            try:
                df = pd.read_csv(path, low_memory=False)
                analyze_general(df, name)
                if name == "merged_schedule_flight":
                    analyze_merged_detailed(df)
                    
            except Exception as e:
                print(f"Error analyzing {name}: {e}")
        else:
            print(f"[WARN] File not found: {path} (Expected at: {path})")

if __name__ == "__main__":
    main()
