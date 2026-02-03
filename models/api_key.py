"""
/* * Nom de l'application : ATM-RDC
 * Description : Source file: api_key.py
 * Produit de : MOA Digital Agency, www.myoneart.com
 * Fait par : Aisance KALONJI, www.aisancekalonji.com
 * Auditer par : La CyberConfiance, www.cyberconfiance.com
 */
"""
from datetime import datetime
import json
from .base import db

class ApiKey(db.Model):
    """
    API Keys for external system access
    Secured via UUID token and Role-Based Access
    """
    __tablename__ = 'api_keys'

    id = db.Column(db.Integer, primary_key=True)
    key = db.Column(db.String(64), unique=True, nullable=False, index=True)
    name = db.Column(db.String(100), nullable=False)
    status = db.Column(db.String(20), default='active', index=True)  # active, suspended, revoked
    role = db.Column(db.String(50), default='external_audit')
    permissions = db.Column(db.Text)  # Stored as JSON string
    rate_limit = db.Column(db.Integer, default=60)  # Requests per minute

    created_by = db.Column(db.Integer, db.ForeignKey('users.id'))
    last_used_at = db.Column(db.DateTime)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    creator = db.relationship('User', backref=db.backref('created_api_keys', lazy='dynamic'))

    def set_permissions(self, perms_list):
        self.permissions = json.dumps(perms_list)

    def get_permissions(self):
        if not self.permissions:
            return []
        try:
            return json.loads(self.permissions)
        except:
            return []

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'key_masked': f"{self.key[:4]}...{self.key[-4:]}" if self.key and len(self.key) > 8 else "***",
            'status': self.status,
            'role': self.role,
            'permissions': self.get_permissions(),
            'rate_limit': self.rate_limit,
            'last_used_at': self.last_used_at.isoformat() if self.last_used_at else None,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }
