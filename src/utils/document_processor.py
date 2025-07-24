from typing import List, Dict, Any
from dataclasses import dataclass
import hashlib
import re
from langchain.text_splitter import RecursiveCharacterTextSplitter
from loguru import logger
from config import Config

@dataclass
class DocumentChunk:
    chunk_id: str
    content: str
    metadata: Dict[str, Any]
    
class DocumentProcessor:
    def __init__(self):
        self.config = Config()
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=self.config.CHUNK_SIZE,
            chunk_overlap=self.config.CHUNK_OVERLAP,
            length_function=len,
            separators=["\n\n", "\n", " ", ""]
        )
        
    def generate_chunk_id(self, content: str, url: str, chunk_index: int) -> str:
        """Generate unique chunk ID"""
        content_hash = hashlib.md5(content.encode()).hexdigest()[:8]
        url_hash = hashlib.md5(url.encode()).hexdigest()[:8]
        return f"{url_hash}_{chunk_index}_{content_hash}"
        
    def preprocess_content(self, content: str) -> str:
        """Clean and preprocess content"""
        # Remove extra whitespace
        content = re.sub(r'\s+', ' ', content)
        
        # Remove special characters that might interfere with processing
        content = re.sub(r'[^\w\s.,!?;:()\-]', '', content)
        
        # Remove very short lines that are likely navigation/UI elements
        lines = content.split('\n')
        filtered_lines = [line.strip() for line in lines if len(line.strip()) > 10]
        
        return '\n'.join(filtered_lines)
        
    def is_meaningful_chunk(self, chunk: str) -> bool:
        """Check if chunk contains meaningful content"""
        # Skip chunks that are too short
        if len(chunk.strip()) < 20:  # Reduced from 50 to 20
            return False
            
        # Skip chunks that are mostly navigation/UI elements
        ui_indicators = [
            'click here', 'home page', 'contact us', 'about us',
            'privacy policy', 'terms of service', 'cookie policy',
            'skip to content', 'main menu', 'search'
        ]
        
        chunk_lower = chunk.lower()
        if any(indicator in chunk_lower for indicator in ui_indicators):
            return False
            
        # Skip chunks with too many repeated words (more lenient)
        words = chunk.split()
        if len(words) < 3:  # Skip very short chunks
            return False
            
        if len(set(words)) < len(words) * 0.2:  # Less than 20% unique words (was 30%)
            return False
            
        return True
        
    def create_chunk_metadata(self, original_metadata: Dict, chunk_index: int, 
                            total_chunks: int) -> Dict[str, Any]:
        """Create metadata for a chunk"""
        chunk_metadata = original_metadata.copy()
        chunk_metadata.update({
            'chunk_index': chunk_index,
            'total_chunks': total_chunks,
            'chunk_size': self.config.CHUNK_SIZE,
            'chunk_overlap': self.config.CHUNK_OVERLAP
        })
        return chunk_metadata
        
    def process_scraped_content(self, scraped_data: List[Any]) -> List[DocumentChunk]:
        """Process scraped content into chunks"""
        logger.info(f"Processing {len(scraped_data)} scraped documents")
        
        all_chunks = []
        
        for doc in scraped_data:
            # Preprocess content
            processed_content = self.preprocess_content(doc.content)
            
            if not processed_content.strip():
                logger.warning(f"Empty content after preprocessing: {doc.url}")
                continue
                
            # Split into chunks
            chunks = self.text_splitter.split_text(processed_content)
            
            # Filter meaningful chunks
            meaningful_chunks = [chunk for chunk in chunks if self.is_meaningful_chunk(chunk)]
            
            if not meaningful_chunks:
                logger.warning(f"No meaningful chunks found: {doc.url}")
                continue
                
            # Create DocumentChunk objects
            for i, chunk_content in enumerate(meaningful_chunks):
                chunk_metadata = self.create_chunk_metadata(
                    doc.metadata, i, len(meaningful_chunks)
                )
                
                # Add document-specific metadata
                chunk_metadata.update({
                    'source_url': doc.url,
                    'source_title': doc.title,
                    'source_type': doc.source_type,
                    'document_links': doc.document_links,
                    'original_content_length': len(doc.content)
                })
                
                chunk_id = self.generate_chunk_id(chunk_content, doc.url, i)
                
                chunk = DocumentChunk(
                    chunk_id=chunk_id,
                    content=chunk_content,
                    metadata=chunk_metadata
                )
                
                all_chunks.append(chunk)
                
        logger.info(f"Created {len(all_chunks)} document chunks")
        return all_chunks
        
    def create_search_optimized_content(self, chunk: DocumentChunk) -> str:
        """Create search-optimized version of chunk content"""
        # Combine title and content for better search
        search_content = f"Title: {chunk.metadata.get('source_title', '')}\n\n"
        search_content += f"Content: {chunk.content}"
        
        # Add source type context
        if chunk.metadata.get('source_type'):
            search_content += f"\n\nDocument Type: {chunk.metadata['source_type']}"
            
        return search_content
        
    def extract_key_entities(self, content: str) -> List[str]:
        """Extract key entities from content for metadata"""
        # Simple keyword extraction (can be enhanced with NLP)
        insurance_keywords = [
            'irdai', 'insurance', 'policy', 'premium', 'claim', 'regulation',
            'circular', 'guideline', 'act', 'amendment', 'notification',
            'life insurance', 'general insurance', 'health insurance',
            'motor insurance', 'fire insurance', 'marine insurance'
        ]
        
        found_entities = []
        content_lower = content.lower()
        
        for keyword in insurance_keywords:
            if keyword in content_lower:
                found_entities.append(keyword)
                
        return found_entities
        
    def enrich_metadata(self, chunks: List[DocumentChunk]) -> List[DocumentChunk]:
        """Enrich chunks with additional metadata"""
        logger.info("Enriching chunk metadata")
        
        for chunk in chunks:
            # Extract key entities
            entities = self.extract_key_entities(chunk.content)
            chunk.metadata['key_entities'] = entities
            
            # Add content statistics
            chunk.metadata['word_count'] = len(chunk.content.split())
            chunk.metadata['char_count'] = len(chunk.content)
            
            # Identify document type patterns
            content_lower = chunk.content.lower()
            if any(word in content_lower for word in ['circular', 'notification', 'order']):
                chunk.metadata['document_category'] = 'regulatory'
            elif any(word in content_lower for word in ['annual report', 'financial']):
                chunk.metadata['document_category'] = 'financial'
            elif any(word in content_lower for word in ['policy', 'terms', 'conditions']):
                chunk.metadata['document_category'] = 'policy'
            else:
                chunk.metadata['document_category'] = 'general'
                
        return chunks