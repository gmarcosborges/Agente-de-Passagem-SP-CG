"""Busca de voos SP -> Campo Grande, na especificacao que o Gabriel pediu.

Duas perguntas por execucao:

  1. A VIAGEM FIXA: ida 08/10 a noite, volta 12/10 a tarde ou a noite.
     Sempre reportada, custe o que custar - ele quer acompanhar o preco.

  2. O MELHOR FIM DE SEMANA: ida quinta ou sexta depois das 20h, volta
     domingo a tarde ou a noite, dentro de uma janela futura. Devolve o
     par mais barato e a data.

Sem preferencia de companhia, sem exigir voo direto: vale a mais barata.
Aceita ate uma conexao.

POR QUE ISTO RODA AQUI E NAO NO LIFE INBOX: a sessao do Life Inbox nao
alcanca google.com nem serpapi.com - o proxy da rede dela bloqueia os
dois. O GitHub Actions alcanca, e a chave da SerpAPI ja mora nos secrets
deste repositorio. Entao a busca roda aqui, grava data/voos.json, e o
Life Inbox le esse arquivo pela API do GitHub, que e um dos poucos
enderecos que a rede dele alcanca.
"""
import json
import os
import sys
from datetime import date, datetime, time, timedelta
from pathlib import Path

from dateutil import tz

from flight_search import build_purchase_link, search_one_way

BRT = tz.gettz("America/Sao_Paulo")

SP = ["CGH", "GRU"]
DEST = "CGR"

# A viagem fixa que ele quer acompanhar sempre.
VIAGEM_FIXA_IDA = date(2026, 10, 8)
VIAGEM_FIXA_VOLTA = date(2026, 10, 12)

# Janela da busca flexivel, em dias a partir de hoje.
JANELA_INICIO = int(os.environ.get("JANELA_INICIO", "14"))
JANELA_FIM = int(os.environ.get("JANELA_FIM", "90"))

SAIDA = Path(__file__).resolve().parent.parent / "data" / "voos.json"


def ida_valida(voo):
    """Ida: quinta ou sexta, decolando das 20h em diante."""
    return voo["departure"].time() >= time(20, 0)


def volta_valida(voo):
    """Volta: domingo, decolando do meio-dia em diante (tarde ou noite)."""
    return voo["departure"].time() >= time(12, 0)


def _mais_barato(voos, criterio):
    validos = [v for v in voos if criterio(v)]
    return min(validos, key=lambda v: v["price_brl"]) if validos else None


def _resumir(voo):
    if voo is None:
        return None
    return {
        "companhia": voo["airline"],
        "origem": voo["origin"],
        "destino": voo["destination"],
        "partida": voo["departure"].strftime("%d/%m %H:%M"),
        "chegada": voo["arrival"].strftime("%d/%m %H:%M"),
        "direto": voo["is_direct"],
        "conexoes": voo["stops"],
        "preco_brl": round(voo["price_brl"], 2),
    }


def melhor_par(ida_data, volta_data, exigir_horario=True):
    """Melhor combinacao ida+volta entre CGH e GRU, pelo preco total."""
    melhor = None

    for sp in SP:
        idas = search_one_way(sp, DEST, ida_data, apenas_diretos=False)
        voltas = search_one_way(DEST, sp, volta_data, apenas_diretos=False)

        criterio_ida = ida_valida if exigir_horario else (lambda v: True)
        criterio_volta = volta_valida if exigir_horario else (lambda v: True)

        melhor_ida = _mais_barato(idas, criterio_ida)
        melhor_volta = _mais_barato(voltas, criterio_volta)
        if not melhor_ida or not melhor_volta:
            continue

        total = melhor_ida["price_brl"] + melhor_volta["price_brl"]
        if melhor is None or total < melhor["total_brl"]:
            melhor = {
                "aeroporto_sp": sp,
                "ida": ida_data.isoformat(),
                "volta": volta_data.isoformat(),
                "total_brl": round(total, 2),
                "ida_detalhe": _resumir(melhor_ida),
                "volta_detalhe": _resumir(melhor_volta),
                "link": build_purchase_link(sp, DEST, ida_data, volta_data),
            }

    return melhor


def pares_quinta_sexta_domingo():
    """Quinta ou sexta -> domingo seguinte, dentro da janela."""
    hoje = datetime.now(BRT).date()
    atual = hoje + timedelta(days=JANELA_INICIO)
    fim = hoje + timedelta(days=JANELA_FIM)

    pares = []
    while atual <= fim:
        if atual.weekday() in (3, 4):  # quinta, sexta
            dias_ate_domingo = (6 - atual.weekday()) % 7 or 7
            volta = atual + timedelta(days=dias_ate_domingo)
            if volta <= fim:
                pares.append((atual, volta))
        atual += timedelta(days=1)
    return pares


def main():
    erros = []

    print(f"Viagem fixa: {VIAGEM_FIXA_IDA} -> {VIAGEM_FIXA_VOLTA}", file=sys.stderr)
    try:
        fixa = melhor_par(VIAGEM_FIXA_IDA, VIAGEM_FIXA_VOLTA)
    except Exception as e:
        fixa, _ = None, erros.append(f"viagem fixa: {type(e).__name__}")

    pares = pares_quinta_sexta_domingo()
    print(f"Janela flexivel: {len(pares)} combinacoes", file=sys.stderr)

    melhor_fds = None
    for ida, volta in pares:
        try:
            candidato = melhor_par(ida, volta)
        except Exception as e:
            erros.append(f"{ida}: {type(e).__name__}")
            continue
        if candidato and (melhor_fds is None or candidato["total_brl"] < melhor_fds["total_brl"]):
            melhor_fds = candidato
            print(f"  novo melhor: {ida} R$ {candidato['total_brl']:.2f}", file=sys.stderr)

    resultado = {
        "atualizado_em": datetime.now(BRT).isoformat(timespec="seconds"),
        "viagem_fixa": fixa,
        "melhor_fim_de_semana": melhor_fds,
        "combinacoes_testadas": len(pares),
        "erros": erros,
    }

    SAIDA.parent.mkdir(parents=True, exist_ok=True)
    SAIDA.write_text(json.dumps(resultado, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Gravado em {SAIDA}", file=sys.stderr)
    return 1 if erros and not (fixa or melhor_fds) else 0


if __name__ == "__main__":
    sys.exit(main())
