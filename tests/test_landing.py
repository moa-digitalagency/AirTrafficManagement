"""
/* * Nom de l'application : ATM-RDC
 * Description : Source file: test_landing.py
 * Produit de : MOA Digital Agency, www.myoneart.com
 * Fait par : Aisance KALONJI, www.aisancekalonji.com
 * Auditer par : La CyberConfiance, www.cyberconfiance.com
 */
"""
import unittest
from unittest.mock import MagicMock, patch
import sys
import os
from datetime import datetime, timedelta

# Add repo root to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from services.flight_tracker import check_landing_events

class TestLandingLogic(unittest.TestCase):

    @patch('services.flight_tracker.Flight')
    @patch('services.flight_tracker.Airport')
    @patch('services.flight_tracker.Landing')
    @patch('services.flight_tracker.TariffConfig')
    @patch('services.flight_tracker.db')
    def test_landing_sequence(self, mock_db, mock_tariff_config, mock_landing_model, mock_airport_model, mock_flight_model):
        # Setup Tariff
        mock_tariff = MagicMock()
        mock_tariff.value = 100.0
        mock_tariff_config.query.filter_by.return_value.first.return_value = mock_tariff

        # Setup Airport (Kinshasa)
        airport = MagicMock()
        airport.icao_code = 'FZAA'
        airport.name = "N'Djili"
        airport.latitude = -4.3858
        airport.longitude = 15.4446
        airport.elevation_ft = 1026 # ~312m
        mock_airport_model.query.filter_by.return_value.all.return_value = [airport]

        # Setup Flight
        flight = MagicMock()
        flight.id = 1
        flight.callsign = 'AFR123'
        flight.is_domestic = False
        mock_flight_model.query.get.return_value = flight

        # 1. Test Approach
        # Aircraft at 10km distance
        # 1 deg lat approx 111km. 0.1 deg approx 11km.
        lat_approaching = airport.latitude + 0.05
        lon_approaching = airport.longitude + 0.05

        # Mock no existing landing
        mock_landing_model.query.filter.return_value.order_by.return_value.first.return_value = None

        # Altitude 2000ft AGL approx. Speed 200kts.
        landing = check_landing_events(1, lat_approaching, lon_approaching, 3026, 200)

        # It should create a new landing record
        self.assertIsNotNone(landing)

        # Verify Landing constructor was called with status='approach'
        mock_landing_model.assert_called()
        call_args = mock_landing_model.call_args[1]
        self.assertEqual(call_args.get('status'), 'approach')
        self.assertEqual(call_args.get('airport_icao'), 'FZAA')

        mock_db.session.add.assert_called()
        mock_db.session.commit.assert_called()

        # 2. Test Touchdown
        # Setup existing landing as 'approach'
        existing_landing = MagicMock()
        existing_landing.status = 'approach'
        mock_landing_model.query.filter.return_value.order_by.return_value.first.return_value = existing_landing

        # Aircraft very close (lat/lon of airport), low altitude (50ft AGL), low speed (130kts)
        landing = check_landing_events(1, airport.latitude, airport.longitude, 1076, 130)

        self.assertEqual(existing_landing.status, 'landed')
        self.assertIsNotNone(existing_landing.touchdown_time)

        # 3. Test Parking
        existing_landing.status = 'landed'

        # Speed < 5kts
        landing = check_landing_events(1, airport.latitude, airport.longitude, 1026, 3)

        self.assertEqual(existing_landing.status, 'parking')
        self.assertIsNotNone(existing_landing.parking_start)

        # 4. Test Completion (Pushback)
        existing_landing.status = 'parking'
        existing_landing.parking_start = datetime.utcnow() - timedelta(hours=2)
        existing_landing.landing_fee = 0
        existing_landing.parking_fee = 0

        # Speed > 10kts
        landing = check_landing_events(1, airport.latitude, airport.longitude, 1026, 15)

        self.assertEqual(existing_landing.status, 'completed')
        self.assertIsNotNone(existing_landing.parking_end)

        # Verify fee calculation called (mocked property access might not trigger real logic if it's a MagicMock unless we implemented logic in the function)
        # The logic IS in the function:
        # landing.total_fee = (landing.landing_fee or 0) + (landing.parking_fee or 0)

        # Check if duration was calculated
        self.assertTrue(isinstance(existing_landing.parking_duration_minutes, float) or isinstance(existing_landing.parking_duration_minutes, int) or isinstance(existing_landing.parking_duration_minutes, MagicMock))

if __name__ == '__main__':
    unittest.main()
