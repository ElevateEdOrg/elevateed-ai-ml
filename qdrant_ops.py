from qdrant_client import QdrantClient, models
import groq
import os
import hashlib
from sentence_transformers import SentenceTransformer

from config import Config

# Configure Groq API
API_KEY = Config.GROQ_API_KEY
groq_client = groq.Client(api_key=API_KEY)

# Connect to Qdrant
client = QdrantClient("localhost", port=6333)



def get_text_embedding(text: str):
    """Converts text into an embedding using sentence-transformers."""
    model = SentenceTransformer('all-mpnet-base-v2')  # or another model
    embedding = model.encode(text)
    return embedding.tolist()

def store_transcript_in_qdrant(course_id: str, lecture_id: str, transcript_path: str):
    """Stores transcript text embeddings in a Qdrant collection based on course_id."""
    collection_name = f"course_{course_id}"
    
    # Ensure collection exists
    existing_collections = client.get_collections().collections
    if collection_name not in [col.name for col in existing_collections]:
        client.recreate_collection(
            collection_name=collection_name,
            vectors_config=models.VectorParams(size=768, distance=models.Distance.COSINE),
        )
    
    # Read transcript text
    with open(transcript_path, "r", encoding="utf-8") as f:
        transcript = f.read()
    
    # Chunk transcript and store embeddings
    chunks = [transcript[i:i+512] for i in range(0, len(transcript), 512)]
    points = []
    
    for idx, chunk in enumerate(chunks):
        embedding = get_text_embedding(chunk)
        # Use integer IDs instead of string IDs
        point_id = int(f"{hash(lecture_id) % 10000}{idx}") 
        
        points.append(
            models.PointStruct(
                id=point_id,
                vector=embedding, 
                payload={"text": chunk, "lecture_id": lecture_id, "course_id": course_id}
            )
        )
    
    # Batch upsert all points at once
    client.upsert(
        collection_name=collection_name,
        points=points
    )
    
    print(f"Stored transcript for {lecture_id} in Qdrant.")

def search_transcript_in_qdrant(course_id: str, query: str):
    """Searches for relevant transcript chunks in Qdrant."""
    query_embedding = get_text_embedding(query)
    collection_name = f"course_{course_id}"
    
    if collection_name not in [col.name for col in client.get_collections().collections]:
        return {"error": f"Course {course_id} not found"}
    
    results = client.search(
        collection_name=collection_name,
        query_vector=query_embedding,
        limit=3
    )
    return [hit.payload["text"] for hit in results]
