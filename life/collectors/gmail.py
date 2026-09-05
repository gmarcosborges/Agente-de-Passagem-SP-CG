"""Coletor de email (Gmail, somente leitura).

Pega so os metadados (remetente, assunto, data, labels) das ultimas N horas.
Nao baixa corpo de email: e mais rapido, mais barato e menos invasivo -
metadado ja basta pra triagem, e o corpo so viria se o v1 precisar.
"""
import base64  # noqa: F401  (reservado para quando o v1 ler corpo)
from datetime import datetime, timedelta
from email.utils import parsedate_to_datetime

from life.brain.rules import classificar_email, extrair_valor
from life.config import BRT, EMAIL_LOOKBACK_HOURS, EMAIL_MAX_RESULTS
from life.google_auth import service

HEADERS = ["From", "Subject", "Date", "List-Unsubscribe"]


def _header(msg, nome):
    for h in msg.get("payload", {}).get("headers", []):
        if h.get("name", "").lower() == nome.lower():
            return h.get("value", "")
    return ""


def coletar(horas=None):
    horas = horas or EMAIL_LOOKBACK_HOURS
    gmail = service("gmail", "v1")
    corte = datetime.now(BRT) - timedelta(hours=horas)

    query = f"after:{int(corte.timestamp())} -in:chats -in:spam -in:trash"
    resp = gmail.users().messages().list(
        userId="me", q=query, maxResults=EMAIL_MAX_RESULTS
    ).execute()
    ids = [m["id"] for m in resp.get("messages", [])]

    eventos = []
    for mid in ids:
        msg = gmail.users().messages().get(
            userId="me", id=mid, format="metadata", metadataHeaders=HEADERS
        ).execute()

        assunto = _header(msg, "Subject") or "(sem assunto)"
        remetente = _header(msg, "From")
        labels = msg.get("labelIds", [])
        unsub = bool(_header(msg, "List-Unsubscribe"))

        try:
            ts = parsedate_to_datetime(_header(msg, "Date")).astimezone(BRT)
        except (TypeError, ValueError):
            ts = datetime.fromtimestamp(int(msg["internalDate"]) / 1000, BRT)

        kind = classificar_email(assunto, remetente, labels, unsub)
        eventos.append({
            "source": "gmail",
            "external_id": mid,
            "ts": ts.isoformat(timespec="seconds"),
            "kind": kind,
            "title": assunto,
            "who": remetente,
            "amount_brl": extrair_valor(assunto) if kind == "dinheiro" else None,
            "link": f"https://mail.google.com/mail/u/0/#inbox/{mid}",
            "raw": {"labels": labels, "snippet": msg.get("snippet", "")},
        })

    return eventos
