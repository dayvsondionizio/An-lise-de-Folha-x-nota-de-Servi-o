# -*- coding: utf-8 -*-
"""
Painel Gerencial de Folha de Pagamento — eSocial
Departamento Pessoal · Contador de Padaria
"""
import io, re, os, json, zipfile
from datetime import date, datetime
import pandas as pd
import streamlit as st

import esocial_parser as ep
import relatorio_pdf as rpdf
import db_supabase as db

st.set_page_config(page_title="Análise de Folha × Nota de Serviço", page_icon="📋",
                   layout="wide", initial_sidebar_state="collapsed",
                   menu_items={})

st.markdown("""
<style>
html, body, [class*="css"] { font-family:'Segoe UI','Inter',-apple-system,sans-serif; }
.block-container { padding-top:3.5rem; max-width:1480px; }
/* oculta sidebar e o botão de abrir */
[data-testid="stSidebar"], [data-testid="collapsedControl"] { display:none !important; }

/* ── PASSOS DO SIMULADOR ── */
.sim-step { display:flex; align-items:flex-start; gap:14px; margin:18px 0 6px; }
.sim-step-num { min-width:32px; height:32px; border-radius:50%;
  background:linear-gradient(135deg,#16304f,#2e6da4); color:#fff;
  font-weight:800; font-size:14px; display:flex; align-items:center;
  justify-content:center; flex-shrink:0; box-shadow:0 2px 8px rgba(22,48,79,.25); }
.sim-step-body { flex:1; }
.sim-step-title { font-size:13px; font-weight:700; letter-spacing:.04em;
  text-transform:uppercase; opacity:.65; margin:0 0 2px; }
.sim-step-desc { font-size:13px; margin:0; opacity:.8; }

/* ── RESULTADO DESTAQUE ── */
.nota-destaque { border-radius:16px; padding:28px 32px; margin:20px 0 12px;
  background:linear-gradient(135deg,#0f2540 0%,#1a4a7a 100%);
  box-shadow:0 8px 32px rgba(15,37,64,.35); text-align:center; }
.nota-destaque .label { font-size:11px; font-weight:700; letter-spacing:.12em;
  text-transform:uppercase; color:rgba(255,255,255,.6); margin-bottom:8px; }
.nota-destaque .valor { font-size:44px; font-weight:900; color:#fff;
  letter-spacing:-.02em; line-height:1; margin-bottom:6px; }
.nota-destaque .sub { font-size:13px; color:rgba(255,255,255,.65); }

/* ── CARD MANUAL ── */
.card-manual { border-radius:12px; padding:16px 20px; margin:10px 0; }
@media (prefers-color-scheme: light) {
  .card-manual { background:#fffbf0; border:1.5px dashed #d4ac0d; }
  .sim-step-title { color:#16304f; }
}
@media (prefers-color-scheme: dark) {
  .card-manual { background:#2a2310; border:1.5px dashed #d4ac0d; }
  .sim-step-title { color:#a8c4e0; }
}

/* ── LIGHT ── */
@media (prefers-color-scheme: light) {
  .stApp { background:#f5f7fa; }
  h1,h2,h3,h4 { color:#16304f; }
  .kpi { background:#fff; border:1px solid #eaeef4; }
  .kpi .v { color:#16304f; }
  .al-r,.al-y,.al-g,.al-b { color:#1c2733 !important; }
  .al-r small,.al-y small,.al-g small,.al-b small { color:#1c2733 !important; }
  .al-r { background:#fdf0ee; }
  .al-y { background:#fdf7ec; }
  .al-g { background:#eef7f1; }
  .al-b { background:#eef3f9; }
  .box { background:#fff; border:1px solid #eaeef4; color:#1c2733 !important; }
  .stTabs [data-baseweb="tab"] { color:#5a6675; }
  .stTabs [aria-selected="true"] { color:#16304f !important; background:#eef3f9; }
  [data-testid="stDataFrame"] { border:1px solid #eaeef4; }
  hr { border-color:#e7ecf3; }
  [data-testid="stExpander"] { border:1px solid #eaeef4; }
}

/* ── DARK ── */
@media (prefers-color-scheme: dark) {
  h1,h2,h3,h4 { color:#a8c4e0; }
  .kpi { background:#1e2d3d; border:1px solid #2e4057; }
  .kpi .v { color:#a8c4e0; }
  .kpi .l { color:#6b8299; }
  .al-r,.al-y,.al-g,.al-b { color:#e0e8f0 !important; }
  .al-r small,.al-y small,.al-g small,.al-b small { color:#e0e8f0 !important; }
  .al-r { background:#3d1f1c; border-left:4px solid #c0392b; }
  .al-y { background:#3d2e10; border-left:4px solid #d4ac0d; }
  .al-g { background:#1a3328; border-left:4px solid #27ae60; }
  .al-b { background:#1a2a3d; border-left:4px solid #2980b9; }
  .box { background:#1e2d3d; border:1px solid #2e4057; color:#e0e8f0 !important; }
  .box p,.box span,.box td,.box th { color:#e0e8f0 !important; }
  .stTabs [data-baseweb="tab"] { color:#8aa3bb; }
  .stTabs [aria-selected="true"] { color:#a8c4e0 !important; background:#1e2d3d; }
  [data-testid="stDataFrame"] { border:1px solid #2e4057; }
  hr { border-color:#2e4057; }
  [data-testid="stExpander"] { border:1px solid #2e4057; }
}

/* ── COMUM (ambos os temas) ── */
h1,h2,h3,h4 { font-weight:700; letter-spacing:-.01em; }
h4 { font-size:15px; margin:4px 0 10px; }
.hero { background:linear-gradient(120deg,#16304f 0%,#27517f 100%); color:#fff;
        border-radius:16px; padding:24px 30px; margin-bottom:16px;
        box-shadow:0 8px 28px rgba(22,48,79,.20); }
.hero h1 { color:#fff !important; margin:0; font-size:27px; font-weight:750; }
.hero p  { margin:7px 0 0 0; opacity:.88; font-size:13px; color:#fff !important; }
.kpi { border-radius:14px; padding:18px; text-align:left; height:100%;
       box-shadow:0 2px 10px rgba(16,40,80,.05); transition:box-shadow .15s ease; }
.kpi:hover { box-shadow:0 6px 18px rgba(16,40,80,.11); }
.kpi .v { font-size:25px; font-weight:800; line-height:1.08; }
.kpi .l { font-size:10.5px; color:#8a94a3; text-transform:uppercase;
          letter-spacing:.06em; margin-top:7px; font-weight:600; }
.kpi .d { font-size:11.5px; margin-top:5px; font-weight:600; }
.kpi .d.up { color:#27ae60; } .kpi .d.down { color:#c0392b; } .kpi .d.n { color:#8a94a3; }
.al-r,.al-y,.al-g,.al-b { border-radius:10px; padding:13px 17px; margin:7px 0;
       font-size:13.5px; line-height:1.5; }
.al-r { border-left:4px solid #b03a2e; }
.al-y { border-left:4px solid #b9770e; }
.al-g { border-left:4px solid #2f7a4d; }
.al-b { border-left:4px solid #2e5b8a; }
.box { border-radius:14px; padding:18px 20px; margin-bottom:12px;
       box-shadow:0 2px 10px rgba(16,40,80,.05); }
.box table td { padding:6px 2px; }
.stTabs [data-baseweb="tab-list"] { gap:3px; border-bottom:1px solid #2e4057; }
.stTabs [data-baseweb="tab"] { font-size:13.5px; padding:9px 15px; font-weight:600;
       border-radius:8px 8px 0 0; }
[data-testid="stDataFrame"] { border-radius:12px; overflow:hidden;
       box-shadow:0 2px 10px rgba(16,40,80,.05); }
hr { margin:1.1rem 0; }
[data-testid="stExpander"] { border-radius:12px;
       box-shadow:0 2px 10px rgba(16,40,80,.04); }
</style>
""", unsafe_allow_html=True)

MESES = {"01":"Jan","02":"Fev","03":"Mar","04":"Abr","05":"Mai","06":"Jun",
         "07":"Jul","08":"Ago","09":"Set","10":"Out","11":"Nov","12":"Dez"}
MESES_F = {"01":"Janeiro","02":"Fevereiro","03":"Março","04":"Abril","05":"Maio",
           "06":"Junho","07":"Julho","08":"Agosto","09":"Setembro",
           "10":"Outubro","11":"Novembro","12":"Dezembro"}

def brl(v):
    try:
        s = "{:,.2f}".format(float(v))
        return "R$ " + s.replace(",","X").replace(".",",").replace("X",".")
    except (ValueError, TypeError):
        return "R$ 0,00"

def brl_k(v):
    v = float(v or 0)
    if abs(v) >= 1_000_000: return f"R$ {v/1_000_000:.1f}M"
    if abs(v) >= 1_000: return f"R$ {v/1_000:.0f}k"
    return f"R$ {v:.0f}"

def fmt_df(df, money=(), pct=()):
    """Formata colunas no padrão BR (R$ 100.000,00 / 12,3%) como texto, para
    o dataframe exibir certo (o NumberColumn do Streamlit não faz milhar BR)."""
    d = df.copy()
    for c in money:
        if c in d.columns:
            d[c] = d[c].apply(lambda v: brl(v) if (pd.notna(v) and not isinstance(v, str))
                              else (v if (isinstance(v, str) and v) else "—"))
    for c in pct:
        if c in d.columns:
            d[c] = d[c].apply(lambda v: (f"{v:.1f}%".replace(".", ",")) if (pd.notna(v) and not isinstance(v, str))
                              else (v if (isinstance(v, str) and v) else "—"))
    return d


def tabela_barra(pares, label_col="Item", money=True):
    """Renderiza uma tabela 'executiva' com valor formatado (R$ BR ou inteiro) +
    uma barra de PARTICIPAÇÃO (%). Substitui gráficos mantendo o número visível.
    `pares`: lista de (rótulo, valor) já ordenada como desejado."""
    pares = [(l, float(v or 0)) for l, v in pares]
    total = sum(v for _, v in pares) or 1
    vcol = "Valor" if money else "Qtd"
    d = pd.DataFrame({
        label_col: [l for l, _ in pares],
        vcol: [ (brl(v) if money else f"{int(v)}") for _, v in pares ],
        "Participação": [ v / total * 100 for _, v in pares ],
    })
    st.dataframe(d, use_container_width=True, hide_index=True, column_config={
        "Participação": st.column_config.ProgressColumn(
            "Participação", format="%.1f%%", min_value=0.0, max_value=100.0),
    })

def fper(p, full=False):
    if not p or "-" not in str(p): return str(p)
    a, m = str(p).split("-")
    return f"{(MESES_F if full else MESES).get(m, m)}/{a}"

def fdate(s):
    if not s: return ""
    try: return datetime.strptime(str(s), "%Y-%m-%d").strftime("%d/%m/%Y")
    except ValueError: return str(s)

def fmt_cpf(c):
    """CPF formatado 000.000.000-00."""
    if not c or len(c) != 11:
        return c or ""
    return f"{c[:3]}.{c[3:6]}.{c[6:9]}-{c[9:]}"

def mask_cpf(c):
    # respeita o checkbox 'Mostrar CPF completo' (global mostrar_cpf)
    if globals().get("mostrar_cpf"):
        return fmt_cpf(c)
    return f"•••.{c[3:6]}.{c[6:9]}-••" if c and len(c) == 11 else (c or "")

def kpi(col, valor, label, delta="", direcao="n"):
    with col:
        d = f"<div class='d {direcao}'>{delta}</div>" if delta else ""
        st.markdown(f"<div class='kpi'><div class='v'>{valor}</div>"
                    f"<div class='l'>{label}</div>{d}</div>", unsafe_allow_html=True)

def parse_brl_in(s):
    """Aceita o que o usuário digitar: '5423078', '5.423.078', '5.423.078,90'."""
    if s is None: return 0.0
    t = str(s).strip().replace("R$", "").replace(" ", "")
    if not t: return 0.0
    t = t.replace(".", "").replace(",", ".")   # ponto = milhar, vírgula = decimal
    try: return float(t)
    except ValueError: return 0.0

def _fmt_in(v):
    """Formata para exibir no campo: 5423078 -> '5.423.078,00' (sem 'R$')."""
    v = float(v or 0)
    return brl(v).replace("R$ ", "") if v else ""

def editor_faturamento(comps, key_base, store="fat_por_comp", coluna="Faturamento (R$)",
                       label_col="Competência", label_fn=None):
    """Editor com pontuação automática (campo de texto BR).
    Lê/grava em st.session_state[store] (chave = item; competência ou categoria)."""
    if label_fn is None:
        label_fn = lambda p: fper(p, True)
    if store not in st.session_state:
        st.session_state[store] = {}
    vkey = f"{key_base}_ver"
    if vkey not in st.session_state:
        st.session_state[vkey] = 0
    seed = [_fmt_in(st.session_state[store].get(p, 0)) for p in comps]
    ed = pd.DataFrame({label_col: [label_fn(p) for p in comps], coluna: seed})
    out = st.data_editor(
        ed, hide_index=True, use_container_width=True,
        key=f"{key_base}_{st.session_state[vkey]}",
        column_config={
            label_col: st.column_config.TextColumn(label_col, disabled=True),
            coluna: st.column_config.TextColumn(
                coluna, help="Digite o valor — a pontuação é aplicada automaticamente. "
                             "Ex.: 250000 ou 250.000,00"),
        })
    typed = [str(x).strip() if x is not None else "" for x in out[coluna]]
    vals = [parse_brl_in(x) for x in typed]
    for p, v in zip(comps, vals):
        st.session_state[store][p] = v
    if [_fmt_in(v) for v in vals] != typed:
        st.session_state[vkey] += 1
        st.rerun()

# ─────────────────────────────────────────────────────────────────────────────
# ESTADO GLOBAL
# ─────────────────────────────────────────────────────────────────────────────
if "analise" not in st.session_state:
    st.session_state.analise = None
if "upkey" not in st.session_state:
    st.session_state.upkey = 0

empresa = ""  # será preenchido pelo PGDAS quando disponível

# ── BARRA DE CONTROLE SUPERIOR ────────────────────────────────────────────────
_tb_left, _tb_mid, _tb_right = st.columns([3, 1, 1])
with _tb_left:
    empresa = st.text_input("Nome do cliente / empresa",
                            placeholder="Ex.: Padaria São João Ltda",
                            label_visibility="collapsed",
                            key="empresa_input")
with _tb_mid:
    mostrar_cpf = st.checkbox("🔓 CPF completo", value=True,
                              help="Desmarque para mascarar CPF ao compartilhar a tela (LGPD).")
with _tb_right:
    if st.button("🔄 Recomeçar", use_container_width=True):
        _keep = st.session_state.get("upkey", 0) + 1
        for k in list(st.session_state.keys()):
            del st.session_state[k]
        st.session_state.analise = None
        st.session_state.upkey = _keep
        st.rerun()

# botão Início só aparece quando já está em um modo
if st.session_state.get("analise") is not None and st.session_state.get("modo"):
    if st.button("🏠 Início", use_container_width=True):
        st.session_state.modo = None
        st.rerun()

st.divider()

D = st.session_state.analise

# se o cliente não digitou o nome, usa a razão social lida do PGDAS
if not empresa:
    empresa = st.session_state.get("empresa_pgdas", "")

def _cnpj_raiz(c):
    c = re.sub(r"\D", "", str(c or ""))
    return c[:8] if len(c) >= 8 else c

def pgdas_confere_cnpj(r):
    """Confere se o CNPJ do PGDAS bate com o do XML (pela raiz de 8 dígitos).
    Retorna (ok, mensagem_html) — ok=None quando não dá para comparar."""
    cx = _cnpj_raiz((D or {}).get("_cnpj")) if D else ""
    cp = _cnpj_raiz(r.get("cnpj"))
    if not cx or not cp:
        return None, ""
    if cx == cp:
        return True, ""
    return False, (f"⚠️ <b>CNPJ diferente!</b> O PGDAS é do CNPJ <b>{cp[:8]}…</b> e o XML "
                   f"carregado é do <b>{cx[:8]}…</b>. Pode ser de outra empresa — confira "
                   "antes de usar, para não misturar dados.")

if D is None:
    st.markdown("<div class='hero'><h1>📋 Análise de Folha × Nota de Serviço</h1>"
                "<p>Anexe os arquivos do eSocial (ZIP/XML) e comece. Depois você escolhe entre "
                "<b>🎯 Simulador PGDAS</b> (quanto de nota emitir) e <b>📊 Análise de Folha</b> "
                "(painel completo).</p></div>", unsafe_allow_html=True)
    _cu1, _cu2 = st.columns([2, 1])
    with _cu1:
        uploaded = st.file_uploader("Arquivos do eSocial (ZIP ou XML) — pode anexar vários meses",
                                    type=["zip", "xml"], accept_multiple_files=True,
                                    key=f"uploader_{st.session_state.upkey}")
    with _cu2:
        st.markdown("<div style='height:28px'></div>", unsafe_allow_html=True)
        if st.button("▶️ Iniciar", type="primary", use_container_width=True):
            with st.spinner("Lendo eventos do eSocial..."):
                st.session_state.analise = ep.carregar(uploaded) if uploaded else ep.carregar([])
            st.session_state.modo = None
            st.session_state.fat_confirmado = False
            st.rerun()
    if uploaded:
        st.success(f"✅ {len(uploaded)} arquivo(s) anexado(s). Clique em **▶️ Iniciar**.")
    else:
        st.caption("Sem XML? Clique em **▶️ Iniciar** assim mesmo — no Simulador você digita os valores manualmente.")
    st.markdown("<div style='height:8px'></div>", unsafe_allow_html=True)
    c1, c2 = st.columns(2)
    c1.markdown("<div class='box'><h3>🎯 Simulador PGDAS</h3>"
                "<p style='font-size:13px;color:#48535f'>Quanto de <b>nota emitir</b> para sustentar "
                "a folha, com DAS e CPP por tipo de receita (sem/com ST, fator R). Usa o XML + o PGDAS "
                "anterior. Ideal <b>antes</b> de fazer o PGDAS do mês.</p></div>", unsafe_allow_html=True)
    c2.markdown("<div class='box'><h3>📊 Análise de Folha</h3>"
                "<p style='font-size:13px;color:#48535f'>Custo real de pessoal, encargos, gastos por "
                "mês, <b>faturamento × folha</b>, movimentação, conferência e relatório — tudo do XML. "
                "Anexe o PGDAS para incluir o CPP do Simples.</p></div>", unsafe_allow_html=True)
    st.stop()

def _mes_anterior(p):
    try:
        y, m = str(p).split("-"); y = int(y); m = int(m) - 1
        if m == 0: m = 12; y -= 1
        return f"{y:04d}-{m:02d}"
    except Exception:
        return None

# ─────────────────────────────────────────────────────────────────────────────
# CONFORMIDADE — checklist de risco para empresas prestadoras de serviço
# ─────────────────────────────────────────────────────────────────────────────
CONFORMIDADE_SECOES = [
    {"id": "s1", "icone": "🏢", "titulo": "1. Cadastro e Documentação Societária",
     "desc": "Verificar dados formais das empresas envolvidas",
     "alerta": ("laranja", "Registre separadamente cada empresa do grupo — empresa principal, "
                "prestadora(s), matriz e filiais. Mesmos sócios ou endereço não tornam a estrutura "
                "irregular por si só, mas exigem análise mais rigorosa."),
     "itens": [
        ("cnpj_ativo", "critico", "CNPJ ativo e situação cadastral regular (Receita Federal)",
         "Consultar no portal da RFB. CNPJ inapto ou baixado invalida toda a estrutura."),
        ("cnae_compativel", "critico", "CNAE principal e secundários compatíveis com a atividade real",
         "O CNAE não pode ser escolhido apenas para reduzir tributo ou \"cobrir\" atividade diferente."),
        ("objeto_social", "critico", "Objeto social descreve o serviço que será de fato prestado",
         "Objeto genérico como \"prestação de serviços em geral\" é indício de fragilidade."),
        ("capital_compativel", "alto", "Capital social compatível com o porte e a operação (folha+encargos)",
         "Capital irrisório em empresa com folha alta é sinal de risco alto."),
        ("data_abertura", "alto", "Data de abertura anterior à admissão dos empregados transferidos",
         "Empregados admitidos antes da abertura exigem justificativa formal."),
        ("ie_im", "medio", "Inscrição estadual e municipal obtidas quando obrigatórias", ""),
        ("quadro_societario", "medio", "Quadro societário documentado — sócios, participações, poderes",
         "Identificar relações familiares entre sócios das empresas relacionadas."),
        ("regime_tributario", "medio", "Regime tributário definido e compatível com a atividade",
         "Cessão/locação de mão de obra é, como regra, impeditiva ao Simples Nacional."),
     ]},
    {"id": "s2", "icone": "🗺️", "titulo": "2. Operação Real — Mapa de Atividades",
     "desc": "Comprovar que existe prestação de serviço determinada e específica",
     "alerta": ("vermelho", "Regra central (Lei 6.019/1974): a prestadora deve realizar serviços "
                "determinados e específicos, sendo responsável pela contratação, remuneração e "
                "direção dos trabalhadores. Simples cessão de mão de obra não é prestação de serviço."),
     "itens": [
        ("servico_definido", "critico", "Existe serviço claramente definido — não é \"fornecimento de pessoal\"",
         "Ex. correto: execução do setor de produção. Ex. errado: disponibilizar empregados."),
        ("servico_mensuravel", "critico", "O serviço é mensurável e possui entregáveis/indicadores",
         "Ex: kg produzidos, pedidos entregues, relatório mensal."),
        ("atividade_compativel", "critico", "Atividade real dos empregados é compatível com CNAE/objeto social", ""),
        ("unidades_identificadas", "alto", "Identificadas as unidades onde o serviço será prestado",
         "Empregado em unidade não cadastrada no contrato é indício de desvio."),
        ("preposto_presente", "alto", "Existe preposto ou gestor da prestadora presente na operação",
         "Gestão exclusiva pela tomadora é sinal crítico de subordinação direta."),
        ("controle_jornada", "alto", "Mapeado quem define escala, controla ponto e autoriza horas extras",
         "Se a tomadora controla tudo, há subordinação direta independente do contrato."),
        ("decisao_admissao", "medio", "Definido quem aplica advertências e decide admissão/demissão", ""),
        ("uniforme_epi", "medio", "Uniformes, EPIs e ferramentas fornecidos pela prestadora",
         "Fornecimento pela tomadora reforça o vínculo direto com ela."),
     ]},
    {"id": "s3", "icone": "👥", "titulo": "3. Trabalhadores — Registro e Vínculo",
     "desc": "Cada empregado individualmente verificado",
     "alerta": None,
     "itens": [
        ("esocial_transmitido", "critico", "Todos os empregados registrados no eSocial da prestadora (S-2200)", ""),
        ("cbo_compativel", "critico", "CBO de cada empregado é compatível com a função real exercida",
         "CBO de \"auxiliar administrativo\" para quem trabalha na produção é incompatível."),
        ("transferencia_formal", "critico", "Transferências de empresa com documentação formal",
         "Empregado \"transferido\" informalmente sem documento é passivo trabalhista grave."),
        ("folha_paga_prestadora", "alto", "Folha paga integralmente pela prestadora — sem socorro da tomadora", ""),
        ("fgts_prestadora", "alto", "FGTS depositado mensalmente pela prestadora no FGTS Digital", ""),
        ("sem_circulacao", "alto", "Nenhum empregado circula entre empresas sem registro formal", ""),
        ("logomarca", "medio", "Logomarca no uniforme é da prestadora — não exclusivamente da tomadora", ""),
     ]},
    {"id": "s4", "icone": "📄", "titulo": "4. Contrato de Prestação de Serviços",
     "desc": "O contrato deve refletir a operação real — nunca o contrário",
     "alerta": ("vermelho", "O contrato é consequência da operação, não o ponto de partida. Um contrato "
                "bem escrito sobre operação inexistente ou falsa agrava a situação — caracteriza fraude documental."),
     "itens": [
        ("contrato_nao_retroativo", "critico", "Contrato assinado antes do início dos serviços (não retroativo)", ""),
        ("objeto_especifico", "critico", "Objeto do contrato descreve serviço específico — não \"mão de obra\"", ""),
        ("valor_nao_e_folha", "critico", "Valor do contrato não é exatamente igual a folha+FGTS+imposto",
         "Preço = folha + X não remunera serviço. O contrato deve remunerar serviço com entregáveis."),
        ("previsao_medicao", "alto", "Contrato prevê medição, indicadores e relatório mensal de execução", ""),
        ("preposto_no_contrato", "alto", "Contrato identifica preposto da prestadora responsável pela equipe", ""),
        ("clausulas_sst", "alto", "Cláusulas de SST, EPI e responsabilidade por acidentes definidas", ""),
        ("proibicao_pgto_direto", "alto", "Cláusula proíbe pagamento direto de salário pela tomadora", ""),
        ("vigencia_reajuste", "medio", "Prazo de vigência, reajuste e condições de rescisão definidos", ""),
        ("relatorio_mensal", "medio", "Relatório mensal de execução produzido e arquivado por competência",
         "Relatório inexistente = serviço não comprovado, mesmo com contrato."),
     ]},
    {"id": "s5", "icone": "💰", "titulo": "5. Fiscal — PGDAS, Notas e Conciliação",
     "desc": "Receita declarada deve bater com documentos e movimentação bancária",
     "alerta": None,
     "itens": [
        ("pgdas_suportado", "critico", "Receita do PGDAS-D é suportada por notas fiscais do mesmo período",
         "PGDAS maior que notas = receita artificial. Notas maiores = subnotificação."),
        ("comercio_com_estoque", "critico", "Receita de comércio possui notas de entrada, estoque e saída",
         "Venda de mercadorias sem compra e sem estoque é operação fictícia."),
        ("servico_comprovado", "critico", "Receita de serviços possui contrato, OS ou relatório comprobatório", ""),
        ("pagamento_conta_propria", "critico", "Pagamentos recebidos transitam pela conta bancária da prestadora",
         "Recebimento direto na conta da tomadora é confusão patrimonial grave."),
        ("simples_validado", "alto", "Enquadramento no Simples Nacional validado (atividade não impeditiva)",
         "Não concluir automaticamente. Exige validação tributária formal."),
        ("retencao_analisada", "alto", "Análise de retenção previdenciária (11%) e ISS pelo tomador",
         "Serviços por cessão de mão de obra/empreitada: analisar IN RFB 2.110/2022."),
        ("conciliacao_mensal", "alto", "Conciliação mensal: PGDAS × NF-e × NFS-e × banco × folha × encargos", ""),
        ("das_em_dia", "medio", "DAS recolhido dentro do prazo e comprovante arquivado", ""),
     ]},
    {"id": "s6", "icone": "🏦", "titulo": "6. Autonomia Financeira da Prestadora",
     "desc": "Comprovar que a empresa tem vida própria e capacidade econômica",
     "alerta": ("laranja", "Confusão patrimonial: uma empresa que não consegue pagar a própria folha sem "
                "transferências informais da tomadora não possui autonomia real — vira operação de fachada."),
     "itens": [
        ("conta_propria", "critico", "Prestadora possui conta bancária própria, separada da tomadora", ""),
        ("saldo_compativel", "critico", "Saldo bancário mensal compatível com pagamento de folha/FGTS/encargos",
         "Dinheiro só disponível após receber da tomadora = dependência total."),
        ("despesas_proprias", "alto", "Despesas próprias (contador, aluguel, tecnologia) pagas pela prestadora",
         "Tomadora pagando contas da prestadora é confusão patrimonial."),
        ("margem_real", "alto", "Existe margem de lucro real — a prestadora não opera no zero a zero",
         "Receita igual a custo toda competência indica preço calculado só para cobrir folha."),
        ("emprestimos_formais", "alto", "Empréstimos entre empresas possuem contrato com juros e prazo", ""),
        ("cliente_unico", "medio", "Avaliado o risco de dependência de cliente único",
         "Cliente único não é ilegal, mas aumenta o risco de caracterização como fachada."),
     ]},
    {"id": "s7", "icone": "🦺", "titulo": "7. Saúde e Segurança do Trabalho (SST)",
     "desc": "Regularidade fiscal não protege contra fiscalização trabalhista",
     "alerta": None,
     "itens": [
        ("pgr", "critico", "PGR (Programa de Gerenciamento de Riscos) elaborado e atualizado — NR-1", ""),
        ("pcmso", "critico", "PCMSO vigente", ""),
        ("aso_valido", "critico", "ASO válido para cada empregado (admissional/periódico/mudança de risco)", ""),
        ("laudos", "alto", "Laudos de insalubridade e periculosidade emitidos quando exigido",
         "Laudo ausente = pagamento indevido ou adicional faltante = passivo trabalhista."),
        ("epi_ficha", "alto", "Fichas de EPI assinadas e CAs vigentes", ""),
        ("treinamentos", "alto", "Treinamentos obrigatórios realizados e documentados", ""),
        ("responsabilidade_sst", "alto", "Responsabilidade por SST claramente definida no contrato",
         "Ausência de definição = ambas respondem solidariamente em acidente."),
        ("cat_emitida", "medio", "Acidentes anteriores possuem CAT emitida e registrada no eSocial", ""),
     ]},
    {"id": "s8", "icone": "🚨", "titulo": "8. Alertas — Sinais de Risco Grave",
     "desc": "Se qualquer item abaixo for identificado: suspender e encaminhar para análise jurídica",
     "alerta": ("vermelho", "Quando qualquer item abaixo for identificado, NÃO emita parecer de "
                "conformidade. Encaminhe para validação jurídica e tributária antes de qualquer recomendação."),
     "itens": [
        ("alerta_sem_estoque", "critico", "Ausente: receita de mercadorias sem nenhuma compra ou estoque", ""),
        ("alerta_sem_contrato", "critico", "Ausente: receita de serviços sem contrato, relatório ou tomador identificado", ""),
        ("alerta_pgto_direto", "critico", "Ausente: tomadora paga diretamente salários de empregados da prestadora", ""),
        ("alerta_direcao_total", "critico", "Ausente: todos os empregados dirigidos exclusivamente pela tomadora", ""),
        ("alerta_pgdas_sem_doc", "critico", "Ausente: PGDAS-D com receitas sem qualquer documento correspondente", ""),
        ("alerta_sem_conta", "critico", "Ausente: prestadora sem conta própria ou sem capacidade de pagar folha sozinha", ""),
        ("alerta_impeditivo", "critico", "Ausente: atividade impeditiva ao Simples (cessão de mão de obra pura)", ""),
     ]},
]

# ── diagnóstico de risco: questionário Sim/Não (metodologia trabalhista/previd./tributário) ──
# cada pergunta é redigida de forma que "Sim" = sinal de risco (red flag)
DIAGNOSTICO_AREAS = [
    {"id": "trabalhista", "titulo": "⚖️ Trabalhista — Pejotização e Vínculo de Emprego",
     "perguntas": [
        ("pejot_exclusividade", "Pejotização/Vínculo",
         "O prestador PJ atua com exclusividade, prestando serviço apenas para este tomador?",
         "alto", "CLT, art. 3º",
         "Reavaliar carteira de clientes do prestador; documentar múltiplos tomadores se houver."),
        ("pejot_horario", "Pejotização/Vínculo",
         "O prestador cumpre horário fixo determinado/controlado pelo tomador?",
         "alto", "CLT, art. 3º e 6º",
         "Migrar para remuneração por entrega/projeto e eliminar controle de jornada."),
        ("pejot_subordinacao", "Pejotização/Vínculo",
         "O prestador recebe ordens diretas e está sob subordinação hierárquica do tomador?",
         "alto", "CLT, art. 3º",
         "Redesenhar governança do contrato: gestão por resultado, não por comando direto."),
        ("pejot_remuneracao_fixa", "Pejotização/Vínculo",
         "A remuneração é fixa mensal, sem vínculo com entregas, metas ou projetos?",
         "alto", "CLT, art. 3º (onerosidade/habitualidade)",
         "Vincular remuneração a entregáveis específicos e mensuráveis."),
        ("pejot_integracao", "Pejotização/Vínculo",
         "O prestador utiliza crachá, e-mail corporativo, uniforme ou estrutura do tomador como empregado?",
         "alto", "CLT, art. 3º; Súmula 331 TST",
         "Eliminar elementos de integração que sugerem subordinação/pessoalidade."),
        ("pejot_objeto_generico", "Pejotização/Vínculo",
         "O contrato de prestação de serviços descreve o objeto de forma genérica, sem especialização técnica clara?",
         "alto", "Lei 13.429/2017",
         "Redigir objeto contratual específico e tecnicamente delimitado."),
        ("pejot_sem_especializacao", "Pejotização/Vínculo",
         "Houve terceirização de atividade sem observância dos requisitos de especialização previstos em lei?",
         "alto", "Lei 13.429/2017 e 13.467/2017",
         "Revisar contrato de terceirização e comprovar especialização do serviço."),
        ("grupo_economico", "Grupo Econômico e Estrutura",
         "Há indícios de grupo econômico não declarado (mesma direção, funcionários e estrutura compartilhados)?",
         "alto", "CLT, art. 2º, §2º",
         "Formalizar (ou desfazer) a relação de grupo econômico com documentação societária clara."),
        ("esocial_divergente", "Grupo Econômico e Estrutura",
         "Existe divergência entre os dados informados no eSocial e a realidade da prestação de serviço?",
         "alto", "Decreto 8.373/2014 (eSocial)",
         "Auditar e corrigir informações do eSocial antes de fiscalização."),
        ("mei_exclusividade", "MEI / Autônomo",
         "O MEI ou autônomo contratado presta serviço apenas para esta empresa, com habitualidade?",
         "alto", "CLT, art. 3º; LC 128/2008 (MEI)",
         "Verificar se o MEI atende múltiplos clientes; documentar autonomia real."),
     ]},
    {"id": "previdenciario", "titulo": "🏛️ Previdenciário — Retenções e Fatos Geradores",
     "perguntas": [
        ("cessao_sem_retencao", "Retenção de INSS (Cessão de Mão de Obra)",
         "A empresa presta serviço mediante cessão de mão de obra (Anexo IV do Simples) sem que o tomador retenha 11%?",
         "alto", "Lei 8.212/91, art. 31; IN RFB 971/2009",
         "Orientar o tomador a reter e recolher os 11% na nota fiscal."),
        ("tomador_sem_retencao", "Retenção de INSS (Cessão de Mão de Obra)",
         "O tomador de serviços não está retendo a contribuição previdenciária de 11% quando exigido?",
         "alto", "Lei 8.212/91, art. 31",
         "Notificar formalmente o tomador sobre a obrigação de retenção."),
        ("anexo_incompativel", "Retenção de INSS (Cessão de Mão de Obra)",
         "A empresa está classificada em Anexo do Simples incompatível com a atividade de cessão de mão de obra exercida?",
         "alto", "LC 123/2006, art. 18, §5º-C/§5º-H",
         "Reclassificar CNAE/Anexo conforme a atividade efetivamente exercida."),
        ("fatos_geradores_omissos", "Fatos Geradores e Malha Fiscal",
         "Existe omissão de fatos geradores de contribuição previdenciária (funcionários não registrados)?",
         "alto", "Lei 8.212/91; CP, art. 337-A",
         "Regularizar registros e recolhimentos retroativos antes de autuação."),
        ("dctfweb_divergente", "Fatos Geradores e Malha Fiscal",
         "Há divergência entre os valores informados na DCTFWeb e a folha de pagamento real?",
         "alto", "IN RFB 2.005/2021 (DCTFWeb)",
         "Conciliar DCTFWeb x eSocial x folha antes do envio das obrigações."),
        ("sem_comprovantes_retencao", "Fatos Geradores e Malha Fiscal",
         "A empresa não mantém documentação comprobatória das retenções de INSS de terceiros recebidas/efetuadas?",
         "medio", "IN RFB 971/2009, art. 88",
         "Organizar arquivo de comprovantes de retenção por, no mínimo, 5 anos."),
        ("prolabore_baixo", "Pró-labore e Distribuição de Lucros",
         "O pró-labore dos sócios é artificialmente baixo, com distribuição de lucros elevada e desproporcional?",
         "alto", "Lei 8.212/91, art. 28; RIR/2018",
         "Reequilibrar pró-labore compatível com a função exercida pelo sócio."),
        ("rat_fap_divergente", "Pró-labore e Distribuição de Lucros",
         "Há divergência no cálculo/recolhimento do RAT/FAP da empresa?",
         "medio", "Lei 8.212/91, art. 22, II; Decreto 6.957/2009",
         "Revisar CNAE de risco e alíquota de RAT/FAP aplicada."),
     ]},
    {"id": "tributario", "titulo": "💸 Planejamento Tributário — Risco de Simulação",
     "perguntas": [
        ("fracionamento_sem_proposito", "Reorganização Societária",
         "A empresa foi fracionada em múltiplas PJs para permanecer nas faixas do Simples, sem propósito negocial real?",
         "alto", "CTN, art. 116, § único; jurisprudência CARF",
         "Documentar propósito negocial (mercados, operações e sócios distintos) ou reunificar estrutura."),
        ("reorganizacao_sem_documentacao", "Reorganização Societária",
         "Houve reorganização societária recente sem ata, laudo ou justificativa formal do propósito negocial?",
         "medio", "CTN, art. 116, § único",
         "Produzir documentação contemporânea que sustente a motivação da reorganização."),
        ("confusao_patrimonial_trib", "Reorganização Societária",
         "Existe confusão patrimonial entre empresas do grupo (mesmo endereço, funcionários e estrutura operacional)?",
         "alto", "Código Civil, art. 50",
         "Segregar efetivamente estrutura operacional, física e de pessoal entre as empresas."),
        ("precos_fora_mercado", "Simulação de Operações",
         "Há contratos entre empresas do mesmo grupo com preços/condições fora de padrão de mercado, reduzindo tributos?",
         "alto", "CTN, art. 116, § único; art. 149",
         "Ajustar contratos e preços de transferência a parâmetros de mercado (arm's length)."),
        ("distribuicao_desproporcional", "Simulação de Operações",
         "A distribuição de lucros aos sócios é desproporcional à participação societária, sem previsão no contrato social?",
         "medio", "Lei 6.404/76 (por analogia); RIR/2018, art. 238",
         "Prever expressamente distribuição desproporcional no contrato social, com justificativa."),
     ]},
]

_RESPOSTA_OPCOES = ["— não respondido —", "Sim", "Não", "N.A."]

# ── plano de ação 5W2H: modelo genérico inspirado em caso real de alto risco ──
PLANO_5W2H_MODELO = [
    {"o_que": "Suspender novas admissões via a empresa terceirizada até revisão jurídica",
     "por_que": "Estancar o agravamento do risco enquanto o caso é analisado",
     "onde": "Tomadora e empresa terceirizada", "quando": "Imediato (esta semana)",
     "quem": "Sócios / Direção", "como": "Comunicado interno suspendendo novas contratações pela terceirizada",
     "quanto_custa": "R$ 0", "prioridade": "Altíssima", "status": "Pendente"},
    {"o_que": "Contratar avaliação jurídica trabalhista especializada",
     "por_que": "Avaliar exposição real e estratégia de regularização",
     "onde": "Escritório de advocacia trabalhista", "quando": "Em até 7 dias",
     "quem": "Sócios + advogado trabalhista", "como": "Apresentar histórico completo para parecer técnico",
     "quanto_custa": "Honorários do escritório", "prioridade": "Altíssima", "status": "Pendente"},
    {"o_que": "Reinternalizar funções de comando/gerência sob subordinação direta da tomadora",
     "por_que": "Manter a função de comando 'terceirizada' é o maior ponto de exposição",
     "onde": "Tomadora", "quando": "Em até 30 dias, após orientação jurídica",
     "quem": "RH/Departamento Pessoal + advogado", "como": "Rescisão do contrato PJ e novo registro CLT direto",
     "quanto_custa": "Encargos normais de registro CLT", "prioridade": "Altíssima", "status": "Pendente"},
    {"o_que": "Reinternalizar atividade-fim quando há dependência exclusiva sem propósito negocial",
     "por_que": "Terceirizar atividade-fim sem especialização é o núcleo do risco de fraude",
     "onde": "Tomadora", "quando": "Em até 60 dias, de forma escalonada",
     "quem": "RH/Departamento Pessoal + advogado", "como": "Migração gradual e documentada para o quadro CLT",
     "quanto_custa": "Encargos normais de registro CLT", "prioridade": "Altíssima", "status": "Pendente"},
    {"o_que": "Avaliar regularização espontânea junto a órgãos competentes",
     "por_que": "Denúncia espontânea pode reduzir multas em relação a autuação de ofício",
     "onde": "Receita Federal / Ministério do Trabalho", "quando": "Após orientação jurídica",
     "quem": "Contador + advogado tributário/trabalhista", "como": "Levantar passivo estimado e instrumentos disponíveis",
     "quanto_custa": "Custo de tributos/encargos retroativos", "prioridade": "Alta", "status": "Pendente"},
    {"o_que": "Decidir o destino da empresa terceirizada",
     "por_que": "Empresa sem outros clientes tende a ser vista como instrumento de fraude",
     "onde": "Empresa terceirizada", "quando": "Em até 90 dias",
     "quem": "Sócios + contador + advogado",
     "como": "Avaliar: (a) dissolver e reinternalizar, ou (b) manter só p/ atividades de apoio com outros clientes",
     "quanto_custa": "Custo de baixa/alteração societária", "prioridade": "Alta", "status": "Pendente"},
    {"o_que": "Reconstituir apenas terceirizações de baixo risco, com contrato adequado",
     "por_que": "Persistir terceirizando somente o que é seguro (limpeza, manutenção, TI, administrativo)",
     "onde": "Tomadora", "quando": "Após reinternalização das funções de risco",
     "quem": "Sócios + contador", "como": "Usar modelo de contrato e checklist de conformidade já elaborados",
     "quanto_custa": "R$ 0 a baixo custo", "prioridade": "Média", "status": "Pendente"},
    {"o_que": "Provisionar contabilmente o passivo trabalhista contingente",
     "por_que": "Antecipar impacto financeiro caso haja reclamações futuras",
     "onde": "Contabilidade", "quando": "No próximo balanço/fechamento",
     "quem": "Contador", "como": "Registrar provisão para contingências conforme estimativa do advogado",
     "quanto_custa": "Sem custo direto (lançamento contábil)", "prioridade": "Média", "status": "Pendente"},
    {"o_que": "Implementar checklist de conformidade para toda contratação futura",
     "por_que": "Evitar repetição do padrão de risco em novas terceirizações",
     "onde": "Escritório/cliente", "quando": "A partir de agora", "quem": "Sócios + gestores responsáveis",
     "como": "Aplicar os critérios de seleção de prestador já documentados no checklist operacional",
     "quanto_custa": "R$ 0", "prioridade": "Média", "status": "Pendente"},
    {"o_que": "Revisar periodicamente com o checklist de riscos",
     "por_que": "Garantir que a situação regularizada não volte a se repetir",
     "onde": "Escritório/cliente", "quando": "A cada 6 meses", "quem": "Contador/consultor",
     "como": "Reaplicar o diagnóstico de risco e o checklist operacional",
     "quanto_custa": "R$ 0", "prioridade": "Baixa", "status": "Pendente"},
]

_RISK_COLOR = {"critico": "#c53030", "alto": "#c05621", "medio": "#975a16"}
_RISK_LABEL = {"critico": "CRÍTICO", "alto": "ALTO", "medio": "MÉDIO"}
_PAPEL_OPCOES = ["Prestadora", "Tomadora", "Ambas"]
_SITUACAO_OPCOES = ["Em análise", "Risco identificado", "Regularizada", "Encerrada"]
_SITUACAO_COR = {"Em análise": "#975a16", "Risco identificado": "#c53030",
                 "Regularizada": "#276749", "Encerrada": "#718096"}
# ── persistência: tudo via Supabase (schema esocial_dashboard) ──────────────
# empresas, checklist, diagnóstico de risco, plano de ação e documentos vivem
# no banco — ver db_supabase.py. As funções abaixo mantêm nomes compatíveis
# com o restante do app para minimizar mudanças nos pontos de chamada.
def _empresas_carregar():
    return db.empresas_listar()

def _diagnostico_carregar(empresa_id):
    itens, observacoes, pendentes = db.checklist_carregar(empresa_id)
    return {"itens": itens, "observacoes": observacoes, "pendentes": pendentes}

def _diagnostico_upsert(empresa_id, item_id, verificado, observacao, pendente=False):
    db.checklist_upsert_item(empresa_id, item_id, verificado, observacao, pendente)

def _risco_carregar(empresa_id):
    respostas, observacoes = db.risco_carregar(empresa_id)
    return {"respostas": respostas, "observacoes": observacoes}

def _risco_upsert(empresa_id, pergunta_id, resposta, observacao):
    if resposta not in ("Sim", "Não", "N.A."):
        resposta = None
    db.risco_upsert_item(empresa_id, pergunta_id, resposta, observacao)

def _calcular_painel_risco(respostas):
    """Conta itens Alto/Médio/Baixo por área, a partir das respostas Sim/Não/N.A."""
    painel = {}
    total_alto = total_medio = total_respondidos = 0
    for area in DIAGNOSTICO_AREAS:
        alto = medio = baixo = respondidos = 0
        for qid, categoria, pergunta, severidade, base_legal, acao in area["perguntas"]:
            resp = respostas.get(qid)
            if resp in ("Sim", "Não", "N.A."):
                respondidos += 1
            if resp == "Sim":
                if severidade == "alto":
                    alto += 1
                else:
                    medio += 1
            elif resp in ("Não", "N.A."):
                baixo += 1
        painel[area["id"]] = {"alto": alto, "medio": medio, "baixo": baixo, "respondidos": respondidos}
        total_alto += alto
        total_medio += medio
        total_respondidos += respondidos
    if total_alto >= 3:
        nivel_geral = "ALTO"
    elif total_alto >= 1 or total_medio >= 2:
        nivel_geral = "MÉDIO"
    elif total_respondidos > 0:
        nivel_geral = "BAIXO"
    else:
        nivel_geral = "—"
    return painel, total_alto, total_medio, total_respondidos, nivel_geral

# ── plano de ação 5W2H — nomes compatíveis via db_supabase ───────────────────
def _plano_carregar(empresa_id):
    return db.plano_listar(empresa_id)

# ── documentos anexados (Storage do Supabase + mapa único por empresa) ───────
def _docs_mapa(empresa_id):
    """Uma única consulta trazendo os documentos de TODOS os itens da empresa,
    evitando N chamadas de rede (uma por item de checklist/risco)."""
    return db.docs_listar_mapa(empresa_id)

def _docs_salvar(empresa_id, item_id, arquivo):
    db.docs_salvar(empresa_id, item_id, arquivo, datetime.now().strftime("%Y%m%d%H%M%S"))

def _docs_remover(empresa_id, item_id, nome):
    db.docs_remover(empresa_id, item_id, nome)

def _gerar_dossie_zip(empresa):
    buf = io.BytesIO()
    empresa_id = empresa["id"]
    diag = _diagnostico_carregar(empresa_id)
    itens_estado = diag.get("itens", {})
    obs_checklist = diag.get("observacoes", {})
    pend_checklist = diag.get("pendentes", {})
    risco = _risco_carregar(empresa_id)
    respostas = risco.get("respostas", {})
    obs_risco = risco.get("observacoes", {})
    plano = _plano_carregar(empresa_id)
    docs_mapa = _docs_mapa(empresa_id)
    painel, total_alto, total_medio, total_resp, nivel_geral = _calcular_painel_risco(respostas)
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as zf:
        zf.writestr("empresa.json", json.dumps(empresa, ensure_ascii=False, indent=2, default=str))
        zf.writestr("diagnostico.json", json.dumps(diag, ensure_ascii=False, indent=2, default=str))
        zf.writestr("diagnostico_risco.json", json.dumps(risco, ensure_ascii=False, indent=2, default=str))
        zf.writestr("plano_5w2h.json", json.dumps(plano, ensure_ascii=False, indent=2, default=str))
        linhas = [f"DOSSIÊ DE CONFORMIDADE — {empresa.get('razao_social','')}",
                  f"CNPJ: {empresa.get('cnpj') or '—'}  ·  Papel: {empresa.get('papel','—')}  ·  "
                  f"Situação: {empresa.get('situacao','—')}",
                  f"Gerado em: {datetime.now().strftime('%d/%m/%Y %H:%M')}", "",
                  f"NÍVEL GERAL DE RISCO (sugestão preliminar): {nivel_geral}",
                  f"Total Alto: {total_alto}  ·  Total Médio: {total_medio}  ·  Respondidos: {total_resp}", ""]
        linhas.append("\n=== DIAGNÓSTICO DE RISCO (Trabalhista / Previdenciário / Tributário) ===")
        for area in DIAGNOSTICO_AREAS:
            p = painel[area["id"]]
            linhas.append(f"\n{area['titulo']} — Alto:{p['alto']} Médio:{p['medio']} Baixo:{p['baixo']}")
            for qid, categoria, pergunta, severidade, base_legal, acao in area["perguntas"]:
                resp = respostas.get(qid, "— não respondido —")
                ndocs_r = len(docs_mapa.get(f"risco_{qid}", []))
                linhas.append(f"  [{resp}] {pergunta} ({base_legal})"
                              f"{f' — {ndocs_r} doc(s) anexado(s)' if ndocs_r else ''}")
                if obs_risco.get(qid):
                    linhas.append(f"      Obs.: {obs_risco[qid]}")
        linhas.append("\n=== CHECKLIST OPERACIONAL ===")
        for sec in CONFORMIDADE_SECOES:
            linhas.append(f"\n{sec['icone']} {sec['titulo']}")
            for iid, risco_item, texto, nota in sec["itens"]:
                marca = "[PENDENTE]" if pend_checklist.get(iid) else ("[X]" if itens_estado.get(iid) else "[ ]")
                ndocs = len(docs_mapa.get(iid, []))
                linhas.append(f"  {marca} ({_RISK_LABEL[risco_item]}) {texto}"
                              f"{f' — {ndocs} doc(s) anexado(s)' if ndocs else ''}")
                if obs_checklist.get(iid):
                    linhas.append(f"      Obs.: {obs_checklist[iid]}")
        linhas.append("\n=== PLANO DE AÇÃO 5W2H ===")
        for item in plano:
            linhas.append(f"  [{item.get('status','Pendente')}] ({item.get('prioridade','—')}) "
                          f"{item.get('o_que','')}")
            if item.get("por_que"):
                linhas.append(f"      Por quê: {item['por_que']}")
            if item.get("como"):
                linhas.append(f"      Como: {item['como']}")
        zf.writestr("relatorio.txt", "\n".join(linhas))
        for sec in CONFORMIDADE_SECOES:
            for iid, risco_item, texto, nota in sec["itens"]:
                for nome in docs_mapa.get(iid, []):
                    zf.writestr(f"documentos/checklist_{iid}/{nome}", db.docs_baixar(empresa_id, iid, nome))
        for area in DIAGNOSTICO_AREAS:
            for qid, categoria, pergunta, severidade, base_legal, acao in area["perguntas"]:
                for nome in docs_mapa.get(f"risco_{qid}", []):
                    zf.writestr(f"documentos/risco_{qid}/{nome}",
                               db.docs_baixar(empresa_id, f"risco_{qid}", nome))
    buf.seek(0)
    return buf

# ── tela 1: lista de empresas cadastradas ────────────────────────────────────
def render_empresas_lista():
    st.markdown("<div class='hero'><h1>🛡️ Conformidade — Cadastro de Empresas</h1>"
                "<p>Cadastre cada empresa do grupo (tomadora e prestadora(s)) para consultar a situação "
                "em tempo real e reunir os documentos necessários para uma fiscalização. "
                "<b>Análise preliminar — sujeita à validação jurídica e tributária.</b></p></div>",
                unsafe_allow_html=True)

    empresas = _empresas_carregar()

    if empresas:
        _tot_emp = len(empresas)
        _risco_alto_n = _risco_medio_n = _crit_pend_total = 0
        for _e in empresas:
            _resp_e = _risco_carregar(_e["id"]).get("respostas", {})
            _, _, _, _, _nivel_e = _calcular_painel_risco(_resp_e)
            if _nivel_e == "ALTO":
                _risco_alto_n += 1
            elif _nivel_e == "MÉDIO":
                _risco_medio_n += 1
            _itens_e = _diagnostico_carregar(_e["id"]).get("itens", {})
            _crit_pend_total += sum(1 for s in CONFORMIDADE_SECOES for iid, risco_i, *_ in s["itens"]
                                    if risco_i == "critico" and not _itens_e.get(iid))

        st.markdown("##### 📊 Panorama geral do escritório")
        d1, d2, d3, d4 = st.columns(4)
        d1.metric("🏢 Empresas cadastradas", _tot_emp)
        d2.metric("🚨 Risco alto", _risco_alto_n)
        d3.metric("🟡 Risco médio", _risco_medio_n)
        d4.metric("🔴 Itens críticos pendentes", _crit_pend_total)
        st.divider()

    with st.expander("➕ Cadastrar nova empresa", expanded=(len(empresas) == 0)):
        with st.form("form_nova_empresa", clear_on_submit=True):
            c1, c2 = st.columns(2)
            razao = c1.text_input("Razão social *")
            fantasia = c2.text_input("Nome fantasia")
            c3, c4 = st.columns(2)
            cnpj = c3.text_input("CNPJ", placeholder="00.000.000/0000-00")
            papel = c4.selectbox("Papel no grupo", _PAPEL_OPCOES)
            c5, c6 = st.columns(2)
            grupo = c5.text_input("Grupo econômico", placeholder="Ex.: Grupo Sanfernando")
            cnae = c6.text_input("CNAE principal")
            c7, c8 = st.columns(2)
            abertura = c7.date_input("Data de abertura", value=None, format="DD/MM/YYYY")
            regime = c8.selectbox("Regime tributário",
                                  ["Simples Nacional", "Lucro Presumido", "Lucro Real", "MEI", "—"])
            obs = st.text_area("Observações")
            enviado = st.form_submit_button("Cadastrar empresa", type="primary", use_container_width=True)
            if enviado:
                if not razao.strip():
                    st.error("Informe a razão social.")
                else:
                    db.empresa_criar({
                        "razao_social": razao.strip(), "nome_fantasia": fantasia.strip(),
                        "cnpj": cnpj.strip(), "papel": papel, "grupo_economico": grupo.strip(),
                        "cnae_principal": cnae.strip(),
                        "data_abertura": abertura.isoformat() if abertura else None,
                        "regime_tributario": regime, "situacao": "Em análise", "observacoes": obs.strip(),
                    })
                    st.success(f"Empresa **{razao}** cadastrada!")
                    st.rerun()

    if not empresas:
        st.info("Nenhuma empresa cadastrada ainda. Use o formulário acima para começar.")
        return

    st.markdown(f"### 🏢 Empresas cadastradas ({len(empresas)})")
    _filtro = st.text_input("🔎 Filtrar por nome, CNPJ ou grupo", key="filtro_empresas")
    for emp in empresas:
        if _filtro:
            alvo = (f"{emp['razao_social']} {emp.get('nome_fantasia','')} "
                    f"{emp.get('cnpj','')} {emp.get('grupo_economico','')}").lower()
            if _filtro.lower() not in alvo:
                continue
        itens_estado = _diagnostico_carregar(emp["id"]).get("itens", {})
        total = sum(len(s["itens"]) for s in CONFORMIDADE_SECOES)
        ok = sum(1 for s in CONFORMIDADE_SECOES for iid, *_ in s["itens"] if itens_estado.get(iid))
        crit_pend = sum(1 for s in CONFORMIDADE_SECOES for iid, risco, *_ in s["itens"]
                        if risco == "critico" and not itens_estado.get(iid))
        pct = round(100 * ok / total) if total else 0
        _cor_sit = _SITUACAO_COR.get(emp.get("situacao", ""), "#718096")

        with st.container(border=True):
            cc1, cc2, cc3, cc4 = st.columns([3, 1, 1, 1])
            with cc1:
                st.markdown(f"**{emp['razao_social']}**"
                           f"{' — ' + emp['nome_fantasia'] if emp.get('nome_fantasia') else ''}")
                st.caption(f"CNPJ: {emp.get('cnpj') or '—'}  ·  {emp.get('papel','—')}"
                          f"{'  ·  Grupo: ' + emp['grupo_economico'] if emp.get('grupo_economico') else ''}")
            with cc2:
                st.markdown(f"<span style='font-size:11px;font-weight:800;padding:3px 10px;"
                           f"border-radius:99px;background:{_cor_sit}22;color:{_cor_sit};"
                           f"border:1px solid {_cor_sit}55'>{emp.get('situacao','—')}</span>",
                           unsafe_allow_html=True)
            with cc3:
                st.progress(pct/100, text=f"{pct}%")
            with cc4:
                if crit_pend:
                    st.markdown(f"<span style='color:#c53030;font-weight:700;font-size:12px'>"
                               f"🔴 {crit_pend} crítico(s)</span>", unsafe_allow_html=True)
                else:
                    st.markdown("<span style='color:#276749;font-weight:700;font-size:12px'>✅ ok</span>",
                               unsafe_allow_html=True)
            if st.button("Abrir ficha →", key=f"abrir_{emp['id']}", use_container_width=True):
                st.session_state.conf_empresa_id = emp["id"]
                st.rerun()

# ── tela 2: ficha da empresa (dados + checklist + documentos) ────────────────
def render_empresa_ficha(empresa):
    emp_id = empresa["id"]

    if st.button("⬅️ Voltar à lista de empresas"):
        st.session_state.conf_empresa_id = None
        st.rerun()

    _sit_cor_h = _SITUACAO_COR.get(empresa.get("situacao", ""), "#718096")
    st.markdown(f"<div class='hero'><h1>🛡️ {empresa['razao_social']}"
               f"<span style='font-size:12px;font-weight:800;padding:3px 12px;border-radius:99px;"
               f"background:{_sit_cor_h}22;color:{_sit_cor_h};border:1px solid {_sit_cor_h}55;"
               f"margin-left:12px;vertical-align:middle'>{empresa.get('situacao','—')}</span></h1>"
               f"<p>CNPJ: {empresa.get('cnpj') or '—'}  ·  {empresa.get('papel','—')}"
               f"{'  ·  Grupo: ' + empresa['grupo_economico'] if empresa.get('grupo_economico') else ''}</p></div>",
                unsafe_allow_html=True)

    with st.expander("✏️ Editar dados cadastrais"):
        with st.form(f"form_editar_{emp_id}"):
            c1, c2 = st.columns(2)
            razao = c1.text_input("Razão social", value=empresa.get("razao_social", ""))
            fantasia = c2.text_input("Nome fantasia", value=empresa.get("nome_fantasia", ""))
            c3, c4 = st.columns(2)
            cnpj = c3.text_input("CNPJ", value=empresa.get("cnpj", ""))
            _papel_idx = _PAPEL_OPCOES.index(empresa.get("papel")) if empresa.get("papel") in _PAPEL_OPCOES else 0
            papel = c4.selectbox("Papel no grupo", _PAPEL_OPCOES, index=_papel_idx)
            c5, c6 = st.columns(2)
            grupo = c5.text_input("Grupo econômico", value=empresa.get("grupo_economico", ""))
            cnae = c6.text_input("CNAE principal", value=empresa.get("cnae_principal", ""))
            _sit_idx = _SITUACAO_OPCOES.index(empresa.get("situacao")) if empresa.get("situacao") in _SITUACAO_OPCOES else 0
            situacao = st.selectbox("Situação", _SITUACAO_OPCOES, index=_sit_idx)
            obs = st.text_area("Observações", value=empresa.get("observacoes", ""))
            col_a, col_b = st.columns(2)
            salvar = col_a.form_submit_button("💾 Salvar alterações", type="primary", use_container_width=True)
            excluir = col_b.form_submit_button("🗑️ Excluir empresa", use_container_width=True)
            if salvar:
                db.empresa_atualizar(emp_id, {
                    "razao_social": razao.strip(), "nome_fantasia": fantasia.strip(),
                    "cnpj": cnpj.strip(), "papel": papel, "grupo_economico": grupo.strip(),
                    "cnae_principal": cnae.strip(), "situacao": situacao,
                    "observacoes": obs.strip(),
                })
                st.success("Dados atualizados!")
                st.rerun()
            if excluir:
                db.empresa_excluir(emp_id)
                st.session_state.conf_empresa_id = None
                st.success("Empresa excluída.")
                st.rerun()

    st.download_button("📦 Baixar dossiê completo (ZIP — dados + documentos)",
                       data=_gerar_dossie_zip(empresa), file_name=f"dossie_{emp_id}.zip",
                       mime="application/zip", use_container_width=True)

    st.divider()

    _alert_css = {
        "vermelho": ("#fff5f5", "#c53030", "#fc8181"),
        "laranja": ("#fffaf0", "#c05621", "#f6ad55"),
    }
    _nivel_cor = {"ALTO": "#c53030", "MÉDIO": "#975a16", "BAIXO": "#276749", "—": "#718096"}

    docs_mapa = _docs_mapa(emp_id)  # 1 consulta só, evita N chamadas de rede por item

    outer_tabs = st.tabs(["🔍 Diagnóstico de Risco", "📋 Checklist Operacional", "🎯 Plano de Ação 5W2H",
                         "📊 Simulações & Análises"])

    # ═══ ABA 1: DIAGNÓSTICO DE RISCO (Trabalhista / Previdenciário / Tributário) ═══
    with outer_tabs[0]:
        risco_key = f"risco_state_{emp_id}"
        risco_obs_key = f"risco_obs_state_{emp_id}"
        if risco_key not in st.session_state:
            _risco_carregado = _risco_carregar(emp_id)
            st.session_state[risco_key] = _risco_carregado.get("respostas", {})
            st.session_state[risco_obs_key] = _risco_carregado.get("observacoes", {})

        st.caption("Cada pergunta foi redigida de forma que a resposta **Sim** indica um sinal de risco "
                   "(red flag). O nível geral é uma sugestão preliminar — a classificação final exige "
                   "validação jurídica e tributária.")

        painel, total_alto, total_medio, total_resp, nivel_geral = _calcular_painel_risco(st.session_state[risco_key])

        if nivel_geral == "ALTO":
            st.markdown(
                "<div style='background:#fff5f5;border:1px solid #fc8181;color:#c53030;border-radius:10px;"
                "padding:14px 18px;margin-bottom:14px;font-size:13px'>"
                "🚨 <b>PADRÃO DE ALTO RISCO — AÇÃO IMEDIATA RECOMENDADA.</b> Recomenda-se acionar "
                "advogado trabalhista antes de qualquer decisão definitiva. A regularidade formal dos "
                "pagamentos (FGTS, INSS, DAS) não neutraliza o risco de fundo — a Justiça do Trabalho e o "
                "Fisco avaliam a realidade da relação, não a formalidade contratual. Veja a aba "
                "<b>🎯 Plano de Ação 5W2H</b>.</div>", unsafe_allow_html=True)

        nc1, nc2, nc3 = st.columns([2, 1, 1])
        with nc1:
            st.markdown(f"<div style='background:{_nivel_cor[nivel_geral]}15;border:1px solid "
                       f"{_nivel_cor[nivel_geral]}55;border-radius:10px;padding:10px 16px'>"
                       f"<span style='font-size:11px;text-transform:uppercase;letter-spacing:.05em;opacity:.7'>"
                       f"Nível geral de risco (sugestão)</span><br>"
                       f"<span style='font-size:20px;font-weight:800;color:{_nivel_cor[nivel_geral]}'>"
                       f"{nivel_geral}</span></div>", unsafe_allow_html=True)
        nc2.metric("🔴 Total Alto", total_alto)
        nc3.metric("🟡 Total Médio", total_medio)

        st.markdown("")
        painel_cols = st.columns(len(DIAGNOSTICO_AREAS))
        for col, area in zip(painel_cols, DIAGNOSTICO_AREAS):
            p = painel[area["id"]]
            with col:
                st.markdown(f"**{area['titulo']}**")
                st.caption(f"🔴 {p['alto']}  ·  🟡 {p['medio']}  ·  🟢 {p['baixo']}  ·  "
                          f"{p['respondidos']}/{len(area['perguntas'])} respondidas")

        if st.button("💾 Salvar diagnóstico de risco", key=f"salvar_risco_{emp_id}"):
            for _area in DIAGNOSTICO_AREAS:
                for _qid, *_ in _area["perguntas"]:
                    if _qid in st.session_state[risco_key] or _qid in st.session_state[risco_obs_key]:
                        _risco_upsert(emp_id, _qid, st.session_state[risco_key].get(_qid),
                                      st.session_state[risco_obs_key].get(_qid))
            st.success("Salvo!")

        st.divider()

        risco_tabs = st.tabs([a["titulo"] for a in DIAGNOSTICO_AREAS])
        for rtab, area in zip(risco_tabs, DIAGNOSTICO_AREAS):
            with rtab:
                for qid, categoria, pergunta, severidade, base_legal, acao in area["perguntas"]:
                    resp_atual = st.session_state[risco_key].get(qid, "— não respondido —")
                    _docs_r = docs_mapa.get(f"risco_{qid}", [])
                    _ndocs_r = len(_docs_r)
                    if resp_atual == "Sim":
                        _prefixo = "🔴" if severidade == "alto" else "🟡"
                    elif resp_atual in ("Não", "N.A."):
                        _prefixo = "✅"
                    else:
                        _prefixo = "⬜"
                    _sufixo_doc = f" · 📎{_ndocs_r}" if _ndocs_r else ""
                    with st.expander(f"{_prefixo} {pergunta}{_sufixo_doc}"):
                        st.caption(f"Categoria: {categoria}  ·  Base legal: {base_legal}")
                        _idx = _RESPOSTA_OPCOES.index(resp_atual) if resp_atual in _RESPOSTA_OPCOES else 0
                        nova_resp = st.radio("Resposta", _RESPOSTA_OPCOES, index=_idx, horizontal=True,
                                             key=f"risco_{emp_id}_{qid}", label_visibility="collapsed")
                        if nova_resp != resp_atual:
                            st.session_state[risco_key][qid] = nova_resp
                            _risco_upsert(emp_id, qid, nova_resp, st.session_state[risco_obs_key].get(qid))
                            st.rerun()
                        if nova_resp == "Sim":
                            st.markdown(f"<div style='background:#fff5f5;border:1px solid #fc8181;"
                                       f"color:#c53030;border-radius:8px;padding:8px 12px;margin-top:8px;"
                                       f"font-size:13px'>⚠️ <b>Ação recomendada:</b> {acao}</div>",
                                       unsafe_allow_html=True)

                        _obs_atual_r = st.session_state[risco_obs_key].get(qid, "")
                        _nova_obs_r = st.text_area("📝 Observação", value=_obs_atual_r,
                                                   key=f"obsrisco_{emp_id}_{qid}",
                                                   placeholder="Digite aqui uma observação sobre este ponto...")
                        if _nova_obs_r != _obs_atual_r:
                            st.session_state[risco_obs_key][qid] = _nova_obs_r
                            _risco_upsert(emp_id, qid, st.session_state[risco_key].get(qid), _nova_obs_r)

                        st.markdown("**📎 Documentos anexados**")
                        if _docs_r:
                            for _d in _docs_r:
                                _drc1, _drc2, _drc3 = st.columns([4, 1, 1])
                                _drc1.caption(_d.split("__", 1)[-1])
                                _drc2.download_button("⬇️", data=db.docs_baixar(emp_id, f"risco_{qid}", _d),
                                                      file_name=_d.split("__", 1)[-1],
                                                      key=f"dlrisco_{emp_id}_{qid}_{_d}")
                                if _drc3.button("🗑️", key=f"rmrisco_{emp_id}_{qid}_{_d}"):
                                    _docs_remover(emp_id, f"risco_{qid}", _d)
                                    st.rerun()
                        else:
                            st.caption("Nenhum documento anexado ainda.")

                        _upcnt_key_r = f"upcnt_risco_{emp_id}_{qid}"
                        if _upcnt_key_r not in st.session_state:
                            st.session_state[_upcnt_key_r] = 0
                        _novo_doc_r = st.file_uploader(
                            "Anexar documento", key=f"uprisco_{emp_id}_{qid}_{st.session_state[_upcnt_key_r]}",
                            accept_multiple_files=True, label_visibility="collapsed")
                        if _novo_doc_r:
                            for _arq in _novo_doc_r:
                                _docs_salvar(emp_id, f"risco_{qid}", _arq)
                            st.session_state[_upcnt_key_r] += 1
                            st.success(f"{len(_novo_doc_r)} arquivo(s) anexado(s)!")
                            st.rerun()

    # ═══ ABA 2: CHECKLIST OPERACIONAL (documentos por ponto) ═══
    with outer_tabs[1]:
        key_state = f"conf_state_{emp_id}"
        obs_key = f"conf_obs_state_{emp_id}"
        pend_key = f"conf_pend_state_{emp_id}"
        if key_state not in st.session_state:
            _diag_carregado = _diagnostico_carregar(emp_id)
            st.session_state[key_state] = _diag_carregado.get("itens", {})
            st.session_state[obs_key] = _diag_carregado.get("observacoes", {})
            st.session_state[pend_key] = _diag_carregado.get("pendentes", {})

        total_itens, total_ok = 0, 0
        pend = {"critico": [], "alto": [], "medio": []}
        for sec in CONFORMIDADE_SECOES:
            for iid, risco, texto, nota in sec["itens"]:
                total_itens += 1
                if st.session_state[key_state].get(iid):
                    total_ok += 1
                else:
                    pend[risco].append((sec["titulo"], texto))

        pct = round(100 * total_ok / total_itens) if total_itens else 0
        ccx1, ccx2 = st.columns([4, 1])
        with ccx1:
            st.progress(pct/100, text=f"Progresso do checklist — {pct}% ({total_ok}/{total_itens})")
        with ccx2:
            if st.button("💾 Salvar checklist", use_container_width=True):
                for _sec in CONFORMIDADE_SECOES:
                    for _iid, *_ in _sec["itens"]:
                        _diagnostico_upsert(emp_id, _iid, st.session_state[key_state].get(_iid, False),
                                            st.session_state[obs_key].get(_iid),
                                            st.session_state[pend_key].get(_iid, False))
                st.success("Salvo!")

        _n_marcados_pendente = sum(1 for v in st.session_state[pend_key].values() if v)
        m1, m2, m3, m4, m5 = st.columns(5)
        m1.metric("🔴 Crítico pendente", len(pend["critico"]))
        m2.metric("🟠 Alto pendente", len(pend["alto"]))
        m3.metric("🟡 Médio pendente", len(pend["medio"]))
        m4.metric("✅ Verificados", total_ok)
        m5.metric("🟧 Marcados como pendente", _n_marcados_pendente)

        st.divider()

        tabs = st.tabs([f"{s['icone']} {s['id'].upper()}" for s in CONFORMIDADE_SECOES])
        for tab, sec in zip(tabs, CONFORMIDADE_SECOES):
            with tab:
                st.markdown(f"##### {sec['titulo']}")
                st.caption(sec["desc"])
                if sec["alerta"]:
                    _cor, _txt = sec["alerta"]
                    bg, fg, bd = _alert_css[_cor]
                    st.markdown(f"<div style='background:{bg};border:1px solid {bd};color:{fg};"
                               f"border-radius:8px;padding:10px 14px;margin:8px 0;font-size:13px'>"
                               f"⚠️ {_txt}</div>", unsafe_allow_html=True)
                for iid, risco, texto, nota in sec["itens"]:
                    checked = st.session_state[key_state].get(iid, False)
                    pendente_flag = st.session_state[pend_key].get(iid, False)
                    _docs = docs_mapa.get(iid, [])
                    ndocs = len(_docs)
                    if pendente_flag:
                        _icone_ck = "🟧"
                    elif checked:
                        _icone_ck = "✅"
                    else:
                        _icone_ck = "⬜"
                    _icone_doc = f" · 📎{ndocs}" if ndocs else ""
                    with st.expander(f"{_icone_ck} {texto}  ·  {_RISK_LABEL[risco]}{_icone_doc}"):
                        if nota:
                            st.caption(nota)
                        cchk1, cchk2 = st.columns(2)
                        novo_check = cchk1.checkbox("Verificado", value=checked, key=f"chk_{emp_id}_{iid}")
                        novo_pendente = cchk2.checkbox("🟧 Pendente", value=pendente_flag,
                                                       key=f"pend_{emp_id}_{iid}",
                                                       help="Marque quando já foi analisado mas ainda "
                                                            "precisa de ação — fica visível em laranja.")
                        if novo_pendente and not pendente_flag:
                            novo_check = False   # pendente e verificado são mutuamente exclusivos
                        elif novo_check and not checked:
                            novo_pendente = False
                        if novo_check != checked or novo_pendente != pendente_flag:
                            st.session_state[key_state][iid] = novo_check
                            st.session_state[pend_key][iid] = novo_pendente
                            _diagnostico_upsert(emp_id, iid, novo_check,
                                                st.session_state[obs_key].get(iid), novo_pendente)
                            st.rerun()

                        _obs_atual = st.session_state[obs_key].get(iid, "")
                        _nova_obs = st.text_area("📝 Observação", value=_obs_atual, key=f"obs_{emp_id}_{iid}",
                                                 placeholder="Digite aqui uma observação sobre este ponto...")
                        if _nova_obs != _obs_atual:
                            st.session_state[obs_key][iid] = _nova_obs
                            _diagnostico_upsert(emp_id, iid, st.session_state[key_state].get(iid, False),
                                                _nova_obs, st.session_state[pend_key].get(iid, False))

                        st.markdown("**📎 Documentos anexados**")
                        if _docs:
                            for _d in _docs:
                                _dc1, _dc2, _dc3 = st.columns([4, 1, 1])
                                _dc1.caption(_d.split("__", 1)[-1])
                                _dc2.download_button("⬇️", data=db.docs_baixar(emp_id, iid, _d),
                                                     file_name=_d.split("__", 1)[-1],
                                                     key=f"dl_{emp_id}_{iid}_{_d}")
                                if _dc3.button("🗑️", key=f"rm_{emp_id}_{iid}_{_d}"):
                                    _docs_remover(emp_id, iid, _d)
                                    st.rerun()
                        else:
                            st.caption("Nenhum documento anexado ainda.")

                        _upcnt_key = f"upcnt_{emp_id}_{iid}"
                        if _upcnt_key not in st.session_state:
                            st.session_state[_upcnt_key] = 0
                        _novo_doc = st.file_uploader(
                            "Anexar documento", key=f"up_{emp_id}_{iid}_{st.session_state[_upcnt_key]}",
                            accept_multiple_files=True, label_visibility="collapsed")
                        if _novo_doc:
                            for _arq in _novo_doc:
                                _docs_salvar(emp_id, iid, _arq)
                            st.session_state[_upcnt_key] += 1
                            st.success(f"{len(_novo_doc)} arquivo(s) anexado(s)!")
                            st.rerun()

    # ═══ ABA 3: PLANO DE AÇÃO 5W2H ═══
    _PRIORIDADE_OPCOES = ["Altíssima", "Alta", "Média", "Baixa"]
    _STATUS_OPCOES = ["Pendente", "Em andamento", "Concluído"]
    _PRIO_COR = {"Altíssima": "#c53030", "Alta": "#c05621", "Média": "#975a16", "Baixa": "#276749"}
    _STATUS_COR = {"Pendente": "#718096", "Em andamento": "#2a5080", "Concluído": "#276749"}

    with outer_tabs[2]:
        plano_key = f"plano_state_{emp_id}"
        if plano_key not in st.session_state:
            st.session_state[plano_key] = _plano_carregar(emp_id)
        _plano = st.session_state[plano_key]

        st.caption("Ações estruturadas para reduzir os riscos identificados no diagnóstico. Defina "
                  "responsável, prazo, prioridade e acompanhe o status de cada uma.")

        if _plano:
            _total_acoes = len(_plano)
            _concluidas = sum(1 for a in _plano if a.get("status") == "Concluído")
            _andamento = sum(1 for a in _plano if a.get("status") == "Em andamento")
            _pendentes = _total_acoes - _concluidas - _andamento
            _pct_plano = round(100 * _concluidas / _total_acoes) if _total_acoes else 0
            st.progress(_pct_plano / 100, text=f"{_concluidas}/{_total_acoes} ações concluídas ({_pct_plano}%)")
            pm1, pm2, pm3 = st.columns(3)
            pm1.metric("⏳ Pendentes", _pendentes)
            pm2.metric("🔄 Em andamento", _andamento)
            pm3.metric("✅ Concluídas", _concluidas)

        pbtn1, pbtn2 = st.columns(2)
        with pbtn1:
            if not _plano:
                if st.button("📥 Carregar modelo padrão (10 ações)", key=f"modelo_5w2h_{emp_id}",
                            use_container_width=True):
                    db.plano_inserir_lote(emp_id, PLANO_5W2H_MODELO)
                    st.session_state[plano_key] = _plano_carregar(emp_id)
                    st.rerun()
        with pbtn2:
            if _plano:
                if st.button("🗑️ Limpar plano", key=f"limpar_5w2h_{emp_id}", use_container_width=True):
                    db.plano_limpar(emp_id)
                    st.session_state[plano_key] = []
                    st.rerun()

        st.divider()

        with st.expander("➕ Adicionar nova ação", expanded=not _plano):
            with st.form(f"form_nova_acao_{emp_id}", clear_on_submit=True):
                novo_oque = st.text_input("O quê *")
                fc1, fc2 = st.columns(2)
                novo_porque = fc1.text_area("Por quê", height=80)
                novo_como = fc2.text_area("Como", height=80)
                fc3, fc4, fc5 = st.columns(3)
                novo_onde = fc3.text_input("Onde")
                novo_quando = fc4.text_input("Quando")
                novo_quem = fc5.text_input("Quem")
                fc6, fc7 = st.columns(2)
                novo_custo = fc6.text_input("Quanto custa")
                nova_prioridade = fc7.selectbox("Prioridade", _PRIORIDADE_OPCOES)
                if st.form_submit_button("Adicionar ação", type="primary", use_container_width=True):
                    if novo_oque.strip():
                        db.plano_inserir(emp_id, {
                            "o_que": novo_oque.strip(), "por_que": novo_porque.strip(),
                            "onde": novo_onde.strip(), "quando": novo_quando.strip(),
                            "quem": novo_quem.strip(), "como": novo_como.strip(),
                            "quanto_custa": novo_custo.strip(), "prioridade": nova_prioridade,
                            "status": "Pendente",
                        })
                        st.session_state[plano_key] = _plano_carregar(emp_id)
                        st.rerun()
                    else:
                        st.error("Preencha ao menos o campo 'O quê'.")

        if not _plano:
            st.info("Nenhuma ação cadastrada ainda. Use o formulário acima ou carregue o modelo padrão.")

        for acao in _plano:
            _acao_id = acao["id"]
            with st.container(border=True):
                top1, top2, top3 = st.columns([5, 3, 1])
                with top1:
                    st.markdown(f"**{acao.get('o_que') or '(sem título)'}**")
                with top2:
                    _pcor = _PRIO_COR.get(acao.get("prioridade"), "#718096")
                    _scor = _STATUS_COR.get(acao.get("status"), "#718096")
                    st.markdown(
                        f"<span style='font-size:10px;font-weight:800;padding:2px 8px;border-radius:99px;"
                        f"background:{_pcor}22;color:{_pcor};border:1px solid {_pcor}55;margin-right:4px'>"
                        f"{acao.get('prioridade','—')}</span>"
                        f"<span style='font-size:10px;font-weight:800;padding:2px 8px;border-radius:99px;"
                        f"background:{_scor}22;color:{_scor};border:1px solid {_scor}55'>"
                        f"{acao.get('status','Pendente')}</span>", unsafe_allow_html=True)
                with top3:
                    if st.button("🗑️", key=f"del_acao_{emp_id}_{_acao_id}"):
                        db.plano_remover(_acao_id)
                        st.session_state[plano_key] = _plano_carregar(emp_id)
                        st.rerun()

                if acao.get("por_que"):
                    st.caption(f"**Por quê:** {acao['por_que']}")
                _meta = []
                if acao.get("onde"): _meta.append(f"📍 {acao['onde']}")
                if acao.get("quando"): _meta.append(f"🗓️ {acao['quando']}")
                if acao.get("quem"): _meta.append(f"👤 {acao['quem']}")
                if acao.get("quanto_custa"): _meta.append(f"💰 {acao['quanto_custa']}")
                if _meta:
                    st.caption("  ·  ".join(_meta))
                if acao.get("como"):
                    st.markdown(f"<div style='font-size:13px;color:#4a5568;margin-top:4px'>"
                               f"{acao['como']}</div>", unsafe_allow_html=True)

                with st.expander("✏️ Editar / mudar status"):
                    with st.form(f"form_edit_acao_{emp_id}_{_acao_id}"):
                        e_oque = st.text_input("O quê", value=acao.get("o_que", ""))
                        ec1, ec2 = st.columns(2)
                        e_porque = ec1.text_area("Por quê", value=acao.get("por_que", ""), height=80)
                        e_como = ec2.text_area("Como", value=acao.get("como", ""), height=80)
                        ec3, ec4, ec5 = st.columns(3)
                        e_onde = ec3.text_input("Onde", value=acao.get("onde", ""))
                        e_quando = ec4.text_input("Quando", value=acao.get("quando", ""))
                        e_quem = ec5.text_input("Quem", value=acao.get("quem", ""))
                        ec6, ec7, ec8 = st.columns(3)
                        e_custo = ec6.text_input("Quanto custa", value=acao.get("quanto_custa", ""))
                        _prio_idx = _PRIORIDADE_OPCOES.index(acao.get("prioridade")) \
                            if acao.get("prioridade") in _PRIORIDADE_OPCOES else 2
                        e_prio = ec7.selectbox("Prioridade", _PRIORIDADE_OPCOES, index=_prio_idx)
                        _status_idx = _STATUS_OPCOES.index(acao.get("status")) \
                            if acao.get("status") in _STATUS_OPCOES else 0
                        e_status = ec8.selectbox("Status", _STATUS_OPCOES, index=_status_idx)
                        if st.form_submit_button("💾 Salvar alterações", type="primary", use_container_width=True):
                            db.plano_atualizar(_acao_id, {
                                "o_que": e_oque.strip(), "por_que": e_porque.strip(), "onde": e_onde.strip(),
                                "quando": e_quando.strip(), "quem": e_quem.strip(), "como": e_como.strip(),
                                "quanto_custa": e_custo.strip(), "prioridade": e_prio, "status": e_status,
                            })
                            st.session_state[plano_key] = _plano_carregar(emp_id)
                            st.success("Ação atualizada!")
                            st.rerun()

    # ═══ ABA 4: SIMULAÇÕES & ANÁLISES (sempre vinculadas a esta empresa) ═══
    with outer_tabs[3]:
        st.caption("Abra o Simulador ou a Análise de Folha — são exatamente os mesmos do menu "
                  "principal, com a diferença de que, vindo por aqui, ficam vinculados a "
                  "**esta empresa** e você pode salvá-los no histórico abaixo. Pelo menu "
                  "principal continuam avulsos — nada lá é salvo.")

        nv1, nv2 = st.columns(2)
        with nv1:
            if st.button("🎯 Abrir Simulador PGDAS (vinculado a esta empresa)",
                        key=f"ir_sim_{emp_id}", type="primary", use_container_width=True):
                st.session_state.vinculo_empresa_id = emp_id
                st.session_state.vinculo_empresa_nome = empresa["razao_social"]
                st.session_state.modo = "simulador"
                st.rerun()
        with nv2:
            if st.button("📈 Abrir Análise de Folha (vinculada a esta empresa)",
                        key=f"ir_an_{emp_id}", use_container_width=True):
                st.session_state.vinculo_empresa_id = emp_id
                st.session_state.vinculo_empresa_nome = empresa["razao_social"]
                st.session_state.modo = "analise"
                st.rerun()

        st.divider()
        st.markdown("##### 🗂️ Histórico desta empresa")
        _hist_sims = db.simulacoes_listar(emp_id)
        _hist_ans = db.analises_listar(emp_id)
        if not _hist_sims and not _hist_ans:
            st.caption("Nenhuma simulação ou análise salva ainda.")
        else:
            if _hist_sims:
                st.markdown("**Simulações PGDAS**")
                for s in _hist_sims:
                    hs1, hs2, hs3 = st.columns([3, 2, 1])
                    hs1.write(f"{s.get('competencia') or '—'} — Nota: {brl(s.get('nota_a_emitir') or 0)}")
                    _hs_cap = f"DAS: {brl(s.get('das_estimado') or 0)}"
                    if s.get("cpp_estimado"):
                        _hs_cap += f" · CPP: {brl(s['cpp_estimado'])}"
                    hs2.caption(_hs_cap)
                    if hs3.button("🗑️", key=f"del_sim_{s['id']}"):
                        db.simulacao_remover(s["id"])
                        st.rerun()
            if _hist_ans:
                st.markdown("**Análises de Folha**")
                for a in _hist_ans:
                    ha1, ha2, ha3, ha4 = st.columns([3, 2, 1, 1])
                    _r = a.get("resumo") or {}
                    ha1.write(f"{a.get('competencia_inicio') or '—'} a {a.get('competencia_fim') or '—'} "
                             f"— {_r.get('headcount', '—')} func.")
                    ha2.caption(f"Remuneração: {brl(_r.get('remuneracao_total') or 0)}")
                    if a.get("arquivo_origem_path"):
                        ha3.download_button("⬇️", data=db.analise_baixar_arquivo(a["arquivo_origem_path"]),
                                           file_name=a["arquivo_origem_path"].split("/")[-1],
                                           key=f"dl_an_{a['id']}")
                    if ha4.button("🗑️", key=f"del_an_{a['id']}"):
                        db.analise_remover(a["id"], a.get("arquivo_origem_path"))
                        st.rerun()

    st.divider()
    st.markdown("<div style='background:rgba(0,0,0,.03);border-radius:10px;padding:14px 18px;"
                "margin-top:16px;font-size:12px;color:#718096;line-height:1.7'>"
                "<b>Nota legal e ética:</b> ferramenta de orientação interna. Nenhuma resposta \"verificado\" "
                "ou \"não\" equivale a \"sem risco\" ou \"aprovado\". Toda análise exige validação por "
                "responsável jurídico habilitado e responsável tributário com CRC. A cessão/locação de mão "
                "de obra é, como regra, impeditiva ao Simples Nacional (LC 123/2006). A Lei 6.019/1974 exige "
                "que a prestadora execute serviços determinados e específicos, sendo responsável pela "
                "contratação, remuneração e direção dos trabalhadores.</div>", unsafe_allow_html=True)

# ── orquestrador ──────────────────────────────────────────────────────────────
def render_conformidade():
    if "conf_empresa_id" not in st.session_state:
        st.session_state.conf_empresa_id = None

    if st.session_state.conf_empresa_id:
        empresas = _empresas_carregar()
        empresa = next((e for e in empresas if e["id"] == st.session_state.conf_empresa_id), None)
        if empresa is None:
            st.session_state.conf_empresa_id = None
            st.rerun()
        render_empresa_ficha(empresa)
    else:
        render_empresas_lista()

def render_simulador(meses, fgtsdf):
    def _step(n, title, desc=""):
        _d = f"<br><span style='font-size:12px;opacity:.75'>{desc}</span>" if desc else ""
        st.markdown(
            f"<p style='display:flex;align-items:center;gap:12px;margin:20px 0 4px;padding:0'>"
            f"<span style='min-width:30px;height:30px;border-radius:50%;"
            f"background:linear-gradient(135deg,#16304f,#2e6da4);color:#fff;"
            f"font-weight:800;font-size:13px;display:inline-flex;align-items:center;"
            f"justify-content:center;flex-shrink:0;box-shadow:0 2px 8px rgba(22,48,79,.25)'>{n}</span>"
            f"<span><strong style='font-size:11px;letter-spacing:.06em;text-transform:uppercase;opacity:.6'>"
            f"{title}</strong>{_d}</span></p>",
            unsafe_allow_html=True)

    _vinculo_id = st.session_state.get("vinculo_empresa_id")
    _vinculo_nome = st.session_state.get("vinculo_empresa_nome")
    if _vinculo_id:
        vhc1, vhc2 = st.columns([4, 1])
        with vhc1:
            st.markdown(f"<div style='background:#eef4fb;border:1px solid #b8d4ea;border-radius:8px;"
                       f"padding:8px 14px;margin-bottom:10px;font-size:13px'>"
                       f"📌 Esta simulação está <b>vinculada a {_vinculo_nome}</b> — role até o final "
                       f"para salvar no histórico dessa empresa.</div>", unsafe_allow_html=True)
        with vhc2:
            if st.button("⬅️ Voltar à ficha", key="sim_voltar_ficha", use_container_width=True):
                st.session_state.modo = "conformidade"
                st.session_state.conf_empresa_id = _vinculo_id
                st.session_state.vinculo_empresa_id = None
                st.rerun()

    # ── PASSO 1 — MÊS ─────────────────────────────────────────────────────────
    _step(1, "Qual mês você está simulando?")
    _sem_xml_meses = not meses
    if _sem_xml_meses:
        import datetime
        _hoje = datetime.date.today()
        _mes_txt = st.text_input("Competência (AAAA-MM)",
                                 value=f"{_hoje.year}-{_hoje.month-1:02d}",
                                 placeholder="Ex.: 2026-06", key="sim_mes_manual",
                                 help="Formato: ANO-MÊS. Ex.: 2026-06 para junho/2026")
        mes = _mes_txt.strip() if re.match(r"^\d{4}-\d{2}$", _mes_txt.strip()) else None
        if not mes:
            st.info("Informe a competência no formato AAAA-MM (ex.: 2026-06).")
            return
    else:
        mes = st.selectbox("Competência", meses, index=len(meses)-1,
                           format_func=lambda p: fper(p, True), key="sim_mes")

    # ── PASSO 2 — FOLHA (XML ou manual) ───────────────────────────────────────
    gg = fgtsdf[fgtsdf["per_apur"] == mes] if (not fgtsdf.empty and not _sem_xml_meses) else pd.DataFrame()
    sal_xml = gg["base_fgts"].sum() if not gg.empty else 0
    fg_xml = gg["deposito_fgts"].sum() if not gg.empty else 0
    _tem_xml = (not _sem_xml_meses) and (sal_xml > 0 or fg_xml > 0)

    _step(2, "Valores da folha",
          "Do XML (automático) ou digitado em caso de emergência.")

    if _tem_xml:
        st.markdown(f"<div class='al-g'>✅ XML encontrado — <b>Salários {brl(sal_xml)}</b> · "
                    f"<b>FGTS {brl(fg_xml)}</b></div>", unsafe_allow_html=True)
        _usar_manual = st.checkbox("✏️ Substituir pelos valores digitados manualmente",
                                   value=False, key=f"sim_manual_{mes}")
    else:
        if not _sem_xml_meses:
            st.markdown(f"<div class='al-r'>⚠️ Sem folha (S-5003) no XML para {fper(mes, True)}.</div>",
                        unsafe_allow_html=True)
        _usar_manual = True

    if _usar_manual:
        st.markdown("<div class='card-manual'>", unsafe_allow_html=True)
        _mc1, _mc2 = st.columns(2)
        _sal_txt = _mc1.text_input("Salários — base FGTS (R$)", placeholder="Ex.: 175.000,00",
                                   key=f"sim_sal_{mes}",
                                   help="Total da folha que serve de base para o FGTS (S-5003)")
        _fg_txt = _mc2.text_input("FGTS (R$)", placeholder="Ex.: 13.846,00",
                                  key=f"sim_fg_{mes}", help="8% sobre os salários")
        st.markdown("</div>", unsafe_allow_html=True)
        sal = parse_brl_in(_sal_txt)
        fg = parse_brl_in(_fg_txt)
        _obs_sal = "digitado manualmente"
        _obs_fg = "digitado manualmente"
        if sal <= 0 and fg <= 0:
            st.info("⬆️ Digite os valores acima para ver o resultado.")
            return
    else:
        sal, fg = sal_xml, fg_xml
        _obs_sal = "XML (S-5003)"
        _obs_fg = "XML (S-5003)"

    # ── PASSO 3 — PGDAS ANTERIOR (alíquota) ───────────────────────────────────
    _ant = _mes_anterior(mes)
    _step(3, f"PGDAS de {fper(_ant, True) if _ant else 'mês anterior'} (opcional)",
          "Anexe o PDF para preencher a alíquota automaticamente.")
    _pg_ant = st.file_uploader("PGDAS anterior (PDF)", type=["pdf"],
                               accept_multiple_files=False, key="pgdas_sim",
                               label_visibility="collapsed")
    if _pg_ant is not None:
        import pgdas as _pg
        _r = _pg.extrair(_pg_ant)
        _okc, _msgc = pgdas_confere_cnpj(_r) if _r else (None, "")
        if _okc is False:
            st.markdown(f"<div class='al-r'>{_msgc}</div>", unsafe_allow_html=True)
        elif _r and _r.get("aliq_efetiva"):
            st.session_state["sim_aliq"] = _r["aliq_efetiva"]
            st.session_state["sim_anexo"] = _r.get("anexo", "")
            if _r.get("das_total"):
                st.session_state["sim_cpp_share"] = (_r.get("cpp") or 0) / _r["das_total"]
            if _r.get("cpp_ratio"):
                st.session_state["cpp_ratio_ref"] = _r["cpp_ratio"]
            if _r.get("segmentos"):
                st.session_state["sim_segmentos"] = _r["segmentos"]
            if _r.get("rbt12"):
                st.session_state["sim_rbt12"] = _r["rbt12"]
            if _r.get("nome"):
                st.session_state["empresa_pgdas"] = _r["nome"]
            _av = "" if _r.get("competencia") == _ant else " · <b>atenção: não é o mês anterior</b>"
            st.markdown(
                (f"<div class='al-g'>✅ PGDAS lido — Anexo <b>{_r.get('anexo') or '?'}</b> · "
                 f"alíquota <b>{_r['aliq_efetiva']:.2f}%</b> · CPP = "
                 f"<b>{(_r.get('cpp') or 0)/_r['das_total']*100:.0f}%</b> do DAS"
                 f"{_av}</div>").replace(".", ",", 1), unsafe_allow_html=True)
        else:
            st.warning("Não consegui ler a alíquota nesse PDF. Informe manualmente abaixo.")

    _aliq_auto = st.session_state.get("sim_aliq")
    _anexo_det = st.session_state.get("sim_anexo", "")
    _cpp_share = st.session_state.get("sim_cpp_share")

    # ── PASSO 4 — PARÂMETROS ──────────────────────────────────────────────────
    _step(4, "Parâmetros do cálculo")
    sc1, sc2, sc3 = st.columns(3)
    aliq = sc1.number_input("Alíquota DAS (%)", min_value=0.0, max_value=30.0,
        value=round(_aliq_auto, 2) if _aliq_auto else 11.0, step=0.1,
        help=("Vem do PGDAS anterior automaticamente. "
              "Se o faturamento cresceu, suba um pouco — o RBT12 maior eleva a alíquota."))
    margem = sc2.number_input("Margem (%)", min_value=0.0, max_value=50.0,
        value=10.0, step=1.0,
        help="Folga para lucro e imprevistos. Evita faturar 'no osso'.")
    _desp_txt = sc3.text_input("Despesas gerais (R$)", value="",
        placeholder="Ex.: 8.000,00",
        help="Aluguel, contador, água, luz. Mantém a estrutura coerente para o Fisco.")
    desp_ger = parse_brl_in(_desp_txt)
    if _aliq_auto:
        st.caption(f"Alíquota do PGDAS anterior: **{str(_aliq_auto).replace('.',',')}%** · "
                   f"Anexo **{_anexo_det}**" if _anexo_det else
                   f"Alíquota do PGDAS anterior: **{str(_aliq_auto).replace('.',',')}%**")

    _div = 1 - aliq/100 - margem/100
    if _div <= 0:
        st.warning("Alíquota + margem somam 100% ou mais — ajuste os valores.")
        return

    # ── CÁLCULO BASE ──────────────────────────────────────────────────────────
    import simples as _sn
    custo_fora = sal + fg + desp_ger
    nota = custo_fora / _div
    sobra = nota * (margem/100)
    _seg = st.session_state.get("sim_segmentos")
    _rbt12 = st.session_state.get("sim_rbt12")
    _store = "sim_dist_vals"

    # ── DISTRIBUIÇÃO PRIMEIRO (roda o editor, atualiza session_state) ─────────
    _das_resumo = nota * aliq/100
    _cpp_resumo = _das_resumo * _cpp_share if _cpp_share else None
    _tem_iv = False

    if _seg:
        _cats = list(_seg.keys())
        _tot_ref = sum(v["receita"] for v in _seg.values()) or 1
        _seed_now = {c: round(nota * _seg[c]["receita"]/_tot_ref, 2) for c in _cats}
        st.session_state.setdefault(_store, {})
        if (not st.session_state[_store]) or set(st.session_state[_store]) != set(_cats):
            st.session_state[_store] = dict(_seed_now)

        st.markdown(f"##### 🧾 Distribuição da nota de {brl(nota)} no PGDAS")
        st.markdown(
            "<div class='al-b'>📋 <b>Esses valores são o que você vai digitar no PGDAS</b> da Receita Federal. "
            "Serviços (Anexo III) geram CPP maior (~43%) que Revenda (Anexo I, ~41%). "
            "O resultado abaixo atualiza conforme você edita.</div>", unsafe_allow_html=True)
        if st.button("🔄 Redistribuir pelo mix do PGDAS", key="sim_dist_reset"):
            st.session_state[_store] = dict(_seed_now)
            st.session_state["sim_dist_ed_ver"] = st.session_state.get("sim_dist_ed_ver", 0) + 1
            st.rerun()
        editor_faturamento(_cats, "sim_dist_ed", store=_store,
                           coluna="✏️ Valor a lançar (R$) — clique p/ editar",
                           label_col="Tipo de receita", label_fn=lambda c: c)
        _tot_val = sum(float(st.session_state[_store].get(c, 0) or 0) for c in _cats)
        _dif = round(nota - _tot_val, 2)
        sk = st.columns(3)
        kpi(sk[0], brl(nota), "Nota alvo")
        kpi(sk[1], brl(_tot_val), "Distribuído")
        if abs(_dif) <= 0.5:
            kpi(sk[2], "R$ 0,00", "Falta distribuir", "fechou ✓", "up")
        elif _dif > 0:
            kpi(sk[2], brl(_dif), "Falta distribuir", "coloque em alguma parte", "n")
        else:
            kpi(sk[2], brl(-_dif), "Passou da nota", "reduza em alguma parte", "down")

        # tabela com CPP por tipo — calcula os totais reais aqui
        drows = []; _das_resumo = 0.0; _cpp_resumo = 0.0
        for c in _cats:
            val = float(st.session_state[_store].get(c, 0) or 0)
            anexo = _seg[c].get("anexo") or _sn.anexo_de_categoria(c)
            if anexo == "IV": _tem_iv = True
            ae_r = _sn.aliquota_efetiva(_rbt12, anexo) if _rbt12 else None
            das_c = val * ae_r[0] if ae_r else val * (aliq/100)
            cpp_c = _sn.cpp(val, _rbt12, anexo) if _rbt12 else \
                    (val * (_seg[c]["cpp"]/_seg[c]["receita"]) if _seg[c]["receita"] else 0)
            _das_resumo += das_c
            _cpp_resumo += (cpp_c or 0)
            drows.append({"Tipo de receita": c, "Anexo": anexo,
                          "Valor a lançar": val, "CPP gerado": cpp_c or 0})
        drows.append({"Tipo de receita": "TOTAL", "Anexo": "",
                      "Valor a lançar": _tot_val, "CPP gerado": _cpp_resumo})
        st.dataframe(fmt_df(pd.DataFrame(drows), money=["Valor a lançar", "CPP gerado"]),
                     use_container_width=True, hide_index=True)
        if abs(_dif) > 0.5:
            st.markdown((f"<div class='al-y'>⚠️ Ainda não fecha: "
                         f"{'faltam' if _dif>0 else 'passou em'} <b>{brl(abs(_dif))}</b>. "
                         "Ajuste até 'Falta distribuir' zerar.</div>"), unsafe_allow_html=True)
        else:
            st.markdown(f"<div class='al-g'>✅ Fecha na nota (<b>{brl(_tot_val)}</b>) · "
                        f"CPP total <b>{brl(_cpp_resumo)}</b>.</div>", unsafe_allow_html=True)
        if _tem_iv:
            st.markdown(
                "<div class='al-r'>⚠️ <b>Há receita no Anexo IV</b> (ex.: construção, limpeza, "
                "vigilância, cessão de mão de obra). Nele o <b>CPP não está no DAS</b> — é recolhido "
                "à parte, ~20% sobre a folha (via GPS/DCTFWeb). O CPP dessas partes aparece como R$ 0 "
                "aqui, mas o INSS patronal <b>existe e é pago por fora</b> — e isso costuma "
                "<b>anular a vantagem</b> da estrutura de mão de obra no Simples.</div>",
                unsafe_allow_html=True)

    # ── RESUMO FINAL (depois da distribuição — valores sempre atualizados) ─────
    st.divider()
    # garante que DAS nunca fica zero: fallback na alíquota manual se a distribuição zerou
    if not _das_resumo:
        _das_resumo = nota * aliq/100
    if not _cpp_resumo and _cpp_share:
        _cpp_resumo = _das_resumo * _cpp_share
    _fonte = "pela distribuição" if _seg else f"estimado ({aliq:.1f}% da nota)".replace(".",",")
    _das_label = brl(_das_resumo)

    st.markdown(f"""<div class='nota-destaque'>
      <div class='label'>Nota a emitir — {fper(mes, True)}</div>
      <div class='valor'>{brl(nota)}</div>
      <div class='sub'>DAS {_fonte}: {_das_label}
        {f" · CPP (dentro do DAS): {brl(_cpp_resumo)}" if _cpp_resumo else " · Anexe o PGDAS p/ ver a CPP"}
      </div></div>""", unsafe_allow_html=True)

    kk = st.columns(3)
    kpi(kk[0], brl(nota),    "NOTA A EMITIR", f"lançar no PGDAS de {fper(mes, True)}", "n")
    kpi(kk[1], _das_label,   "DAS estimado",  _fonte, "n")
    kpi(kk[2], brl(_cpp_resumo) if _cpp_resumo else "—", "CPP (dentro do DAS)",
        "anexe o PGDAS p/ ver" if not _cpp_resumo else "ja incluida no DAS", "n")

    if _vinculo_id:
        if st.button(f"💾 Salvar esta simulação no histórico de {_vinculo_nome}",
                    key=f"salvar_sim_vinculo_{mes}", type="primary", use_container_width=True):
            db.simulacao_salvar(_vinculo_id, {
                "competencia": mes, "folha_bruta": sal, "fgts": fg,
                "margem_seguranca": margem, "despesas_gerais": desp_ger,
                "nota_a_emitir": round(nota, 2), "das_estimado": round(_das_resumo, 2),
                "cpp_estimado": round(_cpp_resumo, 2) if _cpp_resumo else None,
                "aliquota_efetiva": aliq,
                "distribuicao": st.session_state.get(_store) if _seg else None,
            })
            st.success(f"✅ Simulação salva no histórico de {_vinculo_nome}!")

    # ── CONFIRMAR ─────────────────────────────────────────────────────────────
    _cpp_confirmar = _cpp_resumo
    st.markdown(f"**Gostou do resultado?** Confirme para salvar a nota de **{brl(nota)}** "
                f"como faturamento de {fper(mes, True)} na Análise de Folha.")
    if st.button(f"✅ Confirmar e salvar {fper(mes, True)}", key="sim_confirma",
                 type="primary", use_container_width=True):
        st.session_state.setdefault("fat_por_comp", {})[mes] = round(nota, 2)
        st.session_state.setdefault("cpp_estimado_set", set())
        if _cpp_confirmar is not None:
            st.session_state.setdefault("cpp_por_comp", {})[mes] = round(_cpp_confirmar, 2)
            st.session_state["cpp_estimado_set"].add(mes)
        st.success(
            f"✅ **{fper(mes, True)} salvo** — nota {brl(nota)}" +
            (f" · CPP estimado {brl(_cpp_confirmar)}" if _cpp_confirmar else "") +
            ". O PGDAS real deste mês (quando anexado) substitui o CPP estimado.")

    # ── 5) COMO FICA A CPP (a dúvida do analista) ─────────────────────────────
    if _cpp_resumo:
        st.markdown(
            f"<div class='al-b'>🔎 <b>E a CPP, que não veio no XML?</b> Ela é paga <b>dentro do DAS</b> "
            f"desta nota. Emitindo <b>{brl(nota)}</b>, o DAS fica em ~<b>{brl(_das_resumo)}</b>, e a fatia de "
            f"CPP dele é ~<b>{brl(_cpp_resumo)}</b> — é o INSS patronal do Simples, recolhido via "
            "DAS, não em guia separada.</div>", unsafe_allow_html=True)
    else:
        st.markdown(
            "<div class='al-y'>🔎 <b>E a CPP?</b> No Simples (Anexo III) ela é paga <b>dentro do DAS</b> "
            "da nota — não vem no XML nem é guia separada. Anexe o PGDAS anterior acima para o app mostrar "
            "quanto do DAS é CPP.</div>", unsafe_allow_html=True)

    # ── 6) VALE A PENA? Simples × Lucro Presumido (para o mês) ────────────────
    with st.expander("⚖️ Vale a pena? Folha no Simples (mão de obra) × na empresa que vende (Lucro Presumido)"):
        st.caption("Custo TRIBUTÁRIO de manter a folha deste mês no Simples (DAS sobre a nota) "
                   "versus na empresa que vende (Lucro Presumido — INSS patronal sobre a remuneração).")
        _aliq_pres = st.number_input("INSS patronal no Lucro Presumido (%)",
            min_value=0.0, max_value=40.0, value=27.8, step=0.1,
            help="CPP 20% + RAT/FAP (1–3%) + Terceiros 5,8%. Padrão ~27,8%.")
        _inss_pres = sal * _aliq_pres/100
        _economia = _inss_pres - _das_resumo
        cmp = pd.DataFrame([
            {"Cenário": "A) Folha no Simples (mão de obra)", "Imposto sobre a folha": _das_resumo,
             "Base": "DAS sobre a nota"},
            {"Cenário": "B) Folha no Lucro Presumido", "Imposto sobre a folha": _inss_pres,
             "Base": f"{_aliq_pres:.1f}% da remuneração".replace(".", ",")},
        ])
        st.dataframe(fmt_df(cmp, money=["Imposto sobre a folha"]),
                     use_container_width=True, hide_index=True)
        if _economia > 0:
            st.markdown(f"<div class='al-g'>✅ <b>Vale a pena no Simples.</b> Economia de "
                        f"<b>{brl(_economia)}</b> no mês (~<b>{brl(_economia*12)}/ano</b>) só em "
                        "imposto sobre a folha.</div>", unsafe_allow_html=True)
        else:
            st.markdown(f"<div class='al-r'>❌ <b>Não compensa.</b> No Simples custa "
                        f"<b>{brl(-_economia)}</b> a mais no mês que deixar no Presumido.</div>",
                        unsafe_allow_html=True)
        st.markdown(
            "<div class='al-y'>⚠️ Só vale no <b>Anexo III</b> (CPP no DAS). No <b>Anexo IV</b> "
            "(cessão de mão de obra) a CPP é paga à parte (20%+) e o benefício some. A empresa "
            "precisa de <b>substância real</b> (estrutura, despesas, contrato) para o Fisco não "
            "descaracterizar.</div>", unsafe_allow_html=True)


# ── HUB — escolha do caminho ──────────────────────────────────────────────────
_modo = st.session_state.get("modo")
if _modo is None:
    st.markdown("<div class='hero'><h1>📋 O que você quer fazer?</h1>"
                "<p>Escolha por onde começar. O normal é simular primeiro (achar a nota e fazer o "
                "PGDAS) e depois analisar a folha. Os arquivos anexados servem para os dois.</p></div>",
                unsafe_allow_html=True)
    hc1, hc2, hc3 = st.columns(3)
    with hc1:
        st.markdown("<div class='box'><h3>🎯 Simulador PGDAS</h3>"
                    "<p style='font-size:13px;color:#48535f'>Descubra <b>quanto de nota emitir</b> "
                    "para sustentar a folha, com o DAS e o CPP por tipo de receita. Use o XML + o "
                    "PGDAS anterior (para a alíquota). Ideal <b>antes</b> de fazer o PGDAS do mês.</p></div>",
                    unsafe_allow_html=True)
        if st.button("🎯 Abrir Simulador PGDAS", type="primary", use_container_width=True):
            st.session_state.modo = "simulador"; st.rerun()
    with hc2:
        st.markdown("<div class='box'><h3>📊 Análise de Folha</h3>"
                    "<p style='font-size:13px;color:#48535f'>Painel completo da folha a partir do "
                    "XML: custo real, encargos, gastos por mês, faturamento × folha, movimentação, "
                    "conferência e relatório. Anexe o PGDAS (atual) para incluir o CPP.</p></div>",
                    unsafe_allow_html=True)
        if st.button("📊 Abrir Análise de Folha", use_container_width=True):
            st.session_state.modo = "analise"; st.rerun()
    with hc3:
        st.markdown("<div class='box'><h3>🛡️ Conformidade</h3>"
                    "<p style='font-size:13px;color:#48535f'>Checklist de risco para clientes que "
                    "possuem (ou vão abrir) uma <b>segunda empresa prestadora</b> com empregados. "
                    "Mapeia áreas críticas e guarda o diagnóstico do cliente.</p></div>",
                    unsafe_allow_html=True)
        if st.button("🛡️ Abrir Conformidade", use_container_width=True):
            st.session_state.modo = "conformidade"; st.rerun()
    st.stop()

# ── MODO SIMULADOR (pré-análise) ──────────────────────────────────────────────
if _modo == "simulador":
    # só competências COMPLETAS: holerite (S-1200) + totalizador (S-5001/S-5003) + líquido (S-1210)
    _srem = set(D["remuneracao"]["per_apur"].dropna().unique()) if not D["remuneracao"].empty else set()
    _sinss = set(D["bases_inss"]["per_apur"].dropna().unique()) if not D["bases_inss"].empty else set()
    _sfgts = set(D["bases_fgts"]["per_apur"].dropna().unique()) if not D["bases_fgts"].empty else set()
    _spag = set(D["pagamentos"]["per_apur"].dropna().unique()) if not D["pagamentos"].empty else set()
    _todos_comp = sorted(_srem | _sinss | _sfgts | _spag)
    _comp_fat = sorted(p for p in _todos_comp
                       if p in _srem and (p in _sinss or p in _sfgts) and p in _spag)
    _parciais = [p for p in _todos_comp if p not in _comp_fat]
    st.markdown("<div class='hero'><h1>🎯 Simulação e Faturamento <span style='font-size:15px;opacity:.8'>(antes da análise)</span></h1>"
                "<p>Fluxo: <b>1)</b> simule a nota a emitir a partir da folha · <b>2)</b> gere o PGDAS com esse "
                "valor · <b>3)</b> anexe o PGDAS (ou digite o faturamento) · <b>4)</b> abra o painel. "
                "Tudo opcional — pode pular e ver o painel sem esses dados.</p></div>", unsafe_allow_html=True)
    if "fat_por_comp" not in st.session_state:
        st.session_state.fat_por_comp = {}
    if "cpp_por_comp" not in st.session_state:
        st.session_state.cpp_por_comp = {}
    if "das_por_comp" not in st.session_state:
        st.session_state.das_por_comp = {}

    # ── 1) SIMULADOR (descobrir a nota a emitir, antes do PGDAS) ─────────────
    _fg_norm = D["bases_fgts"].copy()
    if not _fg_norm.empty:
        _fg_norm["base_fgts"] = pd.to_numeric(_fg_norm["base_fgts"], errors="coerce").fillna(0)
        _fg_norm["deposito_fgts"] = pd.to_numeric(_fg_norm["deposito_fgts"], errors="coerce").fillna(0)
    if _parciais:
        st.markdown(
            f"<div class='al-y'>ℹ️ Só aparecem meses com <b>folha completa</b> (holerite + "
            f"totalizadores + líquido). Ficaram de fora por estarem incompletos: "
            f"<b>{', '.join(fper(p, True) for p in _parciais)}</b> — o pacote traz só pedaços deles "
            "(o pacote de um mês carrega a folha completa do mês anterior).</div>",
            unsafe_allow_html=True)
    with st.expander("🎯 Passo 1 — Simular a nota a emitir (antes de fazer o PGDAS)",
                     expanded=True):
        render_simulador(_comp_fat, _fg_norm)
    st.divider()

    # ── 2) FATURAMENTO / PGDAS (depois de simular e fazer o PGDAS) ───────────
    st.markdown("### 📥 Passo 2 — Informe o faturamento / anexe o PGDAS")
    st.caption("Depois de simular e gerar o PGDAS, volte aqui: anexe o PGDAS (extrai CPP e receita) "
               "ou digite o valor da nota que você encontrou na simulação. Pode pular se ainda não tiver.")

    # ── PGDAS (Simples): extrai CPP + receita do PDF ─────────────────────────
    st.markdown("##### 🧾 Empresa do Simples Nacional? Anexe o(s) PGDAS-D (opcional)")
    st.caption("No Simples, o INSS patronal (CPP) é pago no DAS e não vem no eSocial. "
               "Anexe o PDF do PGDAS-D de cada mês — o app extrai o CPP (e a receita) para "
               "compor o custo total. Você confere os valores antes de aplicar.")
    _pgs = st.file_uploader("PGDAS-D (PDF) — pode anexar vários meses", type=["pdf"],
                            accept_multiple_files=True, key="pgdas_up")
    if _pgs:
        import pgdas as _pg
        _achados = []
        _cnpj_alerta = False
        for _f in _pgs:
            r = _pg.extrair(_f)
            if r and r.get("competencia"):
                ok_cnpj, msg_cnpj = pgdas_confere_cnpj(r)
                if ok_cnpj is False:
                    st.markdown(f"<div class='al-r'>{msg_cnpj}</div>", unsafe_allow_html=True)
                    _cnpj_alerta = True
                    continue   # não mistura: ignora PGDAS de outro CNPJ
                _achados.append(r)
        if _achados:
            st.session_state.setdefault("pgdas_segmentos", {})
            for r in _achados:
                c = r["competencia"]
                if r.get("nome"):
                    st.session_state["empresa_pgdas"] = r["nome"]
                if r.get("cpp") is not None:
                    st.session_state.cpp_por_comp[c] = r["cpp"]
                    st.session_state.get("cpp_estimado_set", set()).discard(c)  # real substitui estimado
                if r.get("das_total"):
                    st.session_state.das_por_comp[c] = r["das_total"]
                if r.get("receita") and not st.session_state.fat_por_comp.get(c):
                    st.session_state.fat_por_comp[c] = r["receita"]
                if r.get("cpp_ratio"):
                    st.session_state["cpp_ratio_ref"] = r["cpp_ratio"]   # p/ estimar meses sem PGDAS
                if r.get("segmentos"):
                    st.session_state["pgdas_segmentos"][c] = r["segmentos"]
            _tab = pd.DataFrame([{
                "Competência": fper(r["competencia"], True),
                "CPP extraído": r.get("cpp") or 0,
                "Receita extraída": r.get("receita") or 0,
                "Status": "✅ lido" if r.get("ok") else "⚠️ confira",
            } for r in _achados])
            st.markdown("<div class='al-g'>✅ <b>PGDAS lido.</b> Confira os valores abaixo "
                        "(o CPP entra no custo; a receita preenche o faturamento).</div>",
                        unsafe_allow_html=True)
            st.dataframe(fmt_df(_tab, money=["CPP extraído", "Receita extraída"]),
                         use_container_width=True, hide_index=True)
            # segregação da receita por tipo (com/sem ST, fator R)
            for r in _achados:
                if not r.get("segmentos"):
                    continue
                st.markdown(f"**Segregação da receita — {fper(r['competencia'], True)}** "
                            f"· RBT12 {brl(r.get('rbt12') or 0)} · {r.get('fator_r') or ''}")
                seg_rows = [{"Tipo de receita": k, "Receita": v["receita"], "CPP (no DAS)": v["cpp"]}
                            for k, v in r["segmentos"].items()]
                st.dataframe(fmt_df(pd.DataFrame(seg_rows), money=["Receita", "CPP (no DAS)"]),
                             use_container_width=True, hide_index=True)
        else:
            st.warning("Não consegui ler CPP/competência nesses PDFs. Confira se é o extrato "
                       "do PGDAS-D. Você pode informar o CPP manualmente na aba Encargos.")

    if _comp_fat:
        st.markdown("**Faturamento por mês** (a receita do PGDAS já vem preenchida quando lida):")
        st.caption("A pontuação (1.000.000,00) é aplicada automaticamente. Deixe vazio o que não quiser informar.")
        editor_faturamento(_comp_fat, "fat_editor_inicial")
    else:
        st.info("Não foi possível detectar competências de folha para informar faturamento. "
                "Você poderá informar depois, na aba 💰 Gastos por Mês.")
    _cf1, _cf2, _cf3 = st.columns(3)
    if _cf1.button("➡️ Ir para Análise de Folha", type="primary", use_container_width=True):
        st.session_state.modo = "analise"
        st.rerun()
    if _cf2.button("⏭️ Análise sem faturamento", use_container_width=True):
        st.session_state.modo = "analise"
        st.rerun()
    if _cf3.button("⬅️ Voltar ao início", use_container_width=True):
        st.session_state.modo = None
        st.rerun()
    st.caption("O faturamento/CPP que você confirmar aqui já entra na Análise de Folha. "
               "Pode editar depois na aba 💰 Gastos por Mês / 🏦 Encargos.")
    st.stop()

# ── MODO CONFORMIDADE (cadastro de empresas + checklist — não depende de folha) ──
if _modo == "conformidade":
    render_conformidade()
    st.stop()

adm, alt, afa = D["admissoes"], D["alteracoes"], D["afastamentos"]
exr, des, rub = D["exp_risco"], D["desligamentos"], D["rubricas"]
rem, pag = D["remuneracao"], D["pagamentos"]
inss, irrf, fgts = D["bases_inss"], D["bases_irrf"], D["bases_fgts"]
cs = D["cs_patronal"]
exames = D.get("exames", pd.DataFrame())
hoje = date.today()
# mapa de nomes — exclusivamente do que o eSocial traz (S-2200, S-2205, etc.)
NOMES = dict(D.get("_nomes", {}))
def nome_de(cpf, mat=""):
    """Nome do funcionário; se o eSocial não traz nome, usa o CPF (mascarado/completo)."""
    nm = NOMES.get(cpf)
    if nm:
        return nm
    return f"CPF {mask_cpf(cpf)}" if cpf else (f"Matr. {mat}" if mat else "—")

if inss.empty and adm.empty and pag.empty and _modo not in ("simulador", "conformidade"):
    st.error("Nenhum dado de folha reconhecido. Verifique se os ZIPs contêm eventos do eSocial.")
    st.stop()

# normaliza bases INSS
if not inss.empty:
    for c in ["tp11_i0","tp21_i0","tp11_i1","tp21_i1","tp31_i0","tp32_i0","tp19_i0","inss_seg_calc"]:
        if c not in inss.columns: inss[c] = 0.0
        inss[c] = pd.to_numeric(inss[c], errors="coerce").fillna(0)
    inss["base_inss"]  = inss["tp11_i0"]
    # INSS empregado: vrCpSeg (infoCpCalc) é o desconto REAL calculado pelo eSocial.
    # tp21_i0/i1 é a BASE de cálculo, não o valor descontado. Diferença pequena mas importa.
    inss["inss_seg_calc"] = pd.to_numeric(inss["inss_seg_calc"], errors="coerce").fillna(0)
    inss["inss_emp"]   = inss["inss_seg_calc"]    # valor efetivamente descontado (total mensal+13)
    inss["inss_emp_m"] = inss["tp21_i0"]           # base mensal (para separação)
    inss["inss_emp_13"]= inss["tp21_i1"]           # base 13°
    inss["adic_peric"] = inss["tp31_i0"]
    inss["adic_insal"] = inss["tp32_i0"]

# remuneração (base FGTS) por cpf+período
if not fgts.empty:
    fgts["base_fgts"] = pd.to_numeric(fgts["base_fgts"], errors="coerce").fillna(0)
    fgts["deposito_fgts"] = pd.to_numeric(fgts["deposito_fgts"], errors="coerce").fillna(0)

# INSS por período — exclusivamente o que o eSocial apurou (S-5011), sem inferir regime
inss_per = ep.inss_por_periodo(cs)

# todas as competências presentes em qualquer fonte (inclui histórico do líquido)
periodos = sorted(set(
    list(inss["per_apur"].dropna().unique() if not inss.empty else []) +
    list(fgts["per_apur"].dropna().unique() if not fgts.empty else []) +
    list(cs["per_apur"].dropna().unique() if not cs.empty else []) +
    list(pag["per_apur"].dropna().unique() if not pag.empty else [])
))
# competências FECHADAS = têm totalizador de base (S-5001/S-5003) E pagamento (S-1210).
# Uma competência só com base (sem líquido) é uma PRÉVIA (ainda não paga) — não entra.
_com_base = set(
    list(inss["per_apur"].dropna().unique() if not inss.empty else []) +
    list(fgts["per_apur"].dropna().unique() if not fgts.empty else []))
_com_liq = set(pag["per_apur"].dropna().unique()) if not pag.empty else set()
periodos_fechados = sorted(_com_base & _com_liq)
# prévias: têm base mas ainda sem pagamento (ex.: mês corrente não fechado)
periodos_previa = sorted(_com_base - _com_liq)
# competências que só têm pagamento residual (rescisões/diferenças retroativas),
# sem folha completa — não devem virar uma "competência" no painel.
periodos_residuo = sorted(_com_liq - _com_base)

# competências de folha COMPLETA disponíveis (com totalizadores). Fallback: todas.
periodos_disp = periodos_fechados if periodos_fechados else periodos

# há patronal informado no eSocial? (será 0 para Simples)
tem_patronal = any(v.get("patronal", 0) > 0 for v in inss_per.values())

# ── Header ────────────────────────────────────────────────────────────────────
st.markdown(f"<div class='hero'><h1>📋 Painel de Folha — {empresa or 'eSocial'}</h1>"
            f"<p>{D['_total_xml']} eventos lidos &nbsp;·&nbsp; "
            f"{len(periodos_disp)} competência(s) de folha completa disponível(eis) &nbsp;·&nbsp; "
            f"{'COM INSS patronal apurado' if tem_patronal else 'sem INSS patronal no eSocial'} &nbsp;·&nbsp; "
            f"Emitido em {hoje.strftime('%d/%m/%Y')}</p></div>",
            unsafe_allow_html=True)

_vinculo_id = st.session_state.get("vinculo_empresa_id")
_vinculo_nome = st.session_state.get("vinculo_empresa_nome")
if _vinculo_id:
    vhc1, vhc2 = st.columns([4, 1])
    with vhc1:
        st.markdown(f"<div style='background:#eef4fb;border:1px solid #b8d4ea;border-radius:8px;"
                   f"padding:8px 14px;margin-bottom:10px;font-size:13px'>"
                   f"📌 Esta análise está <b>vinculada a {_vinculo_nome}</b> — role até o final "
                   f"para salvar no histórico dessa empresa.</div>", unsafe_allow_html=True)
    with vhc2:
        if st.button("⬅️ Voltar à ficha", key="an_voltar_ficha", use_container_width=True):
            st.session_state.modo = "conformidade"
            st.session_state.conf_empresa_id = _vinculo_id
            st.session_state.vinculo_empresa_id = None
            st.rerun()

# ── MAPA DE COMPETÊNCIAS (o que está completo e o que falta) ──────────────────
# Toda competência presente em QUALQUER evento (não só as fechadas).
_todas_comp = sorted(set(
    list(rem["per_apur"].dropna().unique() if not rem.empty else []) +
    list(inss["per_apur"].dropna().unique() if not inss.empty else []) +
    list(irrf["per_apur"].dropna().unique() if not irrf.empty else []) +
    list(fgts["per_apur"].dropna().unique() if not fgts.empty else []) +
    list(pag["per_apur"].dropna().unique() if not pag.empty else [])))
_set_rem = set(rem["per_apur"].dropna().unique()) if not rem.empty else set()
_set_inss = set(inss["per_apur"].dropna().unique()) if not inss.empty else set()
_set_irrf = set(irrf["per_apur"].dropna().unique()) if not irrf.empty else set()
_set_fgts = set(fgts["per_apur"].dropna().unique()) if not fgts.empty else set()
_set_pag = set(pag["per_apur"].dropna().unique()) if not pag.empty else set()

_map_rows = []
_n_completas = 0
for _p in _todas_comp:
    tem_rem = _p in _set_rem
    tem_tot = (_p in _set_inss) or (_p in _set_fgts)
    tem_pag = _p in _set_pag
    if tem_rem and tem_tot and tem_pag:
        _status = "✅ Completa"; _falta = "—"; _n_completas += 1
    elif tem_tot and tem_pag and not tem_rem:
        _status = "⚠️ Sem holerite"; _falta = "Rubricas (S-1200) — vêm no pacote do mês seguinte"
    elif tem_tot and not tem_pag:
        _status = "⏳ Prévia"; _falta = "Pagamento (S-1210) — folha ainda não fechou/pagou"
    elif tem_pag and not tem_tot:
        _status = "↩️ Resíduo"; _falta = "Folha completa — só há pagamento avulso (rescisão/retroativo)"
    else:
        _status = "⏳ Parcial"; _falta = "Eventos faltando para fechar a competência"
    _map_rows.append({
        "Competência": fper(_p, True),
        "Holerite (S-1200)": "✓" if tem_rem else "—",
        "INSS (S-5001)": "✓" if _p in _set_inss else "—",
        "FGTS (S-5003)": "✓" if _p in _set_fgts else "—",
        "Líquido (S-1210)": "✓" if tem_pag else "—",
        "Status": _status,
        "O que falta": _falta,
    })

with st.expander(f"📅 **Mapa de Competências** — {_n_completas} de {len(_todas_comp)} mês(es) completo(s) "
                 "· clique para entender o que está pronto", expanded=(_n_completas < len(_todas_comp))):
    st.markdown(
        "<div class='al-b'>📦 <b>Por que aparecem vários meses?</b> No portal do eSocial você baixa "
        "pela <b>data de envio</b>, mas cada XML pertence a uma <b>competência</b> (mês trabalhado). "
        "Um pacote de Janeiro normalmente contém a folha de <b>Dezembro</b> (que só é transmitida em "
        "janeiro), além de admissões/rescisões de janeiro. O app organiza tudo pela competência correta.</div>",
        unsafe_allow_html=True)
    st.markdown(
        "<div class='al-g'>✅ <b>Quando uma competência está completa?</b> Quando reúne <b>holerite "
        "(S-1200) + totalizadores (S-5001/S-5003) + líquido (S-1210)</b>. Como o S-1200 de um mês só é "
        "transmitido no mês seguinte, <b>Janeiro só fecha quando você anexa também o pacote de Fevereiro</b>. "
        "Use a tabela abaixo para ver exatamente o que ainda falta em cada mês.</div>",
        unsafe_allow_html=True)
    st.dataframe(pd.DataFrame(_map_rows), use_container_width=True, hide_index=True)
    st.caption("Só os meses ✅ Completa entram automaticamente na seleção de análise abaixo. "
               "Os demais ficam de fora até você anexar o pacote que traz o evento que falta.")

# ── SELEÇÃO DE MESES (controle do usuário) ────────────────────────────────────
_ignorados = periodos_previa + periodos_residuo

# CONTROLE ÚNICO: escolha quais meses visualizar (1, alguns ou todos).
comp_marcadas = st.multiselect(
    "📅 Meses para visualizar (escolha um, alguns ou todos)",
    options=periodos_disp,
    default=periodos_disp,
    format_func=lambda x: fper(x, True),
    help="Escolha exatamente os meses que quer analisar. Selecione 1 mês para detalhar "
         "ou conferir com o sistema de folha; selecione vários para ver o período somado. "
         "A competência é o mês TRABALHADO (o nome do arquivo costuma ser o mês de pagamento).")
# se o usuário desmarcar tudo, usa todos os disponíveis
periodos = sorted(comp_marcadas) if comp_marcadas else periodos_disp

# 1 mês → foco nele; vários → agregado do período
per_sel = periodos[0] if len(periodos) == 1 else None

periodos_label = ", ".join(fper(p, True) for p in periodos)

# legenda do que está sendo exibido
if len(periodos) > 1:
    st.markdown(f"<div class='al-b'>📊 Exibindo <b>{len(periodos)} meses</b>: "
                f"{', '.join(fper(p, True) for p in periodos)}. Valores monetários = "
                f"<b>total somado do período</b>; <b>Funcionários = saldo no último mês</b> "
                f"({fper(periodos[-1])}), não a soma entre meses. "
                f"Para conferir com o sistema de folha, deixe <b>apenas 1 mês</b> marcado.</div>",
                unsafe_allow_html=True)
else:
    st.markdown(f"<div class='al-g'>📊 Exibindo a competência <b>{fper(periodos[0], True)}</b> "
                f"(ideal para confronto com o sistema de folha).</div>", unsafe_allow_html=True)

if _ignorados:
    st.caption(
        f"ℹ️ {len(_ignorados)} competência(s) com dados parciais não listada(s) "
        f"({', '.join(fper(p) for p in _ignorados)}) — prévias (mês ainda não pago) "
        f"ou resíduos de rescisões/diferenças retroativas, sem folha completa.")

def filt(df):
    if df.empty or "per_apur" not in df.columns: return df
    if per_sel is None:   # "Todos os selecionados" → só os meses marcados
        return df[df["per_apur"].isin(periodos)]
    return df[df["per_apur"] == per_sel]
def filt_data(df, col):
    if df.empty or col not in df.columns: return df
    if per_sel is None:
        return df[df[col].astype(str).str[:7].isin(periodos)]
    return df[df[col].astype(str).str[:7] == per_sel]

inss_v, fgts_v, irrf_v, pag_v = filt(inss), filt(fgts), filt(irrf), filt(pag)
des_v, adm_v = filt_data(des, "dt_deslig"), filt_data(adm, "dt_adm")

# ── Métricas (precisas) ──────────────────────────────────────────────────────
def soma_patronal(pers):
    return sum(inss_per.get(p, {}).get("patronal", 0) for p in pers)

pers_ativos = [per_sel] if per_sel else periodos
# SALDO (headcount): funcionários ativos na ÚLTIMA competência do período.
# NUNCA somar CPFs entre meses (isso contaria quem entrou e saiu como vários).
_ult = (per_sel if per_sel else (periodos[-1] if periodos else None))
n_func = inss[inss["per_apur"] == _ult]["cpf"].nunique() if (_ult and not inss.empty) else \
         (inss_v["cpf"].nunique() if not inss_v.empty else (adm["cpf"].nunique() if not adm.empty else 0))
# pessoas DISTINTAS que passaram no período (≠ saldo) — útil p/ rotatividade
n_passaram = inss_v["cpf"].nunique() if not inss_v.empty else 0
remun    = fgts_v["base_fgts"].sum() if not fgts_v.empty else (inss_v["base_inss"].sum() if not inss_v.empty else 0)
base_inss_tot = inss_v["base_inss"].sum() if not inss_v.empty else 0
inss_emp = inss_v["inss_emp"].sum() if not inss_v.empty else 0
inss_pat = soma_patronal(pers_ativos)
fgts_dep = fgts_v["deposito_fgts"].sum() if not fgts_v.empty else 0
irrf_tot = irrf_v["irrf"].sum() if not irrf_v.empty else 0
liquido  = pag_v["vr_liquido"].sum() if not pag_v.empty else 0
peric    = inss_v["adic_peric"].sum() if not inss_v.empty else 0
insal    = inss_v["adic_insal"].sum() if not inss_v.empty else 0
sal_fam  = sum(cs[cs["per_apur"]==p]["sal_familia"].sum() for p in pers_ativos) if not cs.empty else 0
sal_mat  = sum(cs[cs["per_apur"]==p]["sal_maternidade"].sum() for p in pers_ativos) if not cs.empty else 0
# CPP do Simples (INSS patronal pago no DAS, não vem no eSocial).
# 1ª opção: valor REAL do PGDAS do mês. 2ª opção (fallback): ESTIMATIVA =
# faturamento do mês × proporção CPP/receita de um PGDAS de referência.
def cpp_de(p):
    real = st.session_state.get("cpp_por_comp", {}).get(p)
    if real is not None:
        return float(real or 0)
    ratio = st.session_state.get("cpp_ratio_ref")
    fat = st.session_state.get("fat_por_comp", {}).get(p, 0)
    if ratio and fat:
        return float(fat) * float(ratio)
    return 0.0
def cpp_estimado(p):
    """True se o CPP do mês é ESTIMADO (simulação ou proporção), não PGDAS real do mês."""
    if p in st.session_state.get("cpp_estimado_set", set()):
        return True
    if st.session_state.get("cpp_por_comp", {}).get(p) is not None:
        return False   # veio do PGDAS real do mês
    return bool(st.session_state.get("cpp_ratio_ref") and
                st.session_state.get("fat_por_comp", {}).get(p, 0))
cpp_tot = sum(cpp_de(p) for p in pers_ativos)
cpp_tem_estimativa = any(cpp_estimado(p) for p in pers_ativos)
# empresa aparenta ser Simples (sem patronal no eSocial) e o CPP não foi informado →
# o Custo Total está SUBESTIMADO (falta o INSS patronal pago via DAS).
cpp_faltando = (not tem_patronal) and cpp_tot <= 0
custo_total = remun + inss_pat + fgts_dep + cpp_tot
n_adm = len(adm_v); n_des = len(des_v)
turnover = (n_des / n_func * 100) if n_func else 0

n_afast_ativos = 0
if not afa.empty:
    afa["_fim"] = afa["dt_fim"].apply(ep._parse_date)
    n_afast_ativos = int(afa["_fim"].apply(lambda d: bool(d and d >= hoje)).sum())

if _vinculo_id:
    st.divider()
    if st.button(f"💾 Salvar esta análise no histórico de {_vinculo_nome}",
                key="salvar_an_vinculo", type="primary", use_container_width=True):
        db.analise_salvar(_vinculo_id, {
            "competencia_inicio": periodos[0] if periodos else None,
            "competencia_fim": periodos[-1] if periodos else None,
            "resumo": {
                "competencias": periodos, "headcount": int(n_func),
                "remuneracao_total": float(remun), "fgts_total": float(fgts_dep),
                "liquido_pago_total": float(liquido), "custo_total": float(custo_total),
            },
        })
        st.success(f"✅ Análise salva no histórico de {_vinculo_nome}!")

# ─────────────────────────────────────────────────────────────────────────────
T = st.tabs(["📊 Visão Geral", "💵 Folha & Custo", "🏦 Encargos", "💰 Gastos por Mês", "🎯 Simulador",
             "🔄 Movimentação", "🏥 Afastamentos",
             "🔎 Consultar Funcionário", "✅ Conferência", "📄 Relatório"])
# índices: 0 Visão, 1 Folha, 2 Encargos, 3 Gastos, 4 Simulador, 5 Movim,
#          6 Consultar, 7 Conferência, 8 Relatório

# ═══════════════════════ VISÃO GERAL ════════════════════════════════════════
with T[0]:
    # ── DIAGNÓSTICO CONSULTIVO (especialista de DP) ──────────────────────────
    import diagnostico as _diag
    # HE valor no período
    _he_val = 0.0
    _rmap = (rub.drop_duplicates("cod_rubr").set_index("cod_rubr") if not rub.empty else pd.DataFrame())
    def _he(cod):
        if cod in {"35","36","37","38","39","40"}: return True
        nm = ""
        if not _rmap.empty and cod in _rmap.index: nm = str(_rmap.loc[cod,"desc"]).upper()
        elif cod in ep.RUBRICAS_PADRAO: nm = ep.RUBRICAS_PADRAO[cod][1].upper()
        return "EXTRA" in nm or "HRS.EXT" in nm or "HORAS EXT" in nm
    for _, _row in filt(rem).iterrows():
        for _rr in _row.get("rubricas", []) or []:
            if _he(_rr["cod_rubr"]): _he_val += _rr.get("valor", 0)
    # variação da folha (último mês vs anterior)
    _var = None
    if len(periodos) >= 2:
        _f = [fgts[fgts["per_apur"]==p]["base_fgts"].sum() for p in periodos]
        if _f[-2]: _var = (_f[-1]-_f[-2])/_f[-2]*100
    # ferias resumo
    _fres = {"Vencida":0,"Crítico":0,"Atenção":0,"Em dia":0,"Adquirindo":0}
    if not adm.empty:
        for _, r in adm.iterrows():
            fx = ep.status_ferias(r.get("dt_adm"), hoje)
            if fx: _fres[fx["status"]] = _fres.get(fx["status"],0)+1
    ctx_diag = {
        "n_func": n_func, "folha": remun, "inss_emp": inss_emp, "fgts": fgts_dep,
        "custo_total": custo_total, "turnover": turnover, "n_adm": n_adm, "n_des": n_des,
        "salario_medio": (remun/n_func if n_func else 0),
        "encargos_pct": ((inss_pat+fgts_dep)/remun*100 if remun else 0),
        "he_valor": _he_val, "var_folha": _var, "ferias_resumo": _fres,
        "afa_df": afa, "exames_df": exames,
        "rescisao_indireta": int((des_v["cod_motivo"]=="02").sum()) if not des_v.empty else 0,
        "sem_justa": int((des_v["cod_motivo"]=="01").sum()) if not des_v.empty else 0,
        "aposentadorias": int(des_v["cod_motivo"].isin(["06","07"]).sum()) if not des_v.empty else 0,
        "pcd": int(adm["pcd"].sum()) if ("pcd" in adm.columns and not adm.empty) else 0,
    }
    insights = _diag.gerar(ctx_diag)
    n_crit = sum(1 for i in insights if i["sev"]=="critico")
    n_aten = sum(1 for i in insights if i["sev"]=="atencao")

    st.markdown("### 🎯 Diagnóstico do Especialista")
    resumo_txt = []
    if n_crit: resumo_txt.append(f"<b style='color:#e03131'>{n_crit} ponto(s) crítico(s)</b>")
    if n_aten: resumo_txt.append(f"<b style='color:#e8951a'>{n_aten} ponto(s) de atenção</b>")
    if not resumo_txt: resumo_txt.append("<b style='color:#2f9e44'>Sem riscos críticos</b>")
    st.markdown(f"<div style='color:#56606e;font-size:13px;margin-bottom:8px'>Análise automática "
                f"dos dados do eSocial · {' · '.join(resumo_txt)}</div>", unsafe_allow_html=True)

    _cor = {"critico":("#fdecec","#e03131","🔴"),"atencao":("#fdf6e9","#e8951a","🟠"),
            "info":("#eef2ff","#3b5bdb","💡"),"ok":("#eaf7ef","#2f9e44","✅")}
    for ins in insights:
        bg, bd, ic = _cor.get(ins["sev"], _cor["info"])
        base_html = f"<div style='font-size:11px;color:#868e96;margin-top:5px'>📖 {ins['base']}</div>" if ins["base"] else ""
        acao_html = f"<div style='margin-top:6px;font-size:12.5px'><b style='color:{bd}'>✓ Recomendação:</b> {ins['acao']}</div>" if ins["acao"] else ""
        st.markdown(
            f"<div style='background:{bg};border-left:4px solid {bd};border-radius:8px;"
            f"padding:12px 16px;margin-bottom:9px'>"
            f"<div style='font-size:10.5px;color:{bd};font-weight:700;text-transform:uppercase;letter-spacing:.04em'>{ins['cat']}</div>"
            f"<div style='font-size:14.5px;font-weight:700;color:#0f1b2d;margin:1px 0 4px'>{ic} {ins['titulo']}</div>"
            f"<div style='font-size:12.5px;color:#3a4250;line-height:1.5'>{ins['analise']}</div>"
            f"{acao_html}{base_html}</div>", unsafe_allow_html=True)

    st.divider()
    st.markdown("### Indicadores do Período")
    if cpp_faltando:
        st.markdown(
            "<div class='al-r'>⚠️ <b>Custo sem o CPP do Simples.</b> Esta empresa não tem INSS "
            "patronal no eSocial (Simples), e o <b>CPP ainda não foi informado</b> — então o "
            "<b>Custo Total abaixo está subestimado</b> (falta o INSS patronal pago via DAS). "
            "Para incluir: anexe o <b>PGDAS</b> (Passo 2 ou no Simulador) ou digite o CPP na aba "
            "<b>🏦 Encargos → ➕ CPP do Simples</b>.</div>", unsafe_allow_html=True)
    r1 = st.columns(4)
    kpi(r1[0], n_func, "Funcionários (saldo)",
        f"saldo em {fper(_ult)}" if _ult else "",
        "n")
    kpi(r1[1], brl(remun), "Remuneração Bruta", "base FGTS", "n")
    kpi(r1[2], brl(liquido), "Líquido Pago")
    kpi(r1[3], brl(custo_total), "Custo Total p/ Empresa")
    r2 = st.columns(4)
    kpi(r2[0], brl(inss_emp), "INSS Empregado", "desconto")
    kpi(r2[1], brl(inss_pat), "INSS Patronal",
        "apurado no eSocial" if tem_patronal else "não recolhido (ex.: Simples)")
    kpi(r2[2], brl(fgts_dep), "FGTS (depósito)", "8%")
    kpi(r2[3], brl(irrf_tot), "IRRF Retido")
    r3 = st.columns(4)
    kpi(r3[0], n_adm, "Admissões", "no período")
    kpi(r3[1], n_des, "Desligamentos", "no período")
    kpi(r3[2], f"{turnover:.1f}%", "Turnover",
        "Alto" if turnover > 5 else "Moderado" if turnover > 2 else "Baixo",
        "down" if turnover > 5 else "n")
    kpi(r3[3], n_afast_ativos, "Afastados hoje")
    # ── Faturamento × Folha (se o usuário já informou) ───────────────────────
    _fat = st.session_state.get("fat_por_comp", {})
    _fat_tot = sum(_fat.get(p, 0) for p in periodos)
    if _fat_tot > 0:
        _pct_custo = custo_total/_fat_tot*100
        _cor = "down" if _pct_custo >= 50 else "n"
        r4 = st.columns(3)
        kpi(r4[0], brl(_fat_tot), "Faturamento (informado)", "digitado por você", "n")
        kpi(r4[1], f"{_pct_custo:.1f}%".replace(".", ","), "% do faturamento na folha",
            "folha + encargos", _cor)
        kpi(r4[2], ("R$ " + f"{100-_pct_custo:.2f}".replace(".", ",")), "Sobra de cada R$ 100",
            "p/ despesas, impostos e lucro", "n")
    else:
        st.caption("💡 Quer ver quanto do faturamento vai para a folha? Informe a receita de cada "
                   "mês na aba 💰 Gastos por Mês → Faturamento × Folha.")
    if len(periodos) > 1:
        saldo_ini = inss[inss["per_apur"]==periodos[0]]["cpf"].nunique() if not inss.empty else 0
        st.markdown(
            f"<div style='font-size:12.5px;color:#56606e;margin-top:6px'>"
            f"👥 <b>Movimento do período:</b> começou com <b>{saldo_ini}</b> em {fper(periodos[0])}, "
            f"terminou com <b>{n_func}</b> em {fper(periodos[-1])} "
            f"(saldo {n_func-saldo_ini:+d}). Ao todo, <b>{n_passaram} pessoas distintas</b> "
            f"passaram pela folha no período (entradas + quem já estava + saídas).</div>",
            unsafe_allow_html=True)

    with st.expander("🔎 Conferência — de onde vem cada número (fonte no eSocial)"):
        conf = pd.DataFrame([
            ["Remuneração Bruta", brl(remun), "S-5003", "remFGTS — base do FGTS (salários + adicionais + 13º)"],
            ["Líquido Pago", brl(liquido), "S-1210", "vrLiq — soma dos pagamentos líquidos"],
            ["INSS Empregado", brl(inss_emp), "S-5001", "vrCpSeg — contribuição descontada do empregado"],
            ["INSS Patronal", brl(inss_pat), "S-5011", "CPP+RAT+Terceiros (zero se não recolhido no eSocial)"],
            ["FGTS", brl(fgts_dep), "S-5003", "dpsFGTS — depósito de 8%"],
            ["IRRF", brl(irrf_tot), "S-5002", "vlrCRMen — imposto retido na fonte"],
            ["Custo Total", brl(custo_total), "cálculo", "Remuneração + INSS patronal + FGTS"],
            ["Funcionários", str(n_func), "S-5001", "CPFs distintos com base no período"],
        ], columns=["Indicador", "Valor", "Evento", "O que é"])
        st.dataframe(conf, use_container_width=True, hide_index=True)
        st.caption("Cada valor vem de um evento específico do eSocial. Rubricas individuais "
                   "(S-1200) NÃO são somadas para formar a folha — usamos os totalizadores oficiais.")

    st.divider()
    cL, cR = st.columns(2)
    with cL:
        st.markdown("#### Composição do Custo da Folha")
        base = remun or 1
        comp_vals = [(l, v) for v, l in [
            (remun, "Remuneração Bruta"),
            (inss_emp, "INSS Empregado (desconto)"),
            (inss_pat, "INSS Patronal"),
            (cpp_tot, "INSS Patronal / CPP (Simples — PGDAS)"),
            (fgts_dep, "FGTS (8%)"),
            (irrf_tot, "IRRF"),
        ] if v > 0]
        tabela_barra(comp_vals, label_col="Componente", money=True)
        enc_pct = (inss_pat+cpp_tot+fgts_dep)/base*100
        st.markdown(
            f"<div style='font-size:13px;color:#48535f'>Encargos patronais (INSS + FGTS) = "
            f"<b>{brl(inss_pat+fgts_dep)}</b> ({enc_pct:.1f}% da remuneração). "
            f"Cada R$ 1,00 pago custa <b>R$ {custo_total/base:.2f}</b> à empresa." +
            ("" if tem_patronal else " <i>(eSocial não traz INSS patronal — ex.: Simples Nacional.)</i>") +
            "</div>", unsafe_allow_html=True)
    with cR:
        st.markdown("#### Custo Total por Competência")
        if len(periodos) > 1:
            rows=[]
            for p in periodos:
                rr = fgts[fgts["per_apur"]==p]["base_fgts"].sum() if not fgts.empty else 0
                gg = fgts[fgts["per_apur"]==p]["deposito_fgts"].sum() if not fgts.empty else 0
                ie = inss[inss["per_apur"]==p]["inss_emp"].sum() if not inss.empty else 0
                ir = irrf[irrf["per_apur"]==p]["irrf"].sum() if not irrf.empty else 0
                rows.append({"lbl":fper(p),"remun":rr,"inss_emp":ie,
                             "pat":inss_per.get(p,{}).get("patronal",0),"cpp":cpp_de(p),"fgts":gg,"irrf":ir})
            ev = pd.DataFrame(rows)
            ev["total"] = ev["remun"] + ev["inss_emp"] + ev["pat"] + ev["cpp"] + ev["fgts"] + ev["irrf"]
            show = pd.DataFrame({
                "Competência": ev["lbl"], "Remuneração": ev["remun"],
                "INSS Empreg.": ev["inss_emp"], "INSS Patronal": ev["pat"],
                "CPP (Simples)": ev["cpp"], "FGTS": ev["fgts"], "IRRF": ev["irrf"],
                "Custo Total": ev["total"]})
            if ev["pat"].sum() == 0: show = show.drop(columns=["INSS Patronal"])
            if ev["cpp"].sum() == 0: show = show.drop(columns=["CPP (Simples)"])
            if ev["irrf"].sum() == 0: show = show.drop(columns=["IRRF"])
            money_cols = [c for c in show.columns if c != "Competência"]
            st.dataframe(fmt_df(show, money=money_cols), use_container_width=True, hide_index=True)
        else:
            st.info("Anexe mais de um mês para ver a evolução.")

    if sal_fam + sal_mat > 0:
        st.markdown(f"<div class='al-b'>💡 <b>Valores reembolsáveis pela Previdência</b> no período: "
                    f"Salário-família {brl(sal_fam)} + Salário-maternidade {brl(sal_mat)} = "
                    f"<b>{brl(sal_fam+sal_mat)}</b> (abatidos na GPS/DCTFWeb).</div>", unsafe_allow_html=True)

    st.divider()
    st.markdown("#### 🔔 Pontos de Atenção")
    alertas = []
    if not des.empty:
        ri = (des["cod_motivo"] == "02").sum()
        if ri: alertas.append(("al-r", f"<b>{ri} rescisão(ões) indireta(s)</b> — funcionário alega culpa da empresa. Exposição a passivo trabalhista; avaliar juridicamente."))
        sjc = (des["cod_motivo"] == "01").sum()
        if sjc: alertas.append(("al-y", f"<b>{sjc} demissão(ões) sem justa causa</b> — geram aviso prévio + multa de 40% do FGTS."))
    if turnover > 5:
        alertas.append(("al-r", f"<b>Turnover de {turnover:.1f}%</b> acima do saudável (5%/mês). Investigar causas de saída."))
    if not afa.empty:
        mat = afa[afa["cod_motivo"].isin(["04","05","06","15","33"])]["cpf"].nunique()
        if mat: alertas.append(("al-b", f"<b>{mat} licença(s)-maternidade</b> no período — planejar cobertura; benefício pago pelo INSS."))
    if not alertas:
        alertas.append(("al-g", "Nenhum ponto crítico identificado neste período. ✔️"))
    for cls, txt in alertas:
        st.markdown(f"<div class='{cls}'>{txt}</div>", unsafe_allow_html=True)

# ═══════════════════════ FOLHA & CUSTO ══════════════════════════════════════
with T[1]:
    st.markdown("### Custo Real por Funcionário")
    if inss_v.empty and fgts_v.empty:
        st.info("Sem bases para o período selecionado.")
    else:
        # base por funcionário: remuneração (FGTS) + INSS emp + FGTS + líquido
        b_inss = inss_v.groupby(["cpf","matricula"]).agg(
            base_inss=("base_inss","sum"), inss_emp=("inss_emp","sum"),
            peric=("adic_peric","sum"), insal=("adic_insal","sum")).reset_index()
        b_fg = fgts_v.groupby("cpf").agg(remun=("base_fgts","sum"), fgts=("deposito_fgts","sum")).reset_index() if not fgts_v.empty else pd.DataFrame(columns=["cpf","remun","fgts"])
        base_df = b_inss.merge(b_fg, on="cpf", how="outer")
        if not pag_v.empty:
            base_df = base_df.merge(pag_v.groupby("cpf").agg(liq=("vr_liquido","sum")).reset_index(), on="cpf", how="left")
        else: base_df["liq"]=0
        base_df = base_df.fillna(0)
        # rateio do INSS patronal por proporção da remuneração
        tot_remun = base_df["remun"].sum() or 1
        base_df["inss_pat"] = base_df["remun"]/tot_remun * inss_pat
        base_df["custo"] = base_df["remun"] + base_df["inss_pat"] + base_df["fgts"]
        base_df["enc_pct"] = ((base_df["inss_pat"]+base_df["fgts"]) /
                              base_df["remun"].replace(0, pd.NA) * 100).fillna(0)
        nomes = NOMES
        base_df["nome"] = base_df["cpf"].apply(nome_de)
        base_df = base_df.sort_values("custo", ascending=False)

        c = st.columns(4)
        kpi(c[0], brl(base_df["custo"].sum()), "Custo Total")
        kpi(c[1], brl(base_df["custo"].mean()), "Custo Médio/Func.")
        kpi(c[2], brl(base_df["remun"].mean()), "Remuneração Média")
        enc = (inss_pat+base_df["fgts"].sum())/(base_df["remun"].sum() or 1)*100
        kpi(c[3], f"{enc:.1f}%", "Encargos s/ Remun.")

        tbl = base_df.copy()
        tbl["CPF"] = tbl["cpf"].apply(mask_cpf)
        show = tbl[["matricula","nome","CPF","remun","base_inss","peric","insal",
                    "inss_emp","inss_pat","fgts","liq","custo","enc_pct"]].copy()
        show.columns = ["Matr.","Nome","CPF","Remuneração","Base INSS","Periculos.","Insalub.",
                        "INSS Emp.","INSS Pat.","FGTS","Líquido","Custo Real","Enc.%"]
        st.dataframe(fmt_df(show,
            money=["Remuneração","Base INSS","Periculos.","Insalub.","INSS Emp.","INSS Pat.","FGTS","Líquido","Custo Real"],
            pct=["Enc.%"]), use_container_width=True, hide_index=True)
        st.caption("INSS patronal rateado por proporção da remuneração de cada funcionário "
                   f"(total do período: {brl(inss_pat)}).")

        st.divider()
        st.markdown("### Resumo Geral de Verbas da Folha")
        st.caption("Composição da folha por rubrica e tipo, a partir do S-1200. "
                   "Mostra QUAIS verbas compõem a folha e quanto cada uma pesa. "
                   "Pode divergir do fechamento do sistema de folha (agrega demonstrativos "
                   "de forma diferente) — os valores oficiais de INSS/FGTS/IRRF estão na aba Encargos.")
        rem_v = filt(rem)
        linhas = []
        for _, row in rem_v.iterrows():
            for rr in row.get("rubricas", []) or []:
                linhas.append({"cod": rr["cod_rubr"], "valor": rr["valor"], "qtd": rr.get("qtd", 0)})
        if not linhas:
            st.info("Sem detalhamento de rubricas (S-1200) para o período.")
        else:
            rdf = pd.DataFrame(linhas)
            rmap = (rub.drop_duplicates("cod_rubr").set_index("cod_rubr")
                    if not rub.empty else pd.DataFrame())

            def info_rub(c):
                # 1º: S-1010 do empregador (nome + tipo). 2º: dicionário padrão Questor.
                if not rmap.empty and c in rmap.index:
                    nome = rmap.loc[c, "desc"]
                    tp = str(rmap.loc[c, "tipo"] or "")
                    nat = str(rmap.loc[c, "natureza"] or "").strip()
                    if tp == "1": cat = "P"
                    elif tp == "2": cat = "D"
                    elif tp in ("3", "4"): cat = "I"
                    elif nat.isdigit() and 9200 <= int(nat) <= 9399: cat = "D"
                    elif nat.isdigit() and int(nat) >= 9900: cat = "I"
                    else: cat = "P"
                    return cat, nome
                if c in ep.RUBRICAS_PADRAO:
                    return ep.RUBRICAS_PADRAO[c]
                return "?", f"Rubrica {c}"

            agg = rdf.groupby("cod").agg(total=("valor","sum"), qtd=("valor","count")).reset_index()
            agg["cat"] = agg["cod"].apply(lambda c: info_rub(c)[0])
            agg["Rubrica"] = agg["cod"].apply(lambda c: info_rub(c)[1])

            # subtotais por categoria
            sub = {k: agg[agg["cat"]==k]["total"].sum() for k in ["P","D","B","I","A","?"]}
            tot_prov = sub["P"] + sub["B"]
            tot_desc = sub["D"]
            liquido_verbas = tot_prov - tot_desc

            cc = st.columns(4)
            kpi(cc[0], brl(tot_prov), "Proventos + Vantagens")
            kpi(cc[1], brl(tot_desc), "Descontos")
            kpi(cc[2], brl(liquido_verbas), "Líquido (Prov − Desc)")
            kpi(cc[3], brl(sub["I"]), "Informativas (FGTS/base)")

            # tabela por categoria
            ordem = [("P","🟢 Proventos"),("B","🔵 Vantagens/Benefícios"),
                     ("D","🔴 Descontos"),("A","🟠 Auxílios (INSS)"),
                     ("I","⚪ Informativas (FGTS/bases)"),("?","❔ Não identificadas")]
            for cat, titulo in ordem:
                bloco = agg[agg["cat"]==cat].sort_values("total", ascending=False)
                if bloco.empty: continue
                with st.expander(f"{titulo} — {len(bloco)} rubrica(s) · {brl(bloco['total'].sum())}",
                                 expanded=(cat in ("P","D"))):
                    s = bloco[["cod","Rubrica","qtd","total"]].copy()
                    s.columns = ["Cód.","Rubrica","Ocorrências","Valor Total"]
                    st.dataframe(fmt_df(s, money=["Valor Total"]), use_container_width=True, hide_index=True)
            if sub["?"] > 0:
                st.caption("Rubricas 'não identificadas' não constam no S-1010 dos arquivos nem no "
                           "dicionário padrão. Os totais oficiais da folha (INSS/FGTS/IRRF) usam "
                           "sempre os eventos totalizadores S-5001/5002/5003.")

        # ── HORAS EXTRAS (qtdRubr das rubricas de HE) ────────────────────────
        st.divider()
        st.markdown("### ⏱️ Horas Extras")
        st.caption("Quantidade e valor de horas extras (rubricas de HE no S-1200). "
                   "HE elevada sinaliza necessidade de contratar ou rever a jornada.")
        # rubricas de HE: códigos cujo nome contém 'extra' ou cod conhecidos (35)
        HE_CODS = {"35","36","37","38","39","40"}  # faixas comuns de HE no Questor
        rem_v2 = filt(rem)
        he_rows = []
        rmap2 = (rub.drop_duplicates("cod_rubr").set_index("cod_rubr")
                 if not rub.empty else pd.DataFrame())
        def _is_he(cod):
            if cod in HE_CODS: return True
            nm = ""
            if not rmap2.empty and cod in rmap2.index: nm = str(rmap2.loc[cod,"desc"]).upper()
            elif cod in ep.RUBRICAS_PADRAO: nm = ep.RUBRICAS_PADRAO[cod][1].upper()
            return "EXTRA" in nm or "HRS.EXT" in nm or "HORAS EXT" in nm
        for _, row in rem_v2.iterrows():
            for rr in row.get("rubricas", []) or []:
                if _is_he(rr["cod_rubr"]) and (rr.get("qtd",0) or rr.get("valor",0)):
                    he_rows.append({"matricula": row.get("matricula",""),
                                    "horas": rr.get("qtd",0), "valor": rr.get("valor",0)})
        if not he_rows:
            st.info("Nenhuma hora extra identificada no período.")
        else:
            hedf = pd.DataFrame(he_rows)
            g = hedf.groupby("matricula").agg(horas=("horas","sum"), valor=("valor","sum")).reset_index()
            g = g[g["valor"]>0].sort_values("valor", ascending=False)
            cc = st.columns(3)
            kpi(cc[0], f"{hedf['horas'].sum():.0f}h", "Total de Horas Extras")
            kpi(cc[1], brl(hedf["valor"].sum()), "Custo de HE")
            kpi(cc[2], len(g), "Funcionários c/ HE")
            gs = g.rename(columns={"matricula":"Matr.","horas":"Horas","valor":"Valor"})
            gs["Horas"] = gs["Horas"].apply(lambda h: f"{h:.1f} h".replace(".", ","))
            st.dataframe(fmt_df(gs, money=["Valor"]), use_container_width=True, hide_index=True)

# ═══════════════════════ ENCARGOS ═══════════════════════════════════════════
with T[2]:
    st.markdown("### Encargos e Tributos sobre a Folha")
    c = st.columns(4)
    kpi(c[0], brl(inss_emp+inss_pat), "INSS Total", f"Emp {brl_k(inss_emp)} + Pat {brl_k(inss_pat)}")
    kpi(c[1], brl(inss_pat), "INSS Patronal", "apurado no eSocial" if tem_patronal else "não recolhido")
    kpi(c[2], brl(fgts_dep), "FGTS", "8% s/ remuneração")
    kpi(c[3], brl(irrf_tot), "IRRF Retido", f"{irrf_v['n_dependentes'].sum() if not irrf_v.empty else 0} dependentes")

    # ── VALIDAÇÃO AUTOMÁTICA (sem precisar do Questor/Receita) ────────────────
    with st.expander("🔒 Posso confiar nestes valores? (validação automática pelo próprio XML)"):
        st.markdown(
            "<div class='al-b'>O eSocial traz o INSS do empregado em <b>dois eventos independentes</b>: "
            "o <b>S-5001</b> (somando trabalhador por trabalhador) e o <b>S-5011</b> (total consolidado "
            "que gera a guia). Se os dois batem, a leitura do XML está correta — não é preciso conferir "
            "fora do app.</div>", unsafe_allow_html=True)
        vrows = []
        _all_ok = True
        for p in pers_ativos:
            d = inss_per.get(p)
            if not d: continue
            _s5001 = inss[inss["per_apur"] == p]["inss_emp"].sum() if not inss.empty else 0
            _s5011 = d.get("segurado", 0)
            ok = abs(_s5001 - _s5011) < 0.05
            _all_ok = _all_ok and ok
            vrows.append({"Competência": fper(p),
                          "INSS empregado (S-5001)": _s5001,
                          "INSS empregado (S-5011)": _s5011,
                          "Confere?": "✅ bate" if ok else "⚠️ divergente"})
        if vrows:
            st.dataframe(fmt_df(pd.DataFrame(vrows),
                         money=["INSS empregado (S-5001)", "INSS empregado (S-5011)"]),
                         use_container_width=True, hide_index=True)
            if _all_ok:
                st.markdown("<div class='al-g'>✅ <b>Os dois eventos batem em todos os meses.</b> "
                            "A leitura do XML está consistente.</div>", unsafe_allow_html=True)
        # âncoras externas fáceis de achar
        gtot = []
        for p in pers_ativos:
            d = inss_per.get(p) or {}
            gtot.append({"Competência": fper(p),
                         "INSS → DCTFWeb/DARF (guia)": d.get("apurado", 0),
                         "FGTS → FGTS Digital (DAE)": fgts[fgts["per_apur"]==p]["deposito_fgts"].sum() if not fgts.empty else 0})
        if gtot:
            st.markdown("**Se quiser conferir fora, são só estes 2 números por mês:**")
            st.dataframe(fmt_df(pd.DataFrame(gtot),
                         money=["INSS → DCTFWeb/DARF (guia)", "FGTS → FGTS Digital (DAE)"]),
                         use_container_width=True, hide_index=True)
            st.caption("Esses totalizadores (S-5011 e S-5003) são exatamente os que o governo usa "
                       "para gerar a DCTFWeb (INSS) e o FGTS Digital (DAE). O valor da guia de FGTS do "
                       "mês deve ser igual à coluna FGTS; o INSS da DCTFWeb igual à coluna INSS.")

    # INSS apurado pelo eSocial (S-5011) — valores reais, sem inferência
    if not cs.empty:
        st.markdown("#### INSS apurado no eSocial (S-5011)")
        mem = []
        for p in pers_ativos:
            d = inss_per.get(p)
            if not d: continue
            mem.append({"Competência": fper(p),
                        "Base de cálculo": d["base"],
                        "INSS segurado (empregado)": d["segurado"],
                        "INSS patronal": d["patronal"],
                        "INSS total apurado (guia)": d["apurado"]})
        if mem:
            mdf = pd.DataFrame(mem)
            st.dataframe(fmt_df(mdf, money=[k for k in mdf.columns if k!="Competência"]),
                         use_container_width=True, hide_index=True)
        if not tem_patronal:
            st.caption("Esta empresa não tem INSS patronal informado no eSocial "
                       "(característico do Simples Nacional, que recolhe a contribuição patronal via DAS).")

    # ── CPP do Simples (PGDAS) — informar/editar ─────────────────────────────
    with st.expander("➕ INSS Patronal / CPP do Simples (do PGDAS) — incluir no custo"):
        st.caption("No Simples, o INSS patronal (CPP) é pago no DAS e não vem no eSocial. "
                   "Anexe o PGDAS-D na tela inicial (extrai automático) ou digite aqui o CPP de "
                   "cada mês — ele entra no Custo Total. Os valores se aplicam na hora.")
        editor_faturamento(list(periodos), "cpp_editor_enc",
                           store="cpp_por_comp", coluna="CPP / INSS Patronal (R$)")
        _cpp_now = sum(cpp_de(p) for p in periodos)
        if _cpp_now > 0:
            st.markdown(f"<div class='al-g'>✅ CPP informado no período: <b>{brl(_cpp_now)}</b> "
                        "— já somado ao Custo Total.</div>", unsafe_allow_html=True)

    st.divider()
    cL, cR = st.columns(2)
    with cL:
        st.markdown("#### Distribuição dos Encargos")
        vals = [inss_emp, inss_pat, fgts_dep, irrf_tot]
        labs = ["INSS Empregado","INSS Patronal","FGTS","IRRF"]
        vv = [(l,v) for l,v in zip(labs,vals) if v>0]
        if vv:
            tabela_barra(sorted(vv, key=lambda x: -x[1]), label_col="Encargo", money=True)
    with cR:
        st.markdown("#### Guias a Recolher (estimativa)")
        st.markdown(f"""
<div class='box'>
<table style='width:100%; font-size:14px;'>
<tr><td>GPS / DCTFWeb — INSS (empregado + patronal)</td><td style='text-align:right'><b>{brl(inss_emp+inss_pat)}</b></td></tr>
<tr><td>FGTS Digital (depósito do mês)</td><td style='text-align:right'><b>{brl(fgts_dep)}</b></td></tr>
<tr><td>DARF IRRF (código 0561)</td><td style='text-align:right'><b>{brl(irrf_tot)}</b></td></tr>
<tr style='border-top:2px solid #1f3a5f;'><td><b>Total de obrigações do período</b></td>
<td style='text-align:right'><b>{brl(inss_emp+inss_pat+fgts_dep+irrf_tot)}</b></td></tr>
</table></div>""", unsafe_allow_html=True)
        if sal_fam+sal_mat > 0:
            st.caption(f"A GPS pode ser abatida em {brl(sal_fam+sal_mat)} de salário-família/maternidade (reembolso INSS).")
        st.caption("Confira sempre contra a DCTFWeb e o FGTS Digital antes do recolhimento.")

    if len(periodos) > 1:
        st.divider()
        st.markdown("#### Encargos por Competência")
        rows=[]
        for p in periodos:
            ii = inss[inss["per_apur"]==p]
            gg = fgts[fgts["per_apur"]==p]
            rr = irrf[irrf["per_apur"]==p]
            ie = ii["inss_emp"].sum() if not ii.empty else 0
            fg = gg["deposito_fgts"].sum() if not gg.empty else 0
            ir = rr["irrf"].sum() if not rr.empty else 0
            rows.append({"Competência":fper(p),"INSS Empregado":ie,
                         "FGTS":fg,"IRRF":ir,"Total":ie+fg+ir})
        edf=pd.DataFrame(rows)
        st.dataframe(fmt_df(edf, money=["INSS Empregado","FGTS","IRRF","Total"]), use_container_width=True, hide_index=True)

# ═══════════════════════ GASTOS POR MÊS ═════════════════════════════════════
with T[3]:
    st.markdown("### 💰 Gastos com a Folha — Evolução Mês a Mês")
    st.caption("Quanto a empresa gastou e com o quê, mês a mês. O 'Custo Total' é o gasto "
               "real (remuneração + INSS patronal + FGTS). Acompanhe a variação para "
               "detectar aumentos.")
    if len(periodos) == 0:
        st.info("Sem competências para exibir.")
    else:
        # ── QUANTO GASTOU (custo total por mês + variação) ───────────────────
        st.markdown("#### Quanto gastou")
        linhas = []
        prev = None
        for p in periodos:
            gg = fgts[fgts["per_apur"]==p]
            rr = irrf[irrf["per_apur"]==p]
            remun_p = gg["base_fgts"].sum() if not gg.empty else 0
            pat_p = inss_per.get(p, {}).get("patronal", 0)
            cpp_p = cpp_de(p)
            fg_p = gg["deposito_fgts"].sum() if not gg.empty else 0
            custo_p = remun_p + pat_p + cpp_p + fg_p
            var_rs = (custo_p - prev) if prev is not None else None
            var_pct = (var_rs/prev*100) if (prev and prev != 0) else None
            linhas.append({"Competência": fper(p), "Remuneração": remun_p,
                           "INSS Patronal": pat_p, "CPP (Simples)": cpp_p, "FGTS": fg_p,
                           "Custo Total": custo_p, "Δ R$": var_rs, "Δ %": var_pct})
            prev = custo_p
        gdf = pd.DataFrame(linhas)
        _gcols = ["Remuneração","INSS Patronal","CPP (Simples)","FGTS","Custo Total","Δ R$"]
        if gdf["CPP (Simples)"].sum() == 0: gdf = gdf.drop(columns=["CPP (Simples)"]); _gcols.remove("CPP (Simples)")
        st.dataframe(fmt_df(gdf, money=_gcols, pct=["Δ %"]), use_container_width=True, hide_index=True)
        if any(cpp_estimado(p) for p in periodos):
            _est_meses = ", ".join(fper(p) for p in periodos if cpp_estimado(p))
            st.markdown(
                f"<div class='al-y'>≈ <b>CPP estimado</b> em: {_est_meses}. Esses meses não têm "
                "PGDAS anexado — o CPP foi calculado como <b>faturamento × proporção CPP/receita</b> "
                "de um PGDAS de referência. É estimativa (varia com o mix de vendas com/sem "
                "substituição e fator R); ao anexar o PGDAS do mês, o valor real substitui.</div>",
                unsafe_allow_html=True)

        # ── MEMÓRIA DE CÁLCULO (de onde vem o custo + prova de consistência) ──
        with st.expander("🔍 De onde vem esse custo? (memória de cálculo + prova de que confere)"):
            st.markdown(
                "<div class='al-b'>O custo da folha <b>não é estimativa</b>: é montado com os "
                "<b>totalizadores oficiais</b> que a própria empresa transmitiu ao eSocial. "
                "Fórmula: <b>Custo = Remuneração (S-5003) + INSS Patronal (S-5011) + FGTS (S-5003)</b>.</div>",
                unsafe_allow_html=True)
            _cpp_mem = sum(cpp_de(p) for p in periodos)
            _linhas_mem = [
                {"Componente": "Remuneração bruta", "Valor": gdf["Remuneração"].sum(),
                 "Evento": "S-5003", "Campo": "remFGTS", "Como é obtido": "Soma de todos os trabalhadores"},
                {"Componente": "INSS Patronal", "Valor": gdf["INSS Patronal"].sum(),
                 "Evento": "S-5011", "Campo": "vrBcCp00", "Como é obtido": "Apurado pelo eSocial (0 no Simples)"},
            ]
            if _cpp_mem > 0:
                _linhas_mem.append(
                {"Componente": "INSS Patronal / CPP (Simples)", "Valor": _cpp_mem,
                 "Evento": "PGDAS-D", "Campo": "INSS/CPP", "Como é obtido": "Extraído do PGDAS (pago no DAS, fora do eSocial)"})
            _linhas_mem += [
                {"Componente": "FGTS (8%)", "Valor": gdf["FGTS"].sum(),
                 "Evento": "S-5003", "Campo": "dpsFGTS", "Como é obtido": "Depósito do mês (inclui rescisões)"},
                {"Componente": "= CUSTO TOTAL", "Valor": gdf["Custo Total"].sum(),
                 "Evento": "—", "Campo": "—", "Como é obtido": "Soma das parcelas acima"},
            ]
            _mem = pd.DataFrame(_linhas_mem)
            st.dataframe(fmt_df(_mem, money=["Valor"]), use_container_width=True, hide_index=True)
            # PROVA: soma por funcionário tem de bater com o totalizador
            _rem_tot = gdf["Remuneração"].sum()
            _fg_tot = gdf["FGTS"].sum()
            _ind_rem = fgts_v["base_fgts"].sum() if not fgts_v.empty else 0
            _ind_fg = fgts_v["deposito_fgts"].sum() if not fgts_v.empty else 0
            _n_lanc = len(fgts_v) if not fgts_v.empty else 0
            _n_cpf = fgts_v["cpf"].nunique() if not fgts_v.empty else 0
            _ok = abs(_ind_rem - _rem_tot) < 0.05 and abs(_ind_fg - _fg_tot) < 0.05
            _cls = "al-g" if _ok else "al-y"
            _ic = "✅" if _ok else "⚠️"
            st.markdown(
                f"<div class='{_cls}'>{_ic} <b>Prova de consistência:</b> os <b>{_n_lanc}</b> lançamentos "
                f"individuais de <b>{_n_cpf}</b> trabalhador(es) somam "
                f"<b>{brl(_ind_rem)}</b> de remuneração e <b>{brl(_ind_fg)}</b> de FGTS — "
                + ("igual aos totalizadores acima. O número fecha por dentro." if _ok else
                   "há diferença frente ao totalizador; verifique eventos retificados/excluídos.") +
                "</div>", unsafe_allow_html=True)
            st.caption("Para a confirmação final, use a aba ✅ Conferência (mês a mês) e bata cada "
                       "valor com o relatório do seu sistema de folha (Questor).")

        # destaque do movimento total
        if len(periodos) > 1:
            c0 = gdf.iloc[0]["Custo Total"]; cN = gdf.iloc[-1]["Custo Total"]
            dif = cN - c0; pct = (dif/c0*100) if c0 else 0
            cor = "#e03131" if dif > 0 else "#2f9e44"
            seta = "subiu" if dif > 0 else "caiu"
            st.markdown(
                f"<div class='al-b'>📈 De <b>{fper(periodos[0])}</b> a <b>{fper(periodos[-1])}</b>, "
                f"o custo da folha <b style='color:{cor}'>{seta} {abs(pct):.1f}%</b> "
                f"({brl(c0)} → {brl(cN)}, <b>{brl(dif)}</b>). "
                f"Soma do período: <b>{brl(gdf['Custo Total'].sum())}</b>.</div>",
                unsafe_allow_html=True)

        # ── FATURAMENTO × FOLHA (quanto da receita vai para a folha) ─────────
        st.divider()
        st.markdown("#### 🧾 Faturamento × Folha")
        st.caption("Digite o faturamento (receita bruta) de cada mês para ver quanto da receita "
                   "vai para a folha. Esse é um dos indicadores que o gestor mais valoriza. "
                   "O dado é informado por você — não vem do eSocial.")
        editor_faturamento(list(periodos), "editor_fat")

        custos_l = list(gdf["Custo Total"]); remuns_l = list(gdf["Remuneração"])
        fat_tot = sum(st.session_state.fat_por_comp.get(p, 0) for p in periodos)
        if fat_tot > 0:
            res = []
            for i, p in enumerate(periodos):
                fat = st.session_state.fat_por_comp.get(p, 0)
                custo = custos_l[i]
                res.append({"Competência": fper(p), "Faturamento": fat,
                            "Gasto com Folha + Encargos": custo,
                            "% do Faturamento": (custo/fat*100 if fat else None)})
            rdf = pd.DataFrame(res)
            st.dataframe(fmt_df(rdf, money=["Faturamento","Gasto com Folha + Encargos"],
                                pct=["% do Faturamento"]),
                         use_container_width=True, hide_index=True)
            # KPIs consolidados do período
            custo_tot_p = sum(custos_l); pct_custo = custo_tot_p/fat_tot*100
            k = st.columns(3)
            kpi(k[0], brl(fat_tot), "Faturamento do período")
            kpi(k[1], brl(custo_tot_p), "Gasto com folha + encargos")
            kpi(k[2], f"{pct_custo:.1f}%".replace(".", ","), "% do faturamento", "folha + encargos", "n")
            # leitura do indicador
            sobra = 100 - pct_custo
            cor = "#b03a2e" if pct_custo >= 50 else ("#b9770e" if pct_custo >= 35 else "#2f7a4d")
            st.markdown(
                f"<div class='al-b'>💡 <b>Leitura:</b> de cada R$ 100,00 faturados, "
                f"<b style='color:{cor}'>R$ {pct_custo:.2f}</b>".replace(".", ",") +
                f" vão para o custo total da folha (salários + encargos), sobrando "
                f"<b>R$ {sobra:.2f}</b>".replace(".", ",") +
                " para as demais despesas, impostos e o lucro. "
                "Acompanhe esse percentual mês a mês: se ele sobe sem o faturamento acompanhar, "
                "a folha está pesando mais na operação.</div>", unsafe_allow_html=True)
            # nota do CPP: está no custo para dar noção do gasto, mas já vem dentro do DAS
            _cpp_per = sum(cpp_de(p) for p in periodos)
            if _cpp_per > 0:
                _est_txt = " (estimado)" if any(cpp_estimado(p) for p in periodos) else ""
                st.markdown(
                    f"<div class='al-y'>&#8505;&#65039; <b>Sobre o CPP{_est_txt} incluido acima ({brl(_cpp_per)}):</b> "
                    "ele esta somado no &ldquo;Gasto com Folha + Encargos&rdquo; para voce ter a <b>nocao do custo "
                    "real de pessoal</b>. Mas atencao: no Simples esse CPP <b>ja e pago dentro do DAS</b> "
                    "(imposto sobre o faturamento) &mdash; <b>nao e um gasto a mais por fora</b>. Ou seja, ao "
                    "olhar a &ldquo;sobra para impostos&rdquo;, lembre que a parte do DAS referente ao CPP ja esta "
                    "contabilizada aqui na folha.</div>", unsafe_allow_html=True)
        else:
            st.info("Digite o faturamento de pelo menos um mês acima para calcular o "
                    "percentual da receita que vai para a folha.")

        # ── O QUE GASTOU (composição da remuneração por mês via rubricas) ────
        st.divider()
        st.markdown("#### O que gastou (composição por tipo de verba)")
        st.caption("Agrupado pelas rubricas do eSocial (S-1200): proventos por natureza. "
                   "Mostra onde o dinheiro foi — salários, horas extras, adicionais, férias, 13º, etc.")
        rmap_g = (rub.drop_duplicates("cod_rubr").set_index("cod_rubr") if not rub.empty else pd.DataFrame())
        def _grupo(cod):
            # classifica a rubrica num grupo de gasto legível
            nm = ""
            if not rmap_g.empty and cod in rmap_g.index: nm = str(rmap_g.loc[cod,"desc"]).upper()
            elif cod in ep.RUBRICAS_PADRAO: nm = ep.RUBRICAS_PADRAO[cod][1].upper()
            # ⚠️ NÃO são custo extra: adiantamento (antecipação do próprio salário,
            # descontado depois) e reembolsáveis pela Previdência (maternidade/sal.-família).
            if "ADIANTAMENTO" in nm or "ANTECIPA" in nm: return "Adiantamento (antecipação — não é custo extra)"
            if "MATERNID" in nm or "FAMILIA" in nm or "FAMÍLIA" in nm: return "Reembolsável pela Previdência"
            if cod in {"1","33"} or "SALARIO" in nm or "SALÁRIO" in nm or "SALDO" in nm: return "Salários"
            if "EXTRA" in nm or "HRS.EXT" in nm or cod in {"35","36","37"}: return "Horas Extras"
            if "FERIAS" in nm or "FÉRIAS" in nm or "ABONO" in nm or "1/3" in nm: return "Férias / Abono"
            if "13" in nm or "DECIMO" in nm or "DÉCIMO" in nm: return "13º Salário"
            if "PERICUL" in nm or "INSALUB" in nm or "NOTURN" in nm or "ADICIONAL" in nm: return "Adicionais"
            if "PREMIO" in nm or "PRÊMIO" in nm or "GRATIF" in nm or "BONUS" in nm: return "Prêmios / Gratif."
            if "DSR" in nm or "REPOUSO" in nm: return "DSR"
            if "MATERNID" in nm or "LIC" in nm or "AUXILIO" in nm or "AUXÍLIO" in nm: return "Licenças / Auxílios"
            # classifica desconto/informativa: não entra em 'gasto provento'
            tp = str(rmap_g.loc[cod,"tipo"]) if (not rmap_g.empty and cod in rmap_g.index) else ""
            cat = ep.RUBRICAS_PADRAO.get(cod, ("?",""))[0]
            if tp == "2" or cat == "D": return None      # desconto
            if tp in ("3","4") or cat in ("I",): return None  # informativa
            return "Outros Proventos"
        # monta {grupo: {competência: valor}}
        comp_grupo = {}
        for _, row in rem.iterrows():
            p = row.get("per_apur")
            if p not in periodos: continue
            for rr2 in row.get("rubricas", []) or []:
                g = _grupo(rr2["cod_rubr"])
                if not g: continue
                comp_grupo.setdefault(g, {}).setdefault(p, 0.0)
                comp_grupo[g][p] += rr2.get("valor", 0)
        if comp_grupo:
            rows2 = []
            for g, perv in comp_grupo.items():
                linha = {"Tipo de Verba": g}
                tot = 0
                for p in periodos:
                    v = perv.get(p, 0); linha[fper(p)] = v; tot += v
                linha["Total"] = tot
                rows2.append(linha)
            cdf = pd.DataFrame(rows2).sort_values("Total", ascending=False)
            st.dataframe(fmt_df(cdf, money=[c for c in cdf.columns if c != "Tipo de Verba"]),
                         use_container_width=True, hide_index=True)
            st.markdown(
                "<div class='al-y'>⚠️ <b>O total desta tabela NÃO é o custo mensal.</b> Aqui estão os "
                "proventos por tipo (para você ver <b>onde</b> o dinheiro foi). Duas linhas não são custo "
                "extra e por isso aparecem separadas: <b>Adiantamento</b> (é antecipação do próprio salário, "
                "descontado na mesma folha — contar junto dobraria o valor) e <b>Reembolsável pela Previdência</b> "
                "(maternidade/salário-família, devolvidos à empresa). O <b>gasto mensal confiável</b> é o "
                "<b>Custo Total</b> lá em cima (base FGTS + encargos), onde isso já está tratado.</div>",
                unsafe_allow_html=True)
        else:
            st.info("Sem detalhamento de rubricas (S-1200) para compor os gastos.")

# ═══════════════════════ SIMULADOR ══════════════════════════════════════════
with T[4]:
    render_simulador(periodos, fgts)

# ═══════════════════════ MOVIMENTAÇÃO ═══════════════════════════════════════
with T[5]:
    st.markdown("### Movimentação de Pessoal")
    st.caption("Admissões, desligamentos e reajustes que **ocorreram dentro do período anexado** — "
               "esses eventos são transmitidos no mês em que acontecem, então o quadro aqui é fiel ao período.")
    c = st.columns(4)
    kpi(c[0], n_adm, "Admissões")
    kpi(c[1], n_des, "Desligamentos")
    saldo = n_adm - n_des
    kpi(c[2], f"{saldo:+d}", "Saldo Líquido", "Crescendo" if saldo>0 else "Reduzindo" if saldo<0 else "Estável",
        "up" if saldo>0 else "down" if saldo<0 else "n")
    kpi(c[3], f"{turnover:.1f}%", "Turnover")

    st.divider()
    sub = st.tabs(["✅ Admissões", "❌ Desligamentos", "📈 Reajustes"])
    with sub[0]:
        if adm_v.empty:
            st.info("Nenhuma admissão no período.")
        else:
            a = adm_v.copy()
            a["Data"] = a["dt_adm"].apply(fdate)
            a["Contrato"] = a["tp_contr"].map(ep.TP_CONTR).fillna("—")
            a = a[["Data","matricula","nome","cargo","salario","horas_sem","Contrato"]]
            a.columns = ["Data","Matr.","Nome","Cargo","Salário","Horas/sem","Contrato"]
            st.dataframe(fmt_df(a.sort_values("Data", ascending=False), money=["Salário"]), use_container_width=True, hide_index=True)
            st.markdown("**Cargos mais contratados**")
            cc = adm_v.groupby("cargo").agg(Qtd=("cpf","count"), Sal=("salario","mean")).reset_index()
            cc = cc.sort_values("Qtd", ascending=False).rename(columns={"cargo":"Cargo","Sal":"Salário médio"})
            st.dataframe(fmt_df(cc, money=["Salário médio"]), use_container_width=True, hide_index=True)
    with sub[1]:
        if des_v.empty:
            st.info("Nenhum desligamento no período.")
        else:
            d = des_v.copy()
            badge = {"Alta":"🔴 Alta","Média":"🟡 Média","Baixa":"🟢 Baixa","—":"—"}
            d["Data"] = d["dt_deslig"].apply(fdate)
            d["Ônus"] = d["onus"].map(badge).fillna("—")
            d["Nome"] = d["cpf"].apply(nome_de)
            ds = d[["Data","matricula","Nome","motivo","Ônus","total_verbas_resc"]]
            ds.columns = ["Data","Matr.","Nome","Motivo","Ônus","Verbas Rescisórias"]
            st.dataframe(fmt_df(ds.sort_values("Data", ascending=False), money=["Verbas Rescisórias"]), use_container_width=True, hide_index=True)
            cL,cR = st.columns(2)
            with cL:
                st.markdown("**Motivos de saída**")
                mc = des_v["motivo"].value_counts().reset_index()
                mc.columns = ["Motivo","Qtd"]
                mc["%"] = (mc["Qtd"]/mc["Qtd"].sum()*100).round(1).astype(str)+"%"
                st.dataframe(mc, use_container_width=True, hide_index=True)
            with cR:
                st.markdown("**Custo de rescisão por ônus**")
                oc = des_v.groupby("onus").agg(Qtd=("cpf","count"), Verbas=("total_verbas_resc","sum")).reset_index()
                oc.columns = ["Ônus","Qtd","Total Verbas"]
                st.dataframe(fmt_df(oc, money=["Total Verbas"]), use_container_width=True, hide_index=True)
            tot = des_v["total_verbas_resc"].sum()
            if tot>0:
                st.markdown(f"<div class='al-b'>💰 Total de <b>verbas rescisórias</b> no período: <b>{brl(tot)}</b> (somatório das rubricas dos TRCTs no S-2299, já sem duplicar retificações).</div>", unsafe_allow_html=True)
    with sub[2]:
        if alt.empty:
            st.info("Nenhuma alteração contratual (S-2206) no período.")
        else:
            al = alt.copy()
            nomes = NOMES
            al["Nome"] = al["cpf"].apply(nome_de)
            al["Data"] = al["dt_alter"].apply(fdate)
            al = al[["Data","matricula","Nome","cargo","novo_salario"]]
            al.columns = ["Data","Matr.","Nome","Cargo","Novo Salário"]
            st.dataframe(fmt_df(al.sort_values("Data", ascending=False), money=["Novo Salário"]), use_container_width=True, hide_index=True)
            st.caption(f"{len(alt)} alterações contratuais (reajustes/mudança de cargo) registradas.")

# ═══════════════════════ AFASTAMENTOS ═══════════════════════════════════════
with T[6]:
    st.markdown("### Afastamentos e Absenteísmo")
    st.caption("Afastamentos (S-2230) iniciados/informados **no período anexado**. Afastamentos "
               "começados antes só aparecem se o evento estiver entre os arquivos.")
    if afa.empty:
        st.info("Nenhum afastamento (S-2230) encontrado.")
    else:
        afa["_ini"] = afa["dt_ini"].apply(ep._parse_date)
        afa["ativo"] = afa["_fim"].apply(lambda d: bool(d and d >= hoje))
        # taxa de absenteísmo: dias perdidos / (func × dias úteis aprox)
        dias_perdidos = int(afa["dias"].sum())
        c = st.columns(4)
        kpi(c[0], int(afa["ativo"].sum()), "Afastados agora")
        kpi(c[1], len(afa), "Ocorrências totais")
        kpi(c[2], dias_perdidos, "Dias perdidos (total)")
        if n_func and len(periodos):
            abs_pct = dias_perdidos / (n_func * 30 * len(periodos)) * 100
            kpi(c[3], f"{abs_pct:.1f}%", "Absenteísmo aprox.", "dias perdidos/disponíveis")

        st.divider()
        sub = st.tabs(["🔴 Ativos agora","📋 Histórico","📊 Por motivo"])
        with sub[0]:
            at = afa[afa["ativo"]]
            if at.empty:
                st.success("✅ Nenhum funcionário afastado nesta data.")
            else:
                t = at.copy()
                t["Nome"] = t["cpf"].apply(nome_de)
                t["Início"] = t["dt_ini"].apply(fdate)
                t["Término prev."] = t["dt_fim"].apply(fdate)
                t["Dias corridos"] = t["_ini"].apply(lambda d: (hoje-d).days if d else 0)
                t = t[["matricula","Nome","Início","Término prev.","Dias corridos","motivo"]]
                t.columns = ["Matr.","Nome","Início","Término prev.","Dias corridos","Motivo"]
                st.dataframe(t, use_container_width=True, hide_index=True)
        with sub[1]:
            h = afa.copy()
            h["Nome"] = h["cpf"].apply(nome_de)
            h["Início"] = h["dt_ini"].apply(fdate); h["Término"] = h["dt_fim"].apply(fdate)
            h = h[["matricula","Nome","Início","Término","dias","motivo"]]
            h.columns = ["Matr.","Nome","Início","Término","Dias","Motivo"]
            st.dataframe(h.sort_values("Início", ascending=False), use_container_width=True, hide_index=True)
        with sub[2]:
            m = afa.groupby("motivo").agg(Ocorrências=("dias","count"), Dias=("dias","sum")).reset_index()
            m = m.sort_values("Ocorrências", ascending=False).rename(columns={"motivo":"Motivo","Dias":"Total de dias"})
            _tot_oc = m["Ocorrências"].sum() or 1
            m["Participação"] = m["Ocorrências"] / _tot_oc * 100
            st.dataframe(m, use_container_width=True, hide_index=True, column_config={
                "Participação": st.column_config.ProgressColumn(
                    "Participação", format="%.1f%%", min_value=0.0, max_value=100.0)})

    # ── EXAMES OCUPACIONAIS (ASO / S-2220) ────────────────────────────────────
    st.divider()
    st.markdown("### 🩺 Exames Ocupacionais (ASO)")
    st.caption("Atestados de Saúde Ocupacional do eSocial (S-2220) — obrigação da NR-7. "
               "Acompanhe exames realizados e resultados (apto/inapto).")
    if exames.empty:
        st.info("Nenhum exame ocupacional (S-2220) nos arquivos.")
    else:
        ex = exames.copy()
        nomes = NOMES
        ex["Nome"] = ex["cpf"].apply(nome_de)
        c = st.columns(4)
        kpi(c[0], len(ex), "Exames no período")
        n_inapto = (ex["res_cod"]=="2").sum()
        kpi(c[1], int(n_inapto), "Inaptos", "⚠️ atenção" if n_inapto else "", "down" if n_inapto else "n")
        n_peri = (ex["tp_cod"]=="1").sum()
        kpi(c[2], int(n_peri), "Periódicos")
        n_adm_ex = (ex["tp_cod"]=="0").sum()
        kpi(c[3], int(n_adm_ex), "Admissionais")
        sh = ex.copy()
        sh["Data ASO"] = sh["dt_aso"].apply(fdate)
        sh["Médico"] = sh["medico"].str[:35]
        cols = ["Data ASO","matricula","Nome","tp_exame","resultado","Médico"]
        sh = sh[cols].rename(columns={"matricula":"Matr.","tp_exame":"Tipo","resultado":"Resultado"})
        st.dataframe(sh.sort_values("Data ASO", ascending=False), use_container_width=True, hide_index=True)
        if n_inapto:
            st.markdown(f"<div class='al-r'>⚠️ <b>{int(n_inapto)} resultado(s) INAPTO</b> — "
                        f"requer acompanhamento médico e eventual readaptação.</div>", unsafe_allow_html=True)
        st.caption("💡 O exame periódico tem prazo de validade (NR-7). Anexe os ZIPs de mais "
                   "meses para acompanhar quais funcionários estão com exame a vencer.")

# ═══════════════════════ FICHA INDIVIDUAL ═══════════════════════════════════
with T[7]:
    st.markdown("### 🔎 Consultar Funcionário")
    st.caption("Busque por nome, CPF ou matrícula e veja TUDO que o eSocial tem sobre o "
               "funcionário: cadastro, férias, folha mês a mês, holerite, encargos, "
               "afastamentos, exames, dependentes e desligamento.")
    # monta índice de funcionários (todos os CPFs vistos em qualquer evento)
    mat_por_cpf = {}
    for _df in (adm, inss):
        if not _df.empty and "matricula" in _df.columns:
            for _, r in _df.iterrows():
                if r.get("matricula"): mat_por_cpf.setdefault(r["cpf"], r["matricula"])
    todos_cpf = set()
    for _df in (inss, fgts, pag, adm, des):
        if not _df.empty and "cpf" in _df.columns:
            todos_cpf |= set(_df["cpf"].dropna().unique())
    def _label(c):
        nm = NOMES.get(c); mat = mat_por_cpf.get(c, "")
        base = nm if nm else f"CPF {mask_cpf(c)}"
        return f"{base}  ·  Matr. {mat}" if mat else base
    opcoes = sorted(todos_cpf, key=lambda c: (NOMES.get(c) or f"zzz{c}"))
    if not opcoes:
        st.info("Sem funcionários para exibir.")
    else:
        sel_cpf = st.selectbox("Funcionário", options=opcoes, format_func=_label,
                               help="Digite para filtrar por nome, CPF ou matrícula.")
        ainfo = adm[adm["cpf"]==sel_cpf].iloc[0].to_dict() if (not adm.empty and (adm["cpf"]==sel_cpf).any()) else {}
        mat = ainfo.get("matricula") or mat_por_cpf.get(sel_cpf, "—")
        nome_f = NOMES.get(sel_cpf) or ainfo.get("nome") or "(nome não consta no eSocial)"

        # cabeçalho do funcionário
        st.markdown(
            f"<div style='background:linear-gradient(100deg,#1c3d5a,#2e5b8a);color:#fff;"
            f"border-radius:10px;padding:14px 20px;margin-bottom:10px'>"
            f"<div style='font-size:20px;font-weight:800'>{nome_f}</div>"
            f"<div style='opacity:.85;font-size:13px'>Matrícula {mat} · CPF {mask_cpf(sel_cpf)}"
            f"{' · ' + ainfo.get('cargo','') if ainfo.get('cargo') else ''}</div></div>",
            unsafe_allow_html=True)

        # ── CADASTRO + FÉRIAS ────────────────────────────────────────────────
        cL, cR = st.columns([1, 1])
        with cL:
            idade = ep.idade(ainfo.get("dt_nasc"), hoje)
            linhas = [
                ("Cargo", ainfo.get("cargo") or "—"),
                ("CBO", ainfo.get("cbo") or "—"),
                ("Categoria", ep.CATEGORIA.get(ainfo.get("cod_categ",""), ainfo.get("cod_categ","—"))),
                ("Admissão", fdate(ainfo.get("dt_adm")) or "—"),
                ("Nascimento", f"{fdate(ainfo.get('dt_nasc'))} ({idade} anos)" if idade else "—"),
                ("Sexo", ep.SEXO.get(ainfo.get("sexo",""), "—")),
                ("Raça/Cor", ep.RACA_COR.get(ainfo.get("raca_cor",""), "—")),
                ("Estado civil", ep.EST_CIVIL.get(ainfo.get("est_civil",""), "—")),
                ("Escolaridade", ep.GRAU_INSTR.get(ainfo.get("grau_instr",""), "—")),
                ("Salário admissão", brl(ainfo.get("salario",0)) if ainfo.get("salario") else "—"),
                ("Jornada", f"{ainfo.get('horas_sem','—')}h/sem" if ainfo.get("horas_sem") else "—"),
                ("Contrato", ep.TP_CONTR.get(ainfo.get("tp_contr",""), "—")),
                ("PCD", "Sim" if ainfo.get("pcd") else "Não"),
            ]
            rows = "".join(f"<tr><td style='color:#6b7785;padding:2px 0'>{k}</td>"
                           f"<td style='text-align:right;font-weight:600'>{v}</td></tr>" for k,v in linhas)
            st.markdown(f"<div class='box'><b>📋 Cadastro</b><table style='font-size:12.5px;width:100%;margin-top:6px'>{rows}</table></div>",
                        unsafe_allow_html=True)
        with cR:
            # FÉRIAS
            fer = ep.status_ferias(ainfo.get("dt_adm"), hoje) if ainfo.get("dt_adm") else None
            if fer:
                cls={"Vencida":"al-r","Crítico":"al-y","Atenção":"al-y","Em dia":"al-g","Adquirindo":"al-b"}.get(fer["status"],"al-b")
                venc=fer["vencimento"].strftime("%d/%m/%Y") if fer["vencimento"] else "—"
                st.markdown(f"<div class='{cls}'>🏖️ <b>Férias: {fer['status']}</b><br>"
                            f"Vence em {venc} · {fer['periodos_vencidos']} período(s) adquirido(s) · "
                            f"{fer['meses_casa']} meses de casa</div>", unsafe_allow_html=True)
            else:
                st.markdown("<div class='al-b'>🏖️ Férias: sem data de admissão no eSocial "
                            "(anexe o S-2200 deste funcionário para calcular).</div>", unsafe_allow_html=True)
            # DESLIGAMENTO
            dd = des[des["cpf"]==sel_cpf]
            if not dd.empty:
                d0 = dd.iloc[0]
                st.markdown(f"<div class='al-r'>❌ <b>Desligado em {fdate(d0['dt_deslig'])}</b><br>"
                            f"{d0['motivo']} · ônus {d0['onus']} · verbas {brl(d0['total_verbas_resc'])}</div>",
                            unsafe_allow_html=True)
            # AFASTAMENTOS
            af = afa[afa["cpf"]==sel_cpf]
            if not af.empty:
                txt = "<br>".join(f"{fdate(r['dt_ini'])}→{fdate(r['dt_fim'])} ({int(r['dias'])}d) · {r['motivo']}"
                                  for _, r in af.iterrows())
                st.markdown(f"<div class='al-y'>🏥 <b>Afastamentos ({len(af)})</b><br>{txt}</div>", unsafe_allow_html=True)
            # EXAMES ASO
            ex = exames[exames["cpf"]==sel_cpf] if not exames.empty else pd.DataFrame()
            if not ex.empty:
                txt = "<br>".join(f"{fdate(r['dt_aso'])} · {r['tp_exame']} · {r['resultado']}" for _,r in ex.iterrows())
                st.markdown(f"<div class='al-g'>🩺 <b>Exames ocupacionais ({len(ex)})</b><br>{txt}</div>", unsafe_allow_html=True)

        # ── HISTÓRICO DE FOLHA (todas as competências do funcionário) ────────
        # usa TODAS as competências em que o CPF aparece (não só as do filtro global)
        pers_func = sorted(set(
            list(inss[inss["cpf"]==sel_cpf]["per_apur"].dropna().unique()) +
            list(fgts[fgts["cpf"]==sel_cpf]["per_apur"].dropna().unique()) +
            list(pag[pag["cpf"]==sel_cpf]["per_apur"].dropna().unique()) +
            list(irrf[irrf["cpf"]==sel_cpf]["per_apur"].dropna().unique())))
        hist=[]
        for per in pers_func:
            ii=inss[(inss["cpf"]==sel_cpf)&(inss["per_apur"]==per)]
            gg=fgts[(fgts["cpf"]==sel_cpf)&(fgts["per_apur"]==per)]
            pp=pag[(pag["cpf"]==sel_cpf)&(pag["per_apur"]==per)]
            rr=irrf[(irrf["cpf"]==sel_cpf)&(irrf["per_apur"]==per)]
            hist.append({"Competência":fper(per),
                "Remuneração":gg["base_fgts"].sum() if not gg.empty else 0,
                "INSS":ii["inss_emp"].sum() if not ii.empty else 0,
                "FGTS":gg["deposito_fgts"].sum() if not gg.empty else 0,
                "IRRF":rr["irrf"].sum() if not rr.empty else 0,
                "Líquido":pp["vr_liquido"].sum() if not pp.empty else 0})
        if hist:
            st.markdown("**💵 Folha mês a mês** (todas as competências do funcionário nos arquivos)")
            hdf=pd.DataFrame(hist)
            st.dataframe(fmt_df(hdf, money=["Remuneração","INSS","FGTS","IRRF","Líquido"]), use_container_width=True, hide_index=True)
        else:
            st.info("Este CPF não tem lançamentos de folha (INSS/FGTS/líquido) nos arquivos "
                    "anexados — pode aparecer apenas como dependente de outro funcionário, "
                    "ou em competências não incluídas. Anexe mais meses se necessário.")

        # ── HOLERITE (rubricas) por competência ──────────────────────────────
        rsel = rem[rem["cpf"]==sel_cpf] if not rem.empty else pd.DataFrame()
        if not rsel.empty:
            rmap_f = (rub.drop_duplicates("cod_rubr").set_index("cod_rubr") if not rub.empty else pd.DataFrame())
            def _nrub(c):
                if not rmap_f.empty and c in rmap_f.index: return rmap_f.loc[c,"desc"]
                return ep.RUBRICAS_PADRAO.get(c,("?",f"Rubrica {c}"))[1]
            comps_f = sorted(rsel["per_apur"].dropna().unique())
            # competências que aparecem na folha mas NÃO têm holerite (S-1200) anexado
            sem_holerite = [p for p in pers_func if p not in comps_f]
            if sem_holerite:
                falt = ", ".join(fper(p) for p in sem_holerite)
                st.markdown(
                    f"<div class='al-y'>📄 <b>Holerite indisponível para: {falt}.</b><br>"
                    "O detalhamento das rubricas vem do evento <b>S-1200</b>, que no eSocial "
                    "é entregue no pacote do <b>mês seguinte</b> à competência. Os totalizadores "
                    "(base INSS/FGTS, líquido) já fecharam e aparecem na folha acima, mas as "
                    "rubricas detalhadas só ficam disponíveis ao anexar o ZIP do mês posterior.</div>",
                    unsafe_allow_html=True)
            comp_h = st.selectbox("Holerite — competência", comps_f, format_func=fper, key="holerite_comp")
            linhas_h=[]
            for _, row in rsel[rsel["per_apur"]==comp_h].iterrows():
                for rr2 in row.get("rubricas",[]) or []:
                    linhas_h.append({"Cód.":rr2["cod_rubr"],"Rubrica":_nrub(rr2["cod_rubr"]),
                                     "Ref.":rr2.get("qtd",0) or "","Valor":rr2.get("valor",0)})
            if linhas_h:
                hh=pd.DataFrame(linhas_h)
                st.dataframe(fmt_df(hh, money=["Valor"]), use_container_width=True, hide_index=True)

        # ── DEPENDENTES ──────────────────────────────────────────────────────
        deps=[]
        for _, r in (irrf[irrf["cpf"]==sel_cpf]).iterrows():
            for d in r.get("dependentes",[]) or []: deps.append(d)
        if deps:
            st.markdown("**👨‍👩‍👧 Dependentes**")
            ddf=pd.DataFrame(deps).drop_duplicates()
            if "dt_nasc" in ddf.columns: ddf["Nascimento"]=ddf["dt_nasc"].apply(fdate)
            cols=[c for c in ["nome","Nascimento","dep_irrf"] if c in ddf.columns]
            st.dataframe(ddf[cols].rename(columns={"nome":"Nome","dep_irrf":"Dep. IRRF"}),
                         use_container_width=True, hide_index=True)

        # ── REAJUSTES ────────────────────────────────────────────────────────
        rj = alt[alt["cpf"]==sel_cpf] if not alt.empty else pd.DataFrame()
        if not rj.empty:
            st.markdown("**📈 Alterações contratuais (reajustes)**")
            rjs = rj.copy()
            rjs["Data"]=rjs["dt_alter"].apply(fdate)
            st.dataframe(fmt_df(rjs[["Data","cargo","novo_salario"]].rename(
                columns={"cargo":"Cargo","novo_salario":"Novo Salário"}), money=["Novo Salário"]),
                use_container_width=True, hide_index=True)

# ═══════════════════════ CONFERÊNCIA ════════════════════════════════════════
with T[8]:
    st.markdown("### Conferência XML × Sistema de Folha")
    st.caption("Valores oficiais extraídos do eSocial para os meses selecionados. "
               "Digite ao lado os valores do seu sistema de folha (Questor, Domínio, etc.) "
               "e o app mostra automaticamente se bate. Funciona com 1 mês ou vários somados.")
    if True:
        # itens de conferência para um conjunto de competências
        def _conf_itens(pers):
            _in = inss[inss["per_apur"].isin(pers)] if not inss.empty else inss
            _fg = fgts[fgts["per_apur"].isin(pers)] if not fgts.empty else fgts
            _ir = irrf[irrf["per_apur"].isin(pers)] if not irrf.empty else irrf
            _pg = pag[pag["per_apur"].isin(pers)] if not pag.empty else pag
            _um = pers[-1] if pers else None
            _nf = inss[inss["per_apur"]==_um]["cpf"].nunique() if (_um and not inss.empty) else 0
            _nd = int(_ir["n_dependentes"].sum()) if not _ir.empty else 0
            return [
                ("Funcionários", float(_nf), "S-5001", f"Saldo de {fper(_um, True)} — não soma admissões"),
                ("Base INSS", float(_in["base_inss"].sum()) if not _in.empty else 0, "S-5001", "Salário de contribuição (tp11)"),
                ("INSS descontado (empregado)", float(_in["inss_emp"].sum()) if not _in.empty else 0, "S-5001", "vrCpSeg — desconto do segurado"),
                ("Base FGTS", float(_fg["base_fgts"].sum()) if not _fg.empty else 0, "S-5003", "remFGTS"),
                ("FGTS depósito (8%)", float(_fg["deposito_fgts"].sum()) if not _fg.empty else 0, "S-5003", "dpsFGTS (inclui rescisões)"),
                ("IRRF retido", float(_ir["irrf"].sum()) if not _ir.empty else 0, "S-5002", "vlrCRMen"),
                ("Dependentes IRRF", float(_nd), "S-5002", "Total de dependentes"),
                ("Líquido pago", float(_pg["vr_liquido"].sum()) if not _pg.empty else 0, "S-1210", "Soma dos pagamentos líquidos"),
            ]

        # escolha do analista: consolidado ou mês a mês (quando há vários meses)
        if per_sel is None and len(periodos) > 1:
            _modo = st.radio("Como conferir?",
                             ["📊 Consolidado (soma do período)", "📅 Mês a mês"],
                             horizontal=True, key="conf_modo")
            if _modo.startswith("📅"):
                _mes = st.selectbox("Mês para conferir", periodos,
                                    format_func=lambda p: fper(p, True), key="conf_mes")
                pers_conf = [_mes]; _conf_tok = _mes
                st.markdown(f"#### Conferindo: **{fper(_mes, True)}** (mês isolado)")
                st.caption("Valores deste mês — compare com o relatório MENSAL do seu sistema de folha.")
            else:
                pers_conf = list(periodos); _conf_tok = "consol"
                st.markdown(f"#### Conferindo: **{len(periodos)} meses somados** "
                            f"({', '.join(fper(p) for p in periodos)})")
                st.caption(f"⚠️ Valores monetários = SOMA do período. Exceção: **Funcionários** é o "
                           f"SALDO do último mês ({fper(periodos[-1], True)}), não a soma das admissões.")
        else:
            pers_conf = list(periodos); _conf_tok = "single"
            st.markdown(f"#### Conferindo: **{fper(_ult, True) if _ult else '—'}**")

        itens = _conf_itens(pers_conf)
        st.markdown("Preencha a coluna **Seu sistema** com os valores do relatório do seu software:")
        c0, c1, c2, c3 = st.columns([2.4, 1.4, 1.4, 1.4])
        c0.markdown("**Indicador**")
        c1.markdown("**XML (eSocial)**")
        c2.markdown("**Seu sistema**")
        c3.markdown("**Diferença**")
        for i, (nome, val_xml, fonte, desc) in enumerate(itens):
            cc0, cc1, cc2, cc3 = st.columns([2.4, 1.4, 1.4, 1.4])
            cc0.markdown(f"{nome}  \n<small style='color:#8a97a6'>{fonte} · {desc}</small>",
                         unsafe_allow_html=True)
            is_money = nome not in ("Funcionários", "Dependentes IRRF")
            cc1.markdown(f"<div style='padding-top:6px'><b>{brl(val_xml) if is_money else int(val_xml)}</b></div>",
                         unsafe_allow_html=True)
            entrada = cc2.number_input(nome, value=0.0, step=0.01, format="%.2f",
                                       key=f"conf_{_conf_tok}_{i}", label_visibility="collapsed")
            if entrada and entrada != 0:
                dif = val_xml - entrada
                pct = (dif / entrada * 100) if entrada else 0
                if abs(dif) < 0.05:
                    cc3.markdown("<div style='padding-top:6px;color:#2f7a4d'><b>✓ bate</b></div>",
                                 unsafe_allow_html=True)
                else:
                    cor = "#b03a2e" if abs(pct) > 1 else "#b9770e"
                    s = brl(dif) if is_money else f"{int(dif):+d}"
                    cc3.markdown(f"<div style='padding-top:6px;color:{cor}'><b>{s}</b> "
                                 f"<small>({pct:+.1f}%)</small></div>", unsafe_allow_html=True)
            else:
                cc3.markdown("<div style='padding-top:6px;color:#aaa'>—</div>", unsafe_allow_html=True)

        st.divider()
        st.markdown(
            "<div class='al-b'>💡 <b>Como interpretar:</b> INSS, IRRF e nº de funcionários "
            "devem bater exatamente. A <b>Base FGTS</b> e o <b>FGTS</b> podem diferir um pouco "
            "porque alguns sistemas separam FGTS normal (GFIP) de rescisão (GRRF) — o eSocial "
            "junta tudo. O <b>Líquido</b> pode diferir se o sistema separa adiantamento da folha. "
            "Diferenças acima de 1% merecem investigação.</div>", unsafe_allow_html=True)

# ═══════════════════════ RELATÓRIO ══════════════════════════════════════════
with T[9]:
    st.markdown("### Gerar Relatório para o Cliente")
    st.caption("Relatório gerencial consolidado em PDF — pronto para enviar ao gestor do cliente.")

    def build_ctx():
        # competências do PDF = as selecionadas no multiselect
        pers = periodos
        # 1) resumo por competência
        resumo = []
        for per in pers:
            ii=inss[inss["per_apur"]==per]; gg=fgts[fgts["per_apur"]==per]
            rr=irrf[irrf["per_apur"]==per]; pp=pag[pag["per_apur"]==per]
            remun_p = gg["base_fgts"].sum() if not gg.empty else 0
            pat_p = inss_per.get(per,{}).get("patronal",0)
            cpp_p = cpp_de(per)
            fgts_p = gg["deposito_fgts"].sum() if not gg.empty else 0
            resumo.append({"comp":per,"func":ii["cpf"].nunique() if not ii.empty else 0,
                "remun":remun_p,"liq":pp["vr_liquido"].sum() if not pp.empty else 0,
                "inss_emp":ii["inss_emp"].sum() if not ii.empty else 0,"inss_pat":pat_p+cpp_p,
                "fgts":fgts_p,"irrf":rr["irrf"].sum() if not rr.empty else 0,
                "custo":remun_p+pat_p+cpp_p+fgts_p})
        # 2) conferência por evento (cada competência)
        conf = []
        for per in pers:
            ii=inss[inss["per_apur"]==per]; gg=fgts[fgts["per_apur"]==per]
            rr=irrf[irrf["per_apur"]==per]; pp=pag[pag["per_apur"]==per]
            conf.append({"comp":per,"itens":[
                ("Funcionários", str(ii["cpf"].nunique() if not ii.empty else 0), "S-5001"),
                ("Base INSS", brl(ii["base_inss"].sum() if not ii.empty else 0), "S-5001 tp11"),
                ("INSS descontado (empregado)", brl(ii["inss_emp"].sum() if not ii.empty else 0), "S-5001 vrCpSeg"),
                ("Base FGTS", brl(gg["base_fgts"].sum() if not gg.empty else 0), "S-5003 remFGTS"),
                ("FGTS depósito", brl(gg["deposito_fgts"].sum() if not gg.empty else 0), "S-5003 dpsFGTS"),
                ("IRRF retido", brl(rr["irrf"].sum() if not rr.empty else 0), "S-5002 vlrCRMen"),
                ("Dependentes IRRF", str(int(rr["n_dependentes"].sum()) if not rr.empty else 0), "S-5002"),
                ("Líquido pago", brl(pp["vr_liquido"].sum() if not pp.empty else 0), "S-1210 vrLiq"),
            ]})
        # 3) encargos detalhados
        enc = []
        for per in pers:
            ii=inss[inss["per_apur"]==per]; gg=fgts[fgts["per_apur"]==per]; rr=irrf[irrf["per_apur"]==per]
            enc.append({"comp":per,
                "inss_m":ii["tp21_i0"].sum() if not ii.empty else 0,
                "inss_13":ii["tp21_i1"].sum() if not ii.empty else 0,
                "fgts_m":gg["fgts_mensal"].sum() if (not gg.empty and "fgts_mensal" in gg.columns) else 0,
                "fgts_13":gg["fgts_13"].sum() if (not gg.empty and "fgts_13" in gg.columns) else 0,
                "irrf_m":rr["irrf"].sum() if not rr.empty else 0,
                "irrf_13":rr["irrf_13"].sum() if (not rr.empty and "irrf_13" in rr.columns) else 0})
        guias = {"inss": sum(r["inss_emp"]+r["inss_pat"] for r in resumo),
                 "fgts": sum(r["fgts"] for r in resumo),
                 "irrf": sum(r["irrf"] for r in resumo)}
        # 4) verbas (consolidado das competências selecionadas)
        rem_sel = rem[rem["per_apur"].isin(pers)] if not rem.empty else rem
        verbas = None
        linhas=[]
        for _, row in rem_sel.iterrows():
            for rrub in row.get("rubricas",[]) or []:
                linhas.append({"cod":rrub["cod_rubr"],"valor":rrub["valor"]})
        if linhas:
            import pandas as _pd
            rdf=_pd.DataFrame(linhas)
            rmap=rub.drop_duplicates("cod_rubr").set_index("cod_rubr") if not rub.empty else _pd.DataFrame()
            def _info(c):
                if not rmap.empty and c in rmap.index:
                    tp=str(rmap.loc[c,"tipo"] or ""); nome=rmap.loc[c,"desc"]
                    if tp=="1": return "P",nome
                    if tp=="2": return "D",nome
                    if tp in ("3","4"): return "I",nome
                    return "P",nome
                if c in ep.RUBRICAS_PADRAO: return ep.RUBRICAS_PADRAO[c]
                return "?",f"Rubrica {c}"
            agg=rdf.groupby("cod")["valor"].sum().reset_index()
            prov=[]; vant=[]; desc=[]; info=[]
            for _,r in agg.iterrows():
                cat,nome=_info(r["cod"])
                tup=(r["cod"],nome,r["valor"])
                if cat=="P": prov.append(tup)
                elif cat=="B": vant.append(tup)
                elif cat=="D": desc.append(tup)
                elif cat in ("I","A"): info.append(tup)
            verbas={"proventos":prov,"vantagens":vant,"descontos":desc,"informativas":info,
                    "tot_prov":sum(x[2] for x in prov)+sum(x[2] for x in vant),
                    "tot_desc":sum(x[2] for x in desc)}
        # 5) custo por funcionário (consolidado das competências selecionadas)
        cfunc=[]
        if not inss.empty:
            iv2=inss[inss["per_apur"].isin(pers)]
            fv2=fgts[fgts["per_apur"].isin(pers)]
            bi=iv2.groupby(["cpf","matricula"]).agg(inss_emp=("inss_emp","sum")).reset_index()
            bf=fv2.groupby("cpf").agg(remun=("base_fgts","sum"),fgts=("deposito_fgts","sum")).reset_index()
            bd=bi.merge(bf,on="cpf",how="outer").fillna(0)
            nomes = NOMES
            bd["nome"]=bd["cpf"].apply(nome_de)
            bd["custo"]=bd["remun"]+bd["fgts"]
            bd=bd.sort_values("custo",ascending=False)
            cfunc=[{"matricula":r["matricula"],"nome":r["nome"],"remun":r["remun"],
                    "inss_emp":r["inss_emp"],"fgts":r["fgts"],"custo":r["custo"]} for _,r in bd.iterrows()]
        # 6) movimentação (filtrada pelas competências selecionadas)
        admr=[{"dt_adm":r.get("dt_adm"),"matricula":r.get("matricula",""),
               "nome":r.get("nome") or nome_de(r.get("cpf"), r.get("matricula","")),
               "cargo":r.get("cargo",""),"salario":r.get("salario",0)}
              for _,r in adm.iterrows() if str(r.get("dt_adm",""))[:7] in pers] if not adm.empty else []
        desr=[{"dt_deslig":r.get("dt_deslig"),"matricula":r.get("matricula",""),
               "nome":nome_de(r.get("cpf"), r.get("matricula","")),
               "motivo":r.get("motivo",""),
               "onus":r.get("onus",""),"verbas":r.get("total_verbas_resc",0)}
              for _,r in des.iterrows() if str(r.get("dt_deslig",""))[:7] in pers] if not des.empty else []
        # 7) afastamentos
        afr=[]
        if not afa.empty:
            mm=afa.groupby("motivo").agg(qtd=("dias","count"),dias=("dias","sum")).reset_index()
            afr=[{"motivo":r["motivo"],"qtd":int(r["qtd"]),"dias":r["dias"]} for _,r in mm.sort_values("qtd",ascending=False).iterrows()]
        # 8) demografia
        demo=None
        if not adm.empty:
            a=adm.copy()
            a["idade"]=a["dt_nasc"].apply(lambda s: ep.idade(s,hoje))
            a["Sexo"]=a["sexo"].map(ep.SEXO).fillna("Não inf.")
            a["Escol"]=a["grau_instr"].map(ep.GRAU_INSTR).fillna("Não inf.")
            import pandas as _pd
            fa=_pd.cut(a["idade"],bins=[0,24,34,44,54,200],labels=["até 24","25-34","35-44","45-54","55+"])
            demo={
                "sexo":list(a["Sexo"].value_counts().items()),
                "faixa":[(str(k),int(v)) for k,v in fa.value_counts().sort_index().items()],
                "escol":list(a["Escol"].value_counts().items()),
                "cargo":list(a["cargo"].value_counts().head(15).items()),
            }
        # 9) férias
        fer_rows=[]
        if not adm.empty:
            for _, r in adm.iterrows():
                fx=ep.status_ferias(r.get("dt_adm"),hoje)
                if not fx or fx["status"] not in ("Vencida","Crítico","Atenção"): continue
                fer_rows.append({"status":fx["status"],"matricula":r.get("matricula",""),
                    "nome":r.get("nome","") or f"Matr. {r.get('matricula','')}","dt_adm":r.get("dt_adm",""),
                    "vencimento":fx["vencimento"].strftime("%d/%m/%Y") if fx["vencimento"] else "—",
                    "situacao":(f"vencida há {abs(fx['dias_para_vencer'])}d" if fx["dias_para_vencer"]<0 else f"em {fx['dias_para_vencer']}d")})
            fer_rows.sort(key=lambda x:{"Vencida":0,"Crítico":1,"Atenção":2}.get(x["status"],3))
        # 10) faturamento × folha (informado pelo usuário, se houver)
        _fatc = st.session_state.get("fat_por_comp", {})
        _fat_total = sum(_fatc.get(r["comp"], 0) for r in resumo)
        faturamento = None
        if _fat_total > 0:
            _folha_total = sum(r["remun"] for r in resumo)
            _custo_total_p = sum(r["custo"] for r in resumo)
            faturamento = {
                "rows": [{"comp": r["comp"], "fat": _fatc.get(r["comp"], 0),
                          "folha": r["remun"], "custo": r["custo"]} for r in resumo],
                "total": _fat_total, "folha_total": _folha_total, "custo_total": _custo_total_p,
                "pct_folha": _folha_total/_fat_total*100,
                "pct_custo": _custo_total_p/_fat_total*100}
        return {"periodos_label":periodos_label,"empresa":empresa,"faturamento":faturamento,
            "cpp_faltando":cpp_faltando, "cnpj": D.get("_cnpj"),
            "cpp_total": sum(cpp_de(p) for p in pers),
            "cpp_estimado": any(cpp_estimado(p) for p in pers),
            "tem_patronal_real": tem_patronal,
            "emitido_em": hoje.strftime("%d/%m/%Y"),
            "regime":("INSS patronal apurado no eSocial" if tem_patronal else "Sem INSS patronal no eSocial (ex.: Simples Nacional)"),
            "resumo_competencias":resumo,"conferencia":conf,"encargos":enc,"guias":guias,
            "verbas":verbas,"custo_funcionarios":cfunc,"admissoes":admr,"desligamentos":desr,
            "afastamentos_resumo":afr,"demografia":demo,"ferias":fer_rows,
            "periodos":pers}

    cA, cB = st.columns(2)
    with cA:
        if st.button("📄 Gerar Relatório PDF", type="primary", use_container_width=True):
            with st.spinner("Montando relatório..."):
                pdf = rpdf.gerar(build_ctx(), empresa=empresa)
            _emp_fn = re.sub(r"[^\w \-]", "", (empresa or "").strip()).replace(" ", "-")[:40] or "Empresa"
            _cf = periodos[0] if len(periodos) == 1 else f"{periodos[0]}_a_{periodos[-1]}"
            st.download_button("⬇️ Baixar PDF", data=pdf,
                file_name=f"Relatorio-de-Folha_{_emp_fn}_{_cf}.pdf",
                mime="application/pdf", use_container_width=True)
            st.success("Relatório pronto!")
    with cB:
        xb = io.BytesIO()
        with pd.ExcelWriter(xb, engine="openpyxl") as w:
            def dump(df, nome, drop=()):
                if not df.empty:
                    df.drop(columns=[c for c in drop if c in df.columns], errors="ignore").to_excel(w, sheet_name=nome[:31], index=False)
            dump(adm, "Admissões", ["evento"])
            dump(des, "Desligamentos", ["nr_recibo","ind_retif"])
            dump(afa, "Afastamentos", ["_ini","_fim","ativo"])
            dump(alt, "Reajustes")
            if not inss.empty:
                dump(inss[["cpf","matricula","per_apur","base_inss","inss_emp","adic_peric","adic_insal"]], "Bases INSS")
            dump(fgts, "Bases FGTS")
            if not irrf.empty:
                dump(irrf[["cpf","per_apur","rend_tributavel","prev_oficial","irrf","n_dependentes"]], "IRRF")
            dump(pag, "Pagamentos")
            if not cs.empty: dump(cs, "Contrib Patronal")
        st.download_button("📊 Baixar Excel (dados completos)", data=xb.getvalue(),
            file_name=f"dados_folha_{datetime.now().strftime('%Y%m%d')}.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            use_container_width=True)

    st.divider()
    if D["_erros"]:
        with st.expander(f"⚠️ {len(D['_erros'])} avisos de parsing"):
            for e in D["_erros"][:30]: st.text(e)
    st.caption("Painel Gerencial de Folha · eSocial · Dados protegidos pela LGPD (Lei 13.709/2018)")
