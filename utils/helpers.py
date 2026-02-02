"""
Fonctions utilitaires
Air Traffic Management - RDC
"""

from datetime import datetime, timedelta
import math


def format_duration(minutes):
    if not minutes:
        return "0m"
    
    hours = int(minutes // 60)
    mins = int(minutes % 60)
    
    if hours > 0:
        return f"{hours}h {mins}m"
    return f"{mins}m"


def format_distance(km):
    if not km:
        return "0 km"
    return f"{km:,.1f} km"


def format_currency(amount, currency='USD'):
    if not amount:
        return f"0.00 {currency}"
    return f"{amount:,.2f} {currency}"


def format_altitude(feet):
    if not feet:
        return "0 ft"
    
    if feet >= 1000:
        fl = feet / 100
        return f"FL{int(fl)}"
    return f"{int(feet)} ft"


def format_speed(knots):
    if not knots:
        return "0 kts"
    return f"{int(knots)} kts"


def is_night_time(dt=None, timezone_offset=1):
    if dt is None:
        dt = datetime.utcnow()
    
    local_hour = (dt.hour + timezone_offset) % 24
    
    return local_hour >= 18 or local_hour < 6


def calculate_eta(distance_km, speed_kmh):
    if not distance_km or not speed_kmh:
        return None
    
    hours = distance_km / speed_kmh
    return datetime.utcnow() + timedelta(hours=hours)


def degrees_to_cardinal(degrees):
    if degrees is None:
        return "N/A"
    
    directions = ['N', 'NNE', 'NE', 'ENE', 'E', 'ESE', 'SE', 'SSE',
                  'S', 'SSW', 'SW', 'WSW', 'W', 'WNW', 'NW', 'NNW']
    
    index = round(degrees / 22.5) % 16
    return directions[index]


def generate_invoice_number():
    from models import Invoice
    today = datetime.now().strftime('%Y%m%d')
    count = Invoice.query.filter(
        Invoice.invoice_number.like(f'RVA-{today}%')
    ).count()
    return f"RVA-{today}-{count + 1:04d}"
