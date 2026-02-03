"""
/* * Nom de l'application : ATM-RDC
 * Description : Source file: test_notification.py
 * Produit de : MOA Digital Agency, www.myoneart.com
 * Fait par : Aisance KALONJI, www.aisancekalonji.com
 * Auditer par : La CyberConfiance, www.cyberconfiance.com
 */
"""
import unittest
from flask import Flask
from models import db, User, Notification
from models.user import Role, Permission
from services.notification_service import NotificationService

# Create a test app factory avoiding app.py side effects
def create_test_app():
    app = Flask(__name__)
    app.config['TESTING'] = True
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['WTF_CSRF_ENABLED'] = False
    db.init_app(app)
    return app

class TestNotificationService(unittest.TestCase):
    def setUp(self):
        self.app = create_test_app()
        self.app_context = self.app.app_context()
        self.app_context.push()

        # Create tables
        Role.__table__.create(db.engine)
        Permission.__table__.create(db.engine)
        db.metadata.tables['role_permissions'].create(db.engine)
        User.__table__.create(db.engine)
        Notification.__table__.create(db.engine)

        # Create user
        self.user = User(username='testuser', email='test@example.com')
        self.user.set_password('password')
        db.session.add(self.user)
        db.session.commit()

    def tearDown(self):
        db.session.remove()
        db.drop_all()
        self.app_context.pop()

    def test_create_notification(self):
        n = NotificationService.create_notification(
            user_id=self.user.id,
            type='test',
            title='Test Title',
            message='Test Message'
        )
        self.assertIsNotNone(n.id)
        self.assertEqual(n.user_id, self.user.id)
        self.assertEqual(n.title, 'Test Title')

    def test_deduplication(self):
        # Create first
        n1 = NotificationService.create_notification(
            user_id=self.user.id,
            type='test',
            title='Same Title',
            message='Message 1'
        )

        # Create duplicate (should update n1 or return it)
        n2 = NotificationService.create_notification(
            user_id=self.user.id,
            type='test',
            title='Same Title',
            message='Message 2'
        )

        self.assertEqual(n1.id, n2.id)
        self.assertEqual(n1.message, 'Message 2') # It updates message

        # Check count
        count = Notification.query.count()
        self.assertEqual(count, 1)

    def test_mark_read(self):
        n = NotificationService.create_notification(
            user_id=self.user.id,
            type='test',
            title='Read Me',
            message='...'
        )
        self.assertFalse(n.is_read)

        NotificationService.mark_as_read(n.id, self.user.id)

        n_fetched = Notification.query.get(n.id)
        self.assertTrue(n_fetched.is_read)

if __name__ == '__main__':
    unittest.main()
