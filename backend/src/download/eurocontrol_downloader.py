import os
import time
import logging
from datetime import datetime
from dateutil.relativedelta import relativedelta

import requests
from tqdm import tqdm

# ============================================================
# Setup logging
# ============================================================

logger = logging.getLogger("EurocontrolDownloader")
logger.setLevel(logging.INFO)

handler = logging.StreamHandler()
formatter = logging.Formatter("[%(asctime)s] [%(levelname)s] %(message)s")
handler.setFormatter(formatter)
logger.addHandler(handler)


# ============================================================
# URL Generator
# ============================================================

BASE_URL = "https://www.eurocontrol.int/performance/data/download/OPDI/v002"


def generate_urls(data_type: str, start_date: str, end_date: str) -> list:
    """
    Generate monthly Eurocontrol dataset URLs.

    Args:
        data_type (str): "flight_list", "flight_events", "measurements"
        start_date (str): "YYYYMM"
        end_date (str): "YYYYMM"

    Returns:
        list[str]
    """

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


# ============================================================
# File Downloader
# ============================================================

def download_file(url: str, save_path: str, retries: int = 3, timeout: int = 10):
    """
    Download a single file with retry logic and progress bar.

    Args:
        url (str)
        save_path (str)
        retries (int)
        timeout (int)
    """

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


# ============================================================
# Batch Downloader
# ============================================================

def download_range(
    data_type: str,
    start_date: str,
    end_date: str,
    save_folder: str = "backend/data/raw",
):
    """
    Download all monthly files for a given date range.

    Args:
        data_type (str)
        start_date (str)
        end_date (str)
        save_folder (str)
    """

    urls = generate_urls(data_type, start_date, end_date)

    logger.info(f"Found {len(urls)} files to download.")

    for url in urls:
        file_name = url.split("/")[-1]
        path = os.path.join(save_folder, file_name)

        if os.path.exists(path):
            logger.info(f"Skipping {file_name} (already exists)")
            continue

        download_file(url, path)


# ============================================================
# Script entrypoint
# ============================================================

if __name__ == "__main__":
    # Download flight lists 
    download_range(
        data_type="flight_list",
        start_date="202401",
        end_date="202412",
        save_folder="backend/data/raw/flights",
    )