from fast_flights import FlightData, Passengers, get_flights
from datetime import datetime, date
from dateutil import tz

BRT = tz.gettz("America/Sao_Paulo")

def search_one_way(origin: str, destination: str, flight_date: date):
    try:
        result = get_flights(
            flight_data=[
                FlightData(
                    date=flight_date.strftime("%Y-%m-%d"),
                    from_airport=origin,
                    to_airport=destination,
                )
            ],
            trip="one-way",
            seat="economy",
            passengers=Passengers(adults=1),
            fetch_mode="fallback",
        )
    except Exception as e:
        print(f"Erro buscando {origin}->{destination} em {flight_date}: {e}")
        return []

    flights = []
    for f in result.flights:
        try:
            dep = _parse_time(f.departure, flight_date)
            arr = _parse_time(f.arrival, flight_date)
        except Exception:
            continue

        price = _parse_price(f.price)
        if price is None:
            continue

        flights.append({
            "airline": f.name,
            "departure": dep,
            "arrival": arr,
            "duration": f.duration,
            "stops": f.stops,
            "is_direct": f.stops == 0,
            "price_brl": price,
            "origin": origin,
            "destination": destination,
            "date": flight_date,
        })
    return flights

def _parse_time(s: str, ref_date: date) -> datetime:
    time_part = s.split(" on ")[0].strip()
    dt = datetime.strptime(time_part, "%I:%M %p")
    return datetime.combine(ref_date, dt.time(), tzinfo=BRT)

def _parse_price(s):
    if not s:
        return None
    cleaned = s.replace("R$", "").replace(".", "").replace(",", ".").strip()
    try:
        return float(cleaned)
    except ValueError:
        return None

def build_purchase_link(origin: str, destination: str, out_date, ret_date) -> str:
    return (
        f"https://www.google.com/travel/flights?q=Flights%20to%20{destination}"
        f"%20from%20{origin}%20on%20{out_date}%20returning%20{ret_date}"
    )
