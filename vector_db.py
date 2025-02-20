from qdrant_client import QdrantClient as Qdrant
from qdrant_client.http.models import PointStruct, VectorParams, Distance
from sentence_transformers import SentenceTransformer
import os

class QdrantClient:
    def __init__(self):
        # Connect to Qdrant (adjust host/port if needed)
        self.client = Qdrant(host="localhost", port=6333)
        self.collection_name = "uploaded_files"
        self.model = SentenceTransformer("all-MiniLM-L6-v2")
        
        # Create or recreate the collection with the proper vector size (384 for all-MiniLM-L6-v2)
        try:
            self.client.recreate_collection(
                collection_name=self.collection_name,
                vectors_config=VectorParams(size=384, distance=Distance.COSINE)
            )
        except Exception as e:
            print(f"Error creating collection: {e}")

    def store_file(self, file_path: str) -> bool:
        """
        Process the file (here we simply try to read it as text) and store its content
        along with an embedding in Qdrant. In a real implementation, you'd add proper
        processing for PDFs, PPTs, audio, and video.
        """
        try:
            # Attempt to open the file as text; if binary, use dummy text.
            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    text = f.read()
            except Exception:
                text = f"Content of file {os.path.basename(file_path)}"
            
            embedding = self.model.encode(text).tolist()
            payload = {
                "text": text,
                "filename": os.path.basename(file_path),
                "file_type": os.path.splitext(file_path)[1]
            }
            
            self.client.upsert(
                collection_name=self.collection_name,
                points=[PointStruct(
                    id=abs(hash(file_path)) % (10**12),
                    vector=embedding,
                    payload=payload
                )]
            )
            return True
        except Exception as e:
            print(f"Error storing file: {e}")
            return False

    def search_similar_files(self, query: str, limit: int = 5):
        """
        Search for similar content in Qdrant using the query text.
        Returns a list of payloads.
        """
        query_vector = self.model.encode(query).tolist()
        try:
            search_result = self.client.search(
                collection_name=self.collection_name,
                query_vector=query_vector,
                with_payload=True,
                limit=limit
            )
            return [{"score": hit.score, "metadata": hit.payload} for hit in search_result]
        except Exception as e:
            print(f"Error searching similar files: {e}")
            return []
