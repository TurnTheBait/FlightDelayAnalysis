import feedparser
import pandas as pd
import urllib.parse
import time
import os
import random
import json
import socket
import concurrent.futures
import threading
from datetime import datetime
import cloudscraper
from tqdm import tqdm

socket.setdefaulttimeout(60)

current_script_dir = os.path.dirname(os.path.abspath(__file__))
src_dir = os.path.dirname(current_script_dir)
backend_dir = os.path.dirname(src_dir)

AIRPORTS_CSV_PATH = os.path.join(backend_dir, 'data', 'processed', 'airports', 'airports_filtered.csv')
KEYWORDS_JSON_PATH = os.path.join(backend_dir, 'config', 'keywords.json')
OUTPUT_PATH = os.path.join(backend_dir, 'data', 'sentiment', 'news_raw_full.csv')

print_lock = threading.Lock()

COUNTRY_CONFIG = {
    'IT': {'lang_key': 'IT', 'gl': 'IT', 'hl': 'it-IT', 'ceid': 'IT:it'},
    'DE': {'lang_key': 'DE', 'gl': 'DE', 'hl': 'de-DE', 'ceid': 'DE:de'},
    'AT': {'lang_key': 'DE', 'gl': 'AT', 'hl': 'de-AT', 'ceid': 'AT:de'},
    'CH': {'lang_key': 'DE', 'gl': 'CH', 'hl': 'de-CH', 'ceid': 'CH:de'},
    'FR': {'lang_key': 'FR', 'gl': 'FR', 'hl': 'fr-FR', 'ceid': 'FR:fr'},
    'BE': {'lang_key': 'FR', 'gl': 'BE', 'hl': 'fr-BE', 'ceid': 'BE:fr'},
    'ES': {'lang_key': 'ES', 'gl': 'ES', 'hl': 'es-419', 'ceid': 'ES:es'},
    'GB': {'lang_key': 'EN', 'gl': 'GB', 'hl': 'en-GB', 'ceid': 'GB:en'},
    'IE': {'lang_key': 'EN', 'gl': 'IE', 'hl': 'en-IE', 'ceid': 'IE:en'},
    'US': {'lang_key': 'EN', 'gl': 'US', 'hl': 'en-US', 'ceid': 'US:en'}
}

DEFAULT_CONFIG = {'lang_key': 'EN', 'gl': 'US', 'hl': 'en-US', 'ceid': 'US:en'}

def load_data():
    if not os.path.exists(AIRPORTS_CSV_PATH):
        print(f"Error: Airports file not found at {AIRPORTS_CSV_PATH}")
        return None, None
    
    if not os.path.exists(KEYWORDS_JSON_PATH):
        print(f"Error: Keywords config file not found at {KEYWORDS_JSON_PATH}")
        return None, None

    try:
        with open(KEYWORDS_JSON_PATH, 'r', encoding='utf-8') as f:
            keywords_dict = json.load(f)
    except Exception as e:
        print(f"Error reading JSON: {e}")
        return None, None

    try:
        df_airports = pd.read_csv(AIRPORTS_CSV_PATH)
    except Exception as e:
        print(f"Error reading CSV: {e}")
        return None, None
        
    return df_airports, keywords_dict

def get_processed_airports():
    if not os.path.exists(OUTPUT_PATH):
        return set()
    
    try:
        df_existing = pd.read_csv(OUTPUT_PATH)
        if 'airport_code' in df_existing.columns:
            return set(df_existing['airport_code'].unique())
    except Exception:
        pass
    
    return set()

def get_config_for_country(iso_code):
    return COUNTRY_CONFIG.get(str(iso_code).upper(), DEFAULT_CONFIG)

def fetch_feed_with_retry(url, retries=5, delay=5, code="UNK"):
    scraper = cloudscraper.create_scraper()

    for attempt in range(retries):
        try:
            response = scraper.get(url, timeout=30)
            
            if response.status_code == 200:
                feed = feedparser.parse(response.content)
                return feed
            elif response.status_code in [429, 503, 403]:
                wait_time = delay * (2 ** attempt) + random.uniform(5, 10)
                with print_lock:
                    print(f"   [{code}] Hit {response.status_code}, cooling down {wait_time:.1f}s")
                time.sleep(wait_time)
                continue
            else:
                 return None

        except Exception as e:
             if attempt < retries - 1:
                 wait_time = delay * (2 ** attempt)
                 time.sleep(wait_time)
             else:
                 with print_lock:
                     print(f"   [{code}] Failed: {e}")
    
    return None

def process_airport(row, keywords_dict):
    full_name = str(row['name'])
    code = row['ident']
    iso_country = str(row['iso_country'])
    
    city_name = full_name.replace("International", "").replace("Airport", "").replace("Intl", "").split('/')[0].split('(')[0].strip()
    
    config = get_config_for_country(iso_country)
    lang_key = config['lang_key']
    keywords_map = keywords_dict.get(lang_key, keywords_dict['EN'])
    
    airport_news = []
    seen_links = set()
    
    gl = config['gl']
    hl = config['hl']
    ceid = config['ceid']
    
    with print_lock:
        print(f"Processing MISSING: {code} ({city_name})...")

    all_phrases = []
    for category, phrases in keywords_map.items():
        for phrase in phrases:
            all_phrases.append((category, phrase))
            
    with tqdm(total=len(all_phrases), desc=f"[{code}]", leave=False, disable=True) as pbar:
        for category, phrase in all_phrases:
            query = f"{city_name} {phrase} after:2015-01-01"
            encoded_query = urllib.parse.quote(query)
            
            rss_url = f"https://news.google.com/rss/search?q={encoded_query}&hl={hl}&gl={gl}&ceid={ceid}"
            
            try:
                feed = fetch_feed_with_retry(rss_url, code=code)
                
                if not feed or not feed.entries:
                    time.sleep(random.uniform(1.0, 2.0))
                    continue
                    
                for entry in feed.entries:
                    if entry.link in seen_links:
                        continue
                    
                    published_parsed = entry.get("published_parsed")
                    if published_parsed:
                        date_str = time.strftime("%Y-%m-%d %H:%M:%S", published_parsed)
                    else:
                        date_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

                    airport_news.append({
                        "airport_code": code,
                        "search_term": city_name,
                        "full_name": full_name,
                        "category": category,
                        "keyword_used": phrase,
                        "title": entry.title,
                        "link": entry.link,
                        "published": entry.published if 'published' in entry else date_str,
                        "source": entry.source.title if 'source' in entry else "Google News"
                    })
                    
                    seen_links.add(entry.link)
                    
            except Exception as e:
                pass
            
            time.sleep(random.uniform(2.0, 4.0))

    with print_lock:
         print(f"   [{code}] DONE. Saved {len(airport_news)} articles.")
         
    return airport_news

def main():
    df_airports, keywords_dict = load_data()
    if df_airports is None:
        return

    processed_codes = get_processed_airports()
    print(f"Found {len(processed_codes)} airports already processed in {OUTPUT_PATH}")
    
    df_missing = df_airports[~df_airports['ident'].isin(processed_codes)]
    
    if df_missing.empty:
        print("All airports have been processed. Exiting.")
        return

    print(f"Resuming scraping for {len(df_missing)} remaining airports...")
    
    all_news = []
    MAX_WORKERS = 1
    
    with concurrent.futures.ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        future_to_airport = {
            executor.submit(process_airport, row, keywords_dict): row['ident'] 
            for index, row in df_missing.iterrows()
        }
        
        for future in concurrent.futures.as_completed(future_to_airport):
            airport_code = future_to_airport[future]
            try:
                data = future.result()
                
                # Append immediately to CSV to save progress
                if data:
                    df_chunk = pd.DataFrame(data)
                    file_exists = os.path.isfile(OUTPUT_PATH) and os.path.getsize(OUTPUT_PATH) > 0
                    df_chunk.to_csv(OUTPUT_PATH, mode='a', header=not file_exists, index=False)
                    
            except Exception as exc:
                with print_lock:
                    print(f"   [{airport_code}] Error: {exc}")

    print(f"\nCompleted resume job. Data appended to {OUTPUT_PATH}")

if __name__ == "__main__":
    main()