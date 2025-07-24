import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    def __init__(self):
        # OpenAI API Configuration
        self.OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
        
        # Scraping Configuration
        self.SCRAPING_DELAY = 2  # seconds between requests
        self.MAX_DEPTH = 3  # maximum depth for scraping
        self.REQUEST_TIMEOUT = 30  # seconds
        
        # ChromaDB Configuration
        self.CHROMA_DB_PATH = "./data/chroma_db"
        self.COLLECTION_NAME = "irdai_documents"
        
        # RAG Configuration
        self.CHUNK_SIZE = 1000
        self.CHUNK_OVERLAP = 200
        self.TOP_K_RESULTS = 3
        
        # Target Websites
        self.WEBSITES = {
            "irdai": {
                "base_url": "https://irdai.gov.in",
                "type": "regulatory",
                "priority_paths": [
                    "/consolidated-gazette-notified-regulations",
                    "/circulars",
                    "/guidelines",
                    "/annual-reports"
                ]
            },
            "life_insurance_1": {
                "base_url": "https://www.licindia.in",
                "type": "life_insurance",
                "priority_paths": [
                    "/corporate-governance",
                    "/investor-relations",
                    "/annual-reports"
                ]
            },
            "life_insurance_2": {
                "base_url": "https://www.hdfclife.com",
                "type": "life_insurance",
                "priority_paths": [
                    "/investor-relations",
                    "/corporate-governance",
                    "/annual-reports"
                ]
            },
            "general_insurance": {
                "base_url": "https://www.newindia.co.in",
                "type": "general_insurance",
                "priority_paths": [
                    "/corporate-governance",
                    "/investor-relations",
                    "/annual-reports"
                ]
            }
        }
        
        # Embedding Model
        self.EMBEDDING_MODEL = "all-MiniLM-L6-v2"
        
        # Logging
        self.LOG_LEVEL = "INFO"
        self.LOG_FILE = "./logs/irdai_rag.log"
