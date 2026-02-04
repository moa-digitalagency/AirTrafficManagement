"""
/* * Nom de l'application : ATM-RDC
 * Description : Source file: telegram.py
 * Produit de : MOA Digital Agency, www.myoneart.com
 * Fait par : Aisance KALONJI, www.aisancekalonji.com
 * Auditer par : La CyberConfiance, www.cyberconfiance.com
 */
"""
from datetime import datetime
from .base import db

class TelegramSubscriber(db.Model):
    """
    Telegram subscribers for notification system.
    """
    __tablename__ = 'telegram_subscribers'

    id = db.Column(db.Integer, primary_key=True)
    telegram_chat_id = db.Column(db.String(50), unique=True, nullable=False, index=True)
    username = db.Column(db.String(100))
    first_name = db.Column(db.String(100))

    # Status: 'PENDING', 'APPROVED', 'REJECTED', 'REVOKED'
    status = db.Column(db.String(20), default='PENDING', index=True)

    request_date = db.Column(db.DateTime, default=datetime.utcnow)
    approval_date = db.Column(db.DateTime)

    verification_code = db.Column(db.String(6))
    code_generated_at = db.Column(db.DateTime)

    approved_by_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    approved_by = db.relationship('User', backref='approved_telegram_subscribers')

    # Preferences stored as JSON
    # Structure:
    # {
    #   "notify_entry": bool,
    #   "notify_exit": bool,
    #   "notify_alerts": bool,
    #   "notify_daily_report": bool,
    #   "notify_billing": bool
    # }
    preferences = db.Column(db.JSON, default=lambda: {
        "notify_entry": True,
        "notify_exit": True,
        "notify_alerts": True,
        "notify_daily_report": False,
        "notify_billing": True
    })

    def to_dict(self):
        return {
            'id': self.id,
            'telegram_chat_id': self.telegram_chat_id,
            'username': self.username,
            'first_name': self.first_name,
            'status': self.status,
            'request_date': self.request_date.isoformat() if self.request_date else None,
            'approval_date': self.approval_date.isoformat() if self.approval_date else None,
            'preferences': self.preferences
        }
