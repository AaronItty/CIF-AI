-- ─────────────────────────────────────────
-- MESSAGES
-- Individual messages inside a conversation.
-- Can be from user, AI assistant, or operator.
-- ─────────────────────────────────────────

-- Message sender role
create type message_role as enum (
  'user',
  'assistant',
  'operator',
  'system'      -- internal system messages
);

-- Message type (helps with analytics + UI rendering)
create type message_type as enum (
  'text',
  'image',
  'file',
  'audio',
  'tool_call',
  'tool_result',
  'status_update'
);

create table messages (
  id                    uuid primary key default gen_random_uuid(),

  -- Multi-tenant boundary (denormalized for faster RLS + analytics)
  organization_id       uuid not null
                        references organizations(id)
                        on delete cascade,

  -- Conversation relationship
  conversation_id       uuid not null
                        references conversations(id)
                        on delete cascade,

  -- Sender
  role                  message_role not null,
  operator_id           uuid
                        references operators(id)
                        on delete set null,

  -- Content
  type                  message_type not null default 'text',
  content               text,
  metadata              jsonb,      -- channel-specific or tool-specific info

  -- AI-specific tracking
  token_count           integer,
  model_name            text,
  latency_ms            integer,

  -- Tool reference (if message triggered a tool)
  tool_name             text,

  -- Status
  is_internal           boolean not null default false,  -- hidden from customer
  is_deleted            boolean not null default false,

  -- Timestamps
  created_at            timestamptz not null default now(),
  updated_at            timestamptz not null default now()
);

-- Indexes
create index on messages(organization_id);
create index on messages(conversation_id);
create index on messages(created_at);
create index on messages(role);
create index on messages(type);
create index on messages(tool_name);
create index on messages(conversation_id, created_at);

-- Auto-update updated_at
create or replace function update_messages_updated_at()
returns trigger as $$
begin
  new.updated_at = now();
  return new;
end;
$$ language plpgsql;

create trigger messages_updated_at
  before update on messages
  for each row execute procedure update_messages_updated_at();