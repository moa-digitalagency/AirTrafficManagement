"""
Service de génération de factures
Air Traffic Management - RDC
"""

import os
from datetime import datetime
from io import BytesIO
import qrcode

from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.units import cm
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, Image
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_RIGHT

from models import db, Overflight, Landing, TariffConfig, Invoice, SystemConfig, AuditLog, User, Flight
from services.translation_service import t


def get_contact_phone():
    config = SystemConfig.query.filter_by(key='rva_contact_phone').first()
    return config.value if config else "+2431234567890"


def get_tariff(code):
    tariff = TariffConfig.query.filter_by(code=code, is_active=True).first()
    return tariff.value if tariff else 0


def get_billing_mode():
    config = SystemConfig.query.filter_by(key='OVERFLIGHT_BILLING_MODE').first()
    return config.value if config else 'DISTANCE'


def generate_invoice_number(prefix=None):
    """
    Generate invoice number based on system configuration.
    """
    config = SystemConfig.query.filter_by(key='invoice_number_format').first()
    fmt = config.value if config else "RVA-{ANNEE}-{MOIS}-{ID}"

    now = datetime.now()
    count = Invoice.query.count() + 1

    # Replace placeholders
    res = fmt.replace('{ANNEE}', now.strftime('%Y'))
    res = res.replace('{MOIS}', now.strftime('%m'))
    res = res.replace('{JOUR}', now.strftime('%d'))

    if '{ID}' in res:
        res = res.replace('{ID}', f"{count:04d}")

    if '{INCREMENT}' in res:
        res = res.replace('{INCREMENT}', f"{count:04d}")

    if prefix and '{TYPE}' in res:
         res = res.replace('{TYPE}', prefix)

    return res


def generate_qr_code(data):
    """Generate a QR code image and return it as a BytesIO object"""
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_L,
        box_size=10,
        border=4,
    )
    qr.add_data(data)
    qr.make(fit=True)

    img = qr.make_image(fill_color="black", back_color="white")
    buffer = BytesIO()
    img.save(buffer, format="PNG")
    buffer.seek(0)
    return buffer


def calculate_overflight_cost(ovf):
    """
    Calculate cost for an overflight based on system configuration and airline exemptions.
    Returns: (cost, quantity_description, unit_price_description)
    """
    # Check exemption
    if ovf.flight and ovf.flight.airline and ovf.flight.airline.exempt_overflight_fees:
        return 0.0, "Exempted", "0.00 USD"

    mode = get_billing_mode()

    if mode == 'TIME':
        rate = get_tariff('SURVOL_MINUTE')
        qty = ovf.duration_minutes or 0
        cost = qty * rate
        desc = f"{qty} min"
        unit_desc = f"{rate:.2f} USD/min"
    elif mode == 'HYBRID':
        rate_time = get_tariff('SURVOL_HYBRID_TIME')
        rate_dist = get_tariff('SURVOL_HYBRID_DIST')
        qty_time = ovf.duration_minutes or 0
        qty_dist = ovf.distance_km or 0
        cost = (qty_time * rate_time) + (qty_dist * rate_dist)
        desc = f"{qty_time} min / {qty_dist:.1f} km"
        unit_desc = f"Hyb (T:{rate_time:.2f} + D:{rate_dist:.2f})"
    else: # DISTANCE
        rate = get_tariff('SURVOL_KM')
        qty = ovf.distance_km or 0
        cost = qty * rate
        desc = f"{qty:.1f} km"
        unit_desc = f"{rate:.2f} USD/km"

    return cost, desc, unit_desc


def calculate_invoice_amounts(overflight_ids, landing_ids):
    subtotal = 0
    
    tonnage_rate = get_tariff('TONNAGE_RATE')
    landing_base = get_tariff('LANDING_BASE')
    parking_rate = get_tariff('PARKING_HOUR')
    night_surcharge = get_tariff('NIGHT_SURCHARGE') / 100
    tva_rate = get_tariff('TVA_RATE') / 100
    
    for ovf_id in overflight_ids:
        ovf = Overflight.query.get(ovf_id)
        if ovf:
            cost, _, _ = calculate_overflight_cost(ovf)
            
            tonnage_cost = 0
            if ovf.aircraft and ovf.aircraft.mtow:
                tonnage_cost = (ovf.aircraft.mtow / 1000) * tonnage_rate
            
            subtotal += cost + tonnage_cost
    
    for land_id in landing_ids:
        land = Landing.query.get(land_id)
        if land:
            landing_cost = landing_base
            
            parking_minutes = land.parking_duration_minutes or 0
            if parking_minutes > 60:
                extra_hours = (parking_minutes - 60) / 60
                landing_cost += extra_hours * parking_rate
            
            if land.is_night:
                landing_cost *= (1 + night_surcharge)
            
            subtotal += landing_cost
    
    tax = subtotal * tva_rate
    total = subtotal + tax
    
    return {
        'subtotal': round(subtotal, 2),
        'tax': round(tax, 2),
        'total': round(total, 2)
    }


def generate_invoice_pdf(invoice, generated_by_user=None):
    upload_dir = 'statics/uploads/invoices'
    os.makedirs(upload_dir, exist_ok=True)
    
    filename = f"{invoice.invoice_number}.pdf"
    filepath = os.path.join(upload_dir, filename)
    
    doc = SimpleDocTemplate(
        filepath,
        pagesize=A4,
        rightMargin=2*cm,
        leftMargin=2*cm,
        topMargin=2*cm,
        bottomMargin=2*cm
    )
    
    styles = getSampleStyleSheet()
    
    title_style = ParagraphStyle(
        'Title',
        parent=styles['Heading1'],
        fontSize=18,
        textColor=colors.HexColor('#1e3a5f'),
        spaceAfter=20,
        alignment=TA_CENTER
    )
    
    header_style = ParagraphStyle(
        'Header',
        parent=styles['Normal'],
        fontSize=10,
        textColor=colors.HexColor('#666666'),
        alignment=TA_CENTER
    )

    # Fetch Configs
    header_title_conf = SystemConfig.query.filter_by(key='invoice_header_title').first()
    header_title = header_title_conf.value if header_title_conf else "RÉGIE DES VOIES AÉRIENNES"

    header_subtitle_conf = SystemConfig.query.filter_by(key='invoice_header_subtitle').first()
    header_subtitle = header_subtitle_conf.value if header_subtitle_conf else "République Démocratique du Congo"

    header_address_conf = SystemConfig.query.filter_by(key='invoice_header_address').first()
    header_address = header_address_conf.value if header_address_conf else "Aéroport International de N'Djili - Kinshasa"

    footer_legal_conf = SystemConfig.query.filter_by(key='invoice_footer_legal').first()
    footer_legal = footer_legal_conf.value if footer_legal_conf else ""

    footer_banks_conf = SystemConfig.query.filter_by(key='invoice_footer_banks').first()
    footer_banks = footer_banks_conf.value if footer_banks_conf else ""

    logo_path_conf = SystemConfig.query.filter_by(key='logo_path').first()
    logo_path = logo_path_conf.value if logo_path_conf else None
    
    content = []
    
    # Logo
    if logo_path and os.path.exists(os.path.join('static', logo_path)):
        try:
            logo = Image(os.path.join('static', logo_path), width=2*cm, height=2*cm)
            logo.hAlign = 'CENTER'
            content.append(logo)
            content.append(Spacer(1, 0.2*cm))
        except:
            pass

    # Header with Logo/Title
    content.append(Paragraph(header_title, header_style))
    content.append(Paragraph(header_subtitle, header_style))
    if header_address:
        content.append(Paragraph(header_address.replace('\n', '<br/>'), header_style))

    content.append(Spacer(1, 0.5*cm))
    content.append(Paragraph(t('invoices.invoice').upper(), title_style))
    content.append(Spacer(1, 0.5*cm))
    
    # QR Code Generation
    try:
        qr_data = f"RVA|{invoice.invoice_number}|{invoice.total_amount}|{invoice.created_at.isoformat()}"
        qr_buffer = generate_qr_code(qr_data)
        qr_img = Image(qr_buffer, width=3*cm, height=3*cm)
        qr_img.hAlign = 'RIGHT'
    except Exception as e:
        print(f"Error generating QR: {e}")
        qr_img = Spacer(1, 1)

    # Info Table with QR Code
    info_data = [
        [f"{t('invoices.number')}:", invoice.invoice_number, '', ''],
        [f"{t('invoices.date')}:", invoice.created_at.strftime('%d/%m/%Y') if invoice.created_at else '', '', ''],
        [f"{t('invoices.due_date')}:", invoice.due_date.strftime('%d/%m/%Y') if invoice.due_date else '', '', ''],
        [f"{t('invoices.status')}:", t(f"invoices.{invoice.status}").upper(), '', '']
    ]
    
    # Use a table to layout info (left) and QR (right)
    # We will just put the info table first, and maybe QR below or aside.
    # For simplicity, let's put QR code in a separate flowable or create a complex table.

    # Let's create a main table for the header section: [Info Table, QR Code]

    inner_info_table = Table(info_data, colWidths=[3*cm, 5*cm, 1*cm, 1*cm])
    inner_info_table.setStyle(TableStyle([
        ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
    ]))

    header_layout_data = [[inner_info_table, qr_img]]
    header_layout = Table(header_layout_data, colWidths=[12*cm, 4*cm])
    header_layout.setStyle(TableStyle([
        ('VALIGN', (0,0), (-1,-1), 'TOP'),
        ('ALIGN', (1,0), (1,0), 'RIGHT'),
    ]))
    content.append(header_layout)

    content.append(Spacer(1, 0.5*cm))
    
    if invoice.airline:
        content.append(Paragraph("<b>Client:</b>", styles['Normal']))
        content.append(Paragraph(f"{invoice.airline.name}", styles['Normal']))
        if invoice.airline.address:
            content.append(Paragraph(f"{invoice.airline.address}", styles['Normal']))
        if invoice.airline.email:
            content.append(Paragraph(f"Email: {invoice.airline.email}", styles['Normal']))
        content.append(Spacer(1, 0.5*cm))
    
    content.append(Paragraph("<b>Détails des services</b>", styles['Heading2']))
    content.append(Spacer(1, 0.3*cm))
    
    items_data = [['Description', 'Quantité', 'Prix Unitaire', 'Total']]
    
    landing_base = get_tariff('LANDING_BASE')
    
    overflights = Overflight.query.filter_by(invoice_id=invoice.id).all()
    for ovf in overflights:
        cost, desc, unit_desc = calculate_overflight_cost(ovf)

        items_data.append([
            f'Survol {ovf.session_id}',
            desc,
            unit_desc,
            f'{cost:.2f} USD'
        ])
    
    landings = Landing.query.filter_by(invoice_id=invoice.id).all()
    for land in landings:
        items_data.append([
            f'Atterrissage {land.airport_icao}',
            '1',
            f'{landing_base:.2f} USD',
            f'{landing_base:.2f} USD'
        ])
    
    items_table = Table(items_data, colWidths=[8*cm, 3*cm, 3*cm, 3*cm])
    items_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1e3a5f')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 9),
        ('ALIGN', (1, 0), (-1, -1), 'RIGHT'),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
        ('TOPPADDING', (0, 0), (-1, -1), 8),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f5f5f5')]),
    ]))
    content.append(items_table)
    content.append(Spacer(1, 0.5*cm))
    
    totals_data = [
        ['', '', 'Sous-total:', f'{invoice.subtotal:.2f} USD'],
        ['', '', 'TVA (16%):', f'{invoice.tax_amount:.2f} USD'],
        ['', '', 'TOTAL:', f'{invoice.total_amount:.2f} USD'],
    ]
    
    totals_table = Table(totals_data, colWidths=[8*cm, 3*cm, 3*cm, 3*cm])
    totals_table.setStyle(TableStyle([
        ('FONTNAME', (2, -1), (-1, -1), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('ALIGN', (2, 0), (-1, -1), 'RIGHT'),
        ('LINEABOVE', (2, -1), (-1, -1), 1, colors.black),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
    ]))
    content.append(totals_table)
    content.append(Spacer(1, 1*cm))
    
    footer_style = ParagraphStyle(
        'Footer',
        parent=styles['Normal'],
        fontSize=8,
        textColor=colors.HexColor('#888888'),
        alignment=TA_CENTER
    )
    
    if footer_legal:
        content.append(Paragraph(footer_legal.replace('\n', '<br/>'), footer_style))
        content.append(Spacer(1, 0.2*cm))

    if footer_banks:
         content.append(Paragraph("<b>Coordonnées Bancaires:</b>", footer_style))
         content.append(Paragraph(footer_banks.replace('\n', '<br/>'), footer_style))
         content.append(Spacer(1, 0.2*cm))

    content.append(Paragraph("Régie des Voies Aériennes - RDC", footer_style))
    if header_address:
         content.append(Paragraph(header_address.split('\n')[0], footer_style)) # Simplified address for footer

    phone = get_contact_phone()
    content.append(Paragraph(f"Email: facturation@rva.cd | Tél: {phone}", footer_style))
    
    # Add Generation Metadata
    gen_time = datetime.now().strftime("%d/%m/%Y %H:%M")
    gen_user = generated_by_user.username if generated_by_user else (f"User #{invoice.created_by}" if invoice.created_by else "Système")
    content.append(Spacer(1, 0.2*cm))
    content.append(Paragraph(f"Généré le {gen_time} par {gen_user}", footer_style))

    doc.build(content)
    
    invoice.pdf_path = filepath
    invoice.pdf_generated_at = datetime.utcnow()
    db.session.commit()
    
    return filepath


def regenerate_invoice(invoice_id, user_id):
    """
    Regenerate an invoice: recalculate amounts and generate new PDF.
    Logs action to AuditLog.
    """
    invoice = Invoice.query.get(invoice_id)
    if not invoice:
        return False

    # Recalculate amounts
    overflight_ids = [ovf.id for ovf in invoice.overflights]
    landing_ids = [land.id for land in invoice.landings]

    amounts = calculate_invoice_amounts(overflight_ids, landing_ids)

    old_total = invoice.total_amount

    invoice.subtotal = amounts['subtotal']
    invoice.tax_amount = amounts['tax']
    invoice.total_amount = amounts['total']
    invoice.updated_at = datetime.utcnow()

    user = User.query.get(user_id)

    log = AuditLog(
        user_id=user_id,
        action='regenerate_invoice',
        entity_type='invoice',
        entity_id=invoice.id,
        ip_address='127.0.0.1', # Placeholder, should be passed if possible
        changes=f"Regenerated. Old Total: {old_total}, New Total: {invoice.total_amount}"
    )
    db.session.add(log)
    db.session.commit()

    return generate_invoice_pdf(invoice, generated_by_user=user)


def trigger_auto_invoice(flight_id):
    """
    Automatically create an invoice for a flight if not already billed.
    Aggregates Landing and Overflight for the same flight.
    """
    flight = Flight.query.get(flight_id)
    if not flight:
        return None

    # Check for unbilled items
    unbilled_ovf = Overflight.query.filter_by(flight_id=flight_id, is_billed=False, status='completed').all()
    unbilled_land = Landing.query.filter_by(flight_id=flight_id, is_billed=False, status='completed').all()

    if not unbilled_ovf and not unbilled_land:
        return None

    # Check if airline is configured
    if not flight.airline_id:
        # Try to find airline from aircraft
        if flight.aircraft and flight.aircraft.operator_id:
             flight.airline_id = flight.aircraft.operator_id
        else:
             print(f"Skipping invoice for flight {flight.callsign}: No airline identified")
             return None

    amounts = calculate_invoice_amounts([o.id for o in unbilled_ovf], [l.id for l in unbilled_land])

    invoice_number = generate_invoice_number(prefix='AUTO')

    # Get Currency
    currency_conf = SystemConfig.query.filter_by(key='invoice_currency').first()
    currency = currency_conf.value if currency_conf else 'USD'

    invoice = Invoice(
        invoice_number=invoice_number,
        airline_id=flight.airline_id,
        invoice_type='auto_flight',
        subtotal=amounts['subtotal'],
        currency=currency,
        tax_amount=amounts['tax'],
        total_amount=amounts['total'],
        status='draft',
        due_date=datetime.now().date(),
        notes=f"Facture automatique pour vol {flight.callsign}",
        created_by=None # System
    )

    db.session.add(invoice)
    db.session.flush()

    for item in unbilled_ovf:
        item.invoice_id = invoice.id
        item.is_billed = True

    for item in unbilled_land:
        item.invoice_id = invoice.id
        item.is_billed = True

    db.session.commit()

    generate_invoice_pdf(invoice)

    return invoice
