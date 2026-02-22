import pandas as pd
import os
import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np
import sys
import geopandas as gpd
from shapely.geometry import Point, Polygon
from geopy.distance import geodesic
import rasterio
from rasterio.mask import mask

CURRENT_FILE = os.path.abspath(__file__)
ANALYSIS_DIR = os.path.dirname(CURRENT_FILE)
SRC_DIR = os.path.dirname(ANALYSIS_DIR)
BACKEND_DIR = os.path.dirname(SRC_DIR)

AIRPORTS_CSV_PATH = os.path.join(BACKEND_DIR, 'data', 'processed', 'airports', 'airports_filtered.csv')
SENTIMENT_CSV_PATH = os.path.join(BACKEND_DIR, 'data', 'sentiment', 'sentiment_results_noise.csv')
VOLUME_CSV_PATH = os.path.join(BACKEND_DIR, 'results', 'tables', 'airport_volume_analysis_summary.csv')
RASTER_PATH = os.path.join(BACKEND_DIR, 'data', 'raw', 'population', 'global_pop_2026_CN_1km_R2025A_UA_v1.tif')

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
        df_volume = pd.read_csv(VOLUME_CSV_PATH)
        return df_airports, df_sentiment, df_volume
    except Exception as e:
        print(f"Error loading data: {e}")
        return None, None, None

def create_10km_buffer_polygon(lat, lon):
    """
    Creates a 10km geodetic buffer polygon around a given lat/lon point.
    Uses geopy to calculate points at 10 degrees intervals.
    """
    origin = (lat, lon)
    points = []
    for angle in range(0, 360, 10):
        dest = geodesic(kilometers=10).destination(origin, bearing=angle)
        points.append((dest.longitude, dest.latitude))
    return Polygon(points)

def extract_population_from_raster(df_airports):
    """
    Extracts total population within a 10km radius of each airport 
    using the World Population raster.
    """
    print(f"Extracting population from raster: {RASTER_PATH}")
    if not os.path.exists(RASTER_PATH):
        print(f"❌ ERROR: Raster file not found at {RASTER_PATH}.")
        print("Please place the world population .tif file there before running the script.")
        print("For now, generating mock population data for testing purposes.")
        df_airports['population_10km'] = np.random.randint(50000, 2000000, size=len(df_airports))
        return df_airports

    buffers = []
    for idx, row in df_airports.iterrows():
        poly = create_10km_buffer_polygon(row['latitude_deg'], row['longitude_deg'])
        buffers.append(poly)
    
    df_airports['geometry'] = buffers
    gdf_airports = gpd.GeoDataFrame(df_airports, geometry='geometry', crs="EPSG:4326")
    
    populations = []
    try:
        with rasterio.open(RASTER_PATH) as src:
            for idx, row in gdf_airports.iterrows():
                try:
                    out_image, out_transform = mask(src, [row.geometry], crop=True, nodata=np.nan)
                    pop_sum = np.nansum(out_image)
                    populations.append(pop_sum)
                except ValueError:
                    populations.append(0)
    except Exception as e:
        print(f"Error reading raster: {e}")
        populations = [np.nan] * len(gdf_airports)

    gdf_airports['population_10km'] = populations
    return pd.DataFrame(gdf_airports.drop(columns='geometry'))

def analyze_correlation(df_merged):
    print("\nAnalyzing correlations with Airport Size Normalization...")
    
    df_merged = df_merged.dropna(subset=['population_10km', 'total_flights', 'avg_sentiment'])
    
    df_merged['capita_normalized'] = df_merged['population_10km'] / df_merged['total_flights']
    
    corr_raw = df_merged[['population_10km', 'avg_sentiment']].corr().iloc[0,1]
    corr_norm = df_merged[['capita_normalized', 'avg_sentiment']].corr().iloc[0,1]
    
    print(f"Correlation (Raw Population 10km vs Sentiment): {corr_raw:.4f}")
    print(f"Correlation (Capita Normalized by Flights vs Sentiment): {corr_norm:.4f}")
    
    sns.set_theme(style="whitegrid", context="talk")
    fig, axes = plt.subplots(1, 2, figsize=(16, 7))
    
    def get_extreme_points(df, x_col, y_col, n=3):
        extremes = pd.concat([
            df.nlargest(n, x_col),
            df.nsmallest(n, x_col),
            df.nlargest(n, y_col),
            df.nsmallest(n, y_col)
        ]).drop_duplicates(subset=['airport_code'])
        return extremes
        
    ax1 = axes[0]
    sns.scatterplot(
        data=df_merged, 
        x='population_10km', 
        y='avg_sentiment', 
        size='total_flights', 
        sizes=(40, 400), 
        alpha=0.6,
        color='royalblue',
        edgecolor='black',
        linewidth=0.5,
        ax=ax1,
        legend=False
    )
    
    extremes_1 = get_extreme_points(df_merged, 'population_10km', 'avg_sentiment', n=3)
    for _, row in extremes_1.iterrows():
        ax1.annotate(row['airport_code'], 
                     (row['population_10km'], row['avg_sentiment']), 
                     xytext=(5, 5), textcoords='offset points', 
                     fontsize=9, fontweight='bold', color='darkblue')

    sns.regplot(
        data=df_merged, x='population_10km', y='avg_sentiment', 
        scatter=False, ax=ax1, color='darkred', line_kws={'linestyle':'--', 'alpha':0.8}
    )
    ax1.set_xscale('log')
    ax1.set_title(f'10km Buffer Population vs Noise Sentiment\n(Pearson r = {corr_raw:.2f})', pad=15, fontsize=14, fontweight='bold')
    ax1.set_xlabel('10km Buffer Population (Log Scale)', fontsize=12)
    ax1.set_ylabel('Average Noise Sentiment (1-5)', fontsize=12)
    ax1.tick_params(axis='both', which='major', labelsize=11)
    
    ax2 = axes[1]
    scatter2 = sns.scatterplot(
        data=df_merged, 
        x='capita_normalized', 
        y='avg_sentiment', 
        size='total_flights', 
        sizes=(40, 400), 
        alpha=0.6,
        color='mediumseagreen',
        edgecolor='black',
        linewidth=0.5,
        ax=ax2
    )
    
    extremes_2 = get_extreme_points(df_merged, 'capita_normalized', 'avg_sentiment', n=3)
    for _, row in extremes_2.iterrows():
        ax2.annotate(row['airport_code'], 
                     (row['capita_normalized'], row['avg_sentiment']), 
                     xytext=(5, 5), textcoords='offset points', 
                     fontsize=9, fontweight='bold', color='darkgreen')

    sns.regplot(
        data=df_merged, x='capita_normalized', y='avg_sentiment', 
        scatter=False, ax=ax2, color='darkred', line_kws={'linestyle':'--', 'alpha':0.8}
    )
    ax2.set_xscale('log')
    ax2.set_title(f'Normalized Population vs Noise Sentiment\n(Pearson r = {corr_norm:.2f})', pad=15, fontsize=14, fontweight='bold')
    ax2.set_xlabel('Population per Scheduled Flight (Log Scale)', fontsize=12)
    ax2.set_ylabel('Average Noise Sentiment (1-5)', fontsize=12)
    ax2.tick_params(axis='both', which='major', labelsize=11)
    
    handles, labels = scatter2.get_legend_handles_labels()
    ax2.legend(handles, labels, title='Total Flights', bbox_to_anchor=(1.05, 1), loc='upper left', fontsize=10, title_fontsize=11)
    
    plt.tight_layout()
    output_path = os.path.join(FIGURES_RESULTS_DIR, 'sentiment_noise_vs_population_raster.png')
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    print(f"Saved scatter plot to {output_path}")

def main():
    df_airports, df_sentiment, df_volume = load_data()
    if df_airports is None: return
    
    print("Aggregating sentiment scores...")
    df_sent_agg = df_sentiment.groupby('airport_code').apply(
        lambda x: np.average(x['combined_score'], weights=x['weight']),
        include_groups=False
    ).reset_index(name='avg_sentiment')
    
    df_airports_pop = extract_population_from_raster(df_airports)
    
    print("Mapping airport codes...")
    icao_to_iata = get_icao_to_iata_mapping(AIRPORTS_CSV_PATH)
    df_airports_pop['airport_code'] = df_airports_pop['ident'].map(icao_to_iata).fillna(df_airports_pop['ident'])
    
    print("Merging datasets...")
    df_merged = pd.merge(df_airports_pop, df_sent_agg, on='airport_code', how='inner')
    df_final = pd.merge(df_merged, df_volume[['airport_code', 'total_flights', 'log_volume']], on='airport_code', how='inner')
    
    print(f"Final dataset for analysis: {len(df_final)} airports.")
    
    output_csv = os.path.join(TABLES_RESULTS_DIR, 'population_sentiment_noise_raster.csv')
    df_final.to_csv(output_csv, index=False)
    print(f"Saved data table to {output_csv}")
    
    analyze_correlation(df_final)

if __name__ == "__main__":
    main()