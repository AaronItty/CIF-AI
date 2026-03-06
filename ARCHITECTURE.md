# Architecture Documentation: CIF-AI

This document provides a detailed breakdown of the modules shown in the system architecture diagram and maps them to their corresponding implementation in the codebase.

## System Overview
The CIF-AI platform is a multi-layered autonomous AI system built for **multi-channel communication** (Telegram/Email) and **document-augmented reasoning** (RAG).

---

## 1. Presentation & Dashboard Layer (Blue)
*   **Frontend Web Dashboard**: A React-based UI located in the `dashboard/` directory. It provides the primary interface for managing conversations, viewing analytics, and uploading knowledge documents.
*   **Core API Server**: A FastAPI application in [main.py](file:///c:/Users/admin/Desktop/cproject/CIF-AI/main.py). It serves as the primary backend for the dashboard and handles external webhooks on port **8001**.

---

## 2. Service & Execution Layer (Orange)
*   **Knowledge Base Service**: A dedicated microservice in [app-service.py](file:///c:/Users/admin/Desktop/cproject/CIF-AI/app-service.py) running on port **8000**. It handles the ingestion, vectorization, and querying of documents.
*   **Document Vectorization & Embeddings**: Logic implemented in [embeddings.py](file:///c:/Users/admin/Desktop/cproject/CIF-AI/agent_core/embeddings.py) that converts text into searchable vector representations.
*   **MCP Tool Server**: Built using the Model Context Protocol (MCP) in the `mcp_server/` directory. It provides the agent with dynamic capabilities (tools) such as database lookups or order placement.

---

## 3. Communication & Ingest Layer (Green)
*   **Email Service**: Located in [email_service.py](file:///c:/Users/admin/Desktop/cproject/CIF-AI/communication/email_service.py), managing SMTP/IMAP integrations.
*   **Telegram Bot**: Implemented in [telegram_bot.py](file:///c:/Users/admin/Desktop/cproject/CIF-AI/communication/telegram_bot.py), handling real-time messaging updates.
*   **Data Flow**: Raw messages are "normalized" using schemas to ensure the Agent Core receives a consistent format regardless of the source channel.

---

## 4. Agent AI Core Layer (Purple)
The "brain" of the system, located in the `agent_core/` directory.
*   **Planning Loop**: Found in [planning_loop.py](file:///c:/Users/admin/Desktop/cproject/CIF-AI/agent_core/planning_loop.py). It orchestrates the cyclic "Reason -> Evaluate -> Execute -> Update" process for every request.
*   **Reasoning Engine**: Found in [reasoning_engine.py](file:///c:/Users/admin/Desktop/cproject/CIF-AI/agent_core/reasoning_engine.py). It interacts with LLMs to interpret user intent and generate human-like responses.
*   **Controller**: Found in [controller.py](file:///c:/Users/admin/Desktop/cproject/CIF-AI/agent_core/controller.py). A deterministic logic layer that validates AI-proposed actions against internal rules before execution.
*   **Policy Engine**: Found in [policy_engine.py](file:///c:/Users/admin/Desktop/cproject/CIF-AI/agent_core/policy_engine.py). Manages security, permissions (RBAC), and autonomous thresholds.
*   **State Manager**: Found in [state_manager.py](file:///c:/Users/admin/Desktop/cproject/CIF-AI/agent_core/state_manager.py). Handles short-term conversation memory and long-term session persistence in the database.

---

## 5. Data Store
*   **Supabase DB**: A central PostgreSQL database with **pgvector** support. It stores message history, user metadata, and vectorized document chunks for RAG. Database interaction logic is managed by the `SupabaseClient` in [db_client.py](file:///c:/Users/admin/Desktop/cproject/CIF-AI/shared/data_access/db_client.py).

---

## Detailed Data Flow Interaction

1.  **Ingestion**: A user sends a message (e.g., via Telegram).
2.  **Normalization**: The `TelegramBot` converts the update into a `NormalizedMessage`.
3.  **Core Processing**:
    *   `PlanningLoop` receives the message.
    *   `ReasoningEngine` identifies the intent (e.g., "Check order status").
    *   `Controller` validates if the agent has the necessary permissions.
4.  **Retrieval/Action**:
    *   If knowledge is needed, the agent queries the `Knowledge Base Service`.
    *   If a tool is needed, the agent calls the `MCP Tool Server`.
5.  **Response**: The `ReasoningEngine` synthesizes the tool results into a final response, which is then sent back through the original communication channel.

---

# Technical Deep Dive: The "How" & "Why"

## 1. Presentation & Dashboard Layer (Blue)

### **Frontend Web Dashboard**
*   **The "How":** Built as a React SPA (Single Page Application) using **Vite** for high-performance development and bundling. It uses **Tailwind CSS** for its "premium" UI and **pnpm/bun** for fast dependency management.
*   **The "Why":** An SPA approach ensures that the dashboard feels like a native app, with instantaneous transitions between conversation logs and knowledge management. Vite's Hot Module Replacement (HMR) allows for rapid UI iteration.

### **Core API Server**
*   **The "How":** A **FastAPI** instance in [main.py](file:///c:/Users/admin/Desktop/cproject/CIF-AI/main.py) running on port **8001**. It uses Pydantic for strict input validation and `uvicorn` as the ASGI server.
*   **The "Why":** FastAPI is chosen for its native `async/await` support, which is critical for an Agentic UI. The server must handle long-running LLM stream requests and multiple tool executions without blocking the dashboard's event loop.

---

## 2. Service & Execution Layer (Orange)

### **Knowledge Base Service**
*   **The "How":** A decoupled FastAPI microservice on port **8000**. It handles heavy document processing (PDF parsing, text chunking) separately from the main API.
*   **The "Why":** Ingestion is resource-intensive. By separating it, a large document upload won't lag the real-time Telegram bot or the dashboard UI.

### **Document Vectorization & Embeddings**
*   **The "How":** Uses the `EmbeddingService` in [embeddings.py](file:///c:/Users/admin/Desktop/cproject/CIF-AI/agent_core/embeddings.py) to wrap external LLM embedding models. Documents are split into overlapping "chunks" to maintain context between snippets.
*   **The "Why":** Vectorization enables **Semantic Search**. Instead of looking for exact keywords, the AI finds documents with similar *meanings*, which is the foundation of a robust RAG system.

### **MCP Tool Server**
*   **The "How":** Implements the **Model Context Protocol (MCP)**. This allows the Agent Core to "discover" tools at runtime. If you add a new database or an external API, the Agent automatically learns how to use it by reading the MCP manifest.
*   **The "Why":** This ensures **Loose Coupling**. The Agent Core doesn't need to know *how* to talk to the database; it just knows *what* tool to call, and the MCP server handles the implementation.

---

## 3. Communication & Ingest Layer (Green)

### **Email & Telegram Adapters**
*   **The "How":** Multi-threaded or async listeners that poll/webhook for messages. They use the **Adapter Pattern** to convert raw data into a standard [NormalizedMessage](file:///c:/Users/admin/Desktop/cproject/CIF-AI/communication/schemas/normalized_message.py).
*   **The "Why":** The Agent Core shouldn't care if a message came from Telegram or Email. Normalization allows the core logic to remain "channel agnostic," making it trivial to add Slack or WhatsApp in the future.

---

## 4. Agent AI Core Layer (Purple)

### **Planning Loop (OODA)**
*   **The "How":** An asynchronous `while` loop in [planning_loop.py](file:///c:/Users/admin/Desktop/cproject/CIF-AI/agent_core/planning_loop.py). It follows the **OODA** (Observe, Orient, Decide, Act) pattern:
    1.  **Observe**: Read message + memory.
    2.  **Orient**: Extract context and intent.
    3.  **Decide**: Determine if a tool is needed.
    4.  **Act**: Execute the tool and update the state.
*   **The "Why":** Complex tasks (like placing an order) require multiple steps. A loop allows the agent to check its work and recover from tool failures autonomously.

### **Controller & Policy Engine**
*   **The "How":** Deterministic guardrails. The `Controller` checks for "Action Completeness" (e.g., *Does this 'buy' action have a valid phone number?*), while the `Policy Engine` checks for "Authorization" (e.g., *Is this user allowed to delete files?*).
*   **The "Why":** LLMs are probabilistic and can "hallucinate." These modules provide a **Safety Sandbox**, ensuring the AI only acts within defined logical and security boundaries.

### **State Manager**
*   **The "How":** Manages the "Window of Context." It intelligently prunes and summarizes old messages to stay within LLM token limits while persisting the full history in Supabase.
*   **The "Why":** The agent needs "Long-term Memory" to provide a personalized experience and "Short-term Memory" to follow a conversation thread.

---

## 5. Data Store

### **Supabase (pgvector)**
*   **The "How":** Uses PostgreSQL's `pgvector` extension to store 1536-dimensional (or similar) vectors. Queries use **Cosine Similarity** to find the closest document matches.
*   **The "Why":** Supabase provides a unified platform for Auth, File Storage, and Database. Having vectors in the same DB as user data allows for "Hybrid Search" (e.g., searching documents *only* within a specific user's permissions).

---

# Architectural Assumptions

This system is built upon several key technical and operational assumptions:

### 1. Technical & Infrastructure
*   **External Service Reliability**: We assume high availability (99.9%+) of the LLM provider (Groq/OpenAI) and Supabase. The system does not currently have an offline fallback for core reasoning.
*   **Decoupled Performance**: We assume that running the `Knowledge Base Service` as a separate microservice on the same internal network provides enough isolation for heavy document ingestion without impacting real-time bot responsiveness.
*   **Vector Search Scaling**: We assume that PostgreSQL with `pgvector` and an HNSW index can maintain sub-second search latency as the document store grows into the thousands of chunks.

### 2. AI & Reasoning
*   **Intent Determinism**: We assume that the LLM can consistently map varied human language to a fixed set of MCP tool definitions provided in the prompt.
*   **Context Pruning**: We assume that the `StateManager's` strategy for pruning conversation history (keeping recent messages + summary) preserves all critical context needed for the next turn.
*   **LLM "Following"**: We assume the model is capable of following complex system instructions and adhering to the JSON schemas required for intent extraction.

### 3. Security & Governance
*   **Trust in Controller**: We assume that the deterministic `Controller` is the final authority. If the AI hallucinates an action, we assume the Controller's validation rules (e.g., checking for required fields) will catch and block it.
*   **Trusted Internal Network**: We assume the 8000/8001 microservice communication happens within a private network or a secured VPC, as inter-service traffic is currently unencrypted in the default dev setup.

### 4. Operational
*   **Async Tolerance**: We assume that users on Telegram and Email are tolerant of a "processing delay" (3–10 seconds) inherent in the multi-step Agentic OODA loop.
*   **Document Structure**: We assume that knowledge assets uploaded by admins are mostly text-heavy and that our parsing logic (via LangChain or similar) can extract meaningful semantic units from them.
