import os
import pandas as pd
import logging
from tqdm import tqdm

logging.basicConfig(
    level=logging.INFO,
    format="[%(asctime)s] [%(levelname)s] %(message)s",
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger("EventTypesExtractor")

CURRENT_FILE = os.path.abspath(__file__)
PREPROCESS_DIR = os.path.dirname(CURRENT_FILE)
PROJECT_ROOT = os.path.abspath(os.path.join(PREPROCESS_DIR, "..", ".."))
RAW_DATA_PATH = os.path.join(PROJECT_ROOT, "data", "raw", "flight_events")
OUTPUT_FILE = os.path.join(RAW_DATA_PATH, "event_types.txt")

def extract_event_types():
    event_types = set()
    
    if not os.path.exists(RAW_DATA_PATH):
        logger.error(f"Directory not found: {RAW_DATA_PATH}")
        return

    files = [f for f in os.listdir(RAW_DATA_PATH) if f.endswith(".parquet")]
    
    if not files:
        logger.warning("No parquet files found to processing.")
        return

    logger.info(f"Found {len(files)} parquet files. Starting extraction...")

    for file_name in tqdm(files, desc="Processing Files"):
        file_path = os.path.join(RAW_DATA_PATH, file_name)
        try:
            df = pd.read_parquet(file_path, columns=["type"])
            unique_types = df["type"].dropna().unique()
            event_types.update(unique_types)
            
        except Exception as e:
            logger.error(f"Error processing {file_name}: {e}")

    sorted_event_types = sorted(list(event_types))
    
    logger.info(f"Extraction complete. Found {len(sorted_event_types)} unique event types.")
    
    try:
        with open(OUTPUT_FILE, "w") as f:
            for et in sorted_event_types:
                f.write(f"{et}\n")
        logger.info(f"Saved event types to: {OUTPUT_FILE}")
        
        print("\n=== Event Types ===")
        for et in sorted_event_types:
            print(et)
        print("===================")
        
    except Exception as e:
        logger.error(f"Error saving to file: {e}")

if __name__ == "__main__":
    extract_event_types()
