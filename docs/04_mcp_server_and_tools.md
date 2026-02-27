# 04 - MCP Server and Tools Layer

## Subsystem Overview
The critical isolated layer managing all external tool integrations. The MSME SaaS Core lives separately from actual company backend data. 

## Ownership & Boundaries
- **Owned by:** Integrations/Service Team
- **Boundary:** The SaaS Core can ONLY access backend company actions through the Model Context Protocol (MCP) Server. The MCP Server ensures strict validation and permission enforcement before executing logic.

## Architecture & Interfaces
- **MCP Server:** Runs on a separate port or instance. Exposes an RPC-like interface mapping tool schemas exactly to the LLM's function-calling schemas.
- **Tool Registry:** In-memory map of `tool_name` -> `BaseTool` implementation instance.
- **Permission Manager:** Validates API keys/Role credentials passed from the Agent Core.

### Tool Interface (`BaseTool`)
All skills MUST implement:
1. `name`: Unique identifier.
2. `description`: Prompt instructions explicitly detailing boundaries.
3. `schema`: JSON schema ensuring typed parameters.
4. `execute(kwargs)`: Action body returning a structured dict.

## Flow Diagram
```text
                  (SaaS Network)                        |  (Client Network / Isolated Subnet)
                                                        |
[Agent Core Controller]                                 | [MCP Server `server.py`]
      |                                                 |        |
      |-- (POST /execute {tool: 'check_inventory'}) --->|        |
                                                        |        ├-- [PermissionManager] (Verifies rights)
                                                        |        ├-- [ToolRegistry] (Locates InventoryCheckTool)
                                                        |        └-- [InventoryCheckTool.execute(sku)]
                                                        |                 |
                                                        |                 v
                                                        |            (External ERP DB)
      |<-- (Response: {"status":"success", count: 42})--|
```

## Service Integration Design
Because MSMEs operate on massively varied tooling stacks (Shopify, QuickBooks, custom SQL), the Service Layer maps their messy realities to our standardized `BaseTool`. The `example_tool.py` includes mocked forms of `RefundTool` and `InventoryCheckTool` representing typical integrations.

## Future Extensibility Notes
- The MCP Server can be distributed. Client companies could host the MCP server *inside their own VPC*, ensuring zero outside access to their raw databases, while the SaaS Core only routes parameter-safe tool execution requests.

## TODOs
- [ ] Build proper JSON-RPC over HTTP payload formats for MCP requests.
- [ ] Expand PermissionManager with hierarchical RBAC (Role-Based Access Control).
- [ ] Write integration test battery for external failure states.
