-- ─────────────────────────────────────────
-- CONVERSATIONS
-- Represents one complete interaction thread
-- between a customer (user) and the AI system.
-- ─────────────────────────────────────────

-- Conversation status
create type conversation_status as enum (
  'active',        -- ongoing
  'escalated',     -- handed to human
  'resolved',      -- successfully completed
  'closed'         -- manually closed
);

create table conversations (
  id                    uuid primary key default gen_random_uuid(),

  -- Multi-tenant boundary
  organization_id       uuid not null
                        references organizations(id)
                        on delete cascade,

  -- Customer reference
  user_id               uuid not null
                        references users(id)
                        on delete cascade,

  -- Channel reference
  channel_id            uuid
                        references channels(id)
                        on delete set null,

  -- Status & lifecycle
  status                conversation_status not null default 'active',
  priority              smallint not null default 3,  -- 1 (high) → 5 (low)
  ai_confidence_score   numeric(4,3),                 -- for escalation logic

  -- Escalation tracking
  escalated_at          timestamptz,
  resolved_at           timestamptz,
  closed_at             timestamptz,

  -- Metrics
  message_count         integer not null default 0,
  tool_call_count       integer not null default 0,

  -- AI context snapshot (optional)
  summary               text,       -- AI-generated summary
  tags                  text[],     -- categorization labels

  -- Timestamps
  created_at            timestamptz not null default now(),
  updated_at            timestamptz not null default now(),

  -- Helpful composite index for dashboard queries
  constraint conversations_priority_check
    check (priority between 1 and 5)
);

-- Indexes
create index on conversations(organization_id);
create index on conversations(user_id);
create index on conversations(channel_id);
create index on conversations(status);
create index on conversations(created_at);
create index on conversations(organization_id, created_at desc);
create index on conversations(organization_id, status);

-- Auto-update updated_at
create or replace function update_conversations_updated_at()
returns trigger as $$
begin
  new.updated_at = now();
  return new;
end;
$$ language plpgsql;

create trigger conversations_updated_at
  before update on conversations
  for each row execute procedure update_conversations_updated_at();