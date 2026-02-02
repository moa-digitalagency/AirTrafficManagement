"""
Module d'audit et journalisation
Air Traffic Management - RDC
"""

from datetime import datetime
from flask import request
from flask_login import current_user

from models import db, AuditLog


def log_action(action, entity_type=None, entity_id=None, old_value=None, new_value=None):
    try:
        log = AuditLog(
            user_id=current_user.id if current_user.is_authenticated else None,
            action=action,
            entity_type=entity_type,
            entity_id=entity_id,
            old_value=str(old_value) if old_value else None,
            new_value=str(new_value) if new_value else None,
            ip_address=request.remote_addr if request else None,
            user_agent=request.user_agent.string[:500] if request and request.user_agent else None,
            timestamp=datetime.utcnow()
        )
        db.session.add(log)
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        print(f"Error logging action: {e}")


def get_user_activity(user_id, limit=50):
    return AuditLog.query.filter_by(user_id=user_id).order_by(
        AuditLog.timestamp.desc()
    ).limit(limit).all()


def get_entity_history(entity_type, entity_id, limit=50):
    return AuditLog.query.filter_by(
        entity_type=entity_type,
        entity_id=entity_id
    ).order_by(AuditLog.timestamp.desc()).limit(limit).all()


def cleanup_old_logs(days=365):
    from datetime import timedelta
    cutoff = datetime.utcnow() - timedelta(days=days)
    
    old_logs = AuditLog.query.filter(AuditLog.timestamp < cutoff).delete()
    db.session.commit()
    
    return old_logs
