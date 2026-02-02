"""
Configuration Settings for ATM-RDC
Air Traffic Management System - Democratic Republic of Congo
"""
import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    # Flask Core
    SECRET_KEY = os.environ.get('SESSION_SECRET', 'atm-rdc-secret-key-2024')
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ENGINE_OPTIONS = {
        'pool_pre_ping': True,
        'pool_recycle': 300,
    }
    
    # CSRF Protection
    WTF_CSRF_ENABLED = True
    WTF_CSRF_SECRET_KEY = os.environ.get('SESSION_SECRET', 'csrf-secret-key')
    
    # ============================================
    # EXTERNAL FLIGHT DATA APIs
    # ============================================
    # AviationStack API (Primary source for flight tracking)
    # Documentation: https://aviationstack.com/documentation
    AVIATIONSTACK_API_KEY = os.environ.get('AVIATIONSTACK_API_KEY', '')
    AVIATIONSTACK_API_URL = os.environ.get('AVIATIONSTACK_API_URL', 'http://api.aviationstack.com/v1')
    
    # ADSBexchange API (Fallback/Secondary source)
    # Documentation: https://www.adsbexchange.com/data/
    ADSBEXCHANGE_API_KEY = os.environ.get('ADSBEXCHANGE_API_KEY', '')
    ADSBEXCHANGE_API_URL = os.environ.get('ADSBEXCHANGE_API_URL', 'https://adsbexchange.com/api/aircraft/v2')
    
    # ============================================
    # WEATHER DATA APIs
    # ============================================
    # OpenWeatherMap API (Weather overlay for radar)
    # Documentation: https://openweathermap.org/api
    OPENWEATHERMAP_API_KEY = os.environ.get('OPENWEATHERMAP_API_KEY', '')
    OPENWEATHERMAP_API_URL = os.environ.get('OPENWEATHERMAP_API_URL', 'https://api.openweathermap.org/data/2.5')
    
    # Aviation Weather (METAR/TAF data)
    # Documentation: https://aviationweather.gov/data/api/
    AVIATIONWEATHER_API_URL = os.environ.get('AVIATIONWEATHER_API_URL', 'https://aviationweather.gov/api/data')
    
    # ============================================
    # REDIS / CELERY CONFIGURATION
    # ============================================
    REDIS_URL = os.environ.get('REDIS_URL', 'redis://localhost:6379/0')
    CELERY_BROKER_URL = os.environ.get('REDIS_URL', 'redis://localhost:6379/0')
    CELERY_RESULT_BACKEND = os.environ.get('REDIS_URL', 'redis://localhost:6379/0')
    
    # ============================================
    # EMAIL CONFIGURATION (Invoice sending)
    # ============================================
    MAIL_SERVER = os.environ.get('MAIL_SERVER', 'smtp.gmail.com')
    MAIL_PORT = int(os.environ.get('MAIL_PORT', 587))
    MAIL_USE_TLS = True
    MAIL_USERNAME = os.environ.get('MAIL_USERNAME', '')
    MAIL_PASSWORD = os.environ.get('MAIL_PASSWORD', '')
    MAIL_DEFAULT_SENDER = os.environ.get('MAIL_DEFAULT_SENDER', 'facturation@rva.cd')
    
    # ============================================
    # FILE UPLOADS
    # ============================================
    UPLOAD_FOLDER = 'statics/uploads'
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB max
    
    # ============================================
    # RDC TARIFICATION (Configurable by Admin)
    # ============================================
    RDC_TARIFS = {
        # Overflight charges
        'survol_par_km': 0.85,           # USD per km flown over RDC
        'tonnage_par_tonne': 2.50,       # USD per tonne MTOW
        
        # Landing charges
        'atterrissage_base': 150.0,      # Base landing fee USD
        'atterrissage_par_tonne': 3.00,  # USD per tonne for landing
        
        # Parking charges
        'stationnement_heure': 25.0,     # USD per hour (1st hour free)
        'stationnement_gratuit_heures': 1,
        
        # Night surcharge (18h00 - 06h00)
        'surtaxe_nuit_pct': 0.25,        # 25% surcharge
        'heure_debut_nuit': 18,
        'heure_fin_nuit': 6,
        
        # Taxes
        'tva_pct': 0.16,                 # 16% VAT
    }
    
    # ============================================
    # RDC AIRPORTS (ICAO codes)
    # ============================================
    AIRPORTS_RDC = {
        'FZAA': {'name': "N'Djili International", 'city': 'Kinshasa', 'lat': -4.3858, 'lon': 15.4446, 'elevation': 1027},
        'FZQA': {'name': 'Lubumbashi International', 'city': 'Lubumbashi', 'lat': -11.5913, 'lon': 27.5309, 'elevation': 1295},
        'FZNA': {'name': 'Goma International', 'city': 'Goma', 'lat': -1.6708, 'lon': 29.2385, 'elevation': 5089},
        'FZOA': {'name': 'Kisangani Bangoka', 'city': 'Kisangani', 'lat': 0.4817, 'lon': 25.3379, 'elevation': 1289},
        'FZWA': {'name': 'Mbuji-Mayi', 'city': 'Mbuji-Mayi', 'lat': -6.1212, 'lon': 23.5690, 'elevation': 2221},
        'FZIC': {'name': 'Matadi Tshimpi', 'city': 'Matadi', 'lat': -5.7996, 'lon': 13.4404, 'elevation': 1115},
        'FZKA': {'name': 'Kamina', 'city': 'Kamina', 'lat': -8.6420, 'lon': 25.2528, 'elevation': 3543},
        'FZRA': {'name': 'Kolwezi', 'city': 'Kolwezi', 'lat': -10.7659, 'lon': 25.5057, 'elevation': 5007},
        'FZMA': {'name': 'Manono', 'city': 'Manono', 'lat': -7.2889, 'lon': 27.3944, 'elevation': 2077},
        'FZAB': {'name': "N'Dolo", 'city': 'Kinshasa', 'lat': -4.3266, 'lon': 15.3275, 'elevation': 915},
        'FZBO': {'name': 'Bandundu', 'city': 'Bandundu', 'lat': -3.3117, 'lon': 17.3817, 'elevation': 1063},
        'FZEA': {'name': 'Mbandaka', 'city': 'Mbandaka', 'lat': 0.0226, 'lon': 18.2887, 'elevation': 1040},
    }
    
    # ============================================
    # API REFRESH INTERVALS (seconds)
    # ============================================
    FLIGHT_POSITION_REFRESH = 5          # Fetch positions every 5 seconds
    GEOFENCE_CHECK_REFRESH = 10          # Check overflight every 10 seconds
    WEATHER_REFRESH = 300                # Weather data every 5 minutes
    INVOICE_GENERATION_REFRESH = 3600    # Check pending invoices every hour


class DevelopmentConfig(Config):
    DEBUG = True
    TESTING = False


class ProductionConfig(Config):
    DEBUG = False
    TESTING = False


config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'default': DevelopmentConfig
}
