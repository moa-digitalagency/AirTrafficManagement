"""
/* * Nom de l'application : ATM-RDC
 * Description : Source file: api_external.py
 * Produit de : MOA Digital Agency, www.myoneart.com
 * Fait par : Aisance KALONJI, www.aisancekalonji.com
 * Auditer par : La CyberConfiance, www.cyberconfiance.com
 */
"""
from flask import Blueprint, jsonify, request
from sqlalchemy import func
from datetime import datetime, date
from models import db, Flight, Overflight, Landing, Alert, Invoice, TariffConfig
from security.api_auth import require_api_key

api_external_bp = Blueprint('api_external', __name__)

@api_external_bp.route('/surveillance/flights', methods=['GET'])
@require_api_key
def get_flights():
    active_param = request.args.get('active', '').lower()
    date_param = request.args.get('date')

    query = Flight.query

    # Filter by Status/Active
    if active_param == 'true':
        # Active flights are usually "in_flight", "approaching", or "active" in overflight/landing
        query = query.filter(Flight.flight_status.in_(['in_flight', 'approaching']))

    # Filter by Date
    if date_param:
        try:
            query_date = datetime.strptime(date_param, '%Y-%m-%d').date()
            # Flight model has 'flight_date' column
            query = query.filter(Flight.flight_date == query_date)
        except ValueError:
            return jsonify({'error': 'Invalid date format. Use YYYY-MM-DD'}), 400

    # Limit result set for safety
    flights = query.limit(1000).all()

    results = []
    for f in flights:
        # Check relations
        # Note: Overflights and Landings are "dynamic" relationships
        ovf = f.overflights.first()
        landing = f.landings.first()

        distance_km = 0
        duration_min = 0
        ground_time_min = 0
        position_entry = None
        position_exit = None

        if ovf:
            distance_km = ovf.distance_km or 0
            duration_min = ovf.duration_minutes or 0
            position_entry = f"{ovf.entry_lat}, {ovf.entry_lon}" if ovf.entry_lat and ovf.entry_lon else None
            position_exit = f"{ovf.exit_lat}, {ovf.exit_lon}" if ovf.exit_lat and ovf.exit_lon else None

        # Fallback to Flight model data if overflight missing but data exists
        if distance_km == 0 and f.route_distance_km:
            distance_km = f.route_distance_km

        if landing:
            ground_time_min = landing.parking_duration_minutes or 0
            # If landed, exit position is airport
            if not position_exit:
                position_exit = landing.airport_icao

        alerts_count = f.alerts.count()

        results.append({
            'callsign': f.callsign,
            'aircraft': f.aircraft.registration if f.aircraft else None,
            'operator': f.airline.name if f.airline else None,
            'position_entry': position_entry,
            'position_exit': position_exit,
            'distance_km': round(distance_km, 2),
            'duration_minutes': round(duration_min, 1),
            'alerts_count': alerts_count,
            'ground_time_minutes': round(ground_time_min, 1) if ground_time_min else 0,
            'status': f.flight_status
        })

    return jsonify({
        'count': len(results),
        'data': results
    })

@api_external_bp.route('/surveillance/alerts', methods=['GET'])
@require_api_key
def get_alerts():
    alerts = Alert.query.order_by(Alert.created_at.desc()).limit(100).all()
    return jsonify({
        'data': [a.to_dict() for a in alerts]
    })

@api_external_bp.route('/billing/summary', methods=['GET'])
@require_api_key
def get_billing_summary():
    # Aggregate
    total_invoiced = db.session.query(func.sum(Invoice.total_amount)).scalar() or 0
    total_paid = db.session.query(func.sum(Invoice.paid_amount)).scalar() or 0

    return jsonify({
        'currency': 'USD',
        'total_invoiced': round(total_invoiced, 2),
        'total_paid': round(total_paid, 2),
        'outstanding': round(total_invoiced - total_paid, 2),
        'generated_at': datetime.utcnow().isoformat()
    })

@api_external_bp.route('/billing/pricing', methods=['GET'])
@require_api_key
def get_pricing():
    tariffs = TariffConfig.query.filter_by(is_active=True).all()
    return jsonify({
        'data': [t.to_dict() for t in tariffs]
    })
