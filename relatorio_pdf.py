# -*- coding: utf-8 -*-
"""
relatorio_pdf.py — Relatório de folha com visual moderno (2026).
Design: tipografia Segoe UI/DejaVu, cards de KPI, gráficos limpos, paleta elegante.
Mantém o mesmo `ctx` montado pelo app.
"""
import io, os
from datetime import date, datetime
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib import font_manager as _fm
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.units import cm, mm
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_RIGHT, TA_LEFT
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
    PageBreak, HRFlowable, KeepTogether, Image, Frame, PageTemplate,
)

# ── PALETA MODERNA ────────────────────────────────────────────────────────────
INK    = colors.HexColor("#0f1b2d")   # quase preto azulado (texto forte)
NAVY   = colors.HexColor("#1c3d5a")
BRAND  = colors.HexColor("#3b5bdb")   # azul vibrante (destaque)
BRAND2 = colors.HexColor("#5c7cfa")
TEAL   = colors.HexColor("#0ca678")
GREEN  = colors.HexColor("#2f9e44")
AMBER  = colors.HexColor("#e8951a")
RED    = colors.HexColor("#e03131")
GREY   = colors.HexColor("#868e96")
GREY2  = colors.HexColor("#adb5bd")
BG     = colors.HexColor("#f4f6fb")
CARD   = colors.HexColor("#ffffff")
LINE   = colors.HexColor("#e7ebf3")

# ── FONTES (Segoe UI > DejaVu > Helvetica) ────────────────────────────────────
def _reg_fonts():
    candidates = [
        ("UI", r"C:\Windows\Fonts\segoeui.ttf"),
        ("UI-Bold", r"C:\Windows\Fonts\segoeuib.ttf"),
        ("UI-Semi", r"C:\Windows\Fonts\segoeuisb.ttf"),
        ("UI-Light", r"C:\Windows\Fonts\segoeuil.ttf"),
    ]
    ok = True
    for name, path in candidates:
        try:
            if os.path.exists(path):
                pdfmetrics.registerFont(TTFont(name, path))
            else:
                ok = False
        except Exception:
            ok = False
    if ok and os.path.exists(candidates[0][1]):
        return "UI", "UI-Bold", "UI-Semi", "UI-Light"
    # fallback DejaVu
    try:
        base = os.path.join(matplotlib.get_data_path(), "fonts", "ttf")
        pdfmetrics.registerFont(TTFont("UI", os.path.join(base, "DejaVuSans.ttf")))
        pdfmetrics.registerFont(TTFont("UI-Bold", os.path.join(base, "DejaVuSans-Bold.ttf")))
        return "UI", "UI-Bold", "UI-Bold", "UI"
    except Exception:
        return "Helvetica", "Helvetica-Bold", "Helvetica-Bold", "Helvetica"

F, FB, FSB, FL = _reg_fonts()
# fonte dos gráficos (matplotlib)
try:
    _mpl_font = r"C:\Windows\Fonts\segoeui.ttf"
    if os.path.exists(_mpl_font):
        _fm.fontManager.addfont(_mpl_font)
        plt.rcParams["font.family"] = _fm.FontProperties(fname=_mpl_font).get_name()
except Exception:
    pass
plt.rcParams["axes.edgecolor"] = "#dfe3ec"


def brl(v, cents=True):
    try:
        s = ("{:,.2f}" if cents else "{:,.0f}").format(float(v))
        return "R$ " + s.replace(",", "X").replace(".", ",").replace("X", ".")
    except (ValueError, TypeError):
        return "R$ 0,00"

def brl_k(v):
    v = float(v or 0)
    if abs(v) >= 1_000_000: return f"R$ {v/1_000_000:.1f}M".replace(".", ",")
    if abs(v) >= 1_000: return f"R$ {v/1_000:.0f}k"
    return f"R$ {v:.0f}"

def fdate(s):
    if not s: return ""
    try: return datetime.strptime(str(s), "%Y-%m-%d").strftime("%d/%m/%Y")
    except ValueError: return str(s)

def fper(p):
    m = {"01":"Jan","02":"Fev","03":"Mar","04":"Abr","05":"Mai","06":"Jun",
         "07":"Jul","08":"Ago","09":"Set","10":"Out","11":"Nov","12":"Dez"}
    if not p or "-" not in str(p): return str(p)
    a, mm_ = str(p).split("-"); return f"{m.get(mm_,mm_)}/{a}"

def fmt_cnpj(c):
    import re as _re
    d = _re.sub(r"\D", "", str(c or ""))
    if len(d) == 14:
        return f"{d[:2]}.{d[2:5]}.{d[5:8]}/{d[8:12]}-{d[12:]}"
    if len(d) == 8:
        return f"{d[:2]}.{d[2:5]}.{d[5:8]} (raiz)"
    return d

PALETA_G = ["#3b5bdb", "#0ca678", "#e8951a", "#e03131", "#7048e8", "#1098ad", "#868e96"]


def _styles():
    ss = getSampleStyleSheet()
    return {
        "h1":   ParagraphStyle("h1", parent=ss["Title"], fontName=FB, fontSize=23,
                               textColor=colors.white, spaceAfter=0, leading=27),
        "sub":  ParagraphStyle("sub", fontName=F, fontSize=9.5, textColor=colors.HexColor("#c7d2fe"), leading=14),
        "sec":  ParagraphStyle("sec", fontName=FSB, fontSize=13.5, textColor=INK, spaceBefore=2, spaceAfter=8, leading=16),
        "h3":   ParagraphStyle("h3", fontName=FSB, fontSize=10.5, textColor=NAVY, spaceBefore=9, spaceAfter=4),
        "body": ParagraphStyle("body", fontName=F, fontSize=8.6, textColor=colors.HexColor("#3a4250"), leading=12, spaceAfter=4),
        "small":ParagraphStyle("small", fontName=F, fontSize=7.6, textColor=GREY, leading=10),
        "cell": ParagraphStyle("cell", fontName=F, fontSize=7.8, textColor=INK, leading=10),
    }


def _kpi_card(label, value, accent, sub=""):
    """Card de KPI moderno: label pequeno em cima, valor grande, faixa de cor."""
    inner = Table(
        [[Paragraph(label.upper(), ParagraphStyle("kl", fontName=F, fontSize=6.6,
                    textColor=GREY, leading=9, alignment=TA_LEFT))],
         [Paragraph(f"<b>{value}</b>", ParagraphStyle("kv", fontName=FB, fontSize=14.5,
                    textColor=INK, leading=17, alignment=TA_LEFT))],
         [Paragraph(sub, ParagraphStyle("ks", fontName=F, fontSize=6.8,
                    textColor=accent, leading=9, alignment=TA_LEFT))]],
        colWidths=["*"])
    inner.setStyle(TableStyle([
        ("LEFTPADDING",(0,0),(-1,-1),9), ("RIGHTPADDING",(0,0),(-1,-1),6),
        ("TOPPADDING",(0,0),(0,0),8), ("BOTTOMPADDING",(0,-1),(-1,-1),8),
        ("TOPPADDING",(0,1),(-1,-1),0), ("BOTTOMPADDING",(0,0),(-1,0),1),
        ("BACKGROUND",(0,0),(-1,-1), CARD),
        ("LINEABOVE",(0,0),(-1,0), 2.2, accent),
        ("BOX",(0,0),(-1,-1), 0.6, LINE),
        ("ROUNDEDCORNERS",[3,3,3,3]),
    ]))
    return inner

def _kpi_row(cards, sw, gap=0.18*cm):
    n = len(cards)
    cw = (sw - gap*(n-1)) / n
    row = Table([cards], colWidths=[cw]*n, hAlign="LEFT")
    row.setStyle(TableStyle([("LEFTPADDING",(0,0),(-1,-1),0),("RIGHTPADDING",(0,0),(-1,-1),int(gap)),
                             ("VALIGN",(0,0),(-1,-1),"TOP")]))
    return row

def _table(data, col_w, total=False, font=7.8, align_from=1, head=BRAND):
    n=len(data)
    t=Table(data, colWidths=col_w, repeatRows=1)
    style=[
        ("BACKGROUND",(0,0),(-1,0), head),
        ("TEXTCOLOR",(0,0),(-1,0), colors.white),
        ("FONTNAME",(0,0),(-1,0), FSB),
        ("FONTNAME",(0,1),(-1,-1), F),
        ("FONTSIZE",(0,0),(-1,-1), font),
        ("TEXTCOLOR",(0,1),(-1,-1), INK),
        ("ROWBACKGROUNDS",(0,1),(-1,-1 if not total else -2),[CARD, BG]),
        ("LINEBELOW",(0,0),(-1,-2), 0.4, LINE),
        ("VALIGN",(0,0),(-1,-1),"MIDDLE"),
        ("ALIGN",(align_from,0),(-1,-1),"RIGHT"),
        ("LEFTPADDING",(0,0),(-1,-1),7),("RIGHTPADDING",(0,0),(-1,-1),7),
        ("TOPPADDING",(0,0),(-1,-1),5),("BOTTOMPADDING",(0,0),(-1,-1),5),
        ("ROUNDEDCORNERS",[4,4,0,0]),
    ]
    if total:
        style+=[("BACKGROUND",(0,n-1),(-1,n-1), colors.HexColor("#eef2ff")),
                ("FONTNAME",(0,n-1),(-1,n-1), FB),
                ("TEXTCOLOR",(0,n-1),(-1,n-1), BRAND),
                ("LINEABOVE",(0,n-1),(-1,n-1),0.8, BRAND)]
    t.setStyle(TableStyle(style))
    return t

def _secao(num, titulo, S):
    """Título de seção: número em chip colorido + texto."""
    chip = Table([[Paragraph(f"<b>{num}</b>", ParagraphStyle("cn", fontName=FB, fontSize=11,
                  textColor=colors.white, alignment=TA_CENTER))]], colWidths=[0.72*cm], rowHeights=[0.72*cm])
    chip.setStyle(TableStyle([("BACKGROUND",(0,0),(-1,-1),BRAND),("VALIGN",(0,0),(-1,-1),"MIDDLE"),
                              ("ROUNDEDCORNERS",[5,5,5,5]),("LEFTPADDING",(0,0),(-1,-1),0),("RIGHTPADDING",(0,0),(-1,-1),0)]))
    t = Table([[chip, Paragraph(titulo, S["sec"])]], colWidths=[0.95*cm, "*"])
    t.setStyle(TableStyle([("VALIGN",(0,0),(-1,-1),"MIDDLE"),("LEFTPADDING",(0,0),(-1,-1),0),
                           ("TOPPADDING",(0,0),(-1,-1),10),("BOTTOMPADDING",(0,0),(-1,-1),3)]))
    return t


# ── GRÁFICOS ──────────────────────────────────────────────────────────────────
def _fig_to_img(fig, w_cm, h_cm):
    buf = io.BytesIO()
    fig.savefig(buf, format="png", dpi=150, bbox_inches="tight", transparent=True)
    plt.close(fig); buf.seek(0)
    return Image(buf, width=w_cm*cm, height=h_cm*cm)

def _donut(labels, valores, cores, titulo=""):
    fig, ax = plt.subplots(figsize=(7.2/2.54, 6.2/2.54), dpi=150)
    tot = sum(valores) or 1
    w, _ = ax.pie(valores, colors=cores, startangle=90, counterclock=False,
                  wedgeprops=dict(width=0.42, edgecolor="white", linewidth=2))
    ax.text(0, 0.12, brl_k(tot), ha="center", va="center", fontsize=12, fontweight="bold", color="#0f1b2d")
    ax.text(0, -0.22, "total", ha="center", va="center", fontsize=8, color="#868e96")
    # legenda à direita
    leg = [f"{l}  {v/tot*100:.0f}%" for l, v in zip(labels, valores)]
    ax.legend(w, leg, loc="center left", bbox_to_anchor=(1.0, 0.5), frameon=False,
              fontsize=8, handlelength=0.9, labelspacing=0.7)
    ax.set_aspect("equal")
    return _fig_to_img(fig, 9.2, 6.0)

def _barras_evol(periodos, series, titulo=""):
    """Barras agrupadas de evolução (remuneração, encargos...)."""
    fig, ax = plt.subplots(figsize=(9.6/2.54, 6.0/2.54), dpi=150)
    x = range(len(periodos))
    labels = [fper(p) for p in periodos]
    n = len(series)
    bw = 0.72/n
    for i,(nome,vals,cor) in enumerate(series):
        ax.bar([xi + i*bw for xi in x], vals, width=bw, label=nome, color=cor, zorder=3)
    ax.set_xticks([xi + bw*(n-1)/2 for xi in x]); ax.set_xticklabels(labels, fontsize=8, color="#3a4250")
    ax.tick_params(axis="y", labelsize=7, colors="#868e96")
    ax.set_xlim(-0.35, len(periodos)-0.15)
    ax.spines[["top","right"]].set_visible(False)
    ax.spines[["left","bottom"]].set_color("#dfe3ec")
    ax.grid(axis="y", linestyle="-", alpha=0.25, zorder=0)
    ax.legend(frameon=False, fontsize=7.2, ncol=n, loc="upper center", bbox_to_anchor=(0.5,1.18))
    import matplotlib.ticker as mt
    ax.yaxis.set_major_formatter(mt.FuncFormatter(lambda v,_: brl_k(v)))
    return _fig_to_img(fig, 9.6, 6.0)


# ── PÁGINA (faixa de topo + rodapé) via canvas ────────────────────────────────
def _bg_painter(empresa, rodape="Gerado do eSocial · uso gerencial · LGPD"):
    def draw(canvas, doc):
        canvas.saveState()
        pw, ph = A4
        # fundo geral suave
        canvas.setFillColor(BG); canvas.rect(0, 0, pw, ph, fill=1, stroke=0)
        # rodapé
        canvas.setFillColor(GREY2)
        canvas.setFont(F, 7)
        canvas.drawString(1.5*cm, 0.9*cm, rodape)
        canvas.drawRightString(pw-1.5*cm, 0.9*cm, f"Página {doc.page}")
        canvas.setStrokeColor(LINE); canvas.setLineWidth(0.5)
        canvas.line(1.5*cm, 1.2*cm, pw-1.5*cm, 1.2*cm)
        canvas.restoreState()
    return draw


def gerar(ctx, empresa=""):
    S = _styles()
    buf = io.BytesIO()
    pw, ph = A4
    doc = SimpleDocTemplate(buf, pagesize=A4, leftMargin=1.5*cm, rightMargin=1.5*cm,
                            topMargin=1.4*cm, bottomMargin=1.7*cm,
                            title="Relatório de Folha — eSocial")
    sw = pw - 3.0*cm
    story = []
    hoje = date.today()
    periodos = ctx.get("periodos", [])

    # ── MARCA (logo.png se existir; senão wordmark) ──────────────────────────
    _logo = os.path.join(os.path.dirname(os.path.abspath(__file__)), "logo.png")
    if os.path.exists(_logo):
        try:
            from reportlab.lib.utils import ImageReader
            _iw, _ih = ImageReader(_logo).getSize()
            _lw = 4.6*cm; _lh = _lw*_ih/_iw
            _limg = Image(_logo, width=_lw, height=_lh)
            _limg.hAlign = "CENTER"
            story.append(_limg); story.append(Spacer(1, 0.25*cm))
        except Exception:
            story.append(Paragraph("CONTADOR <b>DE PADARIAS</b>",
                ParagraphStyle("wm", fontName=FB, fontSize=15, textColor=colors.HexColor("#F5A623"),
                               leading=17, spaceAfter=6)))
    else:
        story.append(Paragraph("CONTADOR <b>DE PADARIAS</b>",
            ParagraphStyle("wm", fontName=FB, fontSize=15, textColor=colors.HexColor("#F5A623"),
                           leading=17, spaceAfter=6)))

    # ── CABEÇALHO (faixa azul: relatório + empresa + CNPJ + competência) ─────
    _kicker = ParagraphStyle("kick", fontName=FSB, fontSize=9, textColor=colors.HexColor("#9db8de"),
                             leading=12, spaceAfter=2)
    _cnpj_txt = f"CNPJ {fmt_cnpj(ctx.get('cnpj'))}  ·  " if ctx.get("cnpj") else ""
    head_inner = [
        [Paragraph("RELATÓRIO DE FOLHA DE PAGAMENTO", _kicker)],
        [Paragraph(empresa or "Empresa não informada", S["h1"])],
        [Paragraph(_cnpj_txt + "Fonte: eSocial", S["sub"])],
        [Paragraph(f"Competência: {ctx.get('periodos_label','')}", S["sub"])],
    ]
    head = Table(head_inner, colWidths=[sw])
    head.setStyle(TableStyle([
        ("BACKGROUND",(0,0),(-1,-1), NAVY),
        ("LEFTPADDING",(0,0),(-1,-1),18),("RIGHTPADDING",(0,0),(-1,-1),18),
        ("TOPPADDING",(0,0),(0,0),16),("BOTTOMPADDING",(0,-1),(-1,-1),15),
        ("TOPPADDING",(0,1),(-1,-1),3),
        ("ROUNDEDCORNERS",[8,8,8,8]),
    ]))
    story.append(head)
    story.append(Spacer(1, 0.35*cm))

    # ── KPIs PRINCIPAIS (cards) ──────────────────────────────────────────────
    rc = ctx.get("resumo_competencias", [])
    tot = {k: sum(r.get(k,0) for r in rc) for k in ["func","remun","liq","inss_emp","inss_pat","fgts","irrf","custo"]}
    nfunc = max((r.get("func",0) for r in rc), default=0) if len(rc)==1 else \
            (rc[0]["func"] if len(rc)==1 else max((r.get("func",0) for r in rc), default=0))
    # para período único usa o valor; para vários, soma monetária e headcount do maior
    func_disp = rc[0]["func"] if len(rc)==1 else max((r.get("func",0) for r in rc), default=0)

    story.append(_secao("1", "Indicadores do Período", S))
    story.append(_kpi_row([
        _kpi_card("Funcionários", str(func_disp), BRAND, "no período"),
        _kpi_card("Remuneração Bruta", brl(tot["remun"]), TEAL, "base FGTS"),
        _kpi_card("Líquido Pago", brl(tot["liq"]), BRAND2, "S-1210"),
        _kpi_card("Custo Total", brl(tot["custo"]), AMBER, "folha + encargos"),
    ], sw))
    # rótulo do patronal: real (S-5011) x CPP do Simples (via DAS)
    if ctx.get("tem_patronal_real"):
        _pat_titulo, _pat_sub = "INSS Patronal", "S-5011"
    elif tot["inss_pat"] > 0:
        _pat_titulo, _pat_sub = "INSS Patronal / CPP", "CPP · via DAS (Simples)"
    else:
        _pat_titulo, _pat_sub = "INSS Patronal", "não recolhido (Simples)"
    story.append(Spacer(1, 0.18*cm))
    story.append(_kpi_row([
        _kpi_card("INSS Empregado", brl(tot["inss_emp"]), BRAND, "desconto"),
        _kpi_card(_pat_titulo, brl(tot["inss_pat"]), GREY, _pat_sub),
        _kpi_card("FGTS", brl(tot["fgts"]), GREEN, "8%"),
        _kpi_card("IRRF", brl(tot["irrf"]), RED, "retido"),
    ], sw))

    # aviso: custo sem o CPP do Simples (custo subestimado)
    if ctx.get("cpp_faltando"):
        story.append(Spacer(1, 0.2*cm))
        _avbox = Table([[Paragraph(
            "<b>⚠️ Custo sem o CPP do Simples.</b> Não há INSS patronal no eSocial (Simples) e o "
            "CPP não foi informado — o Custo Total acima está subestimado (falta o INSS patronal "
            "pago via DAS). Anexe o PGDAS para incluí-lo.",
            ParagraphStyle("av", fontName=F, fontSize=8, textColor=colors.HexColor("#8a3a2e"),
                           leading=11))]], colWidths=[sw])
        _avbox.setStyle(TableStyle([("BACKGROUND",(0,0),(-1,-1), colors.HexColor("#fdf0ee")),
            ("BOX",(0,0),(-1,-1), 0.6, RED), ("LEFTPADDING",(0,0),(-1,-1),10),
            ("RIGHTPADDING",(0,0),(-1,-1),10), ("TOPPADDING",(0,0),(-1,-1),7),
            ("BOTTOMPADDING",(0,0),(-1,-1),7), ("ROUNDEDCORNERS",[5,5,5,5])]))
        story.append(_avbox)

    # nota do CPP (incluído no custo, mas pago dentro do DAS)
    _cpp = ctx.get("cpp_total", 0) or 0
    if _cpp > 0:
        _est = " (estimado)" if ctx.get("cpp_estimado") else ""
        story.append(Spacer(1, 0.2*cm))
        _cbox = Table([[Paragraph(
            f"<b>CPP{_est} incluído no custo: {brl(_cpp)}.</b> É o INSS patronal do Simples. "
            "Ele está somado ao custo para mostrar o gasto real de pessoal, mas é recolhido "
            "<b>dentro do DAS</b> (imposto sobre o faturamento) — não é um gasto a mais por fora.",
            ParagraphStyle("cpn", fontName=F, fontSize=8, textColor=INK, leading=11))]], colWidths=[sw])
        _cbox.setStyle(TableStyle([("BACKGROUND",(0,0),(-1,-1), colors.HexColor("#eef3f9")),
            ("BOX",(0,0),(-1,-1), 0.6, NAVY), ("LEFTPADDING",(0,0),(-1,-1),10),
            ("RIGHTPADDING",(0,0),(-1,-1),10), ("TOPPADDING",(0,0),(-1,-1),7),
            ("BOTTOMPADDING",(0,0),(-1,-1),7), ("ROUNDEDCORNERS",[5,5,5,5])]))
        story.append(_cbox)

    # ── COMPOSIÇÃO DO CUSTO (tabela com participação — sem gráfico) ───────────
    story.append(Spacer(1, 0.35*cm))
    story.append(Paragraph("Composição do custo da folha", S["h3"]))
    _comp = [("Remuneração (base FGTS)", tot["remun"]),
             ("INSS Patronal / CPP", tot["inss_pat"]),
             ("FGTS (8%)", tot["fgts"])]
    _comp = [(l, v) for l, v in _comp if v > 0]
    _base = tot["custo"] or sum(v for _, v in _comp) or 1
    data = [["Componente", "Valor", "% do custo"]]
    for l, v in sorted(_comp, key=lambda x: -x[1]):
        data.append([l, brl(v), f"{v/_base*100:.1f}%".replace(".", ",")])
    data.append(["CUSTO TOTAL", brl(tot["custo"]), "100,0%"])
    story.append(_table(data, [sw*0.52, sw*0.28, sw*0.20], total=True, align_from=1))

    # ── FATURAMENTO × FOLHA (se o cliente informou) ──────────────────────────
    fat = ctx.get("faturamento")
    if fat:
        story.append(Spacer(1, 0.4*cm))
        bloco = [Paragraph("Faturamento × Folha", S["h3"]),
                 Paragraph("Quanto da receita do período foi para a folha (faturamento informado pelo cliente).",
                           S["small"]), Spacer(1, 0.15*cm)]
        bloco.append(_kpi_row([
            _kpi_card("Faturamento", brl(fat["total"]), BRAND, "informado"),
            _kpi_card("Gasto Folha+Encargos", brl(fat["custo_total"]), AMBER, "custo total"),
            _kpi_card("% do Faturamento", f"{fat['pct_custo']:.1f}%".replace(".", ","), TEAL, "folha + encargos"),
            _kpi_card("Sobra de R$ 100", "R$ " + f"{100-fat['pct_custo']:.2f}".replace(".", ","),
                      GREEN, "demais desp./lucro"),
        ], sw))
        story.append(KeepTogether(bloco))
        if len(fat["rows"]) > 1:
            story.append(Spacer(1, 0.2*cm))
            data=[["Competência","Faturamento","Gasto Folha + Encargos","% do Faturamento"]]
            for r in fat["rows"]:
                f_ = r["fat"]
                data.append([fper(r["comp"]), brl(f_,0), brl(r["custo"],0),
                             (f"{r['custo']/f_*100:.1f}%".replace(".", ",") if f_ else "—")])
            story.append(_table(data, [sw*0.25,sw*0.27,sw*0.28,sw*0.20],
                                font=7.6, align_from=1, head=TEAL))

    # ── 2. RESUMO POR COMPETÊNCIA ────────────────────────────────────────────
    story.append(_secao("2", "Resumo por Competência", S))
    data=[["Competência","Func.","Remuneração","Líquido","INSS Emp.","FGTS","IRRF","Custo Total"]]
    for r in rc:
        data.append([fper(r["comp"]), str(r["func"]), brl(r["remun"],0), brl(r["liq"],0),
                     brl(r["inss_emp"],0), brl(r["fgts"],0), brl(r["irrf"],0), brl(r["custo"],0)])
    if len(rc)>1:
        data.append(["TOTAL", str(tot["func"]), brl(tot["remun"],0), brl(tot["liq"],0),
                     brl(tot["inss_emp"],0), brl(tot["fgts"],0), brl(tot["irrf"],0), brl(tot["custo"],0)])
    story.append(_table(data, [sw*0.15,sw*0.07,sw*0.15,sw*0.14,sw*0.13,sw*0.12,sw*0.10,sw*0.14],
                        total=(len(rc)>1), font=7.4))

    # ── 3. CONFERÊNCIA POR EVENTO ────────────────────────────────────────────
    story.append(_secao("3", "Conferência por Evento (origem no eSocial)", S))
    for bloco in ctx.get("conferencia", []):
        story.append(Paragraph(f"Competência {fper(bloco['comp'])}", S["h3"]))
        data=[["Indicador","Valor","Evento"]]
        for nome,val,fonte in bloco["itens"]:
            data.append([nome, val, fonte])
        story.append(_table(data, [sw*0.46, sw*0.28, sw*0.26], font=7.6))

    # ── 4. ENCARGOS ───────────────────────────────────────────────────────────
    enc = ctx.get("encargos", [])
    if enc:
        story.append(PageBreak())
        story.append(_secao("4", "Encargos Detalhados (mensal × 13º)", S))
        data=[["Competência","INSS Mensal","INSS 13º","FGTS Mensal","FGTS 13º","IRRF Mensal","IRRF 13º"]]
        for r in enc:
            data.append([fper(r["comp"]), brl(r["inss_m"]), brl(r["inss_13"]),
                         brl(r["fgts_m"]), brl(r["fgts_13"]), brl(r["irrf_m"]), brl(r["irrf_13"])])
        story.append(_table(data, [sw*0.16]+[sw*0.14]*6, font=7.2))
        g = ctx.get("guias", {})
        if g:
            story.append(Paragraph("Guias a recolher (estimativa do período)", S["h3"]))
            gd=[["Guia","Valor"],
                ["GPS / DCTFWeb — INSS (empregado + patronal)", brl(g.get("inss",0))],
                ["FGTS Digital", brl(g.get("fgts",0))],
                ["DARF IRRF (cód. 0561)", brl(g.get("irrf",0))],
                ["TOTAL", brl(g.get("inss",0)+g.get("fgts",0)+g.get("irrf",0))]]
            story.append(_table(gd, [sw*0.72, sw*0.28], total=True, head=TEAL))

    # ── 5. RESUMO DE VERBAS ───────────────────────────────────────────────────
    vb = ctx.get("verbas")
    if vb:
        story.append(PageBreak())
        story.append(_secao("5", "Resumo de Verbas (rubricas)", S))
        story.append(_kpi_row([
            _kpi_card("Proventos + Vantagens", brl(vb["tot_prov"]), GREEN, ""),
            _kpi_card("Descontos", brl(vb["tot_desc"]), RED, ""),
            _kpi_card("Líquido (Prov − Desc)", brl(vb["tot_prov"]-vb["tot_desc"]), BRAND, ""),
        ], sw))
        story.append(Spacer(1, 0.25*cm))
        for titulo, chave, cor in [("Proventos","proventos",GREEN),("Vantagens/Benefícios","vantagens",TEAL),
                                   ("Descontos","descontos",RED),("Informativas (FGTS/bases)","informativas",GREY)]:
            lst = vb.get(chave, [])
            if not lst: continue
            story.append(Paragraph(f"{titulo} · {brl(sum(x[2] for x in lst))}", S["h3"]))
            data=[["Cód.","Rubrica","Valor"]]
            for cod,nome,val in sorted(lst, key=lambda x:-x[2]):
                data.append([cod, str(nome)[:48], brl(val)])
            story.append(_table(data, [sw*0.12, sw*0.63, sw*0.25], align_from=2, font=7.4, head=cor))

    # ── 6. CUSTO POR FUNCIONÁRIO ──────────────────────────────────────────────
    cf = ctx.get("custo_funcionarios", [])
    if cf:
        story.append(PageBreak())
        story.append(_secao("6", "Custo por Funcionário", S))
        data=[["Matr.","Nome / CPF","Remuneração","INSS Emp.","FGTS","Custo Real"]]
        for r in cf:
            data.append([str(r["matricula"]), str(r["nome"])[:34], brl(r["remun"],0),
                         brl(r["inss_emp"],0), brl(r["fgts"],0), brl(r["custo"],0)])
        story.append(_table(data, [sw*0.09, sw*0.37, sw*0.16, sw*0.13, sw*0.11, sw*0.14], font=6.8, align_from=2))

    # ── 7. MOVIMENTAÇÃO ───────────────────────────────────────────────────────
    adm = ctx.get("admissoes", []); des = ctx.get("desligamentos", [])
    if adm or des:
        story.append(PageBreak())
        story.append(_secao("7", "Movimentação de Pessoal", S))
        if adm:
            story.append(Paragraph(f"Admissões · {len(adm)}", S["h3"]))
            data=[["Data","Matr.","Nome / CPF","Cargo","Salário"]]
            for r in adm:
                data.append([fdate(r.get("dt_adm")), str(r.get("matricula","")),
                             str(r.get("nome",""))[:28], str(r.get("cargo",""))[:22], brl(r.get("salario",0),0)])
            story.append(_table(data, [sw*0.11,sw*0.08,sw*0.32,sw*0.30,sw*0.19], align_from=4, font=7.2, head=GREEN))
        if des:
            story.append(Paragraph(f"Desligamentos · {len(des)}", S["h3"]))
            data=[["Data","Matr.","Nome / CPF","Motivo","Ônus","Verbas"]]
            for r in des:
                data.append([fdate(r.get("dt_deslig")), str(r.get("matricula","")),
                             str(r.get("nome",""))[:22], str(r.get("motivo",""))[:28],
                             str(r.get("onus","")), brl(r.get("verbas",0),0)])
            story.append(_table(data, [sw*0.10,sw*0.07,sw*0.24,sw*0.30,sw*0.11,sw*0.18], align_from=5, font=7.2, head=RED))

    # ── 8. AFASTAMENTOS ───────────────────────────────────────────────────────
    afr = ctx.get("afastamentos_resumo", [])
    if afr:
        story.append(_secao("8", "Afastamentos e Absenteísmo", S))
        data=[["Motivo","Ocorrências","Total de Dias"]]
        for r in afr:
            data.append([str(r["motivo"])[:52], str(int(r["qtd"])), str(int(r["dias"]))])
        story.append(_table(data, [sw*0.6, sw*0.2, sw*0.2], head=AMBER))

    painter = _bg_painter(empresa)
    doc.build(story, onFirstPage=painter, onLaterPages=painter)
    return buf.getvalue()


def gerar_dre(ctx, empresa=""):
    """DRE gerencial simplificada — receita de serviço x despesas x impostos, por competência.
    ctx: cnpj, periodo_label, linhas [{competencia, receita, despesa_pessoal, despesa_geral,
    impostos, resultado, despesas_detalhadas [{descricao, valor, categoria}]}], tot_receita,
    tot_pessoal, tot_geral, tot_impostos, tot_resultado, responsavel_empresa, cpf_empresa,
    crc_contador, cpf_contador."""
    S = _styles()
    buf = io.BytesIO()
    pw, ph = A4
    doc = SimpleDocTemplate(buf, pagesize=A4, leftMargin=1.5*cm, rightMargin=1.5*cm,
                            topMargin=1.4*cm, bottomMargin=1.7*cm,
                            title="DRE Gerencial")
    sw = pw - 3.0*cm
    story = []
    hoje = date.today()
    linhas = ctx.get("linhas", [])

    _logo = os.path.join(os.path.dirname(os.path.abspath(__file__)), "logo.png")
    if os.path.exists(_logo):
        try:
            from reportlab.lib.utils import ImageReader
            _iw, _ih = ImageReader(_logo).getSize()
            _lw = 4.6*cm; _lh = _lw*_ih/_iw
            _limg = Image(_logo, width=_lw, height=_lh)
            _limg.hAlign = "CENTER"
            story.append(_limg); story.append(Spacer(1, 0.25*cm))
        except Exception:
            pass

    _kicker = ParagraphStyle("kick", fontName=FSB, fontSize=9, textColor=colors.HexColor("#9db8de"),
                             leading=12, spaceAfter=2)
    _cnpj_txt = f"CNPJ {fmt_cnpj(ctx.get('cnpj'))}  ·  " if ctx.get("cnpj") else ""
    head_inner = [
        [Paragraph("DEMONSTRAÇÃO DE RESULTADO (DRE) — GERENCIAL", _kicker)],
        [Paragraph(empresa or "Empresa não informada", S["h1"])],
        [Paragraph(_cnpj_txt + f"Período: {ctx.get('periodo_label','')}", S["sub"])],
    ]
    head = Table(head_inner, colWidths=[sw])
    head.setStyle(TableStyle([
        ("BACKGROUND",(0,0),(-1,-1), NAVY),
        ("LEFTPADDING",(0,0),(-1,-1),18),("RIGHTPADDING",(0,0),(-1,-1),18),
        ("TOPPADDING",(0,0),(0,0),16),("BOTTOMPADDING",(0,-1),(-1,-1),15),
        ("TOPPADDING",(0,1),(-1,-1),3),
        ("ROUNDEDCORNERS",[8,8,8,8]),
    ]))
    story.append(head)
    story.append(Spacer(1, 0.4*cm))

    _resultado = ctx.get("tot_resultado", 0) or 0
    _margem = round(100 * _resultado / ctx["tot_receita"], 1) if ctx.get("tot_receita") else None
    _cor_resultado = GREEN if _resultado >= 0 else RED

    # ── DEMONSTRAÇÃO DO RESULTADO — formato clássico de DRE, de cima para baixo ──
    story.append(_secao("1", "Demonstração do Resultado", S))
    _dre_rows = [
        ["RECEITA BRUTA DE SERVIÇOS", brl(ctx.get("tot_receita", 0))],
        ["(-) Despesa de Pessoal (folha + encargos)", f"({brl(ctx.get('tot_pessoal', 0), False)})"],
        ["(-) Outras Despesas", f"({brl(ctx.get('tot_geral', 0), False)})"],
        ["(-) Impostos", f"({brl(ctx.get('tot_impostos', 0), False)})"],
        ["(=) RESULTADO DO PERÍODO", brl(_resultado)],
    ]
    _dre_t = Table(_dre_rows, colWidths=[sw*0.68, sw*0.32])
    _dre_t.setStyle(TableStyle([
        ("FONTNAME",(0,0),(-1,-1), F),
        ("FONTNAME",(0,0),(-1,0), FB),
        ("FONTNAME",(0,-1),(-1,-1), FB),
        ("FONTSIZE",(0,0),(-1,0), 10.5),
        ("FONTSIZE",(0,1),(-1,-2), 9.2),
        ("FONTSIZE",(0,-1),(-1,-1), 12),
        ("TEXTCOLOR",(0,0),(-1,0), INK),
        ("TEXTCOLOR",(0,1),(-1,-2), colors.HexColor("#5a6472")),
        ("TEXTCOLOR",(0,-1),(-1,-1), _cor_resultado),
        ("ALIGN",(1,0),(1,-1),"RIGHT"),
        ("LEFTPADDING",(0,0),(-1,-1),6),("RIGHTPADDING",(0,0),(-1,-1),6),
        ("TOPPADDING",(0,0),(-1,0),8),("BOTTOMPADDING",(0,0),(-1,0),10),
        ("TOPPADDING",(0,1),(-1,-2),3),("BOTTOMPADDING",(0,1),(-1,-2),3),
        ("LINEBELOW",(0,0),(-1,0), 0.6, LINE),
        ("LINEABOVE",(0,-1),(-1,-1), 1.1, INK),
        ("TOPPADDING",(0,-1),(-1,-1),9),("BOTTOMPADDING",(0,-1),(-1,-1),9),
    ]))
    story.append(_dre_t)
    if _margem is not None:
        story.append(Paragraph(f"Margem do período: <b>{f'{_margem:.1f}'.replace('.', ',')}%</b>",
                               ParagraphStyle("marg", fontName=F, fontSize=8.5, textColor=GREY,
                                             alignment=TA_RIGHT, spaceBefore=2)))

    if _resultado < 0:
        story.append(Spacer(1, 0.25*cm))
        _avbox = Table([[Paragraph(
            "<b>⚠️ Resultado negativo no período.</b> A prestadora não gerou receita própria "
            "suficiente para cobrir seus custos — indício de dependência de repasses do tomador.",
            ParagraphStyle("av", fontName=F, fontSize=8, textColor=colors.HexColor("#8a3a2e"),
                           leading=11))]], colWidths=[sw])
        _avbox.setStyle(TableStyle([("BACKGROUND",(0,0),(-1,-1), colors.HexColor("#fdf0ee")),
            ("BOX",(0,0),(-1,-1), 0.6, RED), ("LEFTPADDING",(0,0),(-1,-1),10),
            ("RIGHTPADDING",(0,0),(-1,-1),10), ("TOPPADDING",(0,0),(-1,-1),7),
            ("BOTTOMPADDING",(0,0),(-1,-1),7), ("ROUNDEDCORNERS",[5,5,5,5])]))
        story.append(_avbox)

    # ── 2. RESUMO POR COMPETÊNCIA ─────────────────────────────────────────────
    story.append(_secao("2", "Resumo por Competência", S))
    data = [["Competência", "Receita", "Despesa Pessoal", "Outras Despesas", "Impostos", "Resultado"]]
    for l in linhas:
        data.append([fper(l["competencia"]), brl(l["receita"], False), brl(l["despesa_pessoal"], False),
                     brl(l["despesa_geral"], False), brl(l.get("impostos", 0), False),
                     brl(l["resultado"], False)])
    if len(linhas) > 1:
        data.append(["TOTAL", brl(ctx.get("tot_receita", 0), False), brl(ctx.get("tot_pessoal", 0), False),
                     brl(ctx.get("tot_geral", 0), False), brl(ctx.get("tot_impostos", 0), False),
                     brl(_resultado, False)])
    story.append(_table(data, [sw*0.17, sw*0.18, sw*0.19, sw*0.16, sw*0.15, sw*0.15],
                        total=(len(linhas) > 1), align_from=1))

    # ── 3. DESPESAS E IMPOSTOS DETALHADOS POR COMPETÊNCIA ─────────────────────
    _tem_detalhe = any(l.get("despesas_detalhadas") for l in linhas)
    if _tem_detalhe:
        story.append(_secao("3", "Despesas e Impostos — Detalhamento", S))
        for l in linhas:
            _dets = l.get("despesas_detalhadas") or []
            if not _dets:
                continue
            story.append(Paragraph(fper(l["competencia"]), S["h3"]))
            data = [["Tipo", "Descrição", "Valor"]]
            for d in sorted(_dets, key=lambda x: -(x.get("valor") or 0)):
                _tipo = "Imposto" if d.get("categoria") == "imposto" else "Despesa"
                data.append([_tipo, str(d.get("descricao") or "—")[:55], brl(d.get("valor") or 0)])
            story.append(_table(data, [sw*0.18, sw*0.57, sw*0.25], font=7.6, align_from=2, head=TEAL))

    # ── ASSINATURAS ────────────────────────────────────────────────────────────
    story.append(Spacer(1, 1.2*cm))
    _assin_style = ParagraphStyle("assin", fontName=F, fontSize=8.5, textColor=INK,
                                  leading=13, alignment=TA_CENTER)
    _linha_assin = Table([[
        Paragraph(f"_______________________________<br/><b>{ctx.get('responsavel_empresa','') or '—'}</b>"
                 f"<br/>CPF: {ctx.get('cpf_empresa','')}", _assin_style),
        Paragraph(f"_______________________________<br/><b>Contador</b>"
                 f"<br/>CRC: {ctx.get('crc_contador','')}   CPF: {ctx.get('cpf_contador','')}",
                 _assin_style),
    ]], colWidths=[sw/2, sw/2])
    _linha_assin.setStyle(TableStyle([("VALIGN",(0,0),(-1,-1),"TOP"),
                                      ("LEFTPADDING",(0,0),(-1,-1),10),
                                      ("RIGHTPADDING",(0,0),(-1,-1),10)]))
    story.append(_linha_assin)

    story.append(Spacer(1, 0.6*cm))
    story.append(Paragraph(
        "DRE gerencial simplificada — não substitui a contabilidade oficial (balancete/DRE "
        f"contábil). Documento gerado em {hoje.strftime('%d/%m/%Y')} para uso interno e "
        "acompanhamento entre as partes.", S["small"]))

    painter = _bg_painter(empresa, rodape="DRE Gerencial · uso gerencial · LGPD")
    doc.build(story, onFirstPage=painter, onLaterPages=painter)
    return buf.getvalue()
