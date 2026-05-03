from datetime import datetime, time, timedelta
from dateutil import tz

BRT = tz.gettz("America/Sao_Paulo")

def get_future_window_dates(days_start: int = 60, days_end: int = 90):
    """
    Retorna combinações de quinta/sexta + domingo numa janela futura.
    
    days_start: quantos dias no futuro começar a buscar (padrão: 60)
    days_end: quantos dias no futuro terminar de buscar (padrão: 90)
    
    Exemplo: hoje é 3 maio → busca de 2 julho a 1 agosto (60-90 dias)
    """
    today = datetime.now(BRT).date()
    
    # Calcula início e fim da janela
    start_date = today + timedelta(days=days_start)
    end_date = today + timedelta(days=days_end)
    
    pairs = []
    current = start_date
    
    # Varre todos os dias na janela
    while current <= end_date:
        # Quinta (3) ou sexta (4)
        if current.weekday() in (3, 4):
            # Próximo domingo
            days_to_sunday = (6 - current.weekday()) % 7
            if days_to_sunday == 0:
                days_to_sunday = 7  # se já for domingo, pula pra próximo
            volta = current + timedelta(days=days_to_sunday)
            
            # Só adiciona se a volta também estiver dentro da janela
            if volta <= end_date:
                pairs.append((current, volta))
        
        current += timedelta(days=1)
    
    return pairs

def is_valid_outbound_time(departure_dt, arrival_dt):
    dep_t = departure_dt.time()
    arr_t = arrival_dt.time()
    if dep_t < time(9, 0):
        return True
    if dep_t > time(19, 0):
        return True
    if dep_t <= time(18, 50) and arr_t > time(19, 0):
        return True
    return False

def filter_flights(flights, direction):
    out = []
    for f in flights:
        if not f.get("is_direct"):
            continue
        if direction == "outbound":
            if not is_valid_outbound_time(f["departure"], f["arrival"]):
                continue
        out.append(f)
    return out
