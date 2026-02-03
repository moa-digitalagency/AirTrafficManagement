"""
/* * Nom de l'application : ATM-RDC
 * Description : Source file: user.py
 * Produit de : MOA Digital Agency, www.myoneart.com
 * Fait par : Aisance KALONJI, www.aisancekalonji.com
 * Auditer par : La CyberConfiance, www.cyberconfiance.com
 */
"""
from datetime import datetime
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from .base import db

# Association table for Role-Permission many-to-many relationship
role_permissions = db.Table('role_permissions',
    db.Column('role_id', db.Integer, db.ForeignKey('roles.id'), primary_key=True),
    db.Column('permission_id', db.Integer, db.ForeignKey('permissions.id'), primary_key=True)
)

class Permission(db.Model):
    """
    Granular permissions for resources and actions
    Format: resource:action (e.g., flights:read, invoices:create)
    """
    __tablename__ = 'permissions'

    id = db.Column(db.Integer, primary_key=True)
    resource = db.Column(db.String(50), nullable=False)
    action = db.Column(db.String(50), nullable=False)
    description = db.Column(db.String(200))

    def __repr__(self):
        return f"{self.resource}:{self.action}"

class Role(db.Model):
    """
    User roles grouping multiple permissions
    """
    __tablename__ = 'roles'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), unique=True, nullable=False)
    description = db.Column(db.String(200))
    is_system = db.Column(db.Boolean, default=False) # System roles cannot be deleted
    permissions = db.relationship('Permission', secondary=role_permissions, lazy='subquery',
        backref=db.backref('roles', lazy=True))

    def has_permission(self, resource, action):
        for perm in self.permissions:
            if perm.resource == '*' and perm.action == '*':
                return True
            if perm.resource == resource and (perm.action == action or perm.action == '*'):
                return True
        return False

class User(db.Model, UserMixin):
    """
    User accounts with role-based access control
    """
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False, index=True)
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(256), nullable=False)

    # Legacy string role, kept for backward compatibility during migration
    # but we should move to using role_id
    role = db.Column(db.String(50), default='observer', index=True)

    role_id = db.Column(db.Integer, db.ForeignKey('roles.id'))
    user_role = db.relationship('Role', backref='users')

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

        # Check against relationship first
        if self.user_role:
            if self.user_role.name in roles:
                return True

        # Fallback to string column
        return self.role in roles

    def has_permission(self, resource, action):
        """Check if user has specific permission"""
        if self.user_role:
            return self.user_role.has_permission(resource, action)

        # Fallback for legacy users without role_id
        # Map legacy roles to implicit permissions (simplified)
        if self.role == 'superadmin':
            return True
        return False

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
