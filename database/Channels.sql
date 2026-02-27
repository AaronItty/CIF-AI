-- ─────────────────────────────────────────
-- CHANNELS
-- Communication channels connected by an
-- organization (Gmail, Telegram, etc.)
-- ─────────────────────────────────────────

-- Channel type enum
create type channel_type as enum (
  'gmail',
  'telegram',
  'whatsapp',
  'phone',
  'webchat'
);

-- Channel status enum
create type channel_status as enum (
  'active',
  'inactive',
  'error'
);

create table channels (
  id                 uuid primary key default gen_random_uuid(),

  -- Multi-tenant boundary
  organization_id    uuid not null
                     references organizations(id)
                     on delete cascade,

  -- Channel metadata
  type               channel_type not null,
  display_name       text,                 -- e.g. "Support Gmail"
  status             channel_status not null default 'active',

  -- Secure config (tokens, webhooks, etc.)
  config             jsonb,                -- Encrypt sensitive values at app layer

  -- Operational tracking
  last_error         text,
  last_active_at     timestamptz,
  connected_at       timestamptz not null default now(),

  -- Audit
  created_at         timestamptz not null default now(),
  updated_at         timestamptz not null default now(),

  -- Prevent duplicate channel type per org (optional rule)
  unique (organization_id, type)
);

-- Indexes
create index on channels(organization_id);
create index on channels(type);
create index on channels(status);
create index on channels(last_active_at);

-- Auto-update updated_at
create or replace function update_channels_updated_at()
returns trigger as $$
begin
  new.updated_at = now();
  return new;
end;
$$ language plpgsql;

create trigger channels_updated_at
  before update on channels
  for each row execute procedure update_channels_updated_at();