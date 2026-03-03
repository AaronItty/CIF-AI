"""Simple launcher for the CIF-AI FastMCP Tool Server."""
from mcp_server.server import mcp

if __name__ == "__main__":
    print("▶ Starting CIF-AI MCP Tool Server on port 8004...")
    mcp.run(transport="sse", port=8004)
