import pandas as pd
import os
import matplotlib.pyplot as plt
import seaborn as sns

CURRENT_FILE = os.path.abspath(__file__)
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(CURRENT_FILE)))
SENTIMENT_DIR = os.path.join(BASE_DIR, 'data', 'sentiment')
PLOTS_DIR = os.path.join(BASE_DIR, 'results', 'figures', 'model_comparison')

os.makedirs(PLOTS_DIR, exist_ok=True)

def plot_model_comparison(file_name, mode_name):
    file_path = os.path.join(SENTIMENT_DIR, file_name)
    
    if not os.path.exists(file_path):
        print(f"[WARNING] File non trovato: {file_path}")
        return
        
    print(f"Elaborazione dati per la modalità: {mode_name}...")
    df = pd.read_csv(file_path)
    
    if 'model_a_score' not in df.columns or 'model_b_score' not in df.columns:
        print(f"[ERROR] Colonne dei modelli mancanti nel file {file_name}")
        return

    df['score_diff'] = df['model_a_score'] - df['model_b_score']
    
    sns.set_theme(style="whitegrid")
    
    plt.figure(figsize=(10, 8))
    sns.scatterplot(data=df, x='model_a_score', y='model_b_score', alpha=0.3)
    plt.plot([0, 10], [0, 10], 'r--', lw=2, label="Parità assoluta (x=y)")
    plt.title(f'Confronto Modelli di Sentiment - {mode_name.capitalize()}')
    plt.xlabel('Model A Score (BERT Multi)')
    plt.ylabel('Model B Score (RoBERTa Twitter)')
    plt.legend()
    plt.tight_layout()
    plt.savefig(os.path.join(PLOTS_DIR, f'scatter_{mode_name}.png'), dpi=300)
    plt.close()
    
    plt.figure(figsize=(10, 6))
    sns.histplot(df['score_diff'], kde=True, bins=50, color='purple')
    plt.axvline(0, color='red', linestyle='--', linewidth=2)
    plt.title(f'Distribuzione della Differenza (Mod. A - Mod. B) - {mode_name.capitalize()}')
    plt.xlabel('Differenza di Punteggio')
    plt.ylabel('Frequenza')
    plt.tight_layout()
    plt.savefig(os.path.join(PLOTS_DIR, f'diff_dist_{mode_name}.png'), dpi=300)
    plt.close()

    plt.figure(figsize=(10, 6))
    sns.kdeplot(df['model_a_score'], fill=True, label='Model A (BERT)', alpha=0.5)
    sns.kdeplot(df['model_b_score'], fill=True, label='Model B (RoBERTa)', alpha=0.5)
    plt.title(f'Confronto Distribuzioni di Punteggio - {mode_name.capitalize()}')
    plt.xlabel('Sentiment Score (1.0 - 10.0)')
    plt.ylabel('Densità')
    plt.legend()
    plt.tight_layout()
    plt.savefig(os.path.join(PLOTS_DIR, f'kde_{mode_name}.png'), dpi=300)
    plt.close()
    
    mae = df['score_diff'].abs().mean()
    corr = df['model_a_score'].corr(df['model_b_score'])
    mean_diff = df['score_diff'].mean()
    
    print(f"Statistiche {mode_name}:")
    print(f"- Correlazione Pearson: {corr:.3f}")
    print(f"- Errore Medio Assoluto (MAE): {mae:.3f}")
    print(f"- Differenza Media (A - B): {mean_diff:.3f}")
    print("-" * 50)

def main():
    print("Inizio analisi comparativa dei modelli di sentiment...\n")
    modes = {
        "general": "sentiment_results_raw_general.csv",
        "delay": "sentiment_results_raw_delay.csv",
        "noise": "sentiment_results_raw_noise.csv"
    }
    
    for mode, file_name in modes.items():
        plot_model_comparison(file_name, mode)
        
    print(f"Tutti i grafici sono stati generati nella cartella: {PLOTS_DIR}")

if __name__ == "__main__":
    main()
