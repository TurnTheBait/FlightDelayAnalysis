import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt
import os
import numpy as np
import matplotlib as mpl
import textwrap

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
    sns.barplot(x='composite_score_scaled', y='airport_code', hue='airport_code', data=top_airports, palette=colors_top, edgecolor='black', legend=False)
    plt.title(f'Top {top_n} Airports by Composite Score\n(Volume + Sentiment)', fontsize=14, weight='bold')
    plt.xlabel('Composite Score (0-10)')
    plt.ylabel('Airport Code')
    plt.xlim(0, 10.5)
    
    for i, row in enumerate(top_airports.itertuples()):
        label = f"{row.composite_score_scaled:.1f} (Vol: {int(row.total_flights)})"
        plt.text(row.composite_score_scaled + 0.1, i, label, va='center', fontsize=9, weight='bold')

    plt.subplot(1, 2, 2)
    colors_bottom = get_colors(bottom_airports['composite_score_scaled'])
    sns.barplot(x='composite_score_scaled', y='airport_code', hue='airport_code', data=bottom_airports, palette=colors_bottom, edgecolor='black', legend=False)
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
    
    df['rounded_score'] = df['composite_score_scaled'].round(1)
    
    def create_label(codes):
        code_list = list(codes)
        if len(code_list) > 10:
             text = ", ".join(code_list[:10]) + f", (+{len(code_list)-10})"
        else:
            text = ", ".join(code_list)
        return textwrap.fill(text, width=40)

    aggregated_wa = df.groupby('rounded_score').agg({
        'airport_code': create_label,
        'composite_score_scaled': 'mean' 
    }).reset_index()
    
    aggregated_wa = aggregated_wa.sort_values('rounded_score', ascending=False)
    
    total_lines = aggregated_wa['airport_code'].apply(lambda x: x.count('\n') + 1).sum()
    fig_height_agg = max(10, len(aggregated_wa) * 0.5 + total_lines * 0.25)
    
    plt.figure(figsize=(16, fig_height_agg))
    
    norm_score = mpl.colors.Normalize(vmin=0, vmax=10)
    cmap_score = mpl.cm.RdYlGn
    
    colors_agg = [cmap_score(norm_score(v)) for v in aggregated_wa['rounded_score']]
    
    ax_agg = sns.barplot(x='rounded_score', y='airport_code', hue='airport_code', data=aggregated_wa, palette=colors_agg, edgecolor='black', legend=False)
    
    plt.title('Aggregated Composite Ranking (Sentiment + Volume)', fontsize=16, weight='bold')
    plt.xlabel('Composite Score (0-10)', fontsize=12)
    plt.ylabel('Airports (Codes)', fontsize=12)
    plt.xlim(0, 10.5)
    
    for i, row in enumerate(aggregated_wa.itertuples()):
        val = row.rounded_score
        ax_agg.text(row.rounded_score + 0.05, i, f"{val:.1f}", va='center', fontsize=10, weight='bold')

    plt.grid(True, axis='x', linestyle='--', alpha=0.3)
    plt.tight_layout()
    
    output_aggregated_comp = os.path.join(OUTPUT_DIR, 'composite_aggregated_ranking.png')
    plt.savefig(output_aggregated_comp, dpi=300, bbox_inches='tight', pad_inches=0.5)
    print(f"Aggregated composite plot saved to: {output_aggregated_comp}")

if __name__ == "__main__":
    main()
