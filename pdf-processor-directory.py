import os
import PyPDF2
import json
import logging
from datetime import datetime, timezone
from typing import Dict, List, Any, Optional
import pymongo
from pymongo import MongoClient, UpdateOne, IndexModel
from pymongo.errors import PyMongoError, BulkWriteError
from bson import ObjectId
import hashlib
from concurrent.futures import ThreadPoolExecutor
from functools import lru_cache

class MongoDBHandler:
    """Handles all MongoDB operations with proper error handling and logging."""
    
    def __init__(self, mongo_uri: str, db_name: str):
        """Initialize MongoDB connection and setup collections."""
        try:
            self.client = MongoClient(
                mongo_uri,
                serverSelectionTimeoutMS=5000,
                retryWrites=True,
                retryReads=True
            )
            
            # Test connection
            self.client.admin.command('ping')
            
            self.db = self.client[db_name]
            
            # Initialize collections
            self.documents = self.db.documents
            self.processing_status = self.db.processing_status
            self.errors = self.db.errors
            
            # Setup indexes
            self._setup_indexes()
            
            logging.info("Successfully connected to MongoDB")
        except PyMongoError as e:
            logging.error(f"MongoDB initialization error: {str(e)}")
            raise

    def _setup_indexes(self):
        """Setup MongoDB indexes for optimal performance."""
        try:
            # Create indexes for documents collection
            document_indexes = [
                IndexModel([("filename", pymongo.ASCENDING)], unique=True),
                IndexModel([("file_hash", pymongo.ASCENDING)]),
                IndexModel([("status", pymongo.ASCENDING)]),
                IndexModel([("last_updated", pymongo.ASCENDING)]),
                IndexModel([("processing_status", pymongo.ASCENDING)])
            ]
            self.documents.create_indexes(document_indexes)
            
            status_indexes = [
                IndexModel([("filename", pymongo.ASCENDING)], unique=True),
                IndexModel([("status", pymongo.ASCENDING)]),
                IndexModel([("timestamp", pymongo.ASCENDING)])
            ]
            self.processing_status.create_indexes(status_indexes)
            
            error_indexes = [
                IndexModel([("filename", pymongo.ASCENDING)]),
                IndexModel([("timestamp", pymongo.ASCENDING)]),
                IndexModel([("error_type", pymongo.ASCENDING)])
            ]
            self.errors.create_indexes(error_indexes)
            
            logging.info("MongoDB indexes created successfully")
        except PyMongoError as e:
            logging.error(f"Error creating MongoDB indexes: {str(e)}")
            raise

    def store_initial_metadata(self, filename: str, file_path: str) -> ObjectId:
        """Store initial document metadata with recovery mechanisms."""
        try:
            # Calculate file hash and size
            with open(file_path, 'rb') as f:
                content = f.read()
                file_hash = hashlib.sha256(content).hexdigest()
                file_size = len(content)

            metadata = {
                "filename": filename,
                "file_hash": file_hash,
                "file_size": file_size,
                "file_path": file_path,
                "upload_date": datetime.now(timezone.utc),
                "status": "pending",
                "processing_status": {
                    "stage": "initial",
                    "attempts": 0,
                    "last_attempt": datetime.now(timezone.utc)
                },
                "last_updated": datetime.now(timezone.utc)
            }
            
            # Use upsert to handle potential duplicates
            result = self.documents.update_one(
                {"filename": filename},
                {"$setOnInsert": metadata},
                upsert=True
            )
            
            # Track processing status
            self.processing_status.update_one(
                {"filename": filename},
                {
                    "$set": {
                        "status": "pending",
                        "timestamp": datetime.now(timezone.utc)
                    }
                },
                upsert=True
            )
            
            doc_id = result.upserted_id or self.documents.find_one({"filename": filename})["_id"]
            logging.info(f"Stored initial metadata for {filename}")
            return doc_id
            
        except Exception as e:
            self._handle_error("metadata_storage", filename, str(e))
            raise

    def _handle_error(self, error_type: str, filename: str, error_message: str):
        """Log errors with detailed information for recovery."""
        try:
            error_doc = {
                "error_type": error_type,
                "filename": filename,
                "error_message": error_message,
                "timestamp": datetime.now(timezone.utc),
                "recovered": False
            }
            
            self.errors.insert_one(error_doc)
            logging.error(f"Error ({error_type}) processing {filename}: {error_message}")
            
        except PyMongoError as e:
            logging.error(f"Error logging error: {str(e)}")

    def store_processing_results(self, doc_id: ObjectId, results: Dict[str, Any]):
        """Store processing results with versioning and error handling."""
        try:
            # Prepare results with metadata
            enriched_results = {
                **results,
                "processing_version": "1.0",
                "last_updated": datetime.now(timezone.utc),
                "status": "completed"
            }
            
            # Store results with versioning
            update = {
                "$set": enriched_results,
                "$push": {
                    "processing_history": {
                        "timestamp": datetime.now(timezone.utc),
                        "version": "1.0",
                        "summary_length": len(results.get("summary", "")),
                        "keyword_count": len(results.get("keywords", []))
                    }
                }
            }
            
            self.documents.update_one({"_id": doc_id}, update)
            logging.info(f"Stored processing results for document {doc_id}")
            
        except PyMongoError as e:
            self._handle_error("results_storage", str(doc_id), str(e))
            raise

    def get_processing_stats(self) -> Dict[str, Any]:
        """Get processing statistics."""
        try:
            stats = {
                "total": self.documents.count_documents({}),
                "completed": self.documents.count_documents({"status": "completed"}),
                "pending": self.documents.count_documents({"status": "pending"}),
                "error": self.documents.count_documents({"status": "error"}),
                "last_updated": datetime.now(timezone.utc)
            }
            return stats
        except PyMongoError as e:
            logging.error(f"Error getting statistics: {str(e)}")
            return {}

    def cleanup(self):
        """Cleanup MongoDB connections."""
        try:
            self.client.close()
            logging.info("MongoDB connection closed")
        except Exception as e:
            logging.error(f"Error closing MongoDB connection: {str(e)}")

class PDFProcessor:
    def __init__(self, mongo_handler: MongoDBHandler, input_dir: str):
        self.mongo_handler = mongo_handler
        self.input_dir = input_dir
        self.recovery_attempts = 3

    def process_pdf(self, filename: str) -> Optional[Dict[str, Any]]:
        """Process a single PDF file with error handling and recovery."""
        file_path = os.path.join(self.input_dir, filename)
        doc_id = None
        
        try:
            # Store initial metadata
            doc_id = self.mongo_handler.store_initial_metadata(filename, file_path)
            
            # Extract text from PDF
            with open(file_path, 'rb') as file:
                pdf_reader = PyPDF2.PdfReader(file)
                text = ""
                for page in pdf_reader.pages:
                    text += page.extract_text() + "\n"
            
            # Process the extracted text
            processed_data = {
                "filename": filename,
                "summary": text[:500],  # First 500 characters as summary
                "keywords": self._extract_keywords(text),
                "metadata": {
                    "page_count": len(pdf_reader.pages),
                    "text_length": len(text),
                    "processed_time": datetime.now(timezone.utc)
                }
            }
            
            # Store results
            self.mongo_handler.store_processing_results(doc_id, processed_data)
            logging.info(f"Successfully processed {filename}")
            
            return processed_data
            
        except Exception as e:
            error_msg = f"Error processing {filename}: {str(e)}"
            logging.error(error_msg)
            if doc_id:
                self.mongo_handler._handle_error("processing", filename, str(e))
            return None

    def _extract_keywords(self, text: str, max_keywords: int = 10) -> List[Dict[str, Any]]:
        """Extract keywords from text."""
        # Simple keyword extraction (you can implement more sophisticated methods)
        words = text.lower().split()
        word_freq = {}
        for word in words:
            if len(word) > 3:  # Skip short words
                word_freq[word] = word_freq.get(word, 0) + 1
        
        # Sort by frequency and convert to list of dicts
        keywords = sorted(word_freq.items(), key=lambda x: x[1], reverse=True)[:max_keywords]
        return [{"word": word, "frequency": freq} for word, freq in keywords]

    def process_directory(self):
        """Process all PDF files in the input directory."""
        if not os.path.exists(self.input_dir):
            raise ValueError(f"Input directory does not exist: {self.input_dir}")
        
        pdf_files = [f for f in os.listdir(self.input_dir) if f.lower().endswith('.pdf')]
        if not pdf_files:
            logging.warning(f"No PDF files found in {self.input_dir}")
            return
        
        logging.info(f"Found {len(pdf_files)} PDF files to process")
        
        # Process files
        successful = 0
        failed = 0
        
        for filename in pdf_files:
            try:
                result = self.process_pdf(filename)
                if result:
                    successful += 1
                else:
                    failed += 1
            except Exception as e:
                failed += 1
                logging.error(f"Failed to process {filename}: {str(e)}")
        
        # Log final statistics
        logging.info(f"Processing complete. Successful: {successful}, Failed: {failed}")
        return {"successful": successful, "failed": failed}

def main():
    """Main execution function."""
    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )
    
    # Configuration
    mongo_uri = "mongodb://localhost:27017/"
    db_name = "pdf_processor"
    input_dir = "pdf_downloads"  # Directory containing PDF files
    
    try:
        # Ensure input directory exists
        if not os.path.exists(input_dir):
            raise ValueError(f"Input directory not found: {input_dir}")
        
        # Initialize MongoDB handler
        mongo_handler = MongoDBHandler(mongo_uri, db_name)
        
        # Initialize processor
        processor = PDFProcessor(mongo_handler, input_dir)
        
        # Process all PDFs in directory
        results = processor.process_directory()
        
        # Get final statistics
        stats = mongo_handler.get_processing_stats()
        print("\nProcessing Statistics:")
        print(f"Total files processed: {stats['total']}")
        print(f"Successfully completed: {stats['completed']}")
        print(f"Failed: {stats['error']}")
        
    except Exception as e:
        logging.error(f"Main execution error: {str(e)}")
    finally:
        # Cleanup
        if 'mongo_handler' in locals():
            mongo_handler.cleanup()

if __name__ == "__main__":
    main()
