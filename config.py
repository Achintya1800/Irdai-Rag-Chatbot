import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

class Config:
    # ✅ Load OpenAI API Key from environment
    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

    # Vector Database Configuration
    CHROMA_DB_PATH = "data/vector_db"
    COLLECTION_NAME = "irdai_documents"
    EMBEDDING_MODEL = "all-MiniLM-L6-v2"
    
    # Document Processing Configuration
    CHUNK_SIZE = 500
    CHUNK_OVERLAP = 50
    TOP_K_RESULTS = 5
    
    # Scraping Configuration
    MAX_PAGES_PER_WEBSITE = 50
    REQUEST_DELAY = 1
    TIMEOUT = 30
    
    # RAG Configuration
    MAX_CONTEXT_LENGTH = 4000
    TEMPERATURE = 0.7
    
    # LLM Analysis Configuration
    LLM_ANALYSIS_ENABLED = False
    GUARDRAILS_ENABLED = True
    FALLBACK_MODE = True
    
    # File paths
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    DATA_DIR = os.path.join(BASE_DIR, "data")
    SCRAPED_DATA_DIR = os.path.join(DATA_DIR, "scraped")
    LOGS_DIR = os.path.join(BASE_DIR, "logs")
    
    @classmethod
    def validate_config(cls):
        """Validate configuration settings"""
        issues = []

        # Check OpenAI API key
        if not cls.OPENAI_API_KEY:
            issues.append("OpenAI API key not configured")
        
        # Ensure required directories exist
        for dir_path in [cls.DATA_DIR, cls.SCRAPED_DATA_DIR, cls.LOGS_DIR]:
            if not os.path.exists(dir_path):
                try:
                    os.makedirs(dir_path, exist_ok=True)
                except Exception as e:
                    issues.append(f"Cannot create directory {dir_path}: {e}")
        
        return issues
    
    @classmethod
    def get_openai_status(cls):
        """Check OpenAI API key status"""
        key = cls.OPENAI_API_KEY
        if not key:
            return "not_configured"
        elif len(key) < 50:
            return "invalid_format"
        elif key.startswith("sk-"):
            return "configured"
        else:
            return "unknown_format"
