# quiz/qdrant_ops.py

import os
import logging
from qdrant_client import QdrantClient, models
from sentence_transformers import SentenceTransformer

logging.basicConfig(
    filename="qdrant_ops.log",
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)

client = QdrantClient(url=os.getenv("QDRANT_URL", "http://localhost:6333"))
embedding_model = SentenceTransformer("all-mpnet-base-v2")

def get_text_embedding(text: str):
    return embedding_model.encode(text).tolist()

def store_transcript_in_qdrant(course_id: str, lecture_id: str, transcript_path: str):
    collection_name = f"course_{course_id}"
    existing = client.get_collections().collections
    if collection_name not in [col.name for col in existing]:
        client.recreate_collection(
            collection_name=collection_name,
            vectors_config=models.VectorParams(size=768, distance=models.Distance.COSINE),
        )
    with open(transcript_path, "r", encoding="utf-8") as f:
        transcript = f.read()
    chunks = [transcript[i:i+512] for i in range(0, len(transcript), 512)]
    points = []
    for idx, chunk in enumerate(chunks):
        embedding = get_text_embedding(chunk)
        point_id = abs(hash(lecture_id) % 1000000) * 1000 + idx
        points.append(
            models.PointStruct(
                id=point_id,
                vector=embedding,
                payload={"text": chunk, "lecture_id": lecture_id, "course_id": course_id}
            )
        )
    client.upsert(collection_name=collection_name, points=points)
    logging.info(f"Stored transcript for lecture {lecture_id} in Qdrant collection {collection_name}.")

def search_transcript_in_qdrant(collection_name: str, query: str, top_k: int = 3) -> list:
    embedding = embedding_model.encode(query).tolist()
    results = client.search(
        collection_name=collection_name,
        query_vector=embedding,
        limit=top_k
    )
    return [hit.payload["text"] for hit in results]
