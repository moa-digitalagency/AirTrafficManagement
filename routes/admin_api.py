"""
/* * Nom de l'application : ATM-RDC
 * Description : Source file: admin_api.py
 * Produit de : MOA Digital Agency, www.myoneart.com
 * Fait par : Aisance KALONJI, www.aisancekalonji.com
 * Auditer par : La CyberConfiance, www.cyberconfiance.com
 */
"""
from flask import Blueprint, render_template, request, flash, redirect, url_for, jsonify
from flask_login import login_required, current_user
from models import db, ApiKey, AuditLog
from uuid import uuid4
from datetime import datetime

admin_api_bp = Blueprint('admin_api', __name__)

@admin_api_bp.route('/settings/api-keys')
@login_required
def list_api_keys():
    # Simple role check supporting both legacy role string and role object
    is_superadmin = False
    if hasattr(current_user, 'has_role'):
        is_superadmin = current_user.has_role('superadmin')
    elif hasattr(current_user, 'role'):
         is_superadmin = current_user.role == 'superadmin'

    if not is_superadmin:
        flash('Accès non autorisé', 'danger')
        return redirect(url_for('dashboard.index'))

    keys = ApiKey.query.order_by(ApiKey.created_at.desc()).all()
    return render_template('admin/api_keys.html', keys=keys)

@admin_api_bp.route('/settings/api-keys/create', methods=['POST'])
@login_required
def create_api_key():
    is_superadmin = False
    if hasattr(current_user, 'has_role'):
        is_superadmin = current_user.has_role('superadmin')
    elif hasattr(current_user, 'role'):
         is_superadmin = current_user.role == 'superadmin'

    if not is_superadmin:
        return jsonify({'error': 'Unauthorized'}), 403

    name = request.form.get('name')
    rate_limit = request.form.get('rate_limit', type=int, default=60)

    if not name:
        return jsonify({'error': 'Le nom est requis'}), 400

    # Generate Key
    raw_key = f"sk_{str(uuid4()).replace('-', '')}"

    new_key = ApiKey(
        name=name,
        key=raw_key,
        rate_limit=rate_limit,
        created_by=current_user.id,
        status='active',
        role='external_audit',
        permissions='["read:surveillance", "read:billing"]' # Default permissions
    )

    try:
        db.session.add(new_key)

        # Log Audit
        audit = AuditLog(
            user_id=current_user.id,
            action='create_api_key',
            action_type='create',
            entity_type='api_key',
            entity_name=name,
            changes=f"Created API Key for {name} with limit {rate_limit}",
            ip_address=request.remote_addr,
            created_at=datetime.utcnow()
        )
        db.session.add(audit)
        db.session.commit()

        return jsonify({
            'success': True,
            'key': raw_key,
            'message': 'Clé API générée avec succès'
        })

    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@admin_api_bp.route('/settings/api-keys/<int:key_id>/action', methods=['POST'])
@login_required
def action_api_key(key_id):
    is_superadmin = False
    if hasattr(current_user, 'has_role'):
        is_superadmin = current_user.has_role('superadmin')
    elif hasattr(current_user, 'role'):
         is_superadmin = current_user.role == 'superadmin'

    if not is_superadmin:
        return jsonify({'error': 'Unauthorized'}), 403

    key = ApiKey.query.get_or_404(key_id)
    action = request.form.get('action') # suspend, reactivate, revoke

    try:
        old_status = key.status
        if action == 'suspend':
            key.status = 'suspended'
        elif action == 'reactivate':
            key.status = 'active'
        elif action == 'revoke':
            key.status = 'revoked'
        else:
            return jsonify({'error': 'Action invalide'}), 400

        audit = AuditLog(
            user_id=current_user.id,
            action=f'{action}_api_key',
            action_type='update',
            entity_type='api_key',
            entity_id=key.id,
            entity_name=key.name,
            old_value=old_status,
            new_value=key.status,
            ip_address=request.remote_addr,
            created_at=datetime.utcnow()
        )
        db.session.add(audit)
        db.session.commit()

        return jsonify({'success': True})

    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500
