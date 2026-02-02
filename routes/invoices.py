from flask import Blueprint, render_template, jsonify, request, send_file, flash, redirect, url_for
from flask_login import login_required, current_user
from datetime import datetime, date
import os

from models import db, Invoice, Airline, Overflight, Landing, TariffConfig, AuditLog
from services.invoice_generator import generate_invoice_pdf, calculate_invoice_amounts
from utils.decorators import role_required

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
            flash('Veuillez sélectionner une compagnie aérienne.', 'error')
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
        
        flash(f'Facture {invoice_number} créée avec succès.', 'success')
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
    
    flash('Erreur lors de la génération du PDF.', 'error')
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
    
    flash(f'Facture {invoice.invoice_number} marquée comme envoyée.', 'success')
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
    
    flash(f'Facture {invoice.invoice_number} marquée comme payée.', 'success')
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
        
        flash(f'Tarif "{tariff.name}" mis à jour.', 'success')
    
    return redirect(url_for('invoices.tariffs'))
