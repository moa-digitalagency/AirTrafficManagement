from datetime import datetime
from .base import db

class Airline(db.Model):
    """
    Airline company database for billing and reporting
    """
    __tablename__ = 'airlines'

    id = db.Column(db.Integer, primary_key=True)
    iata_code = db.Column(db.String(3), unique=True, index=True)
    icao_code = db.Column(db.String(4), unique=True, index=True)
    name = db.Column(db.String(200), nullable=False)
    name_local = db.Column(db.String(200))
    callsign = db.Column(db.String(50))
    country = db.Column(db.String(100))
    country_code = db.Column(db.String(3))
    headquarters = db.Column(db.String(200))
    address = db.Column(db.Text)
    city = db.Column(db.String(100))
    postal_code = db.Column(db.String(20))
    email = db.Column(db.String(120))
    phone = db.Column(db.String(50))
    fax = db.Column(db.String(50))
    website = db.Column(db.String(200))
    contact_name = db.Column(db.String(100))
    contact_email = db.Column(db.String(120))
    tax_id = db.Column(db.String(50))
    billing_currency = db.Column(db.String(3), default='USD')
    payment_terms_days = db.Column(db.Integer, default=30)
    credit_limit = db.Column(db.Float, default=0)
    current_balance = db.Column(db.Float, default=0)
    is_domestic = db.Column(db.Boolean, default=False)
    is_active = db.Column(db.Boolean, default=True)
    notes = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def to_dict(self):
        return {
            'id': self.id,
            'iata_code': self.iata_code,
            'icao_code': self.icao_code,
            'name': self.name,
            'callsign': self.callsign,
            'country': self.country,
            'email': self.email,
            'phone': self.phone,
            'website': self.website,
            'billing_currency': self.billing_currency,
            'payment_terms_days': self.payment_terms_days,
            'is_active': self.is_active
        }
