# pdf_downloader.py

import json
import os
import requests
import time
from urllib3.exceptions import InsecureRequestWarning
import urllib3

# Disable SSL warnings
urllib3.disable_warnings(InsecureRequestWarning)

def create_download_directory(directory):
    if not os.path.exists(directory):
        os.makedirs(directory)

def download_pdf(url, filename, download_dir):
    for attempt in range(3):
        try:
            # Set verify=False to ignore SSL certificate verification
            response = requests.get(url, stream=True, timeout=30, verify=False)
            response.raise_for_status()
            with open(os.path.join(download_dir, filename), 'wb') as file:
                for chunk in response.iter_content(chunk_size=8192):
                    file.write(chunk)
            print(f"Downloaded: {filename}")
            return True
        except requests.exceptions.RequestException as e:
            print(f"Attempt {attempt + 1} failed for {filename}. Error: {e}")
            time.sleep(2)
    print(f"Failed to download: {filename}")
    return False

def main():
    with open('Dataset.json') as f:
        data = json.load(f)

    create_download_directory('pdf_downloads')
    for pdf_id, url in data.items():
        filename = f"{pdf_id}.pdf"
        download_pdf(url, filename, 'pdf_downloads')

if __name__ == "__main__":
    main()
