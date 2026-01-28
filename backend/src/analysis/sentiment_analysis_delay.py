import pandas as pd
import os
import json
import torch
from transformers import AutoTokenizer, AutoModelForSequenceClassification
import numpy as np

current_script_dir = os.path.dirname(os.path.abspath(__file__))
backend_dir = os.path.dirname(os.path.dirname(current_script_dir))
config_path = os.path.join(backend_dir, 'config', 'keywords.json')

INPUT_FILE = os.path.join(backend_dir, 'data', 'sentiment', 'combined_data.csv')
OUTPUT_FILE = os.path.join(backend_dir, 'data', 'sentiment', 'sentiment_scored_delay.csv')

src_dir = os.path.dirname(current_script_dir)
import sys 
sys.path.append(src_dir)
from utils.airport_utils import get_icao_to_iata_mapping
AIRPORTS_PATH = os.path.join(backend_dir, 'data', 'processed', 'airports', 'airports_filtered.csv')

model_name = "nlptown/bert-base-multilingual-uncased-sentiment"

print(f"Loading AI model ({model_name})...")
tokenizer = AutoTokenizer.from_pretrained(model_name)
model = AutoModelForSequenceClassification.from_pretrained(model_name)
print("Model loaded.")

def calculate_sentiment(text):
    if not text or pd.isna(text):
        return 0, 3
    
    inputs = tokenizer(str(text), return_tensors="pt", truncation=True, padding=True, max_length=512)
    with torch.no_grad():
        outputs = model(**inputs)
    
    probs = torch.nn.functional.softmax(outputs.logits, dim=-1)

    probs_np = probs.cpu().numpy()[0]
    
    stars = sum((i + 1) * p for i, p in enumerate(probs_np))
    
    if stars <= 2.4: polarity = -1
    elif stars <= 3.6: polarity = 0
    else: polarity = 1
    
    return polarity, stars

if not os.path.exists(INPUT_FILE):
    print(f"Error: File not found {INPUT_FILE}")
    exit()
    
if not os.path.exists(config_path):
    print(f"Error: Config file not found {config_path}")
    exit()

print(f"Loading keywords from: {config_path}")
with open(config_path, 'r', encoding='utf-8') as f:
    keywords_config = json.load(f)

delay_keywords = []
for lang in keywords_config:
    if 'delays' in keywords_config[lang]:
        delay_keywords.extend(keywords_config[lang]['delays'])

delay_keywords = list(set(delay_keywords))
print(f"Loaded {len(delay_keywords)} unique delay keywords across languages.")

print(f"Reading data from: {INPUT_FILE}")
df = pd.read_csv(INPUT_FILE)

pattern = '|'.join(map(lambda x: pd.isna(x) and '' or str(x), delay_keywords))
import re
pattern = '|'.join(map(re.escape, delay_keywords))

df = df[df['text'].str.contains(pattern, case=False, na=False)].copy()
print(f"Filtered for DELAY perception. Remaining rows: {len(df)}")


print("Starting sentiment analysis...")
from datetime import datetime
import pytz

CURRENT_DATE = datetime(2026, 1, 1, tzinfo=pytz.UTC)

def calculate_time_weight(date_str):
    try:
        dt = pd.to_datetime(date_str, utc=True)
        if pd.isna(dt):
            return 0.5
        
        age_days = (CURRENT_DATE - dt).days
        if age_days < 0: age_days = 0
        
        weight = 0.5 ** (age_days / 365.0)
        return weight
    except:
        return 0.5

results = df['text'].apply(lambda x: calculate_sentiment(x))
df['sentiment_polarity'] = [res[0] for res in results]
df['stars_score'] = [res[1] for res in results]

print("Calculating time weights...")
df['time_weight'] = df['date'].apply(calculate_time_weight)

if os.path.exists(AIRPORTS_PATH):
    print("Mapping ICAO to IATA...")
    icao_to_iata = get_icao_to_iata_mapping(AIRPORTS_PATH)
    df['airport_code'] = df['airport_code'].map(icao_to_iata).fillna(df['airport_code'])
else:
    print(f"Warning: Airports file not found at {AIRPORTS_PATH}, skipping mapping.")

os.makedirs(os.path.dirname(OUTPUT_FILE), exist_ok=True)
df.to_csv(OUTPUT_FILE, index=False)

print(f"Analysis complete. File saved to: {OUTPUT_FILE}")
if not df.empty:
    print(df[['city', 'text', 'stars_score']].head())
