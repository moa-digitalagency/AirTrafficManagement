"""
/* * Nom de l'application : ATM-RDC
 * Description : Source file: test_qa_audit.py
 * Produit de : MOA Digital Agency, www.myoneart.com
 * Fait par : Aisance KALONJI, www.aisancekalonji.com
 * Auditer par : La CyberConfiance, www.cyberconfiance.com
 */
"""
import unittest
import os
import io
import sys

# Set dummy DB URL and DISABLE_POSTGIS before importing app
os.environ['DATABASE_URL'] = 'sqlite:///:memory:'
os.environ['DISABLE_POSTGIS'] = '1'

from datetime import date, datetime, timedelta
from app import create_app
from models import db, User, Invoice, AuditLog, SystemConfig, Airline, Overflight, Landing, Aircraft
from config.settings import Config

class TestConfig(Config):
    TESTING = True
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'
    WTF_CSRF_ENABLED = False
    SESSION_COOKIE_SECURE = False
    SECRET_KEY = 'test-secret-key'
    WTF_CSRF_SECRET_KEY = 'test-secret-key'

class TestQAAudit(unittest.TestCase):
    def setUp(self):
        # We can pass the config class, but ensure the env var was set anyway
        self.app = create_app(TestConfig)
        self.app_context = self.app.app_context()
        self.app_context.push()

        # When using SQLite without spatialite, we might need to be careful.
        # But DISABLE_POSTGIS=1 should make geometry columns Text.
        db.create_all()

        # Create Admin User
        self.user = User(username='qa_admin', email='qa@rva.cd', role='superadmin', is_active=True)
        self.user.set_password('password')
        db.session.add(self.user)

        # Create Dummy Airline
        self.airline = Airline(name="Test Air", iata_code="TA", icao_code="TST", is_active=True)
        db.session.add(self.airline)

        db.session.commit()

        self.client = self.app.test_client()

        # Login helper
        with self.client.session_transaction() as sess:
            sess['_user_id'] = str(self.user.id)
            sess['_fresh'] = True

    def tearDown(self):
        db.session.remove()
        db.drop_all()
        self.app_context.pop()

    def test_invoice_regeneration_audit(self):
        # Create Invoice
        invoice = Invoice(
            invoice_number="QA-001",
            airline_id=self.airline.id,
            status='sent',
            total_amount=100.0,
            created_by=self.user.id,
            created_at=datetime.utcnow()
        )
        db.session.add(invoice)
        db.session.commit()

        # Call Regenerate Endpoint
        response = self.client.post(f'/invoices/{invoice.id}/regenerate', follow_redirects=True)
        self.assertEqual(response.status_code, 200)

        # Check Audit Log
        log = AuditLog.query.filter_by(action='regenerate_invoice', entity_id=invoice.id).first()
        self.assertIsNotNone(log, "Audit log for regeneration should exist")
        self.assertEqual(log.user_id, self.user.id)

    def test_upload_verification(self):
        # Create Invoice
        invoice = Invoice(
            invoice_number="QA-002",
            airline_id=self.airline.id,
            status='sent',
            total_amount=200.0,
            created_by=self.user.id
        )
        db.session.add(invoice)
        db.session.commit()

        # 1. Attempt without file
        response = self.client.post(f'/invoices/{invoice.id}/mark-paid', follow_redirects=True)
        # Should flash error (localized message)
        # Since we added the translation, it returns the French text by default
        self.assertTrue(b'preuve de paiement' in response.data or b'invoices.proof_required' in response.data)

        invoice = db.session.get(Invoice, invoice.id)
        self.assertNotEqual(invoice.status, 'paid')

        # 2. Attempt with file
        data = {
            'payment_proof': (io.BytesIO(b'my pdf content'), 'proof.pdf')
        }
        response = self.client.post(f'/invoices/{invoice.id}/mark-paid', data=data, content_type='multipart/form-data', follow_redirects=True)

        invoice = db.session.get(Invoice, invoice.id)
        self.assertEqual(invoice.status, 'paid')
        self.assertIsNotNone(invoice.payment_proof_path)

        # Verify file exists
        full_path = invoice.payment_proof_path
        if os.path.exists(full_path):
            os.remove(full_path)

    def test_pdf_compliance(self):
        # Setup System Config for Header/Footer
        db.session.add(SystemConfig(key='invoice_header_title', value='QA TEST TITLE'))
        db.session.commit()

        invoice = Invoice(
            invoice_number="QA-003",
            airline_id=self.airline.id,
            status='draft',
            total_amount=500.0,
            created_by=self.user.id,
            created_at=datetime.utcnow(),
            due_date=date.today()
        )
        db.session.add(invoice)
        db.session.commit()

        # Call PDF Generation via download route
        response = self.client.get(f'/invoices/{invoice.id}/pdf')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.mimetype, 'application/pdf')

        # Verify file was created on disk
        invoice = db.session.get(Invoice, invoice.id)
        self.assertIsNotNone(invoice.pdf_path)
        self.assertTrue(os.path.exists(invoice.pdf_path))

        # Clean up
        if os.path.exists(invoice.pdf_path):
            os.remove(invoice.pdf_path)

if __name__ == '__main__':
    unittest.main()
