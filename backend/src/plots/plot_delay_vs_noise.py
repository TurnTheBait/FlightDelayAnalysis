import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt
import os
import sys
import numpy as np
import warnings

current_script_dir = os.path.dirname(os.path.abspath(__file__))
backend_dir = os.path.dirname(os.path.dirname(current_script_dir))
data_dir = os.path.join(backend_dir, 'data', 'sentiment')
results_dir = os.path.join(backend_dir, 'results', 'figures', 'delay_vs_noise')
os.makedirs(results_dir, exist_ok=True)

df_delay_file = os.path.join(data_dir, 'sentiment_results_delay.csv')
df_noise_file = os.path.join(data_dir, 'sentiment_results_noise.csv')

df_delay_raw = pd.read_csv(df_delay_file) if os.path.exists(df_delay_file) else pd.DataFrame()
df_noise_raw = pd.read_csv(df_noise_file) if os.path.exists(df_noise_file) else pd.DataFrame()

if df_delay_raw.empty and df_noise_raw.empty:
    print("Nessun dato trovato per generare i plot.")
    sys.exit()

def aggregate_data(df, category):
    if df.empty:
        return pd.DataFrame()
        
    agg = df.groupby('airport_code').agg({
        'combined_score': 'mean',
        'pressure_impact_score': 'mean',
        'text': 'count'
    }).reset_index()
    
    agg = agg.rename(columns={'text': 'review_count'})
    
    rename_cols = {c: f"{c}_{category}" for c in agg.columns if c != 'airport_code'}
    agg = agg.rename(columns=rename_cols)
    return agg

df_delay = aggregate_data(df_delay_raw, 'delay')
df_noise = aggregate_data(df_noise_raw, 'noise')

df_merged = pd.merge(df_delay, df_noise, on='airport_code', how='outer').fillna(0)

df_merged['total_reviews'] = df_merged['review_count_delay'] + df_merged['review_count_noise']
top_airports = df_merged.sort_values(by='total_reviews', ascending=False).head(20)

warnings.filterwarnings('ignore')

plt.figure(figsize=(12, 10))
df_scatter = df_merged[(df_merged['combined_score_delay'] > 0) & (df_merged['combined_score_noise'] > 0)].copy()

sns.scatterplot(
    data=df_scatter,
    x='combined_score_delay',
    y='combined_score_noise',
    size='total_reviews',
    sizes=(50, 400),
    hue='total_reviews',
    palette='viridis',
    alpha=0.7,
    edgecolor='black',
    legend='auto'
)

plt.axvline(5.5, color='gray', linestyle='--')
plt.axhline(5.5, color='gray', linestyle='--')

for i, row in df_scatter.iterrows():
    plt.text(row['combined_score_delay'], row['combined_score_noise'], row['airport_code'], 
             fontsize=9, alpha=0.8, ha='center', va='bottom')

plt.text(3.25, 8.5, 'Pessimo Delay\nOttimo Noise', fontsize=12, color='gray', weight='bold', ha='center', va='center')
plt.text(7.75, 8.5, 'Ottimo Delay\nOttimo Noise', fontsize=12, color='gray', weight='bold', ha='center', va='center')
plt.text(3.25, 3.5, 'Pessimo Delay\nPessimo Noise', fontsize=12, color='gray', weight='bold', ha='center', va='center')
plt.text(7.75, 3.5, 'Ottimo Delay\nPessimo Noise', fontsize=12, color='gray', weight='bold', ha='center', va='center')

plt.title('Matrice Relazionale Sentiment: Delay vs Noise', fontsize=16, weight='bold')
plt.xlabel('Voto Sentiment Delay (1-10)', fontsize=12)
plt.ylabel('Voto Sentiment Noise (1-10)', fontsize=12)
plt.xlim(1, 10.5)
plt.ylim(1, 10.5)
plt.grid(True, linestyle=':', alpha=0.5)

plt.legend(title='N. Recensioni', bbox_to_anchor=(1.02, 1), loc='upper left')

plt.tight_layout()

scatter_grid_path = os.path.join(results_dir, 'scatter_relational_delay_vs_noise.png')
plt.savefig(scatter_grid_path, dpi=300)
plt.close()

print(f"Salvati i plot in {results_dir}")