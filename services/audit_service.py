from flask import request
from models import db, AuditLog
import json

def log_audit_event(action, user_id=None, entity_type=None, entity_id=None,
                    old_value=None, new_value=None, details=None,
                    ip_address=None, user_agent=None, severity='info'):
    """
    Centralized service for logging audit events.

    Args:
        action (str): The action performed (e.g., 'login', 'create_user', 'login_failed').
        user_id (int, optional): The ID of the user performing the action.
        entity_type (str, optional): The type of entity affected (e.g., 'user', 'invoice').
        entity_id (int, optional): The ID of the entity affected.
        old_value (str, optional): Previous value (for updates).
        new_value (str, optional): New value (for updates).
        details (dict/str, optional): Additional details about the event.
        ip_address (str, optional): IP address. Defaults to request.remote_addr if available.
        user_agent (str, optional): User agent string. Defaults to request.user_agent if available.
        severity (str, optional): Severity level ('info', 'warning', 'error', 'critical').
    """
    try:
        if ip_address is None:
            # Attempt to get IP from request context if available
            try:
                ip_address = request.remote_addr
            except RuntimeError:
                ip_address = None

        if user_agent is None:
            try:
                user_agent = request.user_agent.string[:500] if request.user_agent else None
            except RuntimeError:
                user_agent = None

        # Process details if it's a dict
        changes_str = details
        if isinstance(details, dict):
            changes_str = json.dumps(details)

        log = AuditLog(
            user_id=user_id,
            action=action,
            entity_type=entity_type,
            entity_id=entity_id,
            old_value=str(old_value) if old_value is not None else None,
            new_value=str(new_value) if new_value is not None else None,
            changes=changes_str,
            ip_address=ip_address,
            user_agent=user_agent,
            severity=severity
        )

        db.session.add(log)
        db.session.commit()

        # Notify admins for critical events
        if severity in ['critical', 'error']:
            from services.notification_service import NotificationService
            NotificationService.notify_admins(
                type='security_alert',
                title=f"Alerte Sécurité: {action}",
                message=f"Action critique détectée: {action}. Gravité: {severity}. ID Entité: {entity_id}",
                icon='fas fa-shield-alt'
            )

        return log
    except Exception as e:
        # Fallback logging to ensure we don't crash the application if audit logging fails
        print(f"Failed to create audit log: {e}")
        db.session.rollback()
        return None
