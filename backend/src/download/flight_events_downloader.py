import os
import time
import logging
from datetime import datetime, timedelta
import requests
from tqdm import tqdm
import pandas as pd

logging.basicConfig(
    level=logging.INFO,
    format="[%(asctime)s] [%(levelname)s] %(message)s",
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger("FlightEventsDownloader")

BASE_URL = "https://www.eurocontrol.int/performance/data/download/OPDI/v002/flight_events"
CURRENT_FILE = os.path.abspath(__file__)
DOWNLOAD_DIR = os.path.dirname(CURRENT_FILE)
PROJECT_ROOT = os.path.abspath(os.path.join(DOWNLOAD_DIR, "..", ".."))
RAW_DATA_PATH = os.path.join(PROJECT_ROOT, "data", "raw", "flight_events")

KEPT_EVENTS = [
    #"exit-parking_position",
    "take-off",
    "landing",
    #"entry-parking_position"
]

def generate_intervals(start_generation_date: str, target_start_date: str, target_end_date: str) -> list[tuple[str, str]]:
    """
    Generates 10-day intervals starting from start_generation_date.
    """
    gen_start = datetime.strptime(start_generation_date, "%Y%m%d")
    tgt_start = datetime.strptime(target_start_date, "%Y%m%d")
    tgt_end = datetime.strptime(target_end_date, "%Y%m%d")
    
    intervals = []
    current = gen_start
    
    while current < tgt_end:
        interval_start = current
        interval_end = current + timedelta(days=10)
        if interval_start < tgt_end and interval_end > tgt_start:
             intervals.append((interval_start.strftime("%Y%m%d"), interval_end.strftime("%Y%m%d")))
        current = interval_end
        if current > tgt_end:
            break

    return intervals

def instance_in_range(date: datetime, start: datetime, end: datetime) -> bool:
    return start <= date <= end

def download_file(url: str, save_path: str, retries: int = 3, timeout: int = 60):
    """
    Downloads a file, filters it for specific event types, and saves the result.
    """
    if os.path.exists(save_path):
        logger.info(f"Skipping {os.path.basename(save_path)} (already exists)")
        return True

    temp_path = save_path + ".temp"

    for attempt in range(1, retries + 1):
        try:
            logger.info(f"Downloading: {url}")
            response = requests.get(url, stream=True, timeout=timeout)
            response.raise_for_status()

            total_size = int(response.headers.get("content-length", 0))

            os.makedirs(os.path.dirname(save_path), exist_ok=True)

            with open(temp_path, "wb") as f, tqdm(
                total=total_size,
                unit="B",
                unit_scale=True,
                desc=f"Downloading {os.path.basename(save_path)}",
            ) as bar:
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)
                        bar.update(len(chunk))

            logger.info(f"Filtering {os.path.basename(save_path)}...")
            
            try:
                df = pd.read_parquet(temp_path)
                
                initial_len = len(df)
                df_filtered = df[df["type"].isin(KEPT_EVENTS)]
                
                cols_to_drop = ["source", "version"]
                df_filtered = df_filtered.drop(columns=[c for c in cols_to_drop if c in df_filtered.columns])
                
                final_len = len(df_filtered)
                
                logger.info(f"Filtered rows: {initial_len} -> {final_len} ({(final_len/initial_len)*100:.2f}%)")
                
                df_filtered.to_parquet(save_path, index=False)
                
                logger.info(f"Saved filtered file → {save_path}")
                
            finally:
                if os.path.exists(temp_path):
                    os.remove(temp_path)

            return True

        except Exception as e:
            logger.warning(f"Attempt {attempt}/{retries} failed for {url}: {e}")
            time.sleep(2)
            
            if os.path.exists(temp_path):
                os.remove(temp_path)
            if os.path.exists(save_path):
                os.remove(save_path)

    logger.error(f"❌ Failed to download/process after {retries} attempts: {url}")
    return False

def main():
    GEN_START = "20220101"
    TARGET_START = "20230101"
    TARGET_END = "20241231"
    
    logger.info(f"Generating intervals from {GEN_START}...")
    intervals = generate_intervals(GEN_START, TARGET_START, TARGET_END)
    
    logger.info(f"Found {len(intervals)} intervals for the period {TARGET_START} to {TARGET_END}.")
    
    for start_str, end_str in intervals:
        file_name = f"flight_events_{start_str}_{end_str}.parquet"
        url = f"{BASE_URL}/{file_name}"
        save_path = os.path.join(RAW_DATA_PATH, file_name)
        
        download_file(url, save_path)

if __name__ == "__main__":
    main()
