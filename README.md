# Hybrid SaaS + Service Agentic AI Platform

A structured, modular Agentic AI Platform for MSMEs built with a Strict Controller Architecture, multi-channel support, an isolated Service layer, and a modern Web Dashboard.

## System Architecture Overview

The system is strictly divided into loosely coupled microservices and components to maintain scalability, security, and extensibility.

### 1. Frontend Web Dashboard (React/Vite)
Located in `/dashboard/frontend` and managed via the root `package.json`.
A modern web UI built with React, Vite, Shadcn UI, and Tailwind CSS. It interacts with the backend APIs to display analytics, manage knowledge bases, and configure the platform.

### 2. Core API Server (FastAPI)
Located in `main.py` (Runs on Port 8001).
Provides the SaaS Core APIs, including the Telegram Webhook and Dashboard REST endpoints. It integrates with Supabase for data persistence (conversations, tool logs, users, and escalations).

### 3. Dedicated Knowledge Base Service (FastAPI)
Located in `app-service.py` (Runs on Port 8000).
A dedicated service for managing embeddings, document vectorization, and the Knowledge Base API.

### 4. Agent Core Service
Located in `/agent_core` (Runs on Port 8002).
The "brain" of the platform. Utilizes a while-not-resolved `PlanningLoop`. Incorporates an LLM `ReasoningEngine` to formulate intents, and a deterministic `Controller` to enforce tool permissions and escalation boundaries using the `PolicyEngine`.

### 5. Communication Layer & Email Service
Located in `/communication` (Runs on Port 8003).
Handles normalized input/output with channels (like Telegram and Email). The Email Service runs as an independent microservice. It passes well-formed data to the Agent Core and does NOT make business logic decisions.

### 6. MCP Server (Service Layer)
Located in `/mcp_server` (Runs on Port 8004).
The SaaS Core NEVER touches internal company backends or side-effects directly. Instead, it makes RPC calls over the Model Context Protocol (MCP) to this separate server. The MCP layer hosts integrations and verifies access rights.

## Getting Started

1. Set your environment variables (see `.env` or `shared/config.py`).
2. Install Python dependencies:
   ```bash
   pip install -r requirements.txt
   ```
3. Install frontend Node.js dependencies:
   ```bash
   npm install
   ```
4. Run the backend microservices (Windows):
   ```bash
   start_microservices.bat
   ```
   *(This starts the Agent Core, Email Service, App Service, and MCP Server in separate terminal windows.)*
5. Run the Core API Server:
   ```bash
   python main.py
   ```
6. Run the Frontend Dashboard:
   ```bash
   npm run dev
   ```
