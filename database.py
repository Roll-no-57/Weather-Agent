import os
from pinecone import Pinecone, ServerlessSpec
from sentence_transformers import SentenceTransformer
import uuid
from datetime import datetime
from dateutil.parser import parse as parse_date 

# Initialize Pinecone
pc = Pinecone(api_key="pcsk_79YHd6_Efrhrai8hs65MRSrezyFcThUMW8DoMgyZRUa4TNBQv8nHk4N9tHboUybfR7oGYA")

# Create or connect to Pinecone index
index_name = "weather-agent-sessions"
if index_name not in pc.list_indexes().names():
    pc.create_index(
        name=index_name,
        dimension=384,  # Dimension for 'all-MiniLM-L6-v2'
        metric='cosine',
        spec=ServerlessSpec(cloud='aws', region='us-east-1')  # Adjust region as needed
    )
index = pc.Index(index_name)

# Initialize sentence transformer for embeddings
model = SentenceTransformer('all-MiniLM-L6-v2')

def store_session(user_id: str, query: str, response: str):
    """
    Store a chat session in Pinecone with embeddings.
    
    Args:
        user_id: Unique identifier for the user
        query: User's query
        response: Agent's response
    """
    session_id = str(uuid.uuid4())
    timestamp = datetime.now().isoformat()
    
    # Combine query and response for embedding
    combined_text = f"Query: {query} Response: {response}"
    embedding = model.encode(combined_text).tolist()
    
    # Store in Pinecone with metadata
    index.upsert(vectors=[{
        "id": session_id,
        "values": embedding,
        "metadata": {
            "user_id": user_id,
            "query": query,
            "response": response,
            "timestamp": timestamp
        }
    }])
    
    return session_id

def fetch_user_sessions(user_id: str, limit: int = 10):
    """
    Fetch recent chat sessions for a user.
    
    Args:
        user_id: Unique identifier for the user
        limit: Maximum number of sessions to return
    
    Returns:
        List of session metadata
    """
    # Query Pinecone for sessions (using a dummy vector for filtering by metadata)
    dummy_vector = [0.0] * 384  # Dummy vector since we're filtering by metadata
    results = index.query(
        vector=dummy_vector,
        top_k=limit,
        include_metadata=True,
        filter={"user_id": user_id}
    )
    
    return [
        {
            "id": match["id"],
            "query": match["metadata"]["query"],
            "response": match["metadata"]["response"],
            "timestamp": match["metadata"]["timestamp"]
        }
        for match in results["matches"]
    ]

def fetch_session_by_id(session_id: str):
    """
    Fetch a specific session by ID.
    
    Args:
        session_id: Unique session ID
    
    Returns:
        Session metadata or None if not found
    """
    results = index.fetch(ids=[session_id])
    if session_id in results["vectors"]:
        metadata = results["vectors"][session_id]["metadata"]
        return {
            "id": session_id,
            "query": metadata["query"],
            "response": metadata["response"],
            "timestamp": metadata["timestamp"]
        }
    return None

def fetch_similar_sessions(query: str, user_id: str, limit: int = 5):
    """
    Fetch sessions with similar queries for context, sorted by timestamp (most recent first).
    
    Args:
        query: Current user query
        user_id: Unique identifier for the user
        limit: Maximum number of similar sessions
    
    Returns:
        List of similar session metadata
    """
    embedding = model.encode(query).tolist()
    
    # Fetch top-K similar sessions
    results = index.query(
        vector=embedding,
        top_k=limit * 2,  # Get more than limit in case we sort/filter further
        include_metadata=True,
        filter={"user_id": user_id}
    )
    
    # Extract metadata
    sessions = [
        {
            "id": match["id"],
            "query": match["metadata"]["query"],
            "response": match["metadata"]["response"],
            "timestamp": match["metadata"]["timestamp"],
            "score": match["score"]
        }
        for match in results["matches"]
    ]
    
    # Sort by timestamp (most recent first)
    sessions.sort(key=lambda x: parse_date(x["timestamp"]), reverse=True)
    
    # Return the top `limit` sessions
    return sessions[:limit]