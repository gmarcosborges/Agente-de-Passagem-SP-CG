from flight_search import search_one_way, build_purchase_link
from filters import get_search_dates, filter_flights
from notifier import send_telegram, format_alert

PRICE_THRESHOLD = 5000.00
SP_AIRPORTS = ["CGH", "GRU"]
DEST = "CGR"

def find_best_pair(out_date, ret_date):
    for sp in SP_AIRPORTS:
        out_raw = search_one_way(sp, DEST, out_date)
        out_valid = filter_flights(out_raw, "outbound")
        if not out_valid:
            continue

        ret_raw = search_one_way(DEST, sp, ret_date)
        ret_valid = filter_flights(ret_raw, "return")
        if not ret_valid:
            continue

        out_best = min(out_valid, key=lambda x: x["price_brl"])
        ret_best = min(ret_valid, key=lambda x: x["price_brl"])
        total = out_best["price_brl"] + ret_best["price_brl"]

        scarcity = ""
        if len(out_valid) == 1 or len(ret_valid) == 1:
            scarcity = "Poucas opcoes disponiveis nesta data."

        return {
            "out": out_best,
            "ret": ret_best,
            "total": total,
            "airport": sp,
            "scarcity": scarcity,
        }
    return None

def main():
    pairs = get_search_dates(weeks_ahead=2)
    print(f"Verificando {len(pairs)} combinacoes de datas...")

    alerts_sent = 0
    for out_date, ret_date in pairs:
        result = find_best_pair(out_date, ret_date)
        if not result:
            continue
        if result["total"] >= PRICE_THRESHOLD:
            print(f"  {out_date} -> {ret_date}: R$ {result['total']:.2f} (acima do limite)")
            continue

        link = build_purchase_link(
            result["airport"], DEST, out_date, ret_date
        )
        result["out"]["_link"] = link
        msg = format_alert(
            result["out"], result["ret"], result["total"],
            result["airport"], result["scarcity"]
        )
        send_telegram(msg)
        alerts_sent += 1
        print(f"  Alerta enviado: {out_date} R$ {result['total']:.2f}")

    print(f"Execucao concluida. {alerts_sent} alerta(s) enviado(s).")

if __name__ == "__main__":
    main()
