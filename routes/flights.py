from flask import Blueprint, render_template, jsonify, request
from flask_login import login_required, current_user
from datetime import datetime, timedelta

from models import db, Flight, Aircraft, Airport, FlightPosition, Overflight, Landing

flights_bp = Blueprint('flights', __name__)


@flights_bp.route('/')
@login_required
def index():
    page = request.args.get('page', 1, type=int)
    status = request.args.get('status', '')
    search = request.args.get('search', '')
    
    query = Flight.query
    
    if status:
        query = query.filter_by(flight_status=status)
    
    if search:
        query = query.filter(
            db.or_(
                Flight.callsign.ilike(f'%{search}%'),
                Flight.flight_number.ilike(f'%{search}%')
            )
        )
    
    flights = query.order_by(Flight.scheduled_departure.desc()).paginate(
        page=page, per_page=20, error_out=False
    )
    
    return render_template('flights/index.html', flights=flights, status=status, search=search)


@flights_bp.route('/<int:flight_id>')
@login_required
def detail(flight_id):
    flight = Flight.query.get_or_404(flight_id)
    positions = FlightPosition.query.filter_by(flight_id=flight_id).order_by(FlightPosition.timestamp.desc()).limit(100).all()
    overflights = Overflight.query.filter_by(flight_id=flight_id).all()
    landings = Landing.query.filter_by(flight_id=flight_id).all()
    
    return render_template('flights/detail.html', 
                          flight=flight, 
                          positions=positions,
                          overflights=overflights,
                          landings=landings)


@flights_bp.route('/history')
@login_required
def history():
    start_date = request.args.get('start_date', (datetime.utcnow() - timedelta(days=7)).strftime('%Y-%m-%d'))
    end_date = request.args.get('end_date', datetime.utcnow().strftime('%Y-%m-%d'))
    
    flights = Flight.query.filter(
        Flight.scheduled_departure >= start_date,
        Flight.scheduled_departure <= end_date + ' 23:59:59'
    ).order_by(Flight.scheduled_departure.desc()).all()
    
    return render_template('flights/history.html', 
                          flights=flights,
                          start_date=start_date,
                          end_date=end_date)


@flights_bp.route('/api/search')
@login_required
def api_search():
    q = request.args.get('q', '')
    if len(q) < 2:
        return jsonify([])
    
    flights = Flight.query.filter(
        db.or_(
            Flight.callsign.ilike(f'%{q}%'),
            Flight.flight_number.ilike(f'%{q}%')
        )
    ).limit(10).all()
    
    return jsonify([f.to_dict() for f in flights])
