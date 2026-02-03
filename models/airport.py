"""
/* * Nom de l'application : ATM-RDC
 * Description : Source file: airport.py
 * Produit de : MOA Digital Agency, www.myoneart.com
 * Fait par : Aisance KALONJI, www.aisancekalonji.com
 * Auditer par : La CyberConfiance, www.cyberconfiance.com
 */
"""
from datetime import datetime
from .base import db

class Airport(db.Model):
    """
    Airport database for RDC and international airports
    Used for route detection and landing billing
    """
    __tablename__ = 'airports'

    id = db.Column(db.Integer, primary_key=True)
    icao_code = db.Column(db.String(4), unique=True, nullable=False, index=True)
    iata_code = db.Column(db.String(3), index=True)
    name = db.Column(db.String(200), nullable=False)
    name_local = db.Column(db.String(200))
    city = db.Column(db.String(100))
    province = db.Column(db.String(100))
    country = db.Column(db.String(100), default='RDC')
    country_code = db.Column(db.String(3), default='CD')
    latitude = db.Column(db.Float, nullable=False)
    longitude = db.Column(db.Float, nullable=False)
    elevation_ft = db.Column(db.Float)
    elevation_m = db.Column(db.Float)
    timezone = db.Column(db.String(50), default='Africa/Kinshasa')
    utc_offset = db.Column(db.Float, default=1.0)
    runway_length_m = db.Column(db.Float)
    runway_surface = db.Column(db.String(50))
    has_customs = db.Column(db.Boolean, default=False)
    has_fuel = db.Column(db.Boolean, default=False)
    has_ils = db.Column(db.Boolean, default=False)
    is_international = db.Column(db.Boolean, default=False)
    is_domestic = db.Column(db.Boolean, default=True)
    is_military = db.Column(db.Boolean, default=False)
    category = db.Column(db.String(50))
    status = db.Column(db.String(20), default='open')
    notes = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def to_dict(self):
        return {
            'id': self.id,
            'icao_code': self.icao_code,
            'iata_code': self.iata_code,
            'name': self.name,
            'city': self.city,
            'province': self.province,
            'country': self.country,
            'latitude': self.latitude,
            'longitude': self.longitude,
            'elevation_ft': self.elevation_ft,
            'timezone': self.timezone,
            'is_international': self.is_international,
            'is_domestic': self.is_domestic,
            'status': self.status
        }
