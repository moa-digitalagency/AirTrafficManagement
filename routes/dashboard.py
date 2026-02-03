"""
/* * Nom de l'application : ATM-RDC
 * Description : Source file: dashboard.py
 * Produit de : MOA Digital Agency, www.myoneart.com
 * Fait par : Aisance KALONJI, www.aisancekalonji.com
 * Auditer par : La CyberConfiance, www.cyberconfiance.com
 */
"""
from flask import Blueprint, render_template, jsonify
from flask_login import login_required, current_user
from datetime import datetime, timedelta
from sqlalchemy import func

from models import db, Flight, Overflight, Landing, Invoice, Alert, Aircraft, Airport

dashboard_bp = Blueprint('dashboard', __name__)


@dashboard_bp.route('/')
@login_required
def index():
    today = datetime.utcnow().date()
    start_of_day = datetime.combine(today, datetime.min.time())
    
    stats = {
        'active_flights': Flight.query.filter(Flight.flight_status.in_(['in_flight', 'approaching'])).count(),
        'flights_today': Flight.query.filter(Flight.scheduled_departure >= start_of_day).count(),
        'overflights_today': Overflight.query.filter(Overflight.entry_time >= start_of_day).count(),
        'landings_today': Landing.query.filter(Landing.touchdown_time >= start_of_day).count(),
        'pending_invoices': Invoice.query.filter_by(status='draft').count(),
        'unread_alerts': Alert.query.filter_by(is_acknowledged=False).count(),
    }
    
    recent_alerts = Alert.query.filter_by(is_acknowledged=False).order_by(Alert.created_at.desc()).limit(5).all()
    
    recent_flights = Flight.query.filter(
        Flight.flight_status.in_(['in_flight', 'approaching', 'scheduled'])
    ).order_by(Flight.scheduled_departure.desc()).limit(10).all()
    
    return render_template('dashboard/index.html', 
                          stats=stats, 
                          recent_alerts=recent_alerts,
                          recent_flights=recent_flights)


@dashboard_bp.route('/stats')
@login_required
def get_stats():
    today = datetime.utcnow().date()
    week_ago = today - timedelta(days=7)
    
    daily_flights = db.session.query(
        func.date(Flight.scheduled_departure).label('date'),
        func.count(Flight.id).label('count')
    ).filter(
        Flight.scheduled_departure >= week_ago
    ).group_by(func.date(Flight.scheduled_departure)).all()
    
    flights_by_type = db.session.query(
        Flight.flight_type,
        func.count(Flight.id).label('count')
    ).group_by(Flight.flight_type).all()
    
    return jsonify({
        'daily_flights': [{'date': str(d.date), 'count': d.count} for d in daily_flights],
        'flights_by_type': [{'type': f.flight_type or 'unknown', 'count': f.count} for f in flights_by_type]
    })
