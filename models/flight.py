from datetime import datetime, date
from .base import db

class Flight(db.Model):
    """
    Flight records with routing and status information
    Linked to aircraft, overflights, and landings
    """
    __tablename__ = 'flights'

    id = db.Column(db.Integer, primary_key=True)
    callsign = db.Column(db.String(20), nullable=False, index=True)
    flight_number = db.Column(db.String(20), index=True)
    flight_iata = db.Column(db.String(10))
    flight_icao = db.Column(db.String(10))
    aircraft_id = db.Column(db.Integer, db.ForeignKey('aircraft.id'), index=True)
    airline_id = db.Column(db.Integer, db.ForeignKey('airlines.id'), index=True)
    departure_icao = db.Column(db.String(4), index=True)
    departure_iata = db.Column(db.String(3))
    departure_airport = db.Column(db.String(200))
    departure_terminal = db.Column(db.String(10))
    departure_gate = db.Column(db.String(10))
    departure_timezone = db.Column(db.String(50))
    arrival_icao = db.Column(db.String(4), index=True)
    arrival_iata = db.Column(db.String(3))
    arrival_airport = db.Column(db.String(200))
    arrival_terminal = db.Column(db.String(10))
    arrival_gate = db.Column(db.String(10))
    arrival_baggage = db.Column(db.String(20))
    arrival_timezone = db.Column(db.String(50))
    codeshared_airline_name = db.Column(db.String(200))
    codeshared_flight_number = db.Column(db.String(20))
    scheduled_departure = db.Column(db.DateTime)
    scheduled_arrival = db.Column(db.DateTime)
    estimated_departure = db.Column(db.DateTime)
    estimated_arrival = db.Column(db.DateTime)
    actual_departure = db.Column(db.DateTime)
    actual_arrival = db.Column(db.DateTime)
    departure_delay_min = db.Column(db.Integer, default=0)
    arrival_delay_min = db.Column(db.Integer, default=0)
    flight_status = db.Column(db.String(50), default='scheduled', index=True)
    flight_type = db.Column(db.String(50))
    flight_date = db.Column(db.Date, index=True)
    is_domestic = db.Column(db.Boolean, default=False)
    is_cargo = db.Column(db.Boolean, default=False)
    route_distance_km = db.Column(db.Float)
    route_duration_min = db.Column(db.Float)
    filed_altitude = db.Column(db.Integer)
    filed_speed = db.Column(db.Integer)
    remarks = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, index=True)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    aircraft = db.relationship('Aircraft', backref=db.backref('flights', lazy='dynamic'))
    airline = db.relationship('Airline', backref=db.backref('flights', lazy='dynamic'))

    def to_dict(self):
        return {
            'id': self.id,
            'callsign': self.callsign,
            'flight_number': self.flight_number,
            'flight_iata': self.flight_iata,
            'aircraft_id': self.aircraft_id,
            'airline_id': self.airline_id,
            'departure_icao': self.departure_icao,
            'departure_airport': self.departure_airport,
            'departure_terminal': self.departure_terminal,
            'departure_gate': self.departure_gate,
            'arrival_icao': self.arrival_icao,
            'arrival_airport': self.arrival_airport,
            'arrival_terminal': self.arrival_terminal,
            'arrival_gate': self.arrival_gate,
            'scheduled_departure': self.scheduled_departure.isoformat() if self.scheduled_departure else None,
            'scheduled_arrival': self.scheduled_arrival.isoformat() if self.scheduled_arrival else None,
            'actual_departure': self.actual_departure.isoformat() if self.actual_departure else None,
            'actual_arrival': self.actual_arrival.isoformat() if self.actual_arrival else None,
            'flight_status': self.flight_status,
            'flight_type': self.flight_type,
            'is_domestic': self.is_domestic,
            'route_distance_km': self.route_distance_km,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }


class FlightPosition(db.Model):
    """
    Real-time flight position tracking
    Stores position history for trajectory visualization
    """
    __tablename__ = 'flight_positions'

    id = db.Column(db.Integer, primary_key=True)
    flight_id = db.Column(db.Integer, db.ForeignKey('flights.id'), index=True)
    overflight_id = db.Column(db.Integer, db.ForeignKey('overflights.id'), index=True)
    icao24 = db.Column(db.String(10), index=True)
    callsign = db.Column(db.String(20))
    latitude = db.Column(db.Float, nullable=False)
    longitude = db.Column(db.Float, nullable=False)
    altitude = db.Column(db.Float)
    altitude_geo = db.Column(db.Float)
    ground_speed = db.Column(db.Float)
    true_track = db.Column(db.Float)
    heading = db.Column(db.Float)
    vertical_rate = db.Column(db.Float)
    squawk = db.Column(db.String(4))
    on_ground = db.Column(db.Boolean, default=False)
    is_in_rdc = db.Column(db.Boolean, default=False, index=True)
    source = db.Column(db.String(50))
    timestamp = db.Column(db.DateTime, default=datetime.utcnow, index=True)

    flight = db.relationship('Flight', backref=db.backref('positions', lazy='dynamic'))

    def to_dict(self):
        return {
            'id': self.id,
            'flight_id': self.flight_id,
            'callsign': self.callsign,
            'latitude': self.latitude,
            'longitude': self.longitude,
            'altitude': self.altitude,
            'ground_speed': self.ground_speed,
            'heading': self.heading,
            'vertical_rate': self.vertical_rate,
            'squawk': self.squawk,
            'on_ground': self.on_ground,
            'is_in_rdc': self.is_in_rdc,
            'timestamp': self.timestamp.isoformat() if self.timestamp else None
        }


class FlightRoute(db.Model):
    """
    Flight route segments for detailed routing analysis
    """
    __tablename__ = 'flight_routes'

    id = db.Column(db.Integer, primary_key=True)
    flight_id = db.Column(db.Integer, db.ForeignKey('flights.id'), index=True)
    sequence = db.Column(db.Integer, default=0)
    waypoint_name = db.Column(db.String(20))
    waypoint_type = db.Column(db.String(20))
    latitude = db.Column(db.Float)
    longitude = db.Column(db.Float)
    altitude_ft = db.Column(db.Integer)
    airway = db.Column(db.String(20))
    distance_from_prev_nm = db.Column(db.Float)
    ete_from_prev_min = db.Column(db.Float)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    flight = db.relationship('Flight', backref=db.backref('route_points', lazy='dynamic'))

    def to_dict(self):
        return {
            'id': self.id,
            'flight_id': self.flight_id,
            'sequence': self.sequence,
            'waypoint_name': self.waypoint_name,
            'latitude': self.latitude,
            'longitude': self.longitude,
            'altitude_ft': self.altitude_ft,
            'airway': self.airway
        }
