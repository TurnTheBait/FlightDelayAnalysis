import pandas as pd
import os
import matplotlib.pyplot as plt
import seaborn as sns
from fuzzywuzzy import process
import sys
import numpy as np

CURRENT_FILE = os.path.abspath(__file__)
ANALYSIS_DIR = os.path.dirname(CURRENT_FILE)
SRC_DIR = os.path.dirname(ANALYSIS_DIR)
BACKEND_DIR = os.path.dirname(SRC_DIR)

AIRPORTS_CSV_PATH = os.path.join(BACKEND_DIR, 'data', 'processed', 'airports', 'airports_filtered.csv')
SENTIMENT_CSV_PATH = os.path.join(BACKEND_DIR, 'data', 'sentiment', 'sentiment_results_noise.csv')
POPULATION_CSV_PATH = os.path.join(BACKEND_DIR, 'data', 'processed', 'population', 'city_population.csv')

sys.path.append(SRC_DIR)
from utils.airport_utils import get_icao_to_iata_mapping

FIGURES_RESULTS_DIR = os.path.join(BACKEND_DIR, 'results', 'figures', 'population_analysis')
TABLES_RESULTS_DIR = os.path.join(BACKEND_DIR, 'results', 'tables', 'population_analysis')

os.makedirs(FIGURES_RESULTS_DIR, exist_ok=True)
os.makedirs(TABLES_RESULTS_DIR, exist_ok=True)

def load_data():
    print("Loading data...")
    try:
        df_airports = pd.read_csv(AIRPORTS_CSV_PATH)
        df_sentiment = pd.read_csv(SENTIMENT_CSV_PATH)
        df_population = pd.read_csv(POPULATION_CSV_PATH)
        return df_airports, df_sentiment, df_population
    except Exception as e:
        print(f"Error loading data: {e}")
        return None, None, None

def match_cities(df_airports, df_population):
    print("Matching airports to cities based on population data...")
    mapping = []
    pop_cities = df_population['city_name'].unique().tolist()
    
    for idx, row in df_airports.iterrows():
        airport_code = row['ident']
        municipality = str(row['municipality'])
        
        if municipality == "London":
            pass 
            
        match, score = process.extractOne(municipality, pop_cities)
        
        if score >= 85: 
             mapping.append({
                 'airport_code': airport_code,
                 'municipality': municipality,
                 'matched_city': match,
                 'match_score': score
             })
        else:
             name = str(row['name'])
             match_name, score_name = process.extractOne(name, pop_cities)
             if score_name >= 85:
                 mapping.append({
                     'airport_code': airport_code,
                     'municipality': municipality,
                     'matched_city': match_name,
                     'match_score': score_name
                 })

    df_mapping = pd.DataFrame(mapping)
    print(f"Matched {len(df_mapping)} airports to population data.")
    return df_mapping

def analyze_correlation(df_merged):
    print("\nAnalyzing correlations...")
    corr = df_merged[['population', 'avg_sentiment']].corr()
    print("Correlation Matrix:")
    print(corr)
    
    plt.figure(figsize=(12, 8))
    sns.scatterplot(data=df_merged, x='population', y='avg_sentiment', hue='match_score', size='population', sizes=(20, 500), alpha=0.7)
    
    for i, row in df_merged.iterrows():
        if row['population'] > 1_000_000 or row['avg_sentiment'] < 2 or row['avg_sentiment'] > 4:
             plt.text(row['population'], row['avg_sentiment'], row['airport_code'], fontsize=9, alpha=0.7)

    plt.xscale('log')
    plt.title(f'Airport Noise Sentiment vs City Population (Log Scale)\nCorrelation: {corr.iloc[0,1]:.2f}')
    plt.xlabel('City Population (Log Scale)')
    plt.ylabel('Average Noise Sentiment Score')
    plt.grid(True, which="both", ls="-", alpha=0.2)
    
    output_path = os.path.join(FIGURES_RESULTS_DIR, 'sentiment_noise_vs_population.png')
    plt.savefig(output_path)
    print(f"Saved scatter plot to {output_path}")

def main():
    df_airports, df_sentiment, df_population = load_data()
    if df_airports is None: return
    
    # Aggregazione basata sui pesi corretti (weighted_score)
    df_sent_agg = df_sentiment.groupby('airport_code').apply(
        lambda x: np.average(x['stars_score'], weights=x['time_weight'])
    ).reset_index(name='avg_sentiment')
    
    df_mapping = match_cities(df_airports, df_population)
    
    if df_mapping.empty:
        print("No matches found. Exiting.")
        return

    df_mapped_pop = pd.merge(df_mapping, df_population, left_on='matched_city', right_on='city_name', how='left')

    icao_to_iata = get_icao_to_iata_mapping(AIRPORTS_CSV_PATH)
    df_mapped_pop['airport_code'] = df_mapped_pop['airport_code'].map(icao_to_iata).fillna(df_mapped_pop['airport_code'])
    
    df_final = pd.merge(df_mapped_pop, df_sent_agg, on='airport_code', how='inner')
    
    print(f"Final dataset for analysis: {len(df_final)} airports.")
    
    df_final.to_csv(os.path.join(TABLES_RESULTS_DIR, 'population_sentiment_noise_merged.csv'), index=False)
    
    analyze_correlation(df_final)

if __name__ == "__main__":
    main()