import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from flask import Flask
from models.base import db
from models.system import SystemConfig

def create_app():
    app = Flask(__name__)
    app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL', 'sqlite:///' + os.path.join(os.getcwd(), 'instance/app.db'))
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['SECRET_KEY'] = 'dev'
    db.init_app(app)
    return app

app = create_app()

with app.app_context():
    key = 'enabled_languages'
    existing = SystemConfig.query.filter_by(key=key).first()
    if not existing:
        conf = SystemConfig(
            key=key,
            value='["fr", "en"]',
            description='Langues activées',
            category='system',
            value_type='json',
            is_editable=False
        )
        db.session.add(conf)
        db.session.commit()
        print(f"Added {key}")
    else:
        print(f"{key} already exists")
