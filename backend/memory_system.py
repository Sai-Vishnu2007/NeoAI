"""
Long-Term Memory System using Qdrant and RAG (Retrieval-Augmented Generation)
"""

from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams, PointStruct, Filter, FieldCondition, MatchValue
from sentence_transformers import SentenceTransformer
import uuid
from typing import List, Dict, Any
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class MemorySystem:
    """
    Long-Term Memory System for storing and retrieving conversational context
    using Qdrant vector database and sentence embeddings.
    """
    
    def __init__(self, collection_name: str = "conversation_memory"):
        """
        Initialize the Memory System in LOCAL MODE.
        This saves data to a folder named 'qdrant_memory' in your project.
        """
        # --- THE FIX IS HERE: Use 'path' instead of 'host' ---
        self.client = QdrantClient(path="./qdrant_memory")
        self.collection_name = collection_name
        
        # Initialize local embedding model
        logger.info("Loading embedding model: all-MiniLM-L6-v2")
        self.embedding_model = SentenceTransformer('all-MiniLM-L6-v2')
        
        # Get embedding dimension
        self.embedding_dim = self.embedding_model.get_sentence_embedding_dimension()
        logger.info(f"Embedding dimension: {self.embedding_dim}")
        
        # Ensure collection exists
        self._ensure_collection_exists()
    
    def _ensure_collection_exists(self):
        """
        Create the Qdrant collection if it doesn't exist.
        """
        try:
            # Check if collection exists
            collections = self.client.get_collections().collections
            collection_names = [collection.name for collection in collections]
            
            if self.collection_name not in collection_names:
                logger.info(f"Creating collection: {self.collection_name}")
                self.client.create_collection(
                    collection_name=self.collection_name,
                    vectors_config=VectorParams(
                        size=self.embedding_dim,
                        distance=Distance.COSINE
                    )
                )
                logger.info(f"Collection '{self.collection_name}' created successfully")
            else:
                logger.info(f"Collection '{self.collection_name}' already exists")
        except Exception as e:
            logger.error(f"Error ensuring collection exists: {e}")
            raise
    
    def store_interaction(self, user_id: str, user_message: str, ai_response: str) -> str:
        """
        Vectorize the user message and store it in Qdrant with the AI response as payload.
        
        Args:
            user_id: Unique identifier for the user
            user_message: The message from the user
            ai_response: The AI's response to the user message
            
        Returns:
            str: The unique ID of the stored point
        """
        try:
            # Generate embedding for the user message
            embedding = self.embedding_model.encode(user_message).tolist()
            
            # Generate unique ID for this interaction
            point_id = str(uuid.uuid4())
            
            # Create point with payload
            point = PointStruct(
                id=point_id,
                vector=embedding,
                payload={
                    "user_id": user_id,
                    "user_message": user_message,
                    "ai_response": ai_response,
                }
            )
            
            # Store in Qdrant
            self.client.upsert(
                collection_name=self.collection_name,
                points=[point]
            )
            
            logger.info(f"Stored interaction for user {user_id} with ID {point_id}")
            return point_id
            
        except Exception as e:
            logger.error(f"Error storing interaction: {e}")
            raise
    
    def retrieve_context(self, user_id: str, query: str, top_k: int = 3) -> List[Dict[str, Any]]:
        """
        Search Qdrant for the top similar past conversations for this specific user.
        
        Args:
            user_id: Unique identifier for the user
            query: The query text to search for similar conversations
            top_k: Number of top similar conversations to retrieve (default: 3)
            
        Returns:
            List[Dict]: List of similar conversations with their metadata
        """
        try:
            # Generate embedding for the query
            query_embedding = self.embedding_model.encode(query).tolist()
            
            # Search with user_id filter
            search_results = self.client.search(
                collection_name=self.collection_name,
                query_vector=query_embedding,
                query_filter=Filter(
                    must=[
                        FieldCondition(
                            key="user_id",
                            match=MatchValue(value=user_id)
                        )
                    ]
                ),
                limit=top_k
            )
            
            # Format results
            results = []
            for hit in search_results:
                results.append({
                    "id": hit.id,
                    "score": hit.score,
                    "user_message": hit.payload.get("user_message"),
                    "ai_response": hit.payload.get("ai_response"),
                    "user_id": hit.payload.get("user_id")
                })
            
            logger.info(f"Retrieved {len(results)} similar conversations for user {user_id}")
            return results
            
        except Exception as e:
            logger.error(f"Error retrieving context: {e}")
            raise


# Singleton instance
_memory_system = None


def get_memory_system() -> MemorySystem:
    """
    Get or create a singleton instance of MemorySystem.
    
    Returns:
        MemorySystem: The memory system instance
    """
    global _memory_system
    if _memory_system is None:
        _memory_system = MemorySystem()
    return _memory_system


# Example usage
if __name__ == "__main__":
    # Initialize memory system
    memory = MemorySystem()
    
    # Example: Store an interaction
    user_id = "user_123"
    user_msg = "What is machine learning?"
    ai_resp = "Machine learning is a branch of artificial intelligence that focuses on building systems that can learn from data."
    
    interaction_id = memory.store_interaction(user_id, user_msg, ai_resp)
    print(f"Stored interaction with ID: {interaction_id}")
    
    # Example: Retrieve similar context
    query = "Tell me about AI"
    context = memory.retrieve_context(user_id, query)
    
    print(f"\nRetrieved {len(context)} similar conversations:")
    for idx, item in enumerate(context, 1):
        print(f"\n{idx}. Score: {item['score']:.4f}")
        print(f"   User: {item['user_message']}")
        print(f"   AI: {item['ai_response']}")
