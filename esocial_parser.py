# -*- coding: utf-8 -*-
"""
esocial_parser.py
Motor de extração de dados dos XMLs do eSocial (eventos de folha e cadastro).
Lê ZIPs/XMLs e devolve DataFrames estruturados por evento.

Eventos suportados:
  S-2190/S-2200  Admissão (cadastro completo do trabalhador)
  S-2205         Alteração cadastral
  S-2206         Alteração contratual (reajuste / mudança de cargo)
  S-2230         Afastamento temporário
  S-2240         Exposição a agentes nocivos (insalubre/periculoso)
  S-2299         Desligamento (com verbas rescisórias detalhadas)
  S-1010         Tabela de rubricas (nomes/natureza)
  S-1200         Remuneração (rubricas por trabalhador)
  S-1210         Pagamentos (líquido pago, dependentes IRRF)
  S-5001         Bases INSS (totalizador oficial)
  S-5002         IRRF (totalizador oficial, dependentes)
  S-5003         Bases FGTS (totalizador oficial)
"""
from __future__ import annotations
import zipfile, io, re
import xml.etree.ElementTree as ET
from datetime import datetime, date
import pandas as pd

try:
    from dateutil.relativedelta import relativedelta
    HAS_DATEUTIL = True
except ImportError:
    HAS_DATEUTIL = False


# ─────────────────────────────────────────────────────────────────────────────
# TABELAS DE DOMÍNIO eSocial
# ─────────────────────────────────────────────────────────────────────────────
MOTIVO_DESLIG = {
    "01": "Rescisão sem justa causa (empregador)",
    "02": "Rescisão indireta (culpa do empregador)",
    "03": "Rescisão por justa causa",
    "04": "Pedido de demissão",
    "05": "Término do contrato por prazo determinado",
    "06": "Aposentadoria espontânea",
    "07": "Aposentadoria por idade compulsória",
    "08": "Aposentadoria por invalidez",
    "09": "Rescisão por culpa recíproca",
    "10": "Falecimento do empregado",
    "11": "Transferência",
    "12": "Mudança de CPF",
    "14": "Rescisão antecipada (prazo determinado) por iniciativa do empregador",
    "17": "Rescisão antecipada (prazo determinado) por iniciativa do empregado",
    "20": "Rescisão sem justa causa (rural)",
    "25": "Extinção do contrato por prazo determinado",
    "27": "Rescisão por falência/encerramento da empresa",
    "31": "Rescisão por culpa recíproca",
    "33": "Outros (sem ônus para o empregador)",
}
# Classificação de custo da rescisão para o gestor
RESCISAO_ONUS = {
    "01": ("Alta", "Aviso prévio + multa 40% FGTS + verbas"),
    "02": ("Alta", "Equiparada à sem justa causa (judicial)"),
    "03": ("Baixa", "Sem aviso/multa — só saldo e férias venc."),
    "04": ("Média", "Sem multa 40%; aviso pode ser descontado"),
    "05": ("Baixa", "Término natural do contrato"),
    "06": ("Baixa", "Aposentadoria"),
    "07": ("Baixa", "Aposentadoria compulsória"),
    "08": ("Baixa", "Invalidez"),
    "09": ("Média", "Multa 20% (culpa recíproca)"),
    "10": ("Baixa", "Falecimento"),
    "14": ("Alta", "Antecipação por iniciativa do empregador"),
    "17": ("Média", "Antecipação por iniciativa do empregado"),
}
MOTIVO_AFAST = {
    "01": "Acidente/doença do trabalho",
    "03": "Doença / acidente não relacionado ao trabalho",
    "04": "Licença-maternidade",
    "05": "Licença-maternidade (adoção/guarda)",
    "06": "Licença-maternidade (antecipação/prorrogação)",
    "07": "Acompanhamento (membro família)",
    "08": "Afastamento por licença não remunerada/sem vencimento",
    "10": "Afastamento por cárcere",
    "11": "Cessão / requisição",
    "12": "Mandato sindical",
    "14": "Mandato eleitoral",
    "15": "Licença-maternidade (120 dias)",
    "16": "Licença não remunerada (Lei)",
    "17": "Afastamento temporário (outros)",
    "18": "Suspensão disciplinar",
    "19": "Aposentadoria por invalidez",
    "20": "Mandato eleitoral (afastamento)",
    "21": "Licença remunerada",
    "22": "Inatividade (intermitente)",
    "23": "Afastamento qualificação (Lei 13.467)",
    "33": "Licença-maternidade prorrogada",
}
GRAU_INSTR = {
    "01": "Analfabeto", "02": "Até 4ª série incompleta",
    "03": "4ª série completa", "04": "5ª a 8ª série (fund. incompleto)",
    "05": "Ensino fundamental completo", "06": "Ensino médio incompleto",
    "07": "Ensino médio completo", "08": "Superior incompleto",
    "09": "Superior completo", "10": "Pós-graduação/especialização",
    "11": "Mestrado", "12": "Doutorado",
}
EST_CIVIL = {"1": "Solteiro(a)", "2": "Casado(a)", "3": "Divorciado(a)",
             "4": "Separado(a)", "5": "Viúvo(a)"}
RACA_COR = {"1": "Branca", "2": "Preta", "3": "Parda", "4": "Amarela",
            "5": "Indígena", "6": "Não informado"}
SEXO = {"M": "Masculino", "F": "Feminino"}
TP_CONTR = {"1": "Prazo indeterminado", "2": "Prazo determinado",
            "3": "Prazo determinado (obra/serviço)"}
TP_JORNADA = {"1": "Jornada com horário diário fixo e folga fixa",
              "2": "Jornada com horário diário fixo e folga variável",
              "3": "Jornada com horário diário variável e folga fixa",
              "4": "Jornada com horário diário variável e folga variável",
              "5": "Jornada com horário diário e folga variáveis",
              "6": "Demais tipos de jornada", "9": "Jornada 12x36"}
CATEGORIA = {
    "101": "Empregado CLT (geral)", "102": "Empregado rural",
    "103": "Empregado aprendiz", "104": "Empregado doméstico",
    "105": "Empregado contrato verde-amarelo", "106": "Trabalhador temporário",
    "111": "Empregado intermitente", "201": "Trabalhador avulso portuário",
    "301": "Servidor público", "701": "Contribuinte individual (autônomo)",
    "722": "Estagiário", "771": "Dirigente sindical",
}

# Dicionário de rubricas comuns (códigos padrão do Questor — sistema de folha).
# Usado para nomear/classificar rubricas do S-1200 quando o S-1010 não as traz.
# categoria: P=Provento, D=Desconto, B=Benefício/Vantagem, I=Informativa, A=Auxílio
RUBRICAS_PADRAO = {
    "1":  ("P", "Salários Normais"),         "19": ("P", "Licença Médica"),
    "23": ("D", "Faltas Diurnas"),            "25": ("D", "Faltas DSR Diurnas"),
    "33": ("P", "Saldo de Salário"),          "35": ("P", "Horas Extras"),
    "53": ("P", "Aviso Prévio"),              "59": ("P", "DSR"),
    "64": ("P", "Periculosidade"),            "71": ("D", "Faltas Dias"),
    "73": ("D", "DSR Faltas Dias"),           "80": ("P", "Adiantamento Salarial"),
    "82": ("P", "Gratificação de Função"),    "85": ("P", "Pró-Labore"),
    "98": ("P", "Prêmio"),                    "110": ("P", "Licença-Maternidade"),
    "150": ("B", "Salário Família"),          "161": ("D", "Estouro do Mês Anterior"),
    "162": ("P", "13º Compl. Lic.Maternidade"),"163": ("B", "Estouro do Mês"),
    "200": ("A", "Auxílio Doença"),           "310": ("D", "Desconto Diverso"),
    "358": ("P", "Férias Diurnas"),           "360": ("P", "Méd. HE s/ Férias"),
    "364": ("P", "Méd. Eventuais s/ Férias"), "386": ("P", "1/3 sobre Férias"),
    "388": ("P", "Diferenças de Férias"),     "390": ("P", "Abono Pecuniário"),
    "392": ("P", "Méd. Eventuais Abono"),     "394": ("P", "Méd. HE Abono"),
    "416": ("P", "1/3 Abono Pecuniário"),     "418": ("P", "Diferença Abono"),
    "448": ("P", "Aviso Prévio Indenizado"),  "469": ("D", "Desconto Adiant. Abono"),
    "510": ("P", "13º Salário Proporcional"), "524": ("P", "Méd. Eventuais 13º"),
    "540": ("P", "13º Salário Indenizado"),   "588": ("D", "Indenização Art. 480 CLT"),
    "630": ("P", "Férias Vencidas"),          "638": ("P", "Méd. HE s/ Férias Venc."),
    "658": ("P", "Férias"),                   "662": ("P", "Periculosidade s/ Férias"),
    "668": ("P", "Méd. HE s/ Férias Prop."),  "672": ("P", "Méd. Eventuais s/ Férias"),
    "678": ("P", "1/3 Férias Proporcionais"), "683": ("P", "Recesso Proporcional"),
    "703": ("P", "Antecipação de Abono"),     "704": ("P", "Antecip. 1/3 Abono"),
    "705": ("P", "Antecipação Férias"),       "709": ("P", "Antecipação Diversos"),
    "710": ("P", "Devolução INSS"),           "750": ("P", "13º Proporcional"),
    "804": ("D", "Atrasos"),                  "808": ("D", "Desconto Diverso"),
    "813": ("D", "Desconto Diverso"),         "816": ("D", "Vale Transporte"),
    "820": ("D", "Desconto Adiantamento"),    "827": ("D", "Perdas e Danos"),
    "868": ("P", "Auxílio Transporte"),       "890": ("D", "Desconto Adto Férias"),
    "896": ("B", "Valor Líquido Negativo"),   "970": ("P", "Férias Proporcionais"),
    "980": ("P", "Méd. HE Férias Prop."),     "995": ("P", "Bolsa Estudo"),
    "996": ("P", "1/3 Férias Proporcionais"), "1021": ("I", "Licença Sem Remuneração"),
    "1027": ("D", "Empréstimo"),              "1028": ("D", "Empréstimo Férias"),
    "1048": ("D", "Devolução VT Antecipado"), "1049": ("P", "Auxílio Maternidade"),
    "1050": ("P", "Reembolso Desc. Indevido"),"1051": ("P", "Adicional Quebra de Caixa"),
    "1445": ("D", "Plano de Saúde Mensal"),   "1448": ("D", "Plano de Saúde Férias"),
    "1866": ("D", "Taxa Assistencial/Negocial"),"1895": ("D", "Desconto Líquido"),
    "1900": ("I", "FGTS"),                    "1901": ("I", "FGTS (compl.)"),
    "1902": ("I", "FGTS s/ Férias"),          "1903": ("I", "FGTS s/ Aviso Prévio"),
    "1904": ("I", "FGTS s/ 13º"),             "1908": ("I", "FGTS Multa - Depósito"),
    "1916": ("I", "FGTS GRFC"),               "1917": ("I", "FGTS 13º GFD"),
    "1918": ("I", "FGTS s/ Férias GRFC"),     "1920": ("I", "FGTS (informativo)"),
    "1921": ("I", "FGTS (informativo)"),      "1950": ("D", "INSS"),
    "1951": ("D", "INSS s/ 13º Salário"),     "1952": ("D", "INSS s/ Férias"),
    "1953": ("D", "INSS (compl.)"),           "2025": ("P", "Licença Médica Diurna"),
    "2032": ("D", "Provisão Empréstimo"),     "4004": ("D", "Empréstimo Crédito Trab."),
    "4005": ("P", "Devol. Empréstimo Férias"),"4006": ("P", "Devol. Empréstimo"),
    "4007": ("P", "Devol. Empréstimo Adto"),  "4008": ("I", "Planos de Saúde - Fatura"),
}
RUBR_CATEGORIA_NOME = {"P": "Provento", "D": "Desconto", "B": "Benefício/Vantagem",
                       "I": "Informativa", "A": "Auxílio (INSS)"}


# ─────────────────────────────────────────────────────────────────────────────
# HELPERS
# ─────────────────────────────────────────────────────────────────────────────
def _tag(el):
    return el.tag.split("}")[-1]

def _first(root, name):
    """Primeiro valor de uma tag em qualquer namespace."""
    for el in root.iter():
        if _tag(el) == name and el.text and el.text.strip():
            return el.text.strip()
    return None

def _all(root, name):
    return [el.text.strip() for el in root.iter()
            if _tag(el) == name and el.text and el.text.strip()]

def _float(v, default=0.0):
    if v is None:
        return default
    try:
        return float(str(v).replace(",", "."))
    except (ValueError, TypeError):
        return default

def _parse_date(s):
    if not s:
        return None
    try:
        return datetime.strptime(s.strip(), "%Y-%m-%d").date()
    except (ValueError, AttributeError):
        return None

def tipo_evento(fname):
    m = re.search(r"\.(S-\d{4})", fname, re.IGNORECASE)
    return m.group(1).upper() if m else "OUTRO"


# ─────────────────────────────────────────────────────────────────────────────
# PARSERS POR EVENTO
# ─────────────────────────────────────────────────────────────────────────────
def parse_s2200(root, fname):
    """Admissão / cadastro inicial — perfil completo do trabalhador."""
    cpf = _first(root, "cpfTrab")
    dt_adm = _first(root, "dtAdm")
    if not cpf and not dt_adm:
        return None

    # localização do nrLograd para montar endereço resumido
    bairro = _first(root, "bairro")
    municipio = _first(root, "codMunic")
    uf = _first(root, "uf")

    return {
        "cpf": cpf,
        "nome": _first(root, "nmTrab") or "",
        "matricula": _first(root, "matricula") or "",
        "sexo": _first(root, "sexo") or "",
        "raca_cor": _first(root, "racaCor") or "",
        "est_civil": _first(root, "estCiv") or "",
        "grau_instr": _first(root, "grauInstr") or "",
        "dt_nasc": _first(root, "dtNascto"),
        "dt_adm": dt_adm,
        "dt_term": _first(root, "dtTerm"),
        "cargo": _first(root, "nmCargo") or "",
        "cbo": _first(root, "CBOCargo") or "",
        "cod_categ": _first(root, "codCateg") or "",
        "salario": _float(_first(root, "vrSalFx")),
        "und_sal": _first(root, "undSalFixo") or "",
        "tp_contr": _first(root, "tpContr") or "",
        "tp_jornada": _first(root, "tpJornada") or "",
        "horas_sem": _float(_first(root, "qtdHrsSem")),
        "desc_jornada": _first(root, "dscJorn") or "",
        "email": _first(root, "emailPrinc") or "",
        "bairro": bairro or "", "municipio": municipio or "", "uf": uf or "",
        # pessoa com deficiência (cota PCD - Lei 8.213/91)
        "pcd": any(_first(root, t) == "S" for t in
                   ("defFisica", "defVisual", "defAuditiva", "defMental", "defIntelectual")),
        "reab": _first(root, "reabReadap") == "S",
        "nr_recibo": _first(root, "nrRecibo") or "",
        "evento": tipo_evento(fname),
    }

def parse_s2206(root, fname):
    """Alteração contratual (reajuste salarial / mudança de cargo)."""
    cpf = _first(root, "cpfTrab")
    mat = _first(root, "matricula")
    if not cpf and not mat:
        return None
    return {
        "cpf": cpf, "matricula": mat or "",
        "cargo": _first(root, "nmCargo") or "",
        "cbo": _first(root, "CBOCargo") or "",
        "novo_salario": _float(_first(root, "vrSalFx")),
        "dt_alter": _first(root, "dtAlteracao") or _first(root, "dtAlter") or _first(root, "dtEf"),
        "nr_recibo": _first(root, "nrRecibo") or "",
    }

def parse_s2230(root, fname):
    """Afastamento temporário."""
    dt_ini = _first(root, "dtIniAfast")
    if not dt_ini:
        return None
    dt_fim = _first(root, "dtTermAfast")
    cod = _first(root, "codMotAfast") or ""
    d1, d2 = _parse_date(dt_ini), _parse_date(dt_fim)
    dias = (d2 - d1).days + 1 if (d1 and d2) else None
    return {
        "cpf": _first(root, "cpfTrab"),
        "matricula": _first(root, "matricula") or "",
        "dt_ini": dt_ini, "dt_fim": dt_fim,
        "cod_motivo": cod, "motivo": MOTIVO_AFAST.get(cod, f"Motivo {cod}"),
        "dias": dias if dias is not None else 0,
        "nr_recibo": _first(root, "nrRecibo") or "",
    }

# Tipos de exame ocupacional (S-2220) e resultado do ASO
TP_EXAME = {"0": "Admissional", "1": "Periódico", "2": "Retorno ao trabalho",
            "3": "Mudança de função", "4": "Monitoração pontual", "9": "Demissional"}
RES_ASO = {"1": "Apto", "2": "Inapto"}

def parse_s2220(root, fname):
    """Monitoramento da saúde (ASO — atestado de saúde ocupacional)."""
    cpf = _first(root, "cpfTrab")
    dt_aso = _first(root, "dtAso")
    if not cpf or not dt_aso:
        return None
    tp = _first(root, "tpExameOcup") or ""
    res = _first(root, "resAso") or ""
    return {
        "cpf": cpf, "matricula": _first(root, "matricula") or "",
        "dt_aso": dt_aso, "dt_exame": _first(root, "dtExm"),
        "tp_exame": TP_EXAME.get(tp, f"Tipo {tp}"), "tp_cod": tp,
        "resultado": RES_ASO.get(res, res), "res_cod": res,
        "medico": _first(root, "nmMed") or "",
        "nr_recibo": _first(root, "nrRecibo") or "",
    }

def parse_s3000(root, fname):
    """Exclusão de evento — marca o recibo do evento que foi cancelado."""
    rec = _first(root, "nrRecEvt")
    if not rec:
        return None
    return {"tp_evento": _first(root, "tpEvento") or "",
            "nr_rec_excluido": rec, "cpf": _first(root, "cpfTrab") or ""}

def parse_s2240(root, fname):
    """Exposição a agentes nocivos."""
    cpf = _first(root, "cpfTrab")
    if not cpf:
        return None
    return {
        "cpf": cpf, "matricula": _first(root, "matricula") or "",
        "dt_ini": _first(root, "dtIniCondicao"),
        "setor": _first(root, "dscSetor") or "",
        "ag_nocivo": _first(root, "codAgNoc") or "",
        "atividade": (_first(root, "dscAtivDes") or "")[:200],
    }

def parse_s2299(root, fname):
    """Desligamento + verbas rescisórias detalhadas."""
    dt = _first(root, "dtDeslig")
    if not dt:
        return None
    cod = _first(root, "mtvDeslig") or ""
    # soma das verbas rescisórias (todas as rubricas detVerbas)
    total_verbas = 0.0
    ns_uri = None
    for el in root.iter():
        if _tag(el) == "evtDeslig":
            ns_uri = el.tag[el.tag.find("{")+1:el.tag.find("}")] if "{" in el.tag else None
            break
    # somar vrRubr apenas dentro de detVerbas
    for el in root.iter():
        if _tag(el) == "detVerbas":
            for ch in el:
                if _tag(ch) == "vrRubr":
                    total_verbas += _float(ch.text)
    onus, onus_desc = RESCISAO_ONUS.get(cod, ("—", ""))
    # nrRecibo / nrRecArqBase identifica a versão; retificações têm recibo maior
    nr_rec = _first(root, "nrRecibo") or _first(root, "nrRecArqBase") or ""
    ind_retif = _first(root, "indRetif") or "1"
    return {
        "cpf": _first(root, "cpfTrab"),
        "matricula": _first(root, "matricula") or "",
        "dt_deslig": dt,
        "cod_motivo": cod,
        "motivo": MOTIVO_DESLIG.get(cod, f"Motivo {cod}"),
        "onus": onus, "onus_desc": onus_desc,
        "pensao_alim": _first(root, "pensAlim") or "",
        "aviso_indenizado": _first(root, "indPagtoAPI") or "",
        "total_verbas_resc": round(total_verbas, 2),
        "nr_recibo": nr_rec, "ind_retif": ind_retif,
    }

def parse_s1010(root, fname):
    """Tabela de rubricas (nome, natureza, tipo)."""
    cod = _first(root, "codRubr")
    if not cod:
        return None
    return {
        "cod_rubr": cod,
        "desc": _first(root, "dscRubr") or "",
        "natureza": _first(root, "natRubr") or "",
        "tipo": _first(root, "tpRubr") or "",   # 1=provento 2=desconto 3=informativa 4=inf.dedutora
    }

def parse_s1200(root, fname):
    """Remuneração — rubricas por trabalhador."""
    cpf = _first(root, "cpfTrab")
    per = _first(root, "perApur")
    if not cpf:
        return None
    rubricas = []
    mat = _first(root, "matricula") or ""
    for el in root.iter():
        if _tag(el) == "itensRemun":
            cod = qtd = val = None
            for ch in el:
                t = _tag(ch)
                if t == "codRubr": cod = (ch.text or "").strip()
                elif t == "qtdRubr": qtd = _float(ch.text)
                elif t == "vrRubr": val = _float(ch.text)
            if cod:
                rubricas.append({"cod_rubr": cod, "qtd": qtd or 0, "valor": val or 0})
    return {"cpf": cpf, "matricula": mat, "per_apur": per, "rubricas": rubricas}

def parse_s1210(root, fname):
    """Pagamentos — desmembra o líquido por COMPETÊNCIA DE REFERÊNCIA (perRef).

    Um único S-1210 (enviado num mês) pode conter pagamentos referentes a várias
    competências (folha do mês, 13º do ano, férias/rescisões retroativas). Por isso
    agregamos por perRef — a competência real a que o pagamento se refere — e NÃO
    pelo perApur do evento. Devolve uma lista de registros (um por competência).
    """
    cpf = _first(root, "cpfBenef") or _first(root, "cpfTrab")
    if not cpf:
        return None
    per_evt = _first(root, "perApur")
    dt_pgto = _first(root, "dtPgto")
    # competência de referência -> componentes
    refs = {}
    for ip in root.iter():
        if _tag(ip) == "infoPgto":
            tp = perref = None
            vl = 0.0
            for ch in ip:
                t = _tag(ch); x = (ch.text or "").strip()
                if t == "tpPgto": tp = x
                elif t == "perRef": perref = x
                elif t == "vrLiq": vl = _float(x)
            # normaliza a competência de referência
            is13 = bool(perref and len(perref) == 4)   # AAAA = 13º salário
            if is13:
                comp = f"{perref}-12"                   # atribui o 13º a dezembro
            elif perref and len(perref) == 7:
                comp = perref                           # AAAA-MM
            else:
                comp = per_evt                          # fallback
            d = refs.setdefault(comp, {"folha": 0.0, "resc": 0.0, "d13": 0.0, "total": 0.0})
            if tp == "2":
                d["resc"] += vl
            elif is13:
                d["d13"] += vl
            else:
                d["folha"] += vl
            d["total"] += vl
    if not refs:
        return None
    # devolve um registro por competência de referência (a chave _multi expande no loader)
    linhas = []
    for comp, d in refs.items():
        linhas.append({
            "cpf": cpf, "per_apur": comp, "dt_pgto": dt_pgto,
            "vr_liquido": round(d["total"], 2),
            "liq_folha": round(d["folha"], 2),
            "liq_rescisao": round(d["resc"], 2),
            "liq_13": round(d["d13"], 2),
        })
    return {"_multi": linhas}

def parse_s5001(root, fname):
    """Bases INSS (totalizador oficial)."""
    NS = "http://www.esocial.gov.br/schema/evt/evtBasesTrab/v_S_01_03_00"
    evt = root.find(f".//{{{NS}}}evtBasesTrab")
    if evt is None:
        return None
    def f(el, tag):
        r = el.find(f"{{{NS}}}{tag}")
        return r.text if r is not None else None
    ide_evt = evt.find(f"{{{NS}}}ideEvento")
    ide_trab = evt.find(f"{{{NS}}}ideTrabalhador")
    cp = evt.find(f"{{{NS}}}infoCpCalc")
    info_cp = evt.find(f"{{{NS}}}infoCp")

    per = f(ide_evt, "perApur") if ide_evt is not None else None
    cpf = f(ide_trab, "cpfTrab") if ide_trab is not None else None
    # vrCpSeg = contribuição do SEGURADO (empregado) calculada — NÃO é a patronal
    vr_cp_seg = _float(f(cp, "vrCpSeg")) if cp is not None else 0.0

    mat = ""
    bases = {}
    if info_cp is not None:
        for lot in info_cp.findall(f"{{{NS}}}ideEstabLot"):
            for cat in lot.findall(f"{{{NS}}}infoCategIncid"):
                if not mat:
                    mat = f(cat, "matricula") or ""
                for b in cat.findall(f"{{{NS}}}infoBaseCS"):
                    ind13 = f(b, "ind13") or "0"
                    tp = f(b, "tpValor") or "?"
                    val = _float(f(b, "valor"))
                    bases[f"tp{tp}_i{ind13}"] = bases.get(f"tp{tp}_i{ind13}", 0.0) + val
    if not cpf and not per:
        return None
    nr_rec = f(ide_evt, "nrRecArqBase") if ide_evt is not None else None
    return {"cpf": cpf, "matricula": mat, "per_apur": per,
            "inss_seg_calc": vr_cp_seg, "nr_recibo": nr_rec or "", **bases}


# Terceiros (Outras Entidades) — alíquota total por código FPAS mais comum.
# Pode ser ajustada no app. codTercs '0000' = sem terceiros.
TERCEIROS_PCT = {"0000": 0.0}  # default; comércio (FPAS 515) costuma ser 5.8

def parse_s5011(root, fname):
    """Totalizador da contribuição social do empregador (evtCS).

    Usa exclusivamente o que o eSocial APUROU (sem inferir regime):
      vr_cr      = soma de infoCRContrib/vrCR  -> INSS previdenciário total devido
      vr_seg     = soma de vrCpSeg             -> parte do segurado (empregado)
      (vr_cr - vr_seg) = parte patronal efetiva (0 p/ Simples; real p/ reg. normal)
    Também traz base patronal, salário-família e salário-maternidade.
    """
    per = _first(root, "perApur")
    if not per:
        return None
    base_cp = sum(_float(v) for v in _all(root, "vrBcCp00"))
    sal_fam = sum(_float(v) for v in _all(root, "vrSalFam"))
    sal_mat = sum(_float(v) for v in _all(root, "vrSalMat"))
    vr_seg = sum(_float(v) for v in _all(root, "vrCpSeg"))
    # vrCR apenas dentro de infoCRContrib (contribuição apurada para a guia)
    vr_cr = 0.0
    cr_detalhe = {}
    for el in root.iter():
        if _tag(el) == "infoCRContrib":
            tp = None; vr = 0.0
            for ch in el:
                t = _tag(ch)
                if t == "tpCR": tp = (ch.text or "").strip()
                elif t == "vrCR": vr = _float(ch.text)
            vr_cr += vr
            if tp:
                cr_detalhe[tp] = cr_detalhe.get(tp, 0.0) + vr
    rat = _float(_first(root, "aliqRatAjust")) or _float(_first(root, "aliqRat"))
    fpas = _first(root, "fpas") or ""
    return {"per_apur": per, "base_cp": round(base_cp, 2),
            "sal_familia": round(sal_fam, 2), "sal_maternidade": round(sal_mat, 2),
            "vr_seg": round(vr_seg, 2),
            "inss_apurado": round(vr_cr, 2),
            "inss_patronal": round(max(0.0, vr_cr - vr_seg), 2),
            "nr_recibo": _first(root, "nrRecArqBase") or _first(root, "nrRecibo") or "",
            "rat": rat, "fpas": fpas}

def parse_s5002(root, fname):
    """IRRF (totalizador oficial)."""
    cpf = _first(root, "cpfBenef") or _first(root, "cpfTrab")
    per = _first(root, "perApur")
    if not cpf:
        return None
    # consolidado mensal
    rend_trib = rend_trib13 = prev_of = irrf = irrf13 = 0.0
    dependentes = []
    for el in root.iter():
        if _tag(el) == "consolidApurMen":
            for ch in el:
                t = _tag(ch)
                if t == "vlrRendTrib": rend_trib += _float(ch.text)
                elif t == "vlrRendTrib13": rend_trib13 += _float(ch.text)
                elif t == "vlrPrevOficial": prev_of += _float(ch.text)
                elif t == "vlrCRMen": irrf += _float(ch.text)
                elif t == "vlrCR13Men": irrf13 += _float(ch.text)
    # dependentes (ideDep)
    for el in root.iter():
        if _tag(el) == "ideDep":
            dep = {}
            for ch in el:
                t = _tag(ch)
                if t == "nome": dep["nome"] = (ch.text or "").strip()
                elif t == "dtNascto": dep["dt_nasc"] = (ch.text or "").strip()
                elif t == "tpDep": dep["tipo"] = (ch.text or "").strip()
                elif t == "depIRRF": dep["dep_irrf"] = (ch.text or "").strip()
            if dep:
                dependentes.append(dep)
    # dependentes para IRRF = apenas os com depIRRF=S (abatem o imposto).
    # Os demais são dependentes para salário-família/plano de saúde.
    n_dep_irrf = sum(1 for d in dependentes if d.get("dep_irrf") == "S")
    return {"cpf": cpf, "per_apur": per,
            "nr_recibo": _first(root, "nrRecArqBase") or "",
            "rend_tributavel": round(rend_trib, 2),
            "rend_tributavel13": round(rend_trib13, 2),
            "prev_oficial": round(prev_of, 2),
            "irrf": round(irrf, 2),
            "irrf_13": round(irrf13, 2),
            "n_dependentes": n_dep_irrf,
            "dependentes": dependentes}

def parse_s5003(root, fname):
    """Bases FGTS (totalizador oficial) — remuneração e depósito reais."""
    cpf = _first(root, "cpfTrab")
    per = _first(root, "perApur")
    if not cpf:
        return None
    rem_fgts = sum(_float(v) for v in _all(root, "remFGTS"))
    dps_fgts = sum(_float(v) for v in _all(root, "dpsFGTS"))
    consig = sum(_float(v) for v in _all(root, "vreConsignado"))
    # separa FGTS mensal (tpValor 11) de 13º/outros (12,21,22,...)
    fgts_mensal = fgts_13 = 0.0
    rem_mensal = rem_13 = 0.0
    for b in root.iter():
        if _tag(b) in ("basePerApur", "base13", "basePerAntE", "baseQuarentena"):
            tp = None; rem = dps = 0.0
            for ch in b:
                t = _tag(ch); x = (ch.text or "").strip()
                if t == "tpValor": tp = x
                elif t == "remFGTS": rem = _float(x)
                elif t == "dpsFGTS": dps = _float(x)
            # tpValor FGTS: 11=remun mensal, 12=13º, 21=remun retroativa, 22=13º retroativo
            if tp in ("12", "22"):         # 13º salário
                fgts_13 += dps; rem_13 += rem
            else:                          # mensal e retroativos
                fgts_mensal += dps; rem_mensal += rem
    return {"cpf": cpf, "matricula": _first(root, "matricula") or "",
            "per_apur": per,
            "nr_recibo": _first(root, "nrRecArqBase") or "",
            "base_fgts": round(rem_fgts, 2),
            "deposito_fgts": round(dps_fgts, 2),
            "fgts_mensal": round(fgts_mensal, 2),
            "fgts_13": round(fgts_13, 2),
            "consignado": round(consig, 2)}


PARSERS = {
    "S-2190": parse_s2200, "S-2200": parse_s2200, "S-2206": parse_s2206,
    "S-2220": parse_s2220, "S-2230": parse_s2230, "S-2240": parse_s2240,
    "S-2299": parse_s2299, "S-3000": parse_s3000,
    "S-1010": parse_s1010, "S-1200": parse_s1200, "S-1210": parse_s1210,
    "S-5001": parse_s5001, "S-5002": parse_s5002, "S-5003": parse_s5003,
    "S-5011": parse_s5011,
}
BUCKET = {
    "S-2190": "admissoes", "S-2200": "admissoes", "S-2206": "alteracoes",
    "S-2220": "exames", "S-2230": "afastamentos", "S-2240": "exp_risco",
    "S-2299": "desligamentos", "S-3000": "exclusoes",
    "S-1010": "rubricas", "S-1200": "remuneracao", "S-1210": "pagamentos",
    "S-5001": "bases_inss", "S-5002": "bases_irrf", "S-5003": "bases_fgts",
    "S-5011": "cs_patronal",
}


def carregar(uploaded_files):
    """Recebe arquivos (Streamlit UploadedFile ou caminhos) e devolve dict de DataFrames."""
    buckets = {v: [] for v in set(BUCKET.values())}
    total_xml = 0
    erros = []
    nomes = {}   # cpf -> nome do trabalhador (coletado de QUALQUER evento que tenha)
    cnpj_emp = {"v": None}   # CNPJ do empregador (ideEmpregador/nrInsc)

    def _proc_xml(content, fname):
        nonlocal total_xml
        if not content:
            return
        try:
            root = ET.fromstring(content)
        except ET.ParseError:
            return
        total_xml += 1
        # coleta nome do trabalhador de qualquer evento que o traga (S-2200, S-2205, etc.)
        _cpf = _first(root, "cpfTrab") or _first(root, "cpfBenef")
        _nm = _first(root, "nmTrab")
        if _cpf and _nm and _cpf not in nomes:
            nomes[_cpf] = _nm
        # CNPJ do empregador (primeiro ideEmpregador/nrInsc encontrado)
        if cnpj_emp["v"] is None:
            for el in root.iter():
                if _tag(el) == "ideEmpregador":
                    for ch in el:
                        if _tag(ch) == "nrInsc" and (ch.text or "").strip():
                            cnpj_emp["v"] = re.sub(r"\D", "", ch.text)
                    break
        tp = tipo_evento(fname)
        parser = PARSERS.get(tp)
        if not parser:
            return
        try:
            r = parser(root, fname)
        except Exception as e:                       # noqa: BLE001
            erros.append(f"{fname}: {e}")
            return
        if r:
            # alguns parsers (S-1210) devolvem múltiplas linhas via "_multi"
            if isinstance(r, dict) and "_multi" in r:
                buckets[BUCKET[tp]].extend(r["_multi"])
            else:
                buckets[BUCKET[tp]].append(r)

    for uf in uploaded_files:
        # caminho str ou objeto com .name/.read
        if isinstance(uf, str):
            name = uf
            opener = lambda p=uf: open(p, "rb")
            raw = None
        else:
            name = uf.name
            raw = uf.read()

        low = name.lower()
        if low.endswith(".zip"):
            data = raw if raw is not None else open(name, "rb").read()
            try:
                with zipfile.ZipFile(io.BytesIO(data)) as zf:
                    for member in zf.namelist():
                        if member.lower().endswith(".xml"):
                            _proc_xml(zf.read(member), member)
            except zipfile.BadZipFile:
                erros.append(f"ZIP inválido: {name}")
        elif low.endswith(".xml"):
            data = raw if raw is not None else open(name, "rb").read()
            _proc_xml(data, name)

    # monta DataFrames (remuneracao tem lista de rubricas -> normaliza depois)
    dfs = {}
    for k, rows in buckets.items():
        dfs[k] = pd.DataFrame(rows) if rows else pd.DataFrame()

    # ── EXCLUSÕES (S-3000): remove eventos cancelados ───────────────────────
    # O S-3000 cancela um evento enviado por engano. Removemos dos buckets os
    # registros cujo recibo (nr_recibo) está na lista de excluídos.
    exc = dfs.get("exclusoes")
    recibos_excluidos = set()
    if exc is not None and not exc.empty and "nr_rec_excluido" in exc.columns:
        recibos_excluidos = set(exc["nr_rec_excluido"].dropna().astype(str))
    if recibos_excluidos:
        for bk in ("admissoes", "alteracoes", "afastamentos", "desligamentos", "exames"):
            df = dfs.get(bk)
            if df is not None and not df.empty and "nr_recibo" in df.columns:
                dfs[bk] = df[~df["nr_recibo"].astype(str).isin(recibos_excluidos)].reset_index(drop=True)

    # ── DEDUPLICAÇÃO ────────────────────────────────────────────────────────
    # Admissões: S-2190 (preliminar, sem nome) + S-2200 (completo) p/ mesmo CPF.
    # Mantém 1 por CPF, preferindo o registro mais completo (com nome).
    adm = dfs["admissoes"]
    if not adm.empty and "cpf" in adm.columns:
        adm = adm.copy()
        adm["_score"] = (adm["nome"].fillna("").str.len() > 0).astype(int) * 2 \
                        + (adm["cargo"].fillna("").str.len() > 0).astype(int)
        # mantém maior score por CPF; em empate, o último (S-2200 costuma vir depois)
        adm = (adm.sort_values("_score")
                  .drop_duplicates("cpf", keep="last")
                  .drop(columns="_score")
                  .reset_index(drop=True))
        dfs["admissoes"] = adm

    # Desligamentos: retificações (indRetif=2) geram vários eventos do mesmo
    # desligamento. Mantém o de maior nrRecibo por (CPF, data) = versão final.
    des = dfs["desligamentos"]
    if not des.empty and "cpf" in des.columns:
        des = des.copy()
        des["_rec"] = des["nr_recibo"].fillna("").astype(str)
        des = (des.sort_values("_rec")
                  .drop_duplicates(["cpf", "dt_deslig"], keep="last")
                  .drop(columns="_rec")
                  .reset_index(drop=True))
        dfs["desligamentos"] = des

    # Totalizadores — deduplicação por tipo de evento:
    #  • S-5001 (INSS) e S-5002 (IRRF): eventos repetidos por (CPF, competência)
    #    são RETIFICAÇÕES — mantém só o de MAIOR recibo (versão final).
    #  • S-5003 (FGTS): o mesmo CPF/competência pode ter eventos COMPLEMENTARES
    #    (folha normal + GRRF de rescisão), com recibos distintos — não se pode
    #    descartar por CPF. Deduplica só CÓPIAS exatas (mesmo recibo).
    for bucket in ("bases_inss", "bases_irrf"):
        df = dfs.get(bucket)
        if df is not None and not df.empty and "cpf" in df.columns and "nr_recibo" in df.columns:
            df = df.copy()
            df["_rec"] = df["nr_recibo"].fillna("").astype(str)
            df = (df.sort_values("_rec")
                    .drop_duplicates(["cpf", "per_apur"], keep="last")
                    .drop(columns="_rec").reset_index(drop=True))
            dfs[bucket] = df
    dff = dfs.get("bases_fgts")
    if dff is not None and not dff.empty and "nr_recibo" in dff.columns:
        dff = dff.copy()
        # remove apenas cópias literais do mesmo evento (mesmo recibo)
        dff = dff[dff["nr_recibo"].astype(str) != ""]
        dedup = dff.drop_duplicates(["nr_recibo"], keep="first")
        # registros sem recibo: mantém todos (não dá p/ identificar cópia)
        sem_rec = dfs["bases_fgts"]
        sem_rec = sem_rec[sem_rec["nr_recibo"].astype(str) == ""] if "nr_recibo" in sem_rec.columns else sem_rec.iloc[0:0]
        dfs["bases_fgts"] = pd.concat([dedup, sem_rec], ignore_index=True)

    # S-5011 (contribuição patronal/INSS consolidado): a mesma competência pode
    # ser retransmitida/retificada em vários pacotes (recibos diferentes). É UM
    # totalizador por competência — mantém só a versão de MAIOR recibo (a final).
    # Sem isso, INSS patronal/apurado seria somado repetido (2×, 3×...).
    dcs = dfs.get("cs_patronal")
    if dcs is not None and not dcs.empty and "nr_recibo" in dcs.columns:
        dcs = dcs.copy()
        dcs["_rec"] = dcs["nr_recibo"].fillna("").astype(str)
        dcs = (dcs.sort_values("_rec")
                  .drop_duplicates(["per_apur"], keep="last")
                  .drop(columns="_rec").reset_index(drop=True))
        dfs["cs_patronal"] = dcs

    dfs["_total_xml"] = total_xml
    dfs["_erros"] = erros
    dfs["_nomes"] = nomes   # cpf -> nome (de todos os eventos com nmTrab)
    dfs["_cnpj"] = cnpj_emp["v"]   # CNPJ do empregador (raiz ou completo)
    return dfs


# ─────────────────────────────────────────────────────────────────────────────
# INSS PREVIDENCIÁRIO — exclusivamente do que o eSocial apurou (S-5011)
# ─────────────────────────────────────────────────────────────────────────────
def inss_por_periodo(cs_df):
    """Devolve, por período, os valores de INSS REALMENTE apurados no eSocial.

    Sem inferência de regime tributário nem alíquotas arbitradas:
      apurado  = INSS previdenciário total devido (infoCRContrib/vrCR)
      segurado = parte do empregado (vrCpSeg)
      patronal = apurado − segurado  (0 para Simples; valor real p/ regime normal)
    Retorna {periodo: {apurado, segurado, patronal, base}}.
    """
    out = {}
    if cs_df is None or cs_df.empty:
        return out
    g = cs_df.groupby("per_apur").agg(
        apurado=("inss_apurado", "sum"),
        segurado=("vr_seg", "sum"),
        patronal=("inss_patronal", "sum"),
        base=("base_cp", "sum"),
    ).reset_index()
    for _, r in g.iterrows():
        out[r["per_apur"]] = {"apurado": round(r["apurado"], 2),
                              "segurado": round(r["segurado"], 2),
                              "patronal": round(r["patronal"], 2),
                              "base": round(r["base"], 2)}
    return out


# ─────────────────────────────────────────────────────────────────────────────
# CÁLCULO DE FÉRIAS
# ─────────────────────────────────────────────────────────────────────────────
def status_ferias(dt_adm_str, hoje=None):
    """Status do direito de férias a partir da data de admissão."""
    dt_adm = _parse_date(dt_adm_str)
    if not dt_adm:
        return None
    hoje = hoje or date.today()
    meses = (hoje.year - dt_adm.year) * 12 + (hoje.month - dt_adm.month)
    if hoje.day < dt_adm.day:
        meses -= 1
    periodos_completos = meses // 12

    def add_anos(d, n):
        if HAS_DATEUTIL:
            return d + relativedelta(years=n)
        try:
            return d.replace(year=d.year + n)
        except ValueError:
            return d.replace(year=d.year + n, day=28)

    if periodos_completos == 0:
        venc = add_anos(dt_adm, 1)
        return {"status": "Adquirindo", "periodos_vencidos": 0,
                "vencimento": venc, "dias_para_vencer": (venc - hoje).days,
                "meses_casa": meses}

    fim_aq = add_anos(dt_adm, periodos_completos)
    fim_concessivo = add_anos(fim_aq, 1)      # 12 meses para conceder
    dias = (fim_concessivo - hoje).days
    if dias < 0:
        st = "Vencida"
    elif dias <= 30:
        st = "Crítico"
    elif dias <= 90:
        st = "Atenção"
    else:
        st = "Em dia"
    return {"status": st, "periodos_vencidos": periodos_completos,
            "vencimento": fim_concessivo, "dias_para_vencer": dias,
            "meses_casa": meses}


def idade(dt_nasc_str, hoje=None):
    d = _parse_date(dt_nasc_str)
    if not d:
        return None
    hoje = hoje or date.today()
    return hoje.year - d.year - ((hoje.month, hoje.day) < (d.month, d.day))
