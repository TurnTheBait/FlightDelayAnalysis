import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt
import os
import sys
import numpy as np

current_script_dir = os.path.dirname(os.path.abspath(__file__))
backend_dir = os.path.dirname(os.path.dirname(current_script_dir))
data_dir = os.path.join(backend_dir, 'data', 'sentiment')
results_dir = os.path.join(backend_dir, 'results', 'figures')
os.makedirs(results_dir, exist_ok=True)

df_delay_file = os.path.join(data_dir, 'sentiment_results_delay.csv')
df_noise_file = os.path.join(data_dir, 'sentiment_results_noise.csv')

def process_file_and_update(filepath):
    if not os.path.exists(filepath):
        print(f"File {filepath} not found.")
        return pd.DataFrame()
    df = pd.read_csv(filepath)
    
    needs_save = False
    
    if 'media_pressure_index' not in df.columns or 'pressure_impact_score' not in df.columns:
        counts = df['airport_code'].value_counts().to_dict()
        df['media_pressure_index'] = df['airport_code'].map(counts).fillna(1).apply(np.log1p)
        df['pressure_impact_score'] = (df['combined_score'] - 3.0) * df['media_pressure_index']
        needs_save = True

    if needs_save:
        df.to_csv(filepath, index=False)
        print(f"Aggiornato il file {filepath} con gli indici di pressione mediatica.")
        
    return df

df_delay_raw = process_file_and_update(df_delay_file)
df_noise_raw = process_file_and_update(df_noise_file)

if df_delay_raw.empty and df_noise_raw.empty:
    print("Nessun dato trovato per generare i plot.")
    sys.exit()

def aggregate_data(df, category):
    if df.empty:
        return pd.DataFrame()
        
    agg = df.groupby('airport_code').agg({
        'combined_score': 'mean',
        'pressure_impact_score': 'mean'
    }).reset_index()
    agg['review_count'] = df.groupby('airport_code')['text'].count().values
    
    rename_cols = {c: f"{c}_{category}" for c in agg.columns if c != 'airport_code'}
    agg = agg.rename(columns=rename_cols)
    return agg

df_delay = aggregate_data(df_delay_raw, 'delay')
df_noise = aggregate_data(df_noise_raw, 'noise')

df_merged = pd.merge(df_delay, df_noise, on='airport_code', how='outer').fillna(0)

df_merged['total_reviews'] = df_merged['review_count_delay'] + df_merged['review_count_noise']
top_airports = df_merged.sort_values(by='total_reviews', ascending=False).head(20)

import warnings
warnings.filterwarnings('ignore')

plt.figure(figsize=(14, 8))
melted_counts = pd.melt(top_airports, id_vars=['airport_code'], 
                        value_vars=['review_count_delay', 'review_count_noise'],
                        var_name='Category', value_name='Review Count')
melted_counts['Category'] = melted_counts['Category'].replace({'review_count_delay': 'Delay', 'review_count_noise': 'Noise'})

sns.barplot(data=melted_counts, x='airport_code', y='Review Count', hue='Category', palette=['#ECA3AE', '#99C7DF'])
plt.title('Numero di Recensioni per Aeroporto: Delay vs Noise (Top 20)', fontsize=16, weight='bold')
plt.xlabel('Codice Aeroporto', fontsize=12)
plt.ylabel('Numero di Recensioni', fontsize=12)
plt.xticks(rotation=45)
plt.legend(title='Categoria')
plt.tight_layout()
count_plot_path = os.path.join(results_dir, 'comparison_reviews_count_delay_vs_noise.png')
plt.savefig(count_plot_path, dpi=300)
plt.close()

plt.figure(figsize=(14, 8))
melted_scores = pd.melt(top_airports, id_vars=['airport_code'], 
                        value_vars=['combined_score_delay', 'combined_score_noise'],
                        var_name='Category', value_name='Sentiment Score')
melted_scores['Category'] = melted_scores['Category'].replace({'combined_score_delay': 'Delay', 'combined_score_noise': 'Noise'})
melted_scores['Sentiment Score'] = melted_scores['Sentiment Score'].replace(0, np.nan)
melted_scores['Sentiment Score'] = melted_scores['Sentiment Score'] * 2

sns.barplot(data=melted_scores, x='airport_code', y='Sentiment Score', hue='Category', palette=['#ECA3AE', '#99C7DF'])
plt.title('Voto Finale della Sentiment (1-10): Delay vs Noise (Top 20)', fontsize=16, weight='bold')
plt.xlabel('Codice Aeroporto', fontsize=12)
plt.ylabel('Media Voto Sentiment', fontsize=12)
plt.xticks(rotation=45)
plt.axhline(6, color='black', linestyle='--', label='Neutro (6.0)')
plt.legend(title='Categoria', loc='upper right')
plt.ylim(0, 10.5)
plt.tight_layout()
score_plot_path = os.path.join(results_dir, 'comparison_sentiment_score_delay_vs_noise.png')
plt.savefig(score_plot_path, dpi=300)
plt.close()

plt.figure(figsize=(14, 8))
melted_press = pd.melt(top_airports, id_vars=['airport_code'], 
                        value_vars=['pressure_impact_score_delay', 'pressure_impact_score_noise'],
                        var_name='Category', value_name='Pressure Impact Score')
melted_press['Category'] = melted_press['Category'].replace({'pressure_impact_score_delay': 'Delay', 'pressure_impact_score_noise': 'Noise'})
melted_press['Pressure Impact Score'] = melted_press['Pressure Impact Score'].replace(0, np.nan) # Gestione rimpiazzi fillna mancanti

sns.barplot(data=melted_press, x='airport_code', y='Pressure Impact Score', hue='Category', palette=['#ECA3AE', '#99C7DF'])
plt.title('Indice di Pressione Mediatica * Sentiment: Delay vs Noise (Top 20)', fontsize=16, weight='bold')
plt.xlabel('Codice Aeroporto', fontsize=12)
plt.ylabel('Voto di Impatto (Sentiment * Pressione)', fontsize=12)
plt.xticks(rotation=45)
plt.axhline(0, color='black', linestyle='--', label='Neutro (0)')
plt.legend(title='Categoria')
plt.tight_layout()
pressure_plot_path = os.path.join(results_dir, 'comparison_pressure_impact_delay_vs_noise.png')
plt.savefig(pressure_plot_path, dpi=300)
plt.close()

print(f"Salvati i plot in {results_dir}")
