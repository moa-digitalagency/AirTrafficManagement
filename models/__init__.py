from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash

db = SQLAlchemy()


class User(db.Model, UserMixin):
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
    role = db.Column(db.String(50), default='observer')
    first_name = db.Column(db.String(100))
    last_name = db.Column(db.String(100))
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    last_login = db.Column(db.DateTime)
    
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)
    
    def to_dict(self):
        return {
            'id': self.id,
            'username': self.username,
            'email': self.email,
            'role': self.role,
            'first_name': self.first_name,
            'last_name': self.last_name,
            'is_active': self.is_active,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }


class Aircraft(db.Model):
    __tablename__ = 'aircraft'
    
    id = db.Column(db.Integer, primary_key=True)
    icao_code = db.Column(db.String(10), unique=True, nullable=False)
    registration = db.Column(db.String(20))
    model = db.Column(db.String(100))
    type_code = db.Column(db.String(10))
    operator = db.Column(db.String(100))
    operator_iata = db.Column(db.String(5))
    mtow = db.Column(db.Float, default=0)
    category = db.Column(db.String(50))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def to_dict(self):
        return {
            'id': self.id,
            'icao_code': self.icao_code,
            'registration': self.registration,
            'model': self.model,
            'type_code': self.type_code,
            'operator': self.operator,
            'operator_iata': self.operator_iata,
            'mtow': self.mtow,
            'category': self.category
        }


class Airport(db.Model):
    __tablename__ = 'airports'
    
    id = db.Column(db.Integer, primary_key=True)
    icao_code = db.Column(db.String(4), unique=True, nullable=False)
    iata_code = db.Column(db.String(3))
    name = db.Column(db.String(200), nullable=False)
    city = db.Column(db.String(100))
    country = db.Column(db.String(100), default='RDC')
    latitude = db.Column(db.Float)
    longitude = db.Column(db.Float)
    elevation = db.Column(db.Float)
    timezone = db.Column(db.String(50))
    is_domestic = db.Column(db.Boolean, default=True)
    status = db.Column(db.String(20), default='open')
    
    def to_dict(self):
        return {
            'id': self.id,
            'icao_code': self.icao_code,
            'iata_code': self.iata_code,
            'name': self.name,
            'city': self.city,
            'country': self.country,
            'latitude': self.latitude,
            'longitude': self.longitude,
            'elevation': self.elevation,
            'is_domestic': self.is_domestic,
            'status': self.status
        }


class Flight(db.Model):
    __tablename__ = 'flights'
    
    id = db.Column(db.Integer, primary_key=True)
    callsign = db.Column(db.String(20), nullable=False)
    flight_number = db.Column(db.String(20))
    aircraft_id = db.Column(db.Integer, db.ForeignKey('aircraft.id'))
    departure_icao = db.Column(db.String(4))
    arrival_icao = db.Column(db.String(4))
    scheduled_departure = db.Column(db.DateTime)
    scheduled_arrival = db.Column(db.DateTime)
    actual_departure = db.Column(db.DateTime)
    actual_arrival = db.Column(db.DateTime)
    flight_status = db.Column(db.String(50), default='scheduled')
    flight_type = db.Column(db.String(50))
    is_domestic = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    aircraft = db.relationship('Aircraft', backref='flights')
    
    def to_dict(self):
        return {
            'id': self.id,
            'callsign': self.callsign,
            'flight_number': self.flight_number,
            'aircraft_id': self.aircraft_id,
            'departure_icao': self.departure_icao,
            'arrival_icao': self.arrival_icao,
            'scheduled_departure': self.scheduled_departure.isoformat() if self.scheduled_departure else None,
            'scheduled_arrival': self.scheduled_arrival.isoformat() if self.scheduled_arrival else None,
            'flight_status': self.flight_status,
            'flight_type': self.flight_type,
            'is_domestic': self.is_domestic
        }


class FlightPosition(db.Model):
    __tablename__ = 'flight_positions'
    
    id = db.Column(db.Integer, primary_key=True)
    flight_id = db.Column(db.Integer, db.ForeignKey('flights.id'))
    latitude = db.Column(db.Float, nullable=False)
    longitude = db.Column(db.Float, nullable=False)
    altitude = db.Column(db.Float)
    ground_speed = db.Column(db.Float)
    heading = db.Column(db.Float)
    vertical_rate = db.Column(db.Float)
    squawk = db.Column(db.String(4))
    is_in_rdc = db.Column(db.Boolean, default=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    
    flight = db.relationship('Flight', backref='positions')


class Overflight(db.Model):
    __tablename__ = 'overflights'
    
    id = db.Column(db.Integer, primary_key=True)
    session_id = db.Column(db.String(50), unique=True, nullable=False)
    flight_id = db.Column(db.Integer, db.ForeignKey('flights.id'))
    aircraft_id = db.Column(db.Integer, db.ForeignKey('aircraft.id'))
    entry_lat = db.Column(db.Float)
    entry_lon = db.Column(db.Float)
    entry_alt = db.Column(db.Float)
    entry_time = db.Column(db.DateTime)
    exit_lat = db.Column(db.Float)
    exit_lon = db.Column(db.Float)
    exit_alt = db.Column(db.Float)
    exit_time = db.Column(db.DateTime)
    duration_minutes = db.Column(db.Float)
    distance_km = db.Column(db.Float)
    trajectory_geojson = db.Column(db.Text)
    status = db.Column(db.String(50), default='active')
    is_billed = db.Column(db.Boolean, default=False)
    invoice_id = db.Column(db.Integer, db.ForeignKey('invoices.id'))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    flight = db.relationship('Flight', backref='overflights')
    aircraft = db.relationship('Aircraft', backref='overflights')
    
    def to_dict(self):
        return {
            'id': self.id,
            'session_id': self.session_id,
            'flight_id': self.flight_id,
            'entry_lat': self.entry_lat,
            'entry_lon': self.entry_lon,
            'entry_time': self.entry_time.isoformat() if self.entry_time else None,
            'exit_lat': self.exit_lat,
            'exit_lon': self.exit_lon,
            'exit_time': self.exit_time.isoformat() if self.exit_time else None,
            'duration_minutes': self.duration_minutes,
            'distance_km': self.distance_km,
            'status': self.status,
            'is_billed': self.is_billed
        }


class Landing(db.Model):
    __tablename__ = 'landings'
    
    id = db.Column(db.Integer, primary_key=True)
    flight_id = db.Column(db.Integer, db.ForeignKey('flights.id'))
    aircraft_id = db.Column(db.Integer, db.ForeignKey('aircraft.id'))
    airport_icao = db.Column(db.String(4), nullable=False)
    landing_time = db.Column(db.DateTime)
    parking_start = db.Column(db.DateTime)
    parking_end = db.Column(db.DateTime)
    parking_duration_minutes = db.Column(db.Float)
    is_night = db.Column(db.Boolean, default=False)
    is_billed = db.Column(db.Boolean, default=False)
    invoice_id = db.Column(db.Integer, db.ForeignKey('invoices.id'))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    flight = db.relationship('Flight', backref='landings')
    aircraft = db.relationship('Aircraft', backref='landings')
    
    def to_dict(self):
        return {
            'id': self.id,
            'flight_id': self.flight_id,
            'airport_icao': self.airport_icao,
            'landing_time': self.landing_time.isoformat() if self.landing_time else None,
            'parking_start': self.parking_start.isoformat() if self.parking_start else None,
            'parking_end': self.parking_end.isoformat() if self.parking_end else None,
            'parking_duration_minutes': self.parking_duration_minutes,
            'is_night': self.is_night,
            'is_billed': self.is_billed
        }


class Airline(db.Model):
    __tablename__ = 'airlines'
    
    id = db.Column(db.Integer, primary_key=True)
    iata_code = db.Column(db.String(3), unique=True)
    icao_code = db.Column(db.String(4))
    name = db.Column(db.String(200), nullable=False)
    country = db.Column(db.String(100))
    address = db.Column(db.Text)
    email = db.Column(db.String(120))
    phone = db.Column(db.String(50))
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def to_dict(self):
        return {
            'id': self.id,
            'iata_code': self.iata_code,
            'icao_code': self.icao_code,
            'name': self.name,
            'country': self.country,
            'email': self.email,
            'is_active': self.is_active
        }


class TariffConfig(db.Model):
    __tablename__ = 'tariff_configs'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    code = db.Column(db.String(50), unique=True, nullable=False)
    value = db.Column(db.Float, nullable=False)
    unit = db.Column(db.String(50))
    description = db.Column(db.Text)
    is_active = db.Column(db.Boolean, default=True)
    effective_date = db.Column(db.Date)
    updated_by = db.Column(db.Integer, db.ForeignKey('users.id'))
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'code': self.code,
            'value': self.value,
            'unit': self.unit,
            'description': self.description,
            'is_active': self.is_active
        }


class Invoice(db.Model):
    __tablename__ = 'invoices'
    
    id = db.Column(db.Integer, primary_key=True)
    invoice_number = db.Column(db.String(50), unique=True, nullable=False)
    airline_id = db.Column(db.Integer, db.ForeignKey('airlines.id'))
    invoice_type = db.Column(db.String(50))
    subtotal = db.Column(db.Float, default=0)
    tax_amount = db.Column(db.Float, default=0)
    total_amount = db.Column(db.Float, default=0)
    currency = db.Column(db.String(3), default='USD')
    status = db.Column(db.String(50), default='draft')
    due_date = db.Column(db.Date)
    paid_date = db.Column(db.Date)
    notes = db.Column(db.Text)
    pdf_path = db.Column(db.String(255))
    created_by = db.Column(db.Integer, db.ForeignKey('users.id'))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    airline = db.relationship('Airline', backref='invoices')
    overflights = db.relationship('Overflight', backref='invoice')
    landings = db.relationship('Landing', backref='invoice')
    
    def to_dict(self):
        return {
            'id': self.id,
            'invoice_number': self.invoice_number,
            'airline_id': self.airline_id,
            'invoice_type': self.invoice_type,
            'subtotal': self.subtotal,
            'tax_amount': self.tax_amount,
            'total_amount': self.total_amount,
            'currency': self.currency,
            'status': self.status,
            'due_date': self.due_date.isoformat() if self.due_date else None,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }


class AuditLog(db.Model):
    __tablename__ = 'audit_logs'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    action = db.Column(db.String(100), nullable=False)
    entity_type = db.Column(db.String(50))
    entity_id = db.Column(db.Integer)
    old_value = db.Column(db.Text)
    new_value = db.Column(db.Text)
    ip_address = db.Column(db.String(45))
    user_agent = db.Column(db.String(500))
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    
    user = db.relationship('User', backref='audit_logs')
    
    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'action': self.action,
            'entity_type': self.entity_type,
            'entity_id': self.entity_id,
            'ip_address': self.ip_address,
            'timestamp': self.timestamp.isoformat() if self.timestamp else None
        }


class Alert(db.Model):
    __tablename__ = 'alerts'
    
    id = db.Column(db.Integer, primary_key=True)
    alert_type = db.Column(db.String(50), nullable=False)
    severity = db.Column(db.String(20), default='info')
    title = db.Column(db.String(200))
    message = db.Column(db.Text)
    flight_id = db.Column(db.Integer, db.ForeignKey('flights.id'))
    is_acknowledged = db.Column(db.Boolean, default=False)
    acknowledged_by = db.Column(db.Integer, db.ForeignKey('users.id'))
    acknowledged_at = db.Column(db.DateTime)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    flight = db.relationship('Flight', backref='alerts')
    
    def to_dict(self):
        return {
            'id': self.id,
            'alert_type': self.alert_type,
            'severity': self.severity,
            'title': self.title,
            'message': self.message,
            'flight_id': self.flight_id,
            'is_acknowledged': self.is_acknowledged,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }
