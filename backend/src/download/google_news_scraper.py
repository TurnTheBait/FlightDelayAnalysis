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
shutdown_event = threading.Event()

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

def get_config_for_country(iso_code):
    return COUNTRY_CONFIG.get(str(iso_code).upper(), DEFAULT_CONFIG)

def fetch_feed_with_retry(url, retries=3, delay=2, code="UNK"):
    if shutdown_event.is_set():
        return None

    scraper = cloudscraper.create_scraper()

    for attempt in range(retries):
        if shutdown_event.is_set():
            return None

        try:
            response = scraper.get(url, timeout=20)
            
            if response.status_code == 200:
                feed = feedparser.parse(response.content)
                return feed
            elif response.status_code in [429, 503, 403]:
                wait_time = delay * (1.5 ** attempt) + random.uniform(1, 3)
                time.sleep(wait_time)
                continue
            else:
                 return None

        except Exception as e:
             error_str = str(e)
             if "NameResolutionError" in error_str or "nodename nor servname" in error_str:
                 if not shutdown_event.is_set():
                     with print_lock:
                         print(f"\n[CRITICAL] DNS/Network Error detected on {code}. Stopping scraper to prevent spam.")
                     shutdown_event.set()
                 return None

             if attempt < retries - 1:
                 time.sleep(delay * (1.5 ** attempt))
             else:
                 with print_lock:
                     print(f"   [{code}] Failed: {e}")
    
    return None

def process_airport(row, keywords_dict, current_idx, total_count):
    if shutdown_event.is_set():
        return []

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
        print(f"[{current_idx}/{total_count}] Processing {code} ({city_name})...")

    all_phrases = []
    for category, phrases in keywords_map.items():
        for phrase in phrases:
            all_phrases.append((category, phrase))
            
    with tqdm(total=len(all_phrases), desc=f"[{code}]", leave=False, disable=True) as pbar:
        for category, phrase in all_phrases:
            if shutdown_event.is_set():
                break

            query = f"{city_name} {phrase} after:2015-01-01"
            encoded_query = urllib.parse.quote(query)
            
            rss_url = f"https://news.google.com/rss/search?q={encoded_query}&hl={hl}&gl={gl}&ceid={ceid}"
            
            try:
                feed = fetch_feed_with_retry(rss_url, code=code)
                
                if not feed or not feed.entries:
                    time.sleep(random.uniform(0.5, 1.0))
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
            
            time.sleep(random.uniform(1.0, 2.0))

    if not shutdown_event.is_set():
        with print_lock:
             print(f"   [{code}] DONE. Saved {len(airport_news)} articles.")
         
    return airport_news

def main():
    df_airports, keywords_dict = load_data()
    if df_airports is None:
        return

    all_news = []
    total_airports = len(df_airports)
    
    MAX_WORKERS = 5
    
    print(f"Starting Google News scraping for {total_airports} airports ({MAX_WORKERS} workers)...")
    start_time = time.time()
    
    with concurrent.futures.ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        future_to_airport = {}
        
        for i, (index, row) in enumerate(df_airports.iterrows(), 1):
            if shutdown_event.is_set():
                break
            future = executor.submit(process_airport, row, keywords_dict, i, total_airports)
            future_to_airport[future] = row['ident']
        
        for future in concurrent.futures.as_completed(future_to_airport):
            try:
                data = future.result()
                if data:
                    all_news.extend(data)
            except Exception as exc:
                pass

    if shutdown_event.is_set():
        print("\n!!! SCRAPING STOPPED EARLY DUE TO NETWORK ERRORS !!!")
        print("Saving partial results so you can resume later...")

    df_news = pd.DataFrame(all_news)
    
    os.makedirs(os.path.dirname(OUTPUT_PATH), exist_ok=True)
    df_news.to_csv(OUTPUT_PATH, index=False)
    
    end_time = time.time()
    duration = end_time - start_time
    
    print(f"\nDone in {duration:.2f} seconds.")
    print(f"Collected {len(df_news)} unique articles.")
    print(f"File saved to: {OUTPUT_PATH}")

if __name__ == "__main__":
    main()