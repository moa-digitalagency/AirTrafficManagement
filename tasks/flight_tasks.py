"""
Flight-related Celery tasks for ATM-RDC
Handles asynchronous flight position fetching and overflight detection
"""
import os
from celery_app import celery
from datetime import datetime

@celery.task(bind=True, max_retries=3)
def fetch_flight_positions(self):
    """
    Fetch real-time flight positions from external API
    This task runs every 5 seconds via Celery Beat
    """
    try:
        from app import create_app
        from models import db, Flight, FlightPosition
        from services.flight_tracker import fetch_external_flight_data
        
        app = create_app()
        with app.app_context():
            flights_data = fetch_external_flight_data()
            
            for flight_data in flights_data:
                position = FlightPosition(
                    flight_id=flight_data.get('flight_id'),
                    latitude=flight_data.get('latitude'),
                    longitude=flight_data.get('longitude'),
                    altitude=flight_data.get('altitude'),
                    heading=flight_data.get('heading'),
                    speed=flight_data.get('speed'),
                    timestamp=datetime.utcnow()
                )
                db.session.add(position)
            
            db.session.commit()
            return {'status': 'success', 'positions_updated': len(flights_data)}
            
    except Exception as exc:
        self.retry(exc=exc, countdown=5)


@celery.task(bind=True, max_retries=3)
def check_airspace_entries(self):
    """
    Check for aircraft entering or exiting RDC airspace
    Uses PostGIS for geofencing calculations
    """
    try:
        from app import create_app
        from models import db, Flight, Overflight
        from services.flight_tracker import check_rdc_airspace, get_rdc_boundary
        
        app = create_app()
        with app.app_context():
            active_flights = Flight.query.filter(
                Flight.flight_status.in_(['in_flight', 'approaching'])
            ).all()
            
            rdc_boundary = get_rdc_boundary()
            entries = []
            exits = []
            
            for flight in active_flights:
                is_in_rdc = check_rdc_airspace(
                    flight.current_latitude, 
                    flight.current_longitude,
                    rdc_boundary
                )
                
                existing_overflight = Overflight.query.filter_by(
                    flight_id=flight.id,
                    status='active'
                ).first()
                
                if is_in_rdc and not existing_overflight:
                    overflight = Overflight(
                        flight_id=flight.id,
                        entry_point_lat=flight.current_latitude,
                        entry_point_lon=flight.current_longitude,
                        entry_time=datetime.utcnow(),
                        status='active'
                    )
                    db.session.add(overflight)
                    entries.append(flight.callsign)
                    
                elif not is_in_rdc and existing_overflight:
                    existing_overflight.exit_point_lat = flight.current_latitude
                    existing_overflight.exit_point_lon = flight.current_longitude
                    existing_overflight.exit_time = datetime.utcnow()
                    existing_overflight.status = 'completed'
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
    from app import create_app
    from models import db, Flight, Aircraft
    
    app = create_app()
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
