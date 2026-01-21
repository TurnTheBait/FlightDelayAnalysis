import pandas as pd
import os
import re
import json
from datetime import datetime

current_script_dir = os.path.dirname(os.path.abspath(__file__))
src_dir = os.path.dirname(current_script_dir)
backend_dir = os.path.dirname(src_dir)

INPUT_FILE = os.path.join(backend_dir, 'data', 'sentiment', 'news_raw_full.csv')
KEYWORDS_JSON_PATH = os.path.join(backend_dir, 'config', 'keywords.json')
OUTPUT_FILE = os.path.join(backend_dir, 'data', 'sentiment', 'news_cleaned.csv')

AVIATION_CONTEXT_KEYWORDS = [
    'airport', 'aeroporto', 'flughafen', 'aéroport', 'aeropuerto',
    'flight', 'volo', 'flug', 'vol', 'vuelo',
    'airline', 'compagnia aerea', 'fluggesellschaft', 'aerolínea', 'compagnie aérienne',
    'plane', 'aereo', 'flugzeug', 'avion', 'avión', 'aircraft', 'jet',
    'passenger', 'passeggeri', 'passagier', 'passager', 'pasajero',
    'terminal', 'gate', 'runway', 'pista', 'tarmac',
    'luggage', 'baggage', 'bagaglio', 'gepäck', 'equipaje', 'valigia',
    'aviation', 'aviazione', 'luftfahrt', 'aviación',
    'pilot', 'pilota', 'pilote', 'piloto',
    'cabin crew', 'equipaggio', 'bordpersonal', 'tripulación',
    'enac', 'iata', 'icao', 'atc', 'controllo traffico', 'air traffic'
]

def load_sentiment_keywords(json_path):
    if not os.path.exists(json_path):
        print(f"Error: Keywords JSON not found at {json_path}")
        return set()
    
    try:
        with open(json_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
            
        all_keywords = set()
        for lang in data:
            for category in data[lang]:
                for word in data[lang][category]:
                    all_keywords.add(word.lower())
        return all_keywords
    except Exception as e:
        print(f"Error reading JSON: {e}")
        return set()

def clean_text(text):
    if not isinstance(text, str):
        return ""
    
    text = re.sub(r'<[^>]+>', '', text)      
    text = re.sub(r'http\S+', '', text)      
    text = re.sub(r'\s+', ' ', text).strip() 
    return text.lower()

def build_regex_pattern(keywords):
    sorted_keywords = sorted(list(keywords), key=len, reverse=True)
    pattern = r'\b(?:' + '|'.join(map(re.escape, sorted_keywords)) + r')\b'
    
    return re.compile(pattern, re.IGNORECASE)

def is_strictly_relevant(row, context_pattern, sentiment_pattern):
    title = clean_text(str(row.get('title', '')))
    
    has_aviation_context = bool(context_pattern.search(title))
    has_sentiment_keyword = bool(sentiment_pattern.search(title))
    
    return has_aviation_context and has_sentiment_keyword

def main():
    if not os.path.exists(INPUT_FILE):
        print(f"Error: Input file not found: {INPUT_FILE}")
        return

    print(f"Loading sentiment keywords from: {KEYWORDS_JSON_PATH}")
    sentiment_keywords = load_sentiment_keywords(KEYWORDS_JSON_PATH)
    
    if not sentiment_keywords:
        print("No sentiment keywords loaded. Exiting.")
        return

    print(f"Compiling Regex Patterns with Word Boundaries (\\b)...")
    context_pattern = build_regex_pattern(AVIATION_CONTEXT_KEYWORDS)
    sentiment_pattern = build_regex_pattern(sentiment_keywords)
    print(f"Reading raw news from: {INPUT_FILE}")
    try:
        df = pd.read_csv(INPUT_FILE)
    except Exception as e:
        print(f"Error reading CSV: {e}")
        return

    initial_count = len(df)
    print(f"Initial articles: {initial_count}")

    if 'published' in df.columns:
        df['published_dt'] = pd.to_datetime(df['published'], errors='coerce', utc=True)
        
        df = df[df['published_dt'].dt.year >= 2022]
        print(f"Articles after date filter (>= 2022): {len(df)}")
    else:
        print("Warning: 'published' column not found, skipping date filter.")

    df_filtered = df[df.apply(lambda row: is_strictly_relevant(row, context_pattern, sentiment_pattern), axis=1)]
    
    df_filtered = df_filtered.drop_duplicates(subset=['title', 'link'])
    
    if 'published_dt' in df_filtered.columns:
        df_filtered = df_filtered.drop(columns=['published_dt'])

    removed_count = initial_count - len(df_filtered)
    
    print(f"Removed total of {removed_count} articles (Date < 2022 OR Irrelevant Context/False Positives).")
    print(f"Final valid aviation articles: {len(df_filtered)}")

    os.makedirs(os.path.dirname(OUTPUT_FILE), exist_ok=True)
    df_filtered.to_csv(OUTPUT_FILE, index=False)
    print(f"Saved cleaned data to: {OUTPUT_FILE}")

if __name__ == "__main__":
    main()