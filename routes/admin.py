"""
/* * Nom de l'application : ATM-RDC
 * Description : Source file: admin.py
 * Produit de : MOA Digital Agency, www.myoneart.com
 * Fait par : Aisance KALONJI, www.aisancekalonji.com
 * Auditer par : La CyberConfiance, www.cyberconfiance.com
 */
"""
from flask import Blueprint, render_template, jsonify, request, flash, redirect, url_for, current_app
from flask_login import login_required, current_user
from werkzeug.utils import secure_filename
import os
from datetime import datetime, timedelta
import pytz
import json
import geojson
from shapely import wkt
from shapely.geometry import shape
from geoalchemy2.shape import to_shape

from models import db, User, Aircraft, Airport, Airline, AuditLog, TariffConfig, SystemConfig, Airspace
from models.user import Role, Permission
from utils.decorators import role_required
from services.translation_service import t

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


@admin_bp.route('/roles', methods=['GET', 'POST'])
@login_required
@role_required(['superadmin'])
def roles():
    if request.method == 'POST':
        if 'action' in request.form:
            action = request.form['action']
            if action == 'delete':
                role_id = request.form.get('role_id')
                role = Role.query.get(role_id)
                if role and not role.is_system:
                    if len(role.users) > 0:
                        flash('Impossible de supprimer un rôle assigné à des utilisateurs.', 'error')
                    else:
                        db.session.delete(role)
                        db.session.commit()
                        flash(t('admin.role_deleted').format(name=role.name), 'success')
                else:
                    flash('Impossible de supprimer ce rôle.', 'error')

    roles = Role.query.order_by(Role.name).all()
    return render_template('admin/roles.html', roles=roles)


@admin_bp.route('/roles/edit/<int:role_id>', methods=['GET', 'POST'])
@admin_bp.route('/roles/create', methods=['GET', 'POST'])
@login_required
@role_required(['superadmin'])
def edit_role(role_id=None):
    role = Role.query.get(role_id) if role_id else None

    if request.method == 'POST':
        name = request.form.get('name')
        description = request.form.get('description')
        perm_ids = request.form.getlist('permissions')

        if not role:
            if Role.query.filter_by(name=name).first():
                flash(f'Le rôle {name} existe déjà.', 'error')
                return redirect(url_for('admin.edit_role'))
            role = Role(name=name, description=description)
            db.session.add(role)
        else:
            if role.name != name and Role.query.filter_by(name=name).first():
                flash(f'Le rôle {name} existe déjà.', 'error')
                return redirect(url_for('admin.edit_role', role_id=role.id))
            role.name = name
            role.description = description
            role.permissions = [] # Reset permissions

        # Add selected permissions
        for pid in perm_ids:
            perm = Permission.query.get(int(pid))
            if perm:
                role.permissions.append(perm)

        db.session.commit()

        log = AuditLog(
            user_id=current_user.id,
            action='update_role',
            entity_type='role',
            entity_id=role.id,
            entity_name=role.name,
            ip_address=request.remote_addr
        )
        db.session.add(log)
        db.session.commit()

        flash(t('admin.role_saved').format(name=role.name), 'success')
        return redirect(url_for('admin.roles'))

    permissions = Permission.query.order_by(Permission.resource, Permission.action).all()
    # Group permissions by resource for better UI
    grouped_perms = {}
    for p in permissions:
        if p.resource not in grouped_perms:
            grouped_perms[p.resource] = []
        grouped_perms[p.resource].append(p)

    return render_template('admin/role_form.html', role=role, grouped_perms=grouped_perms)


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
            flash(t('admin.user_exists'), 'error')
            return render_template('admin/user_form.html', user=None)
        
        if User.query.filter_by(email=email).first():
            flash(t('admin.email_exists'), 'error')
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
        
        flash(t('admin.user_created').format(username=username), 'success')
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
        
        flash(t('admin.user_updated').format(username=user.username), 'success')
        return redirect(url_for('admin.users'))
    
    return render_template('admin/user_form.html', user=user)


@admin_bp.route('/users/<int:user_id>/toggle', methods=['POST'])
@login_required
@role_required(['superadmin'])
def toggle_user(user_id):
    user = User.query.get_or_404(user_id)
    
    if user.id == current_user.id:
        flash(t('admin.cannot_disable_self'), 'error')
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
    
    status = t('common.enabled') if user.is_active else t('common.disabled')
    flash(t('admin.user_status_changed').format(username=user.username, status=status), 'success')
    return redirect(url_for('admin.users'))


@admin_bp.route('/airlines', methods=['GET', 'POST'])
@login_required
@role_required(['superadmin', 'billing'])
def airlines():
    # Delete action
    if request.method == 'POST' and request.form.get('action') == 'delete':
        id = request.form.get('id')
        airline = Airline.query.get(id)
        if airline:
            db.session.delete(airline)
            db.session.commit()
            flash(t('admin.airline_deleted'), 'success')

    # Search
    search = request.args.get('search', '')
    query = Airline.query
    if search:
        query = query.filter(db.or_(
            Airline.name.ilike(f'%{search}%'),
            Airline.icao_code.ilike(f'%{search}%'),
            Airline.iata_code.ilike(f'%{search}%'),
            Airline.country.ilike(f'%{search}%')
        ))

    airlines = query.order_by(Airline.name).all()
    return render_template('admin/airlines.html', airlines=airlines, search=search)


@admin_bp.route('/airlines/edit/<int:id>', methods=['GET', 'POST'])
@admin_bp.route('/airlines/create', methods=['GET', 'POST'])
@login_required
@role_required(['superadmin', 'billing'])
def edit_airline(id=None):
    airline = Airline.query.get(id) if id else None

    if request.method == 'POST':
        name = request.form.get('name')
        icao = request.form.get('icao_code')
        iata = request.form.get('iata_code')
        country = request.form.get('country')
        email = request.form.get('email')

        if not airline:
            airline = Airline(icao_code=icao)
            db.session.add(airline)
        else:
            airline.icao_code = icao

        airline.name = name
        airline.iata_code = iata
        airline.country = country
        airline.email = email
        airline.is_active = request.form.get('is_active') == 'on'

        db.session.commit()
        flash(t('admin.airline_saved').format(name=name), 'success')
        return redirect(url_for('admin.airlines'))

    return render_template('admin/airline_form.html', airline=airline)


@admin_bp.route('/airlines/fetch', methods=['POST'])
@login_required
@role_required(['superadmin'])
def fetch_airline_data():
    iata = request.form.get('iata_code')
    if not iata:
        flash('Code IATA requis.', 'error')
        return redirect(url_for('admin.airlines'))

    from services.api_client import aviationstack
    data = aviationstack.get_airline_info(iata)

    if data:
        airline = Airline.query.filter_by(iata_code=iata).first()
        if not airline:
            airline = Airline(iata_code=iata)
            db.session.add(airline)

        airline.name = data.get('airline_name') or data.get('name')
        airline.icao_code = data.get('icao_code')
        airline.country = data.get('country_name')
        airline.is_active = True

        db.session.commit()
        flash(t('admin.fetch_success'), 'success')
    else:
        flash(t('admin.fetch_error'), 'error')

    return redirect(url_for('admin.airlines'))


@admin_bp.route('/aircraft', methods=['GET', 'POST'])
@login_required
@role_required(['superadmin', 'supervisor'])
def aircraft():
    # Delete action
    if request.method == 'POST' and request.form.get('action') == 'delete':
        id = request.form.get('id')
        ac = Aircraft.query.get(id)
        if ac:
            db.session.delete(ac)
            db.session.commit()
            flash('Aéronef supprimé.', 'success')

    # Search
    search = request.args.get('search', '')
    query = Aircraft.query
    if search:
        query = query.filter(db.or_(
            Aircraft.registration.ilike(f'%{search}%'),
            Aircraft.icao24.ilike(f'%{search}%'),
            Aircraft.model.ilike(f'%{search}%'),
            Aircraft.operator.ilike(f'%{search}%')
        ))

    aircraft = query.order_by(Aircraft.operator).all()
    return render_template('admin/aircraft.html', aircraft=aircraft, search=search)


@admin_bp.route('/aircraft/edit/<int:id>', methods=['GET', 'POST'])
@admin_bp.route('/aircraft/create', methods=['GET', 'POST'])
@login_required
@role_required(['superadmin', 'supervisor'])
def edit_aircraft(id=None):
    ac = Aircraft.query.get(id) if id else None

    if request.method == 'POST':
        if not ac:
            ac = Aircraft()
            db.session.add(ac)

        ac.registration = request.form.get('registration')
        ac.icao24 = request.form.get('icao24')
        ac.model = request.form.get('model')
        ac.type_code = request.form.get('type_code')
        ac.operator = request.form.get('operator')
        ac.operator_iata = request.form.get('operator_iata')
        ac.category = request.form.get('category', 'commercial')

        try:
            ac.mtow = float(request.form.get('mtow', 0))
        except ValueError:
            ac.mtow = 0

        db.session.commit()
        flash(f'Aéronef {ac.registration} enregistré.', 'success')
        return redirect(url_for('admin.aircraft'))

    return render_template('admin/aircraft_form.html', aircraft=ac)


@admin_bp.route('/airports', methods=['GET', 'POST'])
@login_required
@role_required(['superadmin', 'supervisor'])
def airports():
    # Delete action
    if request.method == 'POST' and request.form.get('action') == 'delete':
        id = request.form.get('id')
        airport = Airport.query.get(id)
        if airport:
            db.session.delete(airport)
            db.session.commit()
            flash('Aéroport supprimé.', 'success')

    # Search
    search = request.args.get('search', '')
    query = Airport.query
    if search:
        query = query.filter(db.or_(
            Airport.name.ilike(f'%{search}%'),
            Airport.icao_code.ilike(f'%{search}%'),
            Airport.city.ilike(f'%{search}%')
        ))

    airports = query.order_by(Airport.icao_code).all()
    return render_template('admin/airports.html', airports=airports, search=search)


@admin_bp.route('/airports/edit/<int:id>', methods=['GET', 'POST'])
@admin_bp.route('/airports/create', methods=['GET', 'POST'])
@login_required
@role_required(['superadmin', 'supervisor'])
def edit_airport(id=None):
    airport = Airport.query.get(id) if id else None

    if request.method == 'POST':
        if not airport:
            airport = Airport()
            db.session.add(airport)

        airport.icao_code = request.form.get('icao_code')
        airport.iata_code = request.form.get('iata_code')
        airport.name = request.form.get('name')
        airport.city = request.form.get('city')
        airport.country = request.form.get('country')
        airport.status = request.form.get('status', 'open')
        airport.is_domestic = request.form.get('is_domestic') == 'on'

        try:
            airport.latitude = float(request.form.get('latitude', 0))
            airport.longitude = float(request.form.get('longitude', 0))
            airport.elevation_ft = int(request.form.get('elevation_ft', 0))
        except ValueError:
            pass

        db.session.commit()
        flash(f'Aéroport {airport.icao_code} enregistré.', 'success')
        return redirect(url_for('admin.airports'))

    return render_template('admin/airport_form.html', airport=airport)


@admin_bp.route('/airports/fetch', methods=['POST'])
@login_required
@role_required(['superadmin'])
def fetch_airport_data():
    icao = request.form.get('icao_code')
    if not icao:
        flash('Code OACI requis.', 'error')
        return redirect(url_for('admin.airports'))

    from services.api_client import aviationstack

    data = aviationstack.get_airport_info(icao)
    if data:
        airport = Airport.query.filter_by(icao_code=icao).first()
        if not airport:
            airport = Airport(icao_code=icao)
            db.session.add(airport)

        airport.name = data.get('airport_name')
        airport.iata_code = data.get('iata_code')
        airport.country = data.get('country_name')
        # Some guesswork on API fields mapping
        if data.get('latitude'): airport.latitude = float(data.get('latitude'))
        if data.get('longitude'): airport.longitude = float(data.get('longitude'))

        db.session.commit()
        flash(f'Données aéroport {icao} mises à jour.', 'success')
    else:
        flash(f'Impossible de trouver l\'aéroport {icao} ou API non configurée.', 'error')

    return redirect(url_for('admin.airports'))


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
    # Ensure default billing configs exist
    default_configs = [
        {'key': 'invoice_header_title', 'value': 'RÉGIE DES VOIES AÉRIENNES', 'description': 'Titre En-tête Facture', 'category': 'invoice', 'value_type': 'string'},
        {'key': 'invoice_header_subtitle', 'value': 'République Démocratique du Congo', 'description': 'Sous-titre En-tête Facture', 'category': 'invoice', 'value_type': 'string'},
        {'key': 'invoice_header_address', 'value': "Aéroport International de N'Djili - Kinshasa", 'description': 'Adresse En-tête Facture', 'category': 'invoice', 'value_type': 'text'},
        {'key': 'invoice_footer_legal', 'value': 'Arrêté Ministériel...', 'description': 'Mentions Légales (Pied de page)', 'category': 'invoice', 'value_type': 'text'},
        {'key': 'invoice_footer_banks', 'value': 'Banque Centrale du Congo: ...', 'description': 'Coordonnées Bancaires', 'category': 'invoice', 'value_type': 'text'},
        {'key': 'invoice_number_format', 'value': 'RVA-{ANNEE}-{MOIS}-{ID}', 'description': 'Format Numéro Facture', 'category': 'invoice', 'value_type': 'string'},
        {'key': 'invoice_currency', 'value': 'USD', 'description': 'Devise par défaut', 'category': 'invoice', 'value_type': 'select'},
    ]

    for conf in default_configs:
        if not SystemConfig.query.filter_by(key=conf['key']).first():
            new_conf = SystemConfig(
                key=conf['key'],
                value=conf['value'],
                description=conf['description'],
                category=conf['category'],
                value_type=conf['value_type'],
                is_editable=True
            )
            db.session.add(new_conf)

    if db.session.new:
        db.session.commit()

    if request.method == 'POST':
        configs = SystemConfig.query.filter_by(is_editable=True).all()
        changes_count = 0

        # Handle regular form fields
        for config in configs:
            if config.value_type == 'file':
                continue

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

        # Handle file uploads
        upload_fields = ['logo_path', 'favicon_path']
        for field in upload_fields:
            if field in request.files:
                file = request.files[field]
                if file and file.filename:
                    filename = secure_filename(f"{field}_{datetime.now().strftime('%Y%m%d%H%M%S')}_{file.filename}")
                    upload_path = os.path.join(current_app.static_folder, 'uploads', filename)
                    os.makedirs(os.path.dirname(upload_path), exist_ok=True)
                    file.save(upload_path)

                    # Update config
                    config = SystemConfig.query.filter_by(key=field).first()
                    if not config:
                        config = SystemConfig(key=field, category='branding', value_type='file', is_editable=True)
                        db.session.add(config)

                    old_value = config.value
                    new_value = f'uploads/{filename}'

                    if old_value != new_value:
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
            flash(t('admin.settings_updated').format(count=changes_count), 'success')
        else:
            flash(t('admin.no_changes'), 'info')

        return redirect(url_for('admin.settings'))

    configs = SystemConfig.query.filter_by(is_editable=True).order_by(SystemConfig.category, SystemConfig.key).all()
    return render_template('admin/settings.html', configs=configs, timezones=pytz.common_timezones)


@admin_bp.route('/languages', methods=['GET', 'POST'])
@login_required
@role_required(['superadmin'])
def languages():
    from services.translation_service import translation_service
    import json

    if request.method == 'POST':
        # Handle file upload
        if 'file' in request.files:
            file = request.files['file']
            if file and file.filename.endswith('.json'):
                filename = secure_filename(file.filename)
                # Use current_app.root_path which points to the application root
                # Since locales is in the root and app.py is in the root, we can use that.
                # However, Flask apps created with app.py in root usually have root_path as that directory.
                locales_dir = os.path.join(current_app.root_path, 'locales')

                if not os.path.exists(locales_dir):
                    # Fallback if locales is not found (e.g. running from different dir)
                    locales_dir = os.path.abspath('locales')

                os.makedirs(locales_dir, exist_ok=True)
                file.save(os.path.join(locales_dir, filename))
                translation_service.reload()
                flash(t('admin.lang_file_uploaded').format(filename=filename), 'success')

                log = AuditLog(
                    user_id=current_user.id,
                    action='upload_language_file',
                    entity_type='language',
                    entity_name=filename,
                    ip_address=request.remote_addr
                )
                db.session.add(log)
                db.session.commit()

        # Handle toggle
        elif 'toggle' in request.form:
            lang_code = request.form.get('toggle')
            config = SystemConfig.query.filter_by(key='enabled_languages').first()
            if config:
                enabled = config.get_typed_value() or []

                if lang_code in enabled:
                    enabled.remove(lang_code)
                    status = 'désactivé'
                else:
                    enabled.append(lang_code)
                    status = 'activé'

                config.value = json.dumps(enabled)

                log = AuditLog(
                    user_id=current_user.id,
                    action='toggle_language',
                    entity_type='language',
                    entity_name=lang_code,
                    new_value=status,
                    ip_address=request.remote_addr
                )
                db.session.add(log)
                db.session.commit()
                status_text = t('common.enabled') if status == 'activé' else t('common.disabled')
                flash(t('admin.lang_toggled').format(lang=lang_code, status=status_text), 'success')

        return redirect(url_for('admin.languages'))

    available_locales = translation_service.get_available_locales()
    config = SystemConfig.query.filter_by(key='enabled_languages').first()
    enabled_locales = config.get_typed_value() if config else []

    return render_template('admin/languages.html',
                          available=available_locales,
                          enabled=enabled_locales)


@admin_bp.route('/airspace/map')
@login_required
@role_required(['superadmin'])
def airspace_map():
    airspace = Airspace.query.filter_by(name='RDC Airspace').first()

    airspace_geojson = None
    if airspace and airspace.geom:
        try:
            if isinstance(airspace.geom, str):
                # Text/WKT
                geom_shape = wkt.loads(airspace.geom)
            else:
                # Geometry object (WKBElement)
                geom_shape = to_shape(airspace.geom)

            airspace_geojson = geojson.Feature(geometry=geom_shape, properties={})
        except Exception as e:
            current_app.logger.error(f"Error converting geometry: {e}")

    return render_template('admin/airspace_map.html', airspace=airspace, geojson=airspace_geojson)


@admin_bp.route('/airspace/save', methods=['POST'])
@login_required
@role_required(['superadmin'])
def save_airspace():
    data = request.get_json()
    if not data or 'geojson' not in data:
        return jsonify({'success': False, 'message': 'Données invalides'}), 400

    geojson_data = data['geojson']

    try:
        airspace = Airspace.query.filter_by(name='RDC Airspace').first()
        if not airspace:
            airspace = Airspace(name='RDC Airspace', type='boundary')
            db.session.add(airspace)

        # Convert GeoJSON to Shape -> WKT
        # We process the geometry part of the feature
        if 'geometry' in geojson_data:
            geom_shape = shape(geojson_data['geometry'])
        else:
             # Assuming raw geometry passed or FeatureCollection handling needed?
             # Leaflet Draw usually returns FeatureCollection or Feature.
             # We assume we get a Feature or Geometry.
             # If FeatureCollection, take the first feature?
             if geojson_data.get('type') == 'FeatureCollection':
                 geom_shape = shape(geojson_data['features'][0]['geometry'])
             elif geojson_data.get('type') == 'Feature':
                 geom_shape = shape(geojson_data['geometry'])
             else:
                 geom_shape = shape(geojson_data)

        wkt_str = geom_shape.wkt

        # Update model
        # SQLAlchemy/GeoAlchemy2 handles WKT assignment to Geometry column
        # Or string assignment to Text column.
        airspace.geom = wkt_str

        # Log action
        log = AuditLog(
            user_id=current_user.id,
            action='update_airspace',
            entity_type='airspace',
            entity_id=airspace.id or 0,
            entity_name=airspace.name,
            ip_address=request.remote_addr
        )
        db.session.add(log)

        db.session.commit()
        return jsonify({'success': True, 'message': 'Espace aérien mis à jour'})

    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Error saving airspace: {e}")
        return jsonify({'success': False, 'message': str(e)}), 500
