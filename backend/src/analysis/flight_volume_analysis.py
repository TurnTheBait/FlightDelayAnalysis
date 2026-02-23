import pandas as pd
import os
import numpy as np

current_script_dir = os.path.dirname(os.path.abspath(__file__))
src_dir = os.path.dirname(current_script_dir)
backend_dir = os.path.dirname(src_dir)

SENTIMENT_SUMMARY_PATH = os.path.join(backend_dir, 'results', 'tables', 'airport_analysis_summary.csv')
DELAYS_DATA_PATH = os.path.join(backend_dir, 'data', 'processed', 'delays', 'delays_consolidated_filtered.csv')

OUTPUT_CSV = os.path.join(backend_dir, 'results', 'tables', 'airport_volume_analysis_summary.csv')

def min_max_normalize(series):
    return (series - series.min()) / (series.max() - series.min())

def main():
    print(f"Loading sentiment summary from: {SENTIMENT_SUMMARY_PATH}")
    if not os.path.exists(SENTIMENT_SUMMARY_PATH):
        print(f"ERROR: File {SENTIMENT_SUMMARY_PATH} not found.")
        return
    
    df_sentiment = pd.read_csv(SENTIMENT_SUMMARY_PATH)
    
    print(f"Loading flight data from: {DELAYS_DATA_PATH}")
    if not os.path.exists(DELAYS_DATA_PATH):
        print(f"ERROR: File {DELAYS_DATA_PATH} not found.")
        return
    
    df_flights = pd.read_csv(DELAYS_DATA_PATH, usecols=['SchedDepApt', 'SchedArrApt'], low_memory=False)

    print("Calculating flight volumes...")
    dep_counts = df_flights['SchedDepApt'].value_counts()
    arr_counts = df_flights['SchedArrApt'].value_counts()
    
    total_volumes = dep_counts.add(arr_counts, fill_value=0).reset_index()
    total_volumes.columns = ['airport_code', 'total_flights']
    
    df_merged = df_sentiment.merge(total_volumes, on='airport_code', how='left')
    df_merged['total_flights'] = df_merged['total_flights'].fillna(0)
    df_merged = df_merged[(df_merged['total_flights'] > 0) & (df_merged['global_weighted_sentiment'].notna())].copy()

    print("Calculating Composite Score...")
    
    df_merged['sentiment_norm'] = min_max_normalize(df_merged['global_weighted_sentiment'])
    df_merged['log_volume'] = np.log10(df_merged['total_flights'] + 1)
    df_merged['volume_norm'] = min_max_normalize(df_merged['log_volume'])
    
    w_sentiment = 0.5
    w_volume = 0.5
    
    df_merged['composite_score'] = (df_merged['sentiment_norm'] * w_sentiment) + (df_merged['volume_norm'] * w_volume)
    df_merged['composite_score_scaled'] = df_merged['composite_score'] * 10
    
    df_merged = df_merged.sort_values('composite_score_scaled', ascending=False)
    
    os.makedirs(os.path.dirname(OUTPUT_CSV), exist_ok=True)
    df_merged.to_csv(OUTPUT_CSV, index=False)
        
    print(f"Analysis complete. Results saved to: {OUTPUT_CSV}")
    print("\nTop 5 Airports by Volume-Weighted Score:")
    print(df_merged[['airport_code', 'name', 'total_flights', 'global_weighted_sentiment', 'global_pressure_sentiment', 'composite_score_scaled']].head())

if __name__ == "__main__":
    main()