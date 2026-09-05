"""Saida por Telegram. Se nao estiver configurado, cai pro terminal."""
import os

import requests


def configurado():
    return bool(os.environ.get("TELEGRAM_BOT_TOKEN") and os.environ.get("TELEGRAM_CHAT_ID"))


def enviar(mensagem):
    if not configurado():
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
