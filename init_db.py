#!/usr/bin/env python3
"""
/* * Nom de l'application : ATM-RDC
 * Description : Source file: init_db.py
 * Produit de : MOA Digital Agency, www.myoneart.com
 * Fait par : Aisance KALONJI, www.aisancekalonji.com
 * Auditer par : La CyberConfiance, www.cyberconfiance.com
 */
"""
"""
Script d'initialisation de la base de données PostgreSQL
Air Traffic Management - RDC (ATM-RDC)

Ce script crée toutes les tables nécessaires et insère les données initiales
de manière idempotente (sans écraser les données existantes).
"""

import os
import sys
from datetime import datetime, date, timedelta
import random
import logging
from dotenv import load_dotenv

load_dotenv()

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from flask import Flask
from sqlalchemy import text, inspect
from models import (db, User, Aircraft, Airport, Airline, TariffConfig, Flight, 
                    Overflight, Landing, Alert, FlightPosition, FlightRoute, 
                    Invoice, InvoiceLineItem, Notification, SystemConfig, AuditLog,
                    Airspace, ApiKey, Role, Permission, TelegramSubscriber)

# Configuration du logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def create_app():
    app = Flask(__name__)
    app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL')
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['SECRET_KEY'] = os.environ.get('SESSION_SECRET', 'dev-secret-key')
    db.init_app(app)
    return app

def check_and_update_schema(app):
    """
    Vérifie et met à jour le schéma de la base de données (ajout de colonnes manquantes).
    Implémente la logique d'idempotence et de migration 'n-1' requise pour le déploiement VPS.
    """
    with app.app_context():
        logger.info("2b. Vérification des colonnes manquantes (Migration)...")
        inspector = inspect(db.engine)

        target_models = [User, Aircraft, Airport, Airline, TariffConfig, Flight,
                    Overflight, Landing, Alert, FlightPosition, FlightRoute,
                    Invoice, InvoiceLineItem, Notification, SystemConfig, AuditLog,
                    Airspace, ApiKey, Role, Permission, TelegramSubscriber]

        for model in target_models:
            table_name = model.__tablename__
            if not inspector.has_table(table_name):
                # La table n'existe pas encore, create_all s'en chargera ou s'en est chargé
                continue

            existing_columns = {col['name'] for col in inspector.get_columns(table_name)}

            for column in model.__table__.columns:
                if column.name not in existing_columns:
                    logger.info(f"   - Colonne manquante détectée: {table_name}.{column.name}")
                    try:
                        # Compile le type de colonne pour le dialecte actuel (PostgreSQL)
                        col_type = column.type.compile(db.engine.dialect)

                        # On ajoute la colonne en autorisant NULL pour éviter les conflits avec les données existantes
                        # sauf si une valeur par défaut serveur est fournie (ce qui est rare ici)
                        alter_stmt = f"ALTER TABLE {table_name} ADD COLUMN {column.name} {col_type}"
                        db.session.execute(text(alter_stmt))
                        logger.info(f"     -> Colonne {column.name} ajoutée avec succès.")
                    except Exception as e:
                        logger.error(f"     -> Erreur critique lors de l'ajout de la colonne {column.name}: {e}")

            db.session.commit()

def init_database():
    app = create_app()
    
    with app.app_context():
        logger.info("=== Initialisation de la base de données ATM-RDC ===")

        if os.environ.get('DISABLE_POSTGIS'):
            logger.warning("!!! MODE SANS POSTGIS ACTIVÉ (DISABLE_POSTGIS=1) !!!")
            logger.warning("    Les colonnes géométriques seront créées en tant que TEXTE.")
        
        # 1. PostGIS Extension
        logger.info("1. Vérification de l'extension PostGIS...")
        try:
            db.session.execute(text('CREATE EXTENSION IF NOT EXISTS postgis'))
            db.session.commit()
            logger.info("   - Extension PostGIS vérifiée/activée.")
        except Exception as e:
            logger.warning(f"   - Attention: Impossible d'activer PostGIS (peut nécessiter des droits superuser): {e}")
            db.session.rollback()

        # 2. Tables Creation (Safe)
        logger.info("2. Vérification/Création des tables...")
        # db.create_all() checks for existence and creates only missing tables
        db.create_all()
        logger.info("   - Tables vérifiées.")

        # 2b. Schema Migration (Columns)
        check_and_update_schema(app)

        # 3. Data Seeding (Idempotent)
        logger.info("3. Insertion des données initiales (si manquantes)...")

        # RDC Airspace
        logger.info("   - Configuration de l'espace aérien (RDC Boundary)...")
        existing_airspace = Airspace.query.filter_by(name='RDC Airspace').first()
        if not existing_airspace:
            # Coordonnées du polygone RDC (simplifié pour démo)
            rdc_coords = [
                (12.2, -5.9), (12.5, -4.6), (13.1, -4.5), (14.0, -4.4), (15.8, -4.0),
                (16.2, -2.0), (16.5, -1.0), (17.8, -0.5), (18.5, 2.0), (19.5, 3.0),
                (21.0, 4.0), (24.0, 5.5), (27.4, 5.0), (28.0, 4.5), (29.0, 4.3),
                (29.5, 3.0), (29.8, 1.5), (29.6, -1.0), (29.2, -1.5), (29.0, -2.8),
                (29.5, -4.5), (29.0, -6.0), (30.5, -8.0), (30.0, -10.0), (28.5, -11.0),
                (27.5, -12.0), (25.0, -12.5), (22.0, -13.0), (21.5, -12.0), (20.0, -11.0),
                (18.0, -9.5), (16.0, -8.0), (13.0, -6.5), (12.2, -5.9)
            ]
            rdc_wkt = f"MULTIPOLYGON((({', '.join([f'{lon} {lat}' for lon, lat in rdc_coords])})))"

            rdc_airspace = Airspace(
                name='RDC Airspace',
                type='boundary',
                geom=rdc_wkt
            )
            db.session.add(rdc_airspace)
            logger.info("     -> Espace aérien créé.")
        else:
            logger.info("     -> Espace aérien existant.")

        # Users
        logger.info("   - Vérification des utilisateurs...")
        users_data = [
            {'username': 'admin', 'email': 'admin@rva.cd', 'role': 'superadmin', 'first_name': 'Administrateur', 'last_name': 'Système'},
            {'username': 'supervisor_kin', 'email': 'supervisor.kin@rva.cd', 'role': 'supervisor', 'first_name': 'Jean-Pierre', 'last_name': 'Mukendi'},
            {'username': 'controller1', 'email': 'controller1@rva.cd', 'role': 'controller', 'first_name': 'Marie', 'last_name': 'Kabila'},
            {'username': 'billing', 'email': 'facturation@rva.cd', 'role': 'billing', 'first_name': 'Patrick', 'last_name': 'Tshisekedi'},
            {'username': 'auditor', 'email': 'audit@rva.cd', 'role': 'auditor', 'first_name': 'Sophie', 'last_name': 'Lumumba'}
        ]
        
        for u_data in users_data:
            user = User.query.filter_by(username=u_data['username']).first()
            if not user:
                user = User(**u_data)
                user.set_password('password123')
                db.session.add(user)
                logger.info(f"     -> Utilisateur {u_data['username']} créé.")
            else:
                # Update critical fields if needed, or just skip
                pass

        # Airports
        logger.info("   - Vérification des aéroports RDC...")
        airports_data = [
            {'icao_code': 'FZAA', 'iata_code': 'FIH', 'name': "Aéroport International de N'Djili", 'city': 'Kinshasa', 'country': 'RDC', 'latitude': -4.3858, 'longitude': 15.4446, 'elevation_ft': 313, 'is_domestic': True, 'status': 'open'},
            {'icao_code': 'FZQA', 'iata_code': 'FBM', 'name': "Aéroport International de Lubumbashi", 'city': 'Lubumbashi', 'country': 'RDC', 'latitude': -11.5913, 'longitude': 27.5309, 'elevation_ft': 1295, 'is_domestic': True, 'status': 'open'},
            {'icao_code': 'FZNA', 'iata_code': 'GOM', 'name': "Aéroport International de Goma", 'city': 'Goma', 'country': 'RDC', 'latitude': -1.6708, 'longitude': 29.2385, 'elevation_ft': 1528, 'is_domestic': True, 'status': 'open'},
            {'icao_code': 'FZOA', 'iata_code': 'FKI', 'name': "Aéroport de Kisangani Bangoka", 'city': 'Kisangani', 'country': 'RDC', 'latitude': 0.4817, 'longitude': 25.3379, 'elevation_ft': 447, 'is_domestic': True, 'status': 'open'},
            {'icao_code': 'FZWA', 'iata_code': 'MJM', 'name': "Aéroport de Mbuji-Mayi", 'city': 'Mbuji-Mayi', 'country': 'RDC', 'latitude': -6.1212, 'longitude': 23.5690, 'elevation_ft': 609, 'is_domestic': True, 'status': 'open'},
            {'icao_code': 'FZRA', 'iata_code': 'KWZ', 'name': "Aéroport de Kolwezi", 'city': 'Kolwezi', 'country': 'RDC', 'latitude': -10.7659, 'longitude': 25.5057, 'elevation_ft': 1518, 'is_domestic': True, 'status': 'open'},
            {'icao_code': 'FZIC', 'iata_code': 'MAT', 'name': "Aéroport de Matadi Tshimpi", 'city': 'Matadi', 'country': 'RDC', 'latitude': -5.7996, 'longitude': 13.4404, 'elevation_ft': 350, 'is_domestic': True, 'status': 'open'},
            {'icao_code': 'FZKA', 'iata_code': 'KMN', 'name': "Aéroport de Kamina", 'city': 'Kamina', 'country': 'RDC', 'latitude': -8.6420, 'longitude': 25.2528, 'elevation_ft': 1060, 'is_domestic': True, 'status': 'open'},
            {'icao_code': 'FAOR', 'iata_code': 'JNB', 'name': "O.R. Tambo International", 'city': 'Johannesburg', 'country': 'RSA', 'latitude': -26.1392, 'longitude': 28.246, 'elevation_ft': 1694, 'is_domestic': False, 'status': 'open'},
            {'icao_code': 'HKJK', 'iata_code': 'NBO', 'name': "Jomo Kenyatta International", 'city': 'Nairobi', 'country': 'Kenya', 'latitude': -1.3192, 'longitude': 36.9278, 'elevation_ft': 1624, 'is_domestic': False, 'status': 'open'},
            {'icao_code': 'HAAB', 'iata_code': 'ADD', 'name': "Bole International", 'city': 'Addis Ababa', 'country': 'Ethiopia', 'latitude': 8.9779, 'longitude': 38.7993, 'elevation_ft': 2334, 'is_domestic': False, 'status': 'open'},
            {'icao_code': 'LFPG', 'iata_code': 'CDG', 'name': "Paris Charles de Gaulle", 'city': 'Paris', 'country': 'France', 'latitude': 49.0097, 'longitude': 2.5479, 'elevation_ft': 119, 'is_domestic': False, 'status': 'open'},
        ]
        
        for apt_data in airports_data:
            airport = Airport.query.filter_by(icao_code=apt_data['icao_code']).first()
            if not airport:
                airport = Airport(**apt_data)
                db.session.add(airport)

        # Airlines
        logger.info("   - Vérification des compagnies aériennes...")
        airlines_data = [
            {'iata_code': '8V', 'icao_code': 'WCG', 'name': 'Congo Airways', 'country': 'RDC', 'email': 'contact@congoairways.cd', 'is_active': True},
            {'iata_code': 'AF', 'icao_code': 'AFR', 'name': 'Air France', 'country': 'France', 'email': 'cargo@airfrance.fr', 'is_active': True},
            {'iata_code': 'ET', 'icao_code': 'ETH', 'name': 'Ethiopian Airlines', 'country': 'Ethiopia', 'email': 'cargo@ethiopianairlines.com', 'is_active': True},
            {'iata_code': 'KQ', 'icao_code': 'KQA', 'name': 'Kenya Airways', 'country': 'Kenya', 'email': 'cargo@kenya-airways.com', 'is_active': True},
            {'iata_code': 'SA', 'icao_code': 'SAA', 'name': 'South African Airways', 'country': 'RSA', 'email': 'cargo@flysaa.com', 'is_active': True},
            {'iata_code': 'RW', 'icao_code': 'RWD', 'name': 'RwandAir', 'country': 'Rwanda', 'email': 'cargo@rwandair.com', 'is_active': True},
            {'iata_code': 'QR', 'icao_code': 'QTR', 'name': 'Qatar Airways', 'country': 'Qatar', 'email': 'cargo@qatarairways.com', 'is_active': True},
            {'iata_code': 'EK', 'icao_code': 'UAE', 'name': 'Emirates', 'country': 'UAE', 'email': 'cargo@emirates.com', 'is_active': True},
        ]
        
        for al_data in airlines_data:
            airline = Airline.query.filter_by(iata_code=al_data['iata_code']).first()
            if not airline:
                airline = Airline(**al_data)
                db.session.add(airline)

        # Aircraft
        logger.info("   - Vérification des aéronefs...")
        aircraft_data = [
            {'icao24': '4L0001', 'registration': '9Q-CDC', 'model': 'Boeing 737-800', 'type_code': 'B738', 'operator': 'Congo Airways', 'operator_iata': '8V', 'mtow': 79010, 'category': 'commercial'},
            {'icao24': '4L0002', 'registration': '9Q-CDD', 'model': 'Airbus A320', 'type_code': 'A320', 'operator': 'Congo Airways', 'operator_iata': '8V', 'mtow': 77000, 'category': 'commercial'},
            {'icao24': 'F-GKXS', 'registration': 'F-GKXS', 'model': 'Airbus A330-200', 'type_code': 'A332', 'operator': 'Air France', 'operator_iata': 'AF', 'mtow': 230000, 'category': 'commercial'},
            {'icao24': 'ET-AVJ', 'registration': 'ET-AVJ', 'model': 'Boeing 787-9', 'type_code': 'B789', 'operator': 'Ethiopian Airlines', 'operator_iata': 'ET', 'mtow': 254011, 'category': 'commercial'},
            {'icao24': '5Y-KZA', 'registration': '5Y-KZA', 'model': 'Boeing 737-800', 'type_code': 'B738', 'operator': 'Kenya Airways', 'operator_iata': 'KQ', 'mtow': 79010, 'category': 'commercial'},
            {'icao24': 'ZS-SNA', 'registration': 'ZS-SNA', 'model': 'Airbus A340-300', 'type_code': 'A343', 'operator': 'South African Airways', 'operator_iata': 'SA', 'mtow': 276500, 'category': 'commercial'},
            {'icao24': '9XR-WP', 'registration': '9XR-WP', 'model': 'Airbus A330-200', 'type_code': 'A332', 'operator': 'RwandAir', 'operator_iata': 'RW', 'mtow': 230000, 'category': 'commercial'},
            {'icao24': 'A7-BFA', 'registration': 'A7-BFA', 'model': 'Boeing 777F', 'type_code': 'B77F', 'operator': 'Qatar Airways', 'operator_iata': 'QR', 'mtow': 347800, 'category': 'cargo'},
            {'icao24': '9Q-CHC', 'registration': '9Q-CHC', 'model': 'Cessna 208 Caravan', 'type_code': 'C208', 'operator': 'CAA', 'operator_iata': '', 'mtow': 3629, 'category': 'private'},
            {'icao24': '9Q-CMK', 'registration': '9Q-CMK', 'model': 'ATR 72-500', 'type_code': 'AT75', 'operator': 'Malu Aviation', 'operator_iata': '', 'mtow': 22800, 'category': 'commercial'},
        ]
        
        for ac_data in aircraft_data:
            ac = Aircraft.query.filter_by(icao24=ac_data['icao24']).first()
            if not ac:
                ac = Aircraft(**ac_data)
                db.session.add(ac)

        # Tariffs
        logger.info("   - Configuration des tarifs...")
        tariffs_data = [
            {'name': 'Redevance de survol par km', 'code': 'SURVOL_KM', 'value': 0.85, 'unit': 'USD/km', 'description': 'Tarif appliqué par kilomètre de survol du territoire RDC'},
            {'name': 'Redevance de survol par minute', 'code': 'SURVOL_MINUTE', 'value': 12.50, 'unit': 'USD/min', 'description': 'Tarif appliqué par minute de survol'},
            {'name': 'Redevance survol Hybride (Temps)', 'code': 'SURVOL_HYBRID_TIME', 'value': 6.00, 'unit': 'USD/min', 'description': 'Partie temps pour le mode hybride'},
            {'name': 'Redevance survol Hybride (Distance)', 'code': 'SURVOL_HYBRID_DIST', 'value': 0.40, 'unit': 'USD/km', 'description': 'Partie distance pour le mode hybride'},
            {'name': 'Redevance atterrissage base', 'code': 'LANDING_BASE', 'value': 150.0, 'unit': 'USD', 'description': 'Tarif de base pour tout atterrissage sur un aéroport RDC'},
            {'name': 'Stationnement par heure', 'code': 'PARKING_HOUR', 'value': 25.0, 'unit': 'USD/h', 'description': 'Tarif de stationnement après la première heure gratuite'},
            {'name': 'Surtaxe de nuit', 'code': 'NIGHT_SURCHARGE', 'value': 25.0, 'unit': '%', 'description': 'Pourcentage de surtaxe appliqué entre 18h00 et 06h00'},
            {'name': 'TVA', 'code': 'TVA_RATE', 'value': 16.0, 'unit': '%', 'description': 'Taux de TVA applicable en RDC'},
            {'name': 'Redevance tonnage', 'code': 'TONNAGE_RATE', 'value': 2.50, 'unit': 'USD/tonne', 'description': 'Tarif appliqué par tonne de MTOW'},
            {'name': 'Service de navigation', 'code': 'NAV_SERVICE', 'value': 50.0, 'unit': 'USD', 'description': 'Redevance pour les services de navigation aérienne'},
            {'name': 'Balisage de piste', 'code': 'RUNWAY_LIGHTING', 'value': 75.0, 'unit': 'USD', 'description': 'Redevance pour le balisage lumineux de nuit'},
        ]
        
        for tariff_data in tariffs_data:
            tariff = TariffConfig.query.filter_by(code=tariff_data['code']).first()
            if not tariff:
                tariff = TariffConfig(**tariff_data)
                tariff.effective_date = date.today()
                db.session.add(tariff)
            # else: Do not overwrite existing values (admin might have changed them)
        
        db.session.commit()
        
        # System Configs
        logger.info("   - Configuration du système...")
        sys_configs_data = [
            {'key': 'system_active', 'value': 'false', 'description': 'État global du système (Master Switch)', 'category': 'system', 'value_type': 'bool', 'is_editable': False},
            {'key': 'rva_contact_phone', 'value': '+2431234567890', 'description': 'Numéro de téléphone de contact sur les factures', 'category': 'invoice', 'value_type': 'string', 'is_editable': True},
            {'key': 'OVERFLIGHT_BILLING_MODE', 'value': 'DISTANCE', 'description': 'Mode de facturation survol: DISTANCE, TIME, HYBRID', 'category': 'invoice', 'value_type': 'string', 'is_editable': True},
            {'key': 'app_name', 'value': 'ATM-RDC', 'description': 'Nom de l\'application', 'category': 'branding', 'value_type': 'string', 'is_editable': True},
            {'key': 'logo_path', 'value': '', 'description': 'Logo de l\'application', 'category': 'branding', 'value_type': 'file', 'is_editable': True},
            {'key': 'favicon_path', 'value': '', 'description': 'Favicon de l\'application', 'category': 'branding', 'value_type': 'file', 'is_editable': True},
            {'key': 'enabled_languages', 'value': '["fr", "en"]', 'description': 'Langues activées', 'category': 'system', 'value_type': 'json', 'is_editable': False},
            {'key': 'unit_altitude', 'value': 'ft', 'description': "Unité d'altitude (ft, m)", 'category': 'display', 'value_type': 'select', 'is_editable': True},
            {'key': 'unit_speed', 'value': 'kts', 'description': 'Unité de vitesse (kts, km/h, Mach)', 'category': 'display', 'value_type': 'select', 'is_editable': True},
            {'key': 'precision_decimals', 'value': '2', 'description': "Nombre de décimales pour l'affichage", 'category': 'display', 'value_type': 'int', 'is_editable': True},
            {'key': 'timezone', 'value': 'UTC', 'description': "Fuseau horaire de l'application", 'category': 'system', 'value_type': 'select', 'is_editable': True},
        ]

        for conf_data in sys_configs_data:
            conf = SystemConfig.query.filter_by(key=conf_data['key']).first()
            if not conf:
                conf = SystemConfig(**conf_data)
                db.session.add(conf)

        db.session.commit()
        
        # Note: Demonstration flights/landings/alerts are not seeded in production usually,
        # or should be checked. For now I'll skip re-seeding them to avoid duplicates if run multiple times,
        # unless I implement complex checks. Given "init_db" usually implies setting up the ENV,
        # I will assume we only want static data seeded idempotently.
        # But to be safe and match original behavior, I will check if Flight table is empty.
        
        if Flight.query.count() == 0:
            logger.info("   - Création des données de démonstration (Vols, etc.)...")

            # Need to re-fetch aircraft objects to link them
            # This logic assumes the aircrafts exist (which they should now)

            # ... (Rest of flight creation logic, strictly only if table is empty)
            # To simplify, I will copy the logic but wrap it in the check.

            aircraft_list = Aircraft.query.all() # Used to have IDs available? Actually original code used hardcoded IDs like `aircraft_id=1`.
            # This is risky if IDs are different.
            # I should lookup by registration or ICAO24.

            # Helper to get ID
            def get_ac_id(icao24):
                ac = Aircraft.query.filter_by(icao24=icao24).first()
                return ac.id if ac else None

            flights = [
                Flight(callsign='WCG101', flight_number='8V101', aircraft_id=get_ac_id('4L0001'),
                       departure_icao='FZAA', arrival_icao='FZQA',
                       scheduled_departure=datetime.now() - timedelta(hours=2),
                       scheduled_arrival=datetime.now() + timedelta(hours=1),
                       flight_status='in_flight', flight_type='commercial', is_domestic=True),
                Flight(callsign='AFR892', flight_number='AF892', aircraft_id=get_ac_id('F-GKXS'),
                       departure_icao='LFPG', arrival_icao='FZAA',
                       scheduled_departure=datetime.now() - timedelta(hours=8),
                       scheduled_arrival=datetime.now() + timedelta(hours=2),
                       flight_status='in_flight', flight_type='commercial', is_domestic=False),
                Flight(callsign='ETH507', flight_number='ET507', aircraft_id=get_ac_id('ET-AVJ'),
                       departure_icao='HAAB', arrival_icao='FZAA',
                       scheduled_departure=datetime.now() - timedelta(hours=3),
                       scheduled_arrival=datetime.now() + timedelta(hours=1, minutes=30),
                       flight_status='in_flight', flight_type='commercial', is_domestic=False),
                Flight(callsign='KQA442', flight_number='KQ442', aircraft_id=get_ac_id('5Y-KZA'),
                       departure_icao='HKJK', arrival_icao='FZNA',
                       scheduled_departure=datetime.now() - timedelta(hours=1),
                       scheduled_arrival=datetime.now() + timedelta(hours=2),
                       flight_status='in_flight', flight_type='commercial', is_domestic=False),
                Flight(callsign='SAA076', flight_number='SA076', aircraft_id=get_ac_id('ZS-SNA'),
                       departure_icao='FAOR', arrival_icao='FZQA',
                       scheduled_departure=datetime.now() - timedelta(hours=4),
                       scheduled_arrival=datetime.now() + timedelta(minutes=45),
                       flight_status='approaching', flight_type='commercial', is_domestic=False),
                Flight(callsign='WCG205', flight_number='8V205', aircraft_id=get_ac_id('4L0002'),
                       departure_icao='FZQA', arrival_icao='FZNA',
                       scheduled_departure=datetime.now() + timedelta(hours=1),
                       scheduled_arrival=datetime.now() + timedelta(hours=3),
                       flight_status='scheduled', flight_type='commercial', is_domestic=True),
                Flight(callsign='QTR8421', flight_number='QR8421', aircraft_id=get_ac_id('A7-BFA'),
                       departure_icao='HAAB', arrival_icao='FAOR',
                       scheduled_departure=datetime.now() - timedelta(hours=2),
                       scheduled_arrival=datetime.now() + timedelta(hours=3),
                       flight_status='in_flight', flight_type='cargo', is_domestic=False),
            ]

            # Filter out any None aircraft_ids
            flights = [f for f in flights if f.aircraft_id is not None]

            for flight in flights:
                db.session.add(flight)

            db.session.commit()

            logger.info("     -> Vols de démonstration créés.")

            # Now handle related demo data which relied on flight IDs.
            # This is complex to do robustly without strictly defining the flight IDs.
            # But since this is just demo data populate only if empty, it's acceptable.
            # I will try to fetch the flights back to get their IDs.

            # ... skipping deep dependency demo data like Overflights/Landings linked to specific dynamic Flight IDs for now
            # unless strictly necessary, as it complicates the script significantly.
            # The original script hardcoded `flight_id=7` etc. which is brittle.
            # I will implement a basic lookup.

            f_qtr = Flight.query.filter_by(callsign='QTR8421').first()
            f_af = Flight.query.filter_by(callsign='AFR892').first()
            f_wcg = Flight.query.filter_by(callsign='WCG101').first()
            f_eth = Flight.query.filter_by(callsign='ETH507').first()

            if f_qtr and f_af:
                overflights = [
                    Overflight(
                        session_id='OVF-2024-00001',
                        flight_id=f_qtr.id,
                        aircraft_id=f_qtr.aircraft_id,
                        entry_lat=-5.0,
                        entry_lon=12.5,
                        entry_alt=35000,
                        entry_time=datetime.now() - timedelta(hours=1, minutes=30),
                        exit_lat=-8.5,
                        exit_lon=28.0,
                        exit_time=datetime.now() - timedelta(minutes=15),
                        duration_minutes=75,
                        distance_km=1450,
                        status='completed',
                        is_billed=False
                    ),
                    Overflight(
                        session_id='OVF-2024-00002',
                        flight_id=f_af.id,
                        aircraft_id=f_af.aircraft_id,
                        entry_lat=4.5,
                        entry_lon=18.5,
                        entry_alt=38000,
                        entry_time=datetime.now() - timedelta(minutes=45),
                        status='active',
                        is_billed=False
                    ),
                ]
                for ovf in overflights:
                    db.session.add(ovf)

            if f_wcg:
                landings = [
                    Landing(
                        flight_id=f_wcg.id,
                        aircraft_id=f_wcg.aircraft_id,
                        airport_icao='FZQA',
                        touchdown_time=datetime.now() - timedelta(hours=3),
                        parking_start=datetime.now() - timedelta(hours=2, minutes=45),
                        parking_end=datetime.now() - timedelta(hours=1),
                        parking_duration_minutes=105,
                        is_night=False,
                        is_billed=True,
                        status='completed'
                    ),
                ]
                for landing in landings:
                    db.session.add(landing)

            if f_eth and f_qtr:
                alerts = [
                    Alert(
                        alert_type='squawk_7700',
                        severity='critical',
                        title='Urgence déclarée',
                        message='Vol ETH507 a déclaré une urgence (Squawk 7700)',
                        flight_id=f_eth.id,
                        is_acknowledged=False
                    ),
                    Alert(
                        alert_type='new_overflight',
                        severity='info',
                        title='Nouveau survol détecté',
                        message='Aéronef QTR8421 entré dans l\'espace aérien RDC',
                        flight_id=f_qtr.id,
                        is_acknowledged=True,
                        acknowledged_at=datetime.now() - timedelta(minutes=30)
                    ),
                ]
                for alert in alerts:
                    db.session.add(alert)

            db.session.commit()
            logger.info("     -> Survols/Atterrissages/Alertes de démo créés.")
        else:
            logger.info("   - Données de vols existantes, pas de réinsertion de démo.")

        logger.info("\n=== Base de données initialisée avec succès (Mode Idempotent) ===")

        # Stats
        logger.info(f"\nStatistiques:")
        logger.info(f"  - Utilisateurs: {User.query.count()}")
        logger.info(f"  - Aéroports: {Airport.query.count()}")
        logger.info(f"  - Compagnies aériennes: {Airline.query.count()}")
        logger.info(f"  - Aéronefs: {Aircraft.query.count()}")
        logger.info(f"  - Tarifs: {TariffConfig.query.count()}")
        logger.info(f"  - Vols: {Flight.query.count()}")
        logger.info(f"  - Survols: {Overflight.query.count()}")
        logger.info(f"  - Atterrissages: {Landing.query.count()}")
        logger.info(f"  - Alertes: {Alert.query.count()}")

if __name__ == '__main__':
    init_database()
