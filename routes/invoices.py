from flask import Blueprint, render_template, jsonify, request, send_file, flash, redirect, url_for
from flask_login import login_required, current_user
from datetime import datetime, date
import os

from models import db, Invoice, Airline, Overflight, Landing, TariffConfig, AuditLog
from services.invoice_generator import generate_invoice_pdf, calculate_invoice_amounts
from utils.decorators import role_required
from services.translation_service import t

invoices_bp = Blueprint('invoices', __name__)


@invoices_bp.route('/')
@login_required
@role_required(['superadmin', 'billing', 'supervisor'])
def index():
    page = request.args.get('page', 1, type=int)
    status = request.args.get('status', '')
    
    query = Invoice.query
    
    if status:
        query = query.filter_by(status=status)
    
    invoices = query.order_by(Invoice.created_at.desc()).paginate(
        page=page, per_page=20, error_out=False
    )
    
    pending_count = Invoice.query.filter_by(status='draft').count()
    sent_count = Invoice.query.filter_by(status='sent').count()
    paid_count = Invoice.query.filter_by(status='paid').count()
    
    return render_template('invoices/index.html', 
                          invoices=invoices,
                          status=status,
                          pending_count=pending_count,
                          sent_count=sent_count,
                          paid_count=paid_count)


@invoices_bp.route('/create', methods=['GET', 'POST'])
@login_required
@role_required(['superadmin', 'billing'])
def create():
    if request.method == 'POST':
        airline_id = request.form.get('airline_id', type=int)
        invoice_type = request.form.get('invoice_type')
        overflight_ids = request.form.getlist('overflights')
        landing_ids = request.form.getlist('landings')
        
        if not airline_id:
            flash(t('invoices.select_airline'), 'error')
            return redirect(url_for('invoices.create'))
        
        invoice_number = f"RVA-{datetime.now().strftime('%Y%m%d')}-{Invoice.query.count() + 1:04d}"
        
        amounts = calculate_invoice_amounts(overflight_ids, landing_ids)
        
        invoice = Invoice(
            invoice_number=invoice_number,
            airline_id=airline_id,
            invoice_type=invoice_type,
            subtotal=amounts['subtotal'],
            tax_amount=amounts['tax'],
            total_amount=amounts['total'],
            status='draft',
            due_date=date.today(),
            created_by=current_user.id
        )
        
        db.session.add(invoice)
        db.session.flush()
        
        for ovf_id in overflight_ids:
            ovf = Overflight.query.get(ovf_id)
            if ovf:
                ovf.invoice_id = invoice.id
                ovf.is_billed = True
        
        for land_id in landing_ids:
            land = Landing.query.get(land_id)
            if land:
                land.invoice_id = invoice.id
                land.is_billed = True
        
        log = AuditLog(
            user_id=current_user.id,
            action='create_invoice',
            entity_type='invoice',
            entity_id=invoice.id,
            ip_address=request.remote_addr
        )
        db.session.add(log)
        db.session.commit()
        
        flash(t('invoices.created_success').format(number=invoice_number), 'success')
        return redirect(url_for('invoices.detail', invoice_id=invoice.id))
    
    airlines = Airline.query.filter_by(is_active=True).all()
    unbilled_overflights = Overflight.query.filter_by(is_billed=False, status='completed').all()
    unbilled_landings = Landing.query.filter_by(is_billed=False).all()
    
    return render_template('invoices/create.html',
                          airlines=airlines,
                          overflights=unbilled_overflights,
                          landings=unbilled_landings)


@invoices_bp.route('/<int:invoice_id>')
@login_required
@role_required(['superadmin', 'billing', 'supervisor', 'auditor'])
def detail(invoice_id):
    invoice = Invoice.query.get_or_404(invoice_id)
    return render_template('invoices/detail.html', invoice=invoice)


@invoices_bp.route('/<int:invoice_id>/pdf')
@login_required
@role_required(['superadmin', 'billing', 'supervisor'])
def download_pdf(invoice_id):
    invoice = Invoice.query.get_or_404(invoice_id)
    
    pdf_path = generate_invoice_pdf(invoice)
    
    if pdf_path and os.path.exists(pdf_path):
        return send_file(pdf_path, as_attachment=True, download_name=f'{invoice.invoice_number}.pdf')
    
    flash(t('invoices.pdf_error'), 'error')
    return redirect(url_for('invoices.detail', invoice_id=invoice_id))


@invoices_bp.route('/<int:invoice_id>/send', methods=['POST'])
@login_required
@role_required(['superadmin', 'billing'])
def send_invoice(invoice_id):
    invoice = Invoice.query.get_or_404(invoice_id)
    invoice.status = 'sent'
    
    log = AuditLog(
        user_id=current_user.id,
        action='send_invoice',
        entity_type='invoice',
        entity_id=invoice.id,
        ip_address=request.remote_addr
    )
    db.session.add(log)
    db.session.commit()
    
    flash(t('invoices.marked_sent').format(number=invoice.invoice_number), 'success')
    return redirect(url_for('invoices.detail', invoice_id=invoice_id))


@invoices_bp.route('/<int:invoice_id>/mark-paid', methods=['POST'])
@login_required
@role_required(['superadmin', 'billing'])
def mark_paid(invoice_id):
    invoice = Invoice.query.get_or_404(invoice_id)
    invoice.status = 'paid'
    invoice.paid_date = date.today()
    
    log = AuditLog(
        user_id=current_user.id,
        action='mark_invoice_paid',
        entity_type='invoice',
        entity_id=invoice.id,
        ip_address=request.remote_addr
    )
    db.session.add(log)
    db.session.commit()
    
    flash(t('invoices.marked_paid').format(number=invoice.invoice_number), 'success')
    return redirect(url_for('invoices.detail', invoice_id=invoice_id))


@invoices_bp.route('/tariffs')
@login_required
@role_required(['superadmin', 'billing'])
def tariffs():
    tariffs = TariffConfig.query.filter_by(is_active=True).all()
    return render_template('invoices/tariffs.html', tariffs=tariffs)


@invoices_bp.route('/tariffs/<int:tariff_id>/update', methods=['POST'])
@login_required
@role_required(['superadmin'])
def update_tariff(tariff_id):
    tariff = TariffConfig.query.get_or_404(tariff_id)
    old_value = tariff.value
    
    new_value = request.form.get('value', type=float)
    if new_value is not None:
        tariff.value = new_value
        tariff.updated_by = current_user.id
        
        log = AuditLog(
            user_id=current_user.id,
            action='update_tariff',
            entity_type='tariff',
            entity_id=tariff.id,
            old_value=str(old_value),
            new_value=str(new_value),
            ip_address=request.remote_addr
        )
        db.session.add(log)
        db.session.commit()
        
        flash(t('invoices.tariff_updated').format(name=tariff.name), 'success')
    
    return redirect(url_for('invoices.tariffs'))


@invoices_bp.route('/generate/overflight/<int:overflight_id>', methods=['POST'])
@login_required
@role_required(['superadmin', 'billing'])
def generate_overflight_invoice(overflight_id):
    """Generate invoice for a specific overflight"""
    ovf = Overflight.query.get_or_404(overflight_id)
    
    if ovf.is_billed:
        return jsonify({'success': False, 'error': t('invoices.already_billed')})
    
    def get_tariff(name, default):
        tariff = TariffConfig.query.filter_by(name=name, is_active=True).first()
        return tariff.value if tariff else default
    
    survol_par_km = get_tariff('survol_par_km', 0.85)
    tonnage_par_tonne = get_tariff('tonnage_par_tonne', 2.50)
    surtaxe_nuit_pct = get_tariff('surtaxe_nuit_pct', 0.25)
    tva_pct = get_tariff('tva_pct', 0.16)
    heure_debut_nuit = get_tariff('heure_debut_nuit', 18)
    heure_fin_nuit = get_tariff('heure_fin_nuit', 6)
    
    distance_km = ovf.distance_km or 0
    overflight_charge = distance_km * survol_par_km
    
    mtow = 0
    if ovf.aircraft:
        mtow = ovf.aircraft.mtow or 0
    tonnage_charge = mtow * tonnage_par_tonne
    
    subtotal = overflight_charge + tonnage_charge
    
    is_night = False
    if ovf.entry_time:
        hour = ovf.entry_time.hour
        if hour >= heure_debut_nuit or hour < heure_fin_nuit:
            is_night = True
            subtotal *= (1 + surtaxe_nuit_pct)
    
    tax = subtotal * tva_pct
    total = subtotal + tax
    
    airline_id = None
    if ovf.aircraft and ovf.aircraft.operator_iata:
        airline = Airline.query.filter_by(iata_code=ovf.aircraft.operator_iata).first()
        if airline:
            airline_id = airline.id
    
    invoice_number = f"RVA-OVF-{datetime.now().strftime('%Y%m%d')}-{Invoice.query.count() + 1:04d}"
    
    invoice = Invoice(
        invoice_number=invoice_number,
        airline_id=airline_id,
        invoice_type='overflight',
        subtotal=subtotal,
        tax_amount=tax,
        total_amount=total,
        status='draft',
        due_date=date.today(),
        notes=f"Survol: {ovf.session_id}, Distance: {distance_km:.1f} km, MTOW: {mtow} tonnes",
        created_by=current_user.id
    )
    
    db.session.add(invoice)
    db.session.flush()
    
    ovf.invoice_id = invoice.id
    ovf.is_billed = True
    
    log = AuditLog(
        user_id=current_user.id,
        action='generate_overflight_invoice',
        entity_type='invoice',
        entity_id=invoice.id,
        ip_address=request.remote_addr
    )
    db.session.add(log)
    db.session.commit()
    
    return jsonify({
        'success': True,
        'invoice_number': invoice_number,
        'invoice_id': invoice.id,
        'total': float(total)
    })
