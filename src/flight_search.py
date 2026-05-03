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
    print(f"    URL: {url}")
    
    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            context = browser.new_context(
                viewport={'width': 1920, 'height': 1080},
                user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            )
            page = context.new_page()
            
            print(f"    Carregando página...")
            page.goto(url, timeout=90000, wait_until='networkidle')
            
            # Aguarda 5 segundos pro JS renderizar
            page.wait_for_timeout(5000)
            
            # Tenta vários seletores possíveis
            selectors = [
                '[role="listitem"]',
                '.pIav2d',  # classe comum de card de voo
                '[jsname]',  # elementos com atributo jsname
            ]
            
            content_loaded = False
            for selector in selectors:
                try:
                    page.wait_for_selector(selector, timeout=10000)
                    print(f"    Encontrou elementos: {selector}")
                    content_loaded = True
                    break
                except PlaywrightTimeout:
                    continue
            
            if not content_loaded:
                print(f"    Nenhum seletor funcionou. HTML da página:")
                print(page.content()[:2000])  # Primeiros 2000 chars
                browser.close()
                return []
            
            # Extrai texto da página inteira
            page_text = page.inner_text('body')
            
            # Procura por padrões de preço + horário no texto
            # Exemplo: "R$ 450" ... "07:30 – 09:00" ... "Direto"
            flights = []
            
            # Regex pra encontrar blocos de voo
            # Formato: preço + horários + "Direto"
            pattern = r'R\$\s*([\d.]+).*?(\d{1,2}:\d{2})\s*[–-]\s*(\d{1,2}:\d{2}).*?Direto'
            matches = re.finditer(pattern, page_text, re.DOTALL | re.MULTILINE)
            
            for match in matches:
                try:
                    price_str = match.group(1).replace(".", "")
                    price = float(price_str)
                    dep_str = match.group(2)
                    arr_str = match.group(3)
                    
                    dep = datetime.strptime(dep_str, "%H:%M")
                    arr = datetime.strptime(arr_str, "%H:%M")
                    dep = datetime.combine(flight_date, dep.time(), tzinfo=BRT)
                    arr = datetime.combine(flight_date, arr.time(), tzinfo=BRT)
                    
                    if arr < dep:
                        arr = arr + timedelta(days=1)
                    
                    # Tenta extrair companhia
                    airline = "Companhia aérea"
                    chunk = page_text[max(0, match.start() - 100):match.start()]
                    for name in ["LATAM", "GOL", "Azul", "Voepass"]:
                        if name in chunk:
                            airline = name
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
                    print(f"    Erro parseando match: {e}")
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
