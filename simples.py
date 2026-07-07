# -*- coding: utf-8 -*-
"""
simples.py — Cálculo oficial do Simples Nacional (alíquota efetiva + repartição do CPP).

Fórmula (LC 123/2006, Resolução CGSN 140/2018):
    alíquota efetiva = (RBT12 × alíquota_nominal − parcela_a_deduzir) ÷ RBT12
    CPP = receita × alíquota_efetiva × %repartição_CPP(anexo, faixa)

Tabelas conferidas contra PGDAS real (Anexo I e III batem centavo a centavo).
Fonte: Resolução CGSN 140/2018 (Anexos I e III).
"""

# (limite RBT12, alíquota nominal, parcela a deduzir) por faixa
TABELAS = {
    "I": [(180000.0, 0.040, 0.0), (360000.0, 0.073, 5940.0),
          (720000.0, 0.095, 13860.0), (1800000.0, 0.107, 22500.0),
          (3600000.0, 0.143, 87300.0), (4800000.0, 0.190, 378000.0)],
    "II": [(180000.0, 0.045, 0.0), (360000.0, 0.078, 5940.0),
           (720000.0, 0.100, 13860.0), (1800000.0, 0.112, 22500.0),
           (3600000.0, 0.147, 85500.0), (4800000.0, 0.300, 720000.0)],
    "III": [(180000.0, 0.060, 0.0), (360000.0, 0.112, 9360.0),
            (720000.0, 0.135, 17640.0), (1800000.0, 0.160, 35640.0),
            (3600000.0, 0.210, 125640.0), (4800000.0, 0.330, 648000.0)],
    "IV": [(180000.0, 0.045, 0.0), (360000.0, 0.090, 8100.0),
           (720000.0, 0.102, 12420.0), (1800000.0, 0.140, 39780.0),
           (3600000.0, 0.220, 183780.0), (4800000.0, 0.330, 828000.0)],
    "V": [(180000.0, 0.155, 0.0), (360000.0, 0.180, 4500.0),
          (720000.0, 0.195, 9900.0), (1800000.0, 0.205, 17100.0),
          (3600000.0, 0.230, 62100.0), (4800000.0, 0.305, 540000.0)],
}
# % de repartição do CPP por faixa (fração do DAS que é CPP).
# Anexo IV: CPP NÃO está no DAS (é recolhido à parte, ~20% sobre a folha) → 0 aqui.
CPP_REPART = {
    "I":   [0.4150, 0.4150, 0.4200, 0.4200, 0.4200, 0.4210],
    "II":  [0.3750, 0.3750, 0.3750, 0.3750, 0.3750, 0.2350],
    "III": [0.4340, 0.4340, 0.4340, 0.4340, 0.4340, 0.3050],
    "IV":  [0.0, 0.0, 0.0, 0.0, 0.0, 0.0],
    "V":   [0.2885, 0.2785, 0.2385, 0.2385, 0.2385, 0.2950],
}


def anexo_de_categoria(cat):
    """Mapeia a categoria da receita (do PGDAS) para o anexo do Simples."""
    c = (cat or "").lower()
    if "revenda" in c or "comérci" in c or "comerci" in c:
        return "I"
    # serviços não sujeitos ao fator r → Anexo III (padrão desta estrutura)
    return "III"


def _faixa(rbt12, anexo):
    tab = TABELAS.get(anexo, TABELAS["III"])
    for i, (lim, al, pd) in enumerate(tab):
        if rbt12 <= lim:
            return i, al, pd
    return len(tab) - 1, tab[-1][1], tab[-1][2]


def aliquota_efetiva(rbt12, anexo="III"):
    """Alíquota efetiva (fração, ex.: 0.14525) e índice da faixa. None se sem RBT12."""
    if not rbt12 or rbt12 <= 0:
        return None
    i, al, pd = _faixa(rbt12, anexo)
    return max(0.0, (rbt12 * al - pd) / rbt12), i


def cpp(receita, rbt12, anexo="III"):
    """CPP oficial = receita × alíquota_efetiva × %repartição_CPP. None se sem RBT12."""
    r = aliquota_efetiva(rbt12, anexo)
    if r is None:
        return None
    ae, i = r
    return receita * ae * CPP_REPART.get(anexo, CPP_REPART["III"])[i]
