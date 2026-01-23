import pandas as pd
import os
import numpy as np

current_script_dir = os.path.dirname(os.path.abspath(__file__))
src_dir = os.path.dirname(current_script_dir)
backend_dir = os.path.dirname(src_dir)

SCORED_DATA_PATH = os.path.join(backend_dir, 'data', 'sentiment', 'sentiment_scored.csv')
AIRPORTS_PATH = os.path.join(backend_dir, 'data', 'processed', 'airports', 'airports_filtered.csv')

OUTPUT_CSV = os.path.join(backend_dir, 'results', 'tables', 'airport_analysis_summary.csv')


def main():
    if not os.path.exists(SCORED_DATA_PATH):
        print(f"ERRORE: Non trovo {SCORED_DATA_PATH}")
        return

    print(f"Caricamento dati analizzati da: {SCORED_DATA_PATH}")
    df_scored = pd.read_csv(SCORED_DATA_PATH)
    
    print(f"Caricamento anagrafica aeroporti da: {AIRPORTS_PATH}")
    df_airports = pd.read_csv(AIRPORTS_PATH, low_memory=False)

    stats = df_scored.groupby(['airport_code', 'source']).agg(
        count=('text', 'count'),
        avg_score=('stars_score', 'mean') 
    ).reset_index()

    pivot_stats = stats.pivot(index='airport_code', columns='source', values=['count', 'avg_score'])
    pivot_stats.columns = [f"{str(col[1]).lower()}_{col[0]}" for col in pivot_stats.columns]
    pivot_stats = pivot_stats.reset_index()
    summary = df_airports[['ident', 'name', 'iso_country', 'municipality']].copy()
    summary = summary.rename(columns={'ident': 'airport_code'})

    summary = summary.merge(pivot_stats, on='airport_code', how='left')

    count_cols = [c for c in summary.columns if c.endswith('_count')]
    
    for col in count_cols:
        summary[col] = summary[col].fillna(0).astype(int)

    summary['total_mentions'] = summary[count_cols].sum(axis=1)

    def calculate_weighted_sentiment(row):
        total_score_sum = 0
        total_weight_sum = 0
        
        score_cols = [c for c in summary.columns if c.endswith('_avg_score')]
        
        for s_col in score_cols:
            c_col = s_col.replace('_avg_score', '_count')
            
            if c_col in row and pd.notnull(row[s_col]):
                weight = row[c_col]
                if weight > 0:
                    total_score_sum += row[s_col] * weight
                    total_weight_sum += weight
        
        if total_weight_sum > 0:
            return total_score_sum / total_weight_sum
        return np.nan

    summary['global_sentiment'] = summary.apply(calculate_weighted_sentiment, axis=1)

    summary = summary.sort_values('total_mentions', ascending=False)
    summary = summary[summary['total_mentions'] > 0]

    os.makedirs(os.path.dirname(OUTPUT_CSV), exist_ok=True)
    summary.to_csv(OUTPUT_CSV, index=False)
    
    print(f"Analysis complete. Tabella salvata in: {OUTPUT_CSV}")
    print(summary[['airport_code', 'iso_country', 'total_mentions', 'global_sentiment']].head())

if __name__ == "__main__":
    main()