from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_user, logout_user, login_required, current_user
from werkzeug.security import check_password_hash
from datetime import datetime

from models import db, User, AuditLog
from services.translation_service import t

auth_bp = Blueprint('auth', __name__)


@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard.index'))
    
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '')
        remember = request.form.get('remember', False)
        
        user = User.query.filter_by(username=username).first()
        
        if user and user.check_password(password):
            if not user.is_active:
                flash(t('auth.account_disabled'), 'error')
                return render_template('auth/login.html')
            
            login_user(user, remember=remember)
            user.last_login = datetime.utcnow()
            
            log = AuditLog(
                user_id=user.id,
                action='login',
                ip_address=request.remote_addr,
                user_agent=request.user_agent.string[:500] if request.user_agent else None
            )
            db.session.add(log)
            db.session.commit()
            
            next_page = request.args.get('next')
            if next_page:
                return redirect(next_page)
            return redirect(url_for('dashboard.index'))
        
        flash(t('auth.invalid_credentials'), 'error')
    
    return render_template('auth/login.html')


@auth_bp.route('/logout')
@login_required
def logout():
    log = AuditLog(
        user_id=current_user.id,
        action='logout',
        ip_address=request.remote_addr,
        user_agent=request.user_agent.string[:500] if request.user_agent else None
    )
    db.session.add(log)
    db.session.commit()
    
    logout_user()
    flash(t('auth.logout_success'), 'success')
    return redirect(url_for('auth.login'))
