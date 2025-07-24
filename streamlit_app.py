import streamlit as st
import sys
import os
import re
from datetime import datetime
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
from typing import List, Dict, Any
import time

# Add src to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

# Import our modules
from rag.rag_system import RAGSystem
from rag.vector_db import VectorDatabase
from config import Config

# Add comprehensive scraper import
try:
    from scrapers.comprehensive_scraper import ComprehensiveScraper
    SCRAPER_AVAILABLE = True
except ImportError:
    SCRAPER_AVAILABLE = False

# Page configuration
st.set_page_config(
    page_title="IRDAI RAG Chatbot",
    page_icon="🏛️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for professional styling
st.markdown("""
<style>
    .main-header {
        background: linear-gradient(90deg, #1e3c72 0%, #2a5298 100%);
        padding: 2rem;
        border-radius: 10px;
        margin-bottom: 2rem;
        text-align: center;
        color: white;
    }
    
    .stats-card {
        background: white;
        padding: 1.5rem;
        border-radius: 10px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        border-left: 4px solid #2a5298;
        margin-bottom: 1rem;
    }
    
    .confidence-high {
        color: #28a745;
        font-weight: bold;
    }
    
    .confidence-medium {
        color: #ffc107;
        font-weight: bold;
    }
    
    .confidence-low {
        color: #dc3545;
        font-weight: bold;
    }
    
    .stButton > button {
        background-color: #2a5298;
        color: white;
        border: none;
        border-radius: 5px;
        padding: 0.5rem 1rem;
        font-weight: bold;
    }
    
    .stButton > button:hover {
        background-color: #1e3c72;
    }
    
    .status-success {
        background-color: #d4edda;
        border: 1px solid #c3e6cb;
        color: #155724;
    }
    
    .status-warning {
        background-color: #fff3cd;
        border: 1px solid #ffeaa7;
        color: #856404;
    }
    
    .status-error {
        background-color: #f8d7da;
        border: 1px solid #f5c6cb;
        color: #721c24;
    }
</style>
""", unsafe_allow_html=True)

# SIMPLIFIED SYSTEM SETUP USING EXISTING FUNCTIONS
def integrated_system_setup():
    """Simplified system setup using existing scraping functions"""
    
    setup_progress = st.progress(0)
    status_container = st.container()
    
    with status_container:
        st.markdown("### 🔧 **System Initialization**")
        
        # Step 1: Check if system needs setup
        setup_progress.progress(10)
        setup_status = st.empty()
        setup_status.info("🔍 Checking system status...")
        
        try:
            vector_db = VectorDatabase()
            stats = vector_db.get_collection_stats()
            total_docs = stats.get('total_documents', 0)
            
            if total_docs > 0:
                setup_status.success(f"✅ System ready! Found {total_docs} documents in database.")
                setup_progress.progress(100)
                return True, "System already initialized"
            else:
                setup_status.warning("⚠️ Database empty. Running comprehensive setup...")
        except Exception as e:
            setup_status.warning(f"⚠️ Database error: {e}. Running fresh setup...")
        
        # Step 2: Use comprehensive scraper with improved error handling
        setup_progress.progress(40)
        setup_status.info("🌐 Using comprehensive scraper to collect documents...")
        
        try:
            # IMPROVED: Better import error handling
            try:
                from fix_all_websites_system import integrate_comprehensive_documents
                setup_status.info("✅ Successfully imported integration function")
            except ImportError as import_error:
                setup_status.error(f"❌ Import error: {import_error}")
                setup_status.error("🔧 Please check that fix_all_websites_system.py has the integrate_comprehensive_documents function")
                return False, f"Import error: {import_error}"
            
            setup_status.info("🔄 Running comprehensive document integration...")
            success = integrate_comprehensive_documents()
            
            if success:
                setup_progress.progress(100)
                setup_status.success("🎉 **SYSTEM SETUP COMPLETE!** Ready for queries.")
                return True, "Setup completed successfully"
            else:
                setup_status.error("❌ Comprehensive integration failed")
                return False, "Integration failed"
                
        except Exception as e:
            setup_status.error(f"❌ Setup failed: {e}")
            # IMPROVED: Show more detailed error information
            import traceback
            error_details = traceback.format_exc()
            setup_status.error(f"Error details: {error_details}")
            return False, f"Setup error: {e}"

# Cache the initialization
@st.cache_resource
def initialize_complete_system():
    """Initialize the complete system with caching"""
    try:
        # Check if already initialized
        vector_db = VectorDatabase()
        stats = vector_db.get_collection_stats()
        if stats.get('total_documents', 0) > 0:
            return RAGSystem(), True, "System already ready"
        
        # Need to initialize
        return None, False, "Needs setup"
    except:
        return None, False, "Needs setup"

@st.cache_resource  
def initialize_comprehensive_scraper():
    """Initialize comprehensive scraper with caching"""
    if SCRAPER_AVAILABLE:
        try:
            return ComprehensiveScraper(use_selenium=False)
        except Exception as e:
            st.warning(f"Could not initialize scraper: {e}")
            return None
    return None

def format_confidence_score(score: float) -> str:
    """Format confidence score with color coding"""
    if score >= 0.8:
        return f'<span class="confidence-high">{score:.2f}</span>'
    elif score >= 0.6:
        return f'<span class="confidence-medium">{score:.2f}</span>'
    else:
        return f'<span class="confidence-low">{score:.2f}'

def create_confidence_gauge(score: float):
    """Create a confidence gauge chart"""
    fig = go.Figure(go.Indicator(
        mode = "gauge+number",
        value = score,
        domain = {'x': [0, 1], 'y': [0, 1]},
        title = {'text': "Confidence Score"},
        gauge = {
            'axis': {'range': [None, 1]},
            'bar': {'color': "darkblue"},
            'steps': [
                {'range': [0, 0.6], 'color': "lightgray"},
                {'range': [0.6, 0.8], 'color': "yellow"},
                {'range': [0.8, 1], 'color': "green"}
            ],
            'threshold': {
                'line': {'color': "red", 'width': 4},
                'thickness': 0.75,
                'value': 0.9
            }
        }
    ))
    
    fig.update_layout(height=300)
    return fig

@st.cache_data
def get_system_stats():
    """Get system statistics with caching"""
    try:
        vector_db = VectorDatabase()
        return vector_db.get_collection_stats()
    except Exception as e:
        st.error(f"Failed to get system stats: {e}")
        return {}

def display_sources(sources: List[Dict[str, Any]]):
    """Display sources in a formatted way"""
    for i, source in enumerate(sources, 1):
        with st.expander(f"📚 Source {i}: {source['title'][:50]}..." if len(source['title']) > 50 else f"📚 Source {i}: {source['title']}", expanded=True):
            
            col1, col2 = st.columns([3, 1])
            
            with col1:
                st.markdown(f"**🌐 Source Website:** {source['url']}")
                st.markdown(f"**📂 Document Type:** {source['source_type'].replace('_', ' ').title()}")
                st.markdown(f"**📄 Relevance Score:** {source['relevance_score']:.3f}")
                
                # Show content preview
                st.markdown(f"**📝 Content Preview:**")
                st.markdown(f"_{source['snippet']}_")
                
            with col2:
                # Create mini gauge for relevance with unique key
                mini_fig = go.Figure(go.Indicator(
                    mode = "gauge+number",
                    value = source['relevance_score'],
                    domain = {'x': [0, 1], 'y': [0, 1]},
                    gauge = {
                        'axis': {'range': [None, 1]},
                        'bar': {'color': "lightblue"},
                        'bgcolor': "white",
                        'borderwidth': 2,
                        'bordercolor': "gray"
                    }
                ))
                mini_fig.update_layout(height=150, margin=dict(l=20, r=20, t=20, b=20))
                # FIX: Add unique key to prevent duplicate element ID error
                st.plotly_chart(mini_fig, use_container_width=True, key=f"relevance_gauge_{i}_{hash(source['url']) % 10000}")
            
            # Display reference document links prominently
            if source.get('document_links') and len(source['document_links']) > 0:
                st.markdown("---")
                st.markdown("### 🔗 **Reference Document Links**")
                st.markdown("*Official documents, regulations, and policy files:*")
                
                # Categorize documents by type
                document_detail_links = []
                direct_pdf_links = []
                direct_doc_links = []
                other_links = []
                
                for doc_link in source['document_links']:
                    if 'document-detail' in doc_link.lower():
                        document_detail_links.append(doc_link)
                    elif doc_link.lower().endswith('.pdf'):
                        direct_pdf_links.append(doc_link)
                    elif doc_link.lower().endswith(('.doc', '.docx')):
                        direct_doc_links.append(doc_link)
                    else:
                        other_links.append(doc_link)
                
                # Display document detail pages (IRDAI specific)
                if document_detail_links:
                    st.markdown("**📋 IRDAI Document Detail Pages:**")
                    for doc_link in document_detail_links[:5]:
                        # Extract document ID if available
                        doc_id_match = re.search(r'documentId=(\d+)', doc_link)
                        if doc_id_match:
                            doc_id = doc_id_match.group(1)
                            st.markdown(f"- [📋 IRDAI Document ID: {doc_id}]({doc_link})")
                        else:
                            st.markdown(f"- [📋 IRDAI Document Detail]({doc_link})")
                    
                    if len(document_detail_links) > 5:
                        st.markdown(f"... and {len(document_detail_links) - 5} more document detail pages")
                
                # Display direct PDF links
                if direct_pdf_links:
                    st.markdown("**📄 Direct PDF Downloads:**")
                    for doc_link in direct_pdf_links[:5]:
                        doc_name = doc_link.split('/')[-1].replace('%20', ' ')
                        if len(doc_name) > 50:
                            doc_name = doc_name[:47] + "..."
                        st.markdown(f"- [📄 {doc_name}]({doc_link})")
                    
                    if len(direct_pdf_links) > 5:
                        st.markdown(f"... and {len(direct_pdf_links) - 5} more PDF documents")
                
                # Display Word documents
                if direct_doc_links:
                    st.markdown("**📝 Word Documents:**")
                    for doc_link in direct_doc_links[:3]:
                        doc_name = doc_link.split('/')[-1].replace('%20', ' ')
                        if len(doc_name) > 50:
                            doc_name = doc_name[:47] + "..."
                        st.markdown(f"- [📝 {doc_name}]({doc_link})")
                    
                    if len(direct_doc_links) > 3:
                        st.markdown(f"... and {len(direct_doc_links) - 3} more Word documents")
                
                # Display other document links
                if other_links:
                    st.markdown("**🔗 Other Document Links:**")
                    for doc_link in other_links[:3]:
                        if 'documentId=' in doc_link:
                            doc_id_match = re.search(r'documentId=(\d+)', doc_link)
                            if doc_id_match:
                                doc_id = doc_id_match.group(1)
                                st.markdown(f"- [🔗 Document ID: {doc_id}]({doc_link})")
                            else:
                                st.markdown(f"- [🔗 Document Link]({doc_link})")
                        else:
                            doc_name = doc_link.split('/')[-1] if '/' in doc_link else "Document"
                            st.markdown(f"- [🔗 {doc_name}]({doc_link})")
                
                # Show summary statistics
                total_docs = len(source['document_links'])
                st.markdown("---")
                st.markdown(f"**📊 Document Summary:**")
                st.markdown(f"- **Total Documents:** {total_docs}")
                st.markdown(f"- **IRDAI Document Pages:** {len(document_detail_links)}")
                st.markdown(f"- **Direct PDF Downloads:** {len(direct_pdf_links)}")
                st.markdown(f"- **Word Documents:** {len(direct_doc_links)}")
                st.markdown(f"- **Other Links:** {len(other_links)}")
                
            else:
                st.markdown("---")
                st.markdown("### 🔗 **Reference Document Links**")
                st.markdown("*No specific document links found for this source.*")
                st.markdown("*Information is from the main webpage content.*")

def perform_dynamic_search(query: str, rag_system, scraper):
        """
        ENHANCED: Better handling with EARLY STOPPING for perfect matches
        """
        query_lower = query.lower().strip()
        
        # Check if user wants to force fresh search
        force_fresh = st.session_state.get('force_fresh_search', False)
        
        # ENHANCED: More comprehensive keyword detection for deep search
        irdai_specific_terms = [
            "reconstitution", "inter-disciplinary", "standing committee", "cyber security",
            "rules", "act", "regulation", "circular", "notification", 
            "guideline", "procedure", "inquiry", "adjudicating", "officer",
            "annulment", "expression of interest", "empanelment", "advertising agencies"  # NEW: Added administrative terms
        ]
        
        should_deep_search = (
            force_fresh or
            any(term in query_lower for term in irdai_specific_terms) or
            "insurance" in query_lower or
            "irdai" in query_lower or
            re.search(r'\b20\d{2}\b', query) or  # Contains year
            len(query.split()) > 4  # Complex queries likely need deep search
        )
        
        try:
            # ALWAYS try database first (unless forced fresh search)
            database_response = None
            if not force_fresh:
                try:
                    database_response = rag_system.query(query)
                    
                    # ADAPTIVE threshold for accepting database results
                    confidence_threshold = 0.3 if any(term in query_lower for term in ["annulment", "expression of interest"]) else 0.5
                    
                    if database_response.confidence_score >= confidence_threshold and len(database_response.sources) > 0:
                        st.info("📚 **Database Results** - Found relevant information in existing collection")
                        
                        # Create unique keys using timestamp and query hash
                        import hashlib
                        unique_id = hashlib.md5(f"{query}_{time.time()}_{len(st.session_state.messages)}".encode()).hexdigest()[:12]
                        
                        # Add user feedback option
                        col1, col2 = st.columns(2)
                        with col1:
                            if st.button("✅ This is correct", key=f"db_correct_{unique_id}"):
                                st.success("Thank you for the feedback!")
                                return database_response, "database_confirmed"
                        
                        with col2:
                            if st.button("❌ This is wrong - Do deep search", key=f"db_wrong_{unique_id}"):
                                st.session_state.force_fresh_search = True
                                st.warning("🔍 Performing deep search...")
                                # Continue to deep search below
                            else:
                                # Return database result if user doesn't choose deep search
                                return database_response, "database_search"
                except Exception as e:
                    st.error(f"Database search error: {e}")
            
            # Perform deep search if needed or database results insufficient
            if should_deep_search or force_fresh or not database_response or database_response.confidence_score < confidence_threshold:
                st.info(f"🔍 **Deep Recursive Search** - Comprehensive scraping for: '{query}'")
                
                if scraper:
                    with st.spinner("🌐 Performing deep recursive search across all IRDAI sections..."):
                        st.info("🎯 **Deep Search Strategy:** Recursively visiting Acts, Rules, Regulations, Notifications, Circulars, Guidelines, Orders, Notices, and more")
                        
                        # Force comprehensive search
                        scraped_documents = scraper.scrape_all_websites_comprehensive(query)
                        
                        if scraped_documents:
                            # NEW: Check for perfect matches FIRST
                            perfect_matches = [doc for doc in scraped_documents if doc.metadata.get('relevance_score', 0) >= 0.99]
                            
                            if perfect_matches:
                                st.success(f"🎯 **PERFECT MATCH FOUND!** Found {len(perfect_matches)} exact match(es)!")
                                perfect_doc = perfect_matches[0]  # Take the first perfect match
                                
                                st.success(f"🎯 PERFECT MATCH: {perfect_doc.title} (Score: {perfect_doc.metadata.get('relevance_score', 0):.3f}, ID: {perfect_doc.metadata.get('document_id', 'N/A')})")
                                
                                # Create immediate response from perfect match
                                class PerfectMatchResponse:
                                    def __init__(self, doc):
                                        self.answer = f"""🎯 **PERFECT MATCH FOUND!**

**Document Title:** {doc.title}

**Document ID:** {doc.metadata.get('document_id', 'N/A')}

**Relevance Score:** {doc.metadata.get('relevance_score', 0):.3f} (Perfect Match)

**Summary:**
{doc.content}

**Official IRDAI Link:** {doc.url}

This document is an exact match for your query: "{query}"

The system found this document through comprehensive real-time search and it matches your query with 100% accuracy."""
                                        
                                        self.confidence_score = doc.metadata.get('relevance_score', 1.0)
                                        self.sources = [{
                                            'title': doc.title,
                                            'url': doc.url,
                                            'source_type': doc.source_type,
                                            'relevance_score': doc.metadata.get('relevance_score', 1.0),
                                            'snippet': doc.content[:300] + "..." if len(doc.content) > 300 else doc.content,
                                            'document_links': doc.document_links,
                                            'document_id': doc.metadata.get('document_id', 'N/A'),
                                            'is_perfect_match': True
                                        }]
                                
                                st.success("🎯 **EARLY STOP TRIGGERED** - Perfect match found, no further processing needed!")
                                return PerfectMatchResponse(perfect_doc), "perfect_match"
                            
                            st.success(f"🎯 Deep search found {len(scraped_documents)} relevant documents!")
                            
                            # Show top matches with ADAPTIVE threshold display
                            for i, doc in enumerate(scraped_documents[:5]):
                                relevance = doc.metadata.get('relevance_score', 0)
                                doc_id = doc.metadata.get('document_id', 'N/A')
                                
                                # ADAPTIVE highlighting based on query type
                                admin_query = any(term in query_lower for term in ["annulment", "expression of interest", "empanelment"])
                                
                                if admin_query:
                                    # Lower thresholds for administrative queries
                                    if relevance >= 0.15:
                                        st.success(f"🎯 HIGH RELEVANCE - Match {i+1}: {doc.title[:60]}... (Score: {relevance:.3f}, ID: {doc_id})")
                                    elif relevance >= 0.05:
                                        st.info(f"✅ GOOD MATCH - Match {i+1}: {doc.title[:60]}... (Score: {relevance:.3f}, ID: {doc_id})")
                                    else:
                                        st.info(f"📄 Match {i+1}: {doc.title[:60]}... (Score: {relevance:.3f}, ID: {doc_id})")
                                else:
                                    # Standard thresholds for regular queries
                                    if relevance >= 0.3:
                                        st.success(f"🎯 HIGH RELEVANCE - Match {i+1}: {doc.title[:60]}... (Score: {relevance:.3f}, ID: {doc_id})")
                                    elif relevance >= 0.1:
                                        st.info(f"✅ GOOD MATCH - Match {i+1}: {doc.title[:60]}... (Score: {relevance:.3f}, ID: {doc_id})")
                                    else:
                                        st.info(f"📄 Match {i+1}: {doc.title[:60]}... (Score: {relevance:.3f}, ID: {doc_id})")
                            

                            from utils.document_processor import DocumentProcessor
                            processor = DocumentProcessor()
                            
                            class ScrapedContent:
                                def __init__(self, doc):
                                    self.url = doc.url
                                    self.title = doc.title
                                    self.content = doc.content
                                    self.source_type = doc.source_type
                                    self.document_links = doc.document_links
                                    self.metadata = doc.metadata
                            
                            scraped_content = [ScrapedContent(doc) for doc in scraped_documents]
                            all_chunks = []
                            
                            # Sort scraped documents by relevance score to ensure top document is processed first
                            scraped_content.sort(key=lambda x: x.metadata.get('relevance_score', 0), reverse=True)
                            
                            # Generate unique IDs with query fingerprint to prevent collision
                            import hashlib
                            query_hash = hashlib.md5(query.encode()).hexdigest()[:8]
                            processed_ids = set()
                            
                            # REDUCED LOGGING: Only process high-priority documents
                            priority_content = [content for content in scraped_content if content.metadata.get('relevance_score', 0) >= 0.1]
                            
                            for content in priority_content[:50]:  # Limit to top 50 to reduce processing
                                try:
                                    chunks = processor.process_scraped_content([content])
                                    enriched_chunks = processor.enrich_metadata(chunks)
                                    
                                    # Filter out duplicate IDs and add query-specific IDs
                                    unique_chunks = []
                                    for chunk in enriched_chunks:
                                        chunk_id = getattr(chunk, 'id', None) or getattr(chunk, 'chunk_id', None)
                                        if chunk_id and chunk_id not in processed_ids:
                                            processed_ids.add(chunk_id)
                                            unique_chunks.append(chunk)
                                        elif not chunk_id:
                                            # Generate query-specific unique ID
                                            import uuid
                                            new_id = f"q_{query_hash}_{uuid.uuid4().hex[:8]}"
                                            if hasattr(chunk, 'id'):
                                                chunk.id = new_id
                                            elif hasattr(chunk, 'chunk_id'):
                                                chunk.chunk_id = new_id
                                            unique_chunks.append(chunk)
                                    
                                    all_chunks.extend(unique_chunks)
                                    
                                except Exception as e:
                                    # REDUCED LOGGING: Only log significant errors
                                    if content.metadata.get('relevance_score', 0) >= 0.5:
                                        st.warning(f"Error processing high-relevance document: {content.title[:30]}...")
                                    continue
                            
                            if all_chunks:
                                try:
                                    # Create a fresh vector database instance
                                    vector_db = VectorDatabase()
                                    
                                    # ENHANCED: Prioritize high-relevance chunks
                                    high_relevance_chunks = []
                                    regular_chunks = []
                                    
                                    for chunk in all_chunks:
                                        source_relevance = getattr(chunk, 'metadata', {}).get('relevance_score', 0)
                                        if source_relevance >= 0.8:
                                            high_relevance_chunks.append(chunk)
                                        else:
                                            regular_chunks.append(chunk)
                                    
                                    # Ensure top-scoring chunks are prioritized
                                    final_chunks = []
                                    used_ids = set()
                                    
                                    # Process high-relevance chunks first
                                    for i, chunk in enumerate(high_relevance_chunks):
                                        chunk_id = getattr(chunk, 'id', None) or getattr(chunk, 'chunk_id', None)
                                        if not chunk_id or chunk_id in used_ids:
                                            # Generate truly unique ID for high-relevance
                                            import uuid
                                            import time
                                            new_id = f"hr_q_{query_hash}_{uuid.uuid4().hex[:8]}_{int(time.time())}_{i}"
                                            if hasattr(chunk, 'id'):
                                                chunk.id = new_id
                                            elif hasattr(chunk, 'chunk_id'):
                                                chunk.chunk_id = new_id
                                            chunk_id = new_id
                                        
                                        used_ids.add(chunk_id)
                                        final_chunks.append(chunk)
                                        
                                        # Mark as high-relevance in metadata
                                        if hasattr(chunk, 'metadata'):
                                            chunk.metadata['is_high_relevance'] = True
                                            chunk.metadata['priority_rank'] = i + 1
                                        
                                        # REDUCED LOGGING: Only show first few
                                        if i < 3:
                                            st.info(f"🌟 PRIORITY: Added high-relevance chunk {i+1}")
                                    
                                    # Then process regular chunks (limited)
                                    for i, chunk in enumerate(regular_chunks[:50]):  # Limit regular chunks
                                        chunk_id = getattr(chunk, 'id', None) or getattr(chunk, 'chunk_id', None)
                                        if not chunk_id or chunk_id in used_ids:
                                            # Generate truly unique ID
                                            import uuid
                                            import time
                                            new_id = f"rt_q_{query_hash}_{uuid.uuid4().hex[:8]}_{int(time.time())}_{i}"
                                            if hasattr(chunk, 'id'):
                                                chunk.id = new_id
                                            elif hasattr(chunk, 'chunk_id'):
                                                chunk.chunk_id = new_id
                                            chunk_id = new_id
                                        
                                        used_ids.add(chunk_id)
                                        final_chunks.append(chunk)
                                    
                                    st.info(f"📊 Final chunks: {len(high_relevance_chunks)} high-relevance + {len(final_chunks) - len(high_relevance_chunks)} regular = {len(final_chunks)} total")

                                    # Add documents with better error handling
                                    try:
                                        vector_db.add_documents(final_chunks)
                                        st.success(f"✅ Successfully added {len(final_chunks)} new document chunks to search index")
                                        
                                        # Show high-relevance document tracking
                                        if high_relevance_chunks:
                                            st.success(f"🌟 {len(high_relevance_chunks)} high-relevance chunks prioritized in database")
                                        
                                    except Exception as add_error:
                                        st.warning(f"⚠️ Error adding some documents: {add_error}")
                                    
                                    # Query with fresh data
                                    updated_response = rag_system.query(query)
                                    
                                    # NEW: For high-confidence results, don't show verification errors
                                    if updated_response.confidence_score >= 0.8:
                                        st.success(f"🎯 High-confidence result found (Score: {updated_response.confidence_score:.3f})")
                                    
                                    return updated_response, "deep_search"
                                    
                                except Exception as e:
                                    st.error(f"Error adding documents to vector database: {e}")
                                    st.info("💡 Using original response from static database")
                                    if database_response:
                                        return database_response, "static_db_fallback"
                            else:
                                st.warning("No processable content found in scraped documents")
                        else:
                            st.warning("No relevant documents found in real-time search")
                            # ENHANCED: More specific error message for administrative queries
                            if any(term in query_lower for term in ["annulment", "expression of interest", "empanelment"]):
                                class EmptyResponse:
                                    def __init__(self):
                                        self.answer = f"No documents found for '{query}'. This might be because:\n\n1. The document may not exist on the IRDAI website\n2. It might have been removed or archived\n3. The exact title or terminology might be different\n\nPlease try:\n- Checking the IRDAI website directly at https://irdai.gov.in\n- Using different keywords like 'tender', 'procurement', or 'advertisement'\n- Searching for more recent or related announcements"
                                        self.confidence_score = 0.0
                                        self.sources = []
                            else:
                                class EmptyResponse:
                                    def __init__(self):
                                        self.answer = f"No exact matches found for '{query}' in the IRDAI website. The document may not exist or may have a different title. Please try rephrasing your query or check the IRDAI website directly."
                                        self.confidence_score = 0.0
                                        self.sources = []
                            return EmptyResponse(), "no_matches_found"
                else:
                    st.warning("Real-time scraper not available")
            
            # Fallback to database response if available
            if database_response:
                st.info("📚 **Using existing database** - Found relevant information in static collection")
                return database_response, "static_db"
            else:
                # Final fallback
                class FallbackResponse:
                    def __init__(self):
                        self.answer = f"I apologize, but I couldn't find information about '{query}'. Please try rephrasing your question."
                        self.confidence_score = 0.0
                        self.sources = []
                return FallbackResponse(), "error"
            
        except Exception as e:
            st.error(f"Error in dynamic search: {e}")
            
            class FallbackResponse:
                def __init__(self):
                    self.answer = f"I apologize, but I encountered an error while searching for information about '{query}'. Please try rephrasing your question or check the IRDAI website directly at https://irdai.gov.in"
                    self.confidence_score = 0.0
                    self.sources = []
            
            return FallbackResponse(), "error"

def create_analytics_dashboard():
    """Create analytics dashboard"""
    st.header("📊 System Analytics")
    
    # Get system stats
    stats = get_system_stats()
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric(
            label="Total Documents",
            value=stats.get('total_documents', 0),
            delta=None
        )
    
    with col2:
        st.metric(
            label="Collection Name",
            value=stats.get('collection_name', 'N/A'),
            delta=None
        )
    
    with col3:
        st.metric(
            label="Embedding Model",
            value="MiniLM-L6-v2",
            delta=None
        )
    
    with col4:
        st.metric(
            label="Vector DB",
            value="ChromaDB",
            delta=None
        )
    
    # Source type distribution
    if 'source_distribution' in st.session_state:
        st.subheader("📈 Source Type Distribution")
        
        source_data = pd.DataFrame([
            {'Type': 'Regulatory', 'Count': 1},
            {'Type': 'Life Insurance', 'Count': 3},
            {'Type': 'General Insurance', 'Count': 5}
        ])
        
        fig = px.pie(source_data, values='Count', names='Type', 
                     title="Document Sources by Type",
                     color_discrete_sequence=['#FF6B6B', '#4ECDC4', '#45B7D1'])
        st.plotly_chart(fig, use_container_width=True)

def main():
    """Enhanced main interface with deep search capabilities"""
    
    # Header
    st.markdown("""
    <div class="main-header">
        <h1>🏛️ IRDAI RAG System - Production</h1>
        <p>Real-time Insurance Document Search</p>
        <p><em>Query-driven search with live website integration</em></p>
    </div>
    """, unsafe_allow_html=True)
    
    # Initialize session state
    if 'messages' not in st.session_state:
        st.session_state.messages = []
    if 'system_ready' not in st.session_state:
        st.session_state.system_ready = False
    if 'setup_attempted' not in st.session_state:
        st.session_state.setup_attempted = False

    import time  # Ensure time is imported in this scope
    # Add Quick Start option in sidebar
    with st.sidebar:
        if st.button("🚀 **Quick Start (Skip Setup)**"):
            st.session_state.system_ready = True
            st.session_state.setup_attempted = True
            st.success("Quick start enabled! You can now try basic functionality.")
            st.rerun()

    # System Initialization Section
    if not st.session_state.system_ready and not st.session_state.setup_attempted:
        st.markdown("## 🚀 **System Initialization**")
        st.info("💡 **First-time setup**: The system will use the comprehensive scraper to build a complete knowledge base.")
        
        col1, col2 = st.columns(2)
        
        with col1:
            if st.button("🔧 **Initialize Complete System**", type="primary"):
                st.session_state.setup_attempted = True
                with st.container():
                    success, message = integrated_system_setup()
                    if success:
                        st.session_state.system_ready = True
                        st.success("🎉 **System Ready!** You can now ask questions.")
                        time.sleep(2)
                        st.rerun()
                    else:
                        st.error(f"❌ Setup failed: {message}")
                        st.info("💡 You can try the initialization again or use Quick Start for testing.")
        
        with col2:
            if st.button("⚡ **Quick Start Demo**", type="secondary"):
                st.session_state.system_ready = True
                st.session_state.setup_attempted = True
                st.info("🚀 Quick start mode enabled! Limited functionality available.")
                time.sleep(1)
                st.rerun()
        
        # IMPROVED: Add troubleshooting information
        st.markdown("---")
        st.markdown("### 📋 **What the complete initialization will do:**")
        st.markdown("1. 🎯 Use targeted scraping based on query type")
        st.markdown("2. 📄 Process and index documents efficiently")  
        st.markdown("3. 🧪 Validate system functionality")
        st.markdown("4. ✅ Prepare for your questions!")
        
        # IMPROVED: Add troubleshooting section
        with st.expander("🔧 **Troubleshooting Setup Issues**", expanded=False):
            st.markdown("""
            **Common Issues:**
            
            1. **Import Error**: If you see "cannot import name 'integrate_comprehensive_documents'"
               - Make sure all files are saved properly
               - Try refreshing the page
               - Use Quick Start as a workaround
            
            2. **Network Issues**: If real scraping fails
               - Check your internet connection
               - IRDAI website might be temporarily unavailable
               - Use Quick Start to test with existing data
            
            3. **Database Issues**: If vector database fails
               - Try clearing browser cache
               - Restart the Streamlit application
               - Use Quick Start mode
            
            **Quick Fix**: Use the "Quick Start" option to test the system immediately!
            """)
        
        return

    # Initialize systems
    if st.session_state.system_ready and 'rag_system' not in st.session_state:
        try:
            with st.spinner("🔄 Initializing systems..."):
                st.session_state.rag_system, ready, status = initialize_complete_system()
                if not ready:
                    st.warning("⚠️ Using simplified mode. Some features may be limited.")
                    st.session_state.rag_system = None
        except Exception as e:
            st.error(f"Initialization error: {e}")
            st.info("💡 Try refreshing the page or use the 'Reinitialize System' button.")

    # Initialize scraper
    if 'scraper' not in st.session_state:
        st.session_state.scraper = initialize_comprehensive_scraper()

    # Sidebar
    with st.sidebar:
        st.header("🎯 Production System")
        
        # System status
        if st.session_state.system_ready:
            st.markdown("""
            <div class="stats-card status-success">
                <h4>📊 Status: ✅ PRODUCTION READY</h4>
                <p><strong>Mode:</strong> Live Search</p>
                <p><strong>Sources:</strong> Real websites</p>
            </div>
            """, unsafe_allow_html=True)
        
        # NEW: Production search modes
        st.markdown("### 🔧 **Search Mode**")
        search_mode = st.radio(
            "Search preference:",
            ["Smart Search (Recommended)", "IRDAI Only", "Database Only"],
            help="Smart Search uses real-time scraping for best results"
        )
        st.session_state.search_mode = search_mode
        
        # NEW: Sample queries focused on real use cases
        st.markdown("💡 **Test Queries:**")
        production_queries = [
            "Guidelines on Remuneration of Directors and Key Managerial Persons of Insurers",
            "Corporate Agency Matters Concerning RRBs Amalgamated from 1st May 2025 and Beyond",
            "ULIP regulations 2024",
            "IRDAI circular on solvency requirements", 
            "Motor vehicle insurance base premium rules"
        ]
        
        for query in production_queries:
            if st.button(f"🔍 {query[:50]}...", key=f"prod_{hash(query) % 10000}"):
                st.session_state.messages.append({"role": "user", "content": query})
                st.rerun()
        
        st.markdown("### 🔧 **Search Controls**")
        
        if st.button("🔄 **Force Deep Search Next Query**"):
            st.session_state.force_fresh_search = True
            st.success("Next query will perform deep recursive search!")
        
        if st.button("🧹 **Clear Search Cache**"):
            st.session_state.force_fresh_search = False
            st.success("Search cache cleared!")
        
        # Show current search mode
        if st.session_state.get('force_fresh_search', False):
            st.warning("⚡ **Deep Search Mode Active** - Next query will do comprehensive scraping")
    
    # Main interface
    if st.session_state.system_ready:
        st.header("💬 Production Document Search")
        
        # NEW: Show current mode with clear expectations
        current_mode = st.session_state.get('search_mode', 'Smart Search (Recommended)')
        if current_mode == "Smart Search (Recommended)":
            st.info("🧠 **Smart Search Mode** - Uses real-time scraping for regulatory queries, database for general queries")
        elif current_mode == "IRDAI Only":
            st.info("🎯 **IRDAI Only Mode** - Real-time search of IRDAI website for every query")
        else:
            st.info("📚 **Database Only Mode** - Uses existing document collection (may have limited coverage)")
        
        # NEW: Expected result preview for Guidelines test query
        with st.expander("🎯 **Test Case: Guidelines on Remuneration**", expanded=False):
            st.markdown("""
            **Test Query:** "Guidelines on Remuneration of Directors and Key Managerial Persons of Insurers"
            
            **Expected Top Result:**
            - **Title:** बीमाकर्ताओं के निदेशकों और प्रमुख प्रबंधकीय व्यक्तियों के पारिश्रमिक संबंधी दिशानिर्देश _ Guidelines on Remuneration of Directors and Key Managerial Persons of Insurers
            - **Document ID:** 3562210
            - **URL:** https://irdai.gov.in/document-detail?documentId=3562210
            - **Expected Relevance Score:** > 0.90 (should be very high due to exact title match)
            
            This query tests the system's ability to find exact document matches with bilingual titles.
            """)
        
        # Chat input with enhanced handling
        if prompt := st.chat_input("Search for insurance documents, regulations, or specific IRDAI circulars..."):
            st.session_state.messages.append({"role": "user", "content": prompt})
            
            with st.chat_message("user"):
                st.markdown(prompt)
            
            with st.chat_message("assistant"):
                if st.session_state.rag_system:
                    response, search_type = perform_dynamic_search(
                        prompt, 
                        st.session_state.rag_system, 
                        st.session_state.scraper
                    )
                    
                    # Enhanced result display with production focus
                    if search_type == "perfect_match":
                        st.success("🎯 **PERFECT MATCH FOUND** - Exact document located!")
                    elif search_type == "database_search":
                        st.info("📚 **Database Results** - From document collection")
                    elif search_type == "deep_search":
                        st.success("🌐 **Deep Search Results** - Fresh from live websites")
                    elif search_type == "no_matches":
                        st.warning("❌ **No Matches Found** - Try rephrasing your query")
                    
                    st.markdown("### 🤖 **Answer**")
                    st.markdown(response.answer)
                    
                    # FIX: Add feedback buttons with unique keys using message count AND timestamp
                    if search_type == "database_search" and response.confidence_score > 0.8:
                        st.markdown("---")
                        st.markdown("**Is this result correct?**")
                        
                        # Generate unique key based on message count, query, and timestamp
                        import hashlib
                        key_base = f"{len(st.session_state.messages)}_{prompt}_{time.time()}"
                        unique_key = hashlib.md5(key_base.encode()).hexdigest()[:12]
                        
                        col1, col2 = st.columns(2)
                        
                        with col1:
                            if st.button("✅ Correct", key=f"main_correct_{unique_key}"):
                                st.success("Thank you for the feedback!")
                        
                        with col2:
                            if st.button("❌ Wrong - Need Fresh Search", key=f"main_wrong_{unique_key}"):
                                st.session_state.force_fresh_search = True
                                st.warning("Next query will use fresh search. Please ask your question again.")
                    
                    if response.sources:
                        st.markdown("### 🌐 **Source Websites**")
                        source_websites = list(set([source['url'] for source in response.sources]))
                        for website in source_websites:
                            st.markdown(f"- {website}")
                    
                    if response.sources:
                        all_doc_links = []
                        for source in response.sources:
                            if source.get('document_links'):
                                all_doc_links.extend(source['document_links'])
                        
                        if all_doc_links:
                            st.markdown("### 🔗 **Reference Document Links Summary**")
                            st.markdown(f"**Total Documents Found:** {len(all_doc_links)}")
                            
                            # Categorize all documents
                            document_detail_links = [doc for doc in all_doc_links if 'document-detail' in doc.lower()]
                            pdf_docs = [doc for doc in all_doc_links if doc.lower().endswith('.pdf')]
                            doc_docs = [doc for doc in all_doc_links if doc.lower().endswith(('.doc', '.docx'))]
                            
                            # Show key document categories
                            if document_detail_links:
                                st.markdown(f"**📋 IRDAI Document Detail Pages:** {len(document_detail_links)} found")
                                for doc in document_detail_links[:2]:
                                    doc_id_match = re.search(r'documentId=(\d+)', doc)
                                    if doc_id_match:
                                        doc_id = doc_id_match.group(1)
                                        st.markdown(f"- [📋 IRDAI Document ID: {doc_id}]({doc})")
                                    else:
                                        st.markdown(f"- [📋 IRDAI Document Detail]({doc})")
                            
                            if pdf_docs:
                                st.markdown(f"**📄 PDF Documents:** {len(pdf_docs)} found")
                                for doc in pdf_docs[:2]:
                                    doc_name = doc.split('/')[-1].replace('%20', ' ')
                                    if len(doc_name) > 40:
                                        doc_name = doc_name[:37] + "..."
                                    st.markdown(f"- [📄 {doc_name}]({doc})")
                            
                            if doc_docs:
                                st.markdown(f"**📝 Word Documents:** {len(doc_docs)} found")
                                for doc in doc_docs[:2]:
                                    doc_name = doc.split('/')[-1].replace('%20', ' ')
                                    if len(doc_name) > 40:
                                        doc_name = doc_name[:37] + "..."
                                    st.markdown(f"- [📝 {doc_name}]({doc})")
                            
                            if len(all_doc_links) > 6:
                                st.markdown(f"*... and {len(all_doc_links) - 6} more documents (see detailed sources below)*")
                            
                            # Add a note about document types
                            st.info("💡 **Document Types Explained:**\n"
                                   "- **📋 IRDAI Document Detail Pages**: Official IRDAI regulation/circular detail pages\n"
                                   "- **📄 PDF Documents**: Direct downloadable PDF files\n"
                                   "- **📝 Word Documents**: Direct downloadable DOC/DOCX files")
                        
                        else:
                            st.markdown("### 🔗 **Reference Document Links**")
                            st.markdown("*No specific document links found. Information sourced from main webpage content.*")
                    
                    # Display confidence score
                    st.markdown("### 📊 **Confidence Score**")
                    col1, col2 = st.columns([1, 2])
                    
                    with col1:
                        st.markdown(f"**Score:** {format_confidence_score(response.confidence_score)}", 
                                  unsafe_allow_html=True)
                    
                    with col2:
                        fig = create_confidence_gauge(response.confidence_score)
                        st.plotly_chart(fig, use_container_width=True)
                    
                    # Display detailed sources
                    if response.sources:
                        st.markdown("### 📚 **Detailed Sources**")
                        display_sources(response.sources)
                    
                    # Add to message history
                    assistant_response = f"""
**Answer:** {response.answer}

**Search Type:** {search_type.replace('_', ' ').title()}

**Confidence Score:** {response.confidence_score:.2f}

**Sources Found:** {len(response.sources)}
"""
                    st.session_state.messages.append({"role": "assistant", "content": assistant_response})
                else:
                    st.error("RAG system not initialized properly")

if __name__ == "__main__":
    main()