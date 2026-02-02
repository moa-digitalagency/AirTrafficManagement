from datetime import datetime
import json
from .base import db

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
