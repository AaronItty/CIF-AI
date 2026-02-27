-- ─────────────────────────────────────────
-- USERS (End Customers)
-- Customers interacting with the AI through
-- connected channels (email, telegram, etc.)
-- ─────────────────────────────────────────

create table users (
  id                    uuid primary key default gen_random_uuid(),

  -- Multi-tenant boundary
  organization_id       uuid not null
                        references organizations(id)
                        on delete cascade,

  -- Identity (channel-level identifiers)
  email                 text,
  phone_number          text,
  telegram_id           text,
  external_user_id      text,  -- Optional: ID from external system

  -- Profile metadata
  full_name             text,
  metadata              jsonb, -- Custom CRM-style attributes

  -- Activity tracking
  last_interaction_at   timestamptz,
  total_conversations   integer not null default 0,

  -- Status
  is_blocked            boolean not null default false,

  -- Audit
  created_at            timestamptz not null default now(),
  updated_at            timestamptz not null default now(),

  -- Prevent duplicate identities within an org
  unique (organization_id, email),
  unique (organization_id, telegram_id),
  unique (organization_id, phone_number)
);

-- Indexes
create index on users(organization_id);
create index on users(last_interaction_at);
create index on users(total_conversations);
create index on users(is_blocked);

-- Auto-update updated_at
create or replace function update_users_updated_at()
returns trigger as $$
begin
  new.updated_at = now();
  return new;
end;
$$ language plpgsql;

create trigger users_updated_at
  before update on users
  for each row execute procedure update_users_updated_at();