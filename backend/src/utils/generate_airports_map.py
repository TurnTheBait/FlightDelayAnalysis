import pandas as pd
import folium
import os
import sys

current_script_dir = os.path.dirname(os.path.abspath(__file__))
src_dir = os.path.dirname(current_script_dir)
backend_dir = os.path.dirname(src_dir)

AIRPORTS_CSV_PATH = os.path.join(backend_dir, 'data', 'processed', 'airports', 'airports_filtered.csv')
OUTPUT_HTML_PATH = os.path.join(backend_dir, 'results', 'figures', 'airports_map.html')

def generate_map():
    if not os.path.exists(AIRPORTS_CSV_PATH):
        print(f"Error: File not found {AIRPORTS_CSV_PATH}")
        return

    print("Loading airport data...")
    df = pd.read_csv(AIRPORTS_CSV_PATH)

    df = df.dropna(subset=['latitude_deg', 'longitude_deg'])
    
    europe_center = [54.5260, 15.2551] 
    
    print("Generating Folium map...")
    m = folium.Map(location=europe_center, zoom_start=4, tiles="CartoDB positron")

    for idx, row in df.iterrows():
        folium.CircleMarker(
            location=[row['latitude_deg'], row['longitude_deg']],
            radius=4,
            popup=f"{row['name']} ({row['iata_code']})",
            color="blue",
            fill=True,
            fill_color="blue",
            fill_opacity=0.7
        ).add_to(m)
        
    os.makedirs(os.path.dirname(OUTPUT_HTML_PATH), exist_ok=True)
    m.save(OUTPUT_HTML_PATH)
    print(f"Interactive map saved to: {OUTPUT_HTML_PATH}")
    
if __name__ == "__main__":
    generate_map()
