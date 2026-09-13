import os
import requests
from datetime import datetime, date
from dateutil import tz

BRT = tz.gettz("America/Sao_Paulo")
SERPAPI_BASE = "https://serpapi.com/search.json"

def search_one_way(origin: str, destination: str, flight_date: date, apenas_diretos: bool = True):
    """Busca voos via SerpAPI Google Flights.

    apenas_diretos=False aceita ate uma conexao: o Gabriel pediu a mais
    barata, sem preferencia de companhia nem de trecho.
    """
    api_key = os.environ["SERPAPI_KEY"]
    
    print(f"  Buscando {origin}→{destination} em {flight_date}...")
    
    try:
        r = requests.get(
            SERPAPI_BASE,
            params={
                "engine": "google_flights",
                "departure_id": origin,
                "arrival_id": destination,
                "outbound_date": flight_date.strftime("%Y-%m-%d"),
                "type": "2",  # one-way
                "currency": "BRL",
                "hl": "pt",
                "api_key": api_key,
            },
            timeout=30,
        )
        r.raise_for_status()
        data = r.json()
        
        best_flights = data.get("best_flights", [])
        print(f"    Retornou {len(best_flights)} opções")
        
    except Exception as e:
        print(f"    Erro na SerpAPI: {e}")
        return []
    
    flights = []
    for offer in best_flights:
        try:
            segmentos = offer.get("flights") or []
            if not segmentos:
                continue
            if apenas_diretos and len(segmentos) != 1:
                continue
            if len(segmentos) > 2:
                continue  # duas conexoes ja nao vale a pena

            # Sai no primeiro segmento, chega no ultimo.
            flight_seg = segmentos[0]
            dep_airport = segmentos[0]["departure_airport"]
            arr_airport = segmentos[-1]["arrival_airport"]
            
            # Parse timestamps
            dep = datetime.strptime(dep_airport["time"], "%Y-%m-%d %H:%M")
            arr = datetime.strptime(arr_airport["time"], "%Y-%m-%d %H:%M")
            dep = dep.replace(tzinfo=BRT)
            arr = arr.replace(tzinfo=BRT)
            
            airline = flight_seg.get("airline", "Desconhecida")
            price = float(offer.get("price", 0))
            
            flights.append({
                "airline": airline,
                "departure": dep,
                "arrival": arr,
                "duration": f"{flight_seg.get('duration', 0)} min",
                "stops": len(segmentos) - 1,
                "is_direct": len(segmentos) == 1,
                "price_brl": price,
                "origin": origin,
                "destination": destination,
                "date": flight_date,
            })
            
        except Exception as e:
            print(f"    Erro parseando oferta: {e}")
            continue
    
    print(f"    Encontrados {len(flights)} voos diretos")
    return flights

def build_purchase_link(origin: str, destination: str, out_date, ret_date) -> str:
    return (
        f"https://www.google.com/travel/flights?q=Flights%20to%20{destination}"
        f"%20from%20{origin}%20on%20{out_date}%20returning%20{ret_date}"
    )
