"""
/* * Nom de l'application : ATM-RDC
 * Description : Source file: test_telegram_bot.py
 * Produit de : MOA Digital Agency, www.myoneart.com
 * Fait par : Aisance KALONJI, www.aisancekalonji.com
 * Auditer par : La CyberConfiance, www.cyberconfiance.com
 */
"""
import unittest
from unittest.mock import patch, MagicMock
from flask import Flask
from models import db, TelegramSubscriber, User
from services.telegram_service import TelegramService

def create_test_app():
    app = Flask(__name__)
    app.config['TESTING'] = True
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    db.init_app(app)
    return app

class TestTelegramBot(unittest.TestCase):
    def setUp(self):
        self.app = create_test_app()
        self.app_context = self.app.app_context()
        self.app_context.push()

        # Create tables
        TelegramSubscriber.__table__.create(db.engine)
        User.__table__.create(db.engine)

    def tearDown(self):
        db.session.remove()
        db.drop_all()
        self.app_context.pop()

    @patch('services.telegram_service.bot')
    def test_send_message_security(self, mock_bot):
        # Ensure the mocked bot is treated as "enabled"
        # Since 'bot' variable in service is checked, patch replaces it.

        # 1. No subscriber -> Should not send
        TelegramService.send_message('123', 'test')
        mock_bot.send_message.assert_not_called()

        # 2. PENDING subscriber -> Should not send
        sub = TelegramSubscriber(telegram_chat_id='123', status='PENDING')
        db.session.add(sub)
        db.session.commit()

        TelegramService.send_message('123', 'test')
        mock_bot.send_message.assert_not_called()

        # 3. APPROVED subscriber -> Should send
        sub.status = 'APPROVED'
        db.session.commit()

        TelegramService.send_message('123', 'test')
        mock_bot.send_message.assert_called_with('123', 'test', parse_mode='Markdown')

        # 4. REJECTED subscriber -> Should not send
        sub.status = 'REJECTED'
        db.session.commit()
        mock_bot.reset_mock()

        TelegramService.send_message('123', 'test')
        mock_bot.send_message.assert_not_called()

    @patch('services.telegram_service.bot')
    def test_preferences(self, mock_bot):
        sub = TelegramSubscriber(telegram_chat_id='456', status='APPROVED')
        # Default prefs are set in model defaults, but we should ensure they exist
        db.session.add(sub)
        db.session.commit()

        # Reload to get defaults
        sub = TelegramSubscriber.query.get(sub.id)

        # Mock Flight
        flight = MagicMock()
        flight.callsign = "TEST01"
        flight.flight_type = "commercial"
        flight.departure_icao = "AAAA"
        flight.arrival_icao = "BBBB"

        TelegramService.notify_entry(flight)
        mock_bot.send_message.assert_called()

        # Disable preference
        # We need to assign a new dict to trigger SQLAlchemy update detection for JSON type sometimes
        prefs = dict(sub.preferences)
        prefs["notify_entry"] = False
        sub.preferences = prefs
        db.session.commit()

        mock_bot.reset_mock()
        TelegramService.notify_entry(flight)
        mock_bot.send_message.assert_not_called()

if __name__ == '__main__':
    unittest.main()
