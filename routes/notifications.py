"""
/* * Nom de l'application : ATM-RDC
 * Description : Source file: notifications.py
 * Produit de : MOA Digital Agency, www.myoneart.com
 * Fait par : Aisance KALONJI, www.aisancekalonji.com
 * Auditer par : La CyberConfiance, www.cyberconfiance.com
 */
"""
from flask import Blueprint, jsonify, request
from flask_login import login_required, current_user
from services.notification_service import NotificationService
from models import Notification

notifications_bp = Blueprint('notifications', __name__)

@notifications_bp.route('/')
@login_required
def get_notifications():
    """Get user notifications"""
    limit = request.args.get('limit', 10, type=int)
    unread_only = request.args.get('unread_only', 'false') == 'true'

    query = Notification.query.filter_by(user_id=current_user.id)

    if unread_only:
        query = query.filter_by(is_read=False)

    notifications = query.order_by(Notification.created_at.desc()).limit(limit).all()

    return jsonify([n.to_dict() for n in notifications])

@notifications_bp.route('/count')
@login_required
def get_count():
    """Get unread count"""
    count = NotificationService.get_unread_count(current_user.id)
    return jsonify({'count': count})

@notifications_bp.route('/mark-read', methods=['POST'])
@login_required
def mark_read():
    """Mark notifications as read"""
    data = request.json or {}
    notification_id = data.get('id')

    if notification_id == 'all':
        NotificationService.mark_all_read(current_user.id)
        return jsonify({'success': True, 'message': 'All notifications marked as read'})

    if notification_id:
        success = NotificationService.mark_as_read(notification_id, current_user.id)
        if success:
            return jsonify({'success': True})
        return jsonify({'error': 'Notification not found'}), 404

    return jsonify({'error': 'Missing notification ID'}), 400
