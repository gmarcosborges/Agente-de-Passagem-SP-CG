"""Monta o briefing diario.

A regra do projeto: a saida e curta. Se o briefing precisar de scroll,
a triagem esta ruim - conserta a regra, nao aumenta a mensagem.
"""
from datetime import datetime

from life.config import BRT

LIMITE_POR_BALDE = 5


def _hora(ts):
    try:
        dt = datetime.fromisoformat(ts)
    except ValueError:
        return ""
    if dt.tzinfo:
        dt = dt.astimezone(BRT)
    return dt.strftime("%H:%M")


def _dia(ts):
    try:
        dt = datetime.fromisoformat(ts)
    except ValueError:
        return ""
    if dt.tzinfo:
        dt = dt.astimezone(BRT)
    hoje = datetime.now(BRT).date()
    if dt.date() == hoje:
        return "hoje"
    if (dt.date() - hoje).days == 1:
        return "amanha"
    return dt.strftime("%d/%m")


def _brl(valor):
    """1240.5 -> 'R$ 1.240,50' (formato brasileiro, sem locale)."""
    inteiro, centavos = f"{valor:,.2f}".split(".")
    return f"R$ {inteiro.replace(',', '.')},{centavos}"


def _quem(evento):
    who = evento.get("who") or ""
    if "<" in who:
        nome = who.split("<")[0].strip().strip('"')
        return nome or who
    return who.split("@")[0] if "@" in who else who


def montar(eventos):
    baldes = {"acao": [], "dinheiro": [], "compromisso": [], "info": [], "ruido": []}
    for ev in eventos:
        baldes.setdefault(ev.get("kind", "info"), []).append(ev)

    for k in ("compromisso",):
        baldes[k].sort(key=lambda e: e["ts"])

    agora = datetime.now(BRT)
    linhas = [f"*Life Inbox* - {agora.strftime('%a %d/%m %H:%M')}", ""]

    compromissos = baldes["compromisso"]
    if compromissos:
        linhas.append(f"*Agenda* ({len(compromissos)})")
        for ev in compromissos[:LIMITE_POR_BALDE]:
            dia_inteiro = ev.get("raw", {}).get("dia_inteiro")
            quando = _dia(ev["ts"]) if dia_inteiro else f"{_dia(ev['ts'])} {_hora(ev['ts'])}"
            linhas.append(f"  {quando} - {ev['title']}")
        if len(compromissos) > LIMITE_POR_BALDE:
            linhas.append(f"  +{len(compromissos) - LIMITE_POR_BALDE} outros")
        linhas.append("")

    acoes = baldes["acao"]
    if acoes:
        linhas.append(f"*Pedem acao* ({len(acoes)})")
        for ev in acoes[:LIMITE_POR_BALDE]:
            linhas.append(f"  {_quem(ev)}: {ev['title']}")
        if len(acoes) > LIMITE_POR_BALDE:
            linhas.append(f"  +{len(acoes) - LIMITE_POR_BALDE} outros")
        linhas.append("")

    dinheiro = baldes["dinheiro"]
    if dinheiro:
        total = sum(e["amount_brl"] for e in dinheiro if e.get("amount_brl"))
        cabecalho = f"*Dinheiro* ({len(dinheiro)})"
        if total:
            cabecalho += f" - {_brl(total)} identificados"
        linhas.append(cabecalho)
        for ev in dinheiro[:LIMITE_POR_BALDE]:
            # Nao repete o valor se ele ja aparece no proprio assunto.
            valor = ""
            if ev.get("amount_brl") and "R$" not in ev["title"]:
                valor = f" - {_brl(ev['amount_brl'])}"
            linhas.append(f"  {_quem(ev)}: {ev['title']}{valor}")
        if len(dinheiro) > LIMITE_POR_BALDE:
            linhas.append(f"  +{len(dinheiro) - LIMITE_POR_BALDE} outros")
        linhas.append("")

    rodape = f"_{len(baldes['info'])} informativos, {len(baldes['ruido'])} descartados_"
    if len(linhas) == 2:
        linhas.append("Nada exige voce agora.")
        linhas.append("")
    linhas.append(rodape)

    return "\n".join(linhas)
