import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import os
import numpy as np

current_script_dir = os.path.dirname(os.path.abspath(__file__))
src_dir = os.path.dirname(current_script_dir)
backend_dir = os.path.dirname(src_dir)
CSV_PATH = os.path.join(backend_dir, 'results', 'tables', 'airport_analysis_summary.csv')

if not os.path.exists(CSV_PATH):
    print(f"ERRORE: File non trovato: {CSV_PATH}")
    print("Esegui prima 'generate_summary_table.py'")
    exit()

df = pd.read_csv(CSV_PATH)
df = df[df['total_mentions'] > 0].copy()
global_mean_score = df['delay_sentiment'].mean()
median_volume = df['total_mentions'].median()

print(f"Aeroporti analizzati: {len(df)}")
print(f"Media Sentiment Globale: {global_mean_score:.2f}")
print(f"Mediana Volume Dati: {median_volume:.0f}")

plt.figure(figsize=(14, 10))
sns.set_theme(style="whitegrid")

scatter = sns.scatterplot(
    data=df,
    x="total_mentions",
    y="delay_sentiment",
    size="total_mentions",
    sizes=(50, 600),
    hue="delay_sentiment",
    palette="RdYlGn",  
    alpha=0.8,
    edgecolor="black",
    linewidth=0.5,
    legend=False
)

scatter = sns.scatterplot(
    data=df,
    x="total_mentions",
    y="delay_sentiment",
    size="total_mentions",
    sizes=(50, 600),
    hue="delay_sentiment",
    palette="RdYlGn",  
    alpha=0.8,
    edgecolor="black",
    linewidth=0.5,
    legend=False
)

plt.axhline(y=global_mean_score, color='blue', linestyle='--', linewidth=1.5, label=f'Media Settore ({global_mean_score:.2f})')
plt.axvline(x=median_volume, color='gray', linestyle=':', linewidth=1.5, label='Mediana Volume')
texts = []
for i, row in df.iterrows():
    
    is_high_volume = row['total_mentions'] > df['total_mentions'].quantile(0.90)
    is_extreme_score = row['delay_sentiment'] > 6 or row['delay_sentiment'] < 2
    
    if is_high_volume or is_extreme_score:
        plt.text(
            row['total_mentions'] + (df['total_mentions'].max() * 0.01), 
            row['delay_sentiment'], 
            row['airport_code'], 
            fontsize=9, 
            fontweight='bold', 
            alpha=0.8
        )

plt.title("Matrice di Affidabilità: Volume vs Sentiment\n(Verifica della veridicità dei dati)", fontsize=16, fontweight='bold')
plt.xlabel("Volume di Dati Raccolti (News + Reddit + Skytrax)", fontsize=12)
plt.ylabel("Sentiment Score Globale (1-10)", fontsize=12)
plt.ylim(0, 10) 

plt.text(df['total_mentions'].max()*0.9, 9.5, "LEADER SOLIDI\n(Tanti dati, Voto alto)", 
         color='green', fontweight='bold', ha='center', bbox=dict(facecolor='white', alpha=0.7))

plt.text(df['total_mentions'].max()*0.9, 0.5, "CRITICITÀ CONFERMATE\n(Tanti dati, Voto basso)", 
         color='darkred', fontweight='bold', ha='center', bbox=dict(facecolor='white', alpha=0.7))

plt.tight_layout()

output_img = os.path.join(backend_dir, 'results', 'figures', 'reliability_matrix.png')
os.makedirs(os.path.dirname(output_img), exist_ok=True)
plt.savefig(output_img, dpi=300)
print(f"Grafico salvato in: {output_img}")