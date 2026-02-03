"""
/* * Nom de l'application : ATM-RDC
 * Description : Authentication routes
 * Produit de : MOA Digital Agency, www.myoneart.com
 * Fait par : Aisance KALONJI, www.aisancekalonji.com
 * Auditer par : La CyberConfiance, www.cyberconfiance.com
 */
from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_user, logout_user, login_required, current_user
from werkzeug.security import check_password_hash
from datetime import datetime
from urllib.parse import urlparse, urljoin

from models import db, User, AuditLog
from services.translation_service import t
from services.audit_service import log_audit_event

auth_bp = Blueprint('auth', __name__)


def is_safe_url(target):
    ref_url = urlparse(request.host_url)
    test_url = urlparse(urljoin(request.host_url, target))
    return test_url.scheme in ('http', 'https') and \
           ref_url.netloc == test_url.netloc


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
            
            log_audit_event(
                user_id=user.id,
                action='login'
            )
            
            next_page = request.args.get('next')
            if not next_page or not is_safe_url(next_page):
                next_page = url_for('dashboard.index')
            return redirect(next_page)
        
        if user:
            log_audit_event(user_id=user.id, action='login_failed', severity='warning')
        else:
            log_audit_event(action='login_failed', details={'username': username}, severity='warning')

        flash(t('auth.invalid_credentials'), 'error')
    
    return render_template('auth/login.html')


@auth_bp.route('/logout')
@login_required
def logout():
    log_audit_event(user_id=current_user.id, action='logout')
    
    logout_user()
    flash(t('auth.logout_success'), 'success')
    return redirect(url_for('auth.login'))
