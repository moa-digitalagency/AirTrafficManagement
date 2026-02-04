"""
/* * Nom de l'application : ATM-RDC
 * Description : Source file: flight_tracker.py
 * Produit de : MOA Digital Agency, www.myoneart.com
 * Fait par : Aisance KALONJI, www.aisancekalonji.com
 * Auditer par : La CyberConfiance, www.cyberconfiance.com
 */
"""
"""
Service de suivi des vols en temps réel
Air Traffic Management - RDC
"""

from datetime import datetime
import random
import math
import os
from functools import lru_cache

from shapely.geometry import Point, shape
from shapely.prepared import prep
from geoalchemy2.shape import to_shape
from models import db, Flight, FlightPosition, Aircraft, Airport, Overflight, Landing, TariffConfig, Airspace, SystemConfig
from services.api_client import fetch_external_flight_data, openweathermap, aviationweather
from services.invoice_generator import trigger_auto_invoice
from services.telegram_service import TelegramService
from services.translation_service import t

CACHED_RDC_BOUNDARY_GEOM = None

RDC_BOUNDARY = {
    "type": "Feature",
    "properties": {"name": "République Démocratique du Congo"},
    "geometry": {
        "type": "Polygon",
        "coordinates": [[
            [12.2, -5.9],
            [12.5, -4.6],
            [13.1, -4.5],
            [14.0, -4.4],
            [15.8, -4.0],
            [16.2, -2.0],
            [16.5, -1.0],
            [17.8, -0.5],
            [18.5, 2.0],
            [19.5, 3.0],
            [21.0, 4.0],
            [24.0, 5.5],
            [27.4, 5.0],
            [28.0, 4.5],
            [29.0, 4.3],
            [29.5, 3.0],
            [29.8, 1.5],
            [29.6, -1.0],
            [29.2, -1.5],
            [29.0, -2.8],
            [29.5, -4.5],
            [29.0, -6.0],
            [30.5, -8.0],
            [30.0, -10.0],
            [28.5, -11.0],
            [27.5, -12.0],
            [25.0, -12.5],
            [22.0, -13.0],
            [21.5, -12.0],
            [20.0, -11.0],
            [18.0, -9.5],
            [16.0, -8.0],
            [13.0, -6.5],
            [12.2, -5.9]
        ]]
    }
}


def get_rdc_boundary():
    return RDC_BOUNDARY


def get_rdc_boundary_geom():
    """
    Get cached RDC boundary geometry (prepared for fast spatial checks).
    Tries DB first, falls back to hardcoded constant.
    """
    global CACHED_RDC_BOUNDARY_GEOM

    if CACHED_RDC_BOUNDARY_GEOM is not None:
        return CACHED_RDC_BOUNDARY_GEOM

    # Try fetching from DB
    try:
        airspace = Airspace.query.filter_by(type='boundary').first()
        if airspace and airspace.geom is not None:
            # Convert WKBElement to Shapely geometry
            geom = to_shape(airspace.geom)
            # Prepare for fast spatial predicates
            CACHED_RDC_BOUNDARY_GEOM = prep(geom)
            return CACHED_RDC_BOUNDARY_GEOM
    except Exception as e:
        print(f"[FlightTracker] Failed to load boundary from DB: {e}")

    # Fallback to hardcoded boundary
    try:
        geom = shape(RDC_BOUNDARY['geometry'])
        CACHED_RDC_BOUNDARY_GEOM = prep(geom)
        return CACHED_RDC_BOUNDARY_GEOM
    except Exception as e:
        print(f"[FlightTracker] Failed to load hardcoded boundary: {e}")
        return None


def is_point_in_rdc(lat, lon):
    """
    Check if point is in RDC using cached geometry (Shapely prepared).
    """
    geom = get_rdc_boundary_geom()
    if geom is None:
        return False

    point = Point(lon, lat)
    return geom.contains(point)


def get_active_flights(use_external_api=True):
    """
    Get active flights from external API (AviationStack/ADSBexchange) or database.

    Check system status first.
    
    Strategy:
    1. Try external API first (if configured)
    2. Fallback to database + simulation if API fails or not configured
    
    Args:
        use_external_api: Whether to attempt external API fetch first
        
    Returns:
        List of flight dictionaries with position data
    """
    # Check system status
    config = SystemConfig.query.filter_by(key='system_active').first()
    if config and config.get_typed_value() is False:
        return []

    result = []
    
    # Try external API first (AviationStack → ADSBexchange fallback)
    if use_external_api:
        try:
            external_flights = fetch_external_flight_data()
            if external_flights:
                for flight_data in external_flights:
                    lat = flight_data.get('latitude')
                    lon = flight_data.get('longitude')
                    in_rdc = is_point_in_rdc(lat, lon) if lat and lon else False
                    
                    alt = flight_data.get('altitude') or 0
                    status = 'on_ground' if flight_data.get('on_ground') else 'in_flight'
                    if alt > 0 and alt < 10000 and not flight_data.get('on_ground'):
                        status = 'approaching'
                    
                    status_color = 'green'
                    if status == 'approaching':
                        status_color = 'yellow'
                    elif status == 'on_ground':
                        status_color = 'blue'
                    
                    result.append({
                        'id': hash(flight_data.get('icao24', flight_data.get('callsign', ''))),
                        'callsign': flight_data.get('callsign') or flight_data.get('icao24', 'UNKNOWN'),
                        'flight_number': flight_data.get('flight_number') or flight_data.get('callsign'),
                        'latitude': lat,
                        'longitude': lon,
                        'altitude': alt,
                        'heading': flight_data.get('heading') or 0,
                        'ground_speed': flight_data.get('ground_speed') or 0,
                        'vertical_speed': flight_data.get('vertical_speed') or 0,
                        'status': status,
                        'status_color': status_color,
                        'in_rdc': in_rdc,
                        'departure': flight_data.get('departure_icao'),
                        'arrival': flight_data.get('arrival_icao'),
                        'departure_details': {
                            'icao': flight_data.get('departure_icao'),
                            'terminal': flight_data.get('departure_terminal'),
                            'gate': flight_data.get('departure_gate'),
                            'timezone': flight_data.get('departure_timezone')
                        },
                        'arrival_details': {
                            'icao': flight_data.get('arrival_icao'),
                            'terminal': flight_data.get('arrival_terminal'),
                            'gate': flight_data.get('arrival_gate'),
                            'baggage': flight_data.get('arrival_baggage'),
                            'timezone': flight_data.get('arrival_timezone')
                        },
                        'codeshare': {
                            'airline': flight_data.get('codeshared_airline_name'),
                            'flight_number': flight_data.get('codeshared_flight_number')
                        },
                        'squawk': flight_data.get('squawk'),
                        'aircraft': {
                            'registration': flight_data.get('registration'),
                            'model': flight_data.get('aircraft_type_iata') or flight_data.get('aircraft_type_icao'),
                            'type': flight_data.get('aircraft_type_icao') or flight_data.get('aircraft_type_iata'),
                            'operator': flight_data.get('airline_name') or flight_data.get('airline_iata'),
                            'airline_iata': flight_data.get('airline_iata')
                        }
                    })
                
                if result:
                    return result
        except Exception as e:
            print(f"[FlightTracker] External API error, falling back to simulation: {e}")
    
    # Fallback: Use database flights with simulation
    flights = Flight.query.filter(
        Flight.flight_status.in_(['in_flight', 'approaching', 'on_ground'])
    ).all()
    
    for flight in flights:
        aircraft = flight.aircraft
        
        if flight.flight_status == 'in_flight':
            lat, lon, alt, heading, speed = simulate_flight_position(flight)
        else:
            lat = lon = alt = heading = speed = 0
            if flight.arrival_icao:
                airport = Airport.query.filter_by(icao_code=flight.arrival_icao).first()
                if airport:
                    lat = airport.latitude
                    lon = airport.longitude
        
        in_rdc = is_point_in_rdc(lat, lon) if lat and lon else False
        
        status_color = 'green'
        if flight.flight_status == 'approaching':
            status_color = 'yellow'
        elif flight.flight_status == 'on_ground':
            status_color = 'blue'
        
        result.append({
            'id': flight.id,
            'callsign': flight.callsign,
            'flight_number': flight.flight_number,
            'latitude': lat,
            'longitude': lon,
            'altitude': alt,
            'heading': heading,
            'ground_speed': speed,
            'vertical_speed': 0,
            'status': flight.flight_status,
            'status_color': status_color,
            'in_rdc': in_rdc,
            'departure': flight.departure_icao,
            'arrival': flight.arrival_icao,
            'departure_details': {
                'icao': flight.departure_icao,
                'terminal': flight.departure_terminal,
                'gate': flight.departure_gate,
                'timezone': flight.departure_timezone
            },
            'arrival_details': {
                'icao': flight.arrival_icao,
                'terminal': flight.arrival_terminal,
                'gate': flight.arrival_gate,
                'baggage': flight.arrival_baggage,
                'timezone': flight.arrival_timezone
            },
            'codeshare': {
                'airline': flight.codeshared_airline_name,
                'flight_number': flight.codeshared_flight_number
            },
            'squawk': None,
            'aircraft': {
                'registration': aircraft.registration if aircraft else None,
                'model': aircraft.model if aircraft else None,
                'type': aircraft.type_code if aircraft else None,
                'operator': aircraft.operator if aircraft else None,
                'airline_iata': None  # DB flights might not have this easily available unless stored
            } if aircraft else None
        })
    
    return result


def simulate_flight_position(flight):
    if not flight.departure_icao or not flight.arrival_icao:
        return -2.0, 20.0, 35000, 90, 450
    
    dep = Airport.query.filter_by(icao_code=flight.departure_icao).first()
    arr = Airport.query.filter_by(icao_code=flight.arrival_icao).first()
    
    if not dep or not arr:
        return -2.0, 20.0, 35000, 90, 450
    
    if flight.scheduled_departure and flight.scheduled_arrival:
        total_duration = (flight.scheduled_arrival - flight.scheduled_departure).total_seconds()
        elapsed = (datetime.utcnow() - flight.scheduled_departure).total_seconds()
        progress = min(max(elapsed / total_duration if total_duration > 0 else 0.5, 0), 1)
    else:
        progress = 0.5
    
    lat = dep.latitude + (arr.latitude - dep.latitude) * progress
    lon = dep.longitude + (arr.longitude - dep.longitude) * progress
    
    lat += random.uniform(-0.05, 0.05)
    lon += random.uniform(-0.05, 0.05)
    
    heading = calculate_heading(dep.latitude, dep.longitude, arr.latitude, arr.longitude)
    
    if progress < 0.2:
        altitude = 15000 + progress * 5 * 20000
    elif progress > 0.8:
        altitude = 35000 - (progress - 0.8) * 5 * 20000
    else:
        altitude = 35000
    
    speed = 450 + random.uniform(-20, 20)
    
    return lat, lon, altitude, heading, speed


def calculate_heading(lat1, lon1, lat2, lon2):
    lat1_rad = math.radians(lat1)
    lat2_rad = math.radians(lat2)
    delta_lon = math.radians(lon2 - lon1)
    
    x = math.sin(delta_lon) * math.cos(lat2_rad)
    y = math.cos(lat1_rad) * math.sin(lat2_rad) - math.sin(lat1_rad) * math.cos(lat2_rad) * math.cos(delta_lon)
    
    heading = math.degrees(math.atan2(x, y))
    return (heading + 360) % 360


def check_overflight_entry(flight_id, lat, lon, alt):
    if not is_point_in_rdc(lat, lon):
        return None
    
    existing = Overflight.query.filter_by(
        flight_id=flight_id,
        status='active'
    ).first()
    
    if existing:
        return existing
    
    from uuid import uuid4
    session_id = f"OVF-{datetime.now().strftime('%Y%m%d')}-{uuid4().hex[:8].upper()}"
    
    flight = Flight.query.get(flight_id)
    
    overflight = Overflight(
        session_id=session_id,
        flight_id=flight_id,
        aircraft_id=flight.aircraft_id if flight else None,
        entry_lat=lat,
        entry_lon=lon,
        entry_alt=alt,
        entry_time=datetime.utcnow(),
        status='active'
    )
    
    db.session.add(overflight)
    db.session.commit()
    
    # Notify Telegram: Entry
    try:
        TelegramService.notify_entry(flight)
    except Exception as e:
        print(f"[FlightTracker] Failed to send Telegram entry notification: {e}")

    return overflight


def check_overflight_exit(flight_id, lat, lon, alt):
    if is_point_in_rdc(lat, lon):
        return None
    
    overflight = Overflight.query.filter_by(
        flight_id=flight_id,
        status='active'
    ).first()
    
    if not overflight:
        return None
    
    overflight.exit_lat = lat
    overflight.exit_lon = lon
    overflight.exit_alt = alt
    overflight.exit_time = datetime.utcnow()
    overflight.status = 'completed'
    
    if overflight.entry_time:
        duration = (overflight.exit_time - overflight.entry_time).total_seconds() / 60
        overflight.duration_minutes = duration
    
    if overflight.entry_lat and overflight.entry_lon:
        distance = calculate_distance(
            overflight.entry_lat, overflight.entry_lon,
            overflight.exit_lat, overflight.exit_lon
        )
        overflight.distance_km = distance
    
    db.session.commit()

    # Notify billing
    from services.notification_service import NotificationService
    flight = Flight.query.get(flight_id)
    callsign = flight.callsign if flight else "Unknown"
    NotificationService.notify_billing(
        type='overflight_completed',
        title=t('notifications.overflight_completed_title', 'fr').format(callsign=callsign),
        message=t('notifications.overflight_completed_msg', 'fr').format(callsign=callsign),
        link=f"/radar/overflights"
    )
    
    # Notify Telegram: Exit
    try:
        TelegramService.notify_exit(overflight)
    except Exception as e:
        print(f"[FlightTracker] Failed to send Telegram exit notification: {e}")

    # Check if there is an active landing for this flight.
    # If YES, we wait for landing to complete.
    # If NO, we trigger invoice immediately.
    active_landing = Landing.query.filter(
        Landing.flight_id == flight_id,
        Landing.status != 'completed'
    ).first()

    if not active_landing:
        trigger_auto_invoice(flight_id)

    return overflight


@lru_cache(maxsize=32)
def _get_tariff_config(code):
    tariff = TariffConfig.query.filter_by(code=code).first()
    return tariff.value if tariff else None


def get_tariff_value(code, default=0.0):
    """Get tariff value from DB or return default"""
    try:
        val = _get_tariff_config(code)
        return val if val is not None else default
    except:
        return default


def _fetch_rdc_airports_from_db():
    """Fetch RDC airports as a list of dicts to be cache-friendly"""
    airports = Airport.query.filter_by(country='RDC').all()
    return [{
        'latitude': a.latitude,
        'longitude': a.longitude,
        'elevation_ft': a.elevation_ft,
        'icao_code': a.icao_code,
        'name': a.name
    } for a in airports]


@lru_cache(maxsize=1)
def get_cached_rdc_airports():
    """Cached version of RDC airports fetch"""
    return _fetch_rdc_airports_from_db()


def check_landing_events(flight_id, lat, lon, alt, speed, active_landing=None, skip_db_lookup=False):
    """
    Check for landing and parking events
    """
    flight = Flight.query.get(flight_id)
    if not flight:
        return None

    # Get RDC airports (cached)
    airports = get_cached_rdc_airports()

    nearest_airport = None
    min_dist = float('inf')

    for airport in airports:
        dist = calculate_distance(lat, lon, airport['latitude'], airport['longitude'])
        if dist < min_dist:
            min_dist = dist
            nearest_airport = airport

    if not nearest_airport or min_dist > 50: # Check within 50km
        return None

    # Check for active landing session (not completed)
    if skip_db_lookup:
        landing = active_landing
    else:
        landing = Landing.query.filter(
            Landing.flight_id == flight_id,
            Landing.status != 'completed'
        ).order_by(Landing.created_at.desc()).first()

    # Airport elevation in meters (approx)
    airport_elev_m = (nearest_airport.get('elevation_ft') or 0) * 0.3048
    alt_agl = (alt or 0) * 0.3048 - airport_elev_m # Altitude Above Ground Level (meters)
    speed_knots = speed or 0

    current_time = datetime.utcnow()

    # Create new landing session if approaching
    if not landing:
        # If within 20km and altitude < 3000m (approx 10000ft) -> Approaching
        if min_dist < 20 and alt_agl < 3000:
            landing = Landing(
                flight_id=flight_id,
                aircraft_id=flight.aircraft_id,
                airline_id=flight.airline_id,
                callsign=flight.callsign,
                registration=flight.aircraft.registration if flight.aircraft else None,
                airport_icao=nearest_airport['icao_code'],
                airport_name=nearest_airport['name'],
                approach_time=current_time,
                status='approach',
                is_domestic=flight.is_domestic
            )
            db.session.add(landing)
            db.session.commit()
            return landing

    else:
        # Update existing landing session

        # State: approach -> landed (Touchdown)
        # Logic: Low altitude (< 100m) and low speed (< 150 kts) near airport (< 5km)
        if landing.status == 'approach':
            if min_dist < 5 and alt_agl < 100 and speed_knots < 180:
                landing.status = 'landed'
                landing.touchdown_time = current_time
                landing.landing_fee = get_tariff_value('LANDING_BASE', 150.0)

                # Close any active overflight for this flight as it has landed
                active_overflight = Overflight.query.filter_by(
                    flight_id=flight_id,
                    status='active'
                ).first()

                if active_overflight:
                    active_overflight.exit_lat = lat
                    active_overflight.exit_lon = lon
                    active_overflight.exit_alt = alt
                    active_overflight.exit_time = current_time
                    active_overflight.status = 'completed'

                    if active_overflight.entry_time:
                         duration = (active_overflight.exit_time - active_overflight.entry_time).total_seconds() / 60
                         active_overflight.duration_minutes = duration

                db.session.commit()

                from services.notification_service import NotificationService
                NotificationService.notify_billing(
                    type='flight_landed',
                    title=t('notifications.landing_title', 'fr').format(callsign=landing.callsign),
                    message=t('notifications.landing_msg', 'fr').format(airport=landing.airport_icao),
                    link=f"/radar/terminal"
                )
                return landing

        # State: landed -> parking (Taxi/Parking)
        # Logic: Speed < 5 knots
        elif landing.status == 'landed':
            if speed_knots < 5:
                landing.status = 'parking'
                landing.parking_start = current_time
                db.session.commit()
                return landing

        # State: parking -> completed (Pushback/Departure)
        # Logic: Speed > 10 knots (started moving again) OR left airport area
        elif landing.status == 'parking':
            if speed_knots > 10 or min_dist > 5:
                landing.status = 'completed'
                landing.parking_end = current_time

                if landing.parking_start:
                    duration = (landing.parking_end - landing.parking_start).total_seconds() / 60
                    landing.parking_duration_minutes = duration

                    # Calculate fee (1 hour free, then X$/h)
                    billable_hours = max(0, (duration - 60) / 60)
                    rate = get_tariff_value('PARKING_HOUR', 25.0)
                    landing.parking_fee = billable_hours * rate

                landing.total_fee = (landing.landing_fee or 0) + (landing.parking_fee or 0)
                db.session.commit()

                from services.notification_service import NotificationService
                NotificationService.notify_billing(
                    type='parking_completed',
                    title=t('notifications.parking_completed_title', 'fr').format(callsign=landing.callsign),
                    message=t('notifications.parking_completed_msg', 'fr').format(airport=landing.airport_icao, duration=int(landing.parking_duration_minutes or 0)),
                    link=f"/radar/terminal"
                )

                # Trigger automatic invoice generation
                trigger_auto_invoice(flight_id)

                return landing

    return None


def calculate_distance(lat1, lon1, lat2, lon2):
    R = 6371
    
    lat1_rad = math.radians(lat1)
    lat2_rad = math.radians(lat2)
    delta_lat = math.radians(lat2 - lat1)
    delta_lon = math.radians(lon2 - lon1)
    
    a = math.sin(delta_lat/2)**2 + math.cos(lat1_rad) * math.cos(lat2_rad) * math.sin(delta_lon/2)**2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))
    
    return R * c


def get_weather_tile_url(layer: str = 'clouds_new') -> str:
    """
    Get weather overlay tile URL for Leaflet map
    Available layers: clouds_new, precipitation_new, pressure_new, wind_new, temp_new
    """
    return openweathermap.get_weather_tile_url(layer)


def get_airport_metar(icao_code: str) -> dict:
    """Get METAR data for an airport"""
    return aviationweather.get_metar(icao_code) or {}


def get_airport_weather(icao_code: str) -> dict:
    """Get weather conditions for an airport"""
    airport = Airport.query.filter_by(icao_code=icao_code).first()
    if airport:
        return openweathermap.get_weather_at_point(airport.latitude, airport.longitude) or {}
    return {}


def check_rdc_airspace(lat: float, lon: float, boundary: dict = None) -> bool:
    """Check if a point is within RDC airspace"""
    return is_point_in_rdc(lat, lon)
