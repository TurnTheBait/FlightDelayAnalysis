import pandas as pd
import folium
from folium.plugins import HeatMap
import os
import sys

current_script_dir = os.path.dirname(os.path.abspath(__file__))
src_dir = os.path.dirname(current_script_dir)
backend_dir = os.path.dirname(src_dir)

AIRPORTS_CSV_PATH = os.path.join(backend_dir, 'data', 'processed', 'airports', 'airports_filtered.csv')
RAW_AIRPORTS_CSV_PATH = os.path.join(backend_dir, 'data', 'raw', 'airports', 'airports.csv')
DELAYS_CSV_PATH = os.path.join(backend_dir, 'data', 'processed', 'delays', 'delays_consolidated_filtered.csv')
POPULATION_CSV_PATH = os.path.join(backend_dir, 'data', 'processed', 'population', 'city_population.csv')
SENTIMENT_SUMMARY_PATH = os.path.join(backend_dir, 'results', 'tables', 'airport_volume_analysis_summary.csv')
SENTIMENT_DELAY_PATH = os.path.join(backend_dir, 'results', 'tables', 'delay', 'sentiment_aggregated_delay.csv')
SENTIMENT_NOISE_PATH = os.path.join(backend_dir, 'results', 'tables', 'noise', 'sentiment_aggregated_noise.csv')
OUTPUT_HTML_PATH = os.path.join(backend_dir, 'results', 'figures', 'airports_map.html')

def generate_map():
    if not os.path.exists(AIRPORTS_CSV_PATH):
        print(f"Error: File not found {AIRPORTS_CSV_PATH}")
        return

    print("Loading data...")
    airports_df = pd.read_csv(AIRPORTS_CSV_PATH)
    
    heatmap_df = pd.DataFrame()
    if os.path.exists(POPULATION_CSV_PATH) and os.path.exists(RAW_AIRPORTS_CSV_PATH):
        print("Loading population and raw airport data for heatmap...")
        pop_df = pd.read_csv(POPULATION_CSV_PATH)
        raw_airports_df = pd.read_csv(RAW_AIRPORTS_CSV_PATH)
        
        pop_df['iso_country'] = pop_df['city_code'].str[:2]
        country_map = {'UK': 'GB', 'EL': 'GR'}
        pop_df['iso_country'] = pop_df['iso_country'].replace(country_map)
        
        city_coords = raw_airports_df[['municipality', 'iso_country', 'latitude_deg', 'longitude_deg']].dropna()
        city_coords = city_coords.drop_duplicates(subset=['municipality', 'iso_country'])
        
        heatmap_df = pd.merge(
            pop_df, 
            city_coords, 
            left_on=['city_name', 'iso_country'], 
            right_on=['municipality', 'iso_country'], 
            how='inner'
        )
        print(f"Matched {len(heatmap_df)} cities for heatmap out of {len(pop_df)} population entries.")
        
        airports_df = pd.merge(airports_df, pop_df[['city_name', 'population']], 
                               left_on='municipality', right_on='city_name', how='left')
        airports_df['population'] = airports_df['population'].fillna(0)
    else:
        print("Warning: Population or Raw Airport file not found. Heatmap will be limited.")
        airports_df['population'] = 0

    if os.path.exists(DELAYS_CSV_PATH):
        print("Loading flight data (counting departures)...")
        flights_df = pd.read_csv(DELAYS_CSV_PATH, usecols=['SchedDepApt'])
        flight_counts = flights_df['SchedDepApt'].value_counts().reset_index()
        flight_counts.columns = ['iata_code', 'flight_count']
        
        airports_df = pd.merge(airports_df, flight_counts, on='iata_code', how='left')
        airports_df['flight_count'] = airports_df['flight_count'].fillna(0)
    else:
        print(f"Warning: Delays file not found at {DELAYS_CSV_PATH}")
        airports_df['flight_count'] = 0

    airports_df = airports_df.dropna(subset=['latitude_deg', 'longitude_deg'])

    print("Loading sentiment data...")
    if os.path.exists(SENTIMENT_SUMMARY_PATH):
        df_summary = pd.read_csv(SENTIMENT_SUMMARY_PATH)
        airports_df = pd.merge(airports_df, df_summary[['airport_code', 'global_sentiment']], 
                               left_on='iata_code', right_on='airport_code', how='left')
    else:
        airports_df['global_sentiment'] = None

    if os.path.exists(SENTIMENT_DELAY_PATH):
        df_delay = pd.read_csv(SENTIMENT_DELAY_PATH)
        df_delay = df_delay.rename(columns={'mean': 'sentiment_delay'})
        airports_df = pd.merge(airports_df, df_delay[['airport_code', 'sentiment_delay']], 
                               left_on='iata_code', right_on='airport_code', how='left')
    else:
        airports_df['sentiment_delay'] = None

    if os.path.exists(SENTIMENT_NOISE_PATH):
        df_noise = pd.read_csv(SENTIMENT_NOISE_PATH)
        df_noise = df_noise.rename(columns={'mean': 'sentiment_noise'})
        airports_df = pd.merge(airports_df, df_noise[['airport_code', 'sentiment_noise']], 
                               left_on='iata_code', right_on='airport_code', how='left')
    else:
        airports_df['sentiment_noise'] = None
    
    europe_center = [54.5260, 15.2551] 
    
    print("Generating Folium map...")
    m = folium.Map(location=europe_center, zoom_start=4, tiles="CartoDB positron")

    if not heatmap_df.empty:
        heat_data = heatmap_df[['latitude_deg', 'longitude_deg', 'population']].values.tolist()
    else:
        heat_data = airports_df[airports_df['population'] > 0][['latitude_deg', 'longitude_deg', 'population']].values.tolist()
        
    if heat_data:
        HeatMap(heat_data, name="Population Density", radius=15, blur=10, max_zoom=10).add_to(m)

    max_flights = airports_df['flight_count'].max()
    min_size = 10
    max_size = 30
    
    for idx, row in airports_df.iterrows():
        flights = row['flight_count']
        if max_flights > 0 and flights > 0:
            size = min_size + (flights / max_flights) * (max_size - min_size)
        else:
            size = min_size
            
        icon_html = f'''
            <div style="font-size: {size}px; color: black; text-shadow: 2px 2px 4px rgba(255,255,255,0.5);">
                <i class="fa fa-plane"></i>
            </div>
        '''
        
        def fmt_score(val):
            return f"{val:.1f}" if pd.notnull(val) else "N/A"

        pop_sent_overall = fmt_score(row.get('global_sentiment'))
        pop_sent_delay = fmt_score(row.get('sentiment_delay'))
        pop_sent_noise = fmt_score(row.get('sentiment_noise'))

        popup_text = f"""
        <div style="font-family: Arial; font-size: 13px; width: 220px;">
            <b style="font-size: 14px;">{row['name']}</b> ({row['iata_code']})<br>
            <hr style="margin: 5px 0;">
            <b>Flights:</b> {int(flights)}<br>
            <b>Population:</b> {int(row['population']):,}<br>
            <br>
            <b>Sentiment (0-10):</b><br>
            • Overall: <b>{pop_sent_overall}</b><br>
            • Delay: <b>{pop_sent_delay}</b><br>
            • Noise: <b>{pop_sent_noise}</b>
        </div>
        """

        folium.Marker(
            location=[row['latitude_deg'], row['longitude_deg']],
            icon=folium.DivIcon(html=icon_html, icon_size=(size, size), icon_anchor=(size/2, size/2)),
            popup=folium.Popup(popup_text, max_width=300)
        ).add_to(m)

    legend_html = '''
     <div style="position: fixed; 
     bottom: 50px; left: 50px; width: 250px; height: 180px; 
     border:2px solid grey; z-index:9999; font-size:14px;
     background-color:white; opacity: 0.9; padding: 10px; border-radius: 5px;">
     <b>Map Legend</b><br>
     <i class="fa fa-plane" style="font-size: 10px; color: black;"></i>&nbsp; Low Traffic Airport<br>
     <i class="fa fa-plane" style="font-size: 30px; color: black;"></i>&nbsp; High Traffic Airport<br>
     <br>
     <b>Heatmap (Population)</b><br>
     <div style="background: linear-gradient(to right, blue, lime, yellow, red); height: 10px; width: 100%;"></div>
     <span style="float:left">Low</span><span style="float:right">High</span>
     </div>
     '''
    m.get_root().html.add_child(folium.Element(legend_html))

    os.makedirs(os.path.dirname(OUTPUT_HTML_PATH), exist_ok=True)
    m.save(OUTPUT_HTML_PATH)
    print(f"Interactive map saved to: {OUTPUT_HTML_PATH}")
    
if __name__ == "__main__":
    generate_map()

