from flask import Blueprint, render_template, jsonify, request, flash, redirect, url_for
from flask_login import login_required, current_user
from datetime import datetime, timedelta

from models import db, User, Aircraft, Airport, Airline, AuditLog, TariffConfig, SystemConfig
from utils.decorators import role_required

admin_bp = Blueprint('admin', __name__)


@admin_bp.route('/')
@login_required
@role_required(['superadmin'])
def index():
    user_count = User.query.count()
    aircraft_count = Aircraft.query.count()
    airline_count = Airline.query.count()
    airport_count = Airport.query.count()
    
    recent_logs = AuditLog.query.order_by(AuditLog.created_at.desc()).limit(20).all()
    
    return render_template('admin/index.html',
                          user_count=user_count,
                          aircraft_count=aircraft_count,
                          airline_count=airline_count,
                          airport_count=airport_count,
                          recent_logs=recent_logs)


@admin_bp.route('/users')
@login_required
@role_required(['superadmin'])
def users():
    users = User.query.order_by(User.created_at.desc()).all()
    return render_template('admin/users.html', users=users)


@admin_bp.route('/users/create', methods=['GET', 'POST'])
@login_required
@role_required(['superadmin'])
def create_user():
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        email = request.form.get('email', '').strip()
        password = request.form.get('password', '')
        role = request.form.get('role', 'observer')
        first_name = request.form.get('first_name', '').strip()
        last_name = request.form.get('last_name', '').strip()
        
        if User.query.filter_by(username=username).first():
            flash('Ce nom d\'utilisateur existe déjà.', 'error')
            return render_template('admin/user_form.html', user=None)
        
        if User.query.filter_by(email=email).first():
            flash('Cet email existe déjà.', 'error')
            return render_template('admin/user_form.html', user=None)
        
        user = User(
            username=username,
            email=email,
            role=role,
            first_name=first_name,
            last_name=last_name
        )
        user.set_password(password)
        
        db.session.add(user)
        
        log = AuditLog(
            user_id=current_user.id,
            action='create_user',
            entity_type='user',
            entity_id=user.id,
            ip_address=request.remote_addr
        )
        db.session.add(log)
        db.session.commit()
        
        flash(f'Utilisateur {username} créé avec succès.', 'success')
        return redirect(url_for('admin.users'))
    
    return render_template('admin/user_form.html', user=None)


@admin_bp.route('/users/<int:user_id>/edit', methods=['GET', 'POST'])
@login_required
@role_required(['superadmin'])
def edit_user(user_id):
    user = User.query.get_or_404(user_id)
    
    if request.method == 'POST':
        user.email = request.form.get('email', '').strip()
        user.role = request.form.get('role', 'observer')
        user.first_name = request.form.get('first_name', '').strip()
        user.last_name = request.form.get('last_name', '').strip()
        user.is_active = request.form.get('is_active') == 'on'
        
        new_password = request.form.get('password', '').strip()
        if new_password:
            user.set_password(new_password)
        
        log = AuditLog(
            user_id=current_user.id,
            action='update_user',
            entity_type='user',
            entity_id=user.id,
            ip_address=request.remote_addr
        )
        db.session.add(log)
        db.session.commit()
        
        flash(f'Utilisateur {user.username} mis à jour.', 'success')
        return redirect(url_for('admin.users'))
    
    return render_template('admin/user_form.html', user=user)


@admin_bp.route('/users/<int:user_id>/toggle', methods=['POST'])
@login_required
@role_required(['superadmin'])
def toggle_user(user_id):
    user = User.query.get_or_404(user_id)
    
    if user.id == current_user.id:
        flash('Vous ne pouvez pas désactiver votre propre compte.', 'error')
        return redirect(url_for('admin.users'))
    
    user.is_active = not user.is_active
    
    log = AuditLog(
        user_id=current_user.id,
        action='toggle_user_status',
        entity_type='user',
        entity_id=user.id,
        new_value=str(user.is_active),
        ip_address=request.remote_addr
    )
    db.session.add(log)
    db.session.commit()
    
    status = 'activé' if user.is_active else 'désactivé'
    flash(f'Utilisateur {user.username} {status}.', 'success')
    return redirect(url_for('admin.users'))


@admin_bp.route('/airlines')
@login_required
@role_required(['superadmin', 'billing'])
def airlines():
    airlines = Airline.query.order_by(Airline.name).all()
    return render_template('admin/airlines.html', airlines=airlines)


@admin_bp.route('/aircraft')
@login_required
@role_required(['superadmin', 'supervisor'])
def aircraft():
    aircraft = Aircraft.query.order_by(Aircraft.operator).all()
    return render_template('admin/aircraft.html', aircraft=aircraft)


@admin_bp.route('/airports')
@login_required
@role_required(['superadmin', 'supervisor'])
def airports():
    airports = Airport.query.order_by(Airport.icao_code).all()
    return render_template('admin/airports.html', airports=airports)


@admin_bp.route('/audit-logs')
@login_required
@role_required(['superadmin', 'auditor'])
def audit_logs():
    page = request.args.get('page', 1, type=int)
    user_id = request.args.get('user_id', type=int)
    action = request.args.get('action', '')
    
    query = AuditLog.query
    
    if user_id:
        query = query.filter_by(user_id=user_id)
    
    if action:
        query = query.filter(AuditLog.action.ilike(f'%{action}%'))
    
    logs = query.order_by(AuditLog.created_at.desc()).paginate(
        page=page, per_page=50, error_out=False
    )
    
    users = User.query.all()
    
    return render_template('admin/audit_logs.html', logs=logs, users=users, 
                          selected_user=user_id, selected_action=action)


@admin_bp.route('/settings', methods=['GET', 'POST'])
@login_required
@role_required(['superadmin'])
def settings():
    if request.method == 'POST':
        configs = SystemConfig.query.filter_by(is_editable=True).all()
        changes_count = 0

        for config in configs:
            new_value = request.form.get(config.key)
            if new_value is not None and new_value != config.value:
                old_value = config.value
                config.value = new_value
                config.updated_by = current_user.id

                log = AuditLog(
                    user_id=current_user.id,
                    action='update_system_config',
                    entity_type='system_config',
                    entity_id=config.id,
                    old_value=old_value,
                    new_value=new_value,
                    ip_address=request.remote_addr
                )
                db.session.add(log)
                changes_count += 1

        if changes_count > 0:
            db.session.commit()
            flash(f'{changes_count} paramètre(s) mis à jour.', 'success')
        else:
            flash('Aucun changement détecté.', 'info')

        return redirect(url_for('admin.settings'))

    configs = SystemConfig.query.filter_by(is_editable=True).order_by(SystemConfig.category, SystemConfig.key).all()
    return render_template('admin/settings.html', configs=configs)
