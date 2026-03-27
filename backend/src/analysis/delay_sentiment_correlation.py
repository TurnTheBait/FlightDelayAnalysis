import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.ticker as ticker
import seaborn as sns
import os
import sys
from scipy.stats import pearsonr, spearmanr

current_script_dir = os.path.dirname(os.path.abspath(__file__))
src_dir = os.path.dirname(current_script_dir)
backend_dir = os.path.dirname(src_dir)

VOLUME_SUMMARY_PATH = os.path.join(backend_dir, 'results', 'tables', 'airport_volume_analysis_summary.csv')
DELAYS_DATA_PATH = os.path.join(backend_dir, 'data', 'processed', 'delays', 'delays_consolidated_filtered.csv')
FIGURES_DIR = os.path.join(backend_dir, 'results', 'figures', 'delay_sentiment_correlation')
TABLES_DIR = os.path.join(backend_dir, 'results', 'tables', 'delay_sentiment_correlation')

os.makedirs(FIGURES_DIR, exist_ok=True)
os.makedirs(TABLES_DIR, exist_ok=True)

CATEGORY_THRESHOLDS = [
    ('Hub',    100000, float('inf')),
    ('Large',  40000,  99999),
    ('Medium', 5000,   39999),
    ('Small',  0,      4999),
]

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


def compute_airport_delays(delays_path):
    print("Loading flight delay data (this may take a while)...")
    df = pd.read_csv(
        delays_path,
        usecols=['SchedDepApt', 'MinLateDeparted', 'MinLateArrived', 'Cancelled'],
        low_memory=False
    )

    df['Cancelled'] = pd.to_numeric(df['Cancelled'], errors='coerce').fillna(0)
    df = df[df['Cancelled'] == 0].copy()

    df['MinLateDeparted'] = pd.to_numeric(df['MinLateDeparted'], errors='coerce').fillna(0)
    df['MinLateArrived'] = pd.to_numeric(df['MinLateArrived'], errors='coerce').fillna(0)

    airport_delays = df.groupby('SchedDepApt').agg(
        avg_dep_delay=('MinLateDeparted', 'mean'),
        median_dep_delay=('MinLateDeparted', 'median'),
        pct_delayed_15=('MinLateDeparted', lambda x: (x > 15).mean() * 100),
        avg_arr_delay=('MinLateArrived', 'mean'),
        n_flights_operated=('MinLateDeparted', 'count')
    ).reset_index()

    airport_delays.rename(columns={'SchedDepApt': 'airport_code'}, inplace=True)
    airport_delays = airport_delays.round(3)

    print(f"Computed delay stats for {len(airport_delays)} airports.")
    return airport_delays


def plot_scatter_per_category(df_cat, cat_name, color):
    if len(df_cat) < 3:
        print(f"  {cat_name}: too few airports ({len(df_cat)}), skipping scatter.")
        return

    sns.set_theme(style='whitegrid', context='talk')
    fig, ax = plt.subplots(figsize=(10, 8))

    ax.scatter(
        df_cat['avg_dep_delay'],
        df_cat['delay_weighted_sentiment'],
        s=80,
        color=color,
        edgecolor='white',
        linewidth=0.6,
        alpha=0.75,
        zorder=3
    )

    for _, row in df_cat.iterrows():
        ax.annotate(
            row['airport_code'],
            (row['avg_dep_delay'], row['delay_weighted_sentiment']),
            fontsize=8, alpha=0.85,
            xytext=(5, 5), textcoords='offset points'
        )

    if len(df_cat) >= 3:
        z = np.polyfit(df_cat['avg_dep_delay'], df_cat['delay_weighted_sentiment'], 1)
        p = np.poly1d(z)
        x_line = np.linspace(df_cat['avg_dep_delay'].min(), df_cat['avg_dep_delay'].max(), 100)
        ax.plot(x_line, p(x_line), '--', color='#2c3e50', linewidth=1.5, alpha=0.7, zorder=2)

    r_pearson, p_pearson = pearsonr(df_cat['avg_dep_delay'], df_cat['delay_weighted_sentiment'])
    r_spearman, p_spearman = spearmanr(df_cat['avg_dep_delay'], df_cat['delay_weighted_sentiment'])

    stats_text = f"Correlazione = {r_pearson:.3f}"
    props = dict(boxstyle='round,pad=0.5', facecolor='white', alpha=0.9, edgecolor='gray')
    ax.text(0.97, 0.03, stats_text, transform=ax.transAxes,
            fontsize=10, verticalalignment='bottom', horizontalalignment='right',
            bbox=props)

    ax.set_xlabel('Average Departure Delay (min)', fontsize=12)
    ax.set_ylabel('Delay Weighted Sentiment (1-10)', fontsize=12)
    ax.set_title(
        f'Avg Delay vs Delay Sentiment — {cat_name} Airports',
        fontsize=14, fontweight='bold', pad=15
    )

    plt.tight_layout()
    fname = f'scatter_delay_vs_sentiment_{cat_name.lower()}.png'
    fig.savefig(os.path.join(FIGURES_DIR, fname), dpi=300, bbox_inches='tight')
    plt.close(fig)
    print(f"  Saved: {fname}")


def plot_combined_scatter(df, categories_data):
    sns.set_theme(style='whitegrid', context='talk')
    fig, ax = plt.subplots(figsize=(12, 9))

    for cat_name, df_cat in categories_data.items():
        if len(df_cat) < 2:
            continue
        color = CATEGORY_COLORS[cat_name]
        ax.scatter(
            df_cat['avg_dep_delay'],
            df_cat['delay_weighted_sentiment'],
            s=70,
            color=color,
            edgecolor='white',
            linewidth=0.5,
            alpha=0.75,
            label=cat_name,
            zorder=3
        )

    for _, row in df.iterrows():
        ax.annotate(
            row['airport_code'],
            (row['avg_dep_delay'], row['delay_weighted_sentiment']),
            fontsize=7, alpha=0.7,
            xytext=(4, 4), textcoords='offset points'
        )

    if len(df) >= 3:
        z = np.polyfit(df['avg_dep_delay'], df['delay_weighted_sentiment'], 1)
        p = np.poly1d(z)
        x_line = np.linspace(df['avg_dep_delay'].min(), df['avg_dep_delay'].max(), 100)
        ax.plot(x_line, p(x_line), '--', color='#2c3e50', linewidth=1.5, alpha=0.6, zorder=2)

    r_pearson, p_pearson = pearsonr(df['avg_dep_delay'], df['delay_weighted_sentiment'])
    r_spearman, p_spearman = spearmanr(df['avg_dep_delay'], df['delay_weighted_sentiment'])

    stats_text = f"Correlazione = {r_pearson:.3f}"
    props = dict(boxstyle='round,pad=0.5', facecolor='white', alpha=0.9, edgecolor='gray')
    ax.text(0.97, 0.03, stats_text, transform=ax.transAxes,
            fontsize=10, verticalalignment='bottom', horizontalalignment='right',
            bbox=props)

    ax.set_xlabel('Average Departure Delay (min)', fontsize=12)
    ax.set_ylabel('Delay Weighted Sentiment (1-10)', fontsize=12)
    ax.set_title(
        'Average Delay vs Delay Sentiment — All Categories\n'
        '(colored by category)',
        fontsize=14, fontweight='bold', pad=15
    )
    ax.legend(title='Category', loc='upper right', framealpha=0.9)

    plt.tight_layout()
    fname = 'scatter_delay_vs_sentiment_all.png'
    fig.savefig(os.path.join(FIGURES_DIR, fname), dpi=300, bbox_inches='tight')
    plt.close(fig)
    print(f"  Saved: {fname}")


def plot_pressure_scatter_per_category(df_cat, cat_name, color):
    if len(df_cat) < 3:
        print(f"  {cat_name}: too few airports ({len(df_cat)}), skipping pressure scatter.")
        return

    sns.set_theme(style='whitegrid', context='talk')
    fig, ax = plt.subplots(figsize=(10, 8))

    ax.scatter(
        df_cat['avg_dep_delay'],
        df_cat['delay_reviews_count'],
        s=80,
        color=color,
        edgecolor='white',
        linewidth=0.6,
        alpha=0.75,
        zorder=3
    )

    for _, row in df_cat.iterrows():
        ax.annotate(
            row['airport_code'],
            (row['avg_dep_delay'], row['delay_reviews_count']),
            fontsize=8, alpha=0.85,
            xytext=(5, 5), textcoords='offset points'
        )

    if len(df_cat) >= 3:
        z = np.polyfit(df_cat['avg_dep_delay'], df_cat['delay_reviews_count'], 1)
        p = np.poly1d(z)
        x_line = np.linspace(df_cat['avg_dep_delay'].min(), df_cat['avg_dep_delay'].max(), 100)
        ax.plot(x_line, p(x_line), '--', color='#2c3e50', linewidth=1.5, alpha=0.7, zorder=2)

    r_pearson, p_pearson = pearsonr(df_cat['avg_dep_delay'], df_cat['delay_reviews_count'])

    stats_text = f"Correlazione = {r_pearson:.3f}"
    props = dict(boxstyle='round,pad=0.5', facecolor='white', alpha=0.9, edgecolor='gray')
    ax.text(0.97, 0.97, stats_text, transform=ax.transAxes,
            fontsize=10, verticalalignment='top', horizontalalignment='right',
            bbox=props)

    ax.set_xlabel('Average Departure Delay (min)', fontsize=12)
    ax.set_ylabel('Delay Reviews Count', fontsize=12)
    ax.set_title(
        f'Avg Delay vs Media Pressure (Delay Reviews) — {cat_name} Airports',
        fontsize=14, fontweight='bold', pad=15
    )

    plt.tight_layout()
    fname = f'scatter_delay_vs_pressure_{cat_name.lower()}.png'
    fig.savefig(os.path.join(FIGURES_DIR, fname), dpi=300, bbox_inches='tight')
    plt.close(fig)
    print(f"  Saved: {fname}")


def plot_pressure_combined_scatter(df, categories_data):
    sns.set_theme(style='whitegrid', context='talk')
    fig, ax = plt.subplots(figsize=(12, 9))

    for cat_name, df_cat in categories_data.items():
        if len(df_cat) < 2:
            continue
        color = CATEGORY_COLORS[cat_name]
        ax.scatter(
            df_cat['avg_dep_delay'],
            df_cat['delay_reviews_count'],
            s=70,
            color=color,
            edgecolor='white',
            linewidth=0.5,
            alpha=0.75,
            label=cat_name,
            zorder=3
        )

    for _, row in df.iterrows():
        ax.annotate(
            row['airport_code'],
            (row['avg_dep_delay'], row['delay_reviews_count']),
            fontsize=7, alpha=0.7,
            xytext=(4, 4), textcoords='offset points'
        )

    if len(df) >= 3:
        z = np.polyfit(df['avg_dep_delay'], df['delay_reviews_count'], 1)
        p = np.poly1d(z)
        x_line = np.linspace(df['avg_dep_delay'].min(), df['avg_dep_delay'].max(), 100)
        ax.plot(x_line, p(x_line), '--', color='#2c3e50', linewidth=1.5, alpha=0.6, zorder=2)

    r_pearson, p_pearson = pearsonr(df['avg_dep_delay'], df['delay_reviews_count'])

    stats_text = f"Correlazione = {r_pearson:.3f}"
    props = dict(boxstyle='round,pad=0.5', facecolor='white', alpha=0.9, edgecolor='gray')
    ax.text(0.97, 0.97, stats_text, transform=ax.transAxes,
            fontsize=10, verticalalignment='top', horizontalalignment='right',
            bbox=props)

    ax.set_xlabel('Average Departure Delay (min)', fontsize=12)
    ax.set_ylabel('Delay Reviews Count', fontsize=12)
    ax.set_title(
        'Average Delay vs Media Pressure (Delay Reviews) — All Categories\n'
        '(colored by category)',
        fontsize=14, fontweight='bold', pad=15
    )
    ax.legend(title='Category', loc='upper left', framealpha=0.9)

    plt.tight_layout()
    fname = 'scatter_delay_vs_pressure_all.png'
    fig.savefig(os.path.join(FIGURES_DIR, fname), dpi=300, bbox_inches='tight')
    plt.close(fig)
    print(f"  Saved: {fname}")


def main():
    if not os.path.exists(VOLUME_SUMMARY_PATH):
        print(f"ERROR: {VOLUME_SUMMARY_PATH} not found.")
        return
    if not os.path.exists(DELAYS_DATA_PATH):
        print(f"ERROR: {DELAYS_DATA_PATH} not found.")
        return

    df_volume = pd.read_csv(VOLUME_SUMMARY_PATH)
    df_delays = compute_airport_delays(DELAYS_DATA_PATH)

    df = df_volume.merge(df_delays, on='airport_code', how='inner')

    df = df.dropna(subset=['delay_weighted_sentiment', 'avg_dep_delay']).copy()
    df['delay_reviews_count'] = df['delay_reviews_count'].fillna(0)
    df['category'] = df['total_flights'].apply(classify_airport)

    print(f"\nMerged dataset: {len(df)} airports with both delay data and sentiment.\n")

    print("=" * 60)
    print("  PART 1: Avg Delay vs Delay Sentiment")
    print("=" * 60)

    summary_rows = []
    categories_data = {}

    for cat_name in ['Hub', 'Large', 'Medium', 'Small']:
        df_cat = df[df['category'] == cat_name].copy()
        if len(df_cat) < 3:
            print(f"  {cat_name}: only {len(df_cat)} airports, skipping correlation.")
            continue

        r_pearson, p_pearson = pearsonr(df_cat['avg_dep_delay'], df_cat['delay_weighted_sentiment'])
        r_spearman, p_spearman = spearmanr(df_cat['avg_dep_delay'], df_cat['delay_weighted_sentiment'])

        summary_rows.append({
            'category': cat_name,
            'n_airports': len(df_cat),
            'avg_delay_mean': round(df_cat['avg_dep_delay'].mean(), 2),
            'sentiment_mean': round(df_cat['delay_weighted_sentiment'].mean(), 3),
            'pearson_r': round(r_pearson, 4),
            'pearson_p': round(p_pearson, 6),
            'spearman_r': round(r_spearman, 4),
            'spearman_p': round(p_spearman, 6),
        })

        print(f"  {cat_name:8s}: n={len(df_cat):3d}  "
              f"Pearson r={r_pearson:+.3f} (p={p_pearson:.3e})  "
              f"Spearman r={r_spearman:+.3f} (p={p_spearman:.3e})")

        categories_data[cat_name] = df_cat
        plot_scatter_per_category(df_cat, cat_name, CATEGORY_COLORS[cat_name])

    r_all, p_all = pearsonr(df['avg_dep_delay'], df['delay_weighted_sentiment'])
    r_sp_all, p_sp_all = spearmanr(df['avg_dep_delay'], df['delay_weighted_sentiment'])
    summary_rows.append({
        'category': 'ALL',
        'n_airports': len(df),
        'avg_delay_mean': round(df['avg_dep_delay'].mean(), 2),
        'sentiment_mean': round(df['delay_weighted_sentiment'].mean(), 3),
        'pearson_r': round(r_all, 4),
        'pearson_p': round(p_all, 6),
        'spearman_r': round(r_sp_all, 4),
        'spearman_p': round(p_sp_all, 6),
    })
    print(f"\n  {'ALL':8s}: n={len(df):3d}  "
          f"Pearson r={r_all:+.3f} (p={p_all:.3e})  "
          f"Spearman r={r_sp_all:+.3f} (p={p_sp_all:.3e})")

    plot_combined_scatter(df, categories_data)

    df_summary = pd.DataFrame(summary_rows)
    summary_path = os.path.join(TABLES_DIR, 'correlation_delay_sentiment_by_category.csv')
    df_summary.to_csv(summary_path, index=False)
    print(f"\n  Saved correlation summary: {summary_path}")

    print("\n" + "=" * 60)
    print("  PART 2: Avg Delay vs Media Pressure (Delay Reviews Count)")
    print("=" * 60)

    df_pressure = df[df['delay_reviews_count'] > 0].copy()
    print(f"\n  Airports with delay reviews > 0: {len(df_pressure)}\n")

    pressure_rows = []
    pressure_categories = {}

    for cat_name in ['Hub', 'Large', 'Medium', 'Small']:
        df_cat = df_pressure[df_pressure['category'] == cat_name].copy()
        if len(df_cat) < 3:
            print(f"  {cat_name}: only {len(df_cat)} airports, skipping pressure correlation.")
            continue

        r_pearson, p_pearson = pearsonr(df_cat['avg_dep_delay'], df_cat['delay_reviews_count'])
        r_spearman, p_spearman = spearmanr(df_cat['avg_dep_delay'], df_cat['delay_reviews_count'])

        pressure_rows.append({
            'category': cat_name,
            'n_airports': len(df_cat),
            'avg_delay_mean': round(df_cat['avg_dep_delay'].mean(), 2),
            'avg_delay_reviews': round(df_cat['delay_reviews_count'].mean(), 1),
            'pearson_r': round(r_pearson, 4),
            'pearson_p': round(p_pearson, 6),
            'spearman_r': round(r_spearman, 4),
            'spearman_p': round(p_spearman, 6),
        })

        print(f"  {cat_name:8s}: n={len(df_cat):3d}  "
              f"Pearson r={r_pearson:+.3f} (p={p_pearson:.3e})  "
              f"Spearman r={r_spearman:+.3f} (p={p_spearman:.3e})")

        pressure_categories[cat_name] = df_cat
        plot_pressure_scatter_per_category(df_cat, cat_name, CATEGORY_COLORS[cat_name])

    r_all_p, p_all_p = pearsonr(df_pressure['avg_dep_delay'], df_pressure['delay_reviews_count'])
    r_sp_all_p, p_sp_all_p = spearmanr(df_pressure['avg_dep_delay'], df_pressure['delay_reviews_count'])
    pressure_rows.append({
        'category': 'ALL',
        'n_airports': len(df_pressure),
        'avg_delay_mean': round(df_pressure['avg_dep_delay'].mean(), 2),
        'avg_delay_reviews': round(df_pressure['delay_reviews_count'].mean(), 1),
        'pearson_r': round(r_all_p, 4),
        'pearson_p': round(p_all_p, 6),
        'spearman_r': round(r_sp_all_p, 4),
        'spearman_p': round(p_sp_all_p, 6),
    })
    print(f"\n  {'ALL':8s}: n={len(df_pressure):3d}  "
          f"Pearson r={r_all_p:+.3f} (p={p_all_p:.3e})  "
          f"Spearman r={r_sp_all_p:+.3f} (p={p_sp_all_p:.3e})")

    plot_pressure_combined_scatter(df_pressure, pressure_categories)

    df_pressure_summary = pd.DataFrame(pressure_rows)
    pressure_path = os.path.join(TABLES_DIR, 'correlation_delay_pressure_by_category.csv')
    df_pressure_summary.to_csv(pressure_path, index=False)
    print(f"\n  Saved pressure correlation summary: {pressure_path}")

    detail_cols = [
        'airport_code', 'name', 'category', 'total_flights',
        'avg_dep_delay', 'median_dep_delay', 'pct_delayed_15',
        'delay_weighted_sentiment', 'delay_reviews_count'
    ]
    existing_cols = [c for c in detail_cols if c in df.columns]
    df_detail = df[existing_cols].sort_values(['category', 'avg_dep_delay'], ascending=[True, False])
    detail_path = os.path.join(TABLES_DIR, 'airport_delay_vs_sentiment_detail.csv')
    df_detail.to_csv(detail_path, index=False)
    print(f"  Saved detail table: {detail_path}")

    print(f"\nAll done.")
    print(f"  Figures: {FIGURES_DIR}")
    print(f"  Tables:  {TABLES_DIR}")


if __name__ == '__main__':
    main()
