-- ─────────────────────────────────────────
-- REMINDERS
-- Stores notifications, daily summaries, 
-- and event-triggered alerts for operators.
-- ─────────────────────────────────────────

-- Reminder categories
create type reminder_type as enum (
  'escalation',    -- high priority human handoff
  'system',        -- system alerts or updates
  'daily_summary', -- morning brief / summary of status
  'priority_case'  -- cases requiring immediate attention
);

create table reminders (
  id                    uuid primary key default gen_random_uuid(),

  -- Multi-tenant boundary
  organization_id       uuid not null
                        references organizations(id)
                        on delete cascade,

  type                  reminder_type not null default 'system',
  
  title                 text not null,
  description           text,
  
  -- Deep link context (e.g., "/cases/123")
  link                  text,

  is_read               boolean not null default false,

  -- Audit
  created_at            timestamptz not null default now(),
  updated_at            timestamptz not null default now()
);

-- Indexes for performance
create index on reminders(organization_id);
create index on reminders(is_read);
create index on reminders(type);
create index on reminders(created_at);

-- Auto-update updated_at
create or replace function update_reminders_updated_at()
returns trigger as $$
begin
  new.updated_at = now();
  return new;
end;
$$ language plpgsql;

create trigger reminders_updated_at
  before update on reminders
  for each row execute procedure update_reminders_updated_at();
