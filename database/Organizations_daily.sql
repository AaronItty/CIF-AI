-- ─────────────────────────────────────────
-- ORGANIZATION_USAGE_DAILY
-- Pre-aggregated daily usage metrics for
-- billing, cost tracking, and analytics.
-- ─────────────────────────────────────────

create table organization_usage_daily (
  id                        uuid primary key default gen_random_uuid(),

  -- Multi-tenant boundary
  organization_id           uuid not null
                            references organizations(id)
                            on delete cascade,

  -- Aggregation date
  usage_date                date not null,

  -- Conversation metrics
  conversations_count       integer not null default 0,
  escalations_count         integer not null default 0,
  messages_count            integer not null default 0,

  -- AI usage metrics
  ai_message_count          integer not null default 0,
  operator_message_count    integer not null default 0,

  -- Tool usage
  tool_calls_count          integer not null default 0,
  failed_tool_calls_count   integer not null default 0,

  -- Token usage
  total_tokens              bigint not null default 0,
  input_tokens              bigint not null default 0,
  output_tokens             bigint not null default 0,

  -- Cost tracking
  estimated_cost_usd        numeric(12,6) not null default 0,

  -- Timestamps
  created_at                timestamptz not null default now(),
  updated_at                timestamptz not null default now(),

  -- One row per org per day
  unique (organization_id, usage_date)
);

-- Indexes
create index on organization_usage_daily(organization_id);
create index on organization_usage_daily(usage_date);
create index on organization_usage_daily(organization_id, usage_date);

-- Auto-update updated_at
create or replace function update_org_usage_updated_at()
returns trigger as $$
begin
  new.updated_at = now();
  return new;
end;
$$ language plpgsql;

create trigger organization_usage_daily_updated_at
  before update on organization_usage_daily
  for each row execute procedure update_org_usage_updated_at();