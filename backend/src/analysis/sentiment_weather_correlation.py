import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt
import os
import numpy as np
from pathlib import Path
import sys

sys.path.append(str(Path(__file__).resolve().parent.parent))
from utils.airport_utils import get_icao_to_iata_mapping

AIRPORTS_PATH = os.path.join(Path(__file__).resolve().parent.parent.parent, "data", "processed", "airports", "airports_filtered.csv")

def load_data(flights_path, sentiment_path):
    print(f"Loading flights data from {flights_path}...")
    cols = ['DepICAO', 'MinLateDeparted', 'MinLateArrived', 'Dep_prcp', 'Dep_wspd', 'Dep_temp']
    df_flights = pd.read_csv(flights_path, usecols=cols, low_memory=False)
    
    print(f"Loading sentiment data from {sentiment_path}...")
    df_sentiment = pd.read_csv(sentiment_path)
    
    return df_flights, df_sentiment

def aggregate_data(df_flights, df_sentiment):
    print("Aggregating data...")
    
    sentiment_agg = df_sentiment.groupby('airport_code').apply(
        lambda x: pd.Series({
            'global_sentiment': np.average(x['stars_score'], weights=x['time_weight']),
            'sentiment_count': len(x)
        }),
        include_groups=False
    ).reset_index()
    
    sentiment_agg['global_sentiment'] = sentiment_agg['global_sentiment'] * 2
    
    metrics = {
        'MinLateDeparted': 'mean',
        'MinLateArrived': 'mean',
        'Dep_prcp': 'mean',
        'Dep_wspd': 'mean',
        'Dep_temp': 'mean'
    }
    
    flights_agg = df_flights.groupby('DepICAO').agg(metrics).reset_index()
    flights_agg = flights_agg.rename(columns={'DepICAO': 'airport_code'})

    icao_to_iata = get_icao_to_iata_mapping(AIRPORTS_PATH)
    flights_agg['airport_code'] = flights_agg['airport_code'].map(icao_to_iata).fillna(flights_agg['airport_code'])
    
    return sentiment_agg, flights_agg

def merge_datasets(sentiment_agg, flights_agg):
    print("Merging datasets...")
    merged = pd.merge(sentiment_agg, flights_agg, on='airport_code', how='inner')
    print(f"Merged dataset has {len(merged)} airports.")
    return merged

def calculate_correlation(df, tables_dir):
    print("Calculating correlations...")
    cols_to_corr = ['global_sentiment', 'MinLateDeparted', 'MinLateArrived', 'Dep_prcp', 'Dep_wspd', 'Dep_temp']
    corr_matrix = df[cols_to_corr].corr(method='pearson')
    
    print("Correlation Matrix:")
    print(corr_matrix)
    
    os.makedirs(tables_dir, exist_ok=True)
    corr_matrix.to_csv(os.path.join(tables_dir, 'correlation_delay_weather_summary.csv'))
    return corr_matrix

def plot_results(df, output_dir):
    print("Plotting results...")
    sns.set_theme(style="whitegrid")
    
    plt.figure(figsize=(10, 6))
    sns.regplot(x='global_sentiment', y='MinLateDeparted', data=df, scatter_kws={'alpha':0.5}, line_kws={'color':'red'})
    plt.title('Delay Sentiment vs Average Departure Delay')
    plt.xlabel('Delay Sentiment Score (1-10)')
    plt.ylabel('Average Departure Delay (min)')
    plt.savefig(os.path.join(output_dir, 'sentiment_vs_departure_delay.png'))
    plt.close()
    
    plt.figure(figsize=(10, 6))
    sns.regplot(x='global_sentiment', y='MinLateArrived', data=df, scatter_kws={'alpha':0.5}, line_kws={'color':'orange'})
    plt.title('Delay Sentiment vs Average Arrival Delay')
    plt.xlabel('Delay Sentiment Score (1-10)')
    plt.ylabel('Average Arrival Delay (min)')
    plt.savefig(os.path.join(output_dir, 'sentiment_vs_arrival_delay.png'))
    plt.close()
    
    plt.figure(figsize=(10, 6))
    sns.regplot(x='global_sentiment', y='Dep_prcp', data=df, scatter_kws={'alpha':0.5}, line_kws={'color':'blue'})
    plt.title('Delay Sentiment vs Average Precipitation')
    plt.xlabel('Delay Sentiment Score (1-10)')
    plt.ylabel('Average Precipitation (mm)')
    plt.savefig(os.path.join(output_dir, 'sentiment_vs_weather_prcp.png'))
    plt.close()

    plt.figure(figsize=(10, 6))
    sns.regplot(x='global_sentiment', y='Dep_wspd', data=df, scatter_kws={'alpha':0.5}, line_kws={'color':'green'})
    plt.title('Delay Sentiment vs Average Wind Speed')
    plt.xlabel('Delay Sentiment Score (1-10)')
    plt.ylabel('Average Wind Speed (km/h)')
    plt.savefig(os.path.join(output_dir, 'sentiment_vs_weather_wspd.png'))
    plt.close()
    
    print(f"Plots saved to {output_dir}")

def main():
    BASE_DIR = Path(__file__).resolve().parents[3]
    FLIGHTS_FILE = BASE_DIR / "backend" / "data" / "merged" / "flights_with_weather.csv"
    SENTIMENT_FILE = BASE_DIR / "backend" / "data" / "sentiment" / "sentiment_results_delay.csv"
    
    OUTPUT_DIR = BASE_DIR / "backend" / "results" / "figures" / "sentiment_weather_correlation"
    TABLES_DIR = BASE_DIR / "backend" / "results" / "tables"

    os.makedirs(OUTPUT_DIR, exist_ok=True)
    
    if not FLIGHTS_FILE.exists():
        print(f"Error: {FLIGHTS_FILE} not found.")
        return
    if not SENTIMENT_FILE.exists():
        print(f"Error: {SENTIMENT_FILE} not found.")
        return

    df_flights, df_sentiment = load_data(FLIGHTS_FILE, SENTIMENT_FILE)
    
    sentiment_agg, flights_agg = aggregate_data(df_flights, df_sentiment)
    
    merged_df = merge_datasets(sentiment_agg, flights_agg)
    
    if merged_df.empty:
        print("No overlapping airports found between sentiment and flight data.")
        return
        
    calculate_correlation(merged_df, TABLES_DIR)
    plot_results(merged_df, OUTPUT_DIR)

if __name__ == "__main__":
    main()