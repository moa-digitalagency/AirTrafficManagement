"""
/* * Nom de l'application : ATM-RDC
 * Description : Source file: api.py
 * Produit de : MOA Digital Agency, www.myoneart.com
 * Fait par : Aisance KALONJI, www.aisancekalonji.com
 * Auditer par : La CyberConfiance, www.cyberconfiance.com
 */
"""
from flask import Blueprint, jsonify, request, Response, stream_with_context
from flask_login import login_required, current_user
from datetime import datetime, timedelta
from sqlalchemy import func
import json

from models import db, Flight, Aircraft, Airport, Airline, Overflight, Landing, Invoice, Alert, TelegramSubscriber, SystemConfig, AuditLog
from services.telegram_service import TelegramService
from utils.decorators import role_required
from utils.system_gate import SystemGate

api_bp = Blueprint('api', __name__)


@api_bp.route('/flights')
@login_required
def get_flights():
    status = request.args.get('status')
    limit = request.args.get('limit', 100, type=int)
    
    query = Flight.query
    
    if status:
        query = query.filter_by(flight_status=status)
    
    flights = query.order_by(Flight.scheduled_departure.desc()).limit(limit).all()
    return jsonify([f.to_dict() for f in flights])


@api_bp.route('/flights/<int:flight_id>')
@login_required
def get_flight(flight_id):
    flight = Flight.query.get_or_404(flight_id)
    return jsonify(flight.to_dict())


@api_bp.route('/aircraft')
@login_required
def get_aircraft():
    aircraft = Aircraft.query.all()
    return jsonify([a.to_dict() for a in aircraft])


@api_bp.route('/airports')
@login_required
def get_airports():
    domestic_only = request.args.get('domestic', 'false').lower() == 'true'
    
    query = Airport.query
    if domestic_only:
        query = query.filter_by(is_domestic=True)
    
    airports = query.all()
    return jsonify([a.to_dict() for a in airports])


@api_bp.route('/airlines')
@login_required
def get_airlines():
    airlines = Airline.query.filter_by(is_active=True).all()
    return jsonify([a.to_dict() for a in airlines])


@api_bp.route('/overflights')
@login_required
def get_overflights():
    status = request.args.get('status')
    limit = request.args.get('limit', 50, type=int)
    
    query = Overflight.query
    
    if status:
        query = query.filter_by(status=status)
    
    overflights = query.order_by(Overflight.entry_time.desc()).limit(limit).all()
    return jsonify([o.to_dict() for o in overflights])


@api_bp.route('/landings')
@login_required
def get_landings():
    airport = request.args.get('airport')
    limit = request.args.get('limit', 50, type=int)
    
    query = Landing.query
    
    if airport:
        query = query.filter_by(airport_icao=airport)
    
    landings = query.order_by(Landing.touchdown_time.desc()).limit(limit).all()
    return jsonify([l.to_dict() for l in landings])


@api_bp.route('/stats/summary')
@login_required
def get_stats_summary():
    today = datetime.utcnow().date()
    start_of_day = datetime.combine(today, datetime.min.time())
    start_of_month = today.replace(day=1)
    
    stats = {
        'today': {
            'flights': Flight.query.filter(Flight.scheduled_departure >= start_of_day).count(),
            'overflights': Overflight.query.filter(Overflight.entry_time >= start_of_day).count(),
            'landings': Landing.query.filter(Landing.touchdown_time >= start_of_day).count(),
        },
        'month': {
            'flights': Flight.query.filter(Flight.scheduled_departure >= start_of_month).count(),
            'overflights': Overflight.query.filter(Overflight.entry_time >= start_of_month).count(),
            'landings': Landing.query.filter(Landing.touchdown_time >= start_of_month).count(),
            'revenue': db.session.query(func.sum(Invoice.total_amount)).filter(
                Invoice.created_at >= start_of_month,
                Invoice.status == 'paid'
            ).scalar() or 0
        },
        'active': {
            'flights': Flight.query.filter(Flight.flight_status.in_(['in_flight', 'approaching'])).count(),
            'overflights': Overflight.query.filter_by(status='active').count(),
            'pending_invoices': Invoice.query.filter_by(status='draft').count(),
            'alerts': Alert.query.filter_by(is_acknowledged=False).count()
        }
    }
    
    return jsonify(stats)


@api_bp.route('/stats/traffic')
@login_required
def get_traffic_stats():
    days = request.args.get('days', 7, type=int)
    start_date = datetime.utcnow() - timedelta(days=days)
    
    daily_flights = db.session.query(
        func.date(Flight.scheduled_departure).label('date'),
        func.count(Flight.id).label('count')
    ).filter(
        Flight.scheduled_departure >= start_date
    ).group_by(func.date(Flight.scheduled_departure)).all()
    
    daily_overflights = db.session.query(
        func.date(Overflight.entry_time).label('date'),
        func.count(Overflight.id).label('count')
    ).filter(
        Overflight.entry_time >= start_date
    ).group_by(func.date(Overflight.entry_time)).all()
    
    return jsonify({
        'flights': [{'date': str(d.date), 'count': d.count} for d in daily_flights],
        'overflights': [{'date': str(d.date), 'count': d.count} for d in daily_overflights]
    })


@api_bp.route('/stats/airlines')
@login_required
def get_airline_stats():
    stats = db.session.query(
        Aircraft.operator,
        func.count(Flight.id).label('flight_count')
    ).join(Flight, Flight.aircraft_id == Aircraft.id).group_by(
        Aircraft.operator
    ).order_by(func.count(Flight.id).desc()).limit(10).all()
    
    return jsonify([
        {'airline': s.operator or 'Unknown', 'flights': s.flight_count}
        for s in stats
    ])


@api_bp.route('/export/overflights')
@login_required
def export_overflights():
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')
    format_type = request.args.get('format', 'json')
    
    query = Overflight.query.filter_by(status='completed')
    
    if start_date:
        query = query.filter(Overflight.entry_time >= start_date)
    if end_date:
        query = query.filter(Overflight.exit_time <= end_date + ' 23:59:59')
    
    # Use streaming response to avoid loading all results into memory
    def generate():
        yield '['
        first = True
        # Process in batches of 100
        for overflight in query.yield_per(100):
            if not first:
                yield ','
            yield json.dumps(overflight.to_dict())
            first = False
        yield ']'

    return Response(stream_with_context(generate()), mimetype='application/json')


@api_bp.route('/export/landings')
@login_required
def export_landings():
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')
    airport = request.args.get('airport')
    
    query = Landing.query
    
    if start_date:
        query = query.filter(Landing.touchdown_time >= start_date)
    if end_date:
        query = query.filter(Landing.touchdown_time <= end_date + ' 23:59:59')
    if airport:
        query = query.filter_by(airport_icao=airport)
    
    landings = query.all()
    return jsonify([l.to_dict() for l in landings])


@api_bp.route('/telegram/approve', methods=['POST'])
@login_required
@role_required(['superadmin'])
def approve_telegram_subscriber():
    data = request.get_json()
    if not data:
        return jsonify({'error': 'Invalid payload'}), 400

    user_id = data.get('userId')
    otp_code = data.get('otpCode')

    if not user_id or not otp_code:
        return jsonify({'error': 'Missing userId or otpCode'}), 400

    sub = TelegramSubscriber.query.get(user_id)
    if not sub:
        return jsonify({'error': 'Subscriber not found'}), 404

    if sub.status != 'PENDING':
        return jsonify({'error': 'Request not pending'}), 400

    # Clean OTP code (remove spaces if any)
    otp_code_clean = str(otp_code).replace(' ', '')
    stored_code_clean = str(sub.verification_code).replace(' ', '') if sub.verification_code else ''

    if stored_code_clean != otp_code_clean:
        return jsonify({'error': 'Code de vérification incorrect'}), 400

    # Approve
    sub.status = 'APPROVED'
    sub.approval_date = datetime.utcnow()
    sub.approved_by_id = current_user.id
    sub.verification_code = None # Clear code
    db.session.commit()

    # Notify user
    TelegramService.send_message(sub.telegram_chat_id, "✅ Votre accès est validé.\nTapez /settings pour configurer vos notifications.")

    return jsonify({'success': True, 'message': 'Subscriber approved'})


@api_bp.route('/system/status', methods=['GET'])
@login_required
def get_system_status():
    return jsonify({'active': SystemGate.is_active()})

@api_bp.route('/system/toggle', methods=['POST'])
@login_required
@role_required(['superadmin'])
def toggle_system_status():
    data = request.get_json()
    if not data or 'active' not in data:
        return jsonify({'error': 'Missing active status'}), 400

    new_status = bool(data['active'])

    success, message = SystemGate.set_active(new_status, user_id=current_user.id, ip_address=request.remote_addr)

    if success:
        return jsonify({'success': True, 'active': new_status})
    else:
        return jsonify({'error': message}), 500
