"""
Service de génération de factures
Air Traffic Management - RDC
"""

import os
from datetime import datetime
from io import BytesIO

from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.units import cm
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, Image
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_RIGHT

from models import db, Overflight, Landing, TariffConfig, Invoice


def get_tariff(code):
    tariff = TariffConfig.query.filter_by(code=code, is_active=True).first()
    return tariff.value if tariff else 0


def calculate_invoice_amounts(overflight_ids, landing_ids):
    subtotal = 0
    
    survol_rate = get_tariff('SURVOL_KM')
    tonnage_rate = get_tariff('TONNAGE_RATE')
    landing_base = get_tariff('LANDING_BASE')
    parking_rate = get_tariff('PARKING_HOUR')
    night_surcharge = get_tariff('NIGHT_SURCHARGE') / 100
    tva_rate = get_tariff('TVA_RATE') / 100
    
    for ovf_id in overflight_ids:
        ovf = Overflight.query.get(ovf_id)
        if ovf:
            distance_cost = (ovf.distance_km or 0) * survol_rate
            
            tonnage_cost = 0
            if ovf.aircraft and ovf.aircraft.mtow:
                tonnage_cost = (ovf.aircraft.mtow / 1000) * tonnage_rate
            
            subtotal += distance_cost + tonnage_cost
    
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


def generate_invoice_pdf(invoice):
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
    
    content = []
    
    content.append(Paragraph("RÉGIE DES VOIES AÉRIENNES", header_style))
    content.append(Paragraph("République Démocratique du Congo", header_style))
    content.append(Spacer(1, 0.5*cm))
    content.append(Paragraph("FACTURE", title_style))
    content.append(Spacer(1, 0.5*cm))
    
    info_data = [
        ['N° Facture:', invoice.invoice_number, 'Date:', invoice.created_at.strftime('%d/%m/%Y') if invoice.created_at else ''],
        ['Type:', invoice.invoice_type or 'Standard', 'Échéance:', invoice.due_date.strftime('%d/%m/%Y') if invoice.due_date else ''],
        ['Statut:', invoice.status.upper(), '', ''],
    ]
    
    info_table = Table(info_data, colWidths=[3*cm, 5*cm, 3*cm, 5*cm])
    info_table.setStyle(TableStyle([
        ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
        ('FONTNAME', (2, 0), (2, -1), 'Helvetica-Bold'),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
    ]))
    content.append(info_table)
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
    
    survol_rate = get_tariff('SURVOL_KM')
    landing_base = get_tariff('LANDING_BASE')
    
    overflights = Overflight.query.filter_by(invoice_id=invoice.id).all()
    for ovf in overflights:
        distance = ovf.distance_km or 0
        cost = distance * survol_rate
        items_data.append([
            f'Survol {ovf.session_id}',
            f'{distance:.1f} km',
            f'{survol_rate:.2f} USD/km',
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
    
    content.append(Paragraph("Régie des Voies Aériennes - RDC", footer_style))
    content.append(Paragraph("Aéroport International de N'Djili - Kinshasa", footer_style))
    content.append(Paragraph("Email: facturation@rva.cd | Tél: +243 XXX XXX XXX", footer_style))
    
    doc.build(content)
    
    invoice.pdf_path = filepath
    db.session.commit()
    
    return filepath
