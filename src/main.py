from flight_search import search_one_way, build_purchase_link
from filters import get_future_window_dates, filter_flights
from notifier import send_telegram, format_alert

PRICE_THRESHOLD = 800.00
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
    pairs = get_future_window_dates(days_start=60, days_end=90)
    print(f"Verificando {len(pairs)} combinacoes de datas (60-90 dias no futuro)...")

    alerts_sent = 0
    cheapest_overall = None  # Guarda a mais barata de todas
    
    for out_date, ret_date in pairs:
        result = find_best_pair(out_date, ret_date)
        if not result:
            continue
        
        # Atualiza a mais barata de todas (independente do limite)
        if cheapest_overall is None or result["total"] < cheapest_overall["total"]:
            cheapest_overall = result
            cheapest_overall["out_date"] = out_date
            cheapest_overall["ret_date"] = ret_date
        
        # Se estiver abaixo do limite, envia alerta
        if result["total"] < PRICE_THRESHOLD:
            link = build_purchase_link(result["airport"], DEST, out_date, ret_date)
            result["out"]["_link"] = link
            msg = format_alert(
                result["out"], result["ret"], result["total"],
                result["airport"], result["scarcity"]
            )
            send_telegram(msg)
            alerts_sent += 1
            print(f"  ✅ Alerta enviado: {out_date} R$ {result['total']:.2f}")
        else:
            print(f"  {out_date} -> {ret_date}: R$ {result['total']:.2f} (acima do limite)")
    
    # Se não enviou nenhum alerta, envia a mais barata encontrada
    if alerts_sent == 0 and cheapest_overall is not None:
        out_date = cheapest_overall["out_date"]
        ret_date = cheapest_overall["ret_date"]
        link = build_purchase_link(
            cheapest_overall["airport"], DEST, out_date, ret_date
        )
        cheapest_overall["out"]["_link"] = link
        
        # Adiciona aviso ao scarcity_note
        warning = f"⚠️ Nenhuma oferta abaixo de R$ {PRICE_THRESHOLD:.0f}. Esta é a mais barata encontrada."
        scarcity_combined = (
            cheapest_overall["scarcity"] + "\n" + warning
            if cheapest_overall["scarcity"]
            else warning
        )
        
        msg = format_alert(
            cheapest_overall["out"], cheapest_overall["ret"], 
            cheapest_overall["total"],
            cheapest_overall["airport"], scarcity_combined
        )
        send_telegram(msg)
        alerts_sent += 1
        print(f"  💡 Enviando passagem mais barata: {out_date} R$ {cheapest_overall['total']:.2f}")

    print(f"\nExecucao concluida. {alerts_sent} alerta(s) enviado(s).")
    
    # Log de uso da SerpAPI
    searches_this_run = len(pairs) * 2
    print(f"\n--- Uso da SerpAPI ---")
    print(f"Buscas nesta execucao: {searches_this_run}")
    print(f"Estimativa mensal (1x/dia): ~{searches_this_run * 30} buscas")
    print(f"Limite gratis: 250 buscas/mes")
    print(f"Verificar uso real em: https://serpapi.com/account")

if __name__ == "__main__":
    main()
