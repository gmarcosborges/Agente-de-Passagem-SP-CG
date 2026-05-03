import re
from datetime import datetime, date, timedelta
from dateutil import tz
from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeout

BRT = tz.gettz("America/Sao_Paulo")

def search_one_way(origin: str, destination: str, flight_date: date):
    """Busca voos via Google Flights usando Playwright."""
    url = (
        f"https://www.google.com/travel/flights?q=Flights%20to%20{destination}"
        f"%20from%20{origin}%20on%20{flight_date.strftime('%Y-%m-%d')}"
        f"&curr=BRL&hl=pt-BR"
    )
    
    print(f"  Buscando {origin}→{destination} em {flight_date}...")
    
    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page()
            page.goto(url, timeout=60000)
            
            # Espera a página carregar resultados (até 30s)
            try:
                page.wait_for_selector('[role="listitem"]', timeout=30000)
            except PlaywrightTimeout:
                print(f"    Timeout esperando resultados")
                browser.close()
                return []
            
            # Extrai voos da página
            flights = []
            items = page.query_selector_all('[role="listitem"]')
            
            for item in items[:10]:  # Limita aos 10 primeiros
                try:
                    text = item.inner_text()
                    
                    # Verifica se é voo direto
                    if "escala" in text.lower() or "conexão" in text.lower():
                        continue
                    if "Direto" not in text and "Nonstop" not in text:
                        continue
                    
                    # Extrai horários (formato: "07:30 – 09:00")
                    time_match = re.search(r'(\d{1,2}:\d{2})\s*–\s*(\d{1,2}:\d{2})', text)
                    if not time_match:
                        continue
                    
                    dep_str, arr_str = time_match.groups()
                    dep = datetime.strptime(dep_str, "%H:%M")
                    arr = datetime.strptime(arr_str, "%H:%M")
                    dep = datetime.combine(flight_date, dep.time(), tzinfo=BRT)
                    arr = datetime.combine(flight_date, arr.time(), tzinfo=BRT)
                    
                    # Se chegada é antes da partida, assumir dia seguinte
                    if arr < dep:
                        arr = arr + timedelta(days=1)
                    
                    # Extrai preço (formato: "R$ 450" ou "R$ 1.450")
                    price_match = re.search(r'R\$\s*([\d.]+)', text)
                    if not price_match:
                        continue
                    
                    price_str = price_match.group(1).replace(".", "")
                    price = float(price_str)
                    
                    # Extrai companhia aérea (geralmente primeira linha)
                    airline = "Desconhecida"
                    lines = text.split('\n')
                    for line in lines:
                        if any(x in line for x in ["LATAM", "GOL", "Azul", "Voepass"]):
                            airline = line.strip()
                            break
                    
                    flights.append({
                        "airline": airline,
                        "departure": dep,
                        "arrival": arr,
                        "duration": "",
                        "stops": 0,
                        "is_direct": True,
                        "price_brl": price,
                        "origin": origin,
                        "destination": destination,
                        "date": flight_date,
                    })
                    
                except Exception as e:
                    print(f"    Erro parseando item: {e}")
                    continue
            
            browser.close()
            print(f"    Encontrados {len(flights)} voos diretos")
            return flights
            
    except Exception as e:
        print(f"    Erro no Playwright: {e}")
        return []

def build_purchase_link(origin: str, destination: str, out_date, ret_date) -> str:
    return (
        f"https://www.google.com/travel/flights?q=Flights%20to%20{destination}"
        f"%20from%20{origin}%20on%20{out_date}%20returning%20{ret_date}"
    )
