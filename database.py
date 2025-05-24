import os
from pinecone import Pinecone, ServerlessSpec
from sentence_transformers import SentenceTransformer
import uuid
from datetime import datetime
from dateutil.parser import parse as parse_date
import json

# Initialize Pinecone
pc = Pinecone(api_key="pcsk_79YHd6_Efrhrai8hs65MRSrezyFcThUMW8DoMgyZRUa4TNBQv8nHk4N9tHboUybfR7oGYA")

# Initialize sentence transformer for embeddings
model = SentenceTransformer('all-MiniLM-L6-v2')

# Chat metadata index name
CHAT_METADATA_INDEX = "user-chats-metadata"

def initialize_chat_metadata_index():
    """Initialize the chat metadata index if it doesn't exist."""
    if CHAT_METADATA_INDEX not in pc.list_indexes().names():
        pc.create_index(
            name=CHAT_METADATA_INDEX,
            dimension=384,  # Dimension for 'all-MiniLM-L6-v2'
            metric='cosine',
            spec=ServerlessSpec(cloud='aws', region='us-east-1')
        )

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

def store_chat_metadata(user_id: str, chat_id: str, title: str = None):
    """Store chat metadata in the chat metadata index."""
    initialize_chat_metadata_index()
    index = pc.Index(CHAT_METADATA_INDEX)
    
    if title is None:
        # Get existing chats count to generate title
        existing_chats = fetch_user_chats(user_id)
        title = f"Chat {len(existing_chats) + 1}"
    
    timestamp = datetime.now().isoformat()
    
    # Create a searchable text for the chat metadata
    searchable_text = f"user:{user_id} chat:{chat_id} title:{title}"
    embedding = model.encode(searchable_text).tolist()
    
    metadata_id = f"{user_id}-{chat_id}"
    
    index.upsert(vectors=[{
        "id": metadata_id,
        "values": embedding,
        "metadata": {
            "user_id": user_id,
            "chat_id": chat_id,
            "title": title,
            "created_at": timestamp,
            "last_updated": timestamp
        }
    }])
    
    return metadata_id

def fetch_user_chats(user_id: str):
    """Fetch all chats for a specific user."""
    try:
        initialize_chat_metadata_index()
        index = pc.Index(CHAT_METADATA_INDEX)
        
        # Query using user_id in the searchable text
        user_query = f"user:{user_id}"
        embedding = model.encode(user_query).tolist()
        
        results = index.query(
            vector=embedding,
            top_k=1000,  # Get up to 1000 chats per user
            include_metadata=True,
            filter={"user_id": {"$eq": user_id}}
        )
        
        chats = [
            {
                "chat_id": match["metadata"]["chat_id"],
                "title": match["metadata"]["title"],
                "created_at": match["metadata"]["created_at"],
                "last_updated": match["metadata"].get("last_updated", match["metadata"]["created_at"])
            }
            for match in results["matches"]
        ]
        
        # Sort by creation date (newest first)
        chats.sort(key=lambda x: parse_date(x["created_at"]), reverse=True)
        
        return chats
    except Exception as e:
        print(f"Error fetching user chats: {e}")
        return []

def update_chat_last_activity(user_id: str, chat_id: str):
    """Update the last activity timestamp for a chat."""
    try:
        initialize_chat_metadata_index()
        index = pc.Index(CHAT_METADATA_INDEX)
        
        metadata_id = f"{user_id}-{chat_id}"
        timestamp = datetime.now().isoformat()
        
        # Fetch current metadata
        current_data = index.fetch(ids=[metadata_id])
        if metadata_id in current_data['vectors']:
            current_metadata = current_data['vectors'][metadata_id]['metadata']
            
            # Update the metadata with new timestamp
            updated_metadata = current_metadata.copy()
            updated_metadata['last_updated'] = timestamp
            
            # Create searchable text
            searchable_text = f"user:{user_id} chat:{chat_id} title:{current_metadata['title']}"
            embedding = model.encode(searchable_text).tolist()
            
            index.upsert(vectors=[{
                "id": metadata_id,
                "values": embedding,
                "metadata": updated_metadata
            }])
    except Exception as e:
        print(f"Error updating chat activity: {e}")

def store_query_response(chat_id: str, query: str, response: str, user_id: str = None):
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
    
    # Update chat activity if user_id is provided
    if user_id:
        update_chat_last_activity(user_id, chat_id)
    
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
    
    messages = [
        {
            "id": match["id"],
            "query": match["metadata"]["query"],
            "response": match["metadata"]["response"],
            "timestamp": match["metadata"]["timestamp"]
        }
        for match in results["matches"]
    ]
    
    # Sort by timestamp (oldest first for chat history)
    messages.sort(key=lambda x: parse_date(x["timestamp"]))
    
    return messages

def delete_chat(user_id: str, chat_id: str):
    """Delete a chat and its metadata."""
    try:
        # Delete chat messages index
        chat_index_name = f"chat-{chat_id}"
        if chat_index_name in pc.list_indexes().names():
            pc.delete_index(chat_index_name)
        
        # Delete chat metadata
        initialize_chat_metadata_index()
        metadata_index = pc.Index(CHAT_METADATA_INDEX)
        metadata_id = f"{user_id}-{chat_id}"
        metadata_index.delete(ids=[metadata_id])
        
        return True
    except Exception as e:
        print(f"Error deleting chat: {e}")
        return False