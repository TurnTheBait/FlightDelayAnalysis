import pandas as pd
import os
import matplotlib.pyplot as plt
import seaborn as sns
from fuzzywuzzy import process
import sys
import numpy as np
from geopy.geocoders import Nominatim
from geopy.distance import geodesic
import time

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

def get_city_coordinates_cached(city_names, cache_file='city_coords_cache.csv'):
    geolocator = Nominatim(user_agent="flight_delay_analysis_thesis")
    
    cache_path = os.path.join(BACKEND_DIR, 'data', 'processed', 'population', cache_file)
    if os.path.exists(cache_path):
        df_cache = pd.read_csv(cache_path)
        cache = dict(zip(df_cache['city'], list(zip(df_cache['lat'], df_cache['lon']))))
    else:
        cache = {}
        
    coords = {}
    updated = False
    
    print(f"Geocoding {len(city_names)} cities...")
    for city in city_names:
        if city in cache:
            coords[city] = cache[city]
        else:
            try:
                location = geolocator.geocode(city)
                if location:
                    coords[city] = (location.latitude, location.longitude)
                    cache[city] = (location.latitude, location.longitude)
                    updated = True
                    print(f"Geocoded: {city}")
                else:
                    print(f"Could not geocode: {city}")
                    coords[city] = None
                time.sleep(1)
            except Exception as e:
                 print(f"Error geocoding {city}: {e}")
                 coords[city] = None

    if updated:
        df_save = pd.DataFrame([(k, v[0], v[1]) for k, v in cache.items() if v is not None], columns=['city', 'lat', 'lon'])
        df_save.to_csv(cache_path, index=False)
        
    return coords

def match_cities(df_airports, df_population):
    print("Matching airports to cities based on population data...")
    mapping = []
    pop_cities = df_population['city_name'].unique().tolist()
    
    for idx, row in df_airports.iterrows():
        airport_code = row['ident']
        municipality = str(row['municipality'])
        airport_lat = row['latitude_deg']
        airport_lon = row['longitude_deg']
        
        match, score = process.extractOne(municipality, pop_cities)
        
        final_match = match
        final_score = score
        
        if score < 85:
             name = str(row['name'])
             match_name, score_name = process.extractOne(name, pop_cities)
             if score_name > score:
                 final_match = match_name
                 final_score = score_name
        
        if final_score >= 80:
             mapping.append({
                 'airport_code': airport_code,
                 'municipality': municipality,
                 'matched_city': final_match,
                 'match_score': final_score,
                 'airport_lat': airport_lat,
                 'airport_lon': airport_lon
             })

    df_mapping = pd.DataFrame(mapping)
    print(f"Matched {len(df_mapping)} airports to population data.")
    return df_mapping

def calculate_effective_population(df_merged):
    print("Calculating effective noise-exposed population...")
    
    unique_cities = df_merged['matched_city'].unique()
    city_coords = get_city_coordinates_cached(unique_cities)
    
    distances = []
    effective_populations = []
    
    for idx, row in df_merged.iterrows():
        city = row['matched_city']
        
        if city in city_coords and city_coords[city] is not None:
            city_lat, city_lon = city_coords[city]
            airport_coords = (row['airport_lat'], row['airport_lon'])
            
            dist_km = geodesic(airport_coords, (city_lat, city_lon)).km
            distances.append(dist_km)
            
            REFERENCE_DIST = 10.0
            weight = 1 / (1 + (dist_km / REFERENCE_DIST)**2)
            
            eff_pop = row['population'] * weight
            effective_populations.append(eff_pop)
            
        else:
            distances.append(None)
            effective_populations.append(None)
            
    df_merged['distance_airport_city_km'] = distances
    df_merged['effective_population'] = effective_populations
    
    df_final = df_merged.dropna(subset=['effective_population'])
    print(f"Retained {len(df_final)} airports with valid distance data.")
    
    return df_final

def analyze_correlation(df_merged):
    print("\nAnalyzing correlations...")
    
    corr_raw = df_merged[['population', 'avg_sentiment']].corr().iloc[0,1]
    corr_eff = df_merged[['effective_population', 'avg_sentiment']].corr().iloc[0,1]
    
    print(f"Correlation (Raw Population): {corr_raw:.4f}")
    print(f"Correlation (Effective Population): {corr_eff:.4f}")
    
    plt.figure(figsize=(14, 6))
    
    plt.subplot(1, 2, 1)
    sns.scatterplot(data=df_merged, x='population', y='avg_sentiment', hue='distance_airport_city_km', size='distance_airport_city_km', sizes=(20, 200), alpha=0.7)
    plt.xscale('log')
    plt.title(f'Raw Population vs Sentiment\ncorr={corr_raw:.2f}')
    plt.xlabel('City Population (Log Scale)')
    plt.ylabel('Avg Noise Sentiment')
    
    plt.subplot(1, 2, 2)
    sns.scatterplot(data=df_merged, x='effective_population', y='avg_sentiment', hue='distance_airport_city_km', size='distance_airport_city_km', sizes=(20, 200), alpha=0.7)
    plt.xscale('log')
    plt.title(f'Noise-Weighted Population vs Sentiment\ncorr={corr_eff:.2f}')
    plt.xlabel('Effective Population (Log Scale)')
    plt.ylabel('Avg Noise Sentiment')
    
    output_path = os.path.join(FIGURES_RESULTS_DIR, 'sentiment_noise_vs_population_weighted.png')
    plt.savefig(output_path)
    print(f"Saved scatter plot to {output_path}")

def main():
    df_airports, df_sentiment, df_population = load_data()
    if df_airports is None: return
    
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
    
    df_merged = pd.merge(df_mapped_pop, df_sent_agg, on='airport_code', how='inner')
    
    df_final = calculate_effective_population(df_merged)
    
    print(f"Final dataset for analysis: {len(df_final)} airports.")
    
    df_final.to_csv(os.path.join(TABLES_RESULTS_DIR, 'population_sentiment_noise_weighted.csv'), index=False)
    
    analyze_correlation(df_final)

if __name__ == "__main__":
    main()