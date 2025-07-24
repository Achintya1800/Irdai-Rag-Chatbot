import openai
from openai import OpenAI
from typing import List, Dict, Any, Optional
from dataclasses import dataclass
from loguru import logger
import re  # Added re import
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
        
        # Enhanced system prompt for agentic behavior
        self.system_prompt = """
You are an expert assistant for IRDAI (Insurance Regulatory and Development Authority of India) and insurance company information with enhanced intelligence.

Your enhanced capabilities include:
1. **Intent Recognition**: Understanding user query intent and context
2. **Precise Information Retrieval**: Providing accurate, source-backed answers
3. **Proactive Guidance**: Offering suggestions when information is incomplete
4. **Quality Validation**: Ensuring response accuracy and relevance
5. **User Education**: Explaining complex insurance regulations clearly

Response Guidelines:
- ALWAYS base answers on provided context - never make up information
- Clearly indicate confidence levels in your responses  
- Provide specific document references when available
- Offer related search suggestions when appropriate
- Use clear, professional language suitable for both experts and general users
- Include relevant document links and IDs when available
- Explain regulatory concepts in understandable terms

Context Quality Indicators:
- High quality context: Recent documents, exact matches, official IRDAI sources
- Medium quality context: Related documents, partial matches, indirect sources  
- Low quality context: General information, older documents, tangential matches

Always indicate your confidence based on context quality and relevance.
"""
        
    def analyze_query_complexity(self, query: str) -> Dict[str, Any]:
        """Analyze query complexity and characteristics"""
        words = query.split()
        query_lower = query.lower()
        
        analysis = {
            'word_count': len(words),
            'char_count': len(query),
            'has_year': bool(re.search(r'\b20\d{2}\b', query)),
            'has_document_id': 'document' in query_lower and any(char.isdigit() for char in query),
            'has_regulation_terms': any(term in query_lower for term in ['regulation', 'circular', 'guideline', 'act', 'rule']),
            'has_time_indicators': any(term in query_lower for term in ['latest', 'recent', 'new', 'current', 'updated']),
            'has_specific_terms': any(term in query_lower for term in ['irdai', 'insurance', 'policy', 'premium']),
            'complexity_score': len(words) / 20.0  # Normalized complexity score
        }
        
        # Determine query intent
        if analysis['word_count'] > 8 and analysis['has_regulation_terms']:
            analysis['suggested_intent'] = 'specific_document'
        elif analysis['has_time_indicators']:
            analysis['suggested_intent'] = 'latest_updates'
        elif analysis['has_regulation_terms']:
            analysis['suggested_intent'] = 'regulatory_guidance'
        else:
            analysis['suggested_intent'] = 'general_search'
        
        return analysis
    
    def retrieve_relevant_context(self, query: str, filters: Dict[str, Any] = None) -> List[Dict[str, Any]]:
        """Retrieve relevant context from vector database"""
        logger.info(f"Retrieving context for query: {query}")
        
        if filters:
            results = self.vector_db.search_with_filters(query, filters)
        else:
            results = self.vector_db.search_similar(query)
            
        return results
        
    def validate_search_results(self, results: List[Dict[str, Any]], query: str) -> List[Dict[str, Any]]:
        """Enhanced validation of search results with quality scoring"""
        validated_results = []
        query_lower = query.lower()
        
        for result in results:
            # Calculate quality score
            quality_score = result['similarity_score']
            
            # Boost for exact term matches
            content_lower = result['content'].lower()
            query_words = [word for word in query_lower.split() if len(word) > 3]
            
            exact_matches = sum(1 for word in query_words if word in content_lower)
            if query_words:
                exact_match_ratio = exact_matches / len(query_words)
                quality_score += exact_match_ratio * 0.2
            
            # Boost for official sources
            source_url = result['metadata'].get('source_url', '')
            if 'irdai.gov.in' in source_url:
                quality_score += 0.1
            
            # Boost for document links
            if result['metadata'].get('document_links'):
                quality_score += 0.1
            
            # Boost for recent content
            if any(year in result['content'] for year in ['2023', '2024', '2025']):
                quality_score += 0.05
            
            # Apply validation filters
            if quality_score >= 0.3:  # Minimum quality threshold
                result['quality_score'] = min(quality_score, 1.0)
                validated_results.append(result)
        
        # Sort by quality score
        validated_results.sort(key=lambda x: x['quality_score'], reverse=True)
        
        return validated_results
    
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
            
    def generate_enhanced_response(self, query: str, context: str, query_analysis: Dict) -> str:
        """Generate enhanced response with better prompting"""
        try:
            if not self.config.OPENAI_API_KEY or self.config.OPENAI_API_KEY == "your_openai_api_key_here":
                return self.generate_fallback_response(query, context, query_analysis)
            
            # Enhanced prompt based on query analysis
            enhanced_prompt = self.system_prompt + f"""

Query Analysis:
- Intent: {query_analysis.get('suggested_intent', 'general')}
- Complexity: {query_analysis.get('complexity_score', 0):.2f}
- Has Regulation Terms: {query_analysis.get('has_regulation_terms', False)}
- Has Time Indicators: {query_analysis.get('has_time_indicators', False)}
- Query Length: {query_analysis.get('word_count', 0)} words

Please provide a comprehensive response that:
1. Directly addresses the user's query intent
2. Uses specific information from the provided context
3. Includes document references when available
4. Indicates your confidence level
5. Suggests related searches if appropriate
"""
            
            messages = [
                {"role": "system", "content": enhanced_prompt},
                {"role": "user", "content": f"Context:\n{context}\n\nQuestion: {query}"}
            ]
            
            response = get_openai_response(messages, self.config.OPENAI_API_KEY)
            return response
            
        except Exception as e:
            logger.error(f"Error generating enhanced response: {e}")
            return self.generate_fallback_response(query, context, query_analysis)
    
    def generate_fallback_response(self, query: str, context: str, query_analysis: Dict) -> str:
        """Generate fallback response when OpenAI is not available"""
        if not context or context == "No relevant context found.":
            return f"""I couldn't find specific information about "{query}" in the available documents.

**Suggestions:**
1. Try using different or more general keywords
2. Check the official IRDAI website: https://irdai.gov.in
3. Look for related regulations or circulars
4. Contact IRDAI directly for specific queries

**Query Analysis:**
- Type: {query_analysis.get('suggested_intent', 'general').replace('_', ' ').title()}
- Complexity: {'High' if query_analysis.get('complexity_score', 0) > 0.4 else 'Medium' if query_analysis.get('complexity_score', 0) > 0.2 else 'Low'}
"""
        
        # Extract key information from context
        lines = context.split('\n')
        key_info = []
        sources = []
        
        for line in lines:
            if line.startswith('URL:'):
                sources.append(line.replace('URL:', '').strip())
            elif line.startswith('Content:') and len(line) > 50:
                key_info.append(line.replace('Content:', '').strip()[:200] + "...")
        
        response = f"""Based on the available information about "{query}":

**Key Information Found:**
"""
        
        for i, info in enumerate(key_info[:3], 1):
            response += f"{i}. {info}\n\n"
        
        if sources:
            response += "**Sources:**\n"
            for source in sources[:3]:
                response += f"- {source}\n"
        
        response += f"""
**Query Analysis:**
- Intent: {query_analysis.get('suggested_intent', 'general').replace('_', ' ').title()}
- Found relevant content: {'Yes' if key_info else 'Limited'}

**Note:** This response is generated from document analysis. For the most current information, please visit the official IRDAI website.
"""
        
        return response
    
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
        
    def calculate_enhanced_confidence_score(self, search_results: List[Dict[str, Any]], 
                                          query: str, query_analysis: Dict) -> float:
        """Enhanced confidence scoring with multiple factors"""
        if not search_results:
            return 0.0
        
        # Base confidence from similarity scores
        avg_similarity = sum(result.get('quality_score', result['similarity_score']) 
                           for result in search_results) / len(search_results)
        
        confidence = avg_similarity
        
        # Boost for query-specific factors
        if query_analysis.get('has_regulation_terms') and any('regulation' in result['content'].lower() 
                                                            for result in search_results):
            confidence += 0.1
        
        if query_analysis.get('has_specific_terms') and any('irdai' in result['content'].lower() 
                                                          for result in search_results):
            confidence += 0.1
        
        # Boost for multiple high-quality sources
        high_quality_sources = sum(1 for result in search_results 
                                 if result.get('quality_score', result['similarity_score']) > 0.7)
        if high_quality_sources >= 2:
            confidence += 0.15
        elif high_quality_sources >= 1:
            confidence += 0.1
        
        # Boost for official sources
        official_sources = sum(1 for result in search_results 
                             if 'irdai.gov.in' in result['metadata'].get('source_url', ''))
        if official_sources > 0:
            confidence += 0.1
        
        # Boost for document links
        with_doc_links = sum(1 for result in search_results 
                           if result['metadata'].get('document_links'))
        if with_doc_links > 0:
            confidence += 0.1
        
        # Apply intent-based adjustments
        intent = query_analysis.get('suggested_intent', 'general')
        if intent == 'specific_document' and high_quality_sources >= 1:
            confidence += 0.1
        elif intent == 'latest_updates' and any('2024' in result['content'] or '2025' in result['content'] 
                                              for result in search_results):
            confidence += 0.1
        
        return min(confidence, 1.0)
    
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
        
    def extract_enhanced_sources(self, search_results: List[Dict[str, Any]], 
                                query_analysis: Dict) -> List[Dict[str, Any]]:
        """Extract enhanced source information"""
        sources = []
        
        for result in search_results:
            quality_score = result.get('quality_score', result['similarity_score'])
            
            source = {
                'url': result['metadata'].get('source_url', ''),
                'title': result['metadata'].get('source_title', ''),
                'source_type': result['metadata'].get('source_type', ''),
                'document_links': result['metadata'].get('document_links', []),
                'relevance_score': result['similarity_score'],
                'quality_score': quality_score,
                'snippet': result['content'][:300] + "..." if len(result['content']) > 300 else result['content'],
                'document_id': result['metadata'].get('document_id', ''),
                'is_official_source': 'irdai.gov.in' in result['metadata'].get('source_url', ''),
                'has_document_links': bool(result['metadata'].get('document_links')),
                'content_length': len(result['content']),
                'query_intent_match': query_analysis.get('suggested_intent', 'general')
            }
            sources.append(source)
        
        return sources
    
    def query(self, user_query: str, filters: Dict[str, Any] = None) -> RAGResponse:
        """Enhanced main query method with comprehensive analysis"""
        logger.info(f"Processing enhanced query: {user_query}")
        
        # Analyze query
        query_analysis = self.analyze_query_complexity(user_query)
        
        # Retrieve relevant context with enhanced search
        search_results = self.retrieve_relevant_context(user_query, filters)
        
        # Validate and enhance search results
        validated_results = self.validate_search_results(search_results, user_query)
        
        # Format context
        context = self.format_enhanced_context(validated_results, query_analysis)
        
        # Generate enhanced response
        answer = self.generate_enhanced_response(user_query, context, query_analysis)
        
        # Calculate enhanced confidence score
        confidence_score = self.calculate_enhanced_confidence_score(
            validated_results, user_query, query_analysis
        )
        
        # Extract enhanced sources
        sources = self.extract_enhanced_sources(validated_results, query_analysis)
        
        return RAGResponse(
            answer=answer,
            sources=sources,
            confidence_score=confidence_score,
            query=user_query
        )
    
    def format_enhanced_context(self, search_results: List[Dict[str, Any]], 
                               query_analysis: Dict) -> str:
        """Format search results with enhanced context information"""
        if not search_results:
            return "No relevant context found."
        
        context = f"""RELEVANT INFORMATION (Intent: {query_analysis.get('suggested_intent', 'general').replace('_', ' ').title()}):

"""
        
        for i, result in enumerate(search_results, 1):
            quality_score = result.get('quality_score', result['similarity_score'])
            
            context += f"Source {i} (Quality: {quality_score:.3f}):\n"
            context += f"URL: {result['metadata'].get('source_url', 'N/A')}\n"
            context += f"Title: {result['metadata'].get('source_title', 'N/A')}\n"
            context += f"Type: {result['metadata'].get('source_type', 'N/A')}\n"
            context += f"Content: {result['content']}\n"
            
            # Add document links with enhanced formatting
            doc_links = result['metadata'].get('document_links', [])
            if doc_links:
                context += f"Document Links ({len(doc_links)} available):\n"
                for link in doc_links[:3]:  # Show top 3 links
                    context += f"  - {link}\n"
                if len(doc_links) > 3:
                    context += f"  ... and {len(doc_links) - 3} more links\n"
            
            # Add metadata indicators
            if result['metadata'].get('document_id'):
                context += f"Document ID: {result['metadata']['document_id']}\n"
            
            context += f"Relevance Score: {result['similarity_score']:.3f}\n"
            context += "-" * 60 + "\n\n"
        
        return context
    
    def get_system_stats(self) -> Dict[str, Any]:
        """Get system statistics"""
        db_stats = self.vector_db.get_collection_stats()
        return {
            'vector_db_stats': db_stats,
            'embedding_model': self.config.EMBEDDING_MODEL,
            'chunk_size': self.config.CHUNK_SIZE,
            'top_k_results': self.config.TOP_K_RESULTS
        }