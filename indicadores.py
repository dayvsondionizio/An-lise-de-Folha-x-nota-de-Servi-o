# -*- coding: utf-8 -*-
"""
indicadores.py — Motor de indicadores no modelo do relatório profissional (Dash).

Cada indicador é computado como uma série mensal e exposto com:
  nome, categoria, série {período: valor}, valor atual, variação %, peso %,
  série secundária (taxa/peso), tipo de gráfico, descrição e fonte eSocial.

Replicamos o conjunto de indicadores que o eSocial fornece com precisão.
"""
from __future__ import annotations
import pandas as pd


def _serie(df, per_col, val_col, periodos, agg="sum"):
    """Soma (ou nunique) val_col por período, devolve lista alinhada a `periodos`."""
    if df is None or df.empty or per_col not in df.columns:
        return [0.0 for _ in periodos]
    if agg == "nunique":
        g = df.groupby(per_col)[val_col].nunique()
    else:
        g = df.groupby(per_col)[val_col].sum()
    return [float(g.get(p, 0)) for p in periodos]


def _var(serie):
    """Variação % do último valor vs penúltimo não-nulo."""
    vals = [v for v in serie]
    if len(vals) < 2:
        return None
    atual = vals[-1]
    ant = vals[-2]
    if ant == 0:
        return None
    return (atual - ant) / ant * 100


def construir(D, periodos, inss_per):
    """Devolve lista de indicadores prontos para renderizar.

    D: dict de DataFrames do parser. periodos: lista ordenada de 'AAAA-MM'.
    inss_per: dict {periodo: {apurado, segurado, patronal, base}} do eSocial (S-5011).
    """
    inss = D["bases_inss"]; fgts = D["bases_fgts"]; irrf = D["bases_irrf"]
    pag = D["pagamentos"]; cs = D["cs_patronal"]
    adm = D["admissoes"]; des = D["desligamentos"]; alt = D["alteracoes"]

    # normaliza colunas numéricas que possam faltar
    def col(df, c):
        if df is None or df.empty or c not in df.columns:
            return pd.Series(dtype=float)
        return pd.to_numeric(df[c], errors="coerce").fillna(0)

    if not inss.empty:
        inss = inss.copy()
        for c in ["tp11_i0","tp11_i1","tp21_i0","tp21_i1","tp31_i0","tp32_i0"]:
            if c not in inss.columns: inss[c] = 0.0
            inss[c] = pd.to_numeric(inss[c], errors="coerce").fillna(0)

    # ── séries-base por período ──────────────────────────────────────────────
    remun = _serie(fgts, "per_apur", "base_fgts", periodos) if not fgts.empty else _serie(inss, "per_apur", "tp11_i0", periodos)
    # remuneração bruta = base FGTS (melhor proxy). denominador dos "pesos".
    remun_safe = [r if r else 1 for r in remun]

    liq_folha = _serie(pag, "per_apur", "liq_folha", periodos) if not pag.empty else [0]*len(periodos)
    liq_resc = _serie(pag, "per_apur", "liq_rescisao", periodos) if not pag.empty else [0]*len(periodos)
    liq_13 = _serie(pag, "per_apur", "liq_13", periodos) if not pag.empty else [0]*len(periodos)
    liq_total = _serie(pag, "per_apur", "vr_liquido", periodos) if not pag.empty else [0]*len(periodos)

    # vrCpSeg (inss_seg_calc) é o desconto real. tp21 é base de cálculo. Usamos ambos.
    if not inss.empty and "inss_seg_calc" in inss.columns:
        inss["_inss_seg"] = pd.to_numeric(inss["inss_seg_calc"], errors="coerce").fillna(0)
    else:
        inss["_inss_seg"] = col(inss, "tp21_i0") + col(inss, "tp21_i1")
    inss_emp = _serie(inss, "per_apur", "_inss_seg", periodos)  # desconto real (total)
    inss_emp_m = _serie(inss, "per_apur", "tp21_i0", periodos)  # base mensal (p/ separar)
    inss_emp_13 = _serie(inss, "per_apur", "tp21_i1", periodos) # base 13°

    fgts_m = _serie(fgts, "per_apur", "fgts_mensal", periodos) if not fgts.empty else [0]*len(periodos)
    fgts_13 = _serie(fgts, "per_apur", "fgts_13", periodos) if not fgts.empty else [0]*len(periodos)
    fgts_tot = _serie(fgts, "per_apur", "deposito_fgts", periodos) if not fgts.empty else [0]*len(periodos)

    irrf_m = _serie(irrf, "per_apur", "irrf", periodos) if not irrf.empty else [0]*len(periodos)
    irrf_13 = _serie(irrf, "per_apur", "irrf_13", periodos) if not irrf.empty else [0]*len(periodos)
    irrf_tot = [a+b for a,b in zip(irrf_m, irrf_13)]

    inss_pat = [inss_per.get(p, {}).get("patronal", 0) for p in periodos]
    inss_apurado = [inss_per.get(p, {}).get("apurado", 0) for p in periodos]

    encargos = [a+b+c+d for a,b,c,d in zip(inss_emp, fgts_tot, irrf_tot, inss_pat)]

    # contagem de pessoas
    func = _serie(inss, "per_apur", "cpf", periodos, agg="nunique") if not inss.empty else \
           _serie(pag, "per_apur", "cpf", periodos, agg="nunique")

    # admissões/desligamentos por mês (pela data)
    def conta_por_mes(df, col_data):
        out = []
        if df is None or df.empty or col_data not in df.columns:
            return [0]*len(periodos)
        m = df[col_data].astype(str).str[:7]
        vc = m.value_counts()
        return [int(vc.get(p, 0)) for p in periodos]
    contratacoes = conta_por_mes(adm, "dt_adm")
    demissoes_n = conta_por_mes(des, "dt_deslig")

    # turnover = ((adm+dem)/2)/headcount
    turnover = []
    for a, d, f in zip(contratacoes, demissoes_n, func):
        turnover.append(((a+d)/2)/f*100 if f else 0)

    # promoções (S-2206): valor (soma novos salários) e contagem por mês
    promo_val = []
    promo_n = []
    if not alt.empty and "dt_alter" in alt.columns:
        alt2 = alt.copy()
        alt2["m"] = alt2["dt_alter"].astype(str).str[:7]
        alt2["novo_salario"] = pd.to_numeric(alt2["novo_salario"], errors="coerce").fillna(0)
        gv = alt2.groupby("m")["novo_salario"].sum()
        gn = alt2.groupby("m")["novo_salario"].count()
        promo_val = [float(gv.get(p,0)) for p in periodos]
        promo_n = [int(gn.get(p,0)) for p in periodos]
    else:
        promo_val = [0]*len(periodos); promo_n=[0]*len(periodos)

    custo_total = [r+p+f for r,p,f in zip(remun, inss_pat, fgts_tot)]
    total_folha = [lf+lr+l13+e for lf,lr,l13,e in zip(liq_folha, liq_resc, liq_13, encargos)]

    def peso(serie):
        return [v/b*100 for v,b in zip(serie, remun_safe)]

    # ── monta indicadores ─────────────────────────────────────────────────────
    I = []
    def add(nome, cat, serie, fonte, desc, fmt="brl", sec=None, sec_nome="", sec_fmt="pct", chart="barra_linha"):
        I.append({
            "nome": nome, "categoria": cat, "serie": serie,
            "atual": serie[-1] if serie else 0, "var": _var(serie),
            "fonte": fonte, "desc": desc, "fmt": fmt,
            "sec": sec, "sec_nome": sec_nome, "sec_fmt": sec_fmt, "chart": chart,
        })

    # FOLHA
    add("Remuneração Bruta", "Folha", remun, "S-5003",
        "Remuneração bruta total que serve de base ao FGTS (salários, adicionais, HE, 13º).",
        sec=None)
    add("Folha Líquida", "Folha", liq_folha, "S-1210",
        "Valor líquido dos salários mensais pagos (exclui rescisões e 13º).",
        sec=peso(liq_folha), sec_nome="Peso da Folha Líquida")
    add("13º Salário", "Folha", liq_13, "S-1210",
        "Pagamentos de 13º salário (perRef anual no S-1210).",
        sec=peso(liq_13), sec_nome="Peso do 13º")
    add("Rescisões pagas", "Folha", liq_resc, "S-1210",
        "Verbas rescisórias líquidas pagas (tpPgto=2 no S-1210).",
        sec=peso(liq_resc), sec_nome="Peso das Rescisões")
    add("Total da Folha", "Folha", total_folha, "S-1210 + S-5001/2/3",
        "Soma de folha líquida, 13º, rescisões e encargos do período.",
        sec=None)
    add("Custo Total p/ Empresa", "Folha", custo_total, "S-5003 + S-5011",
        "Remuneração + INSS patronal + FGTS = custo real para o negócio.")
    custo_func = [c/f if f else 0 for c,f in zip(custo_total, func)]
    add("Custo Médio por Funcionário", "Folha", custo_func, "Cálculo",
        "Custo total da folha dividido pelo número de funcionários.")

    # ENCARGOS
    add("Encargos Totais", "Encargos", encargos, "S-5001/2/3 + S-5011",
        "INSS (empregado + patronal) + FGTS + IRRF.",
        sec=peso(encargos), sec_nome="Peso dos Encargos")
    add("INSS Empregado", "Encargos", inss_emp, "S-5001",
        "Contribuição previdenciária descontada do empregado.",
        sec=peso(inss_emp), sec_nome="Peso s/ Remun.")
    add("INSS Empregado — Mensal", "Encargos", inss_emp_m, "S-5001 (ind13=0)",
        "INSS do empregado sobre a remuneração mensal.")
    add("INSS Empregado — 13º", "Encargos", inss_emp_13, "S-5001 (ind13=1)",
        "INSS do empregado sobre o 13º salário.")
    add("INSS Patronal", "Encargos", inss_pat, "S-5011",
        "Parte patronal efetivamente apurada pelo eSocial (vrCR − parte do segurado). "
        "Zero quando a empresa não recolhe CPP patronal (ex.: Simples Nacional).",
        sec=peso(inss_pat), sec_nome="Peso s/ Remun.")
    add("INSS Apurado (guia)", "Encargos", inss_apurado, "S-5011",
        "Contribuição previdenciária total apurada para recolhimento (infoCRContrib/vrCR).")
    add("FGTS", "Encargos", fgts_tot, "S-5003",
        "Depósito de FGTS (8% sobre a remuneração).",
        sec=peso(fgts_tot), sec_nome="Peso s/ Remun.")
    add("FGTS — Mensal", "Encargos", fgts_m, "S-5003",
        "FGTS sobre a remuneração mensal.")
    add("FGTS — 13º", "Encargos", fgts_13, "S-5003",
        "FGTS sobre o 13º salário.")
    add("IRRF", "Encargos", irrf_tot, "S-5002",
        "Imposto de Renda Retido na Fonte.",
        sec=peso(irrf_tot), sec_nome="Peso s/ Remun.")
    add("IRRF — Mensal", "Encargos", irrf_m, "S-5002",
        "IRRF sobre rendimentos mensais.")
    add("IRRF — 13º", "Encargos", irrf_13, "S-5002",
        "IRRF sobre o 13º salário.")

    # MOVIMENTAÇÃO
    add("Número de Funcionários", "Movimentação", func, "S-5001/S-1210",
        "Quantidade de funcionários com remuneração no período.", fmt="int",
        sec=None)
    add("Contratações", "Movimentação", [float(x) for x in contratacoes], "S-2200",
        "Admissões registradas no período.", fmt="int")
    add("Demissões", "Movimentação", [float(x) for x in demissoes_n], "S-2299",
        "Desligamentos registrados no período (sem duplicar retificações).", fmt="int")
    saldo = [c-d for c,d in zip(contratacoes, demissoes_n)]
    add("Saldo de Pessoal", "Movimentação", [float(x) for x in saldo], "S-2200 − S-2299",
        "Contratações menos demissões no período.", fmt="int")
    add("Turnover", "Movimentação", turnover, "S-2200/S-2299",
        "Rotatividade = média de (admissões + demissões) ÷ headcount.", fmt="pct")

    # PROMOÇÕES
    add("Promoções / Reajustes (valor)", "Promoções", promo_val, "S-2206",
        "Soma dos novos salários nas alterações contratuais do período.")
    add("Número de Promoções", "Promoções", [float(x) for x in promo_n], "S-2206",
        "Quantidade de alterações contratuais (reajuste/cargo).", fmt="int")

    return I


def composicoes(D, periodos, inss_per):
    """Indicadores de composição (pizza): rateio da folha, motivos de desligamento."""
    inss = D["bases_inss"]; fgts = D["bases_fgts"]; irrf = D["bases_irrf"]
    pag = D["pagamentos"]; des = D["desligamentos"]
    out = {}

    # Rateio da folha: líquido × encargos
    liq = pag["vr_liquido"].sum() if (pag is not None and not pag.empty) else 0
    inss_emp = (pd.to_numeric(inss.get("inss_seg_calc", inss.get("tp21_i0",0)),
                             errors="coerce").fillna(0).sum()) if not inss.empty else 0
    fgts_t = fgts["deposito_fgts"].sum() if not fgts.empty else 0
    irrf_t = irrf["irrf"].sum() if not irrf.empty else 0
    pat_t = sum(v.get("patronal", 0) for v in inss_per.values())
    out["rateio"] = {
        "Folha Líquida": liq,
        "INSS (emp+pat)": inss_emp + pat_t,
        "FGTS": fgts_t,
        "IRRF": irrf_t,
    }

    # Motivos de desligamento
    if des is not None and not des.empty:
        out["motivos_deslig"] = des["motivo"].value_counts().to_dict()
    else:
        out["motivos_deslig"] = {}
    return out
