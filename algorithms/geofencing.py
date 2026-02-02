"""
Algorithme de Geofencing pour la détection de survol
Air Traffic Management - RDC
"""

from shapely.geometry import Point, Polygon, LineString
from shapely.prepared import prep
from shapely.ops import nearest_points
import math


class RDCGeofence:
    def __init__(self):
        self.boundary_coords = [
            (12.2, -5.9), (12.5, -4.6), (13.1, -4.5), (14.0, -4.4),
            (15.8, -4.0), (16.2, -2.0), (16.5, -1.0), (17.8, -0.5),
            (18.5, 2.0), (19.5, 3.0), (21.0, 4.0), (24.0, 5.5),
            (27.4, 5.0), (28.0, 4.5), (29.0, 4.3), (29.5, 3.0),
            (29.8, 1.5), (29.6, -1.0), (29.2, -1.5), (29.0, -2.8),
            (29.5, -4.5), (29.0, -6.0), (30.5, -8.0), (30.0, -10.0),
            (28.5, -11.0), (27.5, -12.0), (25.0, -12.5), (22.0, -13.0),
            (21.5, -12.0), (20.0, -11.0), (18.0, -9.5), (16.0, -8.0),
            (13.0, -6.5), (12.2, -5.9)
        ]
        self.polygon = Polygon(self.boundary_coords)
        self.prepared_polygon = prep(self.polygon)
    
    def contains(self, lon, lat):
        point = Point(lon, lat)
        return self.prepared_polygon.contains(point)
    
    def distance_to_boundary(self, lon, lat):
        point = Point(lon, lat)
        boundary = self.polygon.exterior
        return point.distance(boundary) * 111
    
    def get_entry_point(self, lon1, lat1, lon2, lat2):
        line = LineString([(lon1, lat1), (lon2, lat2)])
        intersection = line.intersection(self.polygon.exterior)
        
        if intersection.is_empty:
            return None
        
        if intersection.geom_type == 'Point':
            return (intersection.x, intersection.y)
        elif intersection.geom_type == 'MultiPoint':
            first_point = min(intersection.geoms, 
                            key=lambda p: Point(lon1, lat1).distance(p))
            return (first_point.x, first_point.y)
        
        return None
    
    def calculate_trajectory_distance(self, positions):
        if len(positions) < 2:
            return 0
        
        total_distance = 0
        in_rdc_positions = [(p['lon'], p['lat']) for p in positions 
                           if self.contains(p['lon'], p['lat'])]
        
        for i in range(1, len(in_rdc_positions)):
            lon1, lat1 = in_rdc_positions[i-1]
            lon2, lat2 = in_rdc_positions[i]
            total_distance += self._haversine_distance(lat1, lon1, lat2, lon2)
        
        return total_distance
    
    def _haversine_distance(self, lat1, lon1, lat2, lon2):
        R = 6371
        
        lat1_rad = math.radians(lat1)
        lat2_rad = math.radians(lat2)
        delta_lat = math.radians(lat2 - lat1)
        delta_lon = math.radians(lon2 - lon1)
        
        a = (math.sin(delta_lat/2)**2 + 
             math.cos(lat1_rad) * math.cos(lat2_rad) * math.sin(delta_lon/2)**2)
        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))
        
        return R * c
    
    def get_regions(self):
        return {
            'kinshasa': {
                'center': (15.3, -4.3),
                'radius_km': 100
            },
            'katanga': {
                'center': (27.0, -10.5),
                'radius_km': 200
            },
            'nord_kivu': {
                'center': (29.0, -1.0),
                'radius_km': 150
            },
            'equateur': {
                'center': (18.0, 1.0),
                'radius_km': 200
            }
        }
    
    def is_in_region(self, lon, lat, region_name):
        regions = self.get_regions()
        if region_name not in regions:
            return False
        
        region = regions[region_name]
        center_lon, center_lat = region['center']
        radius = region['radius_km']
        
        distance = self._haversine_distance(lat, lon, center_lat, center_lon)
        return distance <= radius


rdc_geofence = RDCGeofence()
