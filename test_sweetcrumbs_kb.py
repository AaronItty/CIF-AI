import asyncio
import os
import sys

# Ensure the app root is in path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from dashboard.backend.db_client import SupabaseClient
from agent_core.embeddings import EmbeddingService
from agent_core.knowledge_base_service import KnowledgeBaseService

# --- SweetCrumbs Knowledge Base Content ---
SWEETCRUMBS_DOC = """
# About SweetCrumbs
SweetCrumbs is a premium online bakery specialized in artisanal, made-to-order cookies. We deliver freshly baked goodness across India, ensuring that every bite tastes like home.

# Order Processing
All orders are processed within 24-48 hours. Since our cookies are baked fresh upon order, we do not keep ready stock. Orders placed on Sundays or public holidays are processed on the next working day.

# Shipping Policy
We offer pan-India delivery. Delivery typically takes 3-5 business days for metro cities and 5-7 business days for other locations. Shipping charges are a flat ₹99 for orders below ₹999, and free for orders above ₹999. Our packaging is vacuum-sealed to ensure freshness during transit.

# Refund & Return Policy
Due to the perishable nature of our products, we do not accept returns. However, if you receive a damaged or incorrect order, please contact support within 24 hours of delivery with photo evidence for a full refund or replacement.

# Order Cancellation Policy
You can cancel your order within 2 hours of placement. Since baking starts shortly after, we cannot accept cancellations once the preparation process has begun.

# Allergy & Ingredient Information
Our cookies contain wheat, butter, and sugar. Some varieties contain nuts (almonds, walnuts, hazelnuts). All our products are baked in a facility that handles nuts and dairy. Please check the individual product page for specific allergen details.

# Product Shelf Life
Our cookies have a shelf life of 15 days when stored in an airtight container in a cool, dry place. For best taste, we recommend consuming them within 7 days of delivery.

# Bulk & Corporate Orders
We accept bulk orders for events and corporate gifting. Please reach out to us at bulk@sweetcrumbs.in for customized packaging and discounted pricing for orders above 50 boxes.

# Loyalty Program – SweetPoints
Earn 1 SweetPoint for every ₹10 spent. SweetPoints can be redeemed for discounts on future orders. 100 SweetPoints = ₹50 discount. Points are valid for 12 months from the date of earning.

# Customer Support
Our support team is available Monday to Saturday, 10 AM to 7 PM IST. You can reach us via email at support@sweetcrumbs.in or via WhatsApp at +91-9876543210.
"""

VALID_QUERIES = [
    "What is the refund policy?",
    "How long does delivery take for metro cities?",
    "What are the shipping charges?",
    "Can I cancel my order after 2 hours?",
    "What allergens are present in the cookies?",
    "What are the support hours?",
    "How does the SweetPoints loyalty program work?"
]

INVALID_QUERIES = [
    "How to test Telegram chatbot integration?",
    "How to deploy a webhook?",
    "Explain vector embeddings",
    "How to build a chatbot?"
]

async def run_sweetcrumbs_test():
    try:
        print("\n" + "="*50)
        print("SIPPING SWEETCRUMBS KB TEST")
        print("="*50)
        
        db_client = SupabaseClient()
        embed_service = EmbeddingService()
        kb_service = KnowledgeBaseService(db_client, embed_service)
        
        org_id = kb_service.get_default_org_id()
        print(f"Target Org ID: {org_id}")

        # 1. Ingest Bakery Doc
        print("\n[1/3] Ingesting SweetCrumbs Knowledge Base...")
        doc_id = await kb_service.ingest_document(
            organization_id=org_id,
            name="SweetCrumbs_Policy.txt",
            file_bytes=SWEETCRUMBS_DOC.encode('utf-8')
        )
        print(f"DONE: Document Ingested (ID: {doc_id})")

        # Verify chunks actually exist in DB
        chunks_res = db_client.get_client().table("document_chunks").select("count").eq("document_id", doc_id).execute()
        print(f"DEBUG: Chunks in DB: {chunks_res.data}")

        # 2. Test Valid Queries
        print("\n[2/3] Running Valid Query Suite (Expected: Relevant Results)...")
        THRESHOLD = 0.50 # Relaxed for prototype logging
        
        for query in VALID_QUERIES:
            print(f"\nQUERY: '{query}'")
            res = await kb_service.search_knowledge_base(org_id, query, limit=3)
            matches = res.get("results", [])
            
            if not matches:
                print(f"FAIL: No results found for valid query.")
                continue
                
            found_high_similarity = False
            for match in matches:
                score = match.get("similarity", 0)
                content = match.get("content", "")[:100].replace("\n", " ").strip() + "..."
                print(f"  - Score: {score:.4f} | Chunk: {content}")
                if score >= THRESHOLD:
                    found_high_similarity = True
            
            if found_high_similarity:
                print(f"PASS: Found relevant content above threshold {THRESHOLD}")
            else:
                print(f"WARN: Results found but all below threshold {THRESHOLD}")

        # 3. Test Invalid Queries
        print("\n[3/3] Running Invalid Query Suite (Expected: Low Similarity)...")
        for query in INVALID_QUERIES:
            print(f"\nQUERY: '{query}'")
            res = await kb_service.search_knowledge_base(org_id, query, limit=1)
            matches = res.get("results", [])
            
            if matches:
                match = matches[0]
                score = match.get("similarity", 0)
                content = match.get("content", "")[:100].replace("\n", " ").strip() + "..."
                print(f"  - Top Score: {score:.4f} | Chunk: {content}")
                if score < 0.45:
                    print(f"PASS: Appropriately low similarity score.")
                else:
                    print(f"FAIL: Unrelated query returned high similarity score!")
            else:
                print(f"PASS: No results returned.")

        # Cleanup
        # print("\nCleaning up...")
        # kb_service.delete_document(doc_id)
        # print("Done.")
        print("="*50)
        print("TEST COMPLETE")
        print("="*50)

    except Exception as e:
        print(f"\nTEST CRASHED: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    # Force UTF-8 for Windows consoles to avoid charmap errors
    if sys.platform == "win32":
        import io
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    asyncio.run(run_sweetcrumbs_test())
