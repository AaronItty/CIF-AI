from sentence_transformers import SentenceTransformer

class EmbeddingService:
    def __init__(self, model_name="nomic-ai/nomic-embed-text-v1.5"):
        """
        Initializes the Embedding Service with the specified model.
        ✅ STEP 3 — Load Model
        """
        self.model = SentenceTransformer(
            model_name,
            trust_remote_code=True
        )

    def embed_document(self, text: str):
        """
        Generates embeddings for document chunks with the required prefix.
        ✅ STEP 4 — Generate Document Embeddings
        """
        prefixed = f"search_document: {text}"
        embedding = self.model.encode(prefixed)
        return embedding.tolist()

    def embed_query(self, query: str):
        """
        Generates embeddings for user queries with the required prefix.
        ✅ STEP 6 — Embed User Queries
        """
        prefixed = f"search_query: {query}"
        embedding = self.model.encode(prefixed)
        return embedding.tolist()
