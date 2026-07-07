# -*- coding: utf-8 -*-
"""
diagnostico.py — Motor de inteligência de Departamento Pessoal.

Lê os dados do eSocial e gera ANÁLISES, RISCOS e RECOMENDAÇÕES como um
consultor de DP entregaria ao cliente — cada achado com interpretação,
severidade e fundamento legal (CLT, NRs, eSocial).

Cada insight é um dict:
  sev      : 'critico' | 'atencao' | 'ok' | 'info'
  cat      : categoria (Risco Trabalhista, Saúde Ocupacional, Custo, ...)
  titulo   : título curto
  analise  : o que os dados mostram (interpretação)
  acao     : recomendação prática
  base     : fundamento legal/normativo (opcional)
"""
from __future__ import annotations
from datetime import date
import pandas as pd


def _brl(v):
    try:
        s = "{:,.2f}".format(float(v))
        return "R$ " + s.replace(",", "X").replace(".", ",").replace("X", ".")
    except (ValueError, TypeError):
        return "R$ 0,00"


def gerar(ctx):
    """ctx: dict com métricas e DataFrames já filtrados pelo app.
    Espera as chaves: n_func, folha, inss_emp, fgts, custo_total, turnover,
    n_adm, n_des, des_df, afa_df, ferias_resumo, ferias_rows, exames_df,
    he_horas, he_valor, periodos, salario_medio, encargos_pct, var_folha,
    aposentadorias, sem_justa, rescisao_indireta, pcd, dependentes.
    """
    I = []
    def add(sev, cat, titulo, analise, acao="", base=""):
        I.append({"sev": sev, "cat": cat, "titulo": titulo,
                  "analise": analise, "acao": acao, "base": base})

    nf = ctx.get("n_func", 0) or 1
    folha = ctx.get("folha", 0)

    # ── RISCO TRABALHISTA ────────────────────────────────────────────────────
    ri = ctx.get("rescisao_indireta", 0)
    if ri:
        add("critico", "Risco Trabalhista",
            f"{ri} rescisão(ões) indireta(s) no período",
            "Na rescisão indireta o empregado alega falta grave do empregador (a 'justa "
            "causa do patrão'). É a modalidade de maior risco: se confirmada na Justiça, "
            "equivale à demissão sem justa causa, com todas as verbas + multa de 40% do FGTS, "
            "e frequentemente vem acompanhada de outras ações (horas extras, danos morais).",
            "Levantar os motivos alegados, reunir documentação de defesa e avaliar acordo "
            "com o jurídico antes de virar processo. Verificar se há padrão (mesmo gestor/setor).",
            "CLT art. 483")

    sjc = ctx.get("sem_justa", 0)
    if sjc:
        custo_est = sjc * ctx.get("salario_medio", 0) * 1.5
        add("atencao", "Risco Trabalhista",
            f"{sjc} demissão(ões) sem justa causa",
            f"Cada dispensa sem justa causa gera aviso prévio (até 90 dias), multa de 40% "
            f"sobre o FGTS depositado e liberação do saque. Custo rescisório estimado do "
            f"período: ~{_brl(custo_est)} (referência por salário médio).",
            "Confirmar se o caixa comporta as rescisões do mês e se o motivo está bem "
            "documentado (evita reversão para indireta).",
            "CLT art. 477 e 487; Lei 8.036/90 art. 18")

    # ── SAÚDE OCUPACIONAL ────────────────────────────────────────────────────
    afa = ctx.get("afa_df")
    if afa is not None and not afa.empty:
        longos = int((afa["dias"] > 15).sum())
        if longos:
            add("atencao", "Saúde Ocupacional",
                f"{longos} afastamento(s) superior(es) a 15 dias",
                "A partir do 16º dia de afastamento por doença, o pagamento passa a ser do "
                "INSS (auxílio por incapacidade), não mais da empresa. É preciso garantir o "
                "encaminhamento ao INSS e o controle do retorno (exame de retorno ao trabalho).",
                "Conferir se os afastados >15 dias foram encaminhados ao INSS e agendar exame "
                "de retorno (S-2220) antes do retorno às atividades.",
                "Lei 8.213/91 art. 60; NR-7")
        # concentração de doença
        doenca = int((afa["cod_motivo"] == "03").sum())
        if doenca >= max(5, nf * 0.15):
            add("atencao", "Saúde Ocupacional",
                f"{doenca} afastamentos por doença no período",
                "Volume relevante de afastamentos por doença pode indicar problemas de "
                "ergonomia, jornada, clima organizacional ou ambiente de trabalho.",
                "Avaliar com o SESMT/medicina do trabalho as causas mais frequentes e "
                "considerar ações de prevenção (ginástica laboral, revisão de postos).",
                "NR-1 (GRO/PGR), NR-17")

    ex = ctx.get("exames_df")
    if ex is not None and not ex.empty:
        inapto = int((ex["res_cod"] == "2").sum())
        if inapto:
            add("critico", "Saúde Ocupacional",
                f"{inapto} exame(s) ocupacional(is) com resultado INAPTO",
                "Funcionário considerado inapto não pode exercer a função sem readaptação. "
                "Manter o trabalhador na função após laudo de inaptidão expõe a empresa a "
                "autuação e a responsabilização em caso de acidente/doença.",
                "Readaptar a função ou afastar conforme o laudo médico. Registrar a conduta.",
                "NR-7 (PCMSO)")

    # ── CUSTO E PRODUTIVIDADE ────────────────────────────────────────────────
    he_val = ctx.get("he_valor", 0)
    if he_val and folha:
        pct = he_val / folha * 100
        if pct >= 5:
            add("atencao", "Custo & Produtividade",
                f"Horas extras = {pct:.1f}% da folha ({_brl(he_val)})",
                f"HE acima de ~5% da folha costuma sinalizar quadro subdimensionado ou má "
                f"distribuição de jornada. Pagar HE recorrente sai mais caro que contratar "
                f"(a HE tem adicional de 50%/100% e reflexos em DSR, férias e 13º).",
                "Comparar o custo da HE recorrente com o de uma nova contratação. Avaliar "
                "banco de horas (acordo) ou redimensionamento de equipe nos setores críticos.",
                "CLT art. 59; CF art. 7º XVI")

    tov = ctx.get("turnover", 0)
    if tov > 5:
        custo_rep = ctx.get("n_des", 0) * ctx.get("salario_medio", 0) * 2.0
        add("atencao", "Custo & Produtividade",
            f"Turnover de {tov:.1f}% (acima do saudável)",
            f"Rotatividade alta encarece a operação: rescisão + recrutamento + treinamento + "
            f"curva de aprendizado. Custo estimado de reposição no período: ~{_brl(custo_rep)} "
            f"(referência ~2x salário por substituição).",
            "Investigar os motivos de saída (entrevista de desligamento), revisar política "
            "salarial/benefícios e clima nos setores com mais saídas.",
            "")

    # encargos
    enc_pct = ctx.get("encargos_pct")
    if enc_pct is not None and enc_pct > 0:
        add("info", "Custo & Produtividade",
            f"Encargos representam {enc_pct:.1f}% sobre a remuneração",
            f"Cada R$ 1,00 de salário custa cerca de R$ {1 + enc_pct/100:.2f} à empresa "
            f"(INSS patronal + FGTS). É o 'custo invisível' da folha que o gestor precisa "
            f"considerar ao precificar produtos/serviços e ao planejar contratações.",
            "Usar o custo total (não o salário) nas decisões de preço e contratação.",
            "")

    # variação da folha
    var = ctx.get("var_folha")
    if var is not None and abs(var) >= 8:
        direc = "aumento" if var > 0 else "redução"
        add("info", "Custo & Produtividade",
            f"Folha teve {direc} de {abs(var):.1f}% no último mês",
            f"Variação relevante na folha entre competências. Pode refletir admissões/"
            f"desligamentos, reajustes, 13º, férias ou horas extras.",
            "Confirmar a causa da variação e refletir no fluxo de caixa projetado.",
            "")

    # ── PROVISÕES (passivo a constituir) ─────────────────────────────────────
    if folha:
        prov_ferias = folha * (1 + 1/3) / 12        # 1/12 da remuneração + 1/3, por mês
        prov_13 = folha / 12                          # 1/12 da remuneração por mês
        add("info", "Provisões",
            f"Provisão mensal estimada: Férias {_brl(prov_ferias)} + 13º {_brl(prov_13)}",
            f"A cada mês trabalhado, a empresa acumula obrigação de férias (1/12 + 1/3) e de "
            f"13º (1/12). Somando ~{_brl(prov_ferias + prov_13)}/mês de passivo que vira caixa "
            f"nas férias e em novembro/dezembro. Em 12 meses: ~{_brl((prov_ferias+prov_13)*12)}.",
            "Provisionar mensalmente esses valores para não comprometer o caixa quando o 13º "
            "e as férias forem pagos. Evita o 'aperto' de fim de ano.",
            "CLT art. 7º (13º Lei 4.090/62); CPC 25 (provisões)")

    # ── tudo certo? ──────────────────────────────────────────────────────────
    if not any(x["sev"] in ("critico", "atencao") for x in I):
        add("ok", "Resumo", "Nenhum risco crítico identificado no período",
            "Os indicadores de folha, encargos e movimentação estão dentro de parâmetros "
            "normais para o período analisado.", "Manter o acompanhamento mensal.", "")

    # ordena por severidade
    ordem = {"critico": 0, "atencao": 1, "info": 2, "ok": 3}
    I.sort(key=lambda x: ordem.get(x["sev"], 9))
    return I
