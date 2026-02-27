# 03 - Dashboard & Supabase Layer

## Subsystem Overview
Handles all persistent states, memory indexing, human operator dashboard endpoints, and system analytics.

## Ownership & Boundaries
- **Owned by:** Fullstack/Data Team
- **Boundary:** Directly interfaces with Supabase. Does not run AI logic or communication loops. Only exposes internal state for the UX Dashboard and the AI's StateManager.

## Supabase Database Schema

### `users`
- `id` (uuid, pk)
- `email` (string)
- `telegram_id` (string)
- `created_at` (timestamp)

### `conversations`
- `id` (uuid, pk)
- `user_id` (uuid, fk -> users.id)
- `status` (enum: 'active', 'escalated', 'resolved')
- `created_at` (timestamp)
- `updated_at` (timestamp)

### `escalations`
- `id` (uuid, pk)
- `conversation_id` (uuid, fk -> conversations.id)
- `reason` (string)
- `assigned_to` (string, operator_id)
- `status` (enum: 'pending', 'in_progress', 'resolved')
- `created_at` (timestamp)

### `tool_logs`
- `id` (uuid, pk)
- `conversation_id` (uuid, fk -> conversations.id)
- `tool_name` (string)
- `parameters` (jsonb)
- `result` (jsonb)
- `executed_at` (timestamp)

## Logging Strategy
All critical checkpoints in the `PlanningLoop` (Intent extraction, Tool decision, Action success/fail) are strictly indexed in `tool_logs` and conversation histories. Supabase RLS policies should restrict dashboard operators to their specific organizational scopes.

## Analytics Model
The `analytics_service.py` provides aggregated queries across table data.
Example Models:
- `Deflection Rate` = 1 - (Escalated Sessions / Total Sessions)
- `Top Failing Tools` = count where `tool_logs.result` contains `"status": "error"`

## Flow Diagram
```text
[Dashboard UI] <--> (REST API `dashboard_routes.py`) <--> [AnalyticsService & Repos]
                                                                  |
                                                                  v
[Agent Core `StateManager`] <---------------------------> [SupabaseClient]
                                                                  |
                                                                  v
                                                        [(Cloud DB Tables)]
```

## Future Extensibility Notes
- Implementing Vector Search (using pgvector via Supabase) for Retrieval-Augmented Generation (RAG) based on `uploaded_documents`.

## TODOs
- [ ] Apply Supabase initialization via SQL migration scripts.
- [ ] Connect FastAPI routes to React frontend templates.
- [ ] Define proper RLS (Row Level Security) schemas.
