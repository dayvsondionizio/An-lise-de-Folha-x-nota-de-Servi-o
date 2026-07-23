# -*- coding: utf-8 -*-
"""
db_supabase.py — Camada de persistência do módulo Conformidade via Supabase.
Todas as tabelas vivem no schema "esocial_dashboard" (isolado de outros
aplicativos que usem o mesmo projeto Supabase).
"""
import streamlit as st
from supabase import create_client, ClientOptions

BUCKET_DOCS = "esocial-documentos-conformidade"
BUCKET_FOLHA = "esocial-arquivos-folha"


@st.cache_resource(show_spinner=False)
def get_client():
    cfg = st.secrets["supabase"]
    return create_client(cfg["url"], cfg["anon_key"],
                         options=ClientOptions(schema=cfg.get("schema", "esocial_dashboard")))


# ── EMPRESAS ──────────────────────────────────────────────────────────────────
def empresas_listar():
    c = get_client()
    r = c.table("empresas").select("*").order("criado_em").execute()
    return r.data or []


def empresa_criar(dados):
    c = get_client()
    r = c.table("empresas").insert(dados).execute()
    return r.data[0]


def empresa_atualizar(empresa_id, dados):
    c = get_client()
    c.table("empresas").update(dados).eq("id", empresa_id).execute()


def empresa_excluir(empresa_id):
    c = get_client()
    # limpa documentos no storage antes (o banco cuida do resto via cascade)
    for bucket in (BUCKET_DOCS, BUCKET_FOLHA):
        try:
            arquivos = c.storage.from_(bucket).list(str(empresa_id))
            for pasta in arquivos or []:
                sub = c.storage.from_(bucket).list(f"{empresa_id}/{pasta['name']}")
                caminhos = [f"{empresa_id}/{pasta['name']}/{a['name']}" for a in (sub or [])]
                if caminhos:
                    c.storage.from_(bucket).remove(caminhos)
        except Exception:
            pass
    c.table("empresas").delete().eq("id", empresa_id).execute()


# ── CHECKLIST OPERACIONAL (61 itens) ─────────────────────────────────────────
def checklist_carregar(empresa_id):
    c = get_client()
    r = c.table("checklist_respostas").select("*").eq("empresa_id", empresa_id).execute()
    itens = {row["item_id"]: row["verificado"] for row in (r.data or [])}
    pendentes = {row["item_id"]: row.get("pendente", False) for row in (r.data or [])}
    observacoes = {row["item_id"]: row["observacao"] for row in (r.data or []) if row.get("observacao")}
    return itens, observacoes, pendentes


def checklist_upsert_item(empresa_id, item_id, verificado, observacao, pendente=False):
    c = get_client()
    c.table("checklist_respostas").upsert({
        "empresa_id": empresa_id, "item_id": item_id,
        "verificado": verificado, "observacao": observacao or None, "pendente": pendente,
    }, on_conflict="empresa_id,item_id").execute()


# ── DIAGNÓSTICO DE RISCO (23 perguntas) ──────────────────────────────────────
def risco_carregar(empresa_id):
    c = get_client()
    r = c.table("diagnostico_risco_respostas").select("*").eq("empresa_id", empresa_id).execute()
    respostas = {row["pergunta_id"]: row["resposta"] for row in (r.data or [])}
    observacoes = {row["pergunta_id"]: row["observacao"] for row in (r.data or []) if row.get("observacao")}
    return respostas, observacoes


def risco_upsert_item(empresa_id, pergunta_id, resposta, observacao):
    c = get_client()
    c.table("diagnostico_risco_respostas").upsert({
        "empresa_id": empresa_id, "pergunta_id": pergunta_id,
        "resposta": resposta, "observacao": observacao or None,
    }, on_conflict="empresa_id,pergunta_id").execute()


# ── PLANO DE AÇÃO 5W2H ────────────────────────────────────────────────────────
def plano_listar(empresa_id):
    c = get_client()
    r = c.table("plano_acao_5w2h").select("*").eq("empresa_id", empresa_id).order("criado_em").execute()
    return r.data or []


def plano_inserir(empresa_id, dados):
    c = get_client()
    dados = dict(dados, empresa_id=empresa_id)
    r = c.table("plano_acao_5w2h").insert(dados).execute()
    return r.data[0]


def plano_atualizar(row_id, dados):
    c = get_client()
    c.table("plano_acao_5w2h").update(dados).eq("id", row_id).execute()


def plano_remover(row_id):
    c = get_client()
    c.table("plano_acao_5w2h").delete().eq("id", row_id).execute()


def plano_limpar(empresa_id):
    c = get_client()
    c.table("plano_acao_5w2h").delete().eq("empresa_id", empresa_id).execute()


def plano_inserir_lote(empresa_id, lista_dados):
    c = get_client()
    linhas = [dict(d, empresa_id=empresa_id) for d in lista_dados]
    c.table("plano_acao_5w2h").insert(linhas).execute()


# ── DOCUMENTOS (Storage + tabela de metadados p/ evitar N+1 no Storage) ──────
def _doc_prefix(empresa_id, contexto):
    return f"{empresa_id}/{contexto}"


def docs_listar_mapa(empresa_id):
    """UMA consulta que traz todos os documentos da empresa, agrupados por contexto."""
    c = get_client()
    r = c.table("documentos").select("contexto, nome_original").eq("empresa_id", empresa_id)\
        .order("nome_original").execute()
    mapa = {}
    for row in (r.data or []):
        mapa.setdefault(row["contexto"], []).append(row["nome_original"])
    return mapa


def docs_salvar(empresa_id, contexto, arquivo, timestamp):
    c = get_client()
    nome = f"{timestamp}__{arquivo.name}"
    caminho = f"{_doc_prefix(empresa_id, contexto)}/{nome}"
    conteudo = arquivo.getbuffer().tobytes()
    c.storage.from_(BUCKET_DOCS).upload(caminho, conteudo,
                                        {"content-type": arquivo.type or "application/octet-stream",
                                         "upsert": "true"})
    c.table("documentos").insert({
        "empresa_id": empresa_id, "contexto": contexto, "nome_original": nome,
        "storage_path": caminho, "tamanho_bytes": len(conteudo),
    }).execute()


def docs_baixar(empresa_id, contexto, nome):
    c = get_client()
    caminho = f"{_doc_prefix(empresa_id, contexto)}/{nome}"
    return c.storage.from_(BUCKET_DOCS).download(caminho)


def docs_remover(empresa_id, contexto, nome):
    c = get_client()
    caminho = f"{_doc_prefix(empresa_id, contexto)}/{nome}"
    c.storage.from_(BUCKET_DOCS).remove([caminho])
    c.table("documentos").delete().eq("empresa_id", empresa_id).eq("contexto", contexto)\
        .eq("nome_original", nome).execute()


# ── SIMULAÇÕES PGDAS (sempre vinculadas a uma empresa — feitas de dentro da ficha) ──
def simulacao_salvar(empresa_id, dados):
    c = get_client()
    dados = dict(dados, empresa_id=empresa_id)
    r = c.table("simulacoes_pgdas").insert(dados).execute()
    return r.data[0]


def simulacoes_listar(empresa_id):
    c = get_client()
    r = c.table("simulacoes_pgdas").select("*").eq("empresa_id", empresa_id)\
        .order("criado_em").execute()
    return list(reversed(r.data or []))


def simulacao_remover(row_id):
    c = get_client()
    c.table("simulacoes_pgdas").delete().eq("id", row_id).execute()


# ── ANÁLISES DE FOLHA (sempre vinculadas a uma empresa) ──────────────────────
def analise_salvar(empresa_id, dados, arquivo=None):
    c = get_client()
    dados = dict(dados, empresa_id=empresa_id)
    if arquivo is not None:
        timestamp = dados.pop("_timestamp")
        caminho = f"{empresa_id}/{timestamp}__{arquivo.name}"
        c.storage.from_(BUCKET_FOLHA).upload(caminho, arquivo.getbuffer().tobytes(),
                                             {"content-type": "application/octet-stream"})
        dados["arquivo_origem_path"] = caminho
    r = c.table("analises_folha").insert(dados).execute()
    return r.data[0]


def analises_listar(empresa_id):
    c = get_client()
    r = c.table("analises_folha").select("*").eq("empresa_id", empresa_id)\
        .order("criado_em").execute()
    return list(reversed(r.data or []))


def analise_remover(row_id, arquivo_origem_path=None):
    c = get_client()
    if arquivo_origem_path:
        try:
            c.storage.from_(BUCKET_FOLHA).remove([arquivo_origem_path])
        except Exception:
            pass
    c.table("analises_folha").delete().eq("id", row_id).execute()


def analise_baixar_arquivo(caminho):
    c = get_client()
    return c.storage.from_(BUCKET_FOLHA).download(caminho)


# ── ADMISSÃO & TERCEIRIZAÇÃO — guia de orientação por empresa (não por pessoa) ──
def orientacao_admissao_carregar(empresa_id):
    c = get_client()
    r = c.table("admissao_orientacao").select("*").eq("empresa_id", empresa_id).execute()
    return r.data[0] if r.data else None


def orientacao_admissao_salvar(empresa_id, dados):
    c = get_client()
    dados = dict(dados, empresa_id=empresa_id)
    c.table("admissao_orientacao").upsert(dados, on_conflict="empresa_id").execute()


# ── DRE GERENCIAL (por competência, por empresa) ─────────────────────────────
def dre_listar(empresa_id):
    c = get_client()
    r = c.table("dre_gerencial").select("*").eq("empresa_id", empresa_id).order("competencia").execute()
    return r.data or []


def dre_upsert(empresa_id, competencia, dados):
    c = get_client()
    dados = dict(dados, empresa_id=empresa_id, competencia=competencia)
    c.table("dre_gerencial").upsert(dados, on_conflict="empresa_id,competencia").execute()


def dre_remover(row_id):
    c = get_client()
    c.table("dre_gerencial").delete().eq("id", row_id).execute()


# ── BIBLIOTECA DE PRECEDENTES JURÍDICOS (office-wide, não por empresa) ───────
def precedentes_listar():
    c = get_client()
    r = c.table("precedentes_juridicos").select("*").order("criado_em").execute()
    return r.data or []


def precedente_criar(dados):
    c = get_client()
    r = c.table("precedentes_juridicos").insert(dados).execute()
    return r.data[0]


def precedente_atualizar(row_id, dados):
    c = get_client()
    c.table("precedentes_juridicos").update(dados).eq("id", row_id).execute()


def precedente_remover(row_id):
    c = get_client()
    c.table("precedentes_juridicos").delete().eq("id", row_id).execute()


# ── TRIAGEM DA CARTEIRA DE CLIENTES (office-wide) ────────────────────────────
def triagem_listar():
    c = get_client()
    r = c.table("triagem_clientes").select("*").order("criado_em").execute()
    return r.data or []


def triagem_criar(dados):
    c = get_client()
    r = c.table("triagem_clientes").insert(dados).execute()
    return r.data[0]


def triagem_atualizar(row_id, dados):
    c = get_client()
    c.table("triagem_clientes").update(dados).eq("id", row_id).execute()


def triagem_remover(row_id):
    c = get_client()
    c.table("triagem_clientes").delete().eq("id", row_id).execute()
