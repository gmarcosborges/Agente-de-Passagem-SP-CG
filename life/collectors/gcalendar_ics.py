"""Coletor de agenda pela URL secreta em formato iCal.

O Google Calendar publica um endereco privado .ics por calendario
(Configuracoes do calendario -> "Endereco secreto em formato iCal").
E so buscar por HTTP: nao tem OAuth, nao tem token pra expirar, funciona
num cron na nuvem pra sempre.

A URL e a credencial - quem tem ela le a sua agenda. Fica em secret,
nunca no codigo.
"""
import os
from datetime import date, datetime, timedelta

import recurring_ical_events
import requests
from icalendar import Calendar

from life.config import BRT, CALENDAR_LOOKAHEAD_HOURS


def configurado():
    return bool(os.environ.get("CALENDAR_ICS_URL"))


def _para_datetime(valor):
    """DTSTART vem como date (dia inteiro) ou datetime (hora marcada)."""
    if isinstance(valor, datetime):
        return valor if valor.tzinfo else valor.replace(tzinfo=BRT), False
    if isinstance(valor, date):
        return datetime(valor.year, valor.month, valor.day, tzinfo=BRT), True
    return None, False


def coletar(horas=None):
    horas = horas or CALENDAR_LOOKAHEAD_HOURS
    urls = [u.strip() for u in os.environ["CALENDAR_ICS_URL"].split(",") if u.strip()]

    agora = datetime.now(BRT)
    limite = agora + timedelta(hours=horas)
    eventos = []

    for indice, url in enumerate(urls):
        r = requests.get(url, timeout=30)
        r.raise_for_status()
        calendario = Calendar.from_ical(r.text)

        # Expande recorrencias: reuniao semanal vira uma ocorrencia por vez.
        for ev in recurring_ical_events.of(calendario).between(agora, limite):
            inicio, dia_inteiro = _para_datetime(ev.get("DTSTART").dt)
            if inicio is None:
                continue

            uid = str(ev.get("UID", f"sem-uid-{indice}"))
            eventos.append({
                "source": "gcalendar",
                "external_id": f"{uid}@{inicio.isoformat()}",
                "ts": inicio.isoformat(timespec="seconds"),
                "kind": "compromisso",
                "title": str(ev.get("SUMMARY", "(sem titulo)")),
                "who": str(ev.get("ORGANIZER", "")) or None,
                "amount_brl": None,
                "link": str(ev.get("URL", "")) or None,
                "raw": {
                    "local": str(ev.get("LOCATION", "")) or None,
                    "dia_inteiro": dia_inteiro,
                },
            })

    eventos.sort(key=lambda e: e["ts"])
    return eventos
