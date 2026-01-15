import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt
import os

current_script_dir = os.path.dirname(os.path.abspath(__file__))
backend_dir = os.path.dirname(os.path.dirname(current_script_dir))
INPUT_FILE = os.path.join(backend_dir, 'data', 'sentiment', 'sentiment_scored.csv')
OUTPUT_IMG = os.path.join(backend_dir, 'results', 'figures', 'sentiment_overview.png')

if not os.path.exists(INPUT_FILE):
    print("Error: Sentiment file not found.")
    exit()

df = pd.read_csv(INPUT_FILE)

agg_data = df.groupby('city')['stars_score'].agg(['mean', 'count']).reset_index()
agg_data = agg_data.sort_values('mean', ascending=False)

plt.figure(figsize=(12, 8))
sns.set_theme(style="whitegrid")

norm = plt.Normalize(1, 5)
colors = plt.cm.RdYlGn(norm(agg_data['mean']))

ax = sns.barplot(x='mean', y='city', data=agg_data, palette=colors, edgecolor='black')

plt.title('Sentiment Analysis: Airport Perception Ranking', fontsize=16, weight='bold')
plt.xlabel('Average Sentiment Score (1=Bad, 5=Good)', fontsize=12)
plt.ylabel('', fontsize=12)
plt.axvline(x=3, color='black', linestyle='--', linewidth=1, label='Neutral Threshold')
plt.xlim(0, 5.5)

for i, row in enumerate(agg_data.itertuples()):
    label = f"{row.mean:.1f} (n={row.count})"
    ax.text(row.mean + 0.05, i, label, va='center', fontsize=10, color='black', weight='bold')

plt.legend(loc='lower right')
plt.tight_layout()

os.makedirs(os.path.dirname(OUTPUT_IMG), exist_ok=True)
plt.savefig(OUTPUT_IMG, dpi=300)

print(f"Plot saved to: {OUTPUT_IMG}")
plt.show()