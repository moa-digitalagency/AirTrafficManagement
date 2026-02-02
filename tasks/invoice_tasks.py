"""
Invoice-related Celery tasks for ATM-RDC
Handles asynchronous invoice generation and processing
"""
from celery_app import celery
from datetime import datetime, timedelta

@celery.task(bind=True, max_retries=3)
def generate_pending_invoices(self):
    """
    Generate invoices for completed overflights and landings
    This task runs hourly via Celery Beat
    """
    try:
        from app import create_app
        from models import db, Overflight, Landing, Invoice, Tariff
        from services.invoice_generator import generate_invoice
        
        app = create_app()
        with app.app_context():
            uninvoiced_overflights = Overflight.query.filter_by(
                status='completed',
                is_invoiced=False
            ).all()
            
            uninvoiced_landings = Landing.query.filter_by(
                is_invoiced=False
            ).all()
            
            invoices_generated = []
            
            for overflight in uninvoiced_overflights:
                invoice = generate_invoice(
                    invoice_type='overflight',
                    reference_id=overflight.id
                )
                if invoice:
                    overflight.is_invoiced = True
                    invoices_generated.append(invoice.invoice_number)
            
            for landing in uninvoiced_landings:
                invoice = generate_invoice(
                    invoice_type='landing',
                    reference_id=landing.id
                )
                if invoice:
                    landing.is_invoiced = True
                    invoices_generated.append(invoice.invoice_number)
            
            db.session.commit()
            return {
                'status': 'success',
                'invoices_generated': invoices_generated
            }
            
    except Exception as exc:
        self.retry(exc=exc, countdown=60)


@celery.task
def generate_single_invoice(invoice_type: str, reference_id: int):
    """
    Generate a single invoice on demand
    """
    from app import create_app
    from services.invoice_generator import generate_invoice
    
    app = create_app()
    with app.app_context():
        invoice = generate_invoice(
            invoice_type=invoice_type,
            reference_id=reference_id
        )
        
        if invoice:
            return {
                'status': 'success',
                'invoice_number': invoice.invoice_number,
                'amount': float(invoice.total_amount)
            }
        
        return {'status': 'failed', 'reason': 'Could not generate invoice'}


@celery.task
def send_invoice_notification(invoice_id: int):
    """
    Send notification for a generated invoice
    """
    from app import create_app
    from models import db, Invoice, Airline
    
    app = create_app()
    with app.app_context():
        invoice = Invoice.query.get(invoice_id)
        
        if invoice:
            return {
                'status': 'notification_sent',
                'invoice_number': invoice.invoice_number,
                'airline': invoice.airline.name if invoice.airline else 'Unknown'
            }
        
        return {'status': 'failed', 'reason': 'Invoice not found'}
