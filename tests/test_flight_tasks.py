import unittest
from unittest.mock import MagicMock, patch
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Mock modules to avoid real imports
mock_app_module = MagicMock()
mock_models_module = MagicMock()
mock_services_module = MagicMock()
mock_celery_app_module = MagicMock()

# We need to setup the specific attributes that are imported from these modules
mock_app = MagicMock()
mock_app_module.app = mock_app

mock_db = MagicMock()
mock_flight = MagicMock()
mock_flight_pos = MagicMock()
mock_models_module.db = mock_db
mock_models_module.Flight = mock_flight
mock_models_module.FlightPosition = mock_flight_pos

mock_fetch_data = MagicMock()
mock_services_module.fetch_external_flight_data = mock_fetch_data

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
            'celery_app': mock_celery_app_module
        })
        self.patcher.start()

        # Clear module cache to force reload with mocks
        if 'tasks.flight_tasks' in sys.modules:
            del sys.modules['tasks.flight_tasks']

        from tasks.flight_tasks import fetch_flight_positions
        self.fetch_flight_positions = fetch_flight_positions

        # Reset mocks
        mock_app.reset_mock()
        mock_db.reset_mock()
        mock_flight.reset_mock()
        mock_flight_pos.reset_mock()
        mock_fetch_data.reset_mock()

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

if __name__ == '__main__':
    unittest.main()
