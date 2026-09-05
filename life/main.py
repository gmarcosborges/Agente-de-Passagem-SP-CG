"""Life Inbox - o coletor da vida, v0.

Roda uma vez por dia: coleta -> classifica -> guarda -> resume.

    python -m life.main              # coleta de verdade e manda o briefing
    python -m life.main --stdout     # imprime o briefing em vez de enviar
    python -m life.main --demo       # roda com dados falsos, sem tocar no Google
"""
import argparse
import sys
import traceback

from life import brief, store
from life.outputs import telegram

COLETORES = {
    "gmail": "life.collectors.gmail",
    "gcalendar": "life.collectors.gcalendar",
}


def _importar(caminho):
    modulo = __import__(caminho, fromlist=["coletar"])
    return modulo.coletar


def coletar_tudo(apenas=None):
    """Roda os coletores. Um coletor que falha nao derruba os outros."""
    eventos, falhas = [], []
    for nome, caminho in COLETORES.items():
        if apenas and nome not in apenas:
            continue
        try:
            novos = _importar(caminho)()
            print(f"  {nome}: {len(novos)} eventos", file=sys.stderr)
            eventos.extend(novos)
        except SystemExit:
            raise
        except Exception as e:
            falhas.append(f"{nome}: {e}")
            print(f"  {nome}: FALHOU - {e}", file=sys.stderr)
            traceback.print_exc(file=sys.stderr)
    return eventos, falhas


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
