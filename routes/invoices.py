"""
/* * Nom de l'application : ATM-RDC
 * Description : Source file: invoices.py
 * Produit de : MOA Digital Agency, www.myoneart.com
 * Fait par : Aisance KALONJI, www.aisancekalonji.com
 * Auditer par : La CyberConfiance, www.cyberconfiance.com
 */
"""
from flask import Blueprint, render_template, jsonify, request, send_file, flash, redirect, url_for, current_app
from flask_login import login_required, current_user
from datetime import datetime, date, timedelta
import os
import zipfile
from io import BytesIO
from werkzeug.utils import secure_filename

from models import db, Invoice, Airline, Overflight, Landing, TariffConfig, AuditLog, Flight, Aircraft, SystemConfig
from services.invoice_generator import generate_invoice_pdf, calculate_invoice_amounts, regenerate_invoice, generate_invoice_number
from utils.decorators import role_required
from services.translation_service import t

invoices_bp = Blueprint('invoices', __name__)

ALLOWED_EXTENSIONS = {'pdf', 'png', 'jpg', 'jpeg'}

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


@invoices_bp.route('/')
@login_required
@role_required(['superadmin', 'billing', 'supervisor'])
def index():
    page = request.args.get('page', 1, type=int)
    status = request.args.get('status', '')
    airline_id = request.args.get('airline_id', type=int)
    date_start = request.args.get('date_start')
    date_end = request.args.get('date_end')
    flight_type = request.args.get('flight_type')
    aircraft_type = request.args.get('aircraft_type')
    
    query = Invoice.query
    
    if status:
        query = query.filter_by(status=status)
    if airline_id:
        query = query.filter_by(airline_id=airline_id)
    if flight_type:
        query = query.filter_by(invoice_type=flight_type)
    if aircraft_type:
        query = query.filter(
            db.or_(
                Invoice.overflights.any(Overflight.aircraft.has(type_code=aircraft_type)),
                Invoice.landings.any(Landing.aircraft.has(type_code=aircraft_type))
            )
        )
    if date_start:
        try:
            start_dt = datetime.strptime(date_start, '%Y-%m-%d')
            query = query.filter(Invoice.created_at >= start_dt)
        except ValueError:
            pass
    if date_end:
        try:
            end_dt = datetime.strptime(date_end, '%Y-%m-%d')
            # Add one day to include the end date fully
            query = query.filter(Invoice.created_at < end_dt + timedelta(days=1))
        except ValueError:
            pass
    
    invoices = query.order_by(Invoice.created_at.desc()).paginate(
        page=page, per_page=20, error_out=False
    )
    
    # Statistics
    pending_count = Invoice.query.filter_by(status='draft').count()
    sent_count = Invoice.query.filter_by(status='sent').count()
    paid_count = Invoice.query.filter_by(status='paid').count()
    
    airlines = Airline.query.filter_by(is_active=True).order_by(Airline.name).all()

    # Fetch options for filters
    flight_types = [r[0] for r in db.session.query(Invoice.invoice_type).distinct().all() if r[0]]
    aircraft_types = [r[0] for r in db.session.query(Aircraft.type_code).distinct().all() if r[0]]

    return render_template('invoices/index.html', 
                          invoices=invoices,
                          status=status,
                          pending_count=pending_count,
                          sent_count=sent_count,
                          paid_count=paid_count,
                          airlines=airlines,
                          flight_types=flight_types,
                          aircraft_types=aircraft_types,
                          current_filters={
                              'airline_id': airline_id,
                              'date_start': date_start,
                              'date_end': date_end,
                              'status': status,
                              'flight_type': flight_type,
                              'aircraft_type': aircraft_type
                          })


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
        
        invoice_number = generate_invoice_number()
        
        amounts = calculate_invoice_amounts(overflight_ids, landing_ids)
        
        currency_conf = SystemConfig.query.filter_by(key='invoice_currency').first()
        currency = currency_conf.value if currency_conf else 'USD'

        invoice = Invoice(
            invoice_number=invoice_number,
            airline_id=airline_id,
            invoice_type=invoice_type,
            subtotal=amounts['subtotal'],
            currency=currency,
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
                # Security Check: Ensure overflight belongs to selected airline
                if ovf.airline_id != airline_id:
                    current_app.logger.warning(f"Security Alert: Attempt to bill overflight {ovf.id} (Airline {ovf.airline_id}) to Airline {airline_id}")
                    continue

                ovf.invoice_id = invoice.id
                ovf.is_billed = True
        
        for land_id in landing_ids:
            land = Landing.query.get(land_id)
            if land:
                # Security Check: Ensure landing belongs to selected airline
                if land.airline_id != airline_id:
                    current_app.logger.warning(f"Security Alert: Attempt to bill landing {land.id} (Airline {land.airline_id}) to Airline {airline_id}")
                    continue

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


@invoices_bp.route('/<int:invoice_id>/regenerate', methods=['POST'])
@login_required
@role_required(['superadmin', 'billing'])
def regenerate(invoice_id):
    if regenerate_invoice(invoice_id, current_user.id):
        flash(t('invoices.regenerated_success'), 'success')
    else:
        flash(t('invoices.regenerated_error'), 'error')
    return redirect(url_for('invoices.detail', invoice_id=invoice_id))


@invoices_bp.route('/<int:invoice_id>/pdf')
@login_required
@role_required(['superadmin', 'billing', 'supervisor'])
def download_pdf(invoice_id):
    invoice = Invoice.query.get_or_404(invoice_id)
    
    # Log download
    log = AuditLog(
        user_id=current_user.id,
        action='download_invoice_pdf',
        entity_type='invoice',
        entity_id=invoice.id,
        ip_address=request.remote_addr,
        changes=f"Downloaded by {current_user.username}"
    )
    db.session.add(log)
    db.session.commit()
    
    if invoice.pdf_path and os.path.exists(invoice.pdf_path):
        return send_file(invoice.pdf_path, as_attachment=True, download_name=f'{invoice.invoice_number}.pdf')

    # Try to generate if missing
    pdf_path = generate_invoice_pdf(invoice)
    if pdf_path and os.path.exists(pdf_path):
        return send_file(pdf_path, as_attachment=True, download_name=f'{invoice.invoice_number}.pdf')
    
    flash(t('invoices.pdf_error'), 'error')
    return redirect(url_for('invoices.detail', invoice_id=invoice_id))


@invoices_bp.route('/batch-download', methods=['POST'])
@login_required
@role_required(['superadmin', 'billing'])
def batch_download():
    invoice_ids = request.form.getlist('invoice_ids')
    if not invoice_ids:
        flash(t('invoices.no_selection'), 'warning')
        return redirect(url_for('invoices.index'))

    invoices = Invoice.query.filter(Invoice.id.in_(invoice_ids)).all()

    memory_file = BytesIO()
    with zipfile.ZipFile(memory_file, 'w') as zf:
        for invoice in invoices:
            path = invoice.pdf_path
            if not path or not os.path.exists(path):
                path = generate_invoice_pdf(invoice)

            if path and os.path.exists(path):
                zf.write(path, os.path.basename(path))

    memory_file.seek(0)

    return send_file(
        memory_file,
        mimetype='application/zip',
        as_attachment=True,
        download_name=f'invoices_batch_{datetime.now().strftime("%Y%m%d%H%M")}.zip'
    )


@invoices_bp.route('/<int:invoice_id>/send', methods=['POST'])
@login_required
@role_required(['superadmin', 'billing'])
def send_invoice(invoice_id):
    invoice = Invoice.query.get_or_404(invoice_id)
    invoice.status = 'sent'
    invoice.sent_at = datetime.utcnow()
    
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

    # Handle file upload
    file = request.files.get('payment_proof')
    if not file:
        flash(t('invoices.proof_required'), 'error')
        return redirect(url_for('invoices.detail', invoice_id=invoice_id))

    if file:
        if not allowed_file(file.filename):
            flash(t('invoices.invalid_file_type'), 'error')
            return redirect(url_for('invoices.detail', invoice_id=invoice_id))

        upload_dir = 'statics/uploads/payments'
        os.makedirs(upload_dir, exist_ok=True)

        filename = secure_filename(file.filename)
        timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
        new_filename = f"proof_{invoice.invoice_number}_{timestamp}_{filename}"

        filepath = os.path.join(upload_dir, new_filename)
        file.save(filepath)
        invoice.payment_proof_path = filepath

    invoice.status = 'paid'
    invoice.paid_date = date.today()
    
    log = AuditLog(
        user_id=current_user.id,
        action='mark_invoice_paid',
        entity_type='invoice',
        entity_id=invoice.id,
        ip_address=request.remote_addr,
        changes=f"Payment proof: {filename if file else 'None'}"
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
    
    invoice_number = generate_invoice_number(prefix='OVF')
    
    currency_conf = SystemConfig.query.filter_by(key='invoice_currency').first()
    currency = currency_conf.value if currency_conf else 'USD'

    invoice = Invoice(
        invoice_number=invoice_number,
        airline_id=airline_id,
        invoice_type='overflight',
        subtotal=subtotal,
        currency=currency,
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


@invoices_bp.route('/generate/flight/<int:flight_id>')
@login_required
@role_required(['superadmin', 'billing'])
def generate_flight_invoice(flight_id):
    """Generate invoice for a specific flight (including overflights and landings)"""
    flight = Flight.query.get_or_404(flight_id)

    # Check if we already have invoices for this flight
    # We look at related overflights and landings
    overflights = Overflight.query.filter_by(flight_id=flight_id).all()
    landings = Landing.query.filter_by(flight_id=flight_id).all()

    existing_invoice_id = None
    all_billed = True

    # Check overflights
    unbilled_ovf_ids = []
    for ovf in overflights:
        if not ovf.is_billed:
            all_billed = False
            unbilled_ovf_ids.append(ovf.id)
        elif ovf.invoice_id:
            existing_invoice_id = ovf.invoice_id

    # Check landings
    unbilled_land_ids = []
    for land in landings:
        if not land.is_billed:
            all_billed = False
            unbilled_land_ids.append(land.id)
        elif land.invoice_id:
            existing_invoice_id = land.invoice_id

    if all_billed and existing_invoice_id:
        return redirect(url_for('invoices.detail', invoice_id=existing_invoice_id))

    if not unbilled_ovf_ids and not unbilled_land_ids:
        flash(t('invoices.no_billable_items'), 'warning')
        if existing_invoice_id:
             return redirect(url_for('invoices.detail', invoice_id=existing_invoice_id))
        return redirect(url_for('flights.detail', flight_id=flight_id))

    # Generate new invoice
    amounts = calculate_invoice_amounts(unbilled_ovf_ids, unbilled_land_ids)

    invoice_number = generate_invoice_number(prefix='FLT')

    currency_conf = SystemConfig.query.filter_by(key='invoice_currency').first()
    currency = currency_conf.value if currency_conf else 'USD'

    invoice = Invoice(
        invoice_number=invoice_number,
        airline_id=flight.airline_id,
        invoice_type='flight',
        subtotal=amounts['subtotal'],
        currency=currency,
        tax_amount=amounts['tax'],
        total_amount=amounts['total'],
        status='draft',
        due_date=date.today(),
        notes=f"Vol: {flight.callsign}, Date: {flight.flight_date}",
        created_by=current_user.id
    )

    db.session.add(invoice)
    db.session.flush()

    # Link items
    for ovf_id in unbilled_ovf_ids:
        ovf = Overflight.query.get(ovf_id)
        if ovf:
            ovf.invoice_id = invoice.id
            ovf.is_billed = True

    for land_id in unbilled_land_ids:
        land = Landing.query.get(land_id)
        if land:
            land.invoice_id = invoice.id
            land.is_billed = True

    log = AuditLog(
        user_id=current_user.id,
        action='generate_flight_invoice',
        entity_type='invoice',
        entity_id=invoice.id,
        ip_address=request.remote_addr
    )
    db.session.add(log)
    db.session.commit()

    flash(t('invoices.created_success').format(number=invoice_number), 'success')
    return redirect(url_for('invoices.detail', invoice_id=invoice.id))
