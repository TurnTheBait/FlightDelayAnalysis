import pandas as pd
import os

current_script_dir = os.path.dirname(os.path.abspath(__file__))
src_dir = os.path.dirname(current_script_dir)
backend_dir = os.path.dirname(src_dir)

NEWS_PATH = os.path.join(backend_dir, 'data', 'sentiment', 'news_cleaned.csv')
REDDIT_PATH = os.path.join(backend_dir, 'data', 'sentiment', 'reddit_raw.csv')
OUTPUT_PATH = os.path.join(backend_dir, 'data', 'sentiment', 'combined_data.csv')

dfs = []

if os.path.exists(NEWS_PATH):
    print(f"Loading News data from {NEWS_PATH}...")
    try:
        df_news = pd.read_csv(NEWS_PATH)
        if not df_news.empty:
            df_news_clean = pd.DataFrame({
                'airport_code': df_news['airport_code'],
                'city': df_news['search_term'], 
                'source': 'Google News',
                'text': df_news['title'], 
                'date': df_news['published']
            })
            dfs.append(df_news_clean)
    except Exception as e:
        print(f"Error reading news file: {e}")

if os.path.exists(REDDIT_PATH):
    print(f"Loading Reddit data from {REDDIT_PATH}...")
    try:
        df_reddit = pd.read_csv(REDDIT_PATH)
        if not df_reddit.empty:
            df_reddit['full_text'] = df_reddit['title'].astype(str) + " " + df_reddit['text'].astype(str)
            
            df_reddit_clean = pd.DataFrame({
                'airport_code': df_reddit['airport_code'],
                'city': df_reddit['search_term'],
                'source': 'Reddit',
                'text': df_reddit['full_text'],
                'date': df_reddit['created_utc'] 
            })
            dfs.append(df_reddit_clean)
    except Exception as e:
        print(f"Error reading reddit file: {e}")

if not dfs:
    print("No data found to merge.")
    exit()

df_combined = pd.concat(dfs, ignore_index=True)

df_combined.dropna(subset=['text'], inplace=True)

os.makedirs(os.path.dirname(OUTPUT_PATH), exist_ok=True)
df_combined.to_csv(OUTPUT_PATH, index=False)

print(f"\nSuccess! Combined dataset saved to: {OUTPUT_PATH}")
print(f"Total records: {len(df_combined)}")
print(df_combined['source'].value_counts())