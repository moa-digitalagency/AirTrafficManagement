"""
Décorateurs personnalisés
Air Traffic Management - RDC
"""

from functools import wraps
from flask import flash, redirect, url_for, abort
from flask_login import current_user


def role_required(allowed_roles):
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not current_user.is_authenticated:
                return redirect(url_for('auth.login'))
            
            if current_user.role not in allowed_roles:
                flash('Vous n\'avez pas les permissions nécessaires pour accéder à cette page.', 'error')
                return redirect(url_for('dashboard.index'))
            
            return f(*args, **kwargs)
        return decorated_function
    return decorator


def admin_required(f):
    return role_required(['superadmin'])(f)


def billing_required(f):
    return role_required(['superadmin', 'billing'])(f)


def controller_required(f):
    return role_required(['superadmin', 'supervisor', 'controller'])(f)
