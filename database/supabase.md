# Organizations Table

The `organizations` table is the root tenant table of the SaaS platform.  
Each row represents one company using the AI Customer Interaction System.

This table enables secure multi-tenancy by acting as the parent entity
for operators, users, channels, conversations, documents, and analytics.

---

## Purpose

- Isolates company data (multi-tenant boundary)
- Stores billing plan information
- Holds default AI behavior configuration
- Enables usage tracking and plan enforcement
- Supports organization-level activation/deactivation

---

## Key Fields

### Identity
- `id` — UUID primary key
- `name` — Company name
- `business_description` — Used to prime AI system behavior

### Billing
- `plan` — Enum (`free`, `pro`, `enterprise`)
- `is_active` — Soft disable flag

### AI Configuration Defaults
- `default_temperature` — Base LLM temperature
- `escalation_threshold` — Confidence threshold before escalation
- `auto_escalation_enabled` — Whether AI can escalate automatically

### Usage Limits (Optional)
- `monthly_conversation_limit`
- `monthly_tool_call_limit`

### Audit
- `created_at`
- `updated_at` (auto-managed via trigger)

---

## Architectural Role

organizations
 ├── operators
 ├── channels
 ├── documents
 ├── users
 │    └── conversations
 │         ├── messages
 │         ├── escalations
 │         ├── tool_logs
 │         └── feedback

This structure ensures:

- Strong tenant isolation
- Clean SaaS boundary
- Scalable analytics
- Plan-based feature control

---

## Why This Matters

The organizations table is the foundation of:

- Row Level Security policies
- Billing enforcement
- Dashboard scoping
- AI behavior customization
- Enterprise scalability

Without this table, secure multi-tenant SaaS would not be possible.

# Operators Table

The `operators` table stores human staff members of each organization
who access the SaaS dashboard.

Operators are not end customers — they are company employees who:
- View conversations
- Handle escalations
- Manage channels
- Upload documents
- Monitor analytics

---

## Purpose

- Defines dashboard access control
- Enables role-based permissions
- Supports secure multi-tenant isolation
- Links Supabase authentication to organization identity

---

## Key Fields

### Identity
- `id` — Internal UUID
- `email` — Login identifier (unique per organization)
- `auth_user_id` — Links to Supabase `auth.users.id`

### Multi-Tenancy
- `organization_id` — Ensures data isolation per company

### Role-Based Access
- `role` — Enum:
  - `agent` → Handles conversations
  - `admin` → Manages team & channels
  - `owner` → Full control (billing-level)

### Status
- `is_active` — Soft-disable access
- `last_login_at` — Activity tracking

### Audit
- `created_at`
- `updated_at`

---

## Architectural Role

organizations
 └── operators
       ├── escalations (assigned_to)
       ├── documents (uploaded_by)
       └── dashboard access control

This table is central to:

- Row Level Security (RLS)
- Role-based policies
- Organization-scoped data visibility

---

## Why This Design Is Important

- Prevents cross-organization data leaks
- Allows granular permission control
- Supports enterprise-ready access management
- Decouples authentication from business logic

This table powers the secure human oversight layer
of the AI customer interaction system.

# Channels Table

The `channels` table stores communication channels connected
by each organization.

These channels allow the AI system to receive and respond to
customer interactions across multiple platforms.

---

## Purpose

- Enables multi-channel communication
- Stores integration configuration securely
- Tracks operational health of channels
- Supports channel-level analytics

---

## Supported Channel Types

- gmail
- telegram
- whatsapp
- phone
- webchat

---

## Key Fields

### Multi-Tenancy
- `organization_id` — Ensures strict tenant isolation

### Channel Info
- `type` — Enum defining platform
- `display_name` — Human-readable label
- `status` — active / inactive / error

### Configuration
- `config` — JSONB storing credentials (encrypted at app layer)

### Monitoring
- `last_error` — Most recent failure reason
- `last_active_at` — Last message timestamp
- `connected_at` — Initial connection time

### Audit
- `created_at`
- `updated_at`

---

## Architectural Role

organizations
 └── channels
       └── conversations
             └── messages

Channels form the communication entry point
for the AI customer interaction system.

---

## Why This Design Matters

- Clean abstraction across platforms
- Secure storage of integration credentials
- Enables channel-based analytics
- Scales across industries without backend access

This table powers the communication layer
of the SaaS system.

# Documents Table

The `documents` table stores files uploaded by each organization to power the AI knowledge base (RAG layer).

These documents are processed, chunked, embedded, and used by the AI system to generate accurate responses to customer queries.

---

## Purpose

- Stores uploaded knowledge base files
- Tracks processing lifecycle (upload → embedding → ready)
- Supports multi-tenant isolation
- Enables versioning and soft activation
- Provides audit tracking

---

## Key Fields

### Multi-Tenancy
- `organization_id` — Ensures strict tenant isolation

### File Metadata
- `name` — Original filename
- `storage_path` — Path in Supabase Storage
- `mime_type`
- `file_size_bytes`

### Processing Lifecycle
- `status` — `uploaded`, `processing`, `ready`, `failed`
- `chunk_count` — Number of chunks created
- `embedding_model` — Model used for vector embeddings
- `last_error` — Stores processing errors

### Versioning
- `version` — Supports document updates
- `is_active` — Allows soft disabling

### Ownership & Audit
- `uploaded_by` — Operator who uploaded the file
- `uploaded_at`
- `processed_at`
- `created_at`
- `updated_at`

---

## Architectural Role

organizations
 └── documents
       └── chunking + embedding
             └── vector retrieval layer

This table forms the foundation of the AI knowledge system,
enabling scalable and organization-specific retrieval.

---

## Important Notes

- Actual file contents are stored in Supabase Storage.
- Individual text chunks and embeddings are stored separately
  (e.g., in a vector table using pgvector).

This design ensures secure, scalable, and enterprise-ready
knowledge management for the SaaS platform.

# Users Table

The `users` table represents end customers who interact
with the AI system through connected channels.

These are not dashboard operators — they are external users
sending messages via email, Telegram, phone, or webchat.

---

## Purpose

- Tracks customer identity per organization
- Supports multi-channel identification
- Enables conversation history tracking
- Stores lightweight CRM-style metadata
- Powers analytics and personalization

---

## Key Fields

### Multi-Tenancy
- `organization_id` — Ensures strict tenant isolation

### Identity
- `email`
- `phone_number`
- `telegram_id`
- `external_user_id`

(Unique within each organization.)

### Profile
- `full_name`
- `metadata` — Custom attributes or CRM data

### Activity
- `last_interaction_at`
- `total_conversations`

### Status
- `is_blocked` — Prevents AI responses if needed

### Audit
- `created_at`
- `updated_at`

---

## Architectural Role

organizations
 └── users
       └── conversations
             └── messages

This table enables:

- Personalized AI responses
- Conversation history retrieval
- Customer analytics
- Multi-channel identity resolution

It forms the foundation of the customer layer
in the SaaS AI interaction system.

# Conversations Table

The `conversations` table represents a complete interaction thread
between a customer and the AI system.

Each conversation contains multiple messages and may involve
AI responses, tool calls, and human escalations.

---

## Purpose

- Groups messages into structured interaction threads
- Tracks conversation lifecycle (active → resolved → closed)
- Enables escalation handling
- Supports analytics and SLA monitoring
- Stores AI-generated metadata (summary, tags)

---

## Key Fields

### Multi-Tenancy
- `organization_id` — Strict tenant isolation

### Relationships
- `user_id` — End customer
- `channel_id` — Origin channel (Gmail, Telegram, etc.)

### Lifecycle
- `status` — active, escalated, resolved, closed
- `priority` — 1 (high) to 5 (low)
- `escalated_at`
- `resolved_at`
- `closed_at`

### Metrics
- `message_count`
- `tool_call_count`
- `ai_confidence_score`

### AI Metadata
- `summary` — AI-generated conversation summary
- `tags` — Categorization labels

### Audit
- `created_at`
- `updated_at`

---

## Architectural Role

organizations
 └── users
       └── conversations
             ├── messages
             ├── escalations
             ├── tool_logs
             └── feedback

This table is the core interaction unit of the platform.
All analytics, SLA tracking, escalation logic, and AI metrics
are derived from conversations.

---

## Why This Design Matters

- Enables scalable multi-channel support
- Supports AI + human hybrid workflows
- Powers analytics dashboards
- Allows SLA & performance monitoring
- Designed for high-scale SaaS deployment

# Messages Table

The `messages` table stores every individual message
within a conversation.

Messages may originate from:
- Customers (user)
- The AI assistant
- Human operators
- Internal system processes

---

## Purpose

- Stores full conversation history
- Enables AI and human hybrid workflows
- Tracks tool calls and AI metadata
- Supports analytics and cost tracking
- Maintains auditability

---

## Key Fields

### Multi-Tenancy
- `organization_id` — Ensures tenant isolation

### Relationships
- `conversation_id` — Parent conversation
- `operator_id` — If sent by human operator

### Message Identity
- `role` — user / assistant / operator / system
- `type` — text / image / audio / tool_call / etc.
- `content` — Main message body
- `metadata` — Channel or tool-specific data

### AI Tracking
- `token_count`
- `model_name`
- `latency_ms`
- `tool_name`

### Visibility
- `is_internal` — Hidden from customer
- `is_deleted` — Soft deletion flag

### Audit
- `created_at`
- `updated_at`

---

## Architectural Role

organizations
 └── conversations
       └── messages

All interaction intelligence flows through this table.

It powers:
- Chat UI rendering
- AI context memory
- Tool execution logging
- Cost analytics
- Compliance & auditing

---

## Why This Design Matters

This table forms the backbone of:

- AI memory construction
- Escalation workflows
- Performance monitoring
- Token usage tracking
- Enterprise audit requirements

It is the most critical data layer in the system.


# Escalations Table

The `escalations` table tracks human handoff events
when a conversation is transferred from the AI system
to a human operator.

This enables hybrid AI + human workflows and ensures
complex issues are handled appropriately.

---

## Purpose

- Tracks AI-to-human transitions
- Enables operator assignment
- Supports SLA monitoring
- Measures human response time
- Powers escalation analytics

---

## Key Fields

### Multi-Tenancy
- `organization_id` — Ensures strict tenant isolation

### Relationships
- `conversation_id` — Parent conversation
- `assigned_to` — Operator responsible

### Trigger Details
- `reason` — Why escalation occurred
- `triggered_by` — ai / user_request / operator / system
- `ai_confidence_score` — AI certainty at time of escalation
- `trigger_rule` — Which rule triggered escalation

### Lifecycle
- `status` — pending → assigned → in_progress → resolved → closed
- `priority` — 1 (high) to 5 (low)

### SLA Tracking
- `first_response_at` — When operator first replied
- `resolved_at` — When issue was resolved

### Audit
- `created_at`
- `updated_at`

---

## Architectural Role

organizations
 └── conversations
       └── escalations
             └── operators

This table enables:

- AI confidence-based escalation logic
- Operator workload tracking
- Human response time analytics
- SLA enforcement

---

## Why This Design Matters

Escalations are what make this system enterprise-ready.

It transforms the platform from a chatbot
into a collaborative AI-human interaction framework.

# Tool Logs Table

The `tool_logs` table records every tool or skill
execution performed by the AI system.

It acts as the observability and audit layer
for the agentic AI framework.

---

## Purpose

- Tracks all AI tool invocations
- Stores input and output payloads
- Monitors execution performance
- Enables cost tracking
- Supports debugging and compliance

---

## Key Fields

### Multi-Tenancy
- `organization_id` — Ensures tenant isolation

### Relationships
- `conversation_id` — Parent conversation
- `message_id` — Optional originating message

### Tool Metadata
- `tool_name`
- `tool_version`
- `execution_source` — ai / operator / system

### Execution Details
- `parameters` — Tool input payload
- `result` — Tool output payload
- `success` — Boolean execution result
- `error_message`

### Performance Metrics
- `latency_ms`
- `retry_count`

### Cost Tracking
- `token_usage`
- `estimated_cost_usd`

### Timestamps
- `executed_at`
- `created_at`

---

## Architectural Role

organizations
 └── conversations
       └── tool_logs

This table powers:

- Tool reliability analytics
- SLA monitoring
- Agent debugging
- Cost optimization
- Usage-based billing

---

## Why This Design Matters

This table transforms the AI from a black box
into a measurable, auditable system.

It enables:

- Enterprise trust
- Operational monitoring
- Profitability tracking
- Scalable skill integrations

# Feedback Table

The `feedback` table stores customer satisfaction data
collected during or after conversations.

This enables continuous improvement of the AI system
through direct user feedback.

---

## Purpose

- Collects customer satisfaction scores
- Tracks sentiment trends
- Links feedback to specific conversations
- Enables AI performance evaluation
- Supports continuous improvement workflows

---

## Key Fields

### Multi-Tenancy
- `organization_id` — Ensures tenant isolation

### Relationships
- `conversation_id` — Parent conversation
- `user_id` — Optional customer reference

### Satisfaction Metrics
- `rating` — 1–5 star rating
- `sentiment` — positive / neutral / negative

### Qualitative Data
- `comment` — Open-ended feedback

### Metadata
- `collected_via` — ai / operator / survey_link / webhook
- `is_verified` — Whether feedback is confirmed

### Timestamps
- `collected_at`
- `created_at`

---

## Architectural Role

organizations
 └── conversations
       └── feedback

This table powers:

- CSAT (Customer Satisfaction) analytics
- Sentiment trend monitoring
- AI quality evaluation
- Continuous improvement loops

---

## Why This Design Matters

Feedback is essential for building trust in AI systems.

This table enables:

- Data-driven AI improvement
- SLA monitoring
- Customer-centric optimization
- Enterprise-grade quality assurance

# Organization Usage Daily

The `organization_usage_daily` table stores pre-aggregated
daily usage metrics per organization.

It prevents expensive real-time aggregation queries
across messages and tool_logs tables.

---

## Purpose

- Enables billing calculations
- Tracks AI token usage
- Measures daily activity trends
- Supports usage-based pricing
- Improves dashboard performance

---

## Key Metrics

- conversations_count
- escalations_count
- messages_count
- tool_calls_count
- total_tokens
- estimated_cost_usd

---

## Why This Matters

Without this table, billing dashboards would require
heavy aggregation across millions of rows.

This design ensures:

- Fast analytics
- Scalable billing
- Profitability tracking
- Enterprise-ready reporting

# Audit Logs

The `audit_logs` table tracks sensitive actions
performed by operators or system processes.

It provides traceability, accountability,
and enterprise compliance support.

---

## Purpose

- Track role changes
- Monitor document deletions
- Record escalation reassignment
- Capture configuration updates
- Maintain security transparency

---

## Key Fields

- actor_operator_id
- action_type
- target_table
- target_id
- old_value
- new_value
- ip_address
- user_agent

---

## Why This Matters

Enterprise customers require:

- Auditability
- Traceability
- Compliance reporting

This table ensures:

- No silent privilege changes
- Full action history
- Incident investigation capability