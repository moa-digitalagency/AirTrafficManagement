import unittest
from unittest.mock import MagicMock, patch
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Mock modules to avoid real imports
mock_app_module = MagicMock()
mock_models_module = MagicMock()
mock_services_module = MagicMock()
mock_flight_tracker_module = MagicMock()
mock_celery_app_module = MagicMock()

# We need to setup the specific attributes that are imported from these modules
mock_app = MagicMock()
mock_app_module.app = mock_app

mock_db = MagicMock()
mock_flight = MagicMock()
mock_flight_pos = MagicMock()
mock_overflight = MagicMock()
mock_models_module.db = mock_db
mock_models_module.Flight = mock_flight
mock_models_module.FlightPosition = mock_flight_pos
mock_models_module.Overflight = mock_overflight

mock_fetch_data = MagicMock()
mock_services_module.fetch_external_flight_data = mock_fetch_data

mock_is_point_in_rdc = MagicMock()
mock_flight_tracker_module.is_point_in_rdc = mock_is_point_in_rdc
mock_flight_tracker_module.get_rdc_boundary = MagicMock()

# Mock celery decorator
def mock_task_decorator(*args, **kwargs):
    def decorator(f):
        f.retry = MagicMock()
        return f
    return decorator

mock_celery = MagicMock()
mock_celery.task = mock_task_decorator
mock_celery_app_module.celery = mock_celery

class TestFlightTasksLogic(unittest.TestCase):

    def setUp(self):
        # Apply patches manually in setUp to be sure
        self.patcher = patch.dict(sys.modules, {
            'app': mock_app_module,
            'models': mock_models_module,
            'services.api_client': mock_services_module,
            'services.flight_tracker': mock_flight_tracker_module,
            'celery_app': mock_celery_app_module
        })
        self.patcher.start()

        # Clear module cache to force reload with mocks
        if 'tasks.flight_tasks' in sys.modules:
            del sys.modules['tasks.flight_tasks']

        from tasks.flight_tasks import fetch_flight_positions, check_airspace_entries
        self.fetch_flight_positions = fetch_flight_positions
        self.check_airspace_entries = check_airspace_entries

        # Reset mocks
        mock_app.reset_mock()
        mock_db.reset_mock()
        mock_flight.reset_mock()
        mock_flight_pos.reset_mock()
        mock_overflight.reset_mock()
        mock_fetch_data.reset_mock()
        mock_is_point_in_rdc.reset_mock()

        # Setup app context mock
        mock_app.app_context.return_value.__enter__.return_value = None

    def tearDown(self):
        self.patcher.stop()

    def test_fetch_flight_positions_logic(self):
        # 3 Flights from API
        mock_fetch_data.return_value = [
            {'callsign': 'FLT1', 'latitude': 10, 'longitude': 10, 'altitude': 1000, 'heading': 100, 'ground_speed': 100},
            {'callsign': 'FLT2', 'latitude': 20, 'longitude': 20, 'altitude': 2000, 'heading': 200, 'ground_speed': 200},
            {'callsign': 'FLT3', 'latitude': 30, 'longitude': 30, 'altitude': 3000, 'heading': 300, 'ground_speed': 300},
        ]

        # 2 Flights in DB (FLT3 is missing in DB)
        f1 = MagicMock(); f1.callsign = 'FLT1'; f1.id=1
        f2 = MagicMock(); f2.callsign = 'FLT2'; f2.id=2

        # When querying filtered flights, return these two
        # The code calls: Flight.query.filter(...).all()
        mock_flight.query.filter.return_value.all.return_value = [f1, f2]

        # Call the task
        # Since we mocked the decorator to return the raw function, we pass mock_self manually
        mock_self = MagicMock()
        result = self.fetch_flight_positions(mock_self)

        # Verifications

        # 1. Verify fetch_external_flight_data called
        mock_fetch_data.assert_called_once()

        # 2. Verify Flight.query.filter called
        # The optimized code calls filter() NOT filter_by()
        mock_flight.query.filter.assert_called_once()

        # 3. Verify positions created for FLT1 and FLT2 only
        # FlightPosition(...) call count
        self.assertEqual(mock_flight_pos.call_count, 2)

        # 4. Verify DB add and commit
        self.assertEqual(mock_db.session.add.call_count, 2)
        mock_db.session.commit.assert_called_once()

        # 5. Verify flight objects updated
        self.assertEqual(f1.current_latitude, 10)
        self.assertEqual(f2.current_latitude, 20)

        # 6. Verify result
        self.assertEqual(result['positions_updated'], 3)

    def test_check_airspace_entries(self):
        # Setup flights
        f1 = MagicMock(id=1, callsign='F1', current_latitude=1, current_longitude=1)
        f2 = MagicMock(id=2, callsign='F2', current_latitude=2, current_longitude=2) # Already has overflight
        f3 = MagicMock(id=3, callsign='F3', current_latitude=3, current_longitude=3) # Outside RDC

        mock_flight.query.filter.return_value.all.return_value = [f1, f2, f3]

        # Setup existing overflights
        ovf2 = MagicMock(flight_id=2, status='active')
        mock_overflight.query.filter.return_value.all.return_value = [ovf2]

        # Setup is_point_in_rdc
        # F1: inside, F2: inside, F3: outside
        def side_effect(lat, lon):
            if lat == 1: return True
            if lat == 2: return True
            if lat == 3: return False
            return False
        mock_is_point_in_rdc.side_effect = side_effect

        # Call task
        mock_self = MagicMock()
        result = self.check_airspace_entries(mock_self)

        # Verify
        # 1. Overflight query should be called ONCE (optimization check)
        # It calls Overflight.query.filter(Overflight.flight_id.in_(...), ...).all()
        # So filter is called, then all()
        self.assertTrue(mock_overflight.query.filter.called)

        # 2. New overflight created for F1
        # db.session.add called once
        self.assertEqual(mock_db.session.add.call_count, 1)
        # Check args
        created_ovf = mock_db.session.add.call_args[0][0]
        # We can check simple attributes on the mock object if constructor set them
        # But MagicMock constructor returns a new mock, so we can't easily check attributes unless we look at call args
        # The Overflight class is mocked, so Overflight(...) creates a mock.
        # But we passed mock_overflight as Overflight class.

        # 3. Existing overflight updated for F2?
        # F2 is inside and has existing overflight -> nothing happens in this logic block?
        # Wait, check logic:
        # if is_in_rdc and not existing_overflight: create new
        # elif not is_in_rdc and existing_overflight: close existing
        # So for F2 (inside + existing), nothing happens.

        # 4. What if F3 had existing overflight?
        # Let's say we have F4 outside with existing overflight.

        # Let's verify result dict
        self.assertIn('F1', result['entries'])

        # 5. Verify NO lookup query inside loop
        # The code uses overflight_map.get(flight.id)
        # If there was a query inside loop it would look like Overflight.query.filter_by(...)
        self.assertFalse(mock_overflight.query.filter_by.called)

if __name__ == '__main__':
    unittest.main()
