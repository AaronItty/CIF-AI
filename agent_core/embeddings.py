import os
import requests

class EmbeddingService:
    def __init__(self, model_name="nomic-embed-text-v1.5"):
  
        self.model_name = model_name
        # Note: the .env uses NOMIC_KEY, so we load that one
        self.api_key = os.getenv("NOMIC_KEY") or os.getenv("NOMIC_API_KEY")
        self.api_url = "https://api-atlas.nomic.ai/v1/embedding/text"
        
        if not self.api_key:
            print("WARNING: NOMIC_API_KEY not found in environment variables. Embedding will fail.")

    def _get_embedding(self, texts: list[str]) -> list[list[float]]:
        if not self.api_key:
            raise ValueError("NOMIC_API_KEY is not set.")
            
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "model": self.model_name,
            "texts": texts
        }
        
        response = requests.post(self.api_url, headers=headers, json=payload)
        response.raise_for_status()
        
        data = response.json()
        return data.get("embeddings", [])

    def embed_document(self, text: str):
        """
        Generates embeddings for document chunks with the required prefix.
        ✅ STEP 4 — Generate Document Embeddings
        """
        prefixed = f"search_document: {text}"
        embeddings = self._get_embedding([prefixed])
        return embeddings[0] if embeddings else []

    def embed_query(self, query: str):
        """
        Generates embeddings for user queries with the required prefix.
        ✅ STEP 6 — Embed User Queries
        """
        prefixed = f"search_query: {query}"
        embeddings = self._get_embedding([prefixed])
        return embeddings[0] if embeddings else []
