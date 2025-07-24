#!/usr/bin/env python3
"""
IRDAI RAG Chatbot - Main Application
"""

import sys
import os
import argparse
from loguru import logger
from config import Config

# Add src to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from scrapers.web_scraper import WebScraper
from utils.document_processor import DocumentProcessor
from rag.vector_db import VectorDatabase
from rag.rag_system import RAGSystem

def setup_logging():
    """Setup logging configuration"""
    config = Config()
    
    # Remove default handler
    logger.remove()
    
    # Add file handler
    logger.add(
        config.LOG_FILE,
        level=config.LOG_LEVEL,
        format="{time:YYYY-MM-DD HH:mm:ss} | {level} | {name}:{function}:{line} | {message}",
        rotation="10 MB",
        retention="7 days"
    )
    
    # Add console handler
    logger.add(
        sys.stderr,
        level=config.LOG_LEVEL,
        format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> | <level>{message}</level>"
    )

def scrape_websites():
    """Scrape all configured websites"""
    logger.info("Starting web scraping process")
    
    scraper = WebScraper()
    scraped_data = scraper.scrape_all_websites()
    
    if scraped_data:
        scraper.save_scraped_data()
        logger.info(f"Successfully scraped {len(scraped_data)} pages")
        return scraped_data
    else:
        logger.error("No data scraped")
        return []

def process_documents():
    """Process scraped documents into chunks"""
    logger.info("Starting document processing")
    
    # Load scraped data
    scraper = WebScraper()
    scraped_data = scraper.load_scraped_data()
    
    if not scraped_data:
        logger.error("No scraped data found. Please run scraping first.")
        return []
    
    # Process documents
    processor = DocumentProcessor()
    chunks = processor.process_scraped_content(scraped_data)
    
    # Enrich with metadata
    enriched_chunks = processor.enrich_metadata(chunks)
    
    logger.info(f"Successfully processed {len(enriched_chunks)} document chunks")
    return enriched_chunks

def build_vector_database():
    """Build vector database from processed documents"""
    logger.info("Building vector database")
    
    # Process documents
    chunks = process_documents()
    
    if not chunks:
        logger.error("No document chunks to process")
        return False
    
    # Initialize vector database
    vector_db = VectorDatabase()
    
    # Add documents to vector database
    vector_db.add_documents(chunks)
    
    # Get stats
    stats = vector_db.get_collection_stats()
    logger.info(f"Vector database built successfully: {stats}")
    
    return True

def run_chatbot():
    """Run the interactive chatbot"""
    logger.info("Starting IRDAI RAG Chatbot")
    
    # Initialize RAG system
    rag_system = RAGSystem()
    
    # Check if vector database has data
    stats = rag_system.get_system_stats()
    total_docs = stats.get('vector_db_stats', {}).get('total_documents', 0)
    
    if total_docs == 0:
        logger.error("Vector database is empty. Please run data pipeline first.")
        print("❌ No data found in vector database. Please run: python main.py --build-pipeline")
        return
    
    print(f"✅ IRDAI RAG Chatbot initialized with {total_docs} documents")
    print("💡 Ask questions about IRDAI regulations, insurance policies, or company information")
    print("🔍 Examples:")
    print("  - What is the latest IRDAI regulation?")
    print("  - Tell me about life insurance guidelines")
    print("  - What are the recent updates in general insurance?")
    print("  - Show me IRDAI circular about motor insurance")
    print("\n" + "="*60)
    
    while True:
        try:
            # Get user query
            user_query = input("\n🤔 Your question: ").strip()
            
            if not user_query:
                continue
                
            if user_query.lower() in ['quit', 'exit', 'bye']:
                print("👋 Thank you for using IRDAI RAG Chatbot!")
                break
                
            if user_query.lower() == 'stats':
                stats = rag_system.get_system_stats()
                print("\n📊 System Statistics:")
                print(f"Total documents: {stats.get('vector_db_stats', {}).get('total_documents', 0)}")
                print(f"Embedding model: {stats.get('embedding_model', 'N/A')}")
                print(f"Chunk size: {stats.get('chunk_size', 'N/A')}")
                continue
            
            # Process query
            print("\n🔍 Searching for relevant information...")
            response = rag_system.query(user_query)
            
            # Display response
            print(f"\n🤖 **Answer:**")
            print(response.answer)
            
            print(f"\n📊 **Confidence Score:** {response.confidence_score:.2f}")
            
            if response.sources:
                print(f"\n📚 **Sources ({len(response.sources)}):**")
                for i, source in enumerate(response.sources, 1):
                    print(f"\n{i}. **{source['title']}**")
                    print(f"   🌐 URL: {source['url']}")
                    print(f"   📂 Type: {source['source_type']}")
                    print(f"   📄 Relevance: {source['relevance_score']:.3f}")
                    
                    if source['document_links']:
                        print(f"   🔗 Documents: {', '.join(source['document_links'])}")
                    
                    print(f"   📝 Snippet: {source['snippet']}")
            
            print("\n" + "="*60)
            
        except KeyboardInterrupt:
            print("\n👋 Thank you for using IRDAI RAG Chatbot!")
            break
        except Exception as e:
            logger.error(f"Error processing query: {e}")
            print(f"❌ Error: {e}")

def main():
    """Main application entry point"""
    setup_logging()
    
    parser = argparse.ArgumentParser(description="IRDAI RAG Chatbot")
    parser.add_argument("--scrape", action="store_true", help="Scrape websites")
    parser.add_argument("--process", action="store_true", help="Process documents")
    parser.add_argument("--build-db", action="store_true", help="Build vector database")
    parser.add_argument("--build-pipeline", action="store_true", help="Run complete pipeline (scrape + process + build)")
    parser.add_argument("--chat", action="store_true", help="Start chatbot interface")
    parser.add_argument("--stats", action="store_true", help="Show system statistics")
    parser.add_argument("--reset", action="store_true", help="Reset vector database")
    
    args = parser.parse_args()
    
    # If no arguments provided, show help
    if not any(vars(args).values()):
        parser.print_help()
        return
    
    try:
        if args.reset:
            logger.info("Resetting vector database")
            vector_db = VectorDatabase()
            vector_db.reset_database()
            print("✅ Vector database reset successfully")
            
        if args.scrape:
            scraped_data = scrape_websites()
            if scraped_data:
                print(f"✅ Successfully scraped {len(scraped_data)} pages")
            else:
                print("❌ Scraping failed")
                
        if args.process:
            chunks = process_documents()
            if chunks:
                print(f"✅ Successfully processed {len(chunks)} document chunks")
            else:
                print("❌ Document processing failed")
                
        if args.build_db:
            success = build_vector_database()
            if success:
                print("✅ Vector database built successfully")
            else:
                print("❌ Vector database build failed")
                
        if args.build_pipeline:
            logger.info("Running complete pipeline")
            
            # Step 1: Scrape
            print("🔄 Step 1: Scraping websites...")
            scraped_data = scrape_websites()
            if not scraped_data:
                print("❌ Pipeline failed at scraping step")
                return
            
            # Step 2: Build vector database (includes processing)
            print("🔄 Step 2: Building vector database...")
            success = build_vector_database()
            if not success:
                print("❌ Pipeline failed at vector database build step")
                return
                
            print("✅ Complete pipeline executed successfully!")
            print("💡 You can now run: python main.py --chat")
            
        if args.stats:
            rag_system = RAGSystem()
            stats = rag_system.get_system_stats()
            print("\n📊 System Statistics:")
            print(f"Total documents: {stats.get('vector_db_stats', {}).get('total_documents', 0)}")
            print(f"Collection name: {stats.get('vector_db_stats', {}).get('collection_name', 'N/A')}")
            print(f"Embedding model: {stats.get('embedding_model', 'N/A')}")
            print(f"Chunk size: {stats.get('chunk_size', 'N/A')}")
            print(f"Top K results: {stats.get('top_k_results', 'N/A')}")
            
        if args.chat:
            run_chatbot()
            
    except Exception as e:
        logger.error(f"Application error: {e}")
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    main()