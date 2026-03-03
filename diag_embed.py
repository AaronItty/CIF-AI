import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from agent_core.embeddings import EmbeddingService

try:
    print("Initializing EmbeddingService...")
    service = EmbeddingService()
    text = "Shipping charges are a flat ₹99."
    print(f"Testing embedding for text: {text}")
    vector = service.embed_document(text)
    print(f"Success! Vector length: {len(vector)}")
except Exception as e:
    print(f"Failed: {e}")
    import traceback
    traceback.print_exc()
