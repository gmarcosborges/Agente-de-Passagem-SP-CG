import os
import requests

def send_telegram(message: str):
    token = os.environ["TELEGRAM_BOT_TOKEN"]
    chat_id = os.environ["TELEGRAM_CHAT_ID"]
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    r = requests.post(url, json={
        "chat_id": chat_id,
        "text": message,
        "parse_mode": "Markdown",
        "disable_web_page_preview": False,
    }, timeout=15)
    r.raise_for_status()

def format_alert(out_flight, ret_flight, total_price, airport_used, scarcity_note=""):
    link = out_flight["_link"]
    msg = f"""✈️ *OFERTA ENCONTRADA — CGR*

💰 *Total ida+volta:* R$ {total_price:.2f}
🛫 *Aeroporto SP:* {airport_used}

*IDA* — {out_flight['date'].strftime('%a %d/%m')}
{out_flight['airline']} • {out_flight['departure'].strftime('%H:%M')} → {out_flight['arrival'].strftime('%H:%M')}
{out_flight['origin']} → {out_flight['destination']} • Direto ✅
R$ {out_flight['price_brl']:.2f}

*VOLTA* — {ret_flight['date'].strftime('%a %d/%m')}
{ret_flight['airline']} • {ret_flight['departure'].strftime('%H:%M')} → {ret_flight['arrival'].strftime('%H:%M')}
{ret_flight['origin']} → {ret_flight['destination']} • Direto ✅
R$ {ret_flight['price_brl']:.2f}

🔗 [Ver no Google Flights]({link})
"""
    if scarcity_note:
        msg += f"\n⚠️ {scarcity_note}"
    return msg
