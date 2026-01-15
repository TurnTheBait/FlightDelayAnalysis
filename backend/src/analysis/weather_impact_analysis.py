import pandas as pd
import matplotlib.pyplot as plt
from pathlib import Path
import numpy as np

def analyze_weather_impact(input_file, output_dir):
    print(f"Loading data from {input_file}...")
    df = pd.read_csv(input_file, low_memory=False)
    
    Path(output_dir).mkdir(parents=True, exist_ok=True)
    
    print("Preparing data...")
    weather_cols = ['Dep_temp', 'Dep_wspd', 'Dep_prcp', 'Arr_temp', 'Arr_wspd', 'Arr_prcp']
    df_clean = df.dropna(subset=weather_cols + ['MinLateDeparted', 'MinLateArrived'])
    
    print("Generating correlation matrix...")
    corr_cols = [
        'MinLateDeparted', 'MinLateArrived',
        'Dep_temp', 'Dep_wspd', 'Dep_prcp', 'Dep_pres',
        'Arr_temp', 'Arr_wspd', 'Arr_prcp', 'Arr_pres'
    ]
    valid_corr_cols = [c for c in corr_cols if c in df_clean.columns]
    
    correlation = df_clean[valid_corr_cols].corr()
    
    fig, ax = plt.subplots(figsize=(10, 8))
    cax = ax.matshow(correlation, cmap='coolwarm', vmin=-1, vmax=1)
    fig.colorbar(cax)
    
    ax.set_xticks(np.arange(len(valid_corr_cols)))
    ax.set_yticks(np.arange(len(valid_corr_cols)))
    ax.set_xticklabels(valid_corr_cols, rotation=45, ha="left")
    ax.set_yticklabels(valid_corr_cols)
    
    for i in range(len(valid_corr_cols)):
        for j in range(len(valid_corr_cols)):
            ax.text(j, i, f"{correlation.iloc[i, j]:.2f}", ha='center', va='center', color='black')
            
    plt.title('Correlation Matrix: Delays vs Weather')
    plt.tight_layout()
    plt.savefig(f"{output_dir}/correlation_matrix.png")
    plt.close()

    print("Generating Wind vs Delay plot...")
    plt.figure(figsize=(10, 6))
    sample_df = df_clean.sample(min(10000, len(df_clean)), random_state=42)
    plt.scatter(sample_df['Dep_wspd'], sample_df['MinLateDeparted'], alpha=0.3, color='blue', s=10)
    
    m, b = np.polyfit(sample_df['Dep_wspd'], sample_df['MinLateDeparted'], 1)
    plt.plot(sample_df['Dep_wspd'], m*sample_df['Dep_wspd'] + b, color='red')
    
    plt.title('Departure Wind Speed vs Departure Delay (Sampled)')
    plt.xlabel('Wind Speed (km/h)')
    plt.ylabel('Departure Delay (min)')
    plt.tight_layout()
    plt.savefig(f"{output_dir}/wind_vs_delay.png")
    plt.close()

    print("Analyzing airport performance...")
    adverse_weather_mask = (df_clean['Dep_wspd'] > 20) | (df_clean['Dep_prcp'] > 0.1)
    adverse_df = df_clean[adverse_weather_mask]
    
    top_airports = adverse_df['SchedDepApt'].value_counts().nlargest(20).index
    avg_delay_adverse = adverse_df[adverse_df['SchedDepApt'].isin(top_airports)].groupby('SchedDepApt')['MinLateDeparted'].mean().sort_values()
    
    plt.figure(figsize=(12, 8))
    plt.bar(avg_delay_adverse.index, avg_delay_adverse.values, color='skyblue')
    plt.title('Average Departure Delay under Adverse Weather (Top 20 Airports)')
    plt.xlabel('Airport')
    plt.ylabel('Avg Delay (min)')
    plt.xticks(rotation=45)
    plt.tight_layout()
    plt.savefig(f"{output_dir}/airport_performance_adverse_weather.png")
    plt.close()

    print(f"Analysis complete. Figures saved to {output_dir}")

if __name__ == "__main__":
    BASE_DIR = Path(__file__).resolve().parents[3]
    INPUT_FILE = BASE_DIR / "backend" / "data" / "merged" / "flights_with_weather.csv"
    OUTPUT_DIR = BASE_DIR / "backend" / "results" / "figures"
    
    analyze_weather_impact(INPUT_FILE, OUTPUT_DIR)
