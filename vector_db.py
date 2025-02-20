import os
from qdrant_client import QdrantClient as Qdrant
from qdrant_client.http.models import PointStruct, VectorParams, Distance
from sentence_transformers import SentenceTransformer
from config import Config

class QdrantClient:
    def __init__(self):
        self.host = Config.QDRANT_HOST
        self.port = Config.QDRANT_PORT
        self.collection_name = Config.COLLECTION_NAME
        self.client = Qdrant(host=self.host, port=self.port)
        self.model = SentenceTransformer("all-MiniLM-L6-v2")
        
        # Check if the collection exists; if not, create it.
        try:
            existing = self.client.get_collections()
            collection_names = [col.name for col in existing.collections] if existing.collections else []
            if self.collection_name not in collection_names:
                self.client.create_collection(
                    collection_name=self.collection_name,
                    vectors_config=VectorParams(size=384, distance=Distance.COSINE)
                )
                print(f"Collection '{self.collection_name}' created successfully.")
            else:
                print(f"Collection '{self.collection_name}' already exists.")
        except Exception as e:
            print(f"Error initializing collection '{self.collection_name}': {e}")

    def store_file(self, file_path: str) -> bool:
        """
        Process the file and store its content along with a vector embedding in Qdrant.
        """
        try:
            # Attempt to read file as text; fallback to a placeholder if necessary.
            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    text = f.read()
            except Exception:
                text = f"Content of file {os.path.basename(file_path)}"
            
            # Encode the text using the SentenceTransformer model.
            embedding = self.model.encode(text).tolist()
            payload = {
                "text": text,
                "filename": os.path.basename(file_path),
                "file_type": os.path.splitext(file_path)[1]
            }
            
            # Upsert the document into the Qdrant collection.
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
        Returns a list of dictionaries with similarity scores and metadata.
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

    def list_documents(self, collection_name: str = None) -> list:
        """
        Retrieve all documents from the specified collection using a scroll query.
        Returns a list of document dictionaries containing IDs and payloads.
        """
        try:
            col_name = collection_name if collection_name else self.collection_name
            scroll_result = self.client.scroll(
                collection_name=col_name,
                limit=100  # adjust this limit as needed
            )
            docs = []
            for point in scroll_result.points:
                doc = {"id": point.id, "metadata": point.payload}
                docs.append(doc)
            return docs
        except Exception as e:
            print(f"Error listing documents: {e}")
            return []

    def search_by_topic(self, collection_name: str, topic: str, limit: int = 3) -> list:
        """
        Retrieve documents from the collection that match a specific topic.
        This method assumes that document payloads include a 'topic' field.
        """
        try:
            # Search using the topic as query to fetch more results, then filter.
            results = self.search_similar_files(topic, limit=limit*2)
            filtered = []
            for result in results:
                payload = result.get("metadata", {})
                if "topic" in payload and topic.lower() in payload["topic"].lower():
                    filtered.append(result)
                    if len(filtered) >= limit:
                        break
            return filtered
        except Exception as e:
            print(f"Error searching by topic: {e}")
            return []
