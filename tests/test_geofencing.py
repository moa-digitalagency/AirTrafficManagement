import unittest
from unittest.mock import MagicMock, patch
import sys
import os

# Add repo root to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from services.flight_tracker import is_point_in_rdc, RDC_BOUNDARY

class TestGeofencing(unittest.TestCase):

    @patch('services.flight_tracker.db')
    def test_postgis_check_success(self, mock_db):
        """Test that PostGIS check is used when DB is available"""
        # Setup mock
        mock_result = MagicMock()
        mock_result.scalar.return_value = True
        mock_db.session.execute.return_value = mock_result

        # Call function
        result = is_point_in_rdc(-4.3, 15.3) # Kinshasa approx

        # Verify
        self.assertTrue(result)
        mock_db.session.execute.assert_called_once()
        args, _ = mock_db.session.execute.call_args
        self.assertIn("ST_Contains", str(args[0]))
        self.assertIn("ST_SetSRID", str(args[0]))

    @patch('services.flight_tracker.db')
    def test_postgis_check_fallback(self, mock_db):
        """Test fallback to Shapely when DB fails"""
        # Setup mock to raise exception
        mock_db.session.execute.side_effect = Exception("DB Connection Failed")

        # Test a point definitely inside RDC (Kinshasa)
        # Kinshasa: -4.325, 15.322
        lat, lon = -4.325, 15.322

        # Note: We need to make sure the point is actually inside the RDC_BOUNDARY defined in the code.
        # The code's boundary is simplified. Let's check a point inside that polygon.
        # One point in polygon: 20.0, -2.0 (Central RDC)
        lat_in, lon_in = -2.0, 20.0

        result = is_point_in_rdc(lat_in, lon_in)
        self.assertTrue(result, "Should be True via Shapely fallback")

        # Test a point outside (Paris)
        lat_out, lon_out = 49.0, 2.35
        result = is_point_in_rdc(lat_out, lon_out)
        self.assertFalse(result, "Should be False via Shapely fallback")

if __name__ == '__main__':
    unittest.main()
