-- ─────────────────────────────────────────
-- ESCALATIONS
-- Represents a human handoff event when
-- a conversation is escalated from AI to
-- an operator.
-- ─────────────────────────────────────────

-- Escalation lifecycle
create type escalation_status as enum (
  'pending',       -- waiting to be picked up
  'assigned',      -- assigned to operator
  'in_progress',   -- operator actively responding
  'resolved',      -- handled successfully
  'closed'         -- manually closed
);

create table escalations (
  id                    uuid primary key default gen_random_uuid(),

  -- Multi-tenant boundary
  organization_id       uuid not null
                        references organizations(id)
                        on delete cascade,

  -- Parent conversation
  conversation_id       uuid not null
                        references conversations(id)
                        on delete cascade,

  -- Why escalation happened
  reason                text not null,
  triggered_by          text not null default 'ai', 
  -- ai | user_request | operator | system

  -- AI metadata (helps analytics)
  ai_confidence_score   numeric(4,3),
  trigger_rule          text,      -- which rule caused escalation

  -- Assignment
  assigned_to           uuid
                        references operators(id)
                        on delete set null,

  status                escalation_status not null default 'pending',
  priority              smallint not null default 3,

  -- SLA & performance tracking
  first_response_at     timestamptz,
  resolved_at           timestamptz,

  -- Audit
  created_at            timestamptz not null default now(),
  updated_at            timestamptz not null default now(),

  constraint escalations_priority_check
    check (priority between 1 and 5)
);

-- Indexes
create index on escalations(organization_id);
create index on escalations(conversation_id);
create index on escalations(status);
create index on escalations(assigned_to);
create index on escalations(priority);
create index on escalations(created_at);

-- Auto-update updated_at
create or replace function update_escalations_updated_at()
returns trigger as $$
begin
  new.updated_at = now();
  return new;
end;
$$ language plpgsql;

create trigger escalations_updated_at
  before update on escalations
  for each row execute procedure update_escalations_updated_at();