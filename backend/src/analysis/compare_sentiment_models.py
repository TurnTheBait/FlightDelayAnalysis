import pandas as pd
import os
import torch
from transformers import AutoTokenizer, AutoModelForSequenceClassification
import numpy as np
from tqdm import tqdm

MODEL_A_NAME = "nlptown/bert-base-multilingual-uncased-sentiment"
MODEL_B_NAME = "cardiffnlp/twitter-xlm-roberta-base-sentiment"

CURRENT_FILE = os.path.abspath(__file__)
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(CURRENT_FILE)))
DATA_DIR = os.path.join(BASE_DIR, 'data')
INPUT_FILE = os.path.join(DATA_DIR, 'sentiment', 'combined_data.csv')
OUTPUT_DIR = os.path.join(BASE_DIR, 'results', 'tables')
OUTPUT_FILE = os.path.join(OUTPUT_DIR, 'sentiment_model_comparison.csv')

def load_model(model_name):
    print(f"Loading Model: {model_name}")
    tokenizer = AutoTokenizer.from_pretrained(model_name)
    model = AutoModelForSequenceClassification.from_pretrained(model_name)
    return tokenizer, model

def predict_nlptown(text, tokenizer, model):
    if not text or pd.isna(text):
        return 0, 3
    
    inputs = tokenizer(str(text), return_tensors="pt", truncation=True, padding=True, max_length=512)
    with torch.no_grad():
        outputs = model(**inputs)
    
    probs = torch.nn.functional.softmax(outputs.logits, dim=-1)
    probs_np = probs.cpu().numpy()[0]
    stars = sum((i + 1) * p for i, p in enumerate(probs_np))
    return stars

def predict_cardiff(text, tokenizer, model):
    if not text or pd.isna(text):
        return "Neutral", 0.0
    
    labels = ["Negative", "Neutral", "Positive"]
    
    inputs = tokenizer(str(text), return_tensors="pt", truncation=True, padding=True, max_length=512)
    with torch.no_grad():
        outputs = model(**inputs)
    
    probs = torch.nn.functional.softmax(outputs.logits, dim=-1)
    probs_np = probs.cpu().numpy()[0]
    
    max_idx = np.argmax(probs_np)
    label = labels[max_idx]
    score = probs_np[max_idx]
    
    return label, score, probs_np

def map_cardiff_to_stars(probs):
    stars_equivalent = (probs[0] * 1.0) + (probs[1] * 3.0) + (probs[2] * 5.0)
    return stars_equivalent

def main():
    if not os.path.exists(INPUT_FILE):
        print(f"Input file not found: {INPUT_FILE}")
        return

    print(f"Loading data from {INPUT_FILE}...")
    df = pd.read_csv(INPUT_FILE)
    
    df = df.sample(min(len(df), 100), random_state=42)
    print(f"Processing {len(df)} rows (Sample).")

    tokenizer_a, model_a = load_model(MODEL_A_NAME)
    tokenizer_b, model_b = load_model(MODEL_B_NAME)

    results = []
    
    print("Running comparisons...")
    for idx, row in tqdm(df.iterrows(), total=len(df)):
        text = row['text']
        
        stars_a = predict_nlptown(text, tokenizer_a, model_a)
        
        label_b, score_b, probs_b = predict_cardiff(text, tokenizer_b, model_b)
        stars_b_mapped = map_cardiff_to_stars(probs_b)
        
        results.append({
            'text': text,
            'source': row.get('source', ''),
            'model_a_stars': round(stars_a, 2),
            'model_b_label': label_b,
            'model_b_stars_mapped': round(stars_b_mapped, 2),
            'diff': round(stars_b_mapped - stars_a, 2)
        })

    os.makedirs(OUTPUT_DIR, exist_ok=True)
    results_df = pd.DataFrame(results)
    results_df.to_csv(OUTPUT_FILE, index=False)
    
    print(f"\nComparison saved to: {OUTPUT_FILE}")
    print("\n--- Sample Comparison (Top 10 Largest Differences) ---")
    
    results_df['abs_diff'] = results_df['diff'].abs()
    top_diffs = results_df.sort_values(by='abs_diff', ascending=False).head(10)
    
    pd.set_option('display.max_colwidth', 100)
    print(top_diffs[['text', 'model_a_stars', 'model_b_label', 'model_b_stars_mapped']])

if __name__ == "__main__":
    main()
