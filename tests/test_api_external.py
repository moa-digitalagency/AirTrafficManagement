
import unittest
import sys
import os
from unittest.mock import MagicMock, patch

# Disable PostGIS for SQLite tests BEFORE importing models
os.environ['DISABLE_POSTGIS'] = '1'

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import create_app
from models import db, ApiKey, User
from config.settings import Config

class TestConfig(Config):
    TESTING = True
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'
    WTF_CSRF_ENABLED = False
    REDIS_URL = 'redis://localhost:6379/0' # Dummy

class TestExternalApi(unittest.TestCase):
    def setUp(self):
        self.app = create_app(TestConfig)
        self.client = self.app.test_client()
        self.app_context = self.app.app_context()
        self.app_context.push()

        # We need to make sure db.create_all() handles the schema correctly with the env var set
        db.create_all()

        # Create Dummy User
        self.user = User(username='admin', email='admin@test.com', password_hash='hash')
        db.session.add(self.user)
        db.session.commit()

        # Create API Key
        self.api_key = ApiKey(
            name="Test Key",
            key="sk_test_12345",
            status="active",
            rate_limit=5,
            created_by=self.user.id
        )
        db.session.add(self.api_key)
        db.session.commit()

    def tearDown(self):
        db.session.remove()
        db.drop_all()
        self.app_context.pop()

    def test_missing_key(self):
        response = self.client.get('/api/v1/external/surveillance/flights')
        self.assertEqual(response.status_code, 401)

    def test_valid_key(self):
        # We assume Redis might fail but fail open, or we mock it.
        # Let's mock it to be safe and avoid "Connection refused" logs if no Redis.
        with patch('security.api_auth.get_redis_client') as mock_get_redis:
            mock_redis = MagicMock()
            mock_get_redis.return_value = mock_redis
            mock_redis.incr.return_value = 1

            response = self.client.get('/api/v1/external/billing/summary', headers={'X-API-KEY': 'sk_test_12345'})
            self.assertEqual(response.status_code, 200)

    def test_rate_limit(self):
        with patch('security.api_auth.get_redis_client') as mock_get_redis:
            mock_redis = MagicMock()
            mock_get_redis.return_value = mock_redis

            # Simulate over limit
            mock_redis.incr.return_value = 6

            response = self.client.get('/api/v1/external/billing/summary', headers={'X-API-KEY': 'sk_test_12345'})
            self.assertEqual(response.status_code, 429)

if __name__ == '__main__':
    unittest.main()
