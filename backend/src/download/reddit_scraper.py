import pandas as pd
import time
import os
import random
import requests

current_script_dir = os.path.dirname(os.path.abspath(__file__))
src_dir = os.path.dirname(current_script_dir)
backend_dir = os.path.dirname(src_dir)

AIRPORTS_CSV_PATH = os.path.join(backend_dir, 'data', 'processed', 'airports', 'airports_filtered.csv')
OUTPUT_PATH = os.path.join(backend_dir, 'data', 'sentiment', 'reddit_raw.csv')

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

results_list = []
print(f"\nStarting ENHANCED Reddit scraping for {len(df_airports)} airports...")

headers = {
    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.114 Safari/537.36'
}

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
        
        try:
            url = f"https://www.reddit.com/search.json?q={query}&sort=relevance&t=year&limit=10" 
            response = requests.get(url, headers=headers, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                posts = data.get('data', {}).get('children', [])
                
                found_count = 0
                if posts:
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
                        results_list.append({
                            "airport_code": code,
                            "search_term": city_name,
                            "source": "Reddit",
                            "title": title,
                            "text": text[:500],
                            "author": post_data.get('author'),
                            "url": f"https://reddit.com{post_url}",
                            "created_utc": post_data.get('created_utc')
                        })
                        found_count += 1
                
                if found_count > 0:
                    print(f"   Saved {found_count} new posts.")
                
            elif response.status_code == 429:
                print("   Rate limit hit. Sleeping 5s...")
                time.sleep(5)
                
        except Exception as e:
            print(f"   Error scraping {code}: {e}")
        
        time.sleep(random.uniform(1.0, 2.0))

df_results = pd.DataFrame(results_list)

os.makedirs(os.path.dirname(OUTPUT_PATH), exist_ok=True)
df_results.to_csv(OUTPUT_PATH, index=False)

print(f"\nDone. Collected {len(df_results)} HIGH QUALITY Reddit posts.")
print(f"File saved to: {OUTPUT_PATH}")