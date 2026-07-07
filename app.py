# -*- coding: utf-8 -*-
"""
Painel Gerencial de Folha de Pagamento — eSocial
Departamento Pessoal · Contador de Padaria
"""
import io, re, os
from datetime import date, datetime
import pandas as pd
import streamlit as st

import esocial_parser as ep
import relatorio_pdf as rpdf

st.set_page_config(page_title="Análise de Folha × Nota de Serviço", page_icon="📋",
                   layout="wide", initial_sidebar_state="collapsed")

st.markdown("""
<style>
html, body, [class*="css"] { font-family:'Segoe UI','Inter',-apple-system,sans-serif; }
.block-container { padding-top:1.6rem; max-width:1480px; }

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
# SIDEBAR
# ─────────────────────────────────────────────────────────────────────────────
with st.sidebar:
    _logo_p = os.path.join(os.path.dirname(os.path.abspath(__file__)), "logo.png")
    if os.path.exists(_logo_p):
        st.image(_logo_p, use_container_width=True)
    else:
        st.markdown("<div style='font-weight:800;font-size:18px;color:#F5A623;letter-spacing:.03em'>"
                    "CONTADOR <span style='color:#c8860f'>DE PADARIAS</span></div>",
                    unsafe_allow_html=True)
    with st.expander("🖼️ Logo do escritório"):
        _lup = st.file_uploader("Enviar logo (PNG/JPG)", type=["png", "jpg", "jpeg"], key="logo_up")
        if _lup is not None:
            with open(_logo_p, "wb") as _lf:
                _lf.write(_lup.read())
            st.success("Logo salva! Aparece no painel e no PDF.")
            st.rerun()
        if os.path.exists(_logo_p) and st.button("Remover logo", use_container_width=True):
            os.remove(_logo_p); st.rerun()
    st.markdown("### 📋 Análise de Folha × Nota de Serviço")
    st.caption("eSocial · Departamento Pessoal")
    empresa = st.text_input("Nome do cliente / empresa", placeholder="Ex.: Padaria São João Ltda")
    mostrar_cpf = st.checkbox("🔓 Mostrar CPF completo", value=True,
                              help="O CPF está completo nos XMLs. Desmarque para mascarar (LGPD) "
                                   "ao compartilhar a tela.")
    st.divider()
    # ── controle de estado ─────────────────────────────────────────────────
    if "analise" not in st.session_state:
        st.session_state.analise = None
    if "upkey" not in st.session_state:
        st.session_state.upkey = 0

    nova = st.button("🔄 Nova análise (recomeçar)", use_container_width=True)
    # voltar ao HUB (trocar entre Simulador e Análise) quando já há dados
    if st.session_state.get("analise") is not None and st.session_state.get("modo"):
        if st.button("🏠 Início (Simulador / Análise)", use_container_width=True):
            st.session_state.modo = None
            st.rerun()

    if nova:
        # zera TUDO: dados, filtros, seleções, valores digitados — começa do zero
        _keep = st.session_state.get("upkey", 0) + 1
        for k in list(st.session_state.keys()):
            del st.session_state[k]
        st.session_state.analise = None
        st.session_state.upkey = _keep   # nova key reseta o file_uploader
        st.rerun()

    st.divider()
    with st.expander("ℹ️ Eventos lidos"):
        st.markdown("""
| Evento | Conteúdo |
|---|---|
| S-2200/2190 | Admissão / cadastro |
| S-2206 | Reajuste / cargo |
| S-2230 | Afastamentos |
| S-2240 | Insalubre/periculoso |
| S-2299 | Desligamento + rescisão |
| S-1200 | Rubricas da folha |
| S-1210 | Líquido pago |
| S-5001 | Bases INSS |
| S-5002 | IRRF + dependentes |
| S-5003 | Bases FGTS |
| S-5011 | Contribuição patronal |
""")

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

def render_simulador(meses, fgtsdf):
    st.divider()
    st.markdown("#### 🎯 Simulador — Quanto de nota emitir (planejar ANTES do PGDAS)")
    st.caption("Para a empresa de mão de obra (Simples) que emite nota de serviço à empresa "
               "principal. Escolha o mês, anexe o PGDAS do mês ANTERIOR (para a alíquota) e o "
               "app calcula a nota a emitir — e quanto dela vira DAS e CPP.")

    # ── 1) MÊS DA SIMULAÇÃO ──────────────────────────────────────────────────
    _sem_xml_meses = not meses
    if _sem_xml_meses:
        st.markdown("<div class='al-y'>⚠️ Nenhum mês completo no XML. Digite o mês manualmente e informe salários e FGTS abaixo.</div>",
                    unsafe_allow_html=True)
        import datetime
        _hoje = datetime.date.today()
        _mes_txt = st.text_input("📅 Competência (AAAA-MM)", value=f"{_hoje.year}-{_hoje.month-1:02d}",
                                 placeholder="Ex.: 2026-06", key="sim_mes_manual")
        mes = _mes_txt.strip() if re.match(r"^\d{4}-\d{2}$", _mes_txt.strip()) else None
        if not mes:
            st.info("Informe a competência no formato AAAA-MM (ex.: 2026-06).")
            return
    else:
        mes = st.selectbox("📅 Mês da simulação", meses, index=len(meses)-1,
                           format_func=lambda p: fper(p, True), key="sim_mes")
    gg = fgtsdf[fgtsdf["per_apur"] == mes] if (not fgtsdf.empty and not _sem_xml_meses) else (fgtsdf.iloc[0:0] if not fgtsdf.empty else fgtsdf)
    sal_xml = gg["base_fgts"].sum() if not gg.empty else 0
    fg_xml = gg["deposito_fgts"].sum() if not gg.empty else 0
    _tem_xml = (not _sem_xml_meses) and (sal_xml > 0 or fg_xml > 0)

    if _tem_xml:
        st.markdown(f"<div class='al-g'>✅ Folha de <b>{fper(mes, True)}</b> encontrada no XML: "
                    f"salários <b>{brl(sal_xml)}</b> + FGTS <b>{brl(fg_xml)}</b>.</div>", unsafe_allow_html=True)
    elif not _sem_xml_meses:
        st.markdown(f"<div class='al-r'>⚠️ Não há folha (S-5003) para <b>{fper(mes, True)}</b> no XML. "
                    "Informe os valores manualmente abaixo para simular mesmo assim.</div>",
                    unsafe_allow_html=True)

    _usar_manual = _sem_xml_meses or st.checkbox(
        "✏️ Informar valores manualmente (emergência — XML ainda não disponível)",
        value=not _tem_xml, key=f"sim_manual_{mes}")
    if _usar_manual:
        _mc1, _mc2 = st.columns(2)
        _sal_txt = _mc1.text_input("Salários — base FGTS (R$)",
                                   value="" if not _tem_xml else "",
                                   placeholder="Ex.: 175.000,00", key=f"sim_sal_{mes}")
        _fg_txt = _mc2.text_input("FGTS (R$)",
                                  value="" if not _tem_xml else "",
                                  placeholder="Ex.: 13.846,00", key=f"sim_fg_{mes}")
        sal = parse_brl_in(_sal_txt)
        fg = parse_brl_in(_fg_txt)
        _obs_sal = "digitado manualmente"
        _obs_fg = "digitado manualmente"
        if sal <= 0 and fg <= 0:
            st.info("Digite os salários e FGTS acima para calcular.")
            return
    else:
        if not _tem_xml:
            return
        sal, fg = sal_xml, fg_xml
        _obs_sal = "do XML (S-5003)"
        _obs_fg = "do XML (S-5003)"

    # ── 2) PGDAS DO MÊS ANTERIOR (alíquota + anexo + fatia da CPP) ────────────
    _ant = _mes_anterior(mes)
    st.markdown(f"📎 **Anexe o PGDAS de {fper(_ant, True) if _ant else 'um mês anterior'}** "
                "(o mês anterior ao da simulação) para detectar a alíquota efetiva e o Anexo:")
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
                st.session_state["cpp_ratio_ref"] = _r["cpp_ratio"]   # p/ estimar CPP de meses sem PGDAS
            if _r.get("segmentos"):
                st.session_state["sim_segmentos"] = _r["segmentos"]   # mix p/ distribuir a nota
            if _r.get("rbt12"):
                st.session_state["sim_rbt12"] = _r["rbt12"]           # p/ cálculo oficial do CPP
            if _r.get("nome"):
                st.session_state["empresa_pgdas"] = _r["nome"]        # razão social p/ relatório
            _av = "" if _r.get("competencia") == _ant else " <b>(atenção: não é o mês anterior)</b>"
            st.markdown(
                (f"<div class='al-g'>✅ PGDAS lido: <b>Anexo {_r.get('anexo') or '?'}</b> · "
                 f"alíquota efetiva <b>{_r['aliq_efetiva']:.2f}%</b> · CPP é "
                 f"<b>{(_r.get('cpp') or 0)/_r['das_total']*100:.0f}%</b> do DAS "
                 f"(ref. {fper(_r['competencia'], True) if _r.get('competencia') else '—'}{_av}).</div>"
                 ).replace(".", ",", 1), unsafe_allow_html=True)
        else:
            st.warning("Não consegui ler a alíquota nesse PDF. Informe manualmente abaixo.")

    _aliq_auto = st.session_state.get("sim_aliq")
    _anexo_det = st.session_state.get("sim_anexo", "")
    _cpp_share = st.session_state.get("sim_cpp_share")
    if _aliq_auto:
        st.markdown(
            (f"<div class='al-b'>📌 <b>Sobre a alíquota ({_aliq_auto:.2f}%):</b> ").replace(".", ",") +
            "vem do PGDAS do <b>mês anterior</b> (DAS ÷ receita) — a do mês simulado só sai no PGDAS "
            "dele, que ainda não existe. O RBT12 muda pouco de um mês para o outro, então é uma boa "
            "referência: <b>faturamento estável</b> → praticamente igual; <b>crescendo</b> → a real "
            "será um pouco maior, então suba a alíquota no campo abaixo.</div>",
            unsafe_allow_html=True)
    if _anexo_det:
        st.caption(f"Anexo detectado: **Anexo {_anexo_det}**")

    # ── 3) PARÂMETROS ────────────────────────────────────────────────────────
    sc1, sc2, sc3 = st.columns(3)
    aliq = sc1.number_input("Alíquota efetiva DAS (%)", min_value=0.0, max_value=30.0,
        value=round(_aliq_auto, 2) if _aliq_auto else 11.0, step=0.1,
        help="% do DAS sobre a nota. Vem do PGDAS anterior; muda mês a mês pelo RBT12.")
    margem = sc2.number_input("Margem de segurança (%)", min_value=0.0, max_value=50.0,
        value=10.0, step=1.0, help="Folga p/ lucro e imprevistos — evita faturar 'no osso'.")
    _desp_txt = sc3.text_input("Despesas gerais (R$/mês)", value="",
        help="Aluguel, contador, água/luz, material. Deixa a estrutura coerente p/ o Fisco. Ex.: 8000")
    desp_ger = parse_brl_in(_desp_txt)

    _div = 1 - aliq/100 - margem/100
    if _div <= 0:
        st.warning("Alíquota + margem somam 100% ou mais — ajuste os valores.")
        return

    # ── 4) CÁLCULO DO MÊS ─────────────────────────────────────────────────────
    custo_fora = sal + fg + desp_ger               # cobertos FORA do DAS
    nota = custo_fora / _div                        # nota a emitir
    das_est = nota * aliq/100                        # DAS que a nota gera
    cpp_est = das_est * _cpp_share if _cpp_share else None   # CPP dentro do DAS
    sobra = nota - custo_fora - das_est              # margem em R$

    st.markdown(f"##### 📋 Resultado para {fper(mes, True)}")
    st.caption("A nota a emitir é a SOMA de três partes: o custo a cobrir + o DAS que a nota gera "
               "+ a margem. A CPP NÃO é uma quarta parte — ela já está dentro do DAS.")
    _das_obs = (f"{aliq:.1f}% da nota · inclui a CPP".replace(".", ",") +
                (f" (~{brl(cpp_est)})" if cpp_est is not None else ""))
    linhas = [
        {"Item": "Salários (base FGTS)", "Valor": sal, "Observação": _obs_sal},
        {"Item": "FGTS (8%)", "Valor": fg, "Observação": _obs_fg},
    ]
    if desp_ger > 0:
        linhas.append({"Item": "Despesas gerais", "Valor": desp_ger, "Observação": "informado por você"})
    linhas += [
        {"Item": "(=) Custo a cobrir", "Valor": custo_fora, "Observação": "salários + FGTS + despesas"},
        {"Item": "(+) DAS sobre a nota", "Valor": das_est, "Observação": _das_obs},
        {"Item": "(+) Margem", "Valor": sobra, "Observação": f"{margem:.1f}% da nota".replace(".", ",")},
        {"Item": "(=) NOTA A EMITIR", "Valor": nota, "Observação": "lançar no PGDAS"},
    ]
    st.dataframe(fmt_df(pd.DataFrame(linhas), money=["Valor"]),
                 use_container_width=True, hide_index=True)
    st.markdown(
        (f"<div class='al-g'>🧮 <b>Conta fechando:</b> {brl(custo_fora)} (custo) + {brl(das_est)} "
         f"(DAS) + {brl(sobra)} (margem) = <b>{brl(nota)}</b> (nota). " +
         (f"A CPP de ~<b>{brl(cpp_est)}</b> já está <b>dentro</b> dos {brl(das_est)} do DAS — "
          "por isso não é somada à parte." if cpp_est is not None else
          "A CPP está dentro do DAS — anexe o PGDAS anterior para ver o valor dela.") +
         "</div>"), unsafe_allow_html=True)

    kk = st.columns(3)
    kpi(kk[0], brl(nota), "NOTA A EMITIR", f"lançar no PGDAS de {fper(mes, True)}", "n")
    kpi(kk[1], brl(das_est), "DAS estimado", f"{aliq:.1f}% da nota".replace(".", ","), "n")
    kpi(kk[2], brl(cpp_est) if cpp_est is not None else "—", "CPP (dentro do DAS)",
        "anexe o PGDAS p/ ver" if cpp_est is None else "já incluída no DAS", "n")

    # CPP a gravar ao confirmar (padrão: a fatia de CPP do DAS da nota)
    _cpp_confirmar = cpp_est
    # ── DISTRIBUIÇÃO DA NOTA POR TIPO DE RECEITA (edite os VALORES em R$) ─────
    _seg = st.session_state.get("sim_segmentos")
    if _seg:
        import simples as _sn
        _rbt12 = st.session_state.get("sim_rbt12")
        _tot_ref = sum(v["receita"] for v in _seg.values()) or 1
        _cats = list(_seg.keys())
        st.markdown(f"##### 🧾 Como distribuir a nota de {brl(nota)} no PGDAS")
        st.caption("Edite quanto colocar em cada tipo de receita — os três são livres. O painel "
                   "mostra em tempo real quanto FALTA (ou sobrou) para fechar na nota, então você "
                   "distribui sem calculadora. O CPP de cada parte usa a fórmula oficial do Simples "
                   "(alíquota efetiva pelo RBT12 × repartição do anexo).")
        _store = "sim_dist_vals"
        st.session_state.setdefault(_store, {})
        _seed_now = {c: round(nota * _seg[c]["receita"]/_tot_ref, 2) for c in _cats}
        if (not st.session_state[_store]) or set(st.session_state[_store]) != set(_cats):
            st.session_state[_store] = dict(_seed_now)
        if st.button("🔄 Redistribuir pelo mix do PGDAS", key="sim_dist_reset"):
            st.session_state[_store] = dict(_seed_now)
            st.session_state["sim_dist_ed_ver"] = st.session_state.get("sim_dist_ed_ver", 0) + 1
            st.rerun()
        st.markdown("<div class='al-b'>✏️ <b>Clique em qualquer valor da coluna azul para editar</b> "
                    "e digite quanto quer lançar naquele tipo de receita. Os três são livres — "
                    "acompanhe o card <b>“Falta distribuir”</b> abaixo até zerar.</div>",
                    unsafe_allow_html=True)
        editor_faturamento(_cats, "sim_dist_ed", store=_store,
                           coluna="✏️ Valor a lançar (R$) — clique p/ editar",
                           label_col="Tipo de receita", label_fn=lambda c: c)
        _tot_val = sum(float(st.session_state[_store].get(c, 0) or 0) for c in _cats)
        _dif = round(nota - _tot_val, 2)   # >0 falta ; <0 passou
        # painel de saldo em tempo real (sem calculadora)
        sk = st.columns(3)
        kpi(sk[0], brl(nota), "Nota alvo")
        kpi(sk[1], brl(_tot_val), "Distribuído")
        if abs(_dif) <= 0.5:
            kpi(sk[2], "R$ 0,00", "Falta distribuir", "fechou ✓", "up")
        elif _dif > 0:
            kpi(sk[2], brl(_dif), "Falta distribuir", "coloque em alguma parte", "n")
        else:
            kpi(sk[2], brl(-_dif), "Passou da nota", "reduza em alguma parte", "down")
        # tabela final com CPP por parte (fórmula oficial)
        drows = []
        _tot_cpp = 0.0; _tem_iv = False
        for c in _cats:
            val = float(st.session_state[_store].get(c, 0) or 0)
            anexo = _seg[c].get("anexo") or _sn.anexo_de_categoria(c)
            if anexo == "IV":
                _tem_iv = True
            cpp_c = _sn.cpp(val, _rbt12, anexo) if _rbt12 else \
                    (val * (_seg[c]["cpp"]/_seg[c]["receita"]) if _seg[c]["receita"] else 0)
            _tot_cpp += (cpp_c or 0)
            drows.append({"Tipo de receita": c, "Anexo": anexo,
                          "Valor a lançar": val, "CPP gerado": cpp_c or 0})
        drows.append({"Tipo de receita": "TOTAL", "Anexo": "",
                      "Valor a lançar": _tot_val, "CPP gerado": _tot_cpp})
        st.dataframe(fmt_df(pd.DataFrame(drows), money=["Valor a lançar", "CPP gerado"]),
                     use_container_width=True, hide_index=True)
        if abs(_dif) > 0.5:
            st.markdown((f"<div class='al-y'>⚠️ Ainda não fecha: "
                         f"{'faltam' if _dif>0 else 'passou em'} <b>{brl(abs(_dif))}</b> "
                         f"em relação à nota ({brl(nota)}). Ajuste as partes até 'Falta distribuir' "
                         "ficar em R$ 0,00.</div>"), unsafe_allow_html=True)
        else:
            st.markdown(f"<div class='al-g'>✅ Fecha na nota (<b>{brl(_tot_val)}</b>) · "
                        f"CPP total <b>{brl(_tot_cpp)}</b>.</div>", unsafe_allow_html=True)
        _cpp_confirmar = _tot_cpp   # CPP exato pela distribuição (fórmula oficial)
        if _tem_iv:
            st.markdown(
                "<div class='al-r'>⚠️ <b>Há receita no Anexo IV</b> (ex.: construção, limpeza, "
                "vigilância, cessão de mão de obra). Nele o <b>CPP não está no DAS</b> — é recolhido "
                "à parte, ~20% sobre a folha (via GPS/DCTFWeb). O CPP dessas partes aparece como R$ 0 "
                "aqui, mas o INSS patronal <b>existe e é pago por fora</b> — e isso costuma "
                "<b>anular a vantagem</b> da estrutura de mão de obra no Simples.</div>",
                unsafe_allow_html=True)

    # ── CONFIRMAR: grava faturamento + CPP (estimado) do mês na Análise ───────
    st.divider()
    cf1, cf2 = st.columns([2, 3])
    if cf1.button(f"✅ Confirmar simulação de {fper(mes, True)}", key="sim_confirma",
                  type="primary", use_container_width=True):
        st.session_state.setdefault("fat_por_comp", {})[mes] = round(nota, 2)
        st.session_state.setdefault("cpp_estimado_set", set())
        if _cpp_confirmar is not None:
            st.session_state.setdefault("cpp_por_comp", {})[mes] = round(_cpp_confirmar, 2)
            st.session_state["cpp_estimado_set"].add(mes)
        st.success(f"{fper(mes, True)}: faturamento {brl(nota)}" +
                   (f" + CPP (estimado) {brl(_cpp_confirmar)}" if _cpp_confirmar else "") +
                   " salvos — já entram no Custo Total da Análise de Folha. Quando você anexar o "
                   "PGDAS real deste mês, ele substitui o CPP estimado.")
    cf2.caption("Grava a nota como faturamento e o CPP estimado da simulação neste mês. "
                "O CPP entra no custo marcado como estimado; o PGDAS real do mês (quando anexado) "
                "assume o lugar.")

    # ── 5) COMO FICA A CPP (a dúvida do analista) ─────────────────────────────
    if cpp_est is not None:
        st.markdown(
            f"<div class='al-b'>🔎 <b>E a CPP, que não veio no XML?</b> Ela é paga <b>dentro do DAS</b> "
            f"desta nota. Emitindo <b>{brl(nota)}</b>, o DAS fica em ~<b>{brl(das_est)}</b>, e a fatia de "
            f"CPP dele é ~<b>{brl(cpp_est)}</b> — é o INSS patronal do Simples (Anexo III), recolhido via "
            "DAS, não em guia separada. Por isso a CPP entra na simulação como parte do DAS, e não como "
            "um custo somado por fora.</div>", unsafe_allow_html=True)
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
        _economia = _inss_pres - das_est
        cmp = pd.DataFrame([
            {"Cenário": "A) Folha no Simples (mão de obra)", "Imposto sobre a folha": das_est,
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
    hc1, hc2 = st.columns(2)
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

if inss.empty and adm.empty and pag.empty and _modo != "simulador":
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
                    f"<div class='al-y'>ℹ️ <b>Sobre o CPP{_est_txt} incluído acima ({brl(_cpp_per)}):</b> "
                    "ele está somado no “Gasto com Folha + Encargos” para você ter a <b>noção do custo "
                    "real de pessoal</b>. Mas atenção: no Simples esse CPP <b>já é pago dentro do DAS</b> "
                    "(imposto sobre o faturamento) — <b>não é um gasto a mais por fora</b>. Ou seja, ao "
                    "olhar a “sobra para impostos”, lembre que a parte do DAS referente ao CPP já está "
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
