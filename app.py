#!/usr/bin/env python3
"""
Air Traffic Management - RDC (ATM-RDC)
Application principale Flask avec WebSocket

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
    login_manager.login_message = 'Veuillez vous connecter pour accéder à cette page.'
    login_manager.login_message_category = 'warning'
    
    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))
    
    from routes.auth import auth_bp
    from routes.dashboard import dashboard_bp
    from routes.radar import radar_bp
    from routes.flights import flights_bp
    from routes.invoices import invoices_bp
    from routes.admin import admin_bp
    from routes.api import api_bp
    
    app.register_blueprint(auth_bp, url_prefix='/auth')
    app.register_blueprint(dashboard_bp, url_prefix='/dashboard')
    app.register_blueprint(radar_bp, url_prefix='/radar')
    app.register_blueprint(flights_bp, url_prefix='/flights')
    app.register_blueprint(invoices_bp, url_prefix='/invoices')
    app.register_blueprint(admin_bp, url_prefix='/admin')
    app.register_blueprint(api_bp, url_prefix='/api')
    
    @app.route('/')
    def index():
        if current_user.is_authenticated:
            return redirect(url_for('dashboard.index'))
        return redirect(url_for('auth.login'))
    
    @app.route('/health')
    def health_check():
        return jsonify({'status': 'healthy', 'timestamp': datetime.utcnow().isoformat()})
    
    @app.context_processor
    def inject_now():
        return {'now': datetime.utcnow()}
    
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
    socketio.run(app, host='0.0.0.0', port=port, debug=True)
