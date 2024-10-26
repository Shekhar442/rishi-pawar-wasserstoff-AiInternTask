# pdf_processor_directory.py

import os
import PyPDF2
import pymongo
from datetime import datetime, timezone  # Added timezone

class MongoDBHandler:
    def __init__(self, uri, db_name):
        self.client = pymongo.MongoClient(uri)
        self.db = self.client[db_name]
        self.documents = self.db.documents

    def store_metadata(self, filename, text, keywords):
        doc = {
            "filename": filename,
            "summary": text[:500],
            "keywords": keywords,
            # Updated to use timezone-aware datetime
            "processed_time": datetime.now(timezone.utc),
            "status": "processed"
        }
        self.documents.update_one({"filename": filename}, {"$set": doc}, upsert=True)

class PDFProcessor:
    def __init__(self, mongo_handler, directory):
        self.mongo_handler = mongo_handler
        self.directory = directory

    def process_pdfs(self):
        for filename in os.listdir(self.directory):
            if filename.endswith('.pdf'):
                with open(os.path.join(self.directory, filename), 'rb') as file:
                    reader = PyPDF2.PdfReader(file)
                    text = " ".join(page.extract_text() for page in reader.pages)
                    keywords = self.extract_keywords(text)
                    self.mongo_handler.store_metadata(filename, text, keywords)

    def extract_keywords(self, text):
        words = text.split()
        return list(set(words[:10]))  # Example extraction logic

def main():
    mongo_handler = MongoDBHandler("mongodb://localhost:27017/", "pdf_manager")
    processor = PDFProcessor(mongo_handler, "pdf_downloads")
    processor.process_pdfs()

if __name__ == "__main__":
    main()
