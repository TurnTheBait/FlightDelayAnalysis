import pandas as pd
import os
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.ticker as ticker
import seaborn as sns
from scipy import stats

current_script_dir = os.path.dirname(os.path.abspath(__file__))
src_dir = os.path.dirname(current_script_dir)
backend_dir = os.path.dirname(src_dir)

VOLUME_SUMMARY_PATH = os.path.join(backend_dir, 'results', 'tables', 'airport_volume_analysis_summary.csv')
FIGURES_DIR = os.path.join(backend_dir, 'results', 'figures', 'category_benchmarking')
TABLES_DIR = os.path.join(backend_dir, 'results', 'tables', 'category_benchmarking')

os.makedirs(FIGURES_DIR, exist_ok=True)
os.makedirs(TABLES_DIR, exist_ok=True)

CATEGORY_THRESHOLDS = [
    ('Hub',    100000, float('inf')),
    ('Large',  20000,  99999),
    ('Medium', 5000,   19999),
    ('Small',  0,      4999),
]

SENTIMENT_COLS = {
    'general': 'global_weighted_sentiment',
    'delay':   'delay_weighted_sentiment',
    'noise':   'noise_weighted_sentiment',
}

CATEGORY_COLORS = {
    'Hub':    '#e74c3c',
    'Large':  '#f39c12',
    'Medium': '#3498db',
    'Small':  '#2ecc71',
}


def classify_airport(total_flights):
    for name, low, high in CATEGORY_THRESHOLDS:
        if low <= total_flights <= high:
            return name
    return 'Small'


def build_category_table(df_cat, mode, sentiment_col):
    """Z-score normalizzazione e ranking dentro un singolo gruppo."""
    df = df_cat.copy()
    df['sentiment_score'] = df[sentiment_col]
    cat_mean = df['sentiment_score'].mean()
    cat_std  = df['sentiment_score'].std(ddof=0)

    if cat_std > 0:
        df['z_score'] = (df['sentiment_score'] - cat_mean) / cat_std
    else:
        df['z_score'] = 0.0

    df['category_mean'] = round(cat_mean, 3)
    df = df.sort_values('sentiment_score', ascending=False).reset_index(drop=True)
    df['rank'] = range(1, len(df) + 1)

    out_cols = ['airport_code', 'name', 'total_flights',
                'sentiment_score', 'category_mean', 'z_score', 'rank']
    return df[out_cols], cat_mean


def plot_category_benchmark(df_table, cat_name, cat_mean, mode):
    """Bar chart orizzontale con barra media tratteggiata."""
    sns.set_theme(style='whitegrid', context='talk')

    n = len(df_table)
    fig_height = max(5, n * 0.45 + 1.5)
    fig, ax = plt.subplots(figsize=(12, fig_height))

    df_plot = df_table.sort_values('sentiment_score', ascending=True)

    cmap = plt.cm.RdYlGn
    scores = df_plot['sentiment_score'].values
    s_min, s_max = scores.min(), scores.max()
    if s_max > s_min:
        norm_vals = (scores - s_min) / (s_max - s_min)
    else:
        norm_vals = np.full_like(scores, 0.5)
    colors = [cmap(v) for v in norm_vals]

    bars = ax.barh(
        y=range(len(df_plot)),
        width=df_plot['sentiment_score'],
        color=colors,
        edgecolor='white',
        linewidth=0.6,
        height=0.7,
        alpha=0.85,
    )

    labels = [f"{row['airport_code']}  ({row['name'][:28]})" for _, row in df_plot.iterrows()]
    ax.set_yticks(range(len(df_plot)))
    ax.set_yticklabels(labels, fontsize=10)

    for i, (_, row) in enumerate(df_plot.iterrows()):
        ax.text(
            row['sentiment_score'] + 0.08,
            i,
            f"{row['sentiment_score']:.2f}",
            va='center', fontsize=9, fontweight='bold',
            color='#2c3e50',
        )

    ax.axvline(cat_mean, color='#2c3e50', linestyle='--', linewidth=2, alpha=0.7,
               label=f'Category Mean: {cat_mean:.2f}')

    ax.set_xlim(0, min(10.5, df_plot['sentiment_score'].max() + 1.0))
    ax.set_xlabel(f'{mode.capitalize()} Weighted Sentiment (1–10)', fontsize=12)
    ax.set_title(
        f'{mode.capitalize()} Sentiment Benchmarking — {cat_name} Airports\n'
        f'({len(df_plot)} airports  ·  Mean = {cat_mean:.2f})',
        fontsize=14, fontweight='bold', pad=15,
    )
    ax.legend(loc='lower right', fontsize=11, framealpha=0.9)
    ax.tick_params(axis='x', labelsize=11)

    plt.tight_layout()
    fname = f'benchmarking_{mode}_{cat_name.lower()}.png'
    path = os.path.join(FIGURES_DIR, fname)
    fig.savefig(path, dpi=300, bbox_inches='tight')
    plt.close(fig)
    print(f'  ✅ Saved figure → {fname}')
    return path


def build_summary_table(results, mode):
    """Tabella riassuntiva per un singolo mode con statistiche per categoria."""
    rows = []
    for cat_name in ['Hub', 'Large', 'Medium', 'Small']:
        if cat_name not in results:
            continue
        df_t = results[cat_name]
        rows.append({
            'category': cat_name,
            'n_airports': len(df_t),
            'mean_sentiment': round(df_t['sentiment_score'].mean(), 3),
            'std_sentiment':  round(df_t['sentiment_score'].std(), 3),
            'min_sentiment':  round(df_t['sentiment_score'].min(), 3),
            'max_sentiment':  round(df_t['sentiment_score'].max(), 3),
            'best_airport':   df_t.iloc[0]['airport_code'],
            'worst_airport':  df_t.iloc[-1]['airport_code'],
        })
    return pd.DataFrame(rows)


def main():
    print(f'Loading data from: {VOLUME_SUMMARY_PATH}')
    if not os.path.exists(VOLUME_SUMMARY_PATH):
        print(f'ERROR: {VOLUME_SUMMARY_PATH} not found.')
        return

    df = pd.read_csv(VOLUME_SUMMARY_PATH)

    df['category'] = df['total_flights'].apply(classify_airport)
    cat_counts = df['category'].value_counts()
    print('\nAirport distribution per category:')
    for cat in ['Hub', 'Large', 'Medium', 'Small']:
        print(f'  {cat:8s}: {cat_counts.get(cat, 0):3d} airports')

    for mode, col in SENTIMENT_COLS.items():
        print(f'\n{"="*55}')
        print(f'  Processing mode: {mode.upper()}')
        print(f'{"="*55}')

        df_valid = df.dropna(subset=[col]).copy()
        results = {}

        for cat_name in ['Hub', 'Large', 'Medium', 'Small']:
            df_cat = df_valid[df_valid['category'] == cat_name]
            if len(df_cat) < 2:
                print(f'  ⚠️  {cat_name}: only {len(df_cat)} airports, skipping.')
                continue

            df_table, cat_mean = build_category_table(df_cat, mode, col)
            results[cat_name] = df_table

            csv_name = f'benchmarking_{mode}_{cat_name.lower()}.csv'
            df_table.to_csv(os.path.join(TABLES_DIR, csv_name), index=False)
            print(f'  ✅ Saved table  → {csv_name}')
            plot_category_benchmark(df_table, cat_name, cat_mean, mode)

        df_summary = build_summary_table(results, mode)
        summary_path = os.path.join(TABLES_DIR, f'summary_{mode}.csv')
        df_summary.to_csv(summary_path, index=False)
        print(f'  ✅ Saved summary → summary_{mode}.csv')

    print('\n All done. Outputs in:')
    print(f'   Figures: {FIGURES_DIR}')
    print(f'   Tables:  {TABLES_DIR}')


if __name__ == '__main__':
    main()
