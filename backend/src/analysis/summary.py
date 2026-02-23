import pandas as pd
import os
import numpy as np
import sys

current_script_dir = os.path.dirname(os.path.abspath(__file__))
src_dir = os.path.dirname(current_script_dir)
backend_dir = os.path.dirname(src_dir)

SCORED_DATA_PATH = os.path.join(backend_dir, 'data', 'sentiment', 'sentiment_results_general.csv')
AIRPORTS_PATH = os.path.join(backend_dir, 'data', 'processed', 'airports', 'airports_filtered.csv')
OUTPUT_CSV = os.path.join(backend_dir, 'results', 'tables', 'airport_analysis_summary.csv')

sys.path.append(src_dir)
from utils.metrics import calculate_weighted_average
from utils.airport_utils import get_icao_to_iata_mapping

def main():
    if not os.path.exists(SCORED_DATA_PATH):
        print(f"ERRORE: Non trovo {SCORED_DATA_PATH}")
        return

    print(f"Caricamento dati analizzati da: {SCORED_DATA_PATH}")
    df_scored = pd.read_csv(SCORED_DATA_PATH)
    
    print(f"Caricamento anagrafica aeroporti da: {AIRPORTS_PATH}")
    df_airports = pd.read_csv(AIRPORTS_PATH, low_memory=False)

    print("Calcolo scomposizione per sorgente...")
    source_counts = df_scored.groupby(['airport_code', 'source']).size().unstack(fill_value=0)
    source_col_map = {
        'Google News': 'google_news_count',
        'Reddit': 'reddit_count',
        'Skytrax': 'skytrax_count'
    }
    source_counts.rename(columns=source_col_map, inplace=True)
    source_counts = source_counts.reset_index()
    
    print("Calcolo metriche globali...")
    global_stats = df_scored.groupby('airport_code').apply(
        lambda x: pd.Series({
            'total_mentions': len(x),
            'global_weighted_sentiment': calculate_weighted_average(x, 'combined_score', 'weight', fallback_to_mean=True),
            'pressure_index': x['media_pressure_index'].mean() if 'media_pressure_index' in x.columns else np.nan,
            'global_pressure_sentiment': x['pressure_impact_score'].mean() if 'pressure_impact_score' in x.columns else np.nan
        })
    ).reset_index()

    icao_to_iata = get_icao_to_iata_mapping(AIRPORTS_PATH)
    df_airports['airport_code'] = df_airports['ident'].map(icao_to_iata).fillna(df_airports['ident'])
    summary = df_airports[['airport_code', 'name', 'iso_country', 'municipality']].drop_duplicates('airport_code').copy()

    summary = summary.merge(global_stats, on='airport_code', how='inner')
    summary = summary.merge(source_counts, on='airport_code', how='left')
    summary = summary.sort_values('total_mentions', ascending=False)
    
    expected_cols = [
        'airport_code', 'name', 'iso_country', 'municipality',
        'google_news_count', 'reddit_count', 'skytrax_count',
        'total_mentions', 'global_weighted_sentiment', 
        'pressure_index', 'global_pressure_sentiment'
    ]
    
    for c in expected_cols:
        if c not in summary.columns:
            summary[c] = 0
            
    summary = summary[expected_cols]

    os.makedirs(os.path.dirname(OUTPUT_CSV), exist_ok=True)
    summary.to_csv(OUTPUT_CSV, index=False)
    
    print(f"Analysis complete. Tabella salvata in: {OUTPUT_CSV}")
    print("\nTop 5 Aeroporti per Mensioni sui Ritardi:")
    print(summary[['airport_code', 'total_mentions', 'global_weighted_sentiment', 'pressure_index', 'global_pressure_sentiment']].head())

if __name__ == "__main__":
    main()