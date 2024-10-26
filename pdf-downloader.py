import json
import os
import requests
import time
import urllib3
from urllib3.exceptions import InsecureRequestWarning

# Suppress only the single warning from urllib3 needed.
urllib3.disable_warnings(InsecureRequestWarning)

def create_download_directory(directory):
    """Create directory if it doesn't exist"""
    if not os.path.exists(directory):
        os.makedirs(directory)

def download_pdf(url, filename, download_dir, verify_ssl=True):
    """Download PDF file with error handling and retry mechanism"""
    max_retries = 3
    retry_delay = 2  # seconds
    
    for attempt in range(max_retries):
        try:
            # First try with SSL verification
            if verify_ssl or attempt < max_retries - 1:
                response = requests.get(url, stream=True, timeout=30)
            else:
                # On last attempt, try without SSL verification if previous attempts failed
                response = requests.get(url, stream=True, timeout=30, verify=False)
            
            response.raise_for_status()
            
            # Verify content type is PDF
            content_type = response.headers.get('content-type', '').lower()
            if 'pdf' not in content_type and attempt == max_retries - 1:
                print(f"Warning: Content-Type is not PDF for {filename}")
            
            # Save the file
            file_path = os.path.join(download_dir, filename)
            with open(file_path, 'wb') as file:
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        file.write(chunk)
            
            print(f"Successfully downloaded: {filename}")
            return True
            
        except requests.exceptions.SSLError as e:
            if attempt < max_retries - 1:
                print(f"SSL Error on attempt {attempt + 1} for {filename}. Retrying in {retry_delay} seconds...")
                time.sleep(retry_delay)
            elif attempt == max_retries - 1:
                # On last attempt, try without SSL verification
                print(f"Attempting download without SSL verification for {filename}...")
                continue
            else:
                print(f"Failed to download {filename} after {max_retries} attempts: SSL Error")
                return False
                
        except requests.exceptions.RequestException as e:
            if attempt < max_retries - 1:
                print(f"Attempt {attempt + 1} failed for {filename}. Retrying in {retry_delay} seconds...")
                time.sleep(retry_delay)
            else:
                print(f"Failed to download {filename} after {max_retries} attempts: {str(e)}")
                return False

def main():
    # Configuration
    json_file = 'Dataset.json'
    download_dir = 'pdf_downloads'
    
    # Create download directory
    create_download_directory(download_dir)
    
    # Read JSON file
    try:
        with open(json_file, 'r') as file:
            data = json.load(file)
    except Exception as e:
        print(f"Error reading JSON file: {str(e)}")
        return
    
    # Sort the items by pdf number to ensure sequential processing
    sorted_items = sorted(data.items(), key=lambda x: int(x[0].replace('pdf', '')))
    
    # Download each PDF
    total_files = len(sorted_items)
    for index, (pdf_id, url) in enumerate(sorted_items, 1):
        # Generate filename with padded numbers (pdf01.pdf, pdf02.pdf, etc.)
        filename = f"pdf{index:02d}.pdf"
        
        print(f"\nProcessing {filename} ({index}/{total_files})...")
        
        # Special handling for known problematic domains
        verify_ssl = not ('ijtr.nic.in' in url)  # Disable SSL verification for problematic domain
        
        # Download the PDF
        success = download_pdf(url, filename, download_dir, verify_ssl=verify_ssl)
        
        if success:
            print(f"✓ {filename} saved successfully")
        else:
            print(f"✗ Failed to download {filename}")
        
        # Add a small delay between downloads to be polite to servers
        time.sleep(1)
    
    print("\nDownload process completed!")

if __name__ == "__main__":
    main()