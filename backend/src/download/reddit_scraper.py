import pandas as pd
import time
import json
import os
import random
import requests
from datetime import datetime

current_script_dir = os.path.dirname(os.path.abspath(__file__))
src_dir = os.path.dirname(current_script_dir)
backend_dir = os.path.dirname(src_dir)

AIRPORTS_CSV_PATH = os.path.join(backend_dir, 'data', 'processed', 'airports', 'airports_filtered.csv')
OUTPUT_PATH = os.path.join(backend_dir, 'data', 'raw', 'reddit', 'reddit_raw.csv')
KEYWORDS_PATH = os.path.join(backend_dir, 'config', 'keywords.json')

USER_AGENTS = [
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.1.1 Safari/605.1.15',
    'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/92.0.4515.107 Safari/537.36',
    'Mozilla/5.0 (iPhone; CPU iPhone OS 14_6 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.0 Mobile/15E148 Safari/604.1',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:90.0) Gecko/20100101 Firefox/90.0'
]

must_have_keywords = []

if os.path.exists(KEYWORDS_PATH):
    try:
        with open(KEYWORDS_PATH, 'r', encoding='utf-8') as f:
            keywords_data = json.load(f)
            for lang in keywords_data:
                if 'delays' in keywords_data[lang]:
                    must_have_keywords.extend(keywords_data[lang]['delays'])
            must_have_keywords = list(set(must_have_keywords))
            print(f"Loaded {len(must_have_keywords)} keywords from {KEYWORDS_PATH}")
    except Exception as e:
        print(f"Error loading keywords from config: {e}. Using default list.")

if not must_have_keywords:
    must_have_keywords = ['delay', 'cancelled', 'stuck', 'chaos', 'wait', 'queue', 'missed connection', 'luggage', 'baggage', 'airline', 'airport', 'flight', 'stranded']
spam_keywords = [
    'pre-order', 'fiction', 'chapter', 'author', 'book', 'novel', 'coin', 'numismatic', 'microbiome', 'diabetes', 
    'university', 'tcg', 'card game', 'movie', 'film', 'oscar', 
    'hiring', 'job', 'salary', 'recruit', 'freelance', 'part-time', 'full-time', 'vacancy', 'distributor', 'earn'
]

seen_urls = set()

if not os.path.exists(AIRPORTS_CSV_PATH):
    print(f"Error: Airports file not found at {AIRPORTS_CSV_PATH}")
    exit()

print(f"Reading airports from: {AIRPORTS_CSV_PATH}")
try:
    df_airports = pd.read_csv(AIRPORTS_CSV_PATH)
    required_cols = ['ident', 'name', 'iso_country']
    if not all(col in df_airports.columns for col in required_cols):
        print(f"Error: CSV missing columns.")
        exit()
except Exception as e:
    print(f"Error reading CSV: {e}")
    exit()

def fetch_reddit_url(url, retries=3):
    for attempt in range(retries):
        headers = {'User-Agent': random.choice(USER_AGENTS)}
        try:
            response = requests.get(url, headers=headers, timeout=10)
            
            if response.status_code == 200:
                return response.json()
            elif response.status_code == 429:
                wait_time = random.uniform(30, 60)
                print(f"   Rate limit hit (429). Sleeping {wait_time:.1f}s...")
                time.sleep(wait_time)
                continue
            elif response.status_code in [403, 503]:
                time.sleep(random.uniform(5, 10))
                continue
            else:
                return None
        except Exception:
            time.sleep(2)
    return None

results_list = []
print(f"\nStarting ENHANCED Reddit scraping for {len(df_airports)} airports...")

for index, row in df_airports.iterrows():
    full_name = str(row['name'])
    code = row['ident']
    
    city_name = full_name.replace("International", "").replace("Airport", "").replace("Intl", "").split('/')[0].split('(')[0].strip()
    
    queries = [
        f"{city_name} airport delay",
        f"{city_name} flight cancelled"
    ]
    
    for query in queries:
        print(f"[{index+1}/{len(df_airports)}] {code} - Searching: '{query}'")
        
        url = f"https://www.reddit.com/search.json?q={query}&sort=relevance&t=all&limit=25" 
        data = fetch_reddit_url(url)
        
        if data and 'data' in data and 'children' in data['data']:
            posts = data['data']['children']
            found_count = 0
            
            for post in posts:
                post_data = post['data']
                title = post_data.get('title', '')
                text = post_data.get('selftext', '')
                post_url = post_data.get('permalink')
                
                full_text = (str(title) + " " + str(text)).lower()
                
                if post_url in seen_urls:
                    continue
                    
                if any(spam in full_text for spam in spam_keywords):
                    continue
                    
                if city_name.lower() not in full_text:
                    continue
                    
                if not any(k in full_text for k in must_have_keywords):
                    continue

                seen_urls.add(post_url)
                
                created_utc = post_data.get('created_utc')
                date_str = datetime.utcfromtimestamp(created_utc).strftime('%Y-%m-%d %H:%M:%S')
                
                if date_str < '2015-01-01':
                    continue

                results_list.append({
                    "airport_code": code,
                    "search_term": city_name,
                    "source": "Reddit",
                    "title": title,
                    "text": text[:1000],
                    "author": post_data.get('author'),
                    "url": f"https://reddit.com{post_url}",
                    "created_utc": date_str
                })
                found_count += 1
            
            if found_count > 0:
                print(f"   Saved {found_count} new posts.")
        
        time.sleep(random.uniform(2.0, 4.0))

    if (index + 1) % 5 == 0:
        df_temp = pd.DataFrame(results_list)
        os.makedirs(os.path.dirname(OUTPUT_PATH), exist_ok=True)
        df_temp.to_csv(OUTPUT_PATH, index=False)

df_results = pd.DataFrame(results_list)
os.makedirs(os.path.dirname(OUTPUT_PATH), exist_ok=True)
df_results.to_csv(OUTPUT_PATH, index=False)

print(f"\nDone. Collected {len(df_results)} HIGH QUALITY Reddit posts.")
print(f"File saved to: {OUTPUT_PATH}")