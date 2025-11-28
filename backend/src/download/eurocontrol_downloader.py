import os
import time
import logging
from datetime import datetime
from dateutil.relativedelta import relativedelta

import requests
from tqdm import tqdm

CURRENT_FILE = os.path.abspath(__file__)
DOWNLOAD_DIR = os.path.dirname(CURRENT_FILE)
PROJECT_ROOT = os.path.abspath(os.path.join(DOWNLOAD_DIR, "..", ".."))
RAW_DATA_PATH = os.path.join(PROJECT_ROOT, "data", "raw")

logger = logging.getLogger("EurocontrolDownloader")
logger.setLevel(logging.INFO)

handler = logging.StreamHandler()
formatter = logging.Formatter("[%(asctime)s] [%(levelname)s] %(message)s")
handler.setFormatter(formatter)
logger.addHandler(handler)

BASE_URL = "https://www.eurocontrol.int/performance/data/download/OPDI/v002"

def generate_urls(data_type: str, start_date: str, end_date: str) -> list:

    start_dt = datetime.strptime(start_date, "%Y%m")
    end_dt = datetime.strptime(end_date, "%Y%m")
    delta = relativedelta(months=1)

    urls = []

    current = start_dt
    while current <= end_dt:
        yyyymm = current.strftime("%Y%m")
        url = f"{BASE_URL}/{data_type}/{data_type}_{yyyymm}.parquet"
        urls.append(url)
        current += delta

    return urls

def download_file(url: str, save_path: str, retries: int = 3, timeout: int = 10):

    for attempt in range(1, retries + 1):
        try:
            logger.info(f"Downloading: {url}")
            response = requests.get(url, stream=True, timeout=timeout)
            response.raise_for_status()

            total_size = int(response.headers.get("content-length", 0))

            os.makedirs(os.path.dirname(save_path), exist_ok=True)

            with open(save_path, "wb") as f, tqdm(
                total=total_size,
                unit="B",
                unit_scale=True,
                desc=f"{os.path.basename(save_path)}",
            ) as bar:
                for chunk in response.iter_content(chunk_size=4096):
                    if chunk:
                        f.write(chunk)
                        bar.update(len(chunk))

            logger.info(f"Saved → {save_path}")
            return True

        except Exception as e:
            logger.warning(f"Attempt {attempt}/{retries} failed for {url}: {e}")
            time.sleep(2)

    logger.error(f"❌ Failed to download after {retries} attempts: {url}")
    return False

def download_range(
    data_type: str,
    start_date: str,
    end_date: str,
    save_folder: str = "backend/data/raw",
):

    urls = generate_urls(data_type, start_date, end_date)

    logger.info(f"Found {len(urls)} files to download.")

    for url in urls:
        file_name = url.split("/")[-1]
        path = os.path.join(save_folder, file_name)

        if os.path.exists(path):
            logger.info(f"Skipping {file_name} (already exists)")
            continue

        download_file(url, path)

if __name__ == "__main__":

    download_range(
        data_type="flight_list",
        start_date="202301",
        end_date="202412",
        save_folder = os.path.join(RAW_DATA_PATH, "flights"),
    )