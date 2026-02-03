import os
from .base import db
from geoalchemy2 import Geometry
from sqlalchemy import Text

class Airspace(db.Model):
    """
    Airspace definitions (Boundaries, FIR, Restricted Areas)
    Uses PostGIS for spatial storage and operations
    """
    __tablename__ = 'airspaces'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False, index=True)
    type = db.Column(db.String(50), default='boundary')  # boundary, fir, restricted, etc.
    min_altitude = db.Column(db.Integer, default=0)
    max_altitude = db.Column(db.Integer, default=60000)

    # PostGIS Geometry column
    if os.environ.get('DISABLE_POSTGIS'):
        geom = db.Column(Text)
    else:
        geom = db.Column(Geometry('MULTIPOLYGON', srid=4326))

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'type': self.type,
            'min_altitude': self.min_altitude,
            'max_altitude': self.max_altitude
        }
