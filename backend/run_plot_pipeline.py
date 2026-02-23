import subprocess
import os
import sys
import time

current_dir = os.path.dirname(os.path.abspath(__file__))

scripts = [
    "src/analysis/summary.py",
    "src/analysis/flight_volume_analysis.py",
    "src/analysis/merge_weather_data.py",
    "src/analysis/sentiment_weather_correlation.py",
    "src/analysis/plot_results.py",
    "src/analysis/plot_results_delay.py",
    "src/analysis/plot_results_noise.py",
    "src/analysis/plot_volume_results.py",
    "src/analysis/population_sentiment_analysis.py",
    "src/analysis/plot_reliability_summary.py"
]

def run_script(script_path):
    full_path = os.path.join(current_dir, script_path)
    
    if not os.path.exists(full_path):
        print(f"ERRORE: Script non trovato: {full_path}")
        return False

    print(f"\n{'='*60}")
    print(f"AVVIO: {script_path}...")
    print(f"{'='*60}\n")
    
    start_time = time.time()
    
    try:
        result = subprocess.run([sys.executable, full_path], check=True)
        elapsed = time.time() - start_time
        print(f"\nCOMPLETATO: {script_path} in {elapsed:.2f} secondi.")
        return True
    except subprocess.CalledProcessError as e:
        print(f"\nFALLITO: {script_path} si è interrotto con errore.")
        return False

def main():
    print("INIZIO AUTOMAZIONE PIPELINE COMPLETA...")
    total_start = time.time()
    
    for script in scripts:
        success = run_script(script)
        if not success:
            print("\nPIPELINE INTERROTTA A CAUSA DI UN ERRORE.")
            sys.exit(1)
            
    total_elapsed = time.time() - total_start
    print(f"\n{'='*60}")
    print(f"TUTTO FATTO! Pipeline completata in {total_elapsed:.2f} secondi.")
    print(f"   Controlla la cartella 'results/figures' per il grafico.")
    print(f"{'='*60}")

if __name__ == "__main__":
    main()