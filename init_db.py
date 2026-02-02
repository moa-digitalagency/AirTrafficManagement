#!/usr/bin/env python3
"""
Script d'initialisation de la base de données PostgreSQL
Air Traffic Management - RDC (ATM-RDC)

Ce script crée toutes les tables nécessaires et insère les données initiales.
"""

import os
import sys
from datetime import datetime, date, timedelta
import random

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from flask import Flask
from models import (db, User, Aircraft, Airport, Airline, TariffConfig, Flight, 
                    Overflight, Landing, Alert, FlightPosition, FlightRoute, 
                    Invoice, InvoiceLineItem, Notification, SystemConfig, AuditLog)


def create_app():
    app = Flask(__name__)
    app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL')
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['SECRET_KEY'] = os.environ.get('SESSION_SECRET', 'dev-secret-key')
    db.init_app(app)
    return app


def init_database():
    app = create_app()
    
    with app.app_context():
        print("=== Initialisation de la base de données ATM-RDC ===\n")
        
        print("1. Suppression des tables existantes...")
        db.drop_all()
        
        print("2. Création des tables...")
        db.create_all()
        
        print("3. Insertion des données initiales...\n")
        
        print("   - Création des utilisateurs...")
        users = [
            User(
                username='admin',
                email='admin@rva.cd',
                role='superadmin',
                first_name='Administrateur',
                last_name='Système'
            ),
            User(
                username='supervisor_kin',
                email='supervisor.kin@rva.cd',
                role='supervisor',
                first_name='Jean-Pierre',
                last_name='Mukendi'
            ),
            User(
                username='controller1',
                email='controller1@rva.cd',
                role='controller',
                first_name='Marie',
                last_name='Kabila'
            ),
            User(
                username='billing',
                email='facturation@rva.cd',
                role='billing',
                first_name='Patrick',
                last_name='Tshisekedi'
            ),
            User(
                username='auditor',
                email='audit@rva.cd',
                role='auditor',
                first_name='Sophie',
                last_name='Lumumba'
            )
        ]
        
        for user in users:
            user.set_password('password123')
            db.session.add(user)
        
        print("   - Création des aéroports RDC...")
        airports = [
            Airport(icao_code='FZAA', iata_code='FIH', name="Aéroport International de N'Djili", 
                    city='Kinshasa', country='RDC', latitude=-4.3858, longitude=15.4446, elevation_ft=313, is_domestic=True, status='open'),
            Airport(icao_code='FZQA', iata_code='FBM', name="Aéroport International de Lubumbashi",
                    city='Lubumbashi', country='RDC', latitude=-11.5913, longitude=27.5309, elevation_ft=1295, is_domestic=True, status='open'),
            Airport(icao_code='FZNA', iata_code='GOM', name="Aéroport International de Goma",
                    city='Goma', country='RDC', latitude=-1.6708, longitude=29.2385, elevation_ft=1528, is_domestic=True, status='open'),
            Airport(icao_code='FZOA', iata_code='FKI', name="Aéroport de Kisangani Bangoka",
                    city='Kisangani', country='RDC', latitude=0.4817, longitude=25.3379, elevation_ft=447, is_domestic=True, status='open'),
            Airport(icao_code='FZWA', iata_code='MJM', name="Aéroport de Mbuji-Mayi",
                    city='Mbuji-Mayi', country='RDC', latitude=-6.1212, longitude=23.5690, elevation_ft=609, is_domestic=True, status='open'),
            Airport(icao_code='FZRA', iata_code='KWZ', name="Aéroport de Kolwezi",
                    city='Kolwezi', country='RDC', latitude=-10.7659, longitude=25.5057, elevation_ft=1518, is_domestic=True, status='open'),
            Airport(icao_code='FZIC', iata_code='MAT', name="Aéroport de Matadi Tshimpi",
                    city='Matadi', country='RDC', latitude=-5.7996, longitude=13.4404, elevation_ft=350, is_domestic=True, status='open'),
            Airport(icao_code='FZKA', iata_code='KMN', name="Aéroport de Kamina",
                    city='Kamina', country='RDC', latitude=-8.6420, longitude=25.2528, elevation_ft=1060, is_domestic=True, status='open'),
            Airport(icao_code='FAOR', iata_code='JNB', name="O.R. Tambo International",
                    city='Johannesburg', country='RSA', latitude=-26.1392, longitude=28.246, elevation_ft=1694, is_domestic=False, status='open'),
            Airport(icao_code='HKJK', iata_code='NBO', name="Jomo Kenyatta International",
                    city='Nairobi', country='Kenya', latitude=-1.3192, longitude=36.9278, elevation_ft=1624, is_domestic=False, status='open'),
            Airport(icao_code='HAAB', iata_code='ADD', name="Bole International",
                    city='Addis Ababa', country='Ethiopia', latitude=8.9779, longitude=38.7993, elevation_ft=2334, is_domestic=False, status='open'),
            Airport(icao_code='LFPG', iata_code='CDG', name="Paris Charles de Gaulle",
                    city='Paris', country='France', latitude=49.0097, longitude=2.5479, elevation_ft=119, is_domestic=False, status='open'),
        ]
        
        for airport in airports:
            db.session.add(airport)
        
        print("   - Création des compagnies aériennes...")
        airlines = [
            Airline(iata_code='8V', icao_code='WCG', name='Congo Airways', country='RDC', 
                    email='contact@congoairways.cd', is_active=True),
            Airline(iata_code='AF', icao_code='AFR', name='Air France', country='France',
                    email='cargo@airfrance.fr', is_active=True),
            Airline(iata_code='ET', icao_code='ETH', name='Ethiopian Airlines', country='Ethiopia',
                    email='cargo@ethiopianairlines.com', is_active=True),
            Airline(iata_code='KQ', icao_code='KQA', name='Kenya Airways', country='Kenya',
                    email='cargo@kenya-airways.com', is_active=True),
            Airline(iata_code='SA', icao_code='SAA', name='South African Airways', country='RSA',
                    email='cargo@flysaa.com', is_active=True),
            Airline(iata_code='RW', icao_code='RWD', name='RwandAir', country='Rwanda',
                    email='cargo@rwandair.com', is_active=True),
            Airline(iata_code='QR', icao_code='QTR', name='Qatar Airways', country='Qatar',
                    email='cargo@qatarairways.com', is_active=True),
            Airline(iata_code='EK', icao_code='UAE', name='Emirates', country='UAE',
                    email='cargo@emirates.com', is_active=True),
        ]
        
        for airline in airlines:
            db.session.add(airline)
        
        print("   - Création des aéronefs...")
        aircraft = [
            Aircraft(icao24='4L0001', registration='9Q-CDC', model='Boeing 737-800', type_code='B738',
                     operator='Congo Airways', operator_iata='8V', mtow=79010, category='commercial'),
            Aircraft(icao24='4L0002', registration='9Q-CDD', model='Airbus A320', type_code='A320',
                     operator='Congo Airways', operator_iata='8V', mtow=77000, category='commercial'),
            Aircraft(icao24='F-GKXS', registration='F-GKXS', model='Airbus A330-200', type_code='A332',
                     operator='Air France', operator_iata='AF', mtow=230000, category='commercial'),
            Aircraft(icao24='ET-AVJ', registration='ET-AVJ', model='Boeing 787-9', type_code='B789',
                     operator='Ethiopian Airlines', operator_iata='ET', mtow=254011, category='commercial'),
            Aircraft(icao24='5Y-KZA', registration='5Y-KZA', model='Boeing 737-800', type_code='B738',
                     operator='Kenya Airways', operator_iata='KQ', mtow=79010, category='commercial'),
            Aircraft(icao24='ZS-SNA', registration='ZS-SNA', model='Airbus A340-300', type_code='A343',
                     operator='South African Airways', operator_iata='SA', mtow=276500, category='commercial'),
            Aircraft(icao24='9XR-WP', registration='9XR-WP', model='Airbus A330-200', type_code='A332',
                     operator='RwandAir', operator_iata='RW', mtow=230000, category='commercial'),
            Aircraft(icao24='A7-BFA', registration='A7-BFA', model='Boeing 777F', type_code='B77F',
                     operator='Qatar Airways', operator_iata='QR', mtow=347800, category='cargo'),
            Aircraft(icao24='9Q-CHC', registration='9Q-CHC', model='Cessna 208 Caravan', type_code='C208',
                     operator='CAA', operator_iata='', mtow=3629, category='private'),
            Aircraft(icao24='9Q-CMK', registration='9Q-CMK', model='ATR 72-500', type_code='AT75',
                     operator='Malu Aviation', operator_iata='', mtow=22800, category='commercial'),
        ]
        
        for ac in aircraft:
            db.session.add(ac)
        
        print("   - Configuration des tarifs...")
        tariffs = [
            TariffConfig(name='Redevance de survol par km', code='SURVOL_KM', value=0.85, unit='USD/km',
                        description='Tarif appliqué par kilomètre de survol du territoire RDC'),
            TariffConfig(name='Redevance atterrissage base', code='LANDING_BASE', value=150.0, unit='USD',
                        description='Tarif de base pour tout atterrissage sur un aéroport RDC'),
            TariffConfig(name='Stationnement par heure', code='PARKING_HOUR', value=25.0, unit='USD/h',
                        description='Tarif de stationnement après la première heure gratuite'),
            TariffConfig(name='Surtaxe de nuit', code='NIGHT_SURCHARGE', value=25.0, unit='%',
                        description='Pourcentage de surtaxe appliqué entre 18h00 et 06h00'),
            TariffConfig(name='TVA', code='TVA_RATE', value=16.0, unit='%',
                        description='Taux de TVA applicable en RDC'),
            TariffConfig(name='Redevance tonnage', code='TONNAGE_RATE', value=2.50, unit='USD/tonne',
                        description='Tarif appliqué par tonne de MTOW'),
            TariffConfig(name='Service de navigation', code='NAV_SERVICE', value=50.0, unit='USD',
                        description='Redevance pour les services de navigation aérienne'),
            TariffConfig(name='Balisage de piste', code='RUNWAY_LIGHTING', value=75.0, unit='USD',
                        description='Redevance pour le balisage lumineux de nuit'),
        ]
        
        for tariff in tariffs:
            tariff.effective_date = date.today()
            db.session.add(tariff)
        
        db.session.commit()
        
        print("   - Création des vols de démonstration...")
        
        aircraft_list = Aircraft.query.all()
        
        flights = [
            Flight(callsign='WCG101', flight_number='8V101', aircraft_id=1,
                   departure_icao='FZAA', arrival_icao='FZQA',
                   scheduled_departure=datetime.now() - timedelta(hours=2),
                   scheduled_arrival=datetime.now() + timedelta(hours=1),
                   flight_status='in_flight', flight_type='commercial', is_domestic=True),
            Flight(callsign='AFR892', flight_number='AF892', aircraft_id=3,
                   departure_icao='LFPG', arrival_icao='FZAA',
                   scheduled_departure=datetime.now() - timedelta(hours=8),
                   scheduled_arrival=datetime.now() + timedelta(hours=2),
                   flight_status='in_flight', flight_type='commercial', is_domestic=False),
            Flight(callsign='ETH507', flight_number='ET507', aircraft_id=4,
                   departure_icao='HAAB', arrival_icao='FZAA',
                   scheduled_departure=datetime.now() - timedelta(hours=3),
                   scheduled_arrival=datetime.now() + timedelta(hours=1, minutes=30),
                   flight_status='in_flight', flight_type='commercial', is_domestic=False),
            Flight(callsign='KQA442', flight_number='KQ442', aircraft_id=5,
                   departure_icao='HKJK', arrival_icao='FZNA',
                   scheduled_departure=datetime.now() - timedelta(hours=1),
                   scheduled_arrival=datetime.now() + timedelta(hours=2),
                   flight_status='in_flight', flight_type='commercial', is_domestic=False),
            Flight(callsign='SAA076', flight_number='SA076', aircraft_id=6,
                   departure_icao='FAOR', arrival_icao='FZQA',
                   scheduled_departure=datetime.now() - timedelta(hours=4),
                   scheduled_arrival=datetime.now() + timedelta(minutes=45),
                   flight_status='approaching', flight_type='commercial', is_domestic=False),
            Flight(callsign='WCG205', flight_number='8V205', aircraft_id=2,
                   departure_icao='FZQA', arrival_icao='FZNA',
                   scheduled_departure=datetime.now() + timedelta(hours=1),
                   scheduled_arrival=datetime.now() + timedelta(hours=3),
                   flight_status='scheduled', flight_type='commercial', is_domestic=True),
            Flight(callsign='QTR8421', flight_number='QR8421', aircraft_id=8,
                   departure_icao='HAAB', arrival_icao='FAOR',
                   scheduled_departure=datetime.now() - timedelta(hours=2),
                   scheduled_arrival=datetime.now() + timedelta(hours=3),
                   flight_status='in_flight', flight_type='cargo', is_domestic=False),
        ]
        
        for flight in flights:
            db.session.add(flight)
        
        db.session.commit()
        
        print("   - Création des survols de démonstration...")
        
        overflights = [
            Overflight(
                session_id='OVF-2024-00001',
                flight_id=7,
                aircraft_id=8,
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
                flight_id=3,
                aircraft_id=3,
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
        
        print("   - Création des atterrissages de démonstration...")
        
        landings = [
            Landing(
                flight_id=1,
                aircraft_id=1,
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
        
        print("   - Création des alertes...")
        
        alerts = [
            Alert(
                alert_type='squawk_7700',
                severity='critical',
                title='Urgence déclarée',
                message='Vol ETH507 a déclaré une urgence (Squawk 7700)',
                flight_id=3,
                is_acknowledged=False
            ),
            Alert(
                alert_type='new_overflight',
                severity='info',
                title='Nouveau survol détecté',
                message='Aéronef QTR8421 entré dans l\'espace aérien RDC',
                flight_id=7,
                is_acknowledged=True,
                acknowledged_at=datetime.now() - timedelta(minutes=30)
            ),
        ]
        
        for alert in alerts:
            db.session.add(alert)
        
        db.session.commit()
        
        print("\n=== Base de données initialisée avec succès! ===")
        print(f"\nStatistiques:")
        print(f"  - Utilisateurs: {User.query.count()}")
        print(f"  - Aéroports: {Airport.query.count()}")
        print(f"  - Compagnies aériennes: {Airline.query.count()}")
        print(f"  - Aéronefs: {Aircraft.query.count()}")
        print(f"  - Tarifs: {TariffConfig.query.count()}")
        print(f"  - Vols: {Flight.query.count()}")
        print(f"  - Survols: {Overflight.query.count()}")
        print(f"  - Atterrissages: {Landing.query.count()}")
        print(f"  - Alertes: {Alert.query.count()}")
        
        print("\n=== Comptes utilisateurs ===")
        print("  admin / password123 (SuperAdmin)")
        print("  supervisor_kin / password123 (Superviseur)")
        print("  controller1 / password123 (Contrôleur)")
        print("  billing / password123 (Facturation)")
        print("  auditor / password123 (Auditeur)")


if __name__ == '__main__':
    init_database()
