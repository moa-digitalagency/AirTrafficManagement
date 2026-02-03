import sys
import os

# Add parent dir to path to import app
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import create_app
from models import db, SystemConfig

app = create_app()

with app.app_context():
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
    print("Done")
