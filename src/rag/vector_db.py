import chromadb
from chromadb.config import Settings
from sentence_transformers import SentenceTransformer
from typing import List, Dict, Any, Optional
import os
import json
from loguru import logger
from config import Config

class VectorDatabase:
    def __init__(self):
        self.config = Config()
        self.client = None
        self.collection = None
        self.embedding_model = None
        self.setup_database()
        
    def setup_database(self):
        """Initialize ChromaDB and embedding model"""
        logger.info("Setting up vector database")
        
        # Create ChromaDB client
        os.makedirs(self.config.CHROMA_DB_PATH, exist_ok=True)
        
        self.client = chromadb.PersistentClient(
            path=self.config.CHROMA_DB_PATH,
            settings=Settings(
                anonymized_telemetry=False,
                allow_reset=True
            )
        )
        
        # Initialize embedding model
        self.embedding_model = SentenceTransformer(self.config.EMBEDDING_MODEL)
        
        # Get or create collection
        try:
            self.collection = self.client.get_collection(
                name=self.config.COLLECTION_NAME
            )
            logger.info(f"Loaded existing collection: {self.config.COLLECTION_NAME}")
        except Exception:
            self.collection = self.client.create_collection(
                name=self.config.COLLECTION_NAME,
                metadata={"hnsw:space": "cosine"}
            )
            logger.info(f"Created new collection: {self.config.COLLECTION_NAME}")
            
    def generate_embeddings(self, texts: List[str]) -> List[List[float]]:
        """Generate embeddings for texts"""
        logger.info(f"Generating embeddings for {len(texts)} texts")
        embeddings = self.embedding_model.encode(texts, convert_to_tensor=False)
        return embeddings.tolist()
        
    def add_documents(self, documents: List[Any]) -> bool:
        """
        ENHANCED: Add documents with better logging and error handling
        """
        try:
            logger.info(f"📥 Adding {len(documents)} documents to vector database")
            
            if not documents:
                logger.warning("No documents to add")
                return False
                
            # Prepare data for ChromaDB
            ids = []
            docs = []
            metadatas = []
            
            # ENHANCED: Log document details
            for i, doc in enumerate(documents[:3]):  # Log first 3
                title = getattr(doc, 'title', 'No title')
                doc_id = getattr(doc, 'metadata', {}).get('document_id', 'N/A')
                logger.info(f"  {i+1}. Adding: '{title[:60]}...' (ID: {doc_id})")
            
            if len(documents) > 3:
                logger.info(f"  ... and {len(documents) - 3} more documents")
            
            for doc in documents:
                ids.append(doc.chunk_id)
                docs.append(doc.content)
                
                # Prepare metadata (ChromaDB requires string values)
                metadata = {}
                for key, value in doc.metadata.items():
                    if isinstance(value, (str, int, float, bool)):
                        metadata[key] = str(value)
                    elif isinstance(value, list):
                        metadata[key] = json.dumps(value)
                    else:
                        metadata[key] = str(value)
                        
                metadatas.append(metadata)
                
            # Generate embeddings
            embeddings = self.generate_embeddings(docs)
            
            # Add to collection
            try:
                self.collection.add(
                    ids=ids,
                    embeddings=embeddings,
                    documents=docs,
                    metadatas=metadatas
                )
                logger.info(f"✅ Successfully added {len(documents)} documents to vector database")
                return True
            except Exception as e:
                logger.error(f"❌ Error adding documents to vector database: {e}")
                return False
                
        except Exception as e:
            logger.error(f"❌ Error adding documents to vector database: {e}")
            return False
    
    def search_similar(self, query: str, top_k: int = None) -> List[Dict[str, Any]]:
        """
        ENHANCED: Search with better logging
        """
        if top_k is None:
            top_k = self.config.TOP_K_RESULTS
            
        logger.info(f"🔍 Querying vector database: '{query}' (top {top_k})")
        
        # Generate query embedding
        query_embedding = self.generate_embeddings([query])[0]
        
        # Search in collection
        results = self.collection.query(
            query_embeddings=[query_embedding],
            n_results=top_k,
            include=["documents", "metadatas", "distances"]
        )
        
        # Format results
        formatted_results = []
        for i in range(len(results['ids'][0])):
            result = {
                'chunk_id': results['ids'][0][i],
                'content': results['documents'][0][i],
                'metadata': results['metadatas'][0][i],
                'distance': results['distances'][0][i],
                'similarity_score': 1 - results['distances'][0][i]  # Convert distance to similarity
            }
            
            # Parse JSON metadata back to original format
            if 'document_links' in result['metadata']:
                try:
                    result['metadata']['document_links'] = json.loads(
                        result['metadata']['document_links']
                    )
                except json.JSONDecodeError:
                    pass
                    
            if 'key_entities' in result['metadata']:
                try:
                    result['metadata']['key_entities'] = json.loads(
                        result['metadata']['key_entities']
                    )
                except json.JSONDecodeError:
                    pass
                    
            formatted_results.append(result)
        
        logger.info(f"✅ Found {len(formatted_results)} results from vector database")
        
        # Log top results for debugging
        for i, result in enumerate(formatted_results[:3]):
            title = result['metadata'].get('title', 'No title')
            score = result.get('similarity_score', 0)
            logger.info(f"  {i+1}. '{title[:60]}...' (Score: {score:.3f})")
            
        return formatted_results

    def search_with_filters(self, query: str, filters: Dict[str, Any] = None, 
                           top_k: int = None) -> List[Dict[str, Any]]:
        """Search with metadata filters"""
        if top_k is None:
            top_k = self.config.TOP_K_RESULTS
            
        query_embedding = self.generate_embeddings([query])[0]
        
        # Build where clause for filters
        where_clause = {}
        if filters:
            for key, value in filters.items():
                where_clause[key] = {"$eq": str(value)}
                
        # Search with filters
        results = self.collection.query(
            query_embeddings=[query_embedding],
            n_results=top_k,
            where=where_clause if where_clause else None,
            include=["documents", "metadatas", "distances"]
        )
        
        # Format results (same as search_similar)
        formatted_results = []
        for i in range(len(results['ids'][0])):
            result = {
                'chunk_id': results['ids'][0][i],
                'content': results['documents'][0][i],
                'metadata': results['metadatas'][0][i],
                'distance': results['distances'][0][i],
                'similarity_score': 1 - results['distances'][0][i]
            }
            
            # Parse JSON metadata
            if 'document_links' in result['metadata']:
                try:
                    result['metadata']['document_links'] = json.loads(
                        result['metadata']['document_links']
                    )
                except json.JSONDecodeError:
                    pass
                    
            if 'key_entities' in result['metadata']:
                try:
                    result['metadata']['key_entities'] = json.loads(
                        result['metadata']['key_entities']
                    )
                except json.JSONDecodeError:
                    pass
                    
            formatted_results.append(result)
            
        return formatted_results
        
    def get_collection_stats(self) -> Dict[str, Any]:
        """Get collection statistics"""
        try:
            count = self.collection.count()
            return {
                'total_documents': count,
                'collection_name': self.config.COLLECTION_NAME,
                'embedding_model': self.config.EMBEDDING_MODEL
            }
        except Exception as e:
            logger.error(f"Error getting collection stats: {e}")
            return {}
            
    def delete_collection(self):
        """Delete the collection"""
        try:
            self.client.delete_collection(self.config.COLLECTION_NAME)
            logger.info(f"Deleted collection: {self.config.COLLECTION_NAME}")
        except Exception as e:
            logger.error(f"Error deleting collection: {e}")
            
    def reset_database(self):
        """Reset the entire database"""
        try:
            self.client.reset()
            logger.info("Database reset successfully")
            self.setup_database()
        except Exception as e:
            logger.error(f"Error resetting database: {e}")
            
    def search_by_source_type(self, query: str, source_type: str, top_k: int = None) -> List[Dict[str, Any]]:
        """Search within a specific source type"""
        filters = {'source_type': source_type}
        return self.search_with_filters(query, filters, top_k)
        
    def search_by_document_category(self, query: str, category: str, top_k: int = None) -> List[Dict[str, Any]]:
        """Search within a specific document category"""
        filters = {'document_category': category}
        return self.search_with_filters(query, filters, top_k)