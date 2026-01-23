import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt
import os
import numpy as np
import matplotlib as mpl

current_script_dir = os.path.dirname(os.path.abspath(__file__))
src_dir = os.path.dirname(current_script_dir)
backend_dir = os.path.dirname(src_dir)

INPUT_FILE = os.path.join(backend_dir, 'results', 'tables', 'airport_volume_analysis_summary.csv')
OUTPUT_DIR = os.path.join(backend_dir, 'results', 'figures', 'volume_analysis')
os.makedirs(OUTPUT_DIR, exist_ok=True)

def main():
    if not os.path.exists(INPUT_FILE):
        print(f"Error: File {INPUT_FILE} not found.")
        return

    print(f"Loading data from {INPUT_FILE}...")
    df = pd.read_csv(INPUT_FILE)
    
    df['total_flights'] = pd.to_numeric(df['total_flights'], errors='coerce').fillna(0)
    df['global_sentiment'] = pd.to_numeric(df['global_sentiment'], errors='coerce')
    df['composite_score_scaled'] = pd.to_numeric(df['composite_score_scaled'], errors='coerce')
    
    norm = mpl.colors.Normalize(vmin=0, vmax=10)
    cmap = mpl.cm.RdYlGn
    
    def get_colors(values):
        return [cmap(norm(v)) for v in values]
    
    top_n = 15
    df_sorted = df.sort_values('composite_score_scaled', ascending=False)
    
    top_airports = df_sorted.head(top_n)
    bottom_airports = df_sorted.tail(top_n)
    
    plt.figure(figsize=(18, 10))
    
    plt.subplot(1, 2, 1)

    colors_top = get_colors(top_airports['composite_score_scaled'])
    sns.barplot(x='composite_score_scaled', y='airport_code', data=top_airports, palette=colors_top, edgecolor='black')
    plt.title(f'Top {top_n} Airports by Composite Score\n(Volume + Sentiment)', fontsize=14, weight='bold')
    plt.xlabel('Composite Score (0-10)')
    plt.ylabel('Airport Code')
    plt.xlim(0, 10.5)
    
    for i, row in enumerate(top_airports.itertuples()):
        label = f"{row.composite_score_scaled:.1f} (Vol: {int(row.total_flights)})"
        plt.text(row.composite_score_scaled + 0.1, i, label, va='center', fontsize=9, weight='bold')

    plt.subplot(1, 2, 2)
    colors_bottom = get_colors(bottom_airports['composite_score_scaled'])
    sns.barplot(x='composite_score_scaled', y='airport_code', data=bottom_airports, palette=colors_bottom, edgecolor='black')
    plt.title(f'Bottom {top_n} Airports by Composite Score', fontsize=14, weight='bold')
    plt.xlabel('Composite Score (0-10)')
    plt.ylabel('')
    plt.xlim(0, 10.5)

    for i, row in enumerate(bottom_airports.itertuples()):
        label = f"{row.composite_score_scaled:.1f} (Vol: {int(row.total_flights)})"
        plt.text(row.composite_score_scaled + 0.1, i, label, va='center', fontsize=9, weight='bold')

    plt.tight_layout()
    output_ranking = os.path.join(OUTPUT_DIR, 'composite_score_ranking.png')
    plt.savefig(output_ranking, dpi=300)
    print(f"Ranking plot saved to: {output_ranking}")
    
    plt.figure(figsize=(12, 8))
    
    scatter = sns.scatterplot(
        data=df, 
        x='total_flights', 
        y='global_sentiment', 
        size='total_mentions', 
        hue='composite_score_scaled', 
        sizes=(20, 500), 
        palette='RdYlGn', 
        hue_norm=(0, 10),
        edgecolor='black', 
        alpha=0.7
    )
    
    plt.xscale('log')
    plt.title('Flight Volume vs. Global Sentiment', fontsize=16, weight='bold')
    plt.xlabel('Total Flights (Log Scale)', fontsize=12)
    plt.ylabel('Global Sentiment (2-10)', fontsize=12)

    plt.ylim(0, 10.5)
    plt.grid(True, which="both", ls="-", alpha=0.2)
    plt.axhline(y=6, color='gray', linestyle='--', label='Neutral Sentiment (6.0)')

    top_vol = df.nlargest(5, 'total_flights')
    top_sent = df.nlargest(3, 'global_sentiment')
    bot_sent = df.nsmallest(3, 'global_sentiment')
    
    points_to_label = pd.concat([top_vol, top_sent, bot_sent]).drop_duplicates(subset=['airport_code'])
    
    for row in points_to_label.itertuples():
        plt.text(row.total_flights, row.global_sentiment, row.airport_code, fontsize=9, weight='bold')

    plt.tight_layout()
    output_scatter = os.path.join(OUTPUT_DIR, 'volume_vs_sentiment.png')
    plt.savefig(output_scatter, dpi=300)
    print(f"Scatter plot saved to: {output_scatter}")

if __name__ == "__main__":
    main()
