"""
/* * Nom de l'application : ATM-RDC
 * Description : Source file: test_invoice_performance.py
 * Produit de : MOA Digital Agency, www.myoneart.com
 * Fait par : Aisance KALONJI, www.aisancekalonji.com
 * Auditer par : La CyberConfiance, www.cyberconfiance.com
 */
"""
import os
import sys
import unittest
from datetime import datetime

# Configure environment before imports
os.environ['DISABLE_POSTGIS'] = '1'
os.environ['FLASK_ENV'] = 'testing'

# Add repo root to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from flask import Flask
from sqlalchemy import event
from sqlalchemy.orm import joinedload
from models import db, Invoice, Airline, User, SystemConfig

def create_test_app():
    app = Flask(__name__)
    app.config['TESTING'] = True
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['SECRET_KEY'] = 'test-secret'
    db.init_app(app)
    return app

class TestInvoicePerformance(unittest.TestCase):
    def setUp(self):
        self.app = create_test_app()
        self.app_context = self.app.app_context()
        self.app_context.push()

        # Create all tables
        db.create_all()

        # Seed data
        self.seed_data()

        # Reset query counter
        self.query_count = 0

        # Register listener
        self.listener = event.listen(db.engine, "before_cursor_execute", self.before_cursor_execute)

    def tearDown(self):
        event.remove(db.engine, "before_cursor_execute", self.before_cursor_execute)
        db.session.remove()
        db.drop_all()
        self.app_context.pop()

    def before_cursor_execute(self, conn, cursor, statement, parameters, context, executemany):
        self.query_count += 1
        # Uncomment to debug queries
        # print(f"QUERY: {statement}")

    def seed_data(self):
        # Create airlines
        self.airlines = []
        for i in range(5):
            airline = Airline(
                name=f"Airline {i}",
                iata_code=f"A{i}",
                icao_code=f"AIR{i}",
                country="TestCountry",
                is_active=True
            )
            db.session.add(airline)
            self.airlines.append(airline)

        db.session.commit()

        # Create invoices
        for i in range(20):
            invoice = Invoice(
                invoice_number=f"INV-{i:03d}",
                airline_id=self.airlines[i % 5].id,
                status='draft',
                created_at=datetime.utcnow()
            )
            db.session.add(invoice)

        db.session.commit()

    def test_invoice_index_n_plus_one(self):
        """
        Simulate the invoice index page logic and count queries.
        Without optimization, accessing airline.name for each invoice triggers a query.
        """
        self.query_count = 0

        # Simulate query in routes/invoices.py
        # Current implementation: query = Invoice.query
        page = 1
        invoices_pagination = Invoice.query.order_by(Invoice.created_at.desc()).paginate(
            page=page, per_page=20, error_out=False
        )

        # Simulate template rendering (accessing relationship)
        airline_names = []
        for invoice in invoices_pagination.items:
            # This triggers N+1 if not eager loaded
            if invoice.airline:
                airline_names.append(invoice.airline.name)

        print(f"\nQueries executed (Original): {self.query_count}")

        # Expected:
        # 1 query for count (pagination)
        # 1 query for fetching invoices
        # 20 queries for fetching airline for each invoice (N+1)
        # Total approx 22 queries.

        self.assertGreater(self.query_count, 5, "Should have N+1 problem before optimization")

    def test_invoice_index_optimized(self):
        """
        Test the optimized query with joinedload.
        """
        self.query_count = 0

        # Optimized implementation
        invoices_pagination = Invoice.query.options(joinedload(Invoice.airline)).order_by(Invoice.created_at.desc()).paginate(
            page=1, per_page=20, error_out=False
        )

        # Simulate template rendering
        airline_names = []
        for invoice in invoices_pagination.items:
            if invoice.airline:
                airline_names.append(invoice.airline.name)

        print(f"Queries executed (Optimized): {self.query_count}")

        # Expected:
        # 1 query for count (pagination)
        # 1 query for fetching invoices with JOIN
        # Total 2 queries.

        self.assertLess(self.query_count, 5, "Should not have N+1 problem with joinedload")

if __name__ == '__main__':
    unittest.main()
