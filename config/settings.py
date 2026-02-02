import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    SECRET_KEY = os.environ.get('SESSION_SECRET', 'atm-rdc-secret-key-2024')
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ENGINE_OPTIONS = {
        'pool_pre_ping': True,
        'pool_recycle': 300,
    }
    
    WTF_CSRF_ENABLED = True
    WTF_CSRF_SECRET_KEY = os.environ.get('SESSION_SECRET', 'csrf-secret-key')
    
    AVIATION_API_KEY = os.environ.get('AVIATION_API_KEY', '')
    WEATHER_API_KEY = os.environ.get('WEATHER_API_KEY', '')
    
    MAIL_SERVER = os.environ.get('MAIL_SERVER', 'smtp.gmail.com')
    MAIL_PORT = int(os.environ.get('MAIL_PORT', 587))
    MAIL_USE_TLS = True
    MAIL_USERNAME = os.environ.get('MAIL_USERNAME', '')
    MAIL_PASSWORD = os.environ.get('MAIL_PASSWORD', '')
    
    UPLOAD_FOLDER = 'statics/uploads'
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024
    
    RDC_TARIFS = {
        'survol_par_km': 0.85,
        'atterrissage_base': 150.0,
        'stationnement_heure': 25.0,
        'surtaxe_nuit_pct': 0.25,
        'tva_pct': 0.16,
        'tonnage_par_tonne': 2.50,
    }
    
    AIRPORTS_RDC = {
        'FZAA': {'name': 'N\'Djili International', 'city': 'Kinshasa', 'lat': -4.3858, 'lon': 15.4446},
        'FZQA': {'name': 'Lubumbashi International', 'city': 'Lubumbashi', 'lat': -11.5913, 'lon': 27.5309},
        'FZNA': {'name': 'Goma International', 'city': 'Goma', 'lat': -1.6708, 'lon': 29.2385},
        'FZOA': {'name': 'Kisangani Bangoka', 'city': 'Kisangani', 'lat': 0.4817, 'lon': 25.3379},
        'FZWA': {'name': 'Mbuji-Mayi', 'city': 'Mbuji-Mayi', 'lat': -6.1212, 'lon': 23.5690},
        'FZIC': {'name': 'Matadi Tshimpi', 'city': 'Matadi', 'lat': -5.7996, 'lon': 13.4404},
        'FZKA': {'name': 'Kamina', 'city': 'Kamina', 'lat': -8.6420, 'lon': 25.2528},
        'FZRA': {'name': 'Kolwezi', 'city': 'Kolwezi', 'lat': -10.7659, 'lon': 25.5057},
    }


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
