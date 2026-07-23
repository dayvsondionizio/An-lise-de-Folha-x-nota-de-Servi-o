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

-- ═══════════════════════════════════════════════════════════════════════════
-- ADIÇÃO: status "Pendente" no checklist operacional (laranja, visível)
-- ═══════════════════════════════════════════════════════════════════════════
alter table esocial_dashboard.checklist_respostas add column if not exists pendente boolean default false;

-- ═══════════════════════════════════════════════════════════════════════════
-- SPRINT A: Plano de Implantação e Regularização Assistida
-- ═══════════════════════════════════════════════════════════════════════════
create table if not exists esocial_dashboard.plano_implantacao (
  id uuid primary key default gen_random_uuid(),
  empresa_id uuid not null references esocial_dashboard.empresas(id) on delete cascade,
  respostas_assistente jsonb default '{}'::jsonb,
  trilha_recomendada text,
  respostas_arvore jsonb default '{}'::jsonb,
  resultado_arvore text,
  atualizado_em timestamptz default now(),
  unique (empresa_id)
);

create table if not exists esocial_dashboard.entrevista_abertura (
  id uuid primary key default gen_random_uuid(),
  empresa_id uuid not null references esocial_dashboard.empresas(id) on delete cascade,
  pergunta_id text not null,
  resposta text,
  entrevistado text,
  cargo text,
  data_entrevista date,
  evidencia text,
  observacao text,
  contradicao boolean default false,
  nova_entrevista boolean default false,
  atualizado_em timestamptz default now(),
  unique (empresa_id, pergunta_id)
);

create index if not exists idx_plano_implantacao_empresa on esocial_dashboard.plano_implantacao(empresa_id);
create index if not exists idx_entrevista_abertura_empresa on esocial_dashboard.entrevista_abertura(empresa_id);

grant all on esocial_dashboard.plano_implantacao to anon, authenticated, service_role;
grant all on esocial_dashboard.entrevista_abertura to anon, authenticated, service_role;

-- ═══════════════════════════════════════════════════════════════════════════
-- MÓDULO: Admissão Transparente + SST por funcionário
-- ═══════════════════════════════════════════════════════════════════════════
create table if not exists esocial_dashboard.funcionarios (
  id uuid primary key default gen_random_uuid(),
  empresa_id uuid not null references esocial_dashboard.empresas(id) on delete cascade,
  nome text not null,
  cpf text,
  funcao text,
  cbo text,
  unidade text,
  contratante_nome text,
  gestor_prestadora text,
  preposto text,
  status text default 'Candidato' check (status in ('Candidato', 'Entrevistado', 'Contratado', 'Desligado')),
  data_admissao date,
  criado_em timestamptz default now(),
  atualizado_em timestamptz default now()
);

create table if not exists esocial_dashboard.entrevista_admissao (
  id uuid primary key default gen_random_uuid(),
  funcionario_id uuid not null references esocial_dashboard.funcionarios(id) on delete cascade,
  respostas jsonb default '{}'::jsonb,
  duvidas text,
  frases_proibidas_usadas jsonb default '[]'::jsonb,
  ciencia_registrada boolean default false,
  entrevistador text,
  data_entrevista date,
  atualizado_em timestamptz default now(),
  unique (funcionario_id)
);

create table if not exists esocial_dashboard.sst_funcionario (
  id uuid primary key default gen_random_uuid(),
  funcionario_id uuid not null references esocial_dashboard.funcionarios(id) on delete cascade,
  aso_tipo text,
  aso_data date,
  aso_validade date,
  epi_entregue text,
  treinamentos text,
  riscos text,
  atualizado_em timestamptz default now(),
  unique (funcionario_id)
);

create index if not exists idx_funcionarios_empresa on esocial_dashboard.funcionarios(empresa_id);
create index if not exists idx_entrevista_admissao_func on esocial_dashboard.entrevista_admissao(funcionario_id);
create index if not exists idx_sst_funcionario_func on esocial_dashboard.sst_funcionario(funcionario_id);

grant all on esocial_dashboard.funcionarios to anon, authenticated, service_role;
grant all on esocial_dashboard.entrevista_admissao to anon, authenticated, service_role;
grant all on esocial_dashboard.sst_funcionario to anon, authenticated, service_role;

-- ═══════════════════════════════════════════════════════════════════════════
-- SUPERSEDES the 3 tables above: o app não cadastra mais funcionário por
-- funcionário. Vira um guia único por empresa (prestadora), orientando o
-- Departamento Pessoal sobre função/CBO compatível com o objeto do contrato
-- de prestação de serviços — não um cadastro de pessoas.
-- As 3 tabelas acima ficam sem uso pelo app a partir de agora; podem ser
-- removidas manualmente (drop table) se você preferir, não é obrigatório.
-- ═══════════════════════════════════════════════════════════════════════════
create table if not exists esocial_dashboard.admissao_orientacao (
  id uuid primary key default gen_random_uuid(),
  empresa_id uuid not null references esocial_dashboard.empresas(id) on delete cascade,
  contratante_nome text,
  unidade text,
  gestor_prestadora text,
  preposto text,
  objeto_contrato text,
  mapeamento_funcoes jsonb default '[]'::jsonb,
  checklist jsonb default '{}'::jsonb,
  atualizado_em timestamptz default now(),
  unique (empresa_id)
);

create index if not exists idx_admissao_orientacao_empresa
  on esocial_dashboard.admissao_orientacao(empresa_id);

grant all on esocial_dashboard.admissao_orientacao to anon, authenticated, service_role;

-- ═══════════════════════════════════════════════════════════════════════════
-- Marcar um item do Checklist Operacional como "Pendente" cria automaticamente
-- uma ação vinculada no Plano de Ação 5W2H. Esta coluna evita duplicar a ação
-- caso o item seja marcado/desmarcado várias vezes.
-- ═══════════════════════════════════════════════════════════════════════════
alter table esocial_dashboard.plano_acao_5w2h
  add column if not exists origem_checklist_item_id text;

create index if not exists idx_plano_origem_checklist
  on esocial_dashboard.plano_acao_5w2h(empresa_id, origem_checklist_item_id);

-- ═══════════════════════════════════════════════════════════════════════════
-- DRE GERENCIAL — indicador simplificado de autonomia financeira da prestadora
-- (receita de serviço × folha+encargos × outras despesas, por competência)
-- ═══════════════════════════════════════════════════════════════════════════
create table if not exists esocial_dashboard.dre_gerencial (
  id uuid primary key default gen_random_uuid(),
  empresa_id uuid not null references esocial_dashboard.empresas(id) on delete cascade,
  competencia text not null,
  receita_servico numeric default 0,
  despesa_pessoal numeric default 0,
  despesa_geral numeric default 0,
  observacao text,
  criado_em timestamptz default now(),
  atualizado_em timestamptz default now(),
  unique (empresa_id, competencia)
);

create index if not exists idx_dre_gerencial_empresa on esocial_dashboard.dre_gerencial(empresa_id);

grant all on esocial_dashboard.dre_gerencial to anon, authenticated, service_role;
