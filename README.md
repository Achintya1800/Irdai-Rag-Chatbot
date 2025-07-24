# IRDAI RAG Chatbot

An intelligent document search and question-answering system for IRDAI (Insurance Regulatory and Development Authority of India) documents.

## Features

- Real-time regulatory document scraping
- Smart query routing
- Exact document matching
- Comprehensive search across multiple insurance websites
- Query-driven prioritization
- Production-ready deployment

## Setup

1. Clone the repository:
```bash
git clone https://github.com/yourusername/irdai-rag-chatbot.git
cd irdai-rag-chatbot
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Run the system:
```bash
streamlit run streamlit_app.py
```

## Project Structure

- `src/` - Core source code
  - `scrapers/` - Document scraping modules
  - `rag/` - RAG system implementation
  - `utils/` - Utility functions
- `data/` - Data storage (gitignored)
- `streamlit_app.py` - Main Streamlit interface
- `fix_all_websites_system.py` - System setup and fixes
- `validate_system.py` - System validation

## Usage

1. Start the system with `streamlit run streamlit_app.py`
2. Use the interface to search for specific IRDAI documents
3. Get accurate results with source links and confidence scores

## Example Queries

- "Corporate Agency Matters Concerning RRBs Amalgamated from 1st May 2025 and Beyond"
- "Insurance (Procedure for Holding Inquiry by Adjudicating Officer) Rules, 2016"
- "Guidelines on Remuneration of Directors and Key Managerial Persons of Insurers"
