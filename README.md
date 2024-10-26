# PDF Processing and Management Web Application

This application is a Flask-based web interface for managing, processing, and displaying metadata for PDFs. It downloads PDFs from URLs specified in a JSON file, extracts metadata and keywords, stores the processed information in a MongoDB database, and provides a user-friendly web interface to filter and download the PDFs.

## Table of Contents
- [Features](#features)
- [Directory Structure](#directory-structure)
- [Requirements](#requirements)
- [Setup](#setup)
- [Usage](#usage)
- [File Descriptions](#file-descriptions)
- [Troubleshooting](#troubleshooting)
- [License](#license)

## Features
- **Download PDFs** from URLs listed in a JSON file
- **Extract Metadata** such as summary and keywords
- **Store Metadata in MongoDB** for easy querying
- **Flask Web Interface** to filter by keywords and status, display metadata, and download PDFs

## Directory Structure
```
├── Dataset.json                # JSON file containing PDF URLs
├── pdf_downloads/             # Directory for downloaded PDFs
├── pdf_downloader.py          # Script to download PDFs from URLs
├── pdf_processor_directory.py # Script to process PDFs and store metadata
├── templates/
│   └── index.html            # HTML template for displaying PDFs in the web interface
└── app.py                    # Flask application for the web interface
```

## Requirements
- Python 3.x
- MongoDB
- Python libraries:
  - `Flask`
  - `pymongo`
  - `requests`
  - `PyPDF2`

Install the dependencies with:
```bash
pip install Flask pymongo requests PyPDF2
```

## Setup
1. **Download PDFs**: Run the `pdf_downloader.py` script to download PDFs from URLs listed in `Dataset.json`:
   ```bash
   python pdf_downloader.py
   ```

2. **Process PDFs and Store Metadata**: Run `pdf_processor_directory.py` to extract metadata and store it in MongoDB:
   ```bash
   python pdf_processor_directory.py
   ```

3. **Start the Flask Web Application**: Run the `app.py` file to start the Flask server:
   ```bash
   python app.py
   ```

Access the app at `http://127.0.0.1:5000` in your browser.

## Usage
1. **Filter PDFs**: Use the form at the top of the page to filter PDFs by keyword or status (`processed`)
2. **View Metadata**: View each PDF's filename, summary, keywords, and download link
3. **Download PDFs**: Click the download link to download any processed PDF directly

## File Descriptions
- **Dataset.json**: JSON file containing a dictionary of PDF URLs (e.g., `{"pdf1": "http://example.com/sample.pdf"}`)
- **pdf_downloader.py**: Script to download PDFs with SSL warnings disabled and retry logic
- **pdf_processor_directory.py**: Script that extracts text and keywords, stores them in MongoDB with a processing status
- **templates/index.html**: HTML file for rendering PDF metadata and download links on the web interface
- **app.py**: Main Flask application for displaying and managing PDFs on the web interface

## Troubleshooting
- **SSL Issues**: `pdf_downloader.py` has SSL warnings disabled. Check network and URL validity if downloads fail
- **Database Connection**: Ensure MongoDB is running and accessible at `mongodb://localhost:27017/`
- **Filtering**: Keywords and status fields are case-insensitive and exact match. Ensure metadata fields exist in MongoDB

## License
This project is open-source and available under the MIT License.
