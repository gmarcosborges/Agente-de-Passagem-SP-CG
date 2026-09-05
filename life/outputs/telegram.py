"""Saida por Telegram. Se nao estiver configurado, cai pro terminal."""
import os

import requests


def configurado():
    return bool(os.environ.get("TELEGRAM_BOT_TOKEN") and os.environ.get("TELEGRAM_CHAT_ID"))


SEM_TELEGRAM = """
Telegram nao configurado, e o briefing NAO vai ser impresso.

Ele tem assunto de email dentro, e aqui isso viraria log gravado.
Configure TELEGRAM_BOT_TOKEN e TELEGRAM_CHAT_ID, ou rode com --stdout
se voce esta na sua maquina e quer ver na tela mesmo.
"""


def enviar(mensagem, permitir_terminal=False):
    if not configurado():
        # Cair pro terminal so quando alguem pediu isso explicitamente.
        if not permitir_terminal:
            raise SystemExit(SEM_TELEGRAM)
        print("\n[Telegram nao configurado - mostrando aqui]\n")
        print(mensagem)
        return False

    r = requests.post(
        f"https://api.telegram.org/bot{os.environ['TELEGRAM_BOT_TOKEN']}/sendMessage",
        json={
            "chat_id": os.environ["TELEGRAM_CHAT_ID"],
            "text": mensagem,
            "parse_mode": "Markdown",
            "disable_web_page_preview": True,
        },
        timeout=15,
    )
    r.raise_for_status()
    return True
