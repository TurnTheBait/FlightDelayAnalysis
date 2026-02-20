import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt
import os
import matplotlib as mpl
import sys
from utils.airport_utils import get_icao_to_iata_mapping

current_script_dir = os.path.dirname(os.path.abspath(__file__))
backend_dir = os.path.dirname(os.path.dirname(current_script_dir))
src_dir = os.path.dirname(current_script_dir)

INPUT_FILE = os.path.join(backend_dir, 'data', 'sentiment', 'sentiment_results_general.csv')
OUTPUT_IMG = os.path.join(backend_dir, 'results', 'figures', 'sentiment_overview.png')
AIRPORTS_PATH = os.path.join(backend_dir, 'data', 'processed', 'airports', 'airports_filtered.csv')

sys.path.append(src_dir)

def main():
    if not os.path.exists(INPUT_FILE):
        print("Error: Sentiment file not found.")
        exit()

    df = pd.read_csv(INPUT_FILE)

    df['score_scaled'] = df['stars_score'] * 2

    agg_data = df.groupby('airport_code')['score_scaled'].agg(['mean', 'count']).reset_index()
    agg_data = agg_data.sort_values('mean', ascending=False)

    norm = mpl.colors.Normalize(vmin=0, vmax=10)
    cmap = mpl.cm.RdYlGn
    
    def get_colors(values):
        return [cmap(norm(v)) for v in values]

    top_n = 15
    top_airports = agg_data.head(top_n)
    bottom_airports = agg_data.tail(top_n)

    plt.figure(figsize=(18, 10))

    plt.subplot(1, 2, 1)
    colors_top = get_colors(top_airports['mean'])
    sns.barplot(x='mean', y='airport_code', hue='airport_code', data=top_airports, palette=colors_top, edgecolor='black', legend=False)
    plt.title(f'Top {top_n} Airports by Sentiment', fontsize=14, weight='bold')
    plt.xlabel('Average Score (0-10)')
    plt.ylabel('')
    plt.xlim(0, 10.5)
    plt.axvline(x=6, color='black', linestyle='--', linewidth=1, label='Neutral (6.0)')

    for i, row in enumerate(top_airports.itertuples()):
       plt.text(row.mean + 0.1, i, f"{row.mean:.1f}", va='center', fontsize=10, weight='bold')

    plt.subplot(1, 2, 2)
    colors_bottom = get_colors(bottom_airports['mean'])
    sns.barplot(x='mean', y='airport_code', hue='airport_code', data=bottom_airports, palette=colors_bottom, edgecolor='black', legend=False)
    plt.title(f'Bottom {top_n} Airports by Sentiment', fontsize=14, weight='bold')
    plt.xlabel('Average Score (0-10)')
    plt.ylabel('')
    plt.xlim(0, 10.5)
    plt.axvline(x=6, color='black', linestyle='--', linewidth=1, label='Neutral (6.0)')

    for i, row in enumerate(bottom_airports.itertuples()):
       plt.text(row.mean + 0.1, i, f"{row.mean:.1f}", va='center', fontsize=10, weight='bold')

    plt.tight_layout()
    output_ranking = os.path.join(backend_dir, 'results', 'figures', 'sentiment_ranking_top_bottom.png')
    os.makedirs(os.path.dirname(output_ranking), exist_ok=True)
    plt.savefig(output_ranking, dpi=300)
    print(f"Ranking plot saved to: {output_ranking}")

    plt.figure(figsize=(10, 6))
    
    sns.scatterplot(
        data=agg_data, 
        x='count', 
        y='mean', 
        size='count', 
        sizes=(50, 400), 
        hue='mean', 
        palette='RdYlGn', 
        hue_norm=(0, 10),
        edgecolor='black', 
        legend=False
    )

    top_volume = agg_data.nlargest(5, 'count')
    top_score = agg_data.nlargest(3, 'mean')
    bottom_score = agg_data.nsmallest(3, 'mean')

    points_to_label = pd.concat([top_volume, top_score, bottom_score]).drop_duplicates()

    for row in points_to_label.itertuples():
       plt.text(row.count, row.mean, row.airport_code, fontsize=9, weight='bold', alpha=0.8)

    plt.title('Volume vs. Sentiment', fontsize=14, weight='bold')
    plt.xlabel('Number of Reviews', fontsize=12)
    plt.ylabel('Average Sentiment Score (0-10)', fontsize=12)
    plt.grid(True, linestyle='--', alpha=0.6)
    plt.axhline(y=6, color='gray', linestyle='--', label='Neutral Threshold')
    plt.ylim(0, 10.5)

    output_scatter = os.path.join(backend_dir, 'results', 'figures', 'sentiment_scatter.png')
    plt.savefig(output_scatter, dpi=300)
    print(f"Scatter plot saved to: {output_scatter}")

    agg_data['rounded_score'] = agg_data['mean'].round(1)
    
    import textwrap
    def create_label(codes):
        code_list = list(codes)
        text = ", ".join(code_list)
        return textwrap.fill(text, width=40)

    aggregated_scores = agg_data.groupby('rounded_score').agg({
        'airport_code': create_label,
        'count': 'sum'
    }).reset_index()

    aggregated_scores = aggregated_scores.sort_values('rounded_score', ascending=False)

    total_lines = aggregated_scores['airport_code'].apply(lambda x: x.count('\n') + 1).sum()
    fig_height_agg = max(10, len(aggregated_scores) * 0.4 + total_lines * 0.25)
    plt.figure(figsize=(16, fig_height_agg))

    colors_agg = get_colors(aggregated_scores['rounded_score'])

    ax_agg = sns.barplot(x='rounded_score', y='airport_code', hue='airport_code', data=aggregated_scores, palette=colors_agg, edgecolor='black', legend=False)

    plt.title('Aggregated Sentiment Ranking (Grouped by Score)', fontsize=16, weight='bold')
    plt.xlabel('Sentiment Score (0-10)', fontsize=12)
    plt.ylabel('Airports (Codes)', fontsize=12)
    plt.xlim(0, 10.5)
    plt.axvline(x=6, color='black', linestyle='--', linewidth=1)

    for i, row in enumerate(aggregated_scores.itertuples()):
        ax_agg.text(row.rounded_score + 0.05, i, f"{row.rounded_score:.1f}", va='center', fontsize=10, weight='bold')

    plt.tight_layout()
    output_aggregated = os.path.join(backend_dir, 'results', 'figures', 'sentiment_aggregated.png')
    plt.savefig(output_aggregated, dpi=300, bbox_inches='tight', pad_inches=1.0)
    print(f"Aggregated plot saved to: {output_aggregated}")

if __name__ == "__main__":
    main()