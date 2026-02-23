import os
import sys
import pandas as pd
import numpy as np
from tqdm import tqdm

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from sentiment_analysis import calculate_time_based_weight, get_dynamic_strategic_hubs, FLIGHTS_DATA_PATH, AIRPORTS_PATH, DATA_DIR

def main():
    print("Fetching strategic hubs...")
    strategic_hubs = set(get_dynamic_strategic_hubs(FLIGHTS_DATA_PATH, AIRPORTS_PATH, top_n=30))
    
    modes = ['general', 'delay', 'noise']
    for mode in modes:
        input_file = os.path.join(DATA_DIR, 'sentiment', f'sentiment_results_raw_{mode}.csv')
        output_file = os.path.join(DATA_DIR, 'sentiment', f'sentiment_results_{mode}.csv')
        
        if not os.path.exists(input_file):
            print(f"Skipping {input_file}, does not exist.")
            continue
            
        print(f"\nProcessing weights and impacts for {input_file}...")
        df = pd.read_csv(input_file)
        
        print("Calculating Media Pressure Index...")
        review_counts_dict = df['airport_code'].value_counts().to_dict()
        
        weights = []
        weighted_scores = []
        media_pressure_indices = []
        pressure_impact_scores = []
        combined_scores_boosted = []
        
        print("Calculating Impact & Weights per row...")
        for _, row in tqdm(df.iterrows(), total=len(df)):
            ap_code = row.get('airport_code', 'UNKNOWN')
            weight = calculate_time_based_weight(row.get('date'), ap_code, strategic_hubs)
            
            review_count = review_counts_dict.get(ap_code, 1)
            media_pressure_index = np.log1p(review_count)
            
            raw_score = row.get('combined_score', 5.5)
            score_10 = np.clip(raw_score * 1.5 + 1.0, 1.0, 10.0)
            
            sentiment_centered = score_10 - 5.5
            raw_impact = sentiment_centered * weight * media_pressure_index
            sigmoid_val = 1 / (1 + np.exp(-0.05 * raw_impact))
            pressure_impact_score = 1 + 9 * sigmoid_val
            
            combined_scores_boosted.append(score_10)
            weights.append(weight)
            weighted_scores.append(score_10 * weight)
            media_pressure_indices.append(media_pressure_index)
            pressure_impact_scores.append(pressure_impact_score)
            
        df['combined_score'] = combined_scores_boosted
        df['weight'] = weights
        df['weighted_score'] = weighted_scores
        df['media_pressure_index'] = media_pressure_indices
        df['pressure_impact_score'] = pressure_impact_scores
        
        df.to_csv(output_file, index=False)
        print(f"Saved completed data to: {output_file}")

if __name__ == '__main__':
    main()
