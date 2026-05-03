import os
import requests
from datetime import datetime, date
from dateutil import tz

BRT = tz.gettz("America/Sao_Paulo")
SERPAPI_BASE = "https://serpapi.com/search.json"

def search_one_way(origin: str, destination: str, flight_date: date):
    """Busca voos via SerpAPI Google Flights."""
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
            # Pega primeiro segmento (voo direto tem só 1)
            if not offer.get("flights") or len(offer["flights"]) != 1:
                continue  # Pula voos com conexão
            
            flight_seg = offer["flights"][0]
            
            dep_airport = flight_seg["departure_airport"]
            arr_airport = flight_seg["arrival_airport"]
            
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
                "stops": 0,
                "is_direct": True,
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
