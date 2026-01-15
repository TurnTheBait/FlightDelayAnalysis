import pandas as pd
import os
import torch
from transformers import AutoTokenizer, AutoModelForSequenceClassification
import numpy as np

current_script_dir = os.path.dirname(os.path.abspath(__file__))
backend_dir = os.path.dirname(os.path.dirname(current_script_dir))

INPUT_FILE = os.path.join(backend_dir, 'data', 'sentiment', 'combined_data.csv')
OUTPUT_FILE = os.path.join(backend_dir, 'data', 'sentiment', 'sentiment_scored.csv')

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
    score_idx = torch.argmax(probs).item()
    
    stars = score_idx + 1 
    
    if stars <= 2: polarity = -1
    elif stars == 3: polarity = 0
    else: polarity = 1
    
    return polarity, stars

if not os.path.exists(INPUT_FILE):
    print(f"Error: File not found {INPUT_FILE}")
    exit()

print(f"Reading data from: {INPUT_FILE}")
df = pd.read_csv(INPUT_FILE)

print("Starting sentiment analysis...")
results = df['text'].apply(lambda x: calculate_sentiment(x))

df['sentiment_polarity'] = [res[0] for res in results]
df['stars_score'] = [res[1] for res in results]

os.makedirs(os.path.dirname(OUTPUT_FILE), exist_ok=True)
df.to_csv(OUTPUT_FILE, index=False)

print(f"Analysis complete. File saved to: {OUTPUT_FILE}")
print(df[['city', 'text', 'stars_score']].head())