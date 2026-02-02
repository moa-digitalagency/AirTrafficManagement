from flask import Blueprint, render_template, jsonify, request
from flask_login import login_required, current_user
from datetime import datetime
import os

from models import db, Flight, FlightPosition, Aircraft, Airport, Overflight, Alert
from services.flight_tracker import (
    get_active_flights, get_rdc_boundary, get_weather_tile_url,
    get_airport_metar, get_airport_weather
)

radar_bp = Blueprint('radar', __name__)


@radar_bp.route('/')
@login_required
def index():
    airports = Airport.query.filter_by(is_domestic=True).all()
    airports_data = [a.to_dict() for a in airports]
    return render_template('radar/index.html', airports=airports_data)


@radar_bp.route('/overflights')
@login_required
def overflights():
    active_overflights = Overflight.query.filter_by(status='active').all()
    completed_overflights = Overflight.query.filter_by(status='completed').order_by(Overflight.exit_time.desc()).limit(50).all()
    
    return render_template('radar/overflights.html', 
                          active_overflights=active_overflights,
                          completed_overflights=completed_overflights)


@radar_bp.route('/terminal')
@login_required
def terminal():
    airports = Airport.query.filter_by(is_domestic=True).all()
    
    inbound = Flight.query.filter(
        Flight.flight_status.in_(['in_flight', 'approaching']),
        Flight.arrival_icao.in_([a.icao_code for a in airports])
    ).all()
    
    on_ground = Flight.query.filter_by(flight_status='on_ground').all()
    
    return render_template('radar/terminal.html', 
                          airports=airports,
                          inbound=inbound,
                          on_ground=on_ground)


@radar_bp.route('/api/flights')
@login_required
def api_flights():
    flights_data = get_active_flights()
    return jsonify(flights_data)


@radar_bp.route('/api/boundary')
@login_required
def api_boundary():
    boundary = get_rdc_boundary()
    return jsonify(boundary)


@radar_bp.route('/api/airports')
@login_required
def api_airports():
    airports = Airport.query.filter_by(is_domestic=True).all()
    return jsonify([a.to_dict() for a in airports])


@radar_bp.route('/api/alerts')
@login_required
def api_alerts():
    alerts = Alert.query.filter_by(is_acknowledged=False).order_by(Alert.created_at.desc()).limit(10).all()
    return jsonify([a.to_dict() for a in alerts])


@radar_bp.route('/api/alert/<int:alert_id>/acknowledge', methods=['POST'])
@login_required
def acknowledge_alert(alert_id):
    alert = Alert.query.get_or_404(alert_id)
    alert.is_acknowledged = True
    alert.acknowledged_by = current_user.id
    alert.acknowledged_at = datetime.utcnow()
    db.session.commit()
    return jsonify({'success': True})


@radar_bp.route('/api/weather/tiles')
@login_required
def api_weather_tiles():
    """Get weather tile layer URLs for map overlay"""
    api_key = os.environ.get('OPENWEATHERMAP_API_KEY', '')
    if not api_key:
        return jsonify({'configured': False, 'layers': {}})
    
    layers = {
        'clouds': get_weather_tile_url('clouds_new'),
        'precipitation': get_weather_tile_url('precipitation_new'),
        'pressure': get_weather_tile_url('pressure_new'),
        'wind': get_weather_tile_url('wind_new'),
        'temperature': get_weather_tile_url('temp_new')
    }
    return jsonify({'configured': True, 'layers': layers})


@radar_bp.route('/api/weather/airport/<icao_code>')
@login_required
def api_airport_weather(icao_code):
    """Get weather and METAR for a specific airport"""
    weather = get_airport_weather(icao_code)
    metar = get_airport_metar(icao_code)
    return jsonify({
        'icao': icao_code,
        'weather': weather,
        'metar': metar
    })


@radar_bp.route('/api/overflights/active')
@login_required
def api_active_overflights():
    """Get active overflights with trajectory data"""
    active = Overflight.query.filter_by(status='active').all()
    
    result = []
    for ovf in active:
        flight = ovf.flight
        trajectory = []
        
        if flight:
            positions = FlightPosition.query.filter_by(
                flight_id=flight.id
            ).order_by(FlightPosition.timestamp.desc()).limit(50).all()
            
            trajectory = [
                {'lat': p.latitude, 'lon': p.longitude, 'alt': p.altitude or 0}
                for p in reversed(positions)
            ]
        
        result.append({
            'id': ovf.id,
            'session_id': ovf.session_id,
            'entry_lat': ovf.entry_lat,
            'entry_lon': ovf.entry_lon,
            'entry_alt': ovf.entry_alt or 0,
            'entry_time': ovf.entry_time.isoformat() if ovf.entry_time else None,
            'exit_lat': ovf.exit_lat,
            'exit_lon': ovf.exit_lon,
            'exit_alt': ovf.exit_alt or 0,
            'current_lat': trajectory[-1]['lat'] if trajectory else ovf.entry_lat,
            'current_lon': trajectory[-1]['lon'] if trajectory else ovf.entry_lon,
            'trajectory': trajectory,
            'flight': {
                'callsign': flight.callsign if flight else None,
                'departure': flight.departure_icao if flight else None,
                'arrival': flight.arrival_icao if flight else None
            } if flight else None
        })
    
    return jsonify(result)


@radar_bp.route('/api/overflights/<int:overflight_id>/trajectory')
@login_required
def api_overflight_trajectory(overflight_id):
    """Get trajectory data for a specific overflight"""
    ovf = Overflight.query.get_or_404(overflight_id)
    
    trajectory = []
    
    if ovf.flight_id:
        positions = FlightPosition.query.filter(
            FlightPosition.flight_id == ovf.flight_id,
            FlightPosition.is_in_rdc == True
        ).order_by(FlightPosition.timestamp).all()
        
        trajectory = [
            {'lat': p.latitude, 'lon': p.longitude, 'alt': p.altitude or 0, 'time': p.timestamp.isoformat() if p.timestamp else None}
            for p in positions
        ]
    
    if ovf.trajectory_geojson:
        import json
        try:
            geojson = json.loads(ovf.trajectory_geojson)
            if geojson.get('coordinates'):
                trajectory = [
                    {'lat': coord[1], 'lon': coord[0], 'alt': coord[2] if len(coord) > 2 else 0}
                    for coord in geojson['coordinates']
                ]
        except:
            pass
    
    return jsonify({
        'id': ovf.id,
        'session_id': ovf.session_id,
        'entry_lat': ovf.entry_lat,
        'entry_lon': ovf.entry_lon,
        'entry_alt': ovf.entry_alt or 0,
        'entry_time': ovf.entry_time.isoformat() if ovf.entry_time else None,
        'exit_lat': ovf.exit_lat,
        'exit_lon': ovf.exit_lon,
        'exit_alt': ovf.exit_alt or 0,
        'exit_time': ovf.exit_time.isoformat() if ovf.exit_time else None,
        'duration_minutes': ovf.duration_minutes,
        'distance_km': ovf.distance_km,
        'trajectory': trajectory,
        'status': ovf.status
    })
