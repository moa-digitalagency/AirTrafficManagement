import unittest
from unittest.mock import MagicMock, patch
import json
import sys
import os
from flask import Flask

# Add repo root to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Set DISABLE_POSTGIS to avoid geometry issues in tests
os.environ['DISABLE_POSTGIS'] = '1'

from models import db, SystemConfig, Airspace, AuditLog, User
from models.user import Role, Permission
from flask_login import LoginManager, UserMixin
from flask import Blueprint

# Create a test app factory
def create_test_app():
    app = Flask(__name__, template_folder='../templates', static_folder='../statics')
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['SECRET_KEY'] = 'test'
    app.config['WTF_CSRF_ENABLED'] = False
    db.init_app(app)

    login_manager = LoginManager()
    login_manager.init_app(app)

    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))

    @app.context_processor
    def inject_context():
        # Mock translation function 't' and 'branding'
        return {
            't': lambda x, **kwargs: x,
            'branding': {},
            'csrf_token': lambda: '',
            'url_for': lambda endpoint, **values: f'/mock/{endpoint}'
        }

    # Register dummy blueprints for navigation
    dashboard_bp = Blueprint('dashboard', __name__)
    dashboard_bp.add_url_rule('/', 'index', lambda: '')
    app.register_blueprint(dashboard_bp, url_prefix='/dashboard')

    radar_bp = Blueprint('radar', __name__)
    radar_bp.add_url_rule('/', 'index', lambda: '')
    app.register_blueprint(radar_bp, url_prefix='/radar')

    flights_bp = Blueprint('flights', __name__)
    flights_bp.add_url_rule('/', 'index', lambda: '')
    app.register_blueprint(flights_bp, url_prefix='/flights')

    analytics_bp = Blueprint('analytics', __name__)
    analytics_bp.add_url_rule('/', 'index', lambda: '')
    app.register_blueprint(analytics_bp, url_prefix='/analytics')

    invoices_bp = Blueprint('invoices', __name__)
    invoices_bp.add_url_rule('/', 'index', lambda: '')
    app.register_blueprint(invoices_bp, url_prefix='/invoices')

    notifications_bp = Blueprint('notifications', __name__)
    notifications_bp.add_url_rule('/', 'index', lambda: '')
    app.register_blueprint(notifications_bp, url_prefix='/notifications')

    auth_bp = Blueprint('auth', __name__)
    auth_bp.add_url_rule('/logout', 'logout', lambda: '')
    app.register_blueprint(auth_bp, url_prefix='/auth')

    return app

class TestAdminSettings(unittest.TestCase):
    def setUp(self):
        # Patch decorators before importing routes
        self.patcher_login = patch('flask_login.login_required', lambda x: x)
        self.patcher_login.start()

        self.patcher_role = patch('utils.decorators.role_required', lambda roles: lambda x: x)
        self.patcher_role.start()

        # Patch current_user
        self.patcher_current_user = patch('flask_login.utils._get_user')
        self.mock_get_user = self.patcher_current_user.start()

        # Setup mock user
        self.mock_user = MagicMock()
        self.mock_user.id = 1
        self.mock_user.username = 'admin'
        self.mock_user.is_authenticated = True
        self.mock_get_user.return_value = self.mock_user

        self.app = create_test_app()
        self.app_context = self.app.app_context()
        self.app_context.push()

        # Create tables
        db.create_all()

        # Ensure routes.admin is reloaded to pick up patched decorators
        if 'routes.admin' in sys.modules:
            del sys.modules['routes.admin']

        from routes.admin import admin_bp
        self.app.register_blueprint(admin_bp, url_prefix='/admin')

        self.client = self.app.test_client()

    def tearDown(self):
        db.session.remove()
        db.drop_all()
        self.app_context.pop()
        self.patcher_login.stop()
        self.patcher_role.stop()
        self.patcher_current_user.stop()
        if 'routes.admin' in sys.modules:
             del sys.modules['routes.admin']

    def test_settings_update(self):
        # Setup initial config
        config = SystemConfig(key='unit_altitude', value='ft', value_type='select', is_editable=True)
        db.session.add(config)
        db.session.commit()

        # Test POST update
        response = self.client.post('/admin/settings', data={'unit_altitude': 'm'}, follow_redirects=True)
        self.assertEqual(response.status_code, 200)

        # Verify DB update
        updated_config = SystemConfig.query.filter_by(key='unit_altitude').first()
        self.assertEqual(updated_config.value, 'm')

        # Verify Audit Log
        log = AuditLog.query.filter_by(action='update_system_config').first()
        self.assertIsNotNone(log)
        self.assertEqual(log.old_value, 'ft')
        self.assertEqual(log.new_value, 'm')

    def test_save_airspace(self):
        # Setup initial airspace
        airspace = Airspace(name='RDC Airspace', type='boundary', geom='POLYGON((0 0, 0 10, 10 10, 10 0, 0 0))')
        db.session.add(airspace)
        db.session.commit()

        # Test POST update
        geojson_payload = {
            'geojson': {
                'type': 'Feature',
                'geometry': {
                    'type': 'Polygon',
                    'coordinates': [[[0, 0], [0, 20], [20, 20], [20, 0], [0, 0]]]
                },
                'properties': {}
            }
        }

        response = self.client.post('/admin/airspace/save',
                                   data=json.dumps(geojson_payload),
                                   content_type='application/json')

        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertTrue(data['success'])

        # Verify DB update
        updated_airspace = Airspace.query.filter_by(name='RDC Airspace').first()
        # Check WKT loosely
        self.assertIn('POLYGON', updated_airspace.geom)
        self.assertIn('20', updated_airspace.geom)

if __name__ == '__main__':
    unittest.main()
