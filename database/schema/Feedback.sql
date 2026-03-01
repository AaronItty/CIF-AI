-- ─────────────────────────────────────────
-- FEEDBACK
-- Stores customer satisfaction data
-- collected during or after a conversation.
-- ─────────────────────────────────────────

-- Sentiment classification
create type feedback_sentiment as enum (
  'positive',
  'neutral',
  'negative'
);

create table feedback (
  id                    uuid primary key default gen_random_uuid(),

  -- Multi-tenant boundary
  organization_id       uuid not null
                        references organizations(id)
                        on delete cascade,

  -- Related conversation
  conversation_id       uuid not null
                        references conversations(id)
                        on delete cascade,

  -- Optional user reference (denormalized for analytics)
  user_id               uuid
                        references users(id)
                        on delete set null,

  -- Rating system (1–5)
  rating                smallint
                        check (rating between 1 and 5),

  -- AI-detected sentiment
  sentiment             feedback_sentiment,

  -- Optional comment
  comment               text,

  -- Metadata
  collected_via         text default 'ai',
  -- ai | operator | survey_link | webhook

  -- Flags
  is_verified           boolean not null default false,

  -- Timestamps
  collected_at          timestamptz not null default now(),
  created_at            timestamptz not null default now()
);

-- Indexes
create index on feedback(organization_id);
create index on feedback(conversation_id);
create index on feedback(user_id);
create index on feedback(sentiment);
create index on feedback(rating);
create index on feedback(collected_at);
create index on feedback(organization_id, collected_at);