
from flask import Flask
import os
import sys

# Add the project root to the python path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from models import db, SystemConfig
from app import create_app

def seed_configs():
    app = create_app()
    with app.app_context():
        configs = [
            {
                'key': 'unit_altitude',
                'value': 'ft',
                'description': 'Unité d\'altitude (ft, m)',
                'category': 'display',
                'value_type': 'select',
                'is_editable': True
            },
            {
                'key': 'unit_speed',
                'value': 'kts',
                'description': 'Unité de vitesse (kts, km/h, Mach)',
                'category': 'display',
                'value_type': 'select',
                'is_editable': True
            },
            {
                'key': 'precision_decimals',
                'value': '2',
                'description': 'Nombre de décimales pour l\'affichage',
                'category': 'display',
                'value_type': 'int',
                'is_editable': True
            },
            {
                'key': 'timezone',
                'value': 'UTC',
                'description': 'Fuseau horaire de l\'application',
                'category': 'system',
                'value_type': 'select',
                'is_editable': True
            }
        ]

        print("Seeding configurations...")
        for config_data in configs:
            existing = SystemConfig.query.filter_by(key=config_data['key']).first()
            if not existing:
                print(f"Adding {config_data['key']}...")
                config = SystemConfig(**config_data)
                db.session.add(config)
            else:
                print(f"{config_data['key']} already exists.")

        db.session.commit()
        print("Done.")

if __name__ == '__main__':
    seed_configs()
