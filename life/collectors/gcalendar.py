"""Coletor de agenda (Google Calendar, somente leitura).

Sem agenda o agente nao sabe o que e urgente: um email de cobranca e uma
coisa quando voce esta livre e outra quando voce tem reuniao o dia todo.
"""
from datetime import datetime, timedelta

from life.config import BRT, CALENDAR_LOOKAHEAD_HOURS
from life.google_auth import service


def coletar(horas=None):
    horas = horas or CALENDAR_LOOKAHEAD_HOURS
    cal = service("calendar", "v3")

    agora = datetime.now(BRT)
    limite = agora + timedelta(hours=horas)

    resp = cal.events().list(
        calendarId="primary",
        timeMin=agora.isoformat(),
        timeMax=limite.isoformat(),
        singleEvents=True,
        orderBy="startTime",
        maxResults=50,
    ).execute()

    eventos = []
    for ev in resp.get("items", []):
        if ev.get("status") == "cancelled":
            continue
        inicio = ev.get("start", {})
        quando = inicio.get("dateTime") or inicio.get("date")
        if not quando:
            continue
        dia_inteiro = "dateTime" not in inicio

        organizador = ev.get("organizer", {}).get("email")
        convidados = [a.get("email") for a in ev.get("attendees", []) if a.get("email")]

        eventos.append({
            "source": "gcalendar",
            # id + inicio: evento recorrente vira uma ocorrencia por vez.
            "external_id": f"{ev['id']}@{quando}",
            "ts": quando,
            "kind": "compromisso",
            "title": ev.get("summary", "(sem titulo)"),
            "who": organizador,
            "amount_brl": None,
            "link": ev.get("htmlLink"),
            "raw": {
                "local": ev.get("location"),
                "dia_inteiro": dia_inteiro,
                "convidados": convidados[:10],
            },
        })

    return eventos
