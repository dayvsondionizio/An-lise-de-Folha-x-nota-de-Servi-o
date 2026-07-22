-- ═══════════════════════════════════════════════════════════════════════════
-- Schema Supabase — Contador de Padarias / esocial-dashboard
-- Roda dentro do schema próprio "esocial_dashboard", isolado de qualquer
-- outro aplicativo que já use este mesmo projeto Supabase.
-- Rode este script inteiro no SQL Editor do seu projeto Supabase.
-- ═══════════════════════════════════════════════════════════════════════════

create extension if not exists "pgcrypto";

create schema if not exists esocial_dashboard;

-- ── EMPRESAS (cadastro central — clientes, prestadoras, tomadoras) ──────────
create table if not exists esocial_dashboard.empresas (
  id uuid primary key default gen_random_uuid(),
  razao_social text not null,
  nome_fantasia text,
  cnpj text,
  papel text check (papel in ('Prestadora', 'Tomadora', 'Ambas')),
  grupo_economico text,
  cnae_principal text,
  data_abertura date,
  regime_tributario text,
  situacao text default 'Em análise'
    check (situacao in ('Em análise', 'Risco identificado', 'Regularizada', 'Encerrada')),
  observacoes text,
  criado_em timestamptz default now(),
  atualizado_em timestamptz default now()
);

-- ── SIMULAÇÕES PGDAS (quanto de nota emitir) — empresa_id nulo = avulsa ─────
create table if not exists esocial_dashboard.simulacoes_pgdas (
  id uuid primary key default gen_random_uuid(),
  empresa_id uuid references esocial_dashboard.empresas(id) on delete set null,
  competencia text,
  folha_bruta numeric,
  fgts numeric,
  margem_seguranca numeric,
  despesas_gerais numeric,
  nota_a_emitir numeric,
  das_estimado numeric,
  cpp_estimado numeric,
  aliquota_efetiva numeric,
  distribuicao jsonb,
  criado_em timestamptz default now()
);

-- ── ANÁLISES DE FOLHA — empresa_id nulo = avulsa ────────────────────────────
create table if not exists esocial_dashboard.analises_folha (
  id uuid primary key default gen_random_uuid(),
  empresa_id uuid references esocial_dashboard.empresas(id) on delete set null,
  competencia_inicio text,
  competencia_fim text,
  arquivo_origem_path text,        -- caminho no bucket 'esocial-arquivos-folha'
  resumo jsonb,                    -- KPIs agregados (custo total, encargos, headcount, gastos por mês, etc.)
  criado_em timestamptz default now()
);

-- ── CONFORMIDADE: checklist operacional (61 itens, sempre vinculado a empresa) ──
create table if not exists esocial_dashboard.checklist_respostas (
  id uuid primary key default gen_random_uuid(),
  empresa_id uuid not null references esocial_dashboard.empresas(id) on delete cascade,
  item_id text not null,
  verificado boolean default false,
  observacao text,
  atualizado_em timestamptz default now(),
  unique (empresa_id, item_id)
);

-- ── CONFORMIDADE: diagnóstico de risco (23 perguntas Sim/Não/N.A.) ──────────
create table if not exists esocial_dashboard.diagnostico_risco_respostas (
  id uuid primary key default gen_random_uuid(),
  empresa_id uuid not null references esocial_dashboard.empresas(id) on delete cascade,
  pergunta_id text not null,
  resposta text check (resposta in ('Sim', 'Não', 'N.A.')),
  observacao text,
  atualizado_em timestamptz default now(),
  unique (empresa_id, pergunta_id)
);

-- ── CONFORMIDADE: plano de ação 5W2H ─────────────────────────────────────────
create table if not exists esocial_dashboard.plano_acao_5w2h (
  id uuid primary key default gen_random_uuid(),
  empresa_id uuid not null references esocial_dashboard.empresas(id) on delete cascade,
  o_que text not null,
  por_que text,
  onde text,
  quando text,
  quem text,
  como text,
  quanto_custa text,
  prioridade text check (prioridade in ('Altíssima', 'Alta', 'Média', 'Baixa')),
  status text default 'Pendente' check (status in ('Pendente', 'Em andamento', 'Concluído')),
  criado_em timestamptz default now(),
  atualizado_em timestamptz default now()
);

-- ── DOCUMENTOS anexados (metadados; arquivo em si vai no Storage) ───────────
create table if not exists esocial_dashboard.documentos (
  id uuid primary key default gen_random_uuid(),
  empresa_id uuid not null references esocial_dashboard.empresas(id) on delete cascade,
  contexto text not null,          -- ex: 'checklist:cnpj_ativo' · 'risco:pejot_exclusividade' · 'folha:2026-05'
  nome_original text,
  storage_path text not null,      -- caminho no bucket 'esocial-documentos-conformidade'
  tamanho_bytes bigint,
  criado_em timestamptz default now()
);

-- ── índices úteis ────────────────────────────────────────────────────────────
create index if not exists idx_simulacoes_empresa on esocial_dashboard.simulacoes_pgdas(empresa_id);
create index if not exists idx_analises_empresa on esocial_dashboard.analises_folha(empresa_id);
create index if not exists idx_checklist_empresa on esocial_dashboard.checklist_respostas(empresa_id);
create index if not exists idx_risco_empresa on esocial_dashboard.diagnostico_risco_respostas(empresa_id);
create index if not exists idx_plano_empresa on esocial_dashboard.plano_acao_5w2h(empresa_id);
create index if not exists idx_documentos_empresa on esocial_dashboard.documentos(empresa_id);

-- ── permissões — schemas próprios não herdam grants automáticos do "public" ──
grant usage on schema esocial_dashboard to anon, authenticated, service_role;
grant all on all tables in schema esocial_dashboard to anon, authenticated, service_role;
grant all on all sequences in schema esocial_dashboard to anon, authenticated, service_role;
alter default privileges in schema esocial_dashboard
  grant all on tables to anon, authenticated, service_role;
alter default privileges in schema esocial_dashboard
  grant all on sequences to anon, authenticated, service_role;

-- ═══════════════════════════════════════════════════════════════════════════
-- PASSOS MANUAIS NO PAINEL DO SUPABASE (não dá pra fazer via SQL):
--
-- 1) Settings → API → Data API → "Exposed schemas"
--    Adicione "esocial_dashboard" na lista (o schema "public" do outro app
--    continua exposto normalmente, sem nenhuma mudança nele).
--
-- 2) Storage → New bucket → crie 2 buckets PRIVADOS com nome exato:
--      - esocial-documentos-conformidade
--      - esocial-arquivos-folha
--    (nomes prefixados para não colidir com buckets do outro aplicativo)
--
-- Nada neste script toca no schema "public" nem em qualquer tabela/bucket
-- que já exista — é 100% aditivo e isolado.
-- ═══════════════════════════════════════════════════════════════════════════
