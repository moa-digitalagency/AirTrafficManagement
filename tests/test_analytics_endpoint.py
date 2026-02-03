"""
/* * Nom de l'application : ATM-RDC
 * Description : Source file: test_analytics_endpoint.py
 * Produit de : MOA Digital Agency, www.myoneart.com
 * Fait par : Aisance KALONJI, www.aisancekalonji.com
 * Auditer par : La CyberConfiance, www.cyberconfiance.com
 */
"""
import unittest
from unittest.mock import MagicMock, patch
import json
import sys
import os
from flask import Flask

# Add repo root to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from models import db, Flight

# Create a test app factory
def create_test_app():
    app = Flask(__name__)
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['SECRET_KEY'] = 'test'
    app.config['WTF_CSRF_ENABLED'] = False
    db.init_app(app)
    return app

class TestAnalyticsEndpoint(unittest.TestCase):
    def setUp(self):
        # Patch decorators before importing routes
        self.patcher_login = patch('flask_login.login_required', lambda x: x)
        self.patcher_login.start()

        self.patcher_role = patch('utils.decorators.role_required', lambda roles: lambda x: x)
        self.patcher_role.start()

        self.app = create_test_app()
        self.app_context = self.app.app_context()
        self.app_context.push()

        # Create tables
        Flight.__table__.create(db.engine)

        # Ensure routes.analytics is reloaded to pick up patched decorators
        if 'routes.analytics' in sys.modules:
            del sys.modules['routes.analytics']

        from routes.analytics import analytics_bp
        self.app.register_blueprint(analytics_bp, url_prefix='/analytics')

        self.client = self.app.test_client()

    def tearDown(self):
        db.session.remove()
        Flight.__table__.drop(db.engine)
        self.app_context.pop()
        self.patcher_login.stop()
        self.patcher_role.stop()
        if 'routes.analytics' in sys.modules:
             del sys.modules['routes.analytics']

    def test_api_airports_traffic(self):
        # Insert data
        # Airport A: 2 arrivals, 1 departure
        # Airport B: 1 arrival, 0 departure
        # Airport C: 0 arrival, 2 departures
        # Airport D: 1 arrival, 1 departure

        flights = [
            Flight(callsign='F1', arrival_icao='AAAA', departure_icao='CCCC'),
            Flight(callsign='F2', arrival_icao='AAAA', departure_icao='CCCC'),
            Flight(callsign='F3', arrival_icao='BBBB', departure_icao='AAAA'),
            Flight(callsign='F4', arrival_icao='DDDD', departure_icao='DDDD'),
        ]
        db.session.add_all(flights)
        db.session.commit()

        # Expected Results:
        # AAAA: Arr 2, Dep 1 -> Total 3
        # CCCC: Arr 0, Dep 2 -> Total 2
        # DDDD: Arr 1, Dep 1 -> Total 2
        # BBBB: Arr 1, Dep 0 -> Total 1

        # Note: Order for CCCC and DDDD might vary as total is same.

        response = self.client.get('/analytics/api/airports/traffic')
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)

        # Verify structure and content
        self.assertEqual(len(data), 4)

        # Check AAAA
        row_aaaa = next((x for x in data if x['airport'] == 'AAAA'), None)
        self.assertIsNotNone(row_aaaa)
        self.assertEqual(row_aaaa['arrivals'], 2)
        self.assertEqual(row_aaaa['departures'], 1)
        self.assertEqual(row_aaaa['total'], 3)

        # Check CCCC
        row_cccc = next((x for x in data if x['airport'] == 'CCCC'), None)
        self.assertIsNotNone(row_cccc)
        self.assertEqual(row_cccc['arrivals'], 0)
        self.assertEqual(row_cccc['departures'], 2)
        self.assertEqual(row_cccc['total'], 2)

        # Check Sort Order
        self.assertEqual(data[0]['airport'], 'AAAA')
        # Second could be CCCC or DDDD
        self.assertIn(data[1]['airport'], ['CCCC', 'DDDD'])
        self.assertIn(data[2]['airport'], ['CCCC', 'DDDD'])
        self.assertEqual(data[3]['airport'], 'BBBB')

if __name__ == '__main__':
    unittest.main()
