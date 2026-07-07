# -*- coding: utf-8 -*-
"""
pgdas.py — Extrai o INSS/CPP (e a Receita Bruta) do extrato do PGDAS-D.

No Simples Nacional, a contribuição patronal (CPP) é recolhida dentro do DAS e
NÃO aparece no eSocial. Este módulo lê o PDF do PGDAS-D e captura, por período
de apuração, o valor de INSS/CPP do 'Total do Débito Exigível' — para somar ao
custo mensal da folha. A leitura é best-effort; o usuário confere/edita depois.
"""
import re
import pdfplumber


def _to_float(s):
    try:
        return float(str(s).replace(".", "").replace(",", "."))
    except (ValueError, TypeError):
        return 0.0


def _cpp_apos(lines, idx_label):
    """Dado o índice de um rótulo 'Total do Débito ...', acha o header com
    INSS/CPP e devolve (cpp, total) da linha de números.
    Ordem das colunas: IRPJ CSLL COFINS PIS CPP ICMS IPI ISS Total."""
    for j in range(idx_label, min(idx_label + 4, len(lines))):
        if "INSS/CPP" in lines[j].upper():
            for k in range(j + 1, min(j + 3, len(lines))):
                nums = re.findall(r"\d[\d.]*,\d{2}", lines[k])
                if len(nums) >= 9:
                    return _to_float(nums[4]), _to_float(nums[8])
    return None, None


def extrair(fileobj):
    """Lê um PDF de PGDAS-D e devolve dict:
       {competencia 'AAAA-MM', cpp, receita, declaracao, ok}.
    Retorna None se não parecer um PGDAS."""
    try:
        with pdfplumber.open(fileobj) as pdf:
            text = "\n".join((pg.extract_text() or "") for pg in pdf.pages)
    except Exception:
        return None
    if "INSS/CPP" not in text.upper() and "SIMPLES NACIONAL" not in text.upper():
        return None
    lines = text.split("\n")

    # competência (início do período de apuração)
    comp = None
    m = re.search(r"Per[ií]odo de Apura[çc][ãa]o:\s*(\d{2})/(\d{2})/(\d{4})", text)
    if m:
        comp = f"{m.group(3)}-{m.group(2)}"

    # CPP/DAS: preferir 'Total do Débito Exigível'; senão 'Declarado (exigível + suspenso)'
    cpp = das = None
    for i, ln in enumerate(lines):
        if re.search(r"Total do D[ée]bito Exig[íi]vel", ln, re.I):
            cpp, das = _cpp_apos(lines, i)
            if cpp is not None:
                break
    if cpp is None:
        for i, ln in enumerate(lines):
            if re.search(r"Total do D[ée]bito Declarado", ln, re.I):
                cpp, das = _cpp_apos(lines, i)
                if cpp is not None:
                    break

    # receita bruta do PA (competência)
    receita = None
    mr = re.search(r"Receita Bruta do PA.*?([\d.]+,\d{2})", text)
    if mr:
        receita = _to_float(mr.group(1))

    md = re.search(r"N[úu]mero da Declara[çc][ãa]o:\s*([\d.]+)", text)
    decl = md.group(1) if md else ""

    # anexo (ex.: 'pelo Anexo III, ...') e alíquota efetiva (DAS ÷ receita)
    ma = re.search(r"Anexo\s+([IVX]+)", text)
    anexo = ma.group(1) if ma else ""
    aliq_efetiva = round(das / receita * 100, 2) if (das and receita) else None

    # CNPJ (formato 00.000.000/0000-00) → só dígitos
    mc = re.search(r"\d{2}\.\d{3}\.\d{3}/\d{4}-\d{2}", text)
    cnpj = re.sub(r"\D", "", mc.group(0)) if mc else ""

    # nome, RBT12, fator R
    mn = re.search(r"Nome empresarial:\s*(.+)", text)
    nome = mn.group(1).strip() if mn else ""
    mrbt = re.search(r"doze meses anteriores\s*\n\s*([\d.]+,\d{2})", text)
    rbt12 = _to_float(mrbt.group(1)) if mrbt else None
    mfr = re.search(r"Fator r\s*=?\s*(.+)", text, re.I)
    fator_r = mfr.group(1).strip() if mfr else ""

    # ── ATIVIDADES: segrega a receita por tipo (com/sem ST, fator R, serviço) ──
    atividades = []
    for bloco in text.split("Valor do Débito por Tributo para a Atividade")[1:]:
        m_rec = re.search(r"Receita Bruta Informada:\s*R\$\s*([\d.]+,\d{2})", bloco)
        if not m_rec:
            continue
        rec = _to_float(m_rec.group(1))
        desc = " ".join(bloco.split("Receita Bruta Informada")[0].split())
        # linha de tributos da atividade
        cpp_a = None
        lb = bloco.split("\n")
        for i, ln in enumerate(lb):
            if "INSS/CPP" in ln.upper():
                for k in range(i + 1, min(i + 3, len(lb))):
                    nums = re.findall(r"\d[\d.]*,\d{2}", lb[k])
                    if len(nums) >= 9:
                        cpp_a = _to_float(nums[4]); break
                break
        d = desc.lower()
        # anexo detectado na descrição da atividade (ex.: "tributados pelo Anexo III")
        ma2 = re.search(r"anexo\s+([ivx]+)", d)
        anexo_at = ma2.group(1).upper() if ma2 else None
        if "servi" in d:
            if "não sujeit" in d or "nao sujeit" in d:
                cat = "Serviços — não sujeitos ao fator R"
            elif "sujeit" in d and "fator" in d:
                cat = "Serviços — sujeitos ao fator R"
            else:
                cat = "Serviços"
            anexo_at = anexo_at or "III"
        elif "com substitui" in d:
            cat = "Revenda — com substituição tributária"
            anexo_at = anexo_at or "I"
        elif "sem substitui" in d:
            cat = "Revenda — sem substituição tributária"
            anexo_at = anexo_at or "I"
        elif "industri" in d or "indústri" in d:
            cat = "Indústria"
            anexo_at = anexo_at or "II"
        else:
            cat = "Outros"
            anexo_at = anexo_at or "III"
        atividades.append({"descricao": desc[:140], "categoria": cat,
                           "receita": rec, "cpp": cpp_a, "anexo": anexo_at})
    # agrega por categoria
    segmentos = {}
    for a in atividades:
        s = segmentos.setdefault(a["categoria"], {"receita": 0.0, "cpp": 0.0, "anexo": a["anexo"]})
        s["receita"] += a["receita"]
        s["cpp"] += (a["cpp"] or 0.0)

    cpp_ratio = (cpp / receita) if (cpp and receita) else None   # CPP como fração da receita

    return {"competencia": comp, "cpp": cpp, "das_total": das, "receita": receita,
            "anexo": anexo, "aliq_efetiva": aliq_efetiva, "cnpj": cnpj, "nome": nome,
            "rbt12": rbt12, "fator_r": fator_r, "atividades": atividades,
            "segmentos": segmentos, "cpp_ratio": cpp_ratio,
            "declaracao": decl, "ok": bool(comp and cpp is not None)}
