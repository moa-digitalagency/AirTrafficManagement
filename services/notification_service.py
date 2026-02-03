from models import db, User, Notification
from datetime import datetime, timedelta

class NotificationService:
    @staticmethod
    def create_notification(user_id, type, title, message, link=None, icon=None):
        """
        Create a notification for a specific user.
        Avoids duplicates if a similar unread notification exists within the last hour.
        """
        # Check for duplicate/spam
        last_hour = datetime.utcnow() - timedelta(hours=1)
        existing = Notification.query.filter(
            Notification.user_id == user_id,
            Notification.notification_type == type,
            Notification.is_read == False,
            Notification.created_at >= last_hour,
            Notification.title == title
        ).first()

        if existing:
            # Update existing notification to show it happened again or just ignore
            # For now, let's update the timestamp so it stays on top, but don't spam
            existing.created_at = datetime.utcnow()
            existing.message = message # Update message in case details changed
            db.session.commit()
            return existing

        notification = Notification(
            user_id=user_id,
            notification_type=type,
            title=title,
            message=message,
            link=link,
            icon=icon
        )
        db.session.add(notification)
        db.session.commit()
        return notification

    @staticmethod
    def notify_role(role_name, type, title, message, link=None, icon=None):
        """
        Send notification to all users with a specific role.
        """
        # Using the legacy 'role' string column or role_id relationship
        # Ideally we should query by Role model if using role_id
        # Based on User model, we have both. Let's support string role for now as it's easier.

        # Find users with this role
        users = User.query.filter(
            (User.role == role_name) | (User.user_role.has(name=role_name))
        ).all()

        count = 0
        for user in users:
            NotificationService.create_notification(user.id, type, title, message, link, icon)
            count += 1
        return count

    @staticmethod
    def notify_admins(type, title, message, link=None, icon='fas fa-shield-alt'):
        """
        Send notification to all admins/superadmins.
        """
        # Notify superadmin and admins (if that role exists, usually 'superadmin' is the key)
        return NotificationService.notify_role('superadmin', type, title, message, link, icon)

    @staticmethod
    def notify_billing(type, title, message, link=None, icon='fas fa-file-invoice-dollar'):
        """
        Send notification to billing staff.
        """
        return NotificationService.notify_role('billing', type, title, message, link, icon)

    @staticmethod
    def get_unread_count(user_id):
        return Notification.query.filter_by(user_id=user_id, is_read=False).count()

    @staticmethod
    def mark_as_read(notification_id, user_id):
        notification = Notification.query.filter_by(id=notification_id, user_id=user_id).first()
        if notification:
            notification.is_read = True
            notification.read_at = datetime.utcnow()
            db.session.commit()
            return True
        return False

    @staticmethod
    def mark_all_read(user_id):
        Notification.query.filter_by(user_id=user_id, is_read=False).update(
            {Notification.is_read: True, Notification.read_at: datetime.utcnow()}
        )
        db.session.commit()
