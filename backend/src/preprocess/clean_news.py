import pandas as pd
import os
from dateutil import parser

current_script_dir = os.path.dirname(os.path.abspath(__file__))
src_dir = os.path.dirname(current_script_dir)
backend_dir = os.path.dirname(src_dir)

INPUT_FILE = os.path.join(backend_dir, 'data', 'sentiment', 'news_raw_full.csv')
OUTPUT_FILE = os.path.join(backend_dir, 'data', 'sentiment', 'news_cleaned.csv')

ACCEPTED_YEARS = [2022,2023, 2024, 2025, 2026]

AVIATION_CONTEXT_WORDS = [
    'airport', 'aeroport', 'flughafen', 'luchthaven', 'aeroporto', 'flygplats',
    'flight', 'volo', 'vuelo', 'flug', 'vlucht', 'flyg',
    'airline', 'aerolínea', 'compagnia aerea', 'luchtvaartmaatschappij',
    'delay', 'ritardo', 'retraso', 'verspätung', 'vertraging',
    'cancel', 'cancellat', 'annullat', 'gestrichen', 'geannuleerd',
    'noise', 'rumore', 'ruido', 'lärm', 'geluid', 'buller',
    'passenger', 'pasajero', 'passagg', 'passagier',
    'runway', 'pista', 'startbahn', 'landebahn',
    'terminal', 'gate', 'baggage', 'bagaglio', 'equipaje', 'gepäck',
    'strike', 'sciopero', 'huelga', 'streik', 'staking',
    'drone', 'uav',
    'traffic', 'traffico', 'tráfico', 'verkehr',
    'turbolenza', 'turbulence', 'turbulencias',
    'emergency', 'emergenza', 'notlandung'
]


EXCLUDE_WORDS = [
    'hiring', 'job', 'vacancy', 'career', 'recruitment', 
    'concert', 'festival', 'band', 'song', 'album', 
    'lego', 'toy', 'game', 
    'sport', 'football', 'match', 'cup' 
]

def check_date(date_str):
    try:
        dt = parser.parse(str(date_str))
        if dt.year in ACCEPTED_YEARS:
            return True
    except:
        return False
    return False

def is_contextually_relevant(row):
    title = str(row['title']).lower()
    city = str(row['search_term']).lower()
    
    if city not in title:
        return False
    
    if any(bad in title for bad in EXCLUDE_WORDS):
        return False

    has_aviation_context = any(word in title for word in AVIATION_CONTEXT_WORDS)
    
    return has_aviation_context

if not os.path.exists(INPUT_FILE):
    print(f"Error: {INPUT_FILE} not found")
    exit()

df = pd.read_csv(INPUT_FILE)

initial_count = len(df)

df = df[df['published'].apply(check_date)]

df = df[df.apply(is_contextually_relevant, axis=1)]

df.to_csv(OUTPUT_FILE, index=False)

print(f"Filtering complete.")
print(f"Initial records: {initial_count}")
print(f"Remaining records: {len(df)}")
print(f"File saved to: {OUTPUT_FILE}")