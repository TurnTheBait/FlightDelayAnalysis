import feedparser
import pandas as pd
import urllib.parse
import time
import os
import random
import json

current_script_dir = os.path.dirname(os.path.abspath(__file__))
src_dir = os.path.dirname(current_script_dir)
backend_dir = os.path.dirname(src_dir)

AIRPORTS_CSV_PATH = os.path.join(backend_dir, 'data', 'processed', 'airports', 'airports_filtered.csv')
KEYWORDS_JSON_PATH = os.path.join(backend_dir, 'config', 'keywords.json')
OUTPUT_PATH = os.path.join(backend_dir, 'data', 'sentiment', 'news_raw_full.csv')

COUNTRY_MAP = {
    'IT': 'IT',
    'DE': 'DE', 'AT': 'DE', 'CH': 'DE',
    'FR': 'FR', 'BE': 'FR',
    'ES': 'ES',
    'GB': 'EN', 'IE': 'EN', 'US': 'EN'
}

if not os.path.exists(AIRPORTS_CSV_PATH):
    print(f"Error: Airports file not found at {AIRPORTS_CSV_PATH}")
    exit()

if not os.path.exists(KEYWORDS_JSON_PATH):
    print(f"Error: Keywords config file not found at {KEYWORDS_JSON_PATH}")
    exit()

print(f"Reading keywords from: {KEYWORDS_JSON_PATH}")
try:
    with open(KEYWORDS_JSON_PATH, 'r', encoding='utf-8') as f:
        KEYWORDS_DICT = json.load(f)
except Exception as e:
    print(f"Error reading JSON: {e}")
    exit()

print(f"Reading airports from: {AIRPORTS_CSV_PATH}")
try:
    df_airports = pd.read_csv(AIRPORTS_CSV_PATH)
except Exception as e:
    print(f"Error reading CSV: {e}")
    exit()

def get_keywords_for_country(iso_code):
    lang_key = COUNTRY_MAP.get(str(iso_code).upper(), 'EN')
    return KEYWORDS_DICT.get(lang_key, KEYWORDS_DICT['EN'])

all_news = []
seen_links = set()

print(f"Starting Google News scraping for {len(df_airports)} airports...")

for index, row in df_airports.iterrows():
    full_name = str(row['name'])
    code = row['ident']
    iso_country = str(row['iso_country'])
    
    city_name = full_name.replace("International", "").replace("Airport", "").replace("Intl", "").split('/')[0].split('(')[0].strip()
    
    keywords_map = get_keywords_for_country(iso_country)
    
    print(f"[{index+1}/{len(df_airports)}] Processing {code} ({city_name}) - Country: {iso_country}...")
    
    airport_news_count = 0
    
    for category, phrases in keywords_map.items():
        for phrase in phrases:
            query = f"{city_name} {phrase}"
            encoded_query = urllib.parse.quote(query)
            
            rss_url = f"https://news.google.com/rss/search?q={encoded_query}&hl=en-US&gl=US&ceid=US:en"
            
            try:
                feed = feedparser.parse(rss_url)
                
                if not feed.entries:
                    continue
                    
                for entry in feed.entries:
                    if entry.link in seen_links:
                        continue
                    
                    published_parsed = entry.get("published_parsed")
                    if published_parsed:
                        date_str = time.strftime("%Y-%m-%d %H:%M:%S", published_parsed)
                    else:
                        date_str = ""

                    all_news.append({
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
                    airport_news_count += 1
                    
            except Exception as e:
                print(f"   Error fetching {query}: {e}")
                
            time.sleep(random.uniform(0.3, 0.7))
    
    print(f"   Saved {airport_news_count} unique articles for {code}")

df_news = pd.DataFrame(all_news)

os.makedirs(os.path.dirname(OUTPUT_PATH), exist_ok=True)
df_news.to_csv(OUTPUT_PATH, index=False)

print(f"Done. Collected {len(df_news)} unique articles.")
print(f"File saved to: {OUTPUT_PATH}")