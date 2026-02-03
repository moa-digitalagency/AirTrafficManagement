#!/usr/bin/env python3
"""
/* * Nom de l'application : ATM-RDC
 * Description : Application principale Flask avec WebSocket
 * Produit de : MOA Digital Agency, www.myoneart.com
 * Fait par : Aisance KALONJI, www.aisancekalonji.com
 * Auditer par : La CyberConfiance, www.cyberconfiance.com
 */

Air Traffic Management - RDC (ATM-RDC)
Régie des Voies Aériennes - République Démocratique du Congo
"""

import os
import eventlet
eventlet.monkey_patch()

from flask import Flask, render_template, redirect, url_for, request, jsonify, session
from flask_socketio import SocketIO, emit
from flask_login import LoginManager, login_required, current_user
from flask_cors import CORS
from flask_wtf.csrf import CSRFProtect
from datetime import datetime

from config.settings import Config
from models import db, User
from services.translation_service import t

socketio = SocketIO()
login_manager = LoginManager()
csrf = CSRFProtect()


def create_app(config_class=Config):
    app = Flask(__name__,
                template_folder='templates',
                static_folder='statics')
    
    app.config.from_object(config_class)
    
    db.init_app(app)
    socketio.init_app(app, cors_allowed_origins="*", async_mode='eventlet')
    login_manager.init_app(app)
    csrf.init_app(app)
    CORS(app)
    
    login_manager.login_view = 'auth.login'
    # login_manager.login_message handled via unauthorized_handler for localization
    
    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))

    @login_manager.unauthorized_handler
    def unauthorized():
        from flask import flash
        flash(t('auth.login_required'), 'warning')
        return redirect(url_for('auth.login', next=request.full_path))
    
    from routes.auth import auth_bp
    from routes.dashboard import dashboard_bp
    from routes.radar import radar_bp
    from routes.flights import flights_bp
    from routes.invoices import invoices_bp
    from routes.admin import admin_bp
    from routes.api import api_bp
    from routes.analytics import analytics_bp
    from routes.notifications import notifications_bp
    
    app.register_blueprint(auth_bp, url_prefix='/auth')
    app.register_blueprint(dashboard_bp, url_prefix='/dashboard')
    app.register_blueprint(radar_bp, url_prefix='/radar')
    app.register_blueprint(flights_bp, url_prefix='/flights')
    app.register_blueprint(invoices_bp, url_prefix='/invoices')
    app.register_blueprint(admin_bp, url_prefix='/admin')
    app.register_blueprint(api_bp, url_prefix='/api')
    app.register_blueprint(analytics_bp, url_prefix='/analytics')
    app.register_blueprint(notifications_bp, url_prefix='/notifications')
    
    @app.route('/lang/<lang_code>')
    def set_language(lang_code):
        if lang_code in ['fr', 'en']:
            session['lang'] = lang_code
        return redirect(request.referrer or url_for('index'))

    @app.route('/')
    def index():
        if current_user.is_authenticated:
            return redirect(url_for('dashboard.index'))
        return redirect(url_for('auth.login'))
    
    @app.route('/health')
    def health_check():
        return jsonify({'status': 'healthy', 'timestamp': datetime.utcnow().isoformat()})
    
    @app.context_processor
    def inject_context():
        branding = {}
        try:
            from models import SystemConfig
            configs = SystemConfig.query.filter_by(category='branding').all()
            for c in configs:
                branding[c.key] = c.value
        except Exception:
            pass

        return {
            'now': datetime.utcnow(),
            't': t,
            'current_lang': session.get('lang', 'fr'),
            'branding': branding
        }
    
    @app.after_request
    def add_security_headers(response):
        response.headers['X-Content-Type-Options'] = 'nosniff'
        response.headers['X-Frame-Options'] = 'SAMEORIGIN'
        response.headers['X-XSS-Protection'] = '1; mode=block'
        response.headers['Strict-Transport-Security'] = 'max-age=31536000; includeSubDomains'
        return response

    @app.errorhandler(404)
    def not_found_error(error):
        return render_template('errors/404.html'), 404
    
    @app.errorhandler(500)
    def internal_error(error):
        db.session.rollback()
        return render_template('errors/500.html'), 500
    
    return app


@socketio.on('connect')
def handle_connect():
    emit('connected', {'status': 'connected', 'timestamp': datetime.utcnow().isoformat()})


@socketio.on('disconnect')
def handle_disconnect():
    pass


@socketio.on('request_flight_update')
def handle_flight_update_request():
    from services.flight_tracker import get_active_flights
    flights = get_active_flights()
    emit('flight_update', {'flights': flights})


@socketio.on('subscribe_radar')
def handle_subscribe_radar(data):
    from flask_socketio import join_room
    region = data.get('region', 'all')
    join_room(f'radar_{region}')
    emit('subscribed', {'region': region})


def broadcast_flight_update(flights_data):
    socketio.emit('flight_update', {'flights': flights_data}, room='radar_all')


app = create_app()

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    debug_mode = os.environ.get('FLASK_DEBUG', 'False').lower() == 'true'
    socketio.run(app, host='0.0.0.0', port=port, debug=debug_mode)
