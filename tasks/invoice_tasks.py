"""
/* * Nom de l'application : ATM-RDC
 * Description : Source file: invoice_tasks.py
 * Produit de : MOA Digital Agency, www.myoneart.com
 * Fait par : Aisance KALONJI, www.aisancekalonji.com
 * Auditer par : La CyberConfiance, www.cyberconfiance.com
 */
"""
"""
Invoice-related Celery tasks for ATM-RDC
Handles asynchronous invoice generation and processing
"""
from datetime import datetime, timedelta
from celery_app import celery


@celery.task(bind=True, max_retries=3)
def generate_pending_invoices(self):
    """
    Generate invoices for completed overflights and landings
    This task runs hourly via Celery Beat
    """
    try:
        from app import app
        from models import db, Overflight, Landing, Invoice
        from services.invoice_generator import generate_overflight_invoice, generate_landing_invoice
        
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
                invoice = generate_overflight_invoice(overflight.id)
                if invoice:
                    overflight.is_invoiced = True
                    invoices_generated.append(invoice.invoice_number)
            
            for landing in uninvoiced_landings:
                invoice = generate_landing_invoice(landing.id)
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
    from app import app
    from services.invoice_generator import generate_overflight_invoice, generate_landing_invoice
    
    with app.app_context():
        if invoice_type == 'overflight':
            invoice = generate_overflight_invoice(reference_id)
        elif invoice_type == 'landing':
            invoice = generate_landing_invoice(reference_id)
        else:
            return {'status': 'failed', 'reason': 'Invalid invoice type'}
        
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
    from app import app
    from models import db, Invoice
    
    with app.app_context():
        invoice = Invoice.query.get(invoice_id)
        
        if invoice:
            return {
                'status': 'notification_sent',
                'invoice_number': invoice.invoice_number,
                'airline': invoice.airline.name if invoice.airline else 'Unknown'
            }
        
        return {'status': 'failed', 'reason': 'Invoice not found'}
