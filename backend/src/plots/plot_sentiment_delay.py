import pandas as pd
import matplotlib.pyplot as plt
import os
import numpy as np
from scipy.stats import pearsonr, spearmanr

BASE_DIR = '/Users/davidegirolamo/Programming/FlightDelayAnalysis/FlightDelayAnalysis/backend'
delays_file = os.path.join(BASE_DIR, 'data', 'processed', 'delays', 'delays_consolidated_filtered.csv')
sentiment_file = os.path.join(BASE_DIR, 'data', 'sentiment', 'sentiment_results_delay.csv')
output_plot = os.path.join(BASE_DIR, 'results', 'figures', 'delay', 'sentiment_delay_vs_delay.png')

print("Loading Delays...")
df_delays = pd.read_csv(delays_file, usecols=['OrigDate', 'MinLateDeparted', 'Cancelled'])
df_delays['OrigDate'] = pd.to_datetime(df_delays['OrigDate'])
df_delays['MinLateDeparted'] = pd.to_numeric(df_delays['MinLateDeparted'], errors='coerce').fillna(0)

print(f"Delays dates: {df_delays['OrigDate'].min().strftime('%Y-%m-%d')} to {df_delays['OrigDate'].max().strftime('%Y-%m-%d')}")

daily_delays = df_delays.groupby('OrigDate')['MinLateDeparted'].mean().reset_index()
daily_delays.columns = ['date', 'avg_delay']

print("Loading Sentiment...")
df_sent = pd.read_csv(sentiment_file, usecols=['date', 'combined_score'])
df_sent['date'] = pd.to_datetime(df_sent['date'], errors='coerce', utc=True).dt.tz_localize(None).dt.normalize()
df_sent.dropna(subset=['date', 'combined_score'], inplace=True)

print(f"Sentiment dates: {df_sent['date'].min().strftime('%Y-%m-%d')} to {df_sent['date'].max().strftime('%Y-%m-%d')}")

daily_sent = df_sent.groupby('date')['combined_score'].mean().reset_index()
daily_sent.columns = ['date', 'avg_sentiment']

print("Aligning data (0-3 days review delay)...")
date_range = pd.date_range(start=min(daily_delays['date'].min(), daily_sent['date'].min()), 
                           end=max(daily_delays['date'].max(), daily_sent['date'].max()))
df_all = pd.DataFrame({'date': date_range})
df_all = df_all.merge(daily_delays, on='date', how='left')
df_all = df_all.merge(daily_sent, on='date', how='left')

df_all['sentiment_T_to_T3'] = df_all['avg_sentiment'].iloc[::-1].rolling(window=4, min_periods=1).mean().iloc[::-1]

df_merged = df_all.dropna(subset=['avg_delay', 'sentiment_T_to_T3']).copy()
df_merged = df_merged.sort_values('date')

corr_pearson, p_pearson = pearsonr(df_merged['avg_delay'], df_merged['sentiment_T_to_T3'])
corr_spearman, p_spearman = spearmanr(df_merged['avg_delay'], df_merged['sentiment_T_to_T3'])

print(f"--- CORRELATION STATISTICS ---")
print(f"Data Points: {len(df_merged)}")
print(f"Pearson Correlation:  {corr_pearson:.3f} (p-value: {p_pearson:.3e})")
print(f"Spearman Correlation: {corr_spearman:.3f} (p-value: {p_spearman:.3e})")

print("Generating Plot...")
fig, ax1 = plt.subplots(figsize=(12, 6))

color1 = '#E63946' 
ax1.set_xlabel('Data Volo', fontsize=12)
ax1.set_ylabel('Ritardo Medio Partenza (min)', color=color1, fontsize=12)
delay_smooth = df_merged['avg_delay'].rolling(14, min_periods=1).mean()
ax1.plot(df_merged['date'], delay_smooth, color=color1, label='Ritardi', linewidth=2)
ax1.tick_params(axis='y', labelcolor=color1)
ax1.grid(True, alpha=0.3)

ax2 = ax1.twinx()  
color2 = '#1D3557' 
ax2.set_ylabel('Sentiment Delay (Scala 1-10, Val. Bassi = Negativo)', color=color2, fontsize=12)  
sent_smooth = df_merged['sentiment_T_to_T3'].rolling(14, min_periods=1).mean()
ax2.plot(df_merged['date'], sent_smooth, color=color2, label='Sentiment Forward 0-3g', linewidth=2)
ax2.tick_params(axis='y', labelcolor=color2)

fig.autofmt_xdate()
plt.title('Ritardo dei Voli vs Sentiment Delay\n(Considerando le recensioni da 0 a 3 giorni successivi al volo)', fontsize=14, pad=15)

lines1, labels1 = ax1.get_legend_handles_labels()
lines2, labels2 = ax2.get_legend_handles_labels()
ax1.legend(lines1 + lines2, labels1 + labels2, loc='upper left')

textstr = f"Correlazione: {corr_pearson:.3f}"
props = dict(boxstyle='round', facecolor='white', alpha=0.9, edgecolor='gray')
ax1.text(0.98, 0.95, textstr, transform=ax1.transAxes, fontsize=11,
         verticalalignment='top', horizontalalignment='right', bbox=props)

os.makedirs(os.path.dirname(output_plot), exist_ok=True)
plt.savefig(output_plot, dpi=300, bbox_inches='tight')

print(f"Plot saved to: {output_plot}")
