"""Coletor de email por IMAP + senha de app.

Por que existe, se ja temos o coletor OAuth: um job que roda na nuvem
precisa de credencial que nao expira. Token OAuth de app em modo
"Testing" no Google morre a cada 7 dias - o briefing quebraria toda
semana. Senha de app nao expira.

Preco disso: a senha de app da acesso total ao IMAP (le e apaga), nao
so leitura. Por isso o coletor abre a caixa em modo readonly e usa
BODY.PEEK, que nao marca nada como lido. Nada aqui escreve.
"""
import email
import imaplib
import os
import re
from datetime import datetime, timedelta
from email.header import decode_header, make_header
from email.utils import parsedate_to_datetime

from life.brain.rules import classificar_email, extrair_valor
from life.config import BRT, EMAIL_LOOKBACK_HOURS, EMAIL_MAX_RESULTS

IMAP_HOST = os.environ.get("IMAP_HOST", "imap.gmail.com")
CABECALHOS = "FROM SUBJECT DATE LIST-UNSUBSCRIBE"
LOTE = 50

RE_MSGID = re.compile(rb"X-GM-MSGID (\d+)")
RE_LABELS = re.compile(rb"X-GM-LABELS \(([^)]*)\)")
RE_FLAGS = re.compile(rb"FLAGS \(([^)]*)\)")


def configurado():
    return bool(os.environ.get("IMAP_USER") and os.environ.get("IMAP_PASSWORD"))


def _decodificar(valor):
    if not valor:
        return ""
    try:
        return str(make_header(decode_header(valor)))
    except Exception:
        return valor


def _labels(prefixo):
    """Traduz labels do Gmail-IMAP pro vocabulario que rules.py entende."""
    bruto = (RE_LABELS.search(prefixo).group(1).decode("utf-8", "replace").lower()
             if RE_LABELS.search(prefixo) else "")
    flags = (RE_FLAGS.search(prefixo).group(1).decode("utf-8", "replace").lower()
             if RE_FLAGS.search(prefixo) else "")

    labels = []
    if "promo" in bruto:
        labels.append("CATEGORY_PROMOTIONS")
    if "social" in bruto:
        labels.append("CATEGORY_SOCIAL")
    if "forum" in bruto or "group" in bruto:
        labels.append("CATEGORY_FORUMS")
    if "updates" in bruto or "notification" in bruto:
        labels.append("CATEGORY_UPDATES")
    if "important" in bruto:
        labels.append("IMPORTANT")
    if "inbox" in bruto:
        labels.append("INBOX")
    if "\\seen" not in flags:
        labels.append("UNREAD")
    # Sem categoria nenhuma, o Gmail trata como pessoal.
    if not any(lb.startswith("CATEGORY_") for lb in labels):
        labels.append("CATEGORY_PERSONAL")
    return labels


def _conectar():
    imap = imaplib.IMAP4_SSL(IMAP_HOST, timeout=45)
    imap.login(os.environ["IMAP_USER"], os.environ["IMAP_PASSWORD"].replace(" ", ""))
    # readonly=True: a sessao inteira e incapaz de alterar a caixa.
    imap.select("INBOX", readonly=True)
    return imap


def _msg_id(prefixo, fallback):
    achado = RE_MSGID.search(prefixo)
    return achado.group(1).decode() if achado else fallback


def coletar(horas=None):
    horas = horas or EMAIL_LOOKBACK_HOURS
    corte = datetime.now(BRT) - timedelta(hours=horas)

    imap = _conectar()
    try:
        # SINCE tem granularidade de dia; o corte fino em horas e feito abaixo.
        desde = (corte - timedelta(days=1)).strftime("%d-%b-%Y")
        typ, dados = imap.search(None, "SINCE", desde)
        if typ != "OK":
            raise RuntimeError(f"busca IMAP falhou: {typ}")

        nums = dados[0].split()[-EMAIL_MAX_RESULTS:]
        eventos = []

        for i in range(0, len(nums), LOTE):
            faixa = b",".join(nums[i:i + LOTE]).decode()
            typ, resposta = imap.fetch(
                faixa,
                f"(X-GM-MSGID X-GM-LABELS FLAGS BODY.PEEK[HEADER.FIELDS ({CABECALHOS})])",
            )
            if typ != "OK":
                continue

            for item in resposta:
                if not isinstance(item, tuple):
                    continue
                prefixo, cabecalhos = item[0], item[1]
                msg = email.message_from_bytes(cabecalhos)

                try:
                    ts = parsedate_to_datetime(msg.get("Date")).astimezone(BRT)
                except (TypeError, ValueError):
                    continue
                if ts < corte:
                    continue

                assunto = _decodificar(msg.get("Subject")) or "(sem assunto)"
                remetente = _decodificar(msg.get("From"))
                labels = _labels(prefixo)
                unsub = bool(msg.get("List-Unsubscribe"))

                kind = classificar_email(assunto, remetente, labels, unsub)
                gm_id = _msg_id(prefixo, f"{ts.isoformat()}|{assunto[:40]}")

                eventos.append({
                    "source": "gmail",
                    "external_id": gm_id,
                    "ts": ts.isoformat(timespec="seconds"),
                    "kind": kind,
                    "title": assunto,
                    "who": remetente,
                    "amount_brl": extrair_valor(assunto) if kind == "dinheiro" else None,
                    "link": f"https://mail.google.com/mail/u/0/#all/{gm_id}",
                    "raw": {"labels": labels},
                })

        return eventos
    finally:
        try:
            imap.close()
        except Exception:
            pass
        imap.logout()
