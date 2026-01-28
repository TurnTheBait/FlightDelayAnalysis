import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt
import os
import matplotlib as mpl

current_script_dir = os.path.dirname(os.path.abspath(__file__))
backend_dir = os.path.dirname(os.path.dirname(current_script_dir))
INPUT_FILE = os.path.join(backend_dir, 'data', 'sentiment', 'sentiment_scored_delay.csv')

OUTPUT_DIR_FIG = os.path.join(backend_dir, 'results', 'figures', 'delay')
OUTPUT_DIR_TAB = os.path.join(backend_dir, 'results', 'tables', 'delay')

def main():
    if not os.path.exists(INPUT_FILE):
        print(f"Error: Sentiment file not found: {INPUT_FILE}")
        exit()

    os.makedirs(OUTPUT_DIR_FIG, exist_ok=True)
    os.makedirs(OUTPUT_DIR_TAB, exist_ok=True)

    df = pd.read_csv(INPUT_FILE)

    if df.empty:
        print("Warning: Sentiment file is empty.")
        return

    df['score_scaled'] = df['stars_score'] * 2

    agg_data = df.groupby('airport_code')['score_scaled'].agg(['mean', 'count']).reset_index()
    agg_data = agg_data.sort_values('mean', ascending=False)
    
    agg_table_path = os.path.join(OUTPUT_DIR_TAB, 'sentiment_aggregated_delay.csv')
    agg_data.to_csv(agg_table_path, index=False)
    print(f"Aggregated table saved to: {agg_table_path}")

    norm = mpl.colors.Normalize(vmin=0, vmax=10)
    cmap = mpl.cm.RdYlGn
    
    def get_colors(values):
        return [cmap(norm(v)) for v in values]

    top_n = 15
    top_airports = agg_data.head(top_n)
    bottom_airports = agg_data.tail(top_n)
    
    top_airports.to_csv(os.path.join(OUTPUT_DIR_TAB, 'top_airports_delay.csv'), index=False)
    bottom_airports.to_csv(os.path.join(OUTPUT_DIR_TAB, 'bottom_airports_delay.csv'), index=False)

    plt.figure(figsize=(18, 10))

    plt.subplot(1, 2, 1)
    colors_top = get_colors(top_airports['mean'])
    sns.barplot(x='mean', y='airport_code', data=top_airports, hue='mean', palette=colors_top, edgecolor='black', legend=False)
    plt.title(f'Top {top_n} Airports by Delay Perception', fontsize=14, weight='bold')
    plt.xlabel('Average Score (0-10)')
    plt.ylabel('')
    plt.xlim(0, 10.5)
    plt.axvline(x=6, color='black', linestyle='--', linewidth=1, label='Neutral (6.0)')

    for i, row in enumerate(top_airports.itertuples()):
       plt.text(row.mean + 0.1, i, f"{row.mean:.1f}", va='center', fontsize=10, weight='bold')

    plt.subplot(1, 2, 2)
    colors_bottom = get_colors(bottom_airports['mean'])
    sns.barplot(x='mean', y='airport_code', data=bottom_airports, hue='mean', palette=colors_bottom, edgecolor='black', legend=False)
    plt.title(f'Bottom {top_n} Airports by Delay Perception', fontsize=14, weight='bold')
    plt.xlabel('Average Score (0-10)')
    plt.ylabel('')
    plt.xlim(0, 10.5)
    plt.axvline(x=6, color='black', linestyle='--', linewidth=1, label='Neutral (6.0)')

    for i, row in enumerate(bottom_airports.itertuples()):
       plt.text(row.mean + 0.1, i, f"{row.mean:.1f}", va='center', fontsize=10, weight='bold')

    plt.tight_layout()
    output_ranking = os.path.join(OUTPUT_DIR_FIG, 'sentiment_ranking_top_bottom_delay.png')
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

    if len(agg_data) >= 5:
        top_volume = agg_data.nlargest(5, 'count')
        top_score = agg_data.nlargest(3, 'mean')
        bottom_score = agg_data.nsmallest(3, 'mean')
        points_to_label = pd.concat([top_volume, top_score, bottom_score]).drop_duplicates()
        for row in points_to_label.itertuples():
           plt.text(row.count, row.mean, row.airport_code, fontsize=9, weight='bold', alpha=0.8)

    plt.title('Delay Perception: Volume vs. Sentiment', fontsize=14, weight='bold')
    plt.xlabel('Number of Mentions', fontsize=12)
    plt.ylabel('Average Sentiment Score (0-10)', fontsize=12)
    plt.grid(True, linestyle='--', alpha=0.6)
    plt.axhline(y=6, color='gray', linestyle='--', label='Neutral Threshold')
    plt.ylim(0, 10.5)

    output_scatter = os.path.join(OUTPUT_DIR_FIG, 'sentiment_scatter_delay.png')
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

    total_lines = aggregated_scores['airport_code'].apply(lambda x: x.count('\n') + 1).sum() if not aggregated_scores.empty else 10
    fig_height_agg = max(10, len(aggregated_scores) * 0.4 + total_lines * 0.25)
    plt.figure(figsize=(16, fig_height_agg))

    colors_agg = get_colors(aggregated_scores['rounded_score'])

    if not aggregated_scores.empty:
        ax_agg = sns.barplot(x='rounded_score', y='airport_code', data=aggregated_scores,hue='rounded_score', palette=colors_agg, edgecolor='black', legend=False)

        plt.title('Aggregated Delay Sentiment Ranking (Grouped by Score)', fontsize=16, weight='bold')
        plt.xlabel('Sentiment Score (0-10)', fontsize=12)
        plt.ylabel('Airports (Codes)', fontsize=12)
        plt.xlim(0, 10.5)
        plt.axvline(x=6, color='black', linestyle='--', linewidth=1)

        for i, row in enumerate(aggregated_scores.itertuples()):
            ax_agg.text(row.rounded_score + 0.05, i, f"{row.rounded_score:.1f}", va='center', fontsize=10, weight='bold')

    plt.tight_layout()
    output_aggregated = os.path.join(OUTPUT_DIR_FIG, 'sentiment_aggregated_delay.png')
    plt.savefig(output_aggregated, dpi=300, bbox_inches='tight', pad_inches=1.0)
    print(f"Aggregated plot saved to: {output_aggregated}")

if __name__ == "__main__":
    main()
