import os
from pinecone import Pinecone, ServerlessSpec
from sentence_transformers import SentenceTransformer
import uuid
from datetime import datetime
from dateutil.parser import parse as parse_date

# Initialize Pinecone
pc = Pinecone(api_key="pcsk_79YHd6_Efrhrai8hs65MRSrezyFcThUMW8DoMgyZRUa4TNBQv8nHk4N9tHboUybfR7oGYA")

# Initialize sentence transformer for embeddings
model = SentenceTransformer('all-MiniLM-L6-v2')

def create_chat_index(chat_id: str):
    """Create a new Pinecone index for a chat."""
    index_name = f"chat-{chat_id}"
    if index_name not in pc.list_indexes().names():
        pc.create_index(
            name=index_name,
            dimension=384,  # Dimension for 'all-MiniLM-L6-v2'
            metric='cosine',
            spec=ServerlessSpec(cloud='aws', region='us-east-1')
        )
    return index_name

def store_query_response(chat_id: str, query: str, response: str):
    """Store a query-response pair in the specified chat's index."""
    index_name = f"chat-{chat_id}"
    index = pc.Index(index_name)
    
    message_id = str(uuid.uuid4())
    timestamp = datetime.now().isoformat()
    
    combined_text = f"Query: {query} Response: {response}"
    embedding = model.encode(combined_text).tolist()
    
    index.upsert(vectors=[{
        "id": message_id,
        "values": embedding,
        "metadata": {
            "query": query,
            "response": response,
            "timestamp": timestamp
        }
    }])
    
    return message_id

def fetch_similar_query_responses(chat_id: str, query: str, limit: int = 5):
    """Fetch similar query-response pairs from the specified chat's index."""
    index_name = f"chat-{chat_id}"
    index = pc.Index(index_name)
    
    embedding = model.encode(query).tolist()
    
    results = index.query(
        vector=embedding,
        top_k=limit,
        include_metadata=True
    )
    
    messages = [
        {
            "id": match["id"],
            "query": match["metadata"]["query"],
            "response": match["metadata"]["response"],
            "timestamp": match["metadata"]["timestamp"],
            "score": match["score"]
        }
        for match in results["matches"]
    ]
    
    messages.sort(key=lambda x: parse_date(x["timestamp"]), reverse=True)
    
    return messages[:limit]

def fetch_chat_messages(chat_id: str, limit: int = 500):
    """Fetch all query-response pairs for a chat."""
    index_name = f"chat-{chat_id}"
    index = pc.Index(index_name)
    
    dummy_vector = [0.0] * 384
    results = index.query(
        vector=dummy_vector,
        top_k=limit,
        include_metadata=True
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