import unittest
from unittest.mock import MagicMock, patch
import sys
import os
from shapely.geometry import Point, Polygon
from shapely.prepared import prep

# Add repo root to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from services import flight_tracker
from services.flight_tracker import is_point_in_rdc, RDC_BOUNDARY

class TestGeofencing(unittest.TestCase):

    def setUp(self):
        # Reset cache before each test
        flight_tracker.CACHED_RDC_BOUNDARY_GEOM = None

    @patch('services.flight_tracker.Airspace')
    @patch('services.flight_tracker.to_shape')
    def test_db_boundary_success(self, mock_to_shape, mock_airspace_model):
        """Test that DB boundary is used when available"""
        # Setup mock Airspace
        mock_airspace = MagicMock()
        mock_airspace.geom = "WKB_DATA"
        mock_airspace_model.query.filter_by.return_value.first.return_value = mock_airspace

        # Setup mock to_shape to return a simple square polygon
        # (0,0) to (10,10)
        simple_polygon = Polygon([(0,0), (0,10), (10,10), (10,0), (0,0)])
        mock_to_shape.return_value = simple_polygon

        # Test point inside (5,5) - note is_point_in_rdc takes (lat, lon), shapely takes (x=lon, y=lat)
        # Here x=5, y=5 is inside.
        result = is_point_in_rdc(5.0, 5.0)
        self.assertTrue(result)

        # Test point outside (15,15)
        result = is_point_in_rdc(15.0, 15.0)
        self.assertFalse(result)

        # Verify DB was queried
        mock_airspace_model.query.filter_by.assert_called_with(type='boundary')
        mock_to_shape.assert_called_with("WKB_DATA")

    @patch('services.flight_tracker.Airspace')
    def test_fallback_boundary(self, mock_airspace_model):
        """Test fallback to hardcoded boundary when DB fails"""
        # Setup mock to return None (DB miss or fail)
        mock_airspace_model.query.filter_by.return_value.first.side_effect = Exception("DB Fail")

        # Test a point definitely inside RDC (Central RDC)
        # Lat -2.0, Lon 20.0
        lat_in, lon_in = -2.0, 20.0
        result = is_point_in_rdc(lat_in, lon_in)
        self.assertTrue(result, "Should be True via fallback")

        # Test a point outside (Paris)
        lat_out, lon_out = 49.0, 2.35
        result = is_point_in_rdc(lat_out, lon_out)
        self.assertFalse(result, "Should be False via fallback")

    @patch('services.flight_tracker.Airspace')
    @patch('services.flight_tracker.to_shape')
    def test_caching(self, mock_to_shape, mock_airspace_model):
        """Test that DB is queried only once"""
        # Setup mock
        mock_airspace = MagicMock()
        mock_airspace.geom = "WKB_DATA"
        mock_airspace_model.query.filter_by.return_value.first.return_value = mock_airspace

        simple_polygon = Polygon([(0,0), (0,10), (10,10), (10,0), (0,0)])
        mock_to_shape.return_value = simple_polygon

        # First call
        is_point_in_rdc(5.0, 5.0)

        # Second call
        is_point_in_rdc(6.0, 6.0)

        # Verify DB query called only once
        mock_airspace_model.query.filter_by.assert_called_once()
        mock_to_shape.assert_called_once()

if __name__ == '__main__':
    unittest.main()
