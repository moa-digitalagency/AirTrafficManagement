"""
ATM-RDC Database Models
Comprehensive data models for Air Traffic Management System

Models:
- User: User accounts with RBAC
- Aircraft: Aircraft registry with MTOW
- Airport: Airports in RDC and international
- Airline: Airline companies
- Flight: Flight records
- FlightPosition: Real-time position tracking
- FlightRoute: Flight route segments
- Overflight: Airspace overflight sessions
- Landing: Landing and parking records
- Invoice: Billing invoices
- InvoiceLineItem: Invoice line items
- TariffConfig: Configurable tariffs
- AuditLog: Audit trail
- Alert: System alerts
- Notification: User notifications
- SystemConfig: System configuration
"""
from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from datetime import datetime, date
from werkzeug.security import generate_password_hash, check_password_hash
import json

db = SQLAlchemy()


class User(db.Model, UserMixin):
    """
    User accounts with role-based access control
    
    Roles:
    - superadmin: Full system access
    - supervisor: Operations management
    - controller: Flight tracking and monitoring
    - billing: Invoice and tariff management
    - auditor: Read-only access + audit logs
    - observer: Read-only dashboard access
    """
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False, index=True)
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(256), nullable=False)
    role = db.Column(db.String(50), default='observer', index=True)
    first_name = db.Column(db.String(100))
    last_name = db.Column(db.String(100))
    phone = db.Column(db.String(50))
    department = db.Column(db.String(100))
    is_active = db.Column(db.Boolean, default=True, index=True)
    is_verified = db.Column(db.Boolean, default=False)
    language = db.Column(db.String(10), default='fr')
    timezone = db.Column(db.String(50), default='Africa/Kinshasa')
    failed_login_attempts = db.Column(db.Integer, default=0)
    locked_until = db.Column(db.DateTime)
    password_changed_at = db.Column(db.DateTime)
    last_login = db.Column(db.DateTime)
    last_login_ip = db.Column(db.String(45))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)
        self.password_changed_at = datetime.utcnow()
    
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)
    
    @property
    def full_name(self):
        if self.first_name and self.last_name:
            return f"{self.first_name} {self.last_name}"
        return self.username
    
    def has_role(self, roles):
        """Check if user has one of the specified roles"""
        if isinstance(roles, str):
            roles = [roles]
        return self.role in roles
    
    def to_dict(self):
        return {
            'id': self.id,
            'username': self.username,
            'email': self.email,
            'role': self.role,
            'first_name': self.first_name,
            'last_name': self.last_name,
            'full_name': self.full_name,
            'phone': self.phone,
            'department': self.department,
            'is_active': self.is_active,
            'language': self.language,
            'last_login': self.last_login.isoformat() if self.last_login else None,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }


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
    arrival_icao = db.Column(db.String(4), index=True)
    arrival_iata = db.Column(db.String(3))
    arrival_airport = db.Column(db.String(200))
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
            'arrival_icao': self.arrival_icao,
            'arrival_airport': self.arrival_airport,
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


class TariffConfig(db.Model):
    """
    Configurable tariff rates for billing
    Supports effective dates for rate changes
    """
    __tablename__ = 'tariff_configs'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False, index=True)
    code = db.Column(db.String(50), unique=True, nullable=False, index=True)
    category = db.Column(db.String(50))
    value = db.Column(db.Float, nullable=False)
    min_value = db.Column(db.Float)
    max_value = db.Column(db.Float)
    unit = db.Column(db.String(50))
    currency = db.Column(db.String(3), default='USD')
    description = db.Column(db.Text)
    description_fr = db.Column(db.Text)
    is_active = db.Column(db.Boolean, default=True, index=True)
    is_percentage = db.Column(db.Boolean, default=False)
    effective_date = db.Column(db.Date)
    expiry_date = db.Column(db.Date)
    updated_by = db.Column(db.Integer, db.ForeignKey('users.id'))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'code': self.code,
            'category': self.category,
            'value': self.value,
            'unit': self.unit,
            'currency': self.currency,
            'description': self.description,
            'is_active': self.is_active,
            'is_percentage': self.is_percentage,
            'effective_date': self.effective_date.isoformat() if self.effective_date else None
        }


class Invoice(db.Model):
    """
    Billing invoices for overflights and landings
    Supports multiple line items and PDF generation
    """
    __tablename__ = 'invoices'
    
    id = db.Column(db.Integer, primary_key=True)
    invoice_number = db.Column(db.String(50), unique=True, nullable=False, index=True)
    reference_number = db.Column(db.String(50))
    airline_id = db.Column(db.Integer, db.ForeignKey('airlines.id'), index=True)
    invoice_type = db.Column(db.String(50), index=True)
    period_start = db.Column(db.Date)
    period_end = db.Column(db.Date)
    subtotal = db.Column(db.Float, default=0)
    discount_amount = db.Column(db.Float, default=0)
    discount_reason = db.Column(db.String(200))
    tax_rate = db.Column(db.Float, default=0.16)
    tax_amount = db.Column(db.Float, default=0)
    total_amount = db.Column(db.Float, default=0)
    currency = db.Column(db.String(3), default='USD')
    exchange_rate = db.Column(db.Float, default=1.0)
    status = db.Column(db.String(50), default='draft', index=True)
    issue_date = db.Column(db.Date, default=date.today)
    due_date = db.Column(db.Date)
    paid_date = db.Column(db.Date)
    paid_amount = db.Column(db.Float)
    payment_reference = db.Column(db.String(100))
    payment_method = db.Column(db.String(50))
    notes = db.Column(db.Text)
    internal_notes = db.Column(db.Text)
    pdf_path = db.Column(db.String(255))
    pdf_generated_at = db.Column(db.DateTime)
    sent_at = db.Column(db.DateTime)
    sent_to = db.Column(db.String(200))
    reminder_count = db.Column(db.Integer, default=0)
    last_reminder_at = db.Column(db.DateTime)
    created_by = db.Column(db.Integer, db.ForeignKey('users.id'))
    approved_by = db.Column(db.Integer, db.ForeignKey('users.id'))
    approved_at = db.Column(db.DateTime)
    cancelled_by = db.Column(db.Integer, db.ForeignKey('users.id'))
    cancelled_at = db.Column(db.DateTime)
    cancelled_reason = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, index=True)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    airline = db.relationship('Airline', backref=db.backref('invoices', lazy='dynamic'))
    overflights = db.relationship('Overflight', backref='invoice', lazy='dynamic')
    landings = db.relationship('Landing', backref='invoice', lazy='dynamic')
    line_items = db.relationship('InvoiceLineItem', backref='invoice', lazy='dynamic', cascade='all, delete-orphan')
    
    def to_dict(self):
        return {
            'id': self.id,
            'invoice_number': self.invoice_number,
            'reference_number': self.reference_number,
            'airline_id': self.airline_id,
            'airline_name': self.airline.name if self.airline else None,
            'invoice_type': self.invoice_type,
            'period_start': self.period_start.isoformat() if self.period_start else None,
            'period_end': self.period_end.isoformat() if self.period_end else None,
            'subtotal': self.subtotal,
            'discount_amount': self.discount_amount,
            'tax_rate': self.tax_rate,
            'tax_amount': self.tax_amount,
            'total_amount': self.total_amount,
            'currency': self.currency,
            'status': self.status,
            'issue_date': self.issue_date.isoformat() if self.issue_date else None,
            'due_date': self.due_date.isoformat() if self.due_date else None,
            'paid_date': self.paid_date.isoformat() if self.paid_date else None,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }
    
    def calculate_totals(self):
        """Recalculate invoice totals from line items"""
        self.subtotal = sum(item.total for item in self.line_items)
        taxable = self.subtotal - self.discount_amount
        self.tax_amount = taxable * self.tax_rate
        self.total_amount = taxable + self.tax_amount


class InvoiceLineItem(db.Model):
    """
    Individual line items on an invoice
    Supports overflights, landings, parking, and other charges
    """
    __tablename__ = 'invoice_line_items'
    
    id = db.Column(db.Integer, primary_key=True)
    invoice_id = db.Column(db.Integer, db.ForeignKey('invoices.id'), nullable=False, index=True)
    line_number = db.Column(db.Integer, default=1)
    item_type = db.Column(db.String(50))
    description = db.Column(db.String(500), nullable=False)
    reference_id = db.Column(db.Integer)
    reference_type = db.Column(db.String(50))
    flight_date = db.Column(db.Date)
    callsign = db.Column(db.String(20))
    registration = db.Column(db.String(20))
    route = db.Column(db.String(100))
    quantity = db.Column(db.Float, default=1)
    unit = db.Column(db.String(50))
    unit_price = db.Column(db.Float, default=0)
    discount = db.Column(db.Float, default=0)
    total = db.Column(db.Float, default=0)
    notes = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def to_dict(self):
        return {
            'id': self.id,
            'invoice_id': self.invoice_id,
            'line_number': self.line_number,
            'item_type': self.item_type,
            'description': self.description,
            'flight_date': self.flight_date.isoformat() if self.flight_date else None,
            'callsign': self.callsign,
            'registration': self.registration,
            'route': self.route,
            'quantity': self.quantity,
            'unit': self.unit,
            'unit_price': self.unit_price,
            'discount': self.discount,
            'total': self.total
        }
    
    def calculate_total(self):
        """Calculate line item total"""
        self.total = (self.quantity * self.unit_price) - self.discount


class AuditLog(db.Model):
    """
    Audit trail for compliance and tracking
    Records all significant system actions
    """
    __tablename__ = 'audit_logs'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), index=True)
    action = db.Column(db.String(100), nullable=False, index=True)
    action_type = db.Column(db.String(50))
    entity_type = db.Column(db.String(50), index=True)
    entity_id = db.Column(db.Integer)
    entity_name = db.Column(db.String(200))
    old_value = db.Column(db.Text)
    new_value = db.Column(db.Text)
    changes = db.Column(db.Text)
    ip_address = db.Column(db.String(45))
    user_agent = db.Column(db.String(500))
    session_id = db.Column(db.String(100))
    request_method = db.Column(db.String(10))
    request_path = db.Column(db.String(500))
    status_code = db.Column(db.Integer)
    duration_ms = db.Column(db.Integer)
    severity = db.Column(db.String(20), default='info')
    created_at = db.Column(db.DateTime, default=datetime.utcnow, index=True)
    
    user = db.relationship('User', backref=db.backref('audit_logs', lazy='dynamic'))
    
    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'username': self.user.username if self.user else None,
            'action': self.action,
            'action_type': self.action_type,
            'entity_type': self.entity_type,
            'entity_id': self.entity_id,
            'entity_name': self.entity_name,
            'ip_address': self.ip_address,
            'severity': self.severity,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }


class Alert(db.Model):
    """
    System alerts and notifications
    Used for flight alerts, emergencies, and system events
    """
    __tablename__ = 'alerts'
    
    id = db.Column(db.Integer, primary_key=True)
    alert_type = db.Column(db.String(50), nullable=False, index=True)
    category = db.Column(db.String(50))
    severity = db.Column(db.String(20), default='info', index=True)
    priority = db.Column(db.Integer, default=0)
    title = db.Column(db.String(200), nullable=False)
    message = db.Column(db.Text)
    source = db.Column(db.String(100))
    flight_id = db.Column(db.Integer, db.ForeignKey('flights.id'), index=True)
    overflight_id = db.Column(db.Integer, db.ForeignKey('overflights.id'))
    airport_icao = db.Column(db.String(4))
    latitude = db.Column(db.Float)
    longitude = db.Column(db.Float)
    extra_data = db.Column(db.Text)
    is_active = db.Column(db.Boolean, default=True, index=True)
    is_acknowledged = db.Column(db.Boolean, default=False, index=True)
    acknowledged_by = db.Column(db.Integer, db.ForeignKey('users.id'))
    acknowledged_at = db.Column(db.DateTime)
    resolved_by = db.Column(db.Integer, db.ForeignKey('users.id'))
    resolved_at = db.Column(db.DateTime)
    resolution_notes = db.Column(db.Text)
    expires_at = db.Column(db.DateTime)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, index=True)
    
    flight = db.relationship('Flight', backref=db.backref('alerts', lazy='dynamic'))
    
    def to_dict(self):
        return {
            'id': self.id,
            'alert_type': self.alert_type,
            'category': self.category,
            'severity': self.severity,
            'priority': self.priority,
            'title': self.title,
            'message': self.message,
            'source': self.source,
            'flight_id': self.flight_id,
            'airport_icao': self.airport_icao,
            'is_active': self.is_active,
            'is_acknowledged': self.is_acknowledged,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }


class Notification(db.Model):
    """
    User notifications for system events
    """
    __tablename__ = 'notifications'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, index=True)
    notification_type = db.Column(db.String(50), nullable=False)
    title = db.Column(db.String(200), nullable=False)
    message = db.Column(db.Text)
    link = db.Column(db.String(500))
    icon = db.Column(db.String(50))
    is_read = db.Column(db.Boolean, default=False, index=True)
    read_at = db.Column(db.DateTime)
    expires_at = db.Column(db.DateTime)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, index=True)
    
    user = db.relationship('User', backref=db.backref('notifications', lazy='dynamic'))
    
    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'notification_type': self.notification_type,
            'title': self.title,
            'message': self.message,
            'link': self.link,
            'is_read': self.is_read,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }


class SystemConfig(db.Model):
    """
    System-wide configuration settings
    """
    __tablename__ = 'system_configs'
    
    id = db.Column(db.Integer, primary_key=True)
    key = db.Column(db.String(100), unique=True, nullable=False, index=True)
    value = db.Column(db.Text)
    value_type = db.Column(db.String(20), default='string')
    category = db.Column(db.String(50))
    description = db.Column(db.Text)
    is_public = db.Column(db.Boolean, default=False)
    is_editable = db.Column(db.Boolean, default=True)
    updated_by = db.Column(db.Integer, db.ForeignKey('users.id'))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def to_dict(self):
        return {
            'id': self.id,
            'key': self.key,
            'value': self.value,
            'value_type': self.value_type,
            'category': self.category,
            'description': self.description,
            'is_editable': self.is_editable
        }
    
    def get_typed_value(self):
        """Get value with proper type conversion"""
        if self.value is None:
            return None
        
        if self.value_type == 'int':
            return int(self.value)
        elif self.value_type == 'float':
            return float(self.value)
        elif self.value_type == 'bool':
            return self.value.lower() in ('true', '1', 'yes')
        elif self.value_type == 'json':
            return json.loads(self.value)
        
        return self.value
