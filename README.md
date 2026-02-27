# Hybrid SaaS + Service Agentic AI Platform

A structured, modular Agentic AI Platform for MSMEs built with a Strict Controller Architecture, multi-channel support, and an isolated Service layer.

## System Architecture Overview

The system is strictly divided into 4 separated responsibilities to maintain scalability, security, and extensibility.

### 1. Communication Layer
Located in `/communication`.
Handles normalized input/output with various channels (Telegram, Email, Voice Stubs). It passes well-formed data to the Agent Core and does NOT make business logic decisions.

### 2. Agent Core
Located in `/agent_core`.
The "brain" of the platform. Utilizes a while-not-resolved `PlanningLoop`. Incorporates an LLM `ReasoningEngine` to formulate intents, and a deterministic `Controller` to enforce tool permissions and escalation boundaries using the `PolicyEngine`.

### 3. Dashboard + Supabase
Located in `/dashboard`.
All state and metadata persistence is routed through `SupabaseClient`. Stores `conversations`, `tool_logs`, `escalations`, and `users`. It also provides data via the `AnalyticsService` for a Frontend Web UI Dashboard.

### 4. MCP Server (Service Layer)
Located in `/mcp_server`.
The SaaS Core NEVER touches internal company backends or side-effects. Instead, the SaaS Core makes RPC calls over the Model Context Protocol (MCP) to this separate server. The MCP layer hosts integrations (`BaseTool` implementations) and verifies access rights via the `PermissionManager`.

## Getting Started

1. Set environment variables (see `shared/config.py`).
2. Install pip dependencies:
   ```bash
   pip install -r requirements.txt
   ```
3. Run the application:
   ```bash
   python app.py
   ```

*(Note: In production deployments, `/mcp_server` and `/app.py` SaaS core should be deployed as separate isolated services.)*

## Documentation

Full architectural documentation for each subsystem can be found in `/docs`:
- `01_communication_layer.md`
- `02_agent_core.md`
- `03_dashboard_and_supabase.md`
- `04_mcp_server_and_tools.md`
