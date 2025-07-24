import openai
from openai import OpenAI
from typing import List, Dict, Any, Optional
from dataclasses import dataclass
from loguru import logger
from config import Config
from .vector_db import VectorDatabase

# Import our OpenAI wrapper
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'utils'))
from openai_client import get_openai_response

@dataclass
class RAGResponse:
    answer: str
    sources: List[Dict[str, Any]]
    confidence_score: float
    query: str

class RAGSystem:
    def __init__(self):
        self.config = Config()
        self.vector_db = VectorDatabase()
        
        # System prompt for the RAG system
        self.system_prompt = """
You are an expert assistant for IRDAI (Insurance Regulatory and Development Authority of India) and insurance company information. 

Your role is to:
1. Provide accurate, helpful answers based on the provided context
2. Always cite your sources when providing information
3. Clearly indicate when you don't have enough information
4. Focus on regulatory, policy, and insurance-related topics

Guidelines:
- Base your answers primarily on the provided context
- If context is insufficient, say so clearly
- Include relevant document links when available
- Maintain professional, informative tone
- Use specific details from the context when possible

Context will be provided below, followed by the user's question.
"""
        
    def retrieve_relevant_context(self, query: str, filters: Dict[str, Any] = None) -> List[Dict[str, Any]]:
        """Retrieve relevant context from vector database"""
        logger.info(f"Retrieving context for query: {query}")
        
        if filters:
            results = self.vector_db.search_with_filters(query, filters)
        else:
            results = self.vector_db.search_similar(query)
            
        return results
        
    def format_context(self, search_results: List[Dict[str, Any]]) -> str:
        """Format search results into context string"""
        if not search_results:
            return "No relevant context found."
            
        context = "RELEVANT INFORMATION:\n\n"
        
        for i, result in enumerate(search_results, 1):
            context += f"Source {i}:\n"
            context += f"URL: {result['metadata'].get('source_url', 'N/A')}\n"
            context += f"Title: {result['metadata'].get('source_title', 'N/A')}\n"
            context += f"Type: {result['metadata'].get('source_type', 'N/A')}\n"
            context += f"Content: {result['content']}\n"
            
            # Add document links if available
            doc_links = result['metadata'].get('document_links', [])
            if doc_links:
                context += f"Document Links: {', '.join(doc_links)}\n"
                
            context += f"Relevance Score: {result['similarity_score']:.3f}\n"
            context += "-" * 50 + "\n\n"
            
        return context
        
    def generate_response(self, query: str, context: str) -> str:
        """Generate response using OpenAI"""
        try:
            # Check if OpenAI API key is available
            if not self.config.OPENAI_API_KEY or self.config.OPENAI_API_KEY == "your_openai_api_key_here":
                return "OpenAI API key not configured. Please add your API key to the .env file."
            
            messages = [
                {"role": "system", "content": self.system_prompt},
                {"role": "user", "content": f"Context:\n{context}\n\nQuestion: {query}"}
            ]
            
            # Use our compatibility wrapper
            response = get_openai_response(messages, self.config.OPENAI_API_KEY)
            
            return response
            
        except Exception as e:
            logger.error(f"Error generating response: {e}")
            return "I apologize, but I'm unable to generate a response at this time. Please try again later."
            
    def calculate_confidence_score(self, search_results: List[Dict[str, Any]], query: str) -> float:
        """Calculate confidence score for the response"""
        if not search_results:
            return 0.0
            
        # Base confidence on similarity scores
        avg_similarity = sum(result['similarity_score'] for result in search_results) / len(search_results)
        
        # Boost confidence if we have multiple relevant sources
        source_bonus = min(len(search_results) * 0.1, 0.3)
        
        # Boost confidence if we have document links
        doc_links_bonus = 0.0
        for result in search_results:
            if result['metadata'].get('document_links'):
                doc_links_bonus += 0.1
                
        doc_links_bonus = min(doc_links_bonus, 0.2)
        
        final_confidence = min(avg_similarity + source_bonus + doc_links_bonus, 1.0)
        return final_confidence
        
    def extract_sources(self, search_results: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Extract source information from search results"""
        sources = []
        
        for result in search_results:
            source = {
                'url': result['metadata'].get('source_url', ''),
                'title': result['metadata'].get('source_title', ''),
                'source_type': result['metadata'].get('source_type', ''),
                'document_links': result['metadata'].get('document_links', []),
                'relevance_score': result['similarity_score'],
                'snippet': result['content'][:200] + "..." if len(result['content']) > 200 else result['content']
            }
            sources.append(source)
            
        return sources
        
    def query(self, user_query: str, filters: Dict[str, Any] = None) -> RAGResponse:
        """Main query method"""
        logger.info(f"Processing query: {user_query}")
        
        # Retrieve relevant context
        search_results = self.retrieve_relevant_context(user_query, filters)
        
        # Format context
        context = self.format_context(search_results)
        
        # Generate response
        answer = self.generate_response(user_query, context)
        
        # Calculate confidence score
        confidence_score = self.calculate_confidence_score(search_results, user_query)
        
        # Extract sources
        sources = self.extract_sources(search_results)
        
        return RAGResponse(
            answer=answer,
            sources=sources,
            confidence_score=confidence_score,
            query=user_query
        )
        
    def query_by_source_type(self, user_query: str, source_type: str) -> RAGResponse:
        """Query filtered by source type"""
        filters = {'source_type': source_type}
        return self.query(user_query, filters)
        
    def query_regulatory_content(self, user_query: str) -> RAGResponse:
        """Query specifically for regulatory content"""
        filters = {'document_category': 'regulatory'}
        return self.query(user_query, filters)
        
    def query_with_enhanced_context(self, user_query: str) -> RAGResponse:
        """Query with enhanced context including related terms"""
        # Add related insurance terms to improve search
        enhanced_query = user_query
        
        insurance_terms = {
            'latest': ['recent', 'new', 'updated', 'current'],
            'act': ['regulation', 'law', 'policy', 'guideline'],
            'insurance': ['IRDAI', 'regulatory', 'policy', 'premium'],
            'update': ['amendment', 'revision', 'change', 'notification']
        }
        
        for key, related_terms in insurance_terms.items():
            if key.lower() in user_query.lower():
                enhanced_query += f" {' '.join(related_terms)}"
                
        return self.query(enhanced_query)
        
    def get_system_stats(self) -> Dict[str, Any]:
        """Get system statistics"""
        db_stats = self.vector_db.get_collection_stats()
        return {
            'vector_db_stats': db_stats,
            'embedding_model': self.config.EMBEDDING_MODEL,
            'chunk_size': self.config.CHUNK_SIZE,
            'top_k_results': self.config.TOP_K_RESULTS
        }