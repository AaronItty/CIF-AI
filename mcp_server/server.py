"""
CIF-AI MCP Tool Server — powered by FastMCP.
Runs on port 8004 as an isolated microservice.

Tools are exposed via the standard MCP protocol.
The Agent Core connects as an MCP Client and discovers tools dynamically.
"""
import os
import uuid
from typing import Optional
from fastmcp import FastMCP
from dotenv import load_dotenv
from supabase import create_client, Client

load_dotenv()

mcp = FastMCP("CIF-AI Tools")

# ── Client / External Database (for shopping tools) ────────────
CLIENT_SUPABASE_URL = os.getenv("CLIENT_SUPABASE_URL")
CLIENT_SUPABASE_ANON_KEY = os.getenv("CLIENT_SUPABASE_ANON_KEY")

# ── Internal / Platform Database (for escalation, KB, etc.) ────
OUR_SUPABASE_URL = os.getenv("OUR_SUPABASE_URL")
OUR_SUPABASE_KEY = os.getenv("OUR_SUPABASE_KEY") or os.getenv("OUR_SUPABASE_ANON_KEY")
NOMIC_API_KEY = os.getenv("NOMIC_KEY") or os.getenv("NOMIC_API_KEY")
DEFAULT_ORG_ID = os.getenv("DEFAULT_ORG_ID", "302945a7-2a4b-4b78-a764-daa12777fbaf")


def _get_client_db() -> Client:
    """Returns a Supabase client for the external/client database."""
    if not CLIENT_SUPABASE_URL or not CLIENT_SUPABASE_ANON_KEY:
        raise ValueError("CLIENT_SUPABASE_URL and CLIENT_SUPABASE_ANON_KEY must be set in .env")
    return create_client(CLIENT_SUPABASE_URL, CLIENT_SUPABASE_ANON_KEY)


def _get_platform_db() -> Client:
    """Returns a Supabase client for the internal platform database."""
    if not OUR_SUPABASE_URL or not OUR_SUPABASE_KEY:
        raise ValueError("OUR_SUPABASE_URL and OUR_SUPABASE_KEY must be set in .env")
    return create_client(OUR_SUPABASE_URL, OUR_SUPABASE_KEY)


# ═══════════════════════════════════════════════════════════════
# SHOPPING TOOLS (migrated from shopping_tools.py)
# ═══════════════════════════════════════════════════════════════

@mcp.tool()
async def search_item(item_name: str) -> dict:
    """
    Search for a product or item by name across all available stores.
    Returns matching products with store name, price, product_id, and store_id.
    """
    try:
        sb = _get_client_db()
        products_res = sb.table("products").select("id, name, price, store_id") \
            .ilike("name", f"%{item_name}%").eq("is_in_stock", True).execute()
        products = products_res.data

        if not products:
            return {"status": "success", "results": [], "message": f"No in-stock items found matching '{item_name}'."}

        # Get store names
        store_ids = list(set([p["store_id"] for p in products if p.get("store_id")]))
        stores_res = sb.table("stores").select("id, store_name").in_("id", store_ids).execute()
        stores = {s["id"]: s["store_name"] for s in stores_res.data}

        results = []
        for p in products:
            results.append({
                "product_id": p["id"],
                "item_name": p["name"],
                "price": p["price"],
                "store_id": p["store_id"],
                "store_name": stores.get(p["store_id"], "Unknown Store")
            })

        return {"status": "success", "results": results}
    except Exception as e:
        return {"status": "error", "message": str(e)}


@mcp.tool()
async def buy_item(
    store_id: str,
    product_id: str,
    quantity: int,
    customer_name: str,
    customer_phone: str,
    customer_email: str,
    pincode: str,
    delivery_address: Optional[str] = None
) -> dict:
    """
    Place an order to buy a specific product for the customer.
    Requires store_id and product_id (from search_item results), quantity,
    customer_name, customer_phone, customer_email, and pincode.
    delivery_address is optional (defaults to pickup if not provided).
    Do not use placeholder values like 'unknown' — ask the user for real details first.
    """
    try:
        import httpx

        if not CLIENT_SUPABASE_URL:
            return {"status": "error", "message": "Supabase URL missing."}

        endpoint = f"{CLIENT_SUPABASE_URL}/functions/v1/Place-Order"
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {CLIENT_SUPABASE_ANON_KEY}"
        }

        payload = {
            "checkout_session_id": str(uuid.uuid4()),
            "store_id": store_id,
            "customer": {
                "name": customer_name,
                "phone": customer_phone,
                "email": customer_email
            },
            "delivery": {
                "method": "pickup" if not delivery_address else "delivery",
                "address": delivery_address,
                "lat": None, "lng": None, "date": None,
                "time_slot": None, "pincode": pincode,
                "landmark": None, "notes": None
            },
            "items": [
                {
                    "product_id": product_id,
                    "quantity": quantity,
                    "variant": None,
                    "custom_note": "Order placed via AI Agent"
                }
            ],
            "notes": "",
            "payment_method": "online"
        }

        async with httpx.AsyncClient() as client:
            response = await client.post(endpoint, json=payload, headers=headers)
            response.raise_for_status()
            data = response.json()

            return {
                "status": "success",
                "payment_link_url": data.get("payment_link_url"),
                "message": "Order placed successfully. Please review the payment link."
            }

    except Exception as e:
        error_body = ""
        if hasattr(e, 'response') and e.response:
            error_body = e.response.text
        return {"status": "error", "message": str(e), "details": error_body}


# ═══════════════════════════════════════════════════════════════
# ESCALATION TOOL
# ═══════════════════════════════════════════════════════════════

@mcp.tool()
async def escalate_to_human(session_id: str, reason: str, user_contact: str = "", channel: str = "unknown") -> dict:
    """
    Transfer the current conversation to a human support agent.
    Provide a clear reason summarizing why the conversation is being escalated.
    
    This tool will:
    1. Update the conversation status in the database
    2. Log the escalation reason
    3. Send a detailed email notification to the support team
    """
    import httpx
    from datetime import datetime
    
    escalation_email = os.getenv("ESCALATION_EMAIL", "")
    email_service_url = os.getenv("EMAIL_SERVICE_URL", "http://localhost:8003/api/v1/send")
    
    try:
        sb = _get_platform_db()

        # 1. Update conversation status to 'escalated'
        sb.table("conversations").update({
            "status": "escalated"
        }).eq("id", session_id).execute()

        # 2. Log the escalation
        sb.table("escalations").insert({
            "conversation_id": session_id,
            "reason": reason,
            "status": "pending_operator"
        }).execute()

        # 3. Fetch full conversation history for the email
        chat_history = sb.table("messages") \
            .select("role, content, created_at") \
            .eq("session_id", session_id) \
            .order("created_at") \
            .execute()
        
        messages = chat_history.data or []
        
        # 4. Format the conversation log
        log_lines = []
        for msg in messages:
            role = msg.get("role", "unknown")
            content = msg.get("content", "")
            timestamp = msg.get("created_at", "")
            # Truncate timestamp to readable format
            if timestamp and len(timestamp) > 19:
                timestamp = timestamp[:19]
            log_lines.append(f"[{role}] {timestamp}: {content}")
        
        conversation_log = "\n".join(log_lines) if log_lines else "(No messages found in history)"
        
        # 5. Build the email
        subject = f"[ESCALATED] {reason[:80]}"
        
        body = (
            f"ESCALATION SUMMARY\n"
            f"==================\n"
            f"{reason}\n\n"
            f"CONTACT INFORMATION\n"
            f"===================\n"
            f"Customer: {user_contact or 'Unknown'}\n"
            f"Channel: {channel}\n"
            f"Session ID: {session_id}\n"
            f"Escalated at: {datetime.utcnow().strftime('%Y-%m-%d %H:%M UTC')}\n\n"
            f"HOW TO RESPOND\n"
            f"==============\n"
        )
        
        if channel == "email" and user_contact:
            body += f"Reply directly to the customer at: {user_contact}\n"
        elif user_contact:
            body += f"Customer contact: {user_contact} (via {channel})\n"
        else:
            body += f"Check the Dashboard for this session to respond.\n"
        
        body += (
            f"\nFULL CONVERSATION LOG\n"
            f"=====================\n"
            f"{conversation_log}\n"
        )
        
        # 6. Send the email via Email Service (port 8003)
        email_sent = False
        if escalation_email:
            try:
                async with httpx.AsyncClient() as client:
                    resp = await client.post(email_service_url, json={
                        "recipient_id": escalation_email,
                        "message": body,
                        "subject": subject
                    }, timeout=15.0)
                    
                    if resp.status_code == 200:
                        email_sent = True
                        print(f"[Escalation] Email sent to {escalation_email}")
                    else:
                        print(f"[Escalation] Email service returned {resp.status_code}: {resp.text}")
            except Exception as email_err:
                print(f"[Escalation] Failed to send email notification: {email_err}")
        else:
            print("[Escalation] No ESCALATION_EMAIL configured, skipping email notification.")

        return {
            "status": "escalated",
            "email_sent": email_sent,
            "message": f"Conversation {session_id} has been escalated. Reason: {reason}"
        }
    except Exception as e:
        return {"status": "error", "message": f"Escalation failed: {str(e)}"}


# ═══════════════════════════════════════════════════════════════
# CONVERSATION HISTORY TOOL
# ═══════════════════════════════════════════════════════════════

@mcp.tool()
async def get_conversation_history(session_id: str, max_messages: int = 20) -> dict:
    """
    Retrieve past conversation messages for a given session.
    Use this when the user references something from a previous interaction,
    or when you need context about what was discussed earlier in the conversation.
    Returns the most recent messages (up to max_messages) with role and content.
    """
    try:
        sb = _get_platform_db()
        resp = sb.table("messages").select("role, content, created_at") \
            .eq("session_id", session_id) \
            .order("created_at", desc=True) \
            .limit(max_messages) \
            .execute()
        
        messages = resp.data or []
        # Reverse to chronological order
        messages.reverse()
        
        formatted = []
        for msg in messages:
            formatted.append({
                "role": msg.get("role", "unknown"),
                "content": msg.get("content", "")[:500],  # Truncate long messages
                "timestamp": msg.get("created_at", "")
            })
        
        return {
            "status": "success",
            "session_id": session_id,
            "message_count": len(formatted),
            "messages": formatted
        }
    except Exception as e:
        return {"status": "error", "message": str(e)}


# ═══════════════════════════════════════════════════════════════
# RAG KNOWLEDGE BASE TOOL
# ═══════════════════════════════════════════════════════════════

@mcp.tool()
async def query_knowledge_base(query: str) -> dict:
    """
    Search the organization's knowledge base for information relevant to the query.
    Use this when the customer asks about policies, FAQs, procedures, shipping,
    returns, store hours, or any information that may be in uploaded documents.
    Returns the most relevant text fragments from the knowledge base.
    """
    try:
        import requests

        if not NOMIC_API_KEY:
            return {"status": "error", "message": "NOMIC_API_KEY not configured."}

        # 1. Embed the query using Nomic API
        embed_response = requests.post(
            "https://api-atlas.nomic.ai/v1/embedding/text",
            headers={
                "Authorization": f"Bearer {NOMIC_API_KEY}",
                "Content-Type": "application/json"
            },
            json={
                "model": "nomic-embed-text-v1.5",
                "texts": [f"search_query: {query}"]
            }
        )
        embed_response.raise_for_status()
        query_embedding = embed_response.json().get("embeddings", [[]])[0]

        if not query_embedding:
            return {"status": "error", "message": "Failed to generate embedding for query."}

        # 2. Vector search in OUR_SUPABASE
        sb = _get_platform_db()
        result = sb.rpc("match_documents", {
            "query_embedding": query_embedding,
            "match_threshold": 0.60,
            "match_count": 3
        }).execute()

        matches = result.data or []

        if not matches:
            return {
                "status": "success",
                "results": [],
                "message": f"No relevant knowledge found for '{query}'. Try rephrasing or ask the customer to clarify."
            }

        # 3. Return the matching chunks
        formatted = []
        for match in matches:
            formatted.append({
                "content": match.get("content", ""),
                "similarity": round(match.get("similarity", 0), 3)
            })

        return {
            "status": "success",
            "results": formatted,
            "message": f"Found {len(formatted)} relevant knowledge base entries."
        }

    except Exception as e:
        return {"status": "error", "message": f"Knowledge base search failed: {str(e)}"}


# ═══════════════════════════════════════════════════════════════
# SERVER ENTRY POINT
# ═══════════════════════════════════════════════════════════════

if __name__ == "__main__":
    print("▶ Starting CIF-AI MCP Tool Server on port 8004...")
    mcp.run(transport="sse", host="0.0.0.0", port=8004)
