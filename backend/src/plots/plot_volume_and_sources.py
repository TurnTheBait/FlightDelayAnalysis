import matplotlib.pyplot as plt
import seaborn as sns
import pandas as pd
import os

sns.set_theme(style="whitegrid")

def plot_volume_before_after(output_dir):
    data = {
        'Fase': ['Prima del Cleaning', 'Prima del Cleaning', 'Prima del Cleaning', 
                 'Dopo il Cleaning', 'Dopo il Cleaning', 'Dopo il Cleaning'],
        'Sorgente': ['Skytrax', 'Google News', 'Reddit', 'Skytrax', 'Google News', 'Reddit'],
        'Conteggio': [14251, 138008, 3899, 13868, 10256, 628]
    }
    
    df = pd.DataFrame(data)
    
    plt.figure(figsize=(10, 6))
    ax = sns.barplot(data=df, x='Fase', y='Conteggio', hue='Sorgente', palette='viridis')
    
    for p in ax.patches:
        height = p.get_height()
        if height > 0:
            ax.annotate(f'{int(height):,}', (p.get_x() + p.get_width() / 2., height),
                        ha='center', va='bottom', fontsize=10, xytext=(0, 5),
                        textcoords='offset points')
    
    plt.yscale('log')
    plt.title('Volume dei Dati: Prima vs Dopo il Cleaning (Scala Logaritmica)', fontsize=14, pad=15)
    plt.ylabel('Numero di Recensioni/Articoli (Log)', fontsize=12)
    plt.xlabel('Fase', fontsize=12)
    plt.legend(title='Sorgente Dati', title_fontsize='11', fontsize='10')
    plt.tight_layout()
    
    plt.savefig(os.path.join(output_dir, 'data_volume_before_after_cleaning.png'), dpi=300)
    plt.close()

def plot_source_ratio(output_dir):
    data_delay = [8041, 7341, 596]
    data_noise = [430, 3154, 39]
    labels = ['Skytrax', 'Google News', 'Reddit']
    colors = sns.color_palette('viridis', n_colors=3)
    
    fig, axes = plt.subplots(1, 2, figsize=(14, 6))
    
    axes[0].pie(data_delay, labels=labels, autopct='%1.1f%%', startangle=140, colors=colors, 
                wedgeprops={'edgecolor': 'white'})
    axes[0].set_title(f'Rapporto Fonti per Delay\n(Totale: {sum(data_delay):,})', fontsize=14)
    
    axes[1].pie(data_noise, labels=labels, autopct='%1.1f%%', startangle=140, colors=colors,
                wedgeprops={'edgecolor': 'white'})
    axes[1].set_title(f'Rapporto Fonti per Noise\n(Totale: {sum(data_noise):,})', fontsize=14)
    
    plt.tight_layout()
    plt.savefig(os.path.join(output_dir, 'data_sources_ratio.png'), dpi=300)
    plt.close()

def main():
    current_script_dir = os.path.dirname(os.path.abspath(__file__))
    backend_dir = os.path.dirname(os.path.dirname(current_script_dir))
    output_dir = os.path.join(backend_dir, 'results', 'figures', 'data_sources')
    
    os.makedirs(output_dir, exist_ok=True)
    
    print("Generazione grafico del volume...")
    plot_volume_before_after(output_dir)
    
    print("Generazione grafico del rapporto fonti...")
    plot_source_ratio(output_dir)
    
    print(f"Grafici generati con successo in: {output_dir}")

if __name__ == "__main__":
    main()
