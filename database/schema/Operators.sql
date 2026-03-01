-- ─────────────────────────────────────────
-- OPERATORS (Dashboard Users / Staff)
-- Human users who log into the SaaS dashboard
-- and manage conversations & escalations.
-- ─────────────────────────────────────────

-- Role enum for safety
create type operator_role as enum ('agent', 'admin', 'owner');

create table operators (
  id                uuid primary key default gen_random_uuid(),

  -- Multi-tenant boundary
  organization_id   uuid not null
                    references organizations(id)
                    on delete cascade,

  -- Identity
  email             text not null,
  full_name         text,
  auth_user_id      uuid unique, 
  -- links to Supabase auth.users.id (recommended)

  -- Role & Permissions
  role              operator_role not null default 'agent',
  is_active         boolean not null default true,

  -- Activity tracking
  last_login_at     timestamptz,
  
  -- Audit
  created_at        timestamptz not null default now(),
  updated_at        timestamptz not null default now(),

  -- Prevent duplicate emails within same org
  unique (organization_id, email)
);

-- Indexes
create index on operators(organization_id);
create index on operators(role);
create index on operators(is_active);

-- Auto-update updated_at
create or replace function update_operators_updated_at()
returns trigger as $$
begin
  new.updated_at = now();
  return new;
end;
$$ language plpgsql;

create trigger operators_updated_at
  before update on operators
  for each row execute procedure update_operators_updated_at();