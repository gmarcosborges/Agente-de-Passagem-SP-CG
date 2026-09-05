"""Life Inbox - o coletor da vida, v0.

Roda uma vez por dia: coleta -> classifica -> guarda -> resume.

    python -m life.main              # coleta de verdade e manda o briefing
    python -m life.main --stdout     # imprime o briefing em vez de enviar
    python -m life.main --demo       # roda com dados falsos, sem tocar no Google
"""
import argparse
import os
import sys
import traceback

from life import brief, collectors, store
from life.outputs import telegram

# Traceback pode carregar pedaco de email; so aparece se voce pedir.
DEBUG = os.environ.get("LIFE_DEBUG") == "1"


def coletar_tudo(apenas=None):
    """Roda os coletores. Um coletor que falha nao derruba os outros."""
    eventos, falhas = [], []
    escolhidos = collectors.disponiveis(apenas)
    if not escolhidos:
        raise SystemExit(SEM_CONFIG)

    for nome, coletar in escolhidos:
        try:
            novos = coletar()
            print(f"  {nome}: {len(novos)} eventos", file=sys.stderr)
            eventos.extend(novos)
        except SystemExit:
            raise
        except Exception as e:
            falhas.append(f"{nome}: {type(e).__name__}")
            print(f"  {nome}: FALHOU - {type(e).__name__}: {e}", file=sys.stderr)
            if DEBUG:
                traceback.print_exc(file=sys.stderr)
    return eventos, falhas


SEM_CONFIG = """
Nenhuma fonte configurada.

Na nuvem (sem computador ligado), no .env ou nos secrets:
  IMAP_USER / IMAP_PASSWORD   senha de app do Google
  CALENDAR_ICS_URL            endereco secreto em formato iCal

Na sua maquina, como alternativa:
  ~/.life-inbox/credentials.json   credencial OAuth somente leitura

Detalhes em docs/life-inbox.md
"""


def eventos_demo():
    from datetime import datetime, timedelta

    from life.config import BRT

    agora = datetime.now(BRT)
    return [
        {"source": "demo", "external_id": "1", "ts": (agora + timedelta(hours=2)).isoformat(),
         "kind": "compromisso", "title": "Consulta dentista", "who": "voce@gmail.com",
         "amount_brl": None, "link": None, "raw": {"dia_inteiro": False}},
        {"source": "demo", "external_id": "2", "ts": agora.isoformat(), "kind": "dinheiro",
         "title": "Fatura do cartao vence sexta - R$ 1.240,50", "who": "Banco <no-reply@banco.com>",
         "amount_brl": 1240.50, "link": None, "raw": {}},
        {"source": "demo", "external_id": "3", "ts": agora.isoformat(), "kind": "acao",
         "title": "Pode confirmar o horario de sabado?", "who": "Joao <joao@gmail.com>",
         "amount_brl": None, "link": None, "raw": {}},
        {"source": "demo", "external_id": "4", "ts": agora.isoformat(), "kind": "ruido",
         "title": "50% OFF so hoje", "who": "mkt@loja.com", "amount_brl": None,
         "link": None, "raw": {}},
    ]


def main():
    p = argparse.ArgumentParser(description="Life Inbox - briefing diario da sua vida")
    p.add_argument("--stdout", action="store_true", help="imprime em vez de enviar no Telegram")
    p.add_argument("--demo", action="store_true", help="dados falsos, sem chamar o Google")
    p.add_argument("--sem-banco", action="store_true", help="nao grava nada no SQLite")
    p.add_argument("--fonte", action="append", help="rodar so estas fontes (repetivel)")
    args = p.parse_args()

    print("Coletando...", file=sys.stderr)
    if args.demo:
        eventos, falhas = eventos_demo(), []
    else:
        eventos, falhas = coletar_tudo(apenas=args.fonte)

    if args.sem_banco or args.demo:
        novos = eventos
    else:
        conn = store.connect()
        novos = store.save_events(conn, eventos)
        print(f"  {len(novos)} novos de {len(eventos)} coletados", file=sys.stderr)
        conn.close()

    mensagem = brief.montar(novos)
    if falhas:
        mensagem += "\n\n_Falhas: " + "; ".join(falhas) + "_"

    if args.stdout:
        print(mensagem)
    else:
        telegram.enviar(mensagem)

    return 1 if falhas else 0


if __name__ == "__main__":
    sys.exit(main())
