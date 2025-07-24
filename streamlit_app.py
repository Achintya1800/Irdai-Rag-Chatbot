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
import hashlib
import uuid

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
    body {
        background-color: #000000;
        color: #FFFFFF;
    }
    .main-header {
        background: linear-gradient(90deg, #000000 0%, #000000 100%);
        padding: 2rem;
        border-radius: 10px;
        margin-bottom: 2rem;
        text-align: center;
        color: #FFFFFF;
    }
    
    .stats-card {
        background: #1E1E1E;
        padding: 1.5rem;
        border-radius: 10px;
        box-shadow: 0 2px 4px rgba(255,255,255,0.1);
        border-left: 4px solid #FFFFFF;
        margin-bottom: 1rem;
        color: #FFFFFF;
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
        background-color: #333333;
        color: #FFFFFF;
        border: none;
        border-radius: 5px;
        padding: 0.5rem 1rem;
        font-weight: bold;
    }
    
    .stButton > button:hover {
        background-color: #555555;
    }
    
    .status-success {
        background-color: #155724;
        border: 1px solid #c3e6cb;
        color: #d4edda;
    }
    
    .status-warning {
        background-color: #856404;
        border: 1px solid #ffeaa7;
        color: #fff3cd;
    }
    
    .status-error {
        background-color: #721c24;
        border: 1px solid #f5c6cb;
        color: #f8d7da;
    }

    .streamlit-expanderHeader {
        color: #FFFFFF;
    }

    .streamlit-expanderContent {
        color: #FFFFFF;
    }
</style>
""", unsafe_allow_html=True)

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
            import traceback
            error_details = traceback.format_exc()
            setup_status.error(f"Error details: {error_details}")
            return False, f"Setup error: {e}"

@st.cache_resource
def initialize_complete_system():
    """Initialize the complete system with caching"""
    try:
        vector_db = VectorDatabase()
        stats = vector_db.get_collection_stats()
        if stats.get('total_documents', 0) > 0:
            return RAGSystem(), True, "System already ready"
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
        return f'<span class="confidence-low">{score:.2f}</span>'

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
                
                st.markdown(f"**📝 Content Preview:**")
                st.markdown(f"_{source['snippet']}_")
                
            with col2:
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
                st.plotly_chart(mini_fig, use_container_width=True, key=f"relevance_gauge_{i}_{hash(source['url']) % 10000}")
            
            # Display reference document links
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
                
                # Display document detail pages
                if document_detail_links:
                    st.markdown("**📋 IRDAI Document Detail Pages:**")
                    for doc_link in document_detail_links[:5]:
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

def perform_dynamic_search(query: str, rag_system, scraper):
    """Enhanced search with better handling"""
    query_lower = query.lower().strip()
    
    force_fresh = st.session_state.get('force_fresh_search', False)
    
    irdai_specific_terms = [
        "reconstitution", "inter-disciplinary", "standing committee", "cyber security",
        "rules", "act", "regulation", "circular", "notification", 
        "guideline", "procedure", "inquiry", "adjudicating", "officer",
        "annulment", "expression of interest", "empanelment", "advertising agencies"
    ]
    
    should_deep_search = (
        force_fresh or
        any(term in query_lower for term in irdai_specific_terms) or
        "insurance" in query_lower or
        "irdai" in query_lower or
        re.search(r'\b20\d{2}\b', query) or
        len(query.split()) > 4
    )
    
    try:
        # Try database first unless forced fresh search
        database_response = None
        if not force_fresh and rag_system:
            try:
                database_response = rag_system.query(query)
                confidence_threshold = 0.3 if any(term in query_lower for term in ["annulment", "expression of interest"]) else 0.5
                
                if database_response.confidence_score >= confidence_threshold and len(database_response.sources) > 0:
                    st.info("📚 **Database Results** - Found relevant information in existing collection")
                    
                    unique_id = hashlib.md5(f"{query}_{time.time()}_{len(st.session_state.messages)}".encode()).hexdigest()[:12]
                    
                    col1, col2 = st.columns(2)
                    with col1:
                        if st.button("✅ This is correct", key=f"db_correct_{unique_id}"):
                            st.success("Thank you for the feedback!")
                            return database_response, "database_confirmed"
                    
                    with col2:
                        if st.button("❌ This is wrong - Do deep search", key=f"db_wrong_{unique_id}"):
                            st.session_state.force_fresh_search = True
                            st.warning("🔍 Performing deep search...")
                        else:
                            return database_response, "database_search"
            except Exception as e:
                st.error(f"Database search error: {e}")
        
        # Perform deep search if needed
        if should_deep_search or force_fresh or not database_response:
            st.info(f"🔍 **Deep Recursive Search** - Comprehensive scraping for: '{query}'")
            
            if scraper:
                with st.spinner("🌐 Performing deep recursive search..."):
                    scraped_documents = scraper.scrape_all_websites_comprehensive(query)
                    
                    if scraped_documents:
                        # Check for perfect matches
                        perfect_matches = [doc for doc in scraped_documents if doc.metadata.get('relevance_score', 0) >= 0.99]
                        
                        if perfect_matches:
                            st.success(f"🎯 **PERFECT MATCH FOUND!** Found {len(perfect_matches)} exact match(es)!")
                            perfect_doc = perfect_matches[0]
                            
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
"""
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
                            
                            return PerfectMatchResponse(perfect_doc), "perfect_match"
                        
                        st.success(f"🎯 Deep search found {len(scraped_documents)} relevant documents!")
                        
                        # Process and add to database if available
                        if rag_system:
                            try:
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
                                scraped_content.sort(key=lambda x: x.metadata.get('relevance_score', 0), reverse=True)
                                
                                all_chunks = []
                                query_hash = hashlib.md5(query.encode()).hexdigest()[:8]
                                
                                for content in scraped_content[:50]:
                                    try:
                                        chunks = processor.process_scraped_content([content])
                                        enriched_chunks = processor.enrich_metadata(chunks)
                                        
                                        for chunk in enriched_chunks:
                                            chunk_id = getattr(chunk, 'id', None) or getattr(chunk, 'chunk_id', None)
                                            if not chunk_id:
                                                new_id = f"q_{query_hash}_{uuid.uuid4().hex[:8]}"
                                                if hasattr(chunk, 'id'):
                                                    chunk.id = new_id
                                                elif hasattr(chunk, 'chunk_id'):
                                                    chunk.chunk_id = new_id
                                            all_chunks.append(chunk)
                                    except Exception as e:
                                        continue
                                
                                if all_chunks:
                                    vector_db = VectorDatabase()
                                    vector_db.add_documents(all_chunks)
                                    st.success(f"✅ Successfully added {len(all_chunks)} new document chunks to search index")
                                    
                                    updated_response = rag_system.query(query)
                                    return updated_response, "deep_search"
                            except Exception as e:
                                st.error(f"Error processing documents: {e}")
                        
                        # Return simple response if no RAG system
                        best_doc = scraped_documents[0]
                        class SimpleResponse:
                            def __init__(self, doc):
                                self.answer = f"**Found: {doc.title}**\n\n{doc.content[:500]}..."
                                self.confidence_score = doc.metadata.get('relevance_score', 0.5)
                                self.sources = [{
                                    'title': doc.title,
                                    'url': doc.url,
                                    'source_type': doc.source_type,
                                    'relevance_score': doc.metadata.get('relevance_score', 0.5),
                                    'snippet': doc.content[:300],
                                    'document_links': getattr(doc, 'document_links', [])
                                }]
                        
                        return SimpleResponse(best_doc), "scraper_only"
                    else:
                        class EmptyResponse:
                            def __init__(self):
                                self.answer = f"No documents found for '{query}'. Please try rephrasing your query or check the IRDAI website directly."
                                self.confidence_score = 0.0
                                self.sources = []
                        return EmptyResponse(), "no_matches_found"
            else:
                st.warning("Real-time scraper not available")
        
        # Fallback to database response
        if database_response:
            return database_response, "static_db"
        else:
            class FallbackResponse:
                def __init__(self):
                    self.answer = f"I apologize, but I couldn't find information about '{query}'. Please try rephrasing your question."
                    self.confidence_score = 0.0
                    self.sources = []
            return FallbackResponse(), "error"
            
    except Exception as e:
        st.error(f"Error in dynamic search: {e}")
        class ErrorResponse:
            def __init__(self):
                self.answer = f"I apologize, but I encountered an error while searching for information about '{query}'. Please try rephrasing your question."
                self.confidence_score = 0.0
                self.sources = []
        return ErrorResponse(), "error"

def create_analytics_dashboard():
    """Create analytics dashboard"""
    st.header("📊 System Analytics")
    
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

def initialize_session_state():
    """Initialize all session state variables"""
    if 'messages' not in st.session_state:
        st.session_state.messages = []
    if 'system_ready' not in st.session_state:
        st.session_state.system_ready = False
    if 'setup_attempted' not in st.session_state:
        st.session_state.setup_attempted = False
    if 'force_fresh_search' not in st.session_state:
        st.session_state.force_fresh_search = False
    if 'search_mode' not in st.session_state:
        st.session_state.search_mode = 'Smart Search (Recommended)'
    if 'urgency_level' not in st.session_state:
        st.session_state.urgency_level = 'medium'
    if 'max_documents' not in st.session_state:
        st.session_state.max_documents = 50
    if 'confidence_threshold' not in st.session_state:
        st.session_state.confidence_threshold = 0.5
    if 'enable_early_stopping' not in st.session_state:
        st.session_state.enable_early_stopping = True

def main():
    """Enhanced main interface with comprehensive features"""
    
    # Initialize session state
    initialize_session_state()
    
    # Header
    st.markdown("""
    <div class="main-header">
        <h1>🏛️ IRDAI RAG System - Enhanced Agentic Version</h1>
        <p>Intelligent Insurance Document Search with User Intent Analysis</p>
        <p><em>AI-powered query understanding and smart document retrieval</em></p>
    </div>
    """, unsafe_allow_html=True)

    # Enhanced sidebar
    with st.sidebar:
        st.header("🧠 Intelligent Search System")
        
        # System capabilities overview
        st.markdown("""
        <div class="stats-card">
            <h4>🎯 Agentic Features Active</h4>
            <ul>
                <li>✅ Query Intent Analysis</li>
                <li>✅ Smart Document Routing</li>
                <li>✅ Relevance Scoring</li>
                <li>✅ Quality Guard Rails</li>
                <li>✅ User Guidance System</li>
            </ul>
        </div>
        """, unsafe_allow_html=True)
        
        # Query examples
        st.markdown("### 🎯 **Smart Query Examples**")
        
        intent_examples = {
            "Latest Documents": [
                "Latest guidelines",
                "Recent IRDAI circulars 2024",
                "Updated regulations 2025"
            ],
            "Specific Document": [
                "Guidelines on Remuneration of Directors",
                "Insurance Adjudicating Officer Rules 2016"
            ],
            "Regulatory Guidance": [
                "ULIP regulations compliance",
                "Motor insurance third party liability"
            ]
        }
        
        for intent_type, examples in intent_examples.items():
            with st.expander(f"📋 {intent_type}", expanded=False):
                for example in examples:
                    if st.button(f"🔍 {example[:40]}...", key=f"intent_{hash(example) % 10000}"):
                        st.session_state.messages.append({"role": "user", "content": example})
                        st.rerun()
        
        # Search controls
        st.markdown("### 🔧 **Search Intelligence Controls**")
        
        manual_intent = st.selectbox(
            "Override Query Intent (Optional):",
            ["Auto-Detect", "Specific Document", "Latest Updates", "Regulatory Guidance", "General Search"],
            help="Force a specific search strategy"
        )
        
        if manual_intent != "Auto-Detect":
            st.session_state.manual_intent = manual_intent.lower().replace(" ", "_")
        else:
            st.session_state.manual_intent = None
        
        urgency_level = st.select_slider(
            "Search Urgency:",
            options=["Low", "Medium", "High", "Critical"],
            value="Medium",
            help="Higher urgency enables faster response modes"
        )
        st.session_state.urgency_level = urgency_level.lower()
        
        # Advanced options
        with st.expander("⚙️ Advanced Options", expanded=False):
            st.session_state.max_documents = st.slider("Max Documents to Process:", 10, 100, 50)
            st.session_state.confidence_threshold = st.slider("Confidence Threshold:", 0.1, 1.0, 0.5, 0.1)
            st.session_state.enable_early_stopping = st.checkbox("Enable Early Stopping", value=True)
        
        # System initialization
        st.markdown("### 🔧 **System Setup**")
        
        if not st.session_state.system_ready and not st.session_state.setup_attempted:
            if st.button("🚀 **Initialize System**", type="primary"):
                with st.spinner("Initializing system..."):
                    st.session_state.setup_attempted = True
                    success, message = integrated_system_setup()
                    if success:
                        st.session_state.system_ready = True
                        st.success("System ready!")
                        st.rerun()
                    else:
                        st.error(f"Setup failed: {message}")
        elif st.session_state.system_ready:
            st.success("🤖 **System Ready**")
            if st.button("🔄 **Reinitialize System**"):
                st.session_state.system_ready = False
                st.session_state.setup_attempted = False
                st.rerun()
        elif st.session_state.setup_attempted and not st.session_state.system_ready:
            st.warning("⚠️ System initialization failed")
            if st.button("🔄 **Retry Setup**"):
                st.session_state.setup_attempted = False
                st.rerun()
        
        # System status
        st.header("🎯 Production System")
        
        if st.session_state.system_ready:
            st.markdown("""
            <div class="stats-card status-success">
                <h4>📊 Status: ✅ PRODUCTION READY</h4>
                <p><strong>Mode:</strong> Live Search</p>
                <p><strong>Sources:</strong> Real websites</p>
            </div>
            """, unsafe_allow_html=True)
        else:
            st.markdown("""
            <div class="stats-card status-warning">
                <h4>📊 Status: ⚠️ SETUP REQUIRED</h4>
                <p><strong>Mode:</strong> Limited functionality</p>
                <p><strong>Action:</strong> Click Initialize System above</p>
            </div>
            """, unsafe_allow_html=True)
        
        # Search mode
        st.markdown("### 🔧 **Search Mode**")
        search_mode = st.radio(
            "Search preference:",
            ["Smart Search (Recommended)", "IRDAI Only", "Database Only"],
            help="Smart Search uses real-time scraping for best results"
        )
        st.session_state.search_mode = search_mode
        
        # Test queries
        st.markdown("💡 **Test Queries:**")
        production_queries = [
            "Latest guidelines",
            "Recent IRDAI circulars 2024",
            "Guidelines on Remuneration of Directors",
            "ULIP regulations 2024",
            "Motor vehicle insurance rules"
        ]
        
        for query in production_queries:
            if st.button(f"🔍 {query[:50]}...", key=f"prod_{hash(query) % 10000}"):
                st.session_state.messages.append({"role": "user", "content": query})
                st.rerun()
        
        # Search controls
        st.markdown("### 🔧 **Search Controls**")
        
        if st.button("🔄 **Force Deep Search Next Query**"):
            st.session_state.force_fresh_search = True
            st.success("Next query will perform deep recursive search!")
        
        if st.button("🧹 **Clear Search Cache**"):
            st.session_state.force_fresh_search = False
            st.success("Search cache cleared!")
        
        if st.session_state.get('force_fresh_search', False):
            st.warning("⚡ **Deep Search Mode Active**")

    # Initialize systems
    if not hasattr(st.session_state, 'rag_system') or st.session_state.rag_system is None:
        try:
            st.session_state.rag_system, ready, status = initialize_complete_system()
            if not ready:
                st.session_state.rag_system = None
        except Exception as e:
            st.session_state.rag_system = None

    if not hasattr(st.session_state, 'scraper') or st.session_state.scraper is None:
        st.session_state.scraper = initialize_comprehensive_scraper()
    
    # Main interface
    st.header("💬 Enhanced Document Search")
    
    # Show current mode
    current_mode = st.session_state.get('search_mode', 'Smart Search (Recommended)')
    if current_mode == "Smart Search (Recommended)":
        st.info("🧠 **Smart Search Mode** - Uses real-time scraping for regulatory queries, database for general queries")
    elif current_mode == "IRDAI Only":
        st.info("🎯 **IRDAI Only Mode** - Real-time search of IRDAI website for every query")
    else:
        st.info("📚 **Database Only Mode** - Uses existing document collection")
    
    # System status indicator
    if not st.session_state.system_ready:
        st.warning("⚠️ **System not fully initialized** - Basic search available, full features require initialization.")
    
    # Test case preview
    with st.expander("🎯 **Test Case: Latest Guidelines**", expanded=False):
        st.markdown("""
        **Test Query:** "Latest guidelines"
        
        **Expected Top Results:**
        1. **Guidelines on Hedging Through Equity Derivatives** (Updated: 28-02-2025)
        2. **IRDAI Bima Vahak Guidelines, 2023** (Updated: 09-10-2023)  
        3. **Guidelines on Remuneration of Directors** (Updated: 30-06-2023)
        
        This query tests the system's ability to identify and prioritize recent documents.
        """)
    
    # Search interface
    st.markdown("### 🔍 **Search Interface**")
    
    # Chat input
    prompt = st.chat_input("🔍 Search for insurance documents, regulations, or specific IRDAI circulars...")
    
    if prompt:
        st.session_state.messages.append({"role": "user", "content": prompt})
        
        with st.chat_message("user"):
            st.markdown(prompt)
        
        with st.chat_message("assistant"):
            try:
                # Use scraper for real-time search
                if st.session_state.scraper:
                    st.info("🌐 **Real-time Search** - Searching IRDAI website directly...")
                    
                    with st.spinner("Searching IRDAI database..."):
                        scraped_documents = st.session_state.scraper.scrape_all_websites_comprehensive(prompt)
                        
                        if scraped_documents:
                            st.success(f"✅ Found {len(scraped_documents)} relevant documents!")
                            
                            best_doc = scraped_documents[0]
                            relevance = best_doc.metadata.get('relevance_score', 0)
                            doc_id = best_doc.metadata.get('document_id', 'N/A')
                            
                            answer = f"""**Document Found: {best_doc.title}**

**Relevance Score:** {relevance:.3f}
**Document ID:** {doc_id}
**Source:** {best_doc.url}

**Summary:**
{best_doc.content[:1000]}{'...' if len(best_doc.content) > 1000 else ''}

This document was found through real-time search of the IRDAI website."""
                            
                            st.markdown("### 🤖 **Answer**")
                            st.markdown(answer)
                            
                            # Show top matches
                            st.markdown("### 📋 **Top Matches Found**")
                            for i, doc in enumerate(scraped_documents[:5], 1):
                                rel_score = doc.metadata.get('relevance_score', 0)
                                d_id = doc.metadata.get('document_id', 'N/A')
                                st.markdown(f"{i}. **{doc.title[:80]}...** (Score: {rel_score:.3f}, ID: {d_id})")
                                st.markdown(f"   🔗 [View Document]({doc.url})")
                            
                            assistant_response = f"Found {len(scraped_documents)} documents for '{prompt}'. Top match: {best_doc.title} (Score: {relevance:.3f})"
                            st.session_state.messages.append({"role": "assistant", "content": assistant_response})
                        else:
                            st.warning("❌ No documents found. Try rephrasing your query.")
                            st.session_state.messages.append({"role": "assistant", "content": f"No results found for '{prompt}'"})
                
                # Fallback to RAG system
                elif st.session_state.rag_system:
                    st.info("📚 **Database Search** - Searching existing document collection...")
                    
                    response, search_type = perform_dynamic_search(
                        prompt, 
                        st.session_state.rag_system, 
                        st.session_state.scraper
                    )
                    
                    st.markdown("### 🤖 **Answer**")
                    st.markdown(response.answer)
                    
                    if hasattr(response, 'sources') and response.sources:
                        st.markdown("### 📚 **Sources**")
                        display_sources(response.sources)
                    
                    st.session_state.messages.append({"role": "assistant", "content": response.answer})
                
                else:
                    st.error("🚫 **System Not Available**")
                    fallback_message = f"""
I apologize, but the search system is not currently available for your query: "{prompt}"

**What you can do:**
1. **Initialize the system** using the "Initialize System" button in the sidebar
2. **Check your internet connection** for real-time search
3. **Try again** after initialization completes

**For immediate access to IRDAI documents:**
- [IRDAI Official Website](https://irdai.gov.in)
- [IRDAI Regulations](https://irdai.gov.in/consolidated-gazette-notified-regulations)
- [IRDAI Circulars](https://irdai.gov.in/circulars)
"""
                    st.markdown(fallback_message)
                    st.session_state.messages.append({"role": "assistant", "content": fallback_message})
                
            except Exception as e:
                st.error(f"🚫 **Search Error:** {e}")
                error_message = f"""
An error occurred while processing your query: "{prompt}"

**Error Details:** {str(e)}

**Possible solutions:**
1. Try rephrasing your query
2. Initialize the system using the sidebar button
3. Check your internet connection
4. Refresh the page and try again
"""
                st.markdown(error_message)
                st.session_state.messages.append({"role": "assistant", "content": f"Error processing '{prompt}': {str(e)}"})
    
    # Display chat history
    if st.session_state.messages:
        st.markdown("---")
        st.markdown("### 💬 **Chat History**")
        
        for i, message in enumerate(st.session_state.messages[-10:]):
            with st.expander(f"{message['role'].title()} - Message {len(st.session_state.messages) - 10 + i + 1}", expanded=False):
                st.markdown(message['content'])
        
        if st.button("🧹 **Clear Chat History**"):
            st.session_state.messages = []
            st.rerun()

if __name__ == "__main__":
    main()