"""
Main MCP Server runtime using the official Standard MCP Python SDK over SSE + FastAPI.
This allows the Agent Core to connect as an MCP Client and execute tools securely.
"""
import os
import json
from contextlib import asynccontextmanager
from fastapi import FastAPI, Depends, HTTPException, Header, Request
from starlette.responses import StreamingResponse
from mcp.server import Server
from mcp.server.sse import SseServerTransport
from mcp.types import Tool, TextContent

from mcp_server.shopping_tools import SearchItemTool, BuyItemTool

# Initialize our tool implementations
search_tool = SearchItemTool()
buy_tool = BuyItemTool()

# Simple shared secret for SaaS Core -> MCP Server authorization
MCP_SHARED_SECRET = os.getenv("MCP_SHARED_SECRET", "super-secret-mcp-key-123")

def verify_token(authorization: str = Header(None)):
    """Simple middleware to ensure only authorized clients can access the MCP Server."""
    if not authorization or authorization != f"Bearer {MCP_SHARED_SECRET}":
        raise HTTPException(status_code=401, detail="Unauthorized MCP Client")

# Setup MCP Server
mcp = Server("msme-shopping-mcp")

@mcp.list_tools()
async def handle_list_tools() -> list[Tool]:
    """Exposes tool schemas to the MCP Client."""
    return [
        Tool(
            name=search_tool.name,
            description=search_tool.description,
            inputSchema=search_tool.schema
        ),
        Tool(
            name=buy_tool.name,
            description=buy_tool.description,
            inputSchema=buy_tool.schema
        )
    ]

@mcp.call_tool()
async def handle_call_tool(name: str, arguments: dict) -> list[TextContent]:
    """Routes execution requests to our standard BaseTool implementations."""
    if name == search_tool.name:
        result = await search_tool.execute(**arguments)
        return [TextContent(type="text", text=json.dumps(result))]
        
    elif name == buy_tool.name:
        result = await buy_tool.execute(**arguments)
        return [TextContent(type="text", text=json.dumps(result))]
        
    else:
        raise ValueError(f"Unknown tool: {name}")


# Ensure graceful Server initialization
sse_transport = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    global sse_transport
    # Startup logic: Transport initialized per request in SSE model, 
    # but lifespan hook required for future cleanups
    yield
    # Shutdown logic
    pass

app = FastAPI(title="SaaS MCP Server", lifespan=lifespan)

@app.get("/sse")
async def handle_sse(request: Request, _auth = Depends(verify_token)):
    """SSE endpoint for MCP Client to connect to."""
    global sse_transport
    sse_transport = SseServerTransport("/messages")
    
    async def run_mcp():
        await mcp.connect(sse_transport)
        
    # Start the event loop for this transport connection
    import asyncio
    asyncio.create_task(run_mcp())
    
    async def generate():
        async for message in sse_transport.messages():
            yield message

    return StreamingResponse(generate(), media_type="text/event-stream")


@app.post("/messages")
async def handle_messages(request: Request, _auth = Depends(verify_token)):
    """Message ingestion endpoint for the established SSE transport."""
    global sse_transport
    if sse_transport is None:
        raise HTTPException(status_code=400, detail="SSE transport not initialized. Connect to /sse first.")
        
    data = await request.json()
    await sse_transport.handle_post_message(data)
    return {"status": "ok"}
