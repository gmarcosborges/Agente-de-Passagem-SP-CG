from datetime import datetime, time, timedelta
from dateutil import tz

BRT = tz.gettz("America/Sao_Paulo")

def get_search_dates(weeks_ahead: int = 2):
    """Retorna lista de (data_ida, data_volta) para próximas N semanas."""
    today = datetime.now(BRT).date()
    pairs = []
    for i in range(weeks_ahead * 7 + 1):
        d = today + timedelta(days=i)
        if d.weekday() in (3, 4):
            days_to_sunday = (6 - d.weekday()) % 7
            if days_to_sunday == 0:
                days_to_sunday = 2
            volta = d + timedelta(days=days_to_sunday)
            pairs.append((d, volta))
    return pairs

def is_valid_outbound_time(departure_dt: datetime, arrival_dt: datetime) -> bool:
    dep_t = departure_dt.time()
    arr_t = arrival_dt.time()

    if dep_t < time(9, 0):
        return True
    if dep_t > time(19, 0):
        return True
    if dep_t <= time(18, 50) and arr_t > time(19, 0):
        return True
    return False

def filter_flights(flights: list, direction: str) -> list:
    out = []
    for f in flights:
        if not f.get("is_direct"):
            continue
        if direction == "outbound":
            if not is_valid_outbound_time(f["departure"], f["arrival"]):
                continue
        out.append(f)
    return out
