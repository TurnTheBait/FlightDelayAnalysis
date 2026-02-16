import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt
import os
import numpy as np
from pathlib import Path
import sys
from datetime import timedelta


sys.path.append(str(Path(__file__).resolve().parent.parent))
from utils.airport_utils import get_icao_to_iata_mapping

AIRPORTS_PATH = os.path.join(Path(__file__).resolve().parent.parent.parent, "data", "processed", "airports", "airports_filtered.csv")

BASE_DIR = Path(__file__).resolve().parents[3]
FLIGHTS_FILE = BASE_DIR / "backend" / "data" / "merged" / "flights_with_weather.csv"
SENTIMENT_FILE = BASE_DIR / "backend" / "data" / "sentiment" / "sentiment_results_delay.csv"

OUTPUT_DIR = BASE_DIR / "backend" / "results" / "figures" / "sentiment_weather_correlation"
TABLES_DIR = BASE_DIR / "backend" / "results" / "tables"

def load_data(flights_path, sentiment_path):
    print(f"Loading flights data from {flights_path}...")
    cols = ['DepICAO', 'MinLateDeparted', 'MinLateArrived', 'Dep_prcp', 'Dep_wspd', 'Dep_temp', 'SchedDepUtc']
    df_flights = pd.read_csv(flights_path, usecols=cols, low_memory=False)
    df_flights['date'] = pd.to_datetime(df_flights['SchedDepUtc'], format='mixed', utc=True).dt.date
    
    print(f"Loading sentiment data from {sentiment_path}...")
    df_sentiment = pd.read_csv(sentiment_path)
    df_sentiment['date'] = pd.to_datetime(df_sentiment['date'], format='mixed', utc=True).dt.date
    
    return df_flights, df_sentiment

def aggregate_daily_data(df_flights, df_sentiment):
    print("Aggregating daily data...")
    
    weather_daily = df_flights.groupby(['DepICAO', 'date']).agg({
        'Dep_prcp': 'max',
        'Dep_wspd': 'max',
        'Dep_temp': 'mean',
        'MinLateDeparted': 'mean',
        'MinLateArrived': 'mean'
    }).reset_index()
    
    icao_to_iata = get_icao_to_iata_mapping(AIRPORTS_PATH)
    weather_daily['airport_code'] = weather_daily['DepICAO'].map(icao_to_iata).fillna(weather_daily['DepICAO'])
    
    sentiment_daily = df_sentiment.groupby(['airport_code', 'date']).agg({
        'weighted_score': 'mean',
        'stars_score': lambda x: (x <= 3).sum()
    }).reset_index()
    sentiment_daily.rename(columns={'stars_score': 'negative_review_count', 'weighted_score': 'daily_sentiment'}, inplace=True)
    
    daily_merged = pd.merge(weather_daily, sentiment_daily, on=['airport_code', 'date'], how='inner')
    
    print(f"Daily merged dataset has {len(daily_merged)} records.")
    return daily_merged

    print("Lagged analysis complete.")
    return df_lagged

def calculate_correlation(df, tables_dir):
    print("Calculating correlations...")
    cols_to_corr = ['global_sentiment', 'MinLateDeparted', 'MinLateArrived', 'Dep_prcp', 'Dep_wspd', 'Dep_temp']
    corr_matrix = df[cols_to_corr].corr(method='pearson')
    
    print("Correlation Matrix:")
    print(corr_matrix)
    
    os.makedirs(tables_dir, exist_ok=True)
    corr_matrix.to_csv(os.path.join(tables_dir, 'correlation_delay_weather_summary.csv'))
    return corr_matrix

def analyze_lagged_correlation(daily_data, tables_dir):
    print("Analyzing lagged correlation for weather events...")
    
    PRECIP_THRESHOLD = 5.0
    WIND_THRESHOLD = 30.0 
    
    results = []
    
    for airport in daily_data['airport_code'].unique():
        airport_data = daily_data[daily_data['airport_code'] == airport].sort_values('date')
        
        for i in range(len(airport_data) - 3):
            day_t = airport_data.iloc[i]
            
            is_rain_event = day_t['Dep_prcp'] > PRECIP_THRESHOLD
            is_wind_event = day_t['Dep_wspd'] > WIND_THRESHOLD
            
            event_type = None
            if is_rain_event and is_wind_event:
                event_type = 'Rain & Wind'
            elif is_rain_event:
                event_type = 'Rain'
            elif is_wind_event:
                event_type = 'Wind'
            else:
                event_type = 'None'
            
            days_lag = []
            for lag in range(4):
                day_lagged = airport_data.iloc[i + lag]
                days_lag.append({
                    'lag': lag,
                    'sentiment': day_lagged['daily_sentiment'],
                    'negative_count': day_lagged['negative_review_count']
                })
            
            results.append({
                'airport_code': airport,
                'event_date': day_t['date'],
                'event_type': event_type,
                'precip': day_t['Dep_prcp'],
                'wind': day_t['Dep_wspd'],
                'sentiment_t0': days_lag[0]['sentiment'],
                'sentiment_t1': days_lag[1]['sentiment'],
                'sentiment_t2': days_lag[2]['sentiment'],
                'sentiment_t3': days_lag[3]['sentiment'],
                'neg_count_t0': days_lag[0]['negative_count'],
                'neg_count_t1': days_lag[1]['negative_count'],
                'neg_count_t2': days_lag[2]['negative_count'],
                'neg_count_t3': days_lag[3]['negative_count']
            })

    df_lagged = pd.DataFrame(results)
    
    os.makedirs(tables_dir, exist_ok=True)
    df_lagged.to_csv(os.path.join(tables_dir, 'weather_event_lagged_analysis.csv'), index=False)
    
    print("Lagged analysis complete.")
    return df_lagged

    return df_lagged

def plot_results(df, df_lagged, output_dir):
    print("Plotting results...")
    sns.set_theme(style="whitegrid")
    
    if not df_lagged.empty:
        lag_columns = ['sentiment_t0', 'sentiment_t1', 'sentiment_t2', 'sentiment_t3']
        
        df_events = df_lagged[df_lagged['event_type'] != 'None'].copy()
        
        if not df_events.empty:
            df_melted = df_events.melt(
                id_vars=['event_type', 'airport_code', 'event_date'], 
                value_vars=lag_columns,
                var_name='Time_Lag', 
                value_name='Sentiment_Score'
            )
            
            df_melted['Time_Lag'] = df_melted['Time_Lag'].map({
                'sentiment_t0': 'Day of Event',
                'sentiment_t1': 'Day +1',
                'sentiment_t2': 'Day +2',
                'sentiment_t3': 'Day +3'
            })
            
            plt.figure(figsize=(12, 8))
            sns.boxplot(x='Time_Lag', y='Sentiment_Score', hue='event_type', data=df_melted)
            plt.title('Sentiment Score Distribution After Weather Events')
            plt.ylabel('Average Daily Sentiment Score')
            plt.xlabel('Time Lag')
            plt.legend(title='Event Type')
            plt.savefig(os.path.join(output_dir, 'lagged_sentiment_boxplot.png'))
            plt.close()
            
            neg_columns = ['neg_count_t0', 'neg_count_t1', 'neg_count_t2', 'neg_count_t3']
            df_melted_neg = df_events.melt(
                id_vars=['event_type'],
                value_vars=neg_columns,
                var_name='Time_Lag',
                value_name='Negative_Reviews'
            )
            
            df_melted_neg['Time_Lag'] = df_melted_neg['Time_Lag'].map({
                'neg_count_t0': 'Day of Event',
                'neg_count_t1': 'Day +1',
                'neg_count_t2': 'Day +2',
                'neg_count_t3': 'Day +3'
            })

            plt.figure(figsize=(12, 8))
            sns.lineplot(x='Time_Lag', y='Negative_Reviews', hue='event_type', data=df_melted_neg, marker='o')
            plt.title('Average Negative Reviews Count After Weather Events')
            plt.ylabel('Avg Negative Reviews Count')
            plt.xlabel('Time Lag')
            plt.savefig(os.path.join(output_dir, 'lagged_neg_reviews_lineplot.png'))
            plt.close()
        else:
            print("No weather events found to plot.")

    plt.figure(figsize=(10, 6))
    corr = df['global_sentiment'].corr(df['MinLateDeparted'])
    sns.regplot(x='global_sentiment', y='MinLateDeparted', data=df, scatter_kws={'alpha':0.5}, line_kws={'color':'red', 'label': f'Correlation: {corr:.2f}'})
    plt.title(f'Delay Sentiment vs Average Departure Delay (r={corr:.2f})')
    plt.xlabel('Delay Sentiment Score (1-10)')
    plt.ylabel('Average Departure Delay (min)')
    plt.legend()
    plt.savefig(os.path.join(output_dir, 'sentiment_vs_departure_delay.png'))
    plt.close()
    
    plt.figure(figsize=(10, 6))
    corr = df['global_sentiment'].corr(df['MinLateArrived'])
    sns.regplot(x='global_sentiment', y='MinLateArrived', data=df, scatter_kws={'alpha':0.5}, line_kws={'color':'orange', 'label': f'Correlation: {corr:.2f}'})
    plt.title(f'Delay Sentiment vs Average Arrival Delay (r={corr:.2f})')
    plt.xlabel('Delay Sentiment Score (1-10)')
    plt.ylabel('Average Arrival Delay (min)')
    plt.legend()
    plt.savefig(os.path.join(output_dir, 'sentiment_vs_arrival_delay.png'))
    plt.close()
    
    plt.figure(figsize=(10, 6))
    corr = df['global_sentiment'].corr(df['Dep_prcp'])
    sns.regplot(x='global_sentiment', y='Dep_prcp', data=df, scatter_kws={'alpha':0.5}, line_kws={'color':'blue', 'label': f'Correlation: {corr:.2f}'})
    plt.title(f'Delay Sentiment vs Average Precipitation (r={corr:.2f})')
    plt.xlabel('Delay Sentiment Score (1-10)')
    plt.ylabel('Average Precipitation (mm)')
    plt.legend()
    plt.savefig(os.path.join(output_dir, 'sentiment_vs_weather_prcp.png'))
    plt.close()

    plt.figure(figsize=(10, 6))
    corr = df['global_sentiment'].corr(df['Dep_wspd'])
    sns.regplot(x='global_sentiment', y='Dep_wspd', data=df, scatter_kws={'alpha':0.5}, line_kws={'color':'green', 'label': f'Correlation: {corr:.2f}'})
    plt.title(f'Delay Sentiment vs Average Wind Speed (r={corr:.2f})')
    plt.xlabel('Delay Sentiment Score (1-10)')
    plt.ylabel('Average Wind Speed (km/h)')
    plt.legend()
    plt.savefig(os.path.join(output_dir, 'sentiment_vs_weather_wspd.png'))
    plt.close()
    
    print(f"Plots saved to {output_dir}")

def main():

    os.makedirs(OUTPUT_DIR, exist_ok=True)
    
    if not FLIGHTS_FILE.exists():
        print(f"Error: {FLIGHTS_FILE} not found.")
        return
    if not SENTIMENT_FILE.exists():
        print(f"Error: {SENTIMENT_FILE} not found.")
        return

    df_flights, df_sentiment = load_data(FLIGHTS_FILE, SENTIMENT_FILE)
    
    # 1. Unified Daily Aggregation (Single Source of Truth)
    daily_merged = aggregate_daily_data(df_flights, df_sentiment)
    
    if daily_merged.empty:
        print("No overlapping data found.")
        return

    # 2. Lagged Analysis on Daily Data
    df_lagged = analyze_lagged_correlation(daily_merged, TABLES_DIR)
    
    # 3. Derive Global Stats from Daily Data
    print("Deriving global stats from daily data...")
    global_stats = daily_merged.groupby('airport_code').agg({
        'daily_sentiment': 'mean',
        'MinLateDeparted': 'mean',
        'MinLateArrived': 'mean',
        'Dep_prcp': 'mean',
        'Dep_wspd': 'mean',
        'Dep_temp': 'mean'
    }).reset_index()
    
    # Rename for consistency with correlation function
    global_stats.rename(columns={'daily_sentiment': 'global_sentiment'}, inplace=True)
    
    calculate_correlation(global_stats, TABLES_DIR)
    plot_results(global_stats, df_lagged, OUTPUT_DIR)

if __name__ == "__main__":
    main()