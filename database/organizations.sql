-- ─────────────────────────────────────────
-- ORGANIZATIONS (Master Tenant Table)
-- Each row represents one company using the SaaS.
-- Multi-tenant root table.
-- ─────────────────────────────────────────

-- Plan enum for billing safety
create type plan_type as enum ('free', 'pro', 'enterprise');

create table organizations (
  id                     uuid primary key default gen_random_uuid(),

  -- Basic Info
  name                   text not null,
  business_description   text,

  -- Billing & Plan
  plan                   plan_type not null default 'free',
  is_active              boolean not null default true,

  -- AI Configuration Defaults
  default_temperature    numeric(3,2) not null default 0.7,
  escalation_threshold   numeric(3,2) not null default 0.85,
  auto_escalation_enabled boolean not null default true,

  -- Usage Tracking (optional but useful)
  monthly_conversation_limit integer,
  monthly_tool_call_limit    integer,

  -- Audit
  created_at             timestamptz not null default now(),
  updated_at             timestamptz not null default now()
);

-- Auto-update updated_at
create or replace function update_organizations_updated_at()
returns trigger as $$
begin
  new.updated_at = now();
  return new;
end;
$$ language plpgsql;

create trigger organizations_updated_at
  before update on organizations
  for each row execute procedure update_organizations_updated_at();

-- Index for billing dashboards / filtering active orgs
create index on organizations(plan);
create index on organizations(is_active);

-- Disable RLS for prototype
alter table organizations disable row level security;