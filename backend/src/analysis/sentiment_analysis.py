import pandas as pd
import os
import json
import torch
from transformers import AutoTokenizer, AutoModelForSequenceClassification
import numpy as np
from datetime import datetime
import re
from tqdm import tqdm

CURRENT_FILE = os.path.abspath(__file__)
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(CURRENT_FILE)))
DATA_DIR = os.path.join(BASE_DIR, 'data')
CONFIG_PATH = os.path.join(BASE_DIR, 'config', 'keywords.json')
INPUT_FILE = os.path.join(DATA_DIR, 'sentiment', 'combined_data.csv')
AIRPORTS_PATH = os.path.join(DATA_DIR, 'processed', 'airports', 'airports_filtered.csv')
FLIGHTS_DATA_PATH = os.path.join(DATA_DIR, 'processed', 'delays', 'delays_consolidated_filtered.csv')

MODEL_A_NAME = "nlptown/bert-base-multilingual-uncased-sentiment"
MODEL_B_NAME = "cardiffnlp/twitter-xlm-roberta-base-sentiment"

print(f"Loading Model A: {MODEL_A_NAME}")
tokenizer_a = AutoTokenizer.from_pretrained(MODEL_A_NAME)
model_a = AutoModelForSequenceClassification.from_pretrained(MODEL_A_NAME)

print(f"Loading Model B: {MODEL_B_NAME}")
tokenizer_b = AutoTokenizer.from_pretrained(MODEL_B_NAME)
model_b = AutoModelForSequenceClassification.from_pretrained(MODEL_B_NAME)

def get_icao_to_iata_mapping(csv_path):
    if not os.path.exists(csv_path):
        return {}
    df = pd.read_csv(csv_path)
    mapping = dict(zip(df['icao_code'], df['iata_code']))
    return mapping

def get_dynamic_strategic_hubs(flights_path, airports_path, top_n=30):
    print(f"Calculating Strategic Hubs dynamically from: {flights_path}")
    
    if not os.path.exists(flights_path):
        print("[WARNING] Flights data not found. Falling back to empty hub list.")
        return []

    try:
        cols_to_use = ['SchedDepApt', 'SchedArrApt']
        df_flights = pd.read_csv(flights_path, usecols=cols_to_use)
        
        dep_counts = df_flights['SchedDepApt'].value_counts()
        arr_counts = df_flights['SchedArrApt'].value_counts()
        
        total_movements = dep_counts.add(arr_counts, fill_value=0)
        
        top_iata_list = total_movements.sort_values(ascending=False).head(top_n).index.tolist()
        
        top_iata_list = [str(x).strip().upper() for x in top_iata_list if pd.notna(x)]
        
        print(f"Identified {len(top_iata_list)} Strategic Hubs (Based on Total Movements).")
        print(f"Top 5 Hubs: {top_iata_list[:5]}")
        
        return top_iata_list

    except Exception as e:
        print(f"[ERROR] Error calculating dynamic hubs: {e}")
        return []

def calculate_bert_sentiment_a(text):
    """Calculates sentiment using the existing NLPTown model (1-5 stars)."""
    if not text or pd.isna(text):
        return 3.0
    
    inputs = tokenizer_a(str(text), return_tensors="pt", truncation=True, padding=True, max_length=512)
    with torch.no_grad():
        outputs = model_a(**inputs)
    
    probs = torch.nn.functional.softmax(outputs.logits, dim=-1)
    probs_np = probs.cpu().numpy()[0]
    stars = sum((i + 1) * p for i, p in enumerate(probs_np))
    return stars

def calculate_roberta_sentiment_b(text):
    """Calculates sentiment using the Twitter XLM-RoBERTa model and maps to 1-5 stars."""
    if not text or pd.isna(text):
        return 3.0
    
    inputs = tokenizer_b(str(text), return_tensors="pt", truncation=True, padding=True, max_length=512)
    with torch.no_grad():
        outputs = model_b(**inputs)
    
    probs = torch.nn.functional.softmax(outputs.logits, dim=-1)
    probs_np = probs.cpu().numpy()[0]
    
    stars_equivalent = (probs_np[0] * 1.0) + (probs_np[1] * 3.0) + (probs_np[2] * 5.0)
    return stars_equivalent

def calculate_ensemble_sentiment(text):
    """Averages the scores from both models."""
    
    score_a = calculate_bert_sentiment_a(text)
    score_b = calculate_roberta_sentiment_b(text)
    
    final_score = (score_a + score_b) / 2
    
    if final_score <= 2.5: 
        polarity = -1
    elif final_score >= 3.5: 
        polarity = 1
    else: 
        polarity = 0
        
    return polarity, final_score

def calculate_sigmoid_weight(row_date, airport_code, strategic_hubs):
    """
    Calculates a time-based weight using a Sigmoid (Logistic) Decay function.
    
    Formula: Weight = 1 / (1 + e^(slope * (delta_days - inflection_point)))
    
    This keeps the weight near 1.0 for recent events (Plateau) and then drops it sharply 
    after the inflection point.
    """
    current_date = datetime.now()
    
    try:
        dt = pd.to_datetime(row_date)
        if pd.isna(dt): return 0.5
    except:
        return 0.5

    if airport_code in strategic_hubs:
        inflection_point = 365 * 1.5
        slope = 0.005 
    else:
        inflection_point = 365 * 3.0
        slope = 0.003

    delta_days = (current_date - dt).days
    if delta_days < 0: delta_days = 0
    
    weight = 1 / (1 + np.exp(slope * (delta_days - inflection_point)))
    
    return weight

def process_dataset(df, mode, strategic_hubs, keywords=None):
    print(f"\n--- Processing Mode: {mode.upper()} ---")
    
    df_subset = df.copy()
    
    if keywords:
        pattern = '|'.join(map(re.escape, keywords))
        df_subset = df_subset[df_subset['text'].str.contains(pattern, case=False, na=False)]
        print(f"Filtered rows (Keyword match): {len(df_subset)}")
    else:
        print(f"Using full dataset: {len(df_subset)}")

    if df_subset.empty:
        print("No data for this category.")
        return

    results = []
    print("Calculating Ensemble Sentiment & Adaptive Weights...")
    
    for idx, row in tqdm(df_subset.iterrows(), total=len(df_subset)):
        pol, stars = calculate_ensemble_sentiment(row['text'])
        
        ap_code = row.get('airport_code', 'UNKNOWN')
        weight = calculate_sigmoid_weight(row['date'], ap_code, strategic_hubs)
        
        results.append({
            'sentiment_polarity': pol,
            'stars_score': stars,
            'time_weight': weight,
            'weighted_score': stars * weight
        })

    result_df = pd.DataFrame(results)
    final_df = pd.concat([df_subset.reset_index(drop=True), result_df], axis=1)
    
    output_filename = f"sentiment_results_{mode}.csv"
    output_path = os.path.join(DATA_DIR, 'sentiment', output_filename)
    final_df.to_csv(output_path, index=False)
    print(f"Saved: {output_path}")

def main():
    if not os.path.exists(INPUT_FILE):
        print("Input file not found.")
        return

    print("Loading Data...")
    df = pd.read_csv(INPUT_FILE)
    
    mapping = get_icao_to_iata_mapping(AIRPORTS_PATH)
    if mapping:
        df['airport_code'] = df['airport_code'].map(mapping).fillna(df['airport_code'])
    
    strategic_hubs_list = get_dynamic_strategic_hubs(FLIGHTS_DATA_PATH, AIRPORTS_PATH, top_n=30)

    with open(CONFIG_PATH, 'r') as f:
        kw_config = json.load(f)
        
    delays_kw = []
    noise_kw = []
    for lang in kw_config:
        if 'delays' in kw_config[lang]: delays_kw.extend(kw_config[lang]['delays'])
        if 'noise' in kw_config[lang]: noise_kw.extend(kw_config[lang]['noise'])
    
    delays_kw = list(set(delays_kw))
    noise_kw = list(set(noise_kw))

    process_dataset(df, "general", strategic_hubs_list, keywords=None)
    
    process_dataset(df, "delay", strategic_hubs_list, keywords=delays_kw)
    
    process_dataset(df, "noise", strategic_hubs_list, keywords=noise_kw)

if __name__ == "__main__":
    main()