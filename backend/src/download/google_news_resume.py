import feedparser
import pandas as pd
import urllib.parse
import time
import os
import random
import json
import socket
import threading
from datetime import datetime
import cloudscraper

socket.setdefaulttimeout(60)

current_script_dir = os.path.dirname(os.path.abspath(__file__))
src_dir = os.path.dirname(current_script_dir)
backend_dir = os.path.dirname(src_dir)

AIRPORTS_CSV_PATH = os.path.join(backend_dir, 'data', 'processed', 'airports', 'airports_filtered.csv')
KEYWORDS_JSON_PATH = os.path.join(backend_dir, 'config', 'keywords.json')
OUTPUT_PATH = os.path.join(backend_dir, 'data', 'raw', 'news', 'news_raw_full.csv')

file_lock = threading.Lock()

LANG_CONFIGS = {
    'EN': {'hl': 'en-US', 'gl': 'US', 'ceid': 'US:en'},
    'IT': {'hl': 'it-IT', 'gl': 'IT', 'ceid': 'IT:it'},
    'DE': {'hl': 'de-DE', 'gl': 'DE', 'ceid': 'DE:de'},
    'FR': {'hl': 'fr-FR', 'gl': 'FR', 'ceid': 'FR:fr'},
    'ES': {'hl': 'es-419', 'gl': 'ES', 'ceid': 'ES:es'},
}

COUNTRY_LANGUAGES = {
    'IT': ['IT', 'EN'],
    'DE': ['DE', 'EN'],
    'AT': ['DE', 'EN'],
    'CH': ['DE', 'FR', 'IT', 'EN'],
    'FR': ['FR', 'EN'],
    'BE': ['FR', 'DE', 'EN'],
    'LU': ['FR', 'DE', 'EN'],
    'ES': ['ES', 'EN'],
    'GB': ['EN'],
    'IE': ['EN'],
    'GI': ['EN', 'ES'],
}

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

def get_languages_for_country(iso_code):
    return COUNTRY_LANGUAGES.get(str(iso_code).upper(), ['EN'])

def save_airport_data(airport_news):
    with file_lock:
        df_chunk = pd.DataFrame(airport_news)
        file_exists = os.path.isfile(OUTPUT_PATH) and os.path.getsize(OUTPUT_PATH) > 0
        df_chunk.to_csv(OUTPUT_PATH, mode='a', header=not file_exists, index=False)

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
                print(f"   [{code}] Hit {response.status_code}, cooling down {wait_time:.1f}s")
                time.sleep(wait_time)
                continue
            else:
                 return None

        except Exception as e:
             error_str = str(e)
             if "NameResolutionError" in error_str or "nodename nor servname" in error_str:
                 wait_time = 60 * (attempt + 1)
                 print(f"   [{code}] DNS error, waiting {wait_time}s before retry...")
                 time.sleep(wait_time)
                 continue

             if attempt < retries - 1:
                 wait_time = delay * (2 ** attempt)
                 time.sleep(wait_time)
             else:
                 print(f"   [{code}] Failed: {e}")
    
    return None

def process_airport(row, keywords_dict, current_idx, total_count):
    full_name = str(row['name'])
    code = row['ident']
    iso_country = str(row['iso_country'])
    
    city_name = full_name.replace("International", "").replace("Airport", "").replace("Intl", "").split('/')[0].split('(')[0].strip()
    
    languages = get_languages_for_country(iso_country)
    
    airport_news = []
    seen_links = set()
    
    print(f"[{current_idx}/{total_count}] Resuming {code} ({city_name}) - langs: {languages}...")

    for lang_key in languages:
        lang_cfg = LANG_CONFIGS.get(lang_key, LANG_CONFIGS['EN'])
        hl = lang_cfg['hl']
        gl = lang_cfg['gl']
        ceid = lang_cfg['ceid']

        keywords_map = keywords_dict.get(lang_key, keywords_dict['EN'])

        all_phrases = []
        for category, phrases in keywords_map.items():
            for phrase in phrases:
                all_phrases.append((category, phrase))
                
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
                        "search_language": lang_key,
                        "title": entry.title,
                        "link": entry.link,
                        "published": entry.published if 'published' in entry else date_str,
                        "source": entry.source.title if 'source' in entry else "Google News"
                    })
                    
                    seen_links.add(entry.link)
                    
            except Exception as e:
                pass
            
            time.sleep(random.uniform(2.0, 4.0))

    if not airport_news:
        airport_news.append({
            "airport_code": code,
            "search_term": city_name,
            "full_name": full_name,
            "category": "NONE",
            "keyword_used": "NONE",
            "search_language": "NONE",
            "title": "NO_DATA",
            "link": "NO_DATA",
            "published": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "source": "NO_DATA"
        })

    save_airport_data(airport_news)
    print(f"   [{code}] DONE. Saved {len(airport_news)} articles.")
         
    return len(airport_news)

def main():
    df_airports, keywords_dict = load_data()
    if df_airports is None:
        return

    processed_codes = get_processed_airports()
    print(f"Found {len(processed_codes)} airports already processed in {OUTPUT_PATH}")
    
    df_missing = df_airports[~df_airports['ident'].isin(processed_codes)]
    
    if df_missing.empty:
        print("All airports have been processed. Nothing to resume.")
        return

    total_missing = len(df_missing)
    print(f"Resuming scraping for {total_missing} remaining airports (1 worker, slow mode)...")
    start_time = time.time()
    
    total_articles = 0
    completed = 0

    for i, (index, row) in enumerate(df_missing.iterrows(), 1):
        try:
            count = process_airport(row, keywords_dict, i, total_missing)
            total_articles += count
            completed += 1
        except Exception as exc:
            print(f"   [{row['ident']}] Error: {exc}")

    end_time = time.time()
    duration = end_time - start_time
    
    print(f"\nResume completed in {duration:.2f} seconds.")
    print(f"Processed {completed}/{total_missing} airports, {total_articles} articles.")
    print(f"File: {OUTPUT_PATH}")

if __name__ == "__main__":
    main()
