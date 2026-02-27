import uvicorn
import os

if __name__ == "__main__":
    print("Starting MSME Shopping MCP Server on port 8000...")
    print("Ensure your HOSTED_BACKEND_URL and HOSTED_BACKEND_API_KEY environment variables are set!")
    
    # Run the FastAPI server which hosts the MCP SSE endpoints
    uvicorn.run("mcp_server.server:app", host="0.0.0.0", port=8000, reload=True)
