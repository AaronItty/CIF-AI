-- STEP 10 — Documents Metadata Table
-- Tracks the lifecycle of uploaded knowledge base files.

do $$ begin
  create type document_status as enum ('uploaded', 'processing', 'ready', 'failed');
exception
  when duplicate_object then null;
end $$;

create table documents (
  id uuid primary key default gen_random_uuid(),

  organization_id uuid not null
      references organizations(id)
      on delete cascade,

  name text not null,
  storage_path text, -- Path in Supabase Storage
  mime_type text,
  file_size_bytes bigint,

  status document_status not null default 'uploaded',
  chunk_count integer default 0,
  embedding_model text default 'nomic-ai/nomic-embed-text-v1.5',
  last_error text,

  uploaded_by uuid -- Optional: references operators(id)
      references operators(id)
      on delete set null,

  uploaded_at timestamptz not null default now(),
  processed_at timestamptz,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);

-- Auto-update updated_at for documents
create trigger documents_updated_at
  before update on documents
  for each row execute procedure update_organizations_updated_at();

-- Indices for performance and tenant isolation
create index on documents(organization_id);
create index on documents(status);
create index on documents(uploaded_by);
