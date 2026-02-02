"""
Analytics and Business Intelligence Routes for ATM-RDC
Provides dashboards, charts, and data export capabilities
"""
from flask import Blueprint, render_template, jsonify, request, Response
from flask_login import login_required, current_user
from datetime import datetime, date, timedelta
from sqlalchemy import func, extract
import json
import csv
import io

from models import db, Flight, Overflight, Landing, Invoice, Airline, Aircraft, Airport, AuditLog
from utils.decorators import role_required

analytics_bp = Blueprint('analytics', __name__)


@analytics_bp.route('/')
@login_required
@role_required(['superadmin', 'supervisor', 'billing', 'auditor'])
def index():
    """Main analytics dashboard"""
    today = date.today()
    first_of_month = today.replace(day=1)
    first_of_year = today.replace(month=1, day=1)
    
    daily_overflights = Overflight.query.filter(
        func.date(Overflight.created_at) == today
    ).count()
    
    monthly_overflights = Overflight.query.filter(
        Overflight.created_at >= first_of_month
    ).count()
    
    daily_revenue = db.session.query(func.sum(Invoice.total_amount)).filter(
        func.date(Invoice.created_at) == today
    ).scalar() or 0
    
    monthly_revenue = db.session.query(func.sum(Invoice.total_amount)).filter(
        Invoice.created_at >= first_of_month
    ).scalar() or 0
    
    yearly_revenue = db.session.query(func.sum(Invoice.total_amount)).filter(
        Invoice.created_at >= first_of_year
    ).scalar() or 0
    
    total_flights = Flight.query.count()
    active_airlines = Airline.query.filter_by(is_active=True).count()
    pending_invoices = Invoice.query.filter_by(status='draft').count()
    
    return render_template('analytics/index.html',
                          daily_overflights=daily_overflights,
                          monthly_overflights=monthly_overflights,
                          daily_revenue=daily_revenue,
                          monthly_revenue=monthly_revenue,
                          yearly_revenue=yearly_revenue,
                          total_flights=total_flights,
                          active_airlines=active_airlines,
                          pending_invoices=pending_invoices)


@analytics_bp.route('/api/traffic/daily')
@login_required
def api_traffic_daily():
    """Get daily traffic data for charts"""
    days = request.args.get('days', 30, type=int)
    end_date = date.today()
    start_date = end_date - timedelta(days=days)
    
    result = db.session.query(
        func.date(Overflight.created_at).label('date'),
        func.count(Overflight.id).label('count')
    ).filter(
        Overflight.created_at >= start_date
    ).group_by(
        func.date(Overflight.created_at)
    ).order_by('date').all()
    
    data = [{'date': str(row.date), 'count': row.count} for row in result]
    return jsonify(data)


@analytics_bp.route('/api/traffic/monthly')
@login_required
def api_traffic_monthly():
    """Get monthly traffic data"""
    months = request.args.get('months', 12, type=int)
    
    result = db.session.query(
        extract('year', Overflight.created_at).label('year'),
        extract('month', Overflight.created_at).label('month'),
        func.count(Overflight.id).label('count'),
        func.sum(Overflight.distance_km).label('total_distance')
    ).group_by('year', 'month').order_by('year', 'month').limit(months).all()
    
    data = [
        {
            'period': f"{int(row.year)}-{int(row.month):02d}",
            'count': row.count,
            'distance': float(row.total_distance or 0)
        }
        for row in result
    ]
    return jsonify(data)


@analytics_bp.route('/api/revenue/by-airline')
@login_required
def api_revenue_by_airline():
    """Get revenue breakdown by airline"""
    result = db.session.query(
        Airline.name.label('airline'),
        Airline.iata_code.label('code'),
        func.sum(Invoice.total_amount).label('revenue'),
        func.count(Invoice.id).label('invoice_count')
    ).join(Invoice, Invoice.airline_id == Airline.id).filter(
        Invoice.status.in_(['sent', 'paid'])
    ).group_by(Airline.id).order_by(func.sum(Invoice.total_amount).desc()).limit(10).all()
    
    data = [
        {
            'airline': row.airline,
            'code': row.code,
            'revenue': float(row.revenue or 0),
            'invoices': row.invoice_count
        }
        for row in result
    ]
    return jsonify(data)


@analytics_bp.route('/api/revenue/by-type')
@login_required
def api_revenue_by_type():
    """Get revenue breakdown by invoice type"""
    result = db.session.query(
        Invoice.invoice_type.label('type'),
        func.sum(Invoice.total_amount).label('revenue'),
        func.count(Invoice.id).label('count')
    ).group_by(Invoice.invoice_type).all()
    
    data = [
        {
            'type': row.type or 'other',
            'revenue': float(row.revenue or 0),
            'count': row.count
        }
        for row in result
    ]
    return jsonify(data)


@analytics_bp.route('/api/airports/traffic')
@login_required
def api_airports_traffic():
    """Get traffic by airport"""
    arrivals = db.session.query(
        Flight.arrival_icao.label('airport'),
        func.count(Flight.id).label('count')
    ).filter(Flight.arrival_icao.isnot(None)).group_by(Flight.arrival_icao).all()
    
    departures = db.session.query(
        Flight.departure_icao.label('airport'),
        func.count(Flight.id).label('count')
    ).filter(Flight.departure_icao.isnot(None)).group_by(Flight.departure_icao).all()
    
    traffic = {}
    for row in arrivals:
        traffic[row.airport] = {'arrivals': row.count, 'departures': 0}
    for row in departures:
        if row.airport in traffic:
            traffic[row.airport]['departures'] = row.count
        else:
            traffic[row.airport] = {'arrivals': 0, 'departures': row.count}
    
    data = [
        {
            'airport': code,
            'arrivals': stats['arrivals'],
            'departures': stats['departures'],
            'total': stats['arrivals'] + stats['departures']
        }
        for code, stats in traffic.items()
    ]
    data.sort(key=lambda x: x['total'], reverse=True)
    return jsonify(data[:15])


@analytics_bp.route('/export/<format_type>')
@login_required
@role_required(['superadmin', 'billing', 'auditor'])
def export_data(format_type):
    """Export data in various formats"""
    data_type = request.args.get('type', 'overflights')
    start_date_str = request.args.get('start')
    end_date_str = request.args.get('end')
    
    start_dt = None
    end_dt = None
    if start_date_str:
        try:
            start_dt = datetime.strptime(start_date_str, '%Y-%m-%d')
        except ValueError:
            pass
    if end_date_str:
        try:
            end_dt = datetime.strptime(end_date_str, '%Y-%m-%d').replace(hour=23, minute=59, second=59)
        except ValueError:
            pass
    
    if data_type == 'overflights':
        query = Overflight.query
        if start_dt:
            query = query.filter(Overflight.created_at >= start_dt)
        if end_dt:
            query = query.filter(Overflight.created_at <= end_dt)
        records = query.order_by(Overflight.created_at.desc()).limit(1000).all()
        
        data = [ovf.to_dict() for ovf in records]
        columns = ['session_id', 'entry_time', 'exit_time', 'duration_minutes', 'distance_km', 'status', 'is_billed']
        
    elif data_type == 'invoices':
        query = Invoice.query
        if start_dt:
            query = query.filter(Invoice.created_at >= start_dt)
        if end_dt:
            query = query.filter(Invoice.created_at <= end_dt)
        records = query.order_by(Invoice.created_at.desc()).limit(1000).all()
        
        data = [inv.to_dict() for inv in records]
        columns = ['invoice_number', 'invoice_type', 'subtotal', 'tax_amount', 'total_amount', 'status', 'created_at']
        
    elif data_type == 'flights':
        query = Flight.query
        if start_dt:
            query = query.filter(Flight.created_at >= start_dt)
        if end_dt:
            query = query.filter(Flight.created_at <= end_dt)
        records = query.order_by(Flight.created_at.desc()).limit(1000).all()
        
        data = [f.to_dict() for f in records]
        columns = ['callsign', 'flight_number', 'departure_icao', 'arrival_icao', 'flight_status', 'is_domestic']
    else:
        return jsonify({'error': 'Invalid data type'}), 400
    
    if format_type == 'json':
        return Response(
            json.dumps(data, indent=2, default=str),
            mimetype='application/json',
            headers={'Content-Disposition': f'attachment; filename={data_type}_{date.today()}.json'}
        )
    
    elif format_type == 'csv':
        output = io.StringIO()
        writer = csv.DictWriter(output, fieldnames=columns, extrasaction='ignore')
        writer.writeheader()
        for row in data:
            writer.writerow(row)
        
        return Response(
            output.getvalue(),
            mimetype='text/csv',
            headers={'Content-Disposition': f'attachment; filename={data_type}_{date.today()}.csv'}
        )
    
    else:
        return jsonify({'error': 'Unsupported format'}), 400


@analytics_bp.route('/reports')
@login_required
@role_required(['superadmin', 'billing', 'auditor'])
def reports():
    """Custom reports page"""
    return render_template('analytics/reports.html')


@analytics_bp.route('/audit')
@login_required
@role_required(['superadmin', 'auditor'])
def audit_logs():
    """Audit log viewer"""
    page = request.args.get('page', 1, type=int)
    action = request.args.get('action', '')
    
    query = AuditLog.query
    if action:
        query = query.filter_by(action=action)
    
    logs = query.order_by(AuditLog.created_at.desc()).paginate(
        page=page, per_page=50, error_out=False
    )
    
    actions = db.session.query(AuditLog.action).distinct().all()
    
    return render_template('analytics/audit.html', 
                          logs=logs,
                          action=action,
                          actions=[a[0] for a in actions])
