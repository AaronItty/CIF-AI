-- ─────────────────────────────────────────
-- AUDIT_LOGS
-- Tracks important system and operator actions
-- for compliance and traceability.
-- ─────────────────────────────────────────

create table audit_logs (
  id                      uuid primary key default gen_random_uuid(),

  -- Multi-tenant boundary
  organization_id         uuid not null
                          references organizations(id)
                          on delete cascade,

  -- Actor
  actor_operator_id       uuid
                          references operators(id)
                          on delete set null,

  actor_role              text,      -- snapshot of role at time of action

  -- Action details
  action_type             text not null,
  -- e.g. role_updated, document_deleted, escalation_reassigned

  target_table            text not null,
  target_id               uuid,

  -- Change tracking
  old_value               jsonb,
  new_value               jsonb,

  -- Context
  ip_address              text,
  user_agent              text,

  -- Timestamp
  created_at              timestamptz not null default now()
);

-- Indexes
create index on audit_logs(organization_id);
create index on audit_logs(actor_operator_id);
create index on audit_logs(action_type);
create index on audit_logs(created_at);
create index on audit_logs(organization_id, created_at);