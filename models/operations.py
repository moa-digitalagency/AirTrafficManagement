"""
/* * Nom de l'application : ATM-RDC
 * Description : Source file: operations.py
 * Produit de : MOA Digital Agency, www.myoneart.com
 * Fait par : Aisance KALONJI, www.aisancekalonji.com
 * Auditer par : La CyberConfiance, www.cyberconfiance.com
 */
"""
from datetime import datetime
import json
import math
from .base import db

class Overflight(db.Model):
    """
    Airspace overflight session tracking
    Records entry/exit points and calculates distance for billing
    """
    __tablename__ = 'overflights'

    id = db.Column(db.Integer, primary_key=True)
    session_id = db.Column(db.String(50), unique=True, nullable=False, index=True)
    flight_id = db.Column(db.Integer, db.ForeignKey('flights.id'), index=True)
    aircraft_id = db.Column(db.Integer, db.ForeignKey('aircraft.id'), index=True)
    airline_id = db.Column(db.Integer, db.ForeignKey('airlines.id'), index=True)
    callsign = db.Column(db.String(20))
    registration = db.Column(db.String(20))
    entry_lat = db.Column(db.Float)
    entry_lon = db.Column(db.Float)
    entry_alt = db.Column(db.Float)
    entry_heading = db.Column(db.Float)
    entry_time = db.Column(db.DateTime, index=True)
    entry_point_name = db.Column(db.String(50))
    exit_lat = db.Column(db.Float)
    exit_lon = db.Column(db.Float)
    exit_alt = db.Column(db.Float)
    exit_heading = db.Column(db.Float)
    exit_time = db.Column(db.DateTime)
    exit_point_name = db.Column(db.String(50))
    duration_minutes = db.Column(db.Float)
    distance_km = db.Column(db.Float)
    distance_nm = db.Column(db.Float)
    max_altitude = db.Column(db.Float)
    min_altitude = db.Column(db.Float)
    avg_speed = db.Column(db.Float)
    trajectory_geojson = db.Column(db.Text)
    position_count = db.Column(db.Integer, default=0)
    fir_crossed = db.Column(db.String(200))
    departure_icao = db.Column(db.String(4))
    arrival_icao = db.Column(db.String(4))
    is_night = db.Column(db.Boolean, default=False)
    status = db.Column(db.String(50), default='active', index=True)
    is_billed = db.Column(db.Boolean, default=False, index=True)
    invoice_id = db.Column(db.Integer, db.ForeignKey('invoices.id'), index=True)
    billing_amount = db.Column(db.Float, default=0)
    notes = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, index=True)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    flight = db.relationship('Flight', backref=db.backref('overflights', lazy='dynamic'))
    aircraft = db.relationship('Aircraft', backref=db.backref('overflights', lazy='dynamic'))
    airline = db.relationship('Airline', backref=db.backref('overflights', lazy='dynamic'))
    positions = db.relationship('FlightPosition', backref='overflight', lazy='dynamic')

    def to_dict(self):
        return {
            'id': self.id,
            'session_id': self.session_id,
            'flight_id': self.flight_id,
            'callsign': self.callsign,
            'registration': self.registration,
            'entry_lat': self.entry_lat,
            'entry_lon': self.entry_lon,
            'entry_alt': self.entry_alt,
            'entry_time': self.entry_time.isoformat() if self.entry_time else None,
            'entry_point_name': self.entry_point_name,
            'exit_lat': self.exit_lat,
            'exit_lon': self.exit_lon,
            'exit_alt': self.exit_alt,
            'exit_time': self.exit_time.isoformat() if self.exit_time else None,
            'exit_point_name': self.exit_point_name,
            'duration_minutes': self.duration_minutes,
            'distance_km': self.distance_km,
            'distance_nm': self.distance_nm,
            'max_altitude': self.max_altitude,
            'avg_speed': self.avg_speed,
            'status': self.status,
            'is_billed': self.is_billed,
            'billing_amount': self.billing_amount,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }

    def get_trajectory(self):
        """Get trajectory as list of coordinates"""
        if self.trajectory_geojson:
            try:
                return json.loads(self.trajectory_geojson)
            except:
                pass
        return []


class Landing(db.Model):
    """
    Landing and parking records for airport billing
    Tracks landing time, parking duration, and associated charges
    """
    __tablename__ = 'landings'

    id = db.Column(db.Integer, primary_key=True)
    flight_id = db.Column(db.Integer, db.ForeignKey('flights.id'), index=True)
    aircraft_id = db.Column(db.Integer, db.ForeignKey('aircraft.id'), index=True)
    airline_id = db.Column(db.Integer, db.ForeignKey('airlines.id'), index=True)
    callsign = db.Column(db.String(20))
    registration = db.Column(db.String(20))
    airport_icao = db.Column(db.String(4), nullable=False, index=True)
    airport_name = db.Column(db.String(200))
    runway = db.Column(db.String(10))
    gate = db.Column(db.String(20))
    stand = db.Column(db.String(20))
    approach_time = db.Column(db.DateTime)
    touchdown_time = db.Column(db.DateTime)
    taxi_start = db.Column(db.DateTime)
    parking_start = db.Column(db.DateTime, index=True)
    parking_end = db.Column(db.DateTime)
    parking_duration_minutes = db.Column(db.Float)
    parking_position = db.Column(db.String(50))
    landing_weight_kg = db.Column(db.Float)
    pax_count = db.Column(db.Integer)
    cargo_kg = db.Column(db.Float)
    fuel_required = db.Column(db.Boolean, default=False)
    handling_required = db.Column(db.Boolean, default=False)
    is_night = db.Column(db.Boolean, default=False)
    is_domestic = db.Column(db.Boolean, default=False)
    is_emergency = db.Column(db.Boolean, default=False)
    landing_fee = db.Column(db.Float, default=0)
    parking_fee = db.Column(db.Float, default=0)
    handling_fee = db.Column(db.Float, default=0)
    total_fee = db.Column(db.Float, default=0)
    status = db.Column(db.String(50), default='approach', index=True)
    is_billed = db.Column(db.Boolean, default=False, index=True)
    invoice_id = db.Column(db.Integer, db.ForeignKey('invoices.id'), index=True)
    notes = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, index=True)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    flight = db.relationship('Flight', backref=db.backref('landings', lazy='dynamic'))
    aircraft = db.relationship('Aircraft', backref=db.backref('landings', lazy='dynamic'))
    airline = db.relationship('Airline', backref=db.backref('landings', lazy='dynamic'))

    def to_dict(self):
        return {
            'id': self.id,
            'flight_id': self.flight_id,
            'callsign': self.callsign,
            'registration': self.registration,
            'airport_icao': self.airport_icao,
            'airport_name': self.airport_name,
            'approach_time': self.approach_time.isoformat() if self.approach_time else None,
            'touchdown_time': self.touchdown_time.isoformat() if self.touchdown_time else None,
            'parking_start': self.parking_start.isoformat() if self.parking_start else None,
            'parking_end': self.parking_end.isoformat() if self.parking_end else None,
            'parking_duration_minutes': self.parking_duration_minutes,
            'parking_position': self.parking_position,
            'landing_fee': self.landing_fee,
            'parking_fee': self.parking_fee,
            'total_fee': self.total_fee,
            'status': self.status,
            'is_night': self.is_night,
            'is_billed': self.is_billed,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }

    def calculate_parking_fee(self, rate_per_hour=25.0, free_hours=1.0):
        """Calculate parking fee based on duration"""
        if not self.parking_duration_minutes:
            return 0

        hours = self.parking_duration_minutes / 60.0
        billable_hours = max(0, hours - free_hours)
        return billable_hours * rate_per_hour
