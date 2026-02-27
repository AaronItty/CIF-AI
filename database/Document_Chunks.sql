create table document_chunks (
  id uuid primary key default gen_random_uuid(),

  organization_id uuid not null
      references organizations(id)
      on delete cascade,

  document_id uuid not null
      references documents(id)
      on delete cascade,

  chunk_index integer not null,
  content text not null,

  embedding vector(768),

  created_at timestamptz not null default now()
);

create index on document_chunks(organization_id);
create index on document_chunks(document_id);

create index on document_chunks
using ivfflat (embedding vector_cosine_ops)
with (lists = 100);

-- Disable RLS for prototype
alter table document_chunks disable row level security;

-- STEP 7 — Vector Search SQL
create or replace function match_documents(
    query_embedding vector(768)
)
returns table (
    content text,
    similarity float
)
language sql
security definer
as $$
    select
        content,
        1 - (embedding <=> query_embedding) as similarity
    from document_chunks
    order by embedding <=> query_embedding
    limit 5;
$$;