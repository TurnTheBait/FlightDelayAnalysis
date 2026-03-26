import pandas as pd
import os
import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np
from scipy import stats

CURRENT_FILE = os.path.abspath(__file__)
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(CURRENT_FILE)))
DATA_RAW_DIR = os.path.join(BASE_DIR, 'data', 'raw', 'skytrax')
DATA_SENTIMENT_DIR = os.path.join(BASE_DIR, 'data', 'sentiment')
PLOTS_DIR = os.path.join(BASE_DIR, 'results', 'figures', 'calibration')

os.makedirs(PLOTS_DIR, exist_ok=True)

def plot_calibration():
    raw_path = os.path.join(DATA_RAW_DIR, 'skytrax_raw.csv')
    sentiment_path = os.path.join(DATA_SENTIMENT_DIR, 'sentiment_results_raw_general.csv')

    if not os.path.exists(raw_path) or not os.path.exists(sentiment_path):
        print(f"[ERROR] Missing files: {raw_path} or {sentiment_path}")
        return

    print("Loading data...")
    df_raw = pd.read_csv(raw_path)
    df_sent = pd.read_csv(sentiment_path)

    df_sent = df_sent[df_sent['source'] == 'Skytrax'].copy()

    import re
    def clean_text(text):
        if not isinstance(text, str): return ""
        text = text.replace("✅Trip Verified|", "").replace("✅Verified Review|", "").replace("Not Verified|", "").replace("Trip Verified |", "")
        text = re.sub(r'[^a-zA-Z0-9]', '', text).lower()
        return text

    print("Cleaning text for matching...")
    df_raw['text_clean'] = df_raw['text'].apply(clean_text)
    df_sent['text_clean'] = df_sent['text'].apply(clean_text)

    df_merged = pd.merge(df_sent, df_raw[['text_clean', 'rating']], on='text_clean', how='inner')
    
    if len(df_merged) < 10:
        print(f"Warning: Only {len(df_merged)} matches with strict alphanumeric cleaning. Trying 'last 100 chars' strategy...")
        def fingerprint(text):
            if not isinstance(text, str): return ""
            clean = re.sub(r'[^a-zA-Z0-9]', '', text).lower()
            return clean[-150:] if len(clean) > 150 else clean
            
        df_raw['fingerprint'] = df_raw['text'].apply(fingerprint)
        df_sent['fingerprint'] = df_sent['text'].apply(fingerprint)
        df_merged = pd.merge(df_sent, df_raw[['fingerprint', 'rating']], on='fingerprint', how='inner')

    df_merged['user_rating'] = pd.to_numeric(df_merged['rating'], errors='coerce')
    df_merged = df_merged.dropna(subset=['user_rating', 'combined_score'])

    if df_merged.empty:
        print("[ERROR] No overlapping data found after merging.")
        return

    print(f"Merged records: {len(df_merged)}")

    pearson_corr, _ = stats.pearsonr(df_merged['user_rating'], df_merged['combined_score'])
    mae = (df_merged['user_rating'] - df_merged['combined_score']).abs().mean()
    mean_diff = (df_merged['combined_score'] - df_merged['user_rating']).mean()

    print(f"Metrics:")
    print(f"- Pearson Correlation: {pearson_corr:.3f}")
    print(f"- Mean Absolute Error (MAE): {mae:.3f}")
    print(f"- Mean Bias Error (MBE): {mean_diff:.3f}")

    sns.set_theme(style="whitegrid")
    plt.figure(figsize=(10, 8))

    sns.regplot(data=df_merged, x='user_rating', y='combined_score', 
                scatter_kws={'alpha': 0.15, 's': 20, 'color': '#3498db', 'label': 'Voti Utente'},
                line_kws={'color': '#e74c3c', 'lw': 2, 'label': 'Trend Sentiment'},
                x_jitter=0.3, y_jitter=0.1)

    plt.plot([1, 10], [1, 10], 'k--', alpha=0.5, label='Ideale (x=y)')
    plt.legend(loc='lower right')
    
    plt.title('Calibrazione Sentiment Analysis vs. Voti Skytrax', fontsize=16, pad=20)
    plt.xlabel('Voto Utente (Skytrax) [1-10]', fontsize=14)
    plt.ylabel('Score Sentiment (Ensemble) [1-10]', fontsize=14)
    
    stats_text = (f"Correlazione: {pearson_corr:.3f}\n"
                  f"MAE: {mae:.2f}\n"
                  f"Bias: {mean_diff:+.2f}")
    
    plt.annotate(stats_text, xy=(0.05, 0.95), xycoords='axes fraction', 
                 verticalalignment='top', bbox=dict(boxstyle='round,pad=0.5', fc='white', alpha=0.8, ec='gray'))

    plt.xticks(range(1, 11))
    plt.yticks(range(1, 11))
    plt.xlim(0.5, 10.5)
    plt.ylim(0.5, 10.5)

    plt.tight_layout()
    output_png = os.path.join(PLOTS_DIR, 'sentiment_calibration_skytrax.png')
    plt.savefig(output_png, dpi=300)
    print(f"Plot saved to: {output_png}")
    plt.close()

    plt.figure(figsize=(12, 6))
    sns.kdeplot(df_merged['user_rating'], fill=True, label='Voti Utente', color='#2ecc71', alpha=0.4, clip=(0, 10))
    sns.kdeplot(df_merged['combined_score'], fill=True, label='Sentiment Score', color='#3498db', alpha=0.4, clip=(0, 10))
    plt.title('Distribuzione Voti Skytrax Utente vs. Sentiment', fontsize=16)
    plt.xlabel('Score [1.0 - 10.0]', fontsize=14)
    plt.ylabel('Densità', fontsize=14)
    plt.legend()
    plt.tight_layout()
    output_dist = os.path.join(PLOTS_DIR, 'sentiment_distribution_comparison.png')
    plt.savefig(output_dist, dpi=300)
    print(f"Distribution plot saved to: {output_dist}")
    plt.close()

if __name__ == "__main__":
    plot_calibration()
