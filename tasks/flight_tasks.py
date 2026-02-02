"""
Flight-related Celery tasks for ATM-RDC
Handles asynchronous flight position fetching and overflight detection
"""
import os
from datetime import datetime
from celery_app import celery


@celery.task(bind=True, max_retries=3)
def fetch_flight_positions(self):
    """
    Fetch real-time flight positions from external API
    This task runs every 5 seconds via Celery Beat
    """
    try:
        from app import app
        from models import db, Flight, FlightPosition
        from services.api_client import fetch_external_flight_data
        
        with app.app_context():
            flights_data = fetch_external_flight_data()
            
            for flight_data in flights_data:
                flight = Flight.query.filter_by(
                    callsign=flight_data.get('callsign')
                ).first()
                
                if flight:
                    lat = flight_data.get('latitude')
                    lon = flight_data.get('longitude')

                    position = FlightPosition(
                        flight_id=flight.id,
                        latitude=lat,
                        longitude=lon,
                        altitude=flight_data.get('altitude'),
                        heading=flight_data.get('heading'),
                        ground_speed=flight_data.get('ground_speed'),
                        timestamp=datetime.utcnow(),
                        geom=f'POINT({lon} {lat})' if lat is not None and lon is not None else None
                    )
                    db.session.add(position)
                    
                    flight.current_latitude = flight_data.get('latitude')
                    flight.current_longitude = flight_data.get('longitude')
                    flight.current_altitude = flight_data.get('altitude')
                    flight.current_heading = flight_data.get('heading')
                    flight.current_speed = flight_data.get('ground_speed')
                    flight.last_position_update = datetime.utcnow()
            
            db.session.commit()
            return {'status': 'success', 'positions_updated': len(flights_data)}
            
    except Exception as exc:
        self.retry(exc=exc, countdown=5)


@celery.task(bind=True, max_retries=3)
def check_airspace_entries(self):
    """
    Check for aircraft entering or exiting RDC airspace
    Uses Shapely for geofencing calculations
    """
    try:
        from app import app
        from models import db, Flight, Overflight
        from services.flight_tracker import is_point_in_rdc, get_rdc_boundary
        
        with app.app_context():
            active_flights = Flight.query.filter(
                Flight.flight_status.in_(['in_flight', 'approaching'])
            ).all()
            
            entries = []
            exits = []
            
            for flight in active_flights:
                if not flight.current_latitude or not flight.current_longitude:
                    continue
                
                is_in_rdc = is_point_in_rdc(
                    flight.current_latitude, 
                    flight.current_longitude
                )
                
                existing_overflight = Overflight.query.filter_by(
                    flight_id=flight.id,
                    status='active'
                ).first()
                
                if is_in_rdc and not existing_overflight:
                    from uuid import uuid4
                    session_id = f"OVF-{datetime.now().strftime('%Y%m%d')}-{uuid4().hex[:8].upper()}"
                    
                    overflight = Overflight(
                        session_id=session_id,
                        flight_id=flight.id,
                        aircraft_id=flight.aircraft_id,
                        entry_lat=flight.current_latitude,
                        entry_lon=flight.current_longitude,
                        entry_alt=flight.current_altitude,
                        entry_time=datetime.utcnow(),
                        status='active'
                    )
                    db.session.add(overflight)
                    entries.append(flight.callsign)
                    
                elif not is_in_rdc and existing_overflight:
                    existing_overflight.exit_lat = flight.current_latitude
                    existing_overflight.exit_lon = flight.current_longitude
                    existing_overflight.exit_alt = flight.current_altitude
                    existing_overflight.exit_time = datetime.utcnow()
                    existing_overflight.status = 'completed'
                    
                    if existing_overflight.entry_time:
                        duration = (existing_overflight.exit_time - existing_overflight.entry_time).total_seconds() / 60
                        existing_overflight.duration_minutes = duration
                    
                    exits.append(flight.callsign)
            
            db.session.commit()
            return {
                'status': 'success',
                'entries': entries,
                'exits': exits
            }
            
    except Exception as exc:
        self.retry(exc=exc, countdown=10)


@celery.task
def process_flight_data(flight_data: dict):
    """
    Process incoming flight data from external API
    """
    from app import app
    from models import db, Flight
    
    with app.app_context():
        flight = Flight.query.filter_by(callsign=flight_data.get('callsign')).first()
        
        if flight:
            flight.current_latitude = flight_data.get('latitude')
            flight.current_longitude = flight_data.get('longitude')
            flight.current_altitude = flight_data.get('altitude')
            flight.current_heading = flight_data.get('heading')
            flight.current_speed = flight_data.get('speed')
            flight.last_position_update = datetime.utcnow()
            db.session.commit()
            
        return {'status': 'updated', 'callsign': flight_data.get('callsign')}


@celery.task(bind=True, max_retries=3)
def check_airport_movements(self):
    """
    Check for aircraft landings and parking at RDC airports
    """
    try:
        from app import app
        from models import db, Flight
        from services.flight_tracker import check_landing_events

        with app.app_context():
            # Check flights that are approaching or on ground
            # We also include in_flight just in case they are descending near an airport
            active_flights = Flight.query.filter(
                Flight.flight_status.in_(['in_flight', 'approaching', 'on_ground'])
            ).all()

            movements = []

            for flight in active_flights:
                if flight.current_latitude is None or flight.current_longitude is None:
                    continue

                landing = check_landing_events(
                    flight.id,
                    flight.current_latitude,
                    flight.current_longitude,
                    flight.current_altitude,
                    flight.current_speed
                )

                if landing:
                    # Update flight status based on landing status
                    if landing.status == 'approach':
                        flight.flight_status = 'approaching'
                    elif landing.status in ['landed', 'parking']:
                         flight.flight_status = 'on_ground'
                    elif landing.status == 'completed':
                         flight.flight_status = 'in_flight'

                    movements.append({
                        'callsign': flight.callsign,
                        'status': landing.status,
                        'airport': landing.airport_icao
                    })

            db.session.commit()
            return {
                'status': 'success',
                'movements': movements
            }

    except Exception as exc:
        self.retry(exc=exc, countdown=10)
