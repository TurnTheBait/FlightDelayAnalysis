import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import os
import numpy as np

current_script_dir = os.path.dirname(os.path.abspath(__file__))
src_dir = os.path.dirname(current_script_dir)
backend_dir = os.path.dirname(src_dir)
CSV_MENTIONS_PATH = os.path.join(backend_dir, 'results', 'tables', 'airport_analysis_summary.csv')
CSV_VOLUME_PATH = os.path.join(backend_dir, 'results', 'tables', 'airport_volume_analysis_summary.csv')

def generate_reliability_matrix(csv_path, x_col, y_col, output_filename, title, x_label, y_label, size_range=(50, 600)):
    if not os.path.exists(csv_path):
        print(f"ERRORE: File non trovato: {csv_path}")
        return

    df = pd.read_csv(csv_path)
    df = df[df[x_col] > 0].copy()
    global_mean_score = df[y_col].mean()
    median_volume = df[x_col].median()

    print(f"\nGenerazione matrice per: {output_filename}")
    print(f"Aeroporti analizzati: {len(df)}")
    print(f"Media Sentiment Globale: {global_mean_score:.2f}")
    print(f"Mediana {x_col}: {median_volume:.0f}")

    plt.figure(figsize=(14, 10))
    sns.set_theme(style="whitegrid")

    scatter = sns.scatterplot(
        data=df,
        x=x_col,
        y=y_col,
        size=x_col,
        sizes=size_range,
        hue=y_col,
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
        is_high_volume = row[x_col] > df[x_col].quantile(0.90)
        is_extreme_score = row[y_col] > 6 or row[y_col] < 2
        
        if is_high_volume or is_extreme_score:
            plt.text(
                row[x_col] + (df[x_col].max() * 0.01), 
                row[y_col], 
                row['airport_code'], 
                fontsize=9, 
                fontweight='bold', 
                alpha=0.8
            )

    plt.title(title, fontsize=16, fontweight='bold')
    plt.xlabel(x_label, fontsize=12)
    plt.ylabel(y_label, fontsize=12)
    
    if x_col == 'total_flights':
        plt.xscale('log')
        plt.xlabel(x_label + " (Log Scale)", fontsize=12)
    
    y_min, y_max = df[y_col].min(), df[y_col].max()
    margin = (y_max - y_min) * 0.1
    if margin == 0: margin = 0.5
    plt.ylim(y_min - margin, y_max + margin)

    plt.tight_layout()

    output_img = os.path.join(backend_dir, 'results', 'figures', output_filename)
    os.makedirs(os.path.dirname(output_img), exist_ok=True)
    plt.savefig(output_img, dpi=300)
    print(f"Grafico salvato in: {output_img}")

if __name__ == "__main__":
    generate_reliability_matrix(
        csv_path=CSV_MENTIONS_PATH,
        x_col="total_mentions",
        y_col="global_weighted_sentiment",
        output_filename='reliability_matrix.png',
        title="Matrice di Affidabilità: Volume vs Sentiment\n(Verifica della veridicità dei dati)",
        x_label="Volume di Dati Raccolti (News + Reddit + Skytrax)",
        y_label="Sentiment Score Globale (1-10)"
    )
    
    generate_reliability_matrix(
        csv_path=CSV_VOLUME_PATH,
        x_col="total_flights",
        y_col="global_weighted_sentiment",
        output_filename='reliability_matrix_volume.png',
        title="Matrice di Affidabilità: Volume Voli vs Sentiment",
        x_label="Volume Totale dei Voli",
        y_label="Sentiment Score Globale (1-10)"
    )