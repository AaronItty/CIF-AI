from sentence_transformers import SentenceTransformer

print("Loading model...")
model = SentenceTransformer(
    "nomic-ai/nomic-embed-text-v1.5",
    trust_remote_code=True
)

print("Generating embedding...")

text = "search_document: This is a refund policy for our airline tickets."

embedding = model.encode(text)

print("Embedding length:", len(embedding))
print("First 5 values:", embedding[:5])
