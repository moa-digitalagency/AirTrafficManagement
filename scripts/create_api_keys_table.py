
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from flask import Flask
from models import db, ApiKey
from config.settings import Config

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)
    db.init_app(app)
    return app

def create_table():
    app = create_app()
    with app.app_context():
        print("Creating api_keys table...")
        # Inspect database engine to see if table exists
        engine = db.engine
        from sqlalchemy import inspect
        inspector = inspect(engine)
        if 'api_keys' not in inspector.get_table_names():
            ApiKey.__table__.create(engine)
            print("Table 'api_keys' created successfully.")
        else:
            print("Table 'api_keys' already exists.")

if __name__ == "__main__":
    create_table()
