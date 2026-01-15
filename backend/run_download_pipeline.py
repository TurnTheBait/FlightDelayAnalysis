import subprocess
import os
import sys
import time

current_dir = os.path.dirname(os.path.abspath(__file__))


scripts = [
    "src/download/google_news_scraper.py",
    "src/download/meteostat_downloader.py",
    "src/download/reddit_scraper.py"
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
    print("INIZIO PIPELINE DI DOWNLOAD...")
    total_start = time.time()
    
    failed_scripts = []
    
    for script in scripts:
        success = run_script(script)
        if not success:
            failed_scripts.append(script)

            
    total_elapsed = time.time() - total_start
    print(f"\n{'='*60}")
    
    if failed_scripts:
        print(f"PIPELINE COMPLETATA CON ERRORI in {total_elapsed:.2f} secondi.")
        print("Script falliti:")
        for s in failed_scripts:
            print(f" - {s}")
    else:
        print(f"TUTTO FATTO! Pipeline di download completata in {total_elapsed:.2f} secondi.")
        
    print(f"{'='*60}")

if __name__ == "__main__":
    main()
