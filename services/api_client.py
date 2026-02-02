"""
External API Client Service for ATM-RDC
Handles connections to AviationStack, ADSBexchange, OpenWeatherMap
"""
import os
import requests
from datetime import datetime
from typing import Optional, Dict, List, Any


class AviationStackClient:
    """
    Client for AviationStack API
    Primary source for real-time flight tracking data
    Documentation: https://aviationstack.com/documentation
    """
    
    def __init__(self):
        self.api_key = os.environ.get('AVIATIONSTACK_API_KEY', '')
        self.base_url = os.environ.get('AVIATIONSTACK_API_URL', 'http://api.aviationstack.com/v1')
        self.timeout = 30
    
    def is_configured(self) -> bool:
        return bool(self.api_key)
    
    def get_real_time_flights(self, bounds: Optional[Dict] = None) -> List[Dict]:
        """
        Fetch real-time flights from AviationStack
        
        Args:
            bounds: Optional dict with lat/lon bounds for RDC airspace
                   {'min_lat': -14, 'max_lat': 6, 'min_lon': 12, 'max_lon': 32}
        
        Returns:
            List of flight dictionaries with position data
        """
        if not self.is_configured():
            return []
        
        try:
            params = {
                'access_key': self.api_key,
                'flight_status': 'active'
            }
            
            response = requests.get(
                f"{self.base_url}/flights",
                params=params,
                timeout=self.timeout
            )
            response.raise_for_status()
            data = response.json()
            
            flights = []
            for flight_data in data.get('data', []):
                live = flight_data.get('live', {})
                
                if not live or live.get('latitude') is None:
                    continue
                
                lat = live.get('latitude')
                lon = live.get('longitude')
                
                if bounds:
                    if not (bounds['min_lat'] <= lat <= bounds['max_lat'] and
                            bounds['min_lon'] <= lon <= bounds['max_lon']):
                        continue
                
                flights.append({
                    'icao24': flight_data.get('aircraft', {}).get('icao24'),
                    'callsign': flight_data.get('flight', {}).get('iata') or flight_data.get('flight', {}).get('icao'),
                    'registration': flight_data.get('aircraft', {}).get('registration'),
                    'latitude': lat,
                    'longitude': lon,
                    'altitude': live.get('altitude'),
                    'heading': live.get('direction'),
                    'ground_speed': live.get('speed_horizontal'),
                    'vertical_speed': live.get('speed_vertical'),
                    'on_ground': live.get('is_ground', False),
                    'departure_icao': flight_data.get('departure', {}).get('icao'),
                    'arrival_icao': flight_data.get('arrival', {}).get('icao'),
                    'airline_iata': flight_data.get('airline', {}).get('iata'),
                    'aircraft_type': flight_data.get('aircraft', {}).get('iata'),
                    'timestamp': datetime.utcnow().isoformat()
                })
            
            return flights
            
        except requests.exceptions.RequestException as e:
            print(f"[AviationStack] API Error: {e}")
            return []
    
    def get_flight_schedule(self, icao_code: str) -> List[Dict]:
        """Get scheduled flights for an airport"""
        if not self.is_configured():
            return []
        
        try:
            params = {
                'access_key': self.api_key,
                'dep_icao': icao_code
            }
            
            response = requests.get(
                f"{self.base_url}/flights",
                params=params,
                timeout=self.timeout
            )
            response.raise_for_status()
            return response.json().get('data', [])
            
        except requests.exceptions.RequestException as e:
            print(f"[AviationStack] Schedule Error: {e}")
            return []


class ADSBExchangeClient:
    """
    Client for ADSBexchange API
    Fallback/Secondary source for flight tracking
    Documentation: https://www.adsbexchange.com/data/
    """
    
    def __init__(self):
        self.api_key = os.environ.get('ADSBEXCHANGE_API_KEY', '')
        self.base_url = os.environ.get('ADSBEXCHANGE_API_URL', 'https://adsbexchange.com/api/aircraft/v2')
        self.timeout = 30
    
    def is_configured(self) -> bool:
        return bool(self.api_key)
    
    def get_flights_in_area(self, lat: float, lon: float, radius_nm: int = 250) -> List[Dict]:
        """
        Get all aircraft within radius of a point
        
        Args:
            lat: Center latitude
            lon: Center longitude  
            radius_nm: Radius in nautical miles
        """
        if not self.is_configured():
            return []
        
        try:
            headers = {
                'api-auth': self.api_key,
                'Accept': 'application/json'
            }
            
            params = {
                'lat': lat,
                'lon': lon,
                'dist': radius_nm
            }
            
            response = requests.get(
                f"{self.base_url}/lat/{lat}/lon/{lon}/dist/{radius_nm}/",
                headers=headers,
                timeout=self.timeout
            )
            response.raise_for_status()
            data = response.json()
            
            flights = []
            for ac in data.get('ac', []):
                flights.append({
                    'icao24': ac.get('hex'),
                    'callsign': ac.get('flight', '').strip(),
                    'registration': ac.get('r'),
                    'latitude': ac.get('lat'),
                    'longitude': ac.get('lon'),
                    'altitude': ac.get('alt_baro'),
                    'heading': ac.get('track'),
                    'ground_speed': ac.get('gs'),
                    'vertical_speed': ac.get('baro_rate'),
                    'on_ground': ac.get('alt_baro') == 'ground',
                    'squawk': ac.get('squawk'),
                    'aircraft_type': ac.get('t'),
                    'timestamp': datetime.utcnow().isoformat()
                })
            
            return flights
            
        except requests.exceptions.RequestException as e:
            print(f"[ADSBExchange] API Error: {e}")
            return []


class OpenWeatherMapClient:
    """
    Client for OpenWeatherMap API
    Provides weather overlay data for radar map
    Documentation: https://openweathermap.org/api
    """
    
    def __init__(self):
        self.api_key = os.environ.get('OPENWEATHERMAP_API_KEY', '')
        self.base_url = os.environ.get('OPENWEATHERMAP_API_URL', 'https://api.openweathermap.org/data/2.5')
        self.timeout = 30
    
    def is_configured(self) -> bool:
        return bool(self.api_key)
    
    def get_weather_at_point(self, lat: float, lon: float) -> Optional[Dict]:
        """Get current weather at a specific location"""
        if not self.is_configured():
            return None
        
        try:
            params = {
                'lat': lat,
                'lon': lon,
                'appid': self.api_key,
                'units': 'metric'
            }
            
            response = requests.get(
                f"{self.base_url}/weather",
                params=params,
                timeout=self.timeout
            )
            response.raise_for_status()
            data = response.json()
            
            return {
                'temperature': data.get('main', {}).get('temp'),
                'humidity': data.get('main', {}).get('humidity'),
                'pressure': data.get('main', {}).get('pressure'),
                'visibility': data.get('visibility'),
                'wind_speed': data.get('wind', {}).get('speed'),
                'wind_direction': data.get('wind', {}).get('deg'),
                'clouds': data.get('clouds', {}).get('all'),
                'weather': data.get('weather', [{}])[0].get('main'),
                'description': data.get('weather', [{}])[0].get('description'),
                'icon': data.get('weather', [{}])[0].get('icon'),
                'timestamp': datetime.utcnow().isoformat()
            }
            
        except requests.exceptions.RequestException as e:
            print(f"[OpenWeatherMap] API Error: {e}")
            return None
    
    def get_weather_tile_url(self, layer: str = 'clouds_new') -> str:
        """
        Get weather tile layer URL for Leaflet overlay
        
        Args:
            layer: One of 'clouds_new', 'precipitation_new', 'pressure_new', 
                   'wind_new', 'temp_new'
        """
        if not self.is_configured():
            return ''
        
        return f"https://tile.openweathermap.org/map/{layer}/{{z}}/{{x}}/{{y}}.png?appid={self.api_key}"
    
    def get_airports_weather(self, icao_codes: List[str]) -> Dict[str, Dict]:
        """Get weather for multiple airports"""
        from config.settings import Config
        
        results = {}
        for icao in icao_codes:
            airport = Config.AIRPORTS_RDC.get(icao)
            if airport:
                weather = self.get_weather_at_point(airport['lat'], airport['lon'])
                if weather:
                    results[icao] = weather
        
        return results


class AviationWeatherClient:
    """
    Client for Aviation Weather API (aviationweather.gov)
    Provides METAR/TAF data for airports
    """
    
    def __init__(self):
        self.base_url = os.environ.get('AVIATIONWEATHER_API_URL', 'https://aviationweather.gov/api/data')
        self.timeout = 30
    
    def get_metar(self, icao_code: str) -> Optional[Dict]:
        """Get METAR data for an airport"""
        try:
            params = {
                'ids': icao_code,
                'format': 'json'
            }
            
            response = requests.get(
                f"{self.base_url}/metar",
                params=params,
                timeout=self.timeout
            )
            response.raise_for_status()
            data = response.json()
            
            if data and len(data) > 0:
                metar = data[0]
                return {
                    'raw': metar.get('rawOb'),
                    'temperature': metar.get('temp'),
                    'dewpoint': metar.get('dewp'),
                    'wind_direction': metar.get('wdir'),
                    'wind_speed': metar.get('wspd'),
                    'visibility': metar.get('visib'),
                    'altimeter': metar.get('altim'),
                    'flight_category': metar.get('fltcat'),
                    'timestamp': metar.get('obsTime')
                }
            
            return None
            
        except requests.exceptions.RequestException as e:
            print(f"[AviationWeather] METAR Error: {e}")
            return None
    
    def get_taf(self, icao_code: str) -> Optional[Dict]:
        """Get TAF (Terminal Aerodrome Forecast) for an airport"""
        try:
            params = {
                'ids': icao_code,
                'format': 'json'
            }
            
            response = requests.get(
                f"{self.base_url}/taf",
                params=params,
                timeout=self.timeout
            )
            response.raise_for_status()
            data = response.json()
            
            if data and len(data) > 0:
                taf = data[0]
                return {
                    'raw': taf.get('rawTAF'),
                    'issue_time': taf.get('issueTime'),
                    'valid_from': taf.get('validTimeFrom'),
                    'valid_to': taf.get('validTimeTo')
                }
            
            return None
            
        except requests.exceptions.RequestException as e:
            print(f"[AviationWeather] TAF Error: {e}")
            return None


# Singleton instances
aviationstack = AviationStackClient()
adsbexchange = ADSBExchangeClient()
openweathermap = OpenWeatherMapClient()
aviationweather = AviationWeatherClient()


def fetch_external_flight_data() -> List[Dict]:
    """
    Fetch flight data from available sources
    Uses AviationStack as primary, falls back to ADSBexchange
    
    Returns:
        List of flight position dictionaries
    """
    # RDC bounding box (approximate)
    rdc_bounds = {
        'min_lat': -14.0,
        'max_lat': 6.0,
        'min_lon': 12.0,
        'max_lon': 32.0
    }
    
    # Try AviationStack first
    if aviationstack.is_configured():
        flights = aviationstack.get_real_time_flights(bounds=rdc_bounds)
        if flights:
            return flights
    
    # Fallback to ADSBexchange
    if adsbexchange.is_configured():
        # Use center of RDC for radius search
        center_lat = -4.0
        center_lon = 22.0
        flights = adsbexchange.get_flights_in_area(center_lat, center_lon, radius_nm=500)
        if flights:
            return flights
    
    # No API configured or available
    return []
