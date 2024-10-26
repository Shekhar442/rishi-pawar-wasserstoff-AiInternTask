# rishi-pawar-wasserstoff-AiInternTask
# PDF Processing System

A comprehensive system for downloading, processing, and analyzing PDF documents with MongoDB integration and structured storage.

## Overview

This system consists of two main components:
1. PDF Downloader (`pdf-downloader.py`) - Downloads PDFs from URLs with retry mechanisms
2. PDF Processor (`pdf-processor-directory.py`) - Processes PDFs and stores results in MongoDB

## Prerequisites

### System Requirements
- Python 3.8+
- MongoDB 4.4+ running locally
- Sufficient disk space for PDFs and processed data

### Python Dependencies
```bash
pip install requests PyPDF2 pymongo urllib3
```

### Directory Structure
```
project_root/
├── pdf_downloads/      # Downloaded PDFs
├── pdf_analysis/       # Processed results
│   ├── processed/      # Successfully processed PDFs
│   ├── failed/        # Failed PDFs
│   ├── summaries/     # JSON summaries
│   ├── metadata/      # Processing metadata
│   └── logs/         # Processing logs
└── Dataset.json       # Input URLs file
```

## Components

### 1. PDF Downloader (pdf-downloader.py)

Downloads PDFs from URLs specified in Dataset.json.

#### Features:
- Automatic retry mechanism (3 attempts)
- SSL verification handling
- Progress tracking
- Polite delay between downloads
- Sequential file naming (pdf01.pdf, pdf02.pdf, etc.)

#### Usage:
```bash
python pdf-downloader.py
```

#### Input Format (Dataset.json):
```json
{
    "pdf1": "http://example.com/file1.pdf",
    "pdf2": "http://example.com/file2.pdf"
}
```

### 2. PDF Processor (pdf-processor-directory.py)

Processes downloaded PDFs and stores results in MongoDB.

#### Features:
- Text extraction
- Keyword identification
- MongoDB integration
- Error handling and recovery
- Processing statistics
- Versioning support

#### Usage:
```bash
python pdf-processor-directory.py
```

## Setup and Running

1. Create required directories:
```bash
mkdir pdf_downloads pdf_analysis
```

2. Start MongoDB:
```bash
mongod
```

3. Run the downloader:
```bash
python pdf-downloader.py
```

4. Run the processor:
```bash
python pdf-processor-directory.py
```

## MongoDB Collections

- `documents`: Main document storage
- `processing_status`: Processing status tracking
- `errors`: Error logging and tracking

## Error Handling

### Downloader:
- SSL verification failures
- Network timeouts
- Invalid URLs
- Non-PDF content

### Processor:
- Corrupt PDFs
- Text extraction failures
- MongoDB connection issues
- Processing failures

## Output

### JSON Structure:
```json
{
    "filename": "pdf01.pdf",
    "summary": "...",
    "keywords": [
        {"word": "example", "frequency": 10}
    ],
    "metadata": {
        "page_count": 5,
        "text_length": 1000,
        "processed_time": "2024-10-26T10:00:00Z"
    }
}
```

## Monitoring

- Check logs in pdf_analysis/logs/
- Monitor MongoDB collections for processing status
- View processing statistics in console output

## Best Practices

1. Keep MongoDB running during processing
2. Monitor disk space for downloaded PDFs
3. Check logs regularly for errors
4. Back up Dataset.json before processing
5. Ensure proper network connectivity

## Troubleshooting

1. If downloads fail:
   - Check network connection
   - Verify URLs in Dataset.json
   - Check SSL certificates

2. If processing fails:
   - Check MongoDB connection
   - Verify PDF file integrity
   - Check available disk space
   - Review error logs

## Maintenance

1. Regular cleanup:
```bash
# Remove temporary files
rm -rf pdf_analysis/logs/*
```

2. MongoDB maintenance:
```bash
# Compact database
mongosh
db.runCommand({compact: 'documents'})
```

## Support

For issues and questions:
1. Check the logs in pdf_analysis/logs/
2. Review MongoDB error collection
3. Verify system prerequisites
4. Check network connectivity