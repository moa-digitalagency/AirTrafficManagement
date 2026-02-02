from flask import Blueprint, render_template, jsonify, request
from flask_login import login_required, current_user
from datetime import datetime

from models import db, Flight, FlightPosition, Aircraft, Airport, Overflight, Alert
from services.flight_tracker import get_active_flights, get_rdc_boundary

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
