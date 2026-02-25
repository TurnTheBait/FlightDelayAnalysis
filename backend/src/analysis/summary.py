import pandas as pd
import os
import numpy as np
import sys

current_script_dir = os.path.dirname(os.path.abspath(__file__))
src_dir = os.path.dirname(current_script_dir)
backend_dir = os.path.dirname(src_dir)

GENERAL_DATA_PATH = os.path.join(backend_dir, 'data', 'sentiment', 'sentiment_results_general.csv')
DELAY_DATA_PATH = os.path.join(backend_dir, 'data', 'sentiment', 'sentiment_results_delay.csv')
NOISE_DATA_PATH = os.path.join(backend_dir, 'data', 'sentiment', 'sentiment_results_noise.csv')
AIRPORTS_PATH = os.path.join(backend_dir, 'data', 'processed', 'airports', 'airports_filtered.csv')
OUTPUT_CSV = os.path.join(backend_dir, 'results', 'tables', 'airport_analysis_summary.csv')

sys.path.append(src_dir)
from utils.metrics import calculate_weighted_average
from utils.airport_utils import get_icao_to_iata_mapping

def get_counts(path, col_name):
    if not os.path.exists(path):
        return pd.DataFrame(columns=['airport_code', col_name])
    df = pd.read_csv(path, usecols=['airport_code'])
    counts = df.groupby('airport_code').size().reset_index(name=col_name)
    return counts

def main():
    if not os.path.exists(GENERAL_DATA_PATH):
        print(f"ERRORE: Non trovo {GENERAL_DATA_PATH}")
        return

    print(f"Caricamento dati generali da: {GENERAL_DATA_PATH}")
    df_general = pd.read_csv(GENERAL_DATA_PATH)
    
    print(f"Caricamento anagrafica aeroporti da: {AIRPORTS_PATH}")
    df_airports = pd.read_csv(AIRPORTS_PATH, low_memory=False)

    print("Calcolo scomposizione per sorgente...")
    source_counts = df_general.groupby(['airport_code', 'source']).size().unstack(fill_value=0)
    source_col_map = {
        'Google News': 'google_news_count',
        'Reddit': 'reddit_count',
        'Skytrax': 'skytrax_count'
    }
    source_counts.rename(columns=source_col_map, inplace=True)
    source_counts = source_counts.reset_index()
    
    counts_general = get_counts(GENERAL_DATA_PATH, 'general_reviews_count')
    counts_delay = get_counts(DELAY_DATA_PATH, 'delay_reviews_count')
    counts_noise = get_counts(NOISE_DATA_PATH, 'noise_reviews_count')

    print("Calcolo metriche globali...")
    global_stats = df_general.groupby('airport_code').apply(
        lambda x: pd.Series({
            'total_mentions': len(x),
            'global_weighted_sentiment': calculate_weighted_average(x, 'combined_score', 'weight', fallback_to_mean=True),
            'global_pressure_sentiment': x['pressure_impact_score'].mean() if 'pressure_impact_score' in x.columns else np.nan
        })
    ).reset_index()

    icao_to_iata = get_icao_to_iata_mapping(AIRPORTS_PATH)
    df_airports['airport_code'] = df_airports['ident'].map(icao_to_iata).fillna(df_airports['ident'])
    summary = df_airports[['airport_code', 'name', 'iso_country', 'municipality']].drop_duplicates('airport_code').copy()

    summary = summary.merge(global_stats, on='airport_code', how='inner')
    summary = summary.merge(source_counts, on='airport_code', how='left')
    summary = summary.merge(counts_general, on='airport_code', how='left')
    summary = summary.merge(counts_delay, on='airport_code', how='left')
    summary = summary.merge(counts_noise, on='airport_code', how='left')
    
    summary['media_pressure_index'] = np.log1p(summary['general_reviews_count'])
    summary['media_pressure_index_delay'] = np.log1p(summary['delay_reviews_count'])
    summary['media_pressure_index_noise'] = np.log1p(summary['noise_reviews_count'])

    summary = summary.sort_values('total_mentions', ascending=False)
    
    expected_cols = [
        'airport_code', 'name', 'iso_country', 'municipality',
        'google_news_count', 'reddit_count', 'skytrax_count',
        'total_mentions', 'delay_reviews_count', 'noise_reviews_count', 
        'media_pressure_index', 'media_pressure_index_delay', 'media_pressure_index_noise',
        'global_weighted_sentiment', 
    ]
    
    for c in expected_cols:
        if c not in summary.columns:
            summary[c] = 0
            
    summary = summary[expected_cols]

    os.makedirs(os.path.dirname(OUTPUT_CSV), exist_ok=True)
    summary.to_csv(OUTPUT_CSV, index=False)
    
    print(f"Analysis complete. Tabella salvata in: {OUTPUT_CSV}")
    print("\nTop 5 Aeroporti per Media Pressure Index:")
    print(summary[['airport_code', 'total_mentions', 'delay_reviews_count', 'noise_reviews_count', 'media_pressure_index']].head())

if __name__ == "__main__":
    main()
