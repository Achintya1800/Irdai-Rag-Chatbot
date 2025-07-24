#!/usr/bin/env python3
"""
Run the updated pipeline with enhanced document link extraction
"""

import sys
import os
from loguru import logger

# Add src to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from scrapers.web_scraper import WebScraper
from utils.document_processor import DocumentProcessor
from rag.vector_db import VectorDatabase
from rag.rag_system import RAGSystem

def main():
    """Run the complete updated pipeline"""
    
    print("🚀 Starting Updated IRDAI RAG Pipeline")
    print("=" * 50)
    
    # Step 1: Enhanced Web Scraping
    print("\n🔄 Step 1: Enhanced Web Scraping (with document link extraction)")
    scraper = WebScraper()
    
    # Reset the database first
    try:
        vector_db = VectorDatabase()
        vector_db.reset_database()
        print("✅ Database reset successfully")
    except Exception as e:
        print(f"⚠️ Database reset failed: {e}")
    
    # Scrape websites with enhanced document link extraction
    try:
        scraped_data = scraper.scrape_all_websites()
        scraper.save_scraped_data()
        
        # Show document link statistics
        total_doc_links = 0
        for data in scraped_data:
            total_doc_links += len(data.document_links)
        
        print(f"✅ Successfully scraped {len(scraped_data)} pages")
        print(f"📄 Total document links found: {total_doc_links}")
        
        # Show breakdown by site
        site_stats = {}
        for data in scraped_data:
            site = data.metadata.get('source_website', 'Unknown')
            if site not in site_stats:
                site_stats[site] = {'pages': 0, 'docs': 0}
            site_stats[site]['pages'] += 1
            site_stats[site]['docs'] += len(data.document_links)
        
        print("\n📊 Site-wise Statistics:")
        for site, stats in site_stats.items():
            print(f"  {site}: {stats['pages']} pages, {stats['docs']} documents")
        
    except Exception as e:
        print(f"❌ Scraping failed: {e}")
        return False
    
    # Step 2: Document Processing
    print("\n🔄 Step 2: Document Processing")
    try:
        processor = DocumentProcessor()
        chunks = processor.process_scraped_content(scraped_data)
        enriched_chunks = processor.enrich_metadata(chunks)
        
        print(f"✅ Successfully processed {len(enriched_chunks)} document chunks")
        
        # Show document link preservation
        chunks_with_docs = sum(1 for chunk in enriched_chunks 
                             if chunk.metadata.get('document_links'))
        print(f"📄 Chunks with document links: {chunks_with_docs}")
        
    except Exception as e:
        print(f"❌ Document processing failed: {e}")
        return False
    
    # Step 3: Vector Database Building
    print("\n🔄 Step 3: Vector Database Building")
    try:
        vector_db = VectorDatabase()
        vector_db.add_documents(enriched_chunks)
        
        stats = vector_db.get_collection_stats()
        print(f"✅ Vector database built successfully")
        print(f"📊 Total documents: {stats.get('total_documents', 0)}")
        print(f"🔍 Embedding model: {stats.get('embedding_model', 'N/A')}")
        
    except Exception as e:
        print(f"❌ Vector database building failed: {e}")
        return False
    
    # Step 4: Test RAG System
    print("\n🔄 Step 4: Testing RAG System")
    try:
        rag_system = RAGSystem()
        
        # Test with a sample query
        test_query = "What are the latest IRDAI regulations?"
        print(f"🔍 Testing query: {test_query}")
        
        response = rag_system.query(test_query)
        
        print(f"✅ RAG system test successful!")
        print(f"📝 Response length: {len(response.answer)} characters")
        print(f"📊 Confidence score: {response.confidence_score:.2f}")
        print(f"📚 Sources found: {len(response.sources)}")
        
        # Count document links in response
        total_doc_links = 0
        for source in response.sources:
            if source.get('document_links'):
                total_doc_links += len(source['document_links'])
        
        print(f"🔗 Document links in response: {total_doc_links}")
        
    except Exception as e:
        print(f"❌ RAG system test failed: {e}")
        return False
    
    # Step 5: Final Statistics
    print("\n📊 Final Pipeline Statistics")
    print("=" * 50)
    print(f"✅ Pipeline Status: SUCCESSFUL")
    print(f"🌐 Websites Scraped: 4")
    print(f"📄 Pages Scraped: {len(scraped_data)}")
    print(f"📝 Document Chunks: {len(enriched_chunks)}")
    print(f"🔗 Total Document Links: {total_doc_links}")
    print(f"🗄️ Vector Database Size: {stats.get('total_documents', 0)} documents")
    
    print("\n🎯 Ready for Demo!")
    print("Run: streamlit run streamlit_app.py")
    
    return True

if __name__ == "__main__":
    success = main()
    if success:
        print("\n🎉 Pipeline completed successfully!")
        print("💡 Your system is now ready for the manager presentation!")
    else:
        print("\n❌ Pipeline failed. Please check the logs for details.")