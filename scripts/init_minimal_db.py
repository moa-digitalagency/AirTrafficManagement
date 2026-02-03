"""
/* * Nom de l'application : ATM-RDC
 * Description : Source file: init_minimal_db.py
 * Produit de : MOA Digital Agency, www.myoneart.com
 * Fait par : Aisance KALONJI, www.aisancekalonji.com
 * Auditer par : La CyberConfiance, www.cyberconfiance.com
 */
"""
import sys
import os

# Add parent dir to path to import app
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from flask import Flask
from sqlalchemy import event
from sqlalchemy.schema import Table
try:
    from geoalchemy2 import admin
except ImportError:
    admin = None

from models.base import db
from models.system import SystemConfig, AuditLog, Alert, Notification

def create_app():
    app = Flask(__name__)
    app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL', 'sqlite:///' + os.path.join(os.getcwd(), 'instance/app.db'))
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['SECRET_KEY'] = 'dev'
    db.init_app(app)
    return app

def init_minimal():
    app = create_app()
    if not os.path.exists('instance'):
        os.makedirs('instance')

    with app.app_context():
        print("Creating minimal tables...")

        # Remove GeoAlchemy2 listeners to avoid SpatiaLite errors on SQLite
        if admin:
            try:
                event.remove(Table, 'before_create', admin.before_create)
            except:
                pass
            try:
                event.remove(Table, 'after_create', admin.after_create)
            except:
                pass
            try:
                event.remove(Table, 'before_drop', admin.before_drop)
            except:
                pass
            try:
                event.remove(Table, 'after_drop', admin.after_drop)
            except:
                pass

        # Create only the tables we need for branding if possible, but create_all creates all.
        # Hopefully removing listeners allows creation of tables with Geometry columns as text or blob (SQLite default)
        # or at least prevents the spatialite function calls.

        db.create_all()

        configs = [
            {
                'key': 'app_name',
                'value': 'ATM-RDC',
                'description': 'Nom de l\'application',
                'category': 'branding',
                'value_type': 'string',
                'is_editable': True
            },
            {
                'key': 'logo_path',
                'value': '',
                'description': 'Logo de l\'application',
                'category': 'branding',
                'value_type': 'file',
                'is_editable': True
            },
            {
                'key': 'favicon_path',
                'value': '',
                'description': 'Favicon de l\'application',
                'category': 'branding',
                'value_type': 'file',
                'is_editable': True
            }
        ]

        for conf in configs:
            existing = SystemConfig.query.filter_by(key=conf['key']).first()
            if not existing:
                new_conf = SystemConfig(
                    key=conf['key'],
                    value=conf['value'],
                    description=conf['description'],
                    category=conf['category'],
                    value_type=conf['value_type'],
                    is_editable=conf['is_editable']
                )
                db.session.add(new_conf)
                print(f"Added {conf['key']}")
            else:
                print(f"{conf['key']} already exists")

        db.session.commit()
        print("Done.")

if __name__ == '__main__':
    init_minimal()
