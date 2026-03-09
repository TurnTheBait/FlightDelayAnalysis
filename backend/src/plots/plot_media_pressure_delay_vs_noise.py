import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt
import os
import sys
import numpy as np
import warnings

current_script_dir = os.path.dirname(os.path.abspath(__file__))
backend_dir = os.path.dirname(os.path.dirname(current_script_dir))
data_file = os.path.join(backend_dir, 'results', 'tables', 'airport_analysis_summary.csv')
results_dir = os.path.join(backend_dir, 'results', 'figures', 'delay_vs_noise')
os.makedirs(results_dir, exist_ok=True)

if not os.path.exists(data_file):
    print(f"File {data_file} non trovato.")
    sys.exit()

df = pd.read_csv(data_file)
df = df[(df['delay_reviews_count'] >= 10) & (df['noise_reviews_count'] >= 10)]

if df.empty or 'delay_reviews_count' not in df.columns or 'noise_reviews_count' not in df.columns:
    print("Dati mancanti per plot pressione mediatica.")
    sys.exit()

pop_file = os.path.join(backend_dir, 'results', 'tables', 'noise_sentiment_10km_population.csv')
if os.path.exists(pop_file):
    df_pop = pd.read_csv(pop_file)
    if 'airport_code' in df_pop.columns and 'population_20km' in df_pop.columns:
        df = df.merge(df_pop[['airport_code', 'population_20km']], on='airport_code', how='left')

df['delay_pressure'] = np.log1p(df['delay_reviews_count'])
df['noise_pressure'] = np.log1p(df['noise_reviews_count'])

warnings.filterwarnings('ignore')

plt.figure(figsize=(12, 10))
df_scatter = df[(df['delay_pressure'] > 0) | (df['noise_pressure'] > 0)].copy()

sns.scatterplot(
    data=df_scatter,
    x='delay_pressure',
    y='noise_pressure',
    size='media_pressure_index',
    sizes=(50, 400),
    hue='media_pressure_index',
    palette='magma',
    alpha=0.7,
    edgecolor='black',
    legend='auto'
)

avg_delay = df_scatter['delay_pressure'].mean()
avg_noise = df_scatter['noise_pressure'].mean()

plt.axvline(avg_delay, color='gray', linestyle='--')
plt.axhline(avg_noise, color='gray', linestyle='--')

for i, row in df_scatter.iterrows():
    plt.text(row['delay_pressure'], row['noise_pressure'] + 0.05, row['airport_code'], 
             fontsize=9, alpha=0.8, ha='center', va='bottom')

plt.title('Pressione Mediatica: Delay vs Noise', fontsize=16, weight='bold')
plt.xlabel('Pressione Mediatica Delay (log)', fontsize=12)
plt.ylabel('Pressione Mediatica Noise (log)', fontsize=12)
plt.grid(True, linestyle=':', alpha=0.5)

plt.legend(title='Indice Pressione(Tot)', bbox_to_anchor=(1.02, 1), loc='upper left')

plt.tight_layout()

scatter_path = os.path.join(results_dir, 'scatter_media_pressure_delay_vs_noise.png')
plt.savefig(scatter_path, dpi=300)
plt.close()

print(f"Salvato il plot pressione mediatica in {results_dir}")

print("Calcolando le correlazioni tra pressione mediatica e sentiment...")
correlation_vars = ['delay_pressure', 'noise_pressure', 'delay_weighted_sentiment', 'noise_weighted_sentiment']
if 'population_20km' in df.columns:
    correlation_vars.append('population_20km')

df_corr = df[correlation_vars].copy()
correlation_matrix = df_corr.corr(method='pearson')

tables_dir = os.path.join(backend_dir, 'results', 'tables')
os.makedirs(tables_dir, exist_ok=True)
corr_csv_path = os.path.join(tables_dir, 'media_pressure_vs_sentiment_correlation.csv')
correlation_matrix.to_csv(corr_csv_path)
print(f"Tabella delle correlazioni salvata in: {corr_csv_path}")

plt.figure(figsize=(10, 8))
sns.heatmap(
    correlation_matrix, 
    annot=True, 
    cmap='coolwarm', 
    vmin=-1, vmax=1, 
    center=0,
    square=True,
    linewidths=.5,
    cbar_kws={"shrink": .8}
)
plt.title('Correlazione: Pressione Mediatica vs Sentiment Score', fontsize=16, weight='bold')

plt.tight_layout()
heatmap_path = os.path.join(results_dir, 'heatmap_media_pressure_vs_sentiment_correlation.png')
plt.savefig(heatmap_path, dpi=300)
plt.close()
print(f"Salvato plot heatmap correlazioni in: {heatmap_path}")
