# quiz/qdrant_ops.py

from qdrant_client import QdrantClient, models
from sentence_transformers import SentenceTransformer
import os
import hashlib
import logging

from quiz.config import Config

logging.basicConfig(
    filename="qdrant_ops.log",
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)

# Connect to Qdrant
qdrant_url = Config.QDRANT_URL
client = QdrantClient(url=qdrant_url)

# Load the SentenceTransformer model once
# (Consider lazy loading if you prefer)
embedding_model = SentenceTransformer('all-mpnet-base-v2')

def get_text_embedding(text: str):
    """Converts text into an embedding using sentence-transformers."""
    embedding = embedding_model.encode(text)
    return embedding.tolist()

def store_transcript_in_qdrant(course_id: str, lecture_id: str, transcript_path: str):
    """Stores transcript text embeddings in a Qdrant collection for a specific course."""
    collection_name = f"course_{course_id}"

    # Ensure collection exists
    existing = client.get_collections().collections
    if collection_name not in [col.name for col in existing]:
        # Recreate or create collection
        client.recreate_collection(
            collection_name=collection_name,
            vectors_config=models.VectorParams(size=768, distance=models.Distance.COSINE),
        )

    # Read transcript text
    with open(transcript_path, "r", encoding="utf-8") as f:
        transcript = f.read()

    # Chunk transcript (simple approach: 512 chars each)
    chunks = [transcript[i:i+512] for i in range(0, len(transcript), 512)]
    points = []

    for idx, chunk in enumerate(chunks):
        embedding = get_text_embedding(chunk)
        # Generate an integer ID
        point_id = abs(hash(lecture_id) % 1000000) * 1000 + idx

        points.append(
            models.PointStruct(
                id=point_id,
                vector=embedding,
                payload={
                    "text": chunk,
                    "lecture_id": lecture_id,
                    "course_id": course_id
                }
            )
        )

    # Upsert points
    client.upsert(collection_name=collection_name, points=points)
    logging.info(f"Stored transcript for lecture {lecture_id} in Qdrant collection {collection_name}.")

def search_transcript_in_qdrant(course_id: str, query: str, top_k: int = 3):
    """Searches for relevant transcript chunks in Qdrant."""
    query_embedding = get_text_embedding(query)
    collection_name = f"course_{course_id}"

    existing = client.get_collections().collections
    if collection_name not in [col.name for col in existing]:
        return {"error": f"Collection {collection_name} not found"}

    results = client.search(
        collection_name=collection_name,
        query_vector=query_embedding,
        limit=top_k
    )
    return [hit.payload["text"] for hit in results]
