import os
import sys
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns

def plot_linear_compensation():
    CURRENT_FILE = os.path.abspath(__file__)
    BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(CURRENT_FILE)))
    DATA_SENTIMENT_DIR = os.path.join(BASE_DIR, 'data', 'sentiment')
    PLOTS_DIR = os.path.join(BASE_DIR, 'results', 'figures', 'calibration')

    os.makedirs(PLOTS_DIR, exist_ok=True)

    sentiment_path = os.path.join(DATA_SENTIMENT_DIR, 'sentiment_results_raw_general.csv')
    
    if os.path.exists(sentiment_path):
        print(f"Loading data from {sentiment_path}...")
        df = pd.read_csv(sentiment_path)
        if 'combined_score' in df.columns:
            raw_scores = df['combined_score'].dropna().values
        else:
            print("[WARNING] 'combined_score' non trovato. Genero dati simulati.")
            raw_scores = np.random.normal(loc=3.5, scale=1.2, size=10000)
    else:
        print("[WARNING] File dati non trovato. Genero dati simulati.")
        raw_scores = np.random.normal(loc=3.5, scale=1.2, size=10000)
    
    raw_scores = np.clip(raw_scores, 1.0, 10.0)
    
    transformed_scores = np.clip((raw_scores * 1.2) + 1.0, 1.0, 10.0)
    
    sns.set_theme(style="whitegrid")
    fig, axes = plt.subplots(1, 2, figsize=(14, 6))
    
    bins = np.linspace(1, 10, 36)
    
    sns.histplot(raw_scores, bins=bins, kde=True, color="#e74c3c", 
                 ax=axes[0], stat='density', alpha=0.4, linewidth=0)
    axes[0].set_title("Prima: Punteggi Grezzi (Bias Negativo)", fontsize=14, pad=15, fontweight='bold')
    axes[0].set_xlabel("Punteggio [1.0 - 10.0]", fontsize=12)
    axes[0].set_ylabel("Densità", fontsize=12)
    axes[0].set_xlim(0.5, 10.5)
    axes[0].set_xticks(range(1, 11))
    
    median_raw = np.median(raw_scores)
    axes[0].axvline(median_raw, color='darkred', linestyle='--', alpha=0.7, label=f'Mediana: {median_raw:.1f}')
    axes[0].legend()
    
    sns.histplot(transformed_scores, bins=bins, kde=True, color="#2ecc71", 
                 ax=axes[1], stat='density', alpha=0.4, linewidth=0)
    axes[1].set_title("Dopo: Compensazione Lineare", fontsize=14, pad=15, fontweight='bold')
    axes[1].set_xlabel("Punteggio [1.0 - 10.0]", fontsize=12)
    axes[1].set_ylabel("Densità", fontsize=12)
    axes[1].set_xlim(0.5, 10.5)
    axes[1].set_xticks(range(1, 11))
    
    median_transformed = np.median(transformed_scores)
    axes[1].axvline(median_transformed, color='darkgreen', linestyle='--', alpha=0.7, label=f'Mediana: {median_transformed:.1f}')
    axes[1].legend()
    
    plt.tight_layout()
    
    output_png = os.path.join(PLOTS_DIR, 'linear_compensation_effect.png')
    plt.savefig(output_png, dpi=300, bbox_inches='tight')
    print(f"Grafico salvato in: {output_png}")
    plt.close()

if __name__ == "__main__":
    plot_linear_compensation()
