from datetime import datetime
from .base import db

class Aircraft(db.Model):
    """
    Aircraft registry with technical specifications
    MTOW (Maximum Take-Off Weight) used for tonnage billing
    """
    __tablename__ = 'aircraft'

    id = db.Column(db.Integer, primary_key=True)
    icao24 = db.Column(db.String(10), unique=True, index=True)
    registration = db.Column(db.String(20), unique=True, index=True)
    model = db.Column(db.String(100))
    type_code = db.Column(db.String(10), index=True)
    type_designator = db.Column(db.String(10))
    manufacturer = db.Column(db.String(100))
    serial_number = db.Column(db.String(50))
    operator = db.Column(db.String(100))
    operator_iata = db.Column(db.String(3), index=True)
    operator_icao = db.Column(db.String(4))
    owner = db.Column(db.String(200))
    country = db.Column(db.String(100))
    mtow = db.Column(db.Float, default=0)
    mlw = db.Column(db.Float, default=0)
    category = db.Column(db.String(50))
    engine_type = db.Column(db.String(50))
    engine_count = db.Column(db.Integer)
    wake_category = db.Column(db.String(10))
    year_built = db.Column(db.Integer)
    is_active = db.Column(db.Boolean, default=True)
    notes = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def to_dict(self):
        return {
            'id': self.id,
            'icao24': self.icao24,
            'registration': self.registration,
            'model': self.model,
            'type_code': self.type_code,
            'manufacturer': self.manufacturer,
            'operator': self.operator,
            'operator_iata': self.operator_iata,
            'mtow': self.mtow,
            'category': self.category,
            'wake_category': self.wake_category,
            'is_active': self.is_active
        }
