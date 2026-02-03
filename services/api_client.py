"""
/* * Nom de l'application : ATM-RDC
 * Description : Source file: api_client.py
 * Produit de : MOA Digital Agency, www.myoneart.com
 * Fait par : Aisance KALONJI, www.aisancekalonji.com
 * Auditer par : La CyberConfiance, www.cyberconfiance.com
 */
"""
"""
External API Client Service for ATM-RDC
Handles connections to AviationStack, ADSBexchange, OpenWeatherMap

AviationStack Documentation: https://aviationstack.com/documentation
- Real-time flight endpoint: /v1/flights
- Request params: access_key, flight_status, dep_icao, arr_icao, airline_iata, flight_iata
- Response: pagination + data[] with flight objects
- Live position data: live.latitude, live.longitude, live.altitude, live.direction, 
                      live.speed_horizontal, live.speed_vertical, live.is_ground
"""
import os
import requests
import logging
from datetime import datetime
from typing import Optional, Dict, List, Any

logger = logging.getLogger(__name__)


class AviationStackClient:
    """
    Client for AviationStack API - Primary source for real-time flight tracking
    
    API Endpoints (v1):
    - /flights - Real-time and historical flight data
    - /routes - Airline routes
    - /airports - Airport lookup
    - /airlines - Airline lookup
    - /aircraft_types - Aircraft type data
    
    Response Structure:
    {
        "pagination": {"limit": 100, "offset": 0, "count": 100, "total": N},
        "data": [
            {
                "flight_date": "2024-01-01",
                "flight_status": "active|scheduled|landed|cancelled|incident|diverted",
                "departure": {"airport", "timezone", "iata", "icao", "terminal", "gate", "delay", "scheduled", "estimated", "actual"},
                "arrival": {"airport", "timezone", "iata", "icao", "terminal", "gate", "baggage", "delay", "scheduled", "estimated", "actual"},
                "airline": {"name", "iata", "icao"},
                "flight": {"number", "iata", "icao", "codeshared"},
                "aircraft": {"registration", "iata", "icao", "icao24"},
                "live": {"updated", "latitude", "longitude", "altitude", "direction", "speed_horizontal", "speed_vertical", "is_ground"}
            }
        ]
    }
    
    Rate Limits:
    - Free: 100-500 requests/month, HTTP only
    - Basic: Higher volume, HTTPS support
    """
    
    def __init__(self):
        self.api_key = os.environ.get('AVIATIONSTACK_API_KEY', '')
        self.base_url = os.environ.get('AVIATIONSTACK_API_URL', 'http://api.aviationstack.com/v1')
        self.timeout = 30
    
    def is_configured(self) -> bool:
        return bool(self.api_key)
    
    def get_real_time_flights(self, 
                               bounds: Optional[Dict] = None,
                               flight_status: str = 'active',
                               limit: int = 100,
                               offset: int = 0) -> List[Dict]:
        """
        Fetch real-time flights from AviationStack
        
        Args:
            bounds: Optional dict with lat/lon bounds for RDC airspace
                   {'min_lat': -14, 'max_lat': 6, 'min_lon': 12, 'max_lon': 32}
            flight_status: Filter by status - active, scheduled, landed, cancelled
            limit: Number of results per request (max 100)
            offset: Pagination offset
        
        Returns:
            List of flight dictionaries with position data
        """
        if not self.is_configured():
            logger.warning("[AviationStack] API key not configured")
            return []
        
        try:
            params = {
                'access_key': self.api_key,
                'flight_status': flight_status,
                'limit': limit,
                'offset': offset
            }
            
            response = requests.get(
                f"{self.base_url}/flights",
                params=params,
                timeout=self.timeout
            )
            response.raise_for_status()
            data = response.json()
            
            if 'error' in data:
                logger.error(f"[AviationStack] API Error: {data['error']}")
                return []
            
            flights = []
            for flight_data in data.get('data', []):
                live = flight_data.get('live') or {}
                
                if not live or live.get('latitude') is None:
                    continue
                
                lat = live.get('latitude')
                lon = live.get('longitude')
                
                if bounds:
                    if not (bounds['min_lat'] <= lat <= bounds['max_lat'] and
                            bounds['min_lon'] <= lon <= bounds['max_lon']):
                        continue
                
                departure = flight_data.get('departure') or {}
                arrival = flight_data.get('arrival') or {}
                airline = flight_data.get('airline') or {}
                flight_info = flight_data.get('flight') or {}
                aircraft = flight_data.get('aircraft') or {}
                codeshared = flight_info.get('codeshared') or {}
                
                flights.append({
                    'icao24': aircraft.get('icao24'),
                    'callsign': flight_info.get('iata') or flight_info.get('icao') or flight_info.get('number'),
                    'flight_number': flight_info.get('number'),
                    'flight_iata': flight_info.get('iata'),
                    'flight_icao': flight_info.get('icao'),
                    'registration': aircraft.get('registration'),
                    'aircraft_type_iata': aircraft.get('iata'),
                    'aircraft_type_icao': aircraft.get('icao'),
                    'latitude': lat,
                    'longitude': lon,
                    'altitude': live.get('altitude'),
                    'heading': live.get('direction'),
                    'ground_speed': live.get('speed_horizontal'),
                    'vertical_speed': live.get('speed_vertical'),
                    'on_ground': live.get('is_ground', False),
                    'flight_status': flight_data.get('flight_status'),
                    'flight_date': flight_data.get('flight_date'),
                    'departure_icao': departure.get('icao'),
                    'departure_iata': departure.get('iata'),
                    'departure_airport': departure.get('airport'),
                    'departure_terminal': departure.get('terminal'),
                    'departure_gate': departure.get('gate'),
                    'departure_timezone': departure.get('timezone'),
                    'departure_scheduled': departure.get('scheduled'),
                    'departure_actual': departure.get('actual'),
                    'departure_delay': departure.get('delay'),
                    'arrival_icao': arrival.get('icao'),
                    'arrival_iata': arrival.get('iata'),
                    'arrival_airport': arrival.get('airport'),
                    'arrival_terminal': arrival.get('terminal'),
                    'arrival_gate': arrival.get('gate'),
                    'arrival_baggage': arrival.get('baggage'),
                    'arrival_timezone': arrival.get('timezone'),
                    'arrival_scheduled': arrival.get('scheduled'),
                    'arrival_estimated': arrival.get('estimated'),
                    'airline_name': airline.get('name'),
                    'airline_iata': airline.get('iata'),
                    'airline_icao': airline.get('icao'),
                    'codeshared_airline_name': codeshared.get('airline_name'),
                    'codeshared_flight_number': codeshared.get('flight_number'),
                    'live_updated': live.get('updated'),
                    'timestamp': datetime.utcnow().isoformat()
                })
            
            logger.info(f"[AviationStack] Fetched {len(flights)} flights with live position")
            return flights
            
        except requests.exceptions.RequestException as e:
            logger.error(f"[AviationStack] API Error: {e}")
            return []
    
    def get_flights_by_airport(self, 
                                dep_icao: Optional[str] = None,
                                arr_icao: Optional[str] = None,
                                flight_status: Optional[str] = None) -> List[Dict]:
        """
        Get flights filtered by departure or arrival airport
        
        Args:
            dep_icao: Departure airport ICAO code (e.g., FZAA for Kinshasa)
            arr_icao: Arrival airport ICAO code
            flight_status: Optional status filter
        """
        if not self.is_configured():
            return []
        
        try:
            params = {'access_key': self.api_key}
            
            if dep_icao:
                params['dep_icao'] = dep_icao
            if arr_icao:
                params['arr_icao'] = arr_icao
            if flight_status:
                params['flight_status'] = flight_status
            
            response = requests.get(
                f"{self.base_url}/flights",
                params=params,
                timeout=self.timeout
            )
            response.raise_for_status()
            data = response.json()
            
            return data.get('data', [])
            
        except requests.exceptions.RequestException as e:
            logger.error(f"[AviationStack] Airport flights Error: {e}")
            return []
    
    def get_flight_schedule(self, icao_code: str, direction: str = 'departure') -> List[Dict]:
        """
        Get scheduled flights for an airport
        
        Args:
            icao_code: Airport ICAO code
            direction: 'departure' or 'arrival'
        """
        if not self.is_configured():
            return []
        
        try:
            params = {
                'access_key': self.api_key,
                'flight_status': 'scheduled'
            }
            
            if direction == 'departure':
                params['dep_icao'] = icao_code
            else:
                params['arr_icao'] = icao_code
            
            response = requests.get(
                f"{self.base_url}/flights",
                params=params,
                timeout=self.timeout
            )
            response.raise_for_status()
            return response.json().get('data', [])
            
        except requests.exceptions.RequestException as e:
            logger.error(f"[AviationStack] Schedule Error: {e}")
            return []
    
    def get_airline_info(self, airline_iata: str) -> Optional[Dict]:
        """Get airline information by IATA code"""
        if not self.is_configured():
            return None
        
        try:
            params = {
                'access_key': self.api_key,
                'airline_iata': airline_iata
            }
            
            response = requests.get(
                f"{self.base_url}/airlines",
                params=params,
                timeout=self.timeout
            )
            response.raise_for_status()
            data = response.json().get('data', [])
            
            return data[0] if data else None
            
        except requests.exceptions.RequestException as e:
            logger.error(f"[AviationStack] Airline lookup Error: {e}")
            return None
    
    def get_airport_info(self, airport_icao: str) -> Optional[Dict]:
        """Get airport information by ICAO code"""
        if not self.is_configured():
            return None
        
        try:
            params = {
                'access_key': self.api_key,
                'search': airport_icao
            }
            
            response = requests.get(
                f"{self.base_url}/airports",
                params=params,
                timeout=self.timeout
            )
            response.raise_for_status()
            data = response.json().get('data', [])
            
            return data[0] if data else None
            
        except requests.exceptions.RequestException as e:
            logger.error(f"[AviationStack] Airport lookup Error: {e}")
            return None


class ADSBExchangeClient:
    """
    Client for ADSBexchange API - Fallback/Secondary source for flight tracking
    Uses ADS-B receiver network data
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
            
            response = requests.get(
                f"{self.base_url}/lat/{lat}/lon/{lon}/dist/{radius_nm}/",
                headers=headers,
                timeout=self.timeout
            )
            response.raise_for_status()
            data = response.json()
            
            flights = []
            for ac in data.get('ac', []):
                alt_baro = ac.get('alt_baro')
                on_ground = alt_baro == 'ground' if isinstance(alt_baro, str) else False
                altitude = None if on_ground else alt_baro
                
                flights.append({
                    'icao24': ac.get('hex'),
                    'callsign': (ac.get('flight') or '').strip(),
                    'registration': ac.get('r'),
                    'latitude': ac.get('lat'),
                    'longitude': ac.get('lon'),
                    'altitude': altitude,
                    'heading': ac.get('track'),
                    'ground_speed': ac.get('gs'),
                    'vertical_speed': ac.get('baro_rate'),
                    'on_ground': on_ground,
                    'squawk': ac.get('squawk'),
                    'aircraft_type_icao': ac.get('t'),
                    'category': ac.get('category'),
                    'emergency': ac.get('emergency'),
                    'timestamp': datetime.utcnow().isoformat()
                })
            
            logger.info(f"[ADSBExchange] Fetched {len(flights)} aircraft in area")
            return flights
            
        except requests.exceptions.RequestException as e:
            logger.error(f"[ADSBExchange] API Error: {e}")
            return []
    
    def get_flights_in_bounds(self, 
                               min_lat: float, max_lat: float,
                               min_lon: float, max_lon: float) -> List[Dict]:
        """Get flights within a bounding box"""
        center_lat = (min_lat + max_lat) / 2
        center_lon = (min_lon + max_lon) / 2
        
        lat_dist = abs(max_lat - min_lat) * 60
        lon_dist = abs(max_lon - min_lon) * 60
        radius_nm = max(lat_dist, lon_dist) / 2
        
        return self.get_flights_in_area(center_lat, center_lon, int(radius_nm))


class OpenWeatherMapClient:
    """
    Client for OpenWeatherMap API - Weather overlay data for radar map
    Documentation: https://openweathermap.org/api
    
    Tile Layers available:
    - clouds_new: Cloud coverage
    - precipitation_new: Rain/snow
    - pressure_new: Pressure systems
    - wind_new: Wind patterns
    - temp_new: Temperature
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
            
            wind = data.get('wind') or {}
            main = data.get('main') or {}
            weather_list = data.get('weather') or [{}]
            weather = weather_list[0] if weather_list else {}
            
            return {
                'temperature': main.get('temp'),
                'feels_like': main.get('feels_like'),
                'humidity': main.get('humidity'),
                'pressure': main.get('pressure'),
                'visibility': data.get('visibility'),
                'wind_speed': wind.get('speed'),
                'wind_direction': wind.get('deg'),
                'wind_gust': wind.get('gust'),
                'clouds': data.get('clouds', {}).get('all'),
                'weather': weather.get('main'),
                'description': weather.get('description'),
                'icon': weather.get('icon'),
                'sunrise': data.get('sys', {}).get('sunrise'),
                'sunset': data.get('sys', {}).get('sunset'),
                'timestamp': datetime.utcnow().isoformat()
            }
            
        except requests.exceptions.RequestException as e:
            logger.error(f"[OpenWeatherMap] API Error: {e}")
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
        
        valid_layers = ['clouds_new', 'precipitation_new', 'pressure_new', 'wind_new', 'temp_new']
        if layer not in valid_layers:
            layer = 'clouds_new'
        
        return f"https://tile.openweathermap.org/map/{layer}/{{z}}/{{x}}/{{y}}.png?appid={self.api_key}"
    
    def get_all_weather_tile_urls(self) -> Dict[str, str]:
        """Get all available weather tile layer URLs"""
        if not self.is_configured():
            return {}
        
        return {
            'clouds': self.get_weather_tile_url('clouds_new'),
            'precipitation': self.get_weather_tile_url('precipitation_new'),
            'pressure': self.get_weather_tile_url('pressure_new'),
            'wind': self.get_weather_tile_url('wind_new'),
            'temperature': self.get_weather_tile_url('temp_new')
        }
    
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
    Provides METAR/TAF data for airports - No API key required
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
                    'station_id': metar.get('icaoId'),
                    'temperature': metar.get('temp'),
                    'dewpoint': metar.get('dewp'),
                    'wind_direction': metar.get('wdir'),
                    'wind_speed': metar.get('wspd'),
                    'wind_gust': metar.get('wgst'),
                    'visibility': metar.get('visib'),
                    'altimeter': metar.get('altim'),
                    'flight_category': metar.get('fltcat'),
                    'cloud_cover': metar.get('cover'),
                    'wx_string': metar.get('wxString'),
                    'timestamp': metar.get('obsTime')
                }
            
            return None
            
        except requests.exceptions.RequestException as e:
            logger.error(f"[AviationWeather] METAR Error: {e}")
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
                    'station_id': taf.get('icaoId'),
                    'issue_time': taf.get('issueTime'),
                    'valid_from': taf.get('validTimeFrom'),
                    'valid_to': taf.get('validTimeTo'),
                    'remarks': taf.get('remarks')
                }
            
            return None
            
        except requests.exceptions.RequestException as e:
            logger.error(f"[AviationWeather] TAF Error: {e}")
            return None
    
    def get_sigmet(self, region: str = 'intl') -> List[Dict]:
        """Get SIGMET/AIRMET data for a region"""
        try:
            params = {
                'region': region,
                'format': 'json'
            }
            
            response = requests.get(
                f"{self.base_url}/airsigmet",
                params=params,
                timeout=self.timeout
            )
            response.raise_for_status()
            return response.json()
            
        except requests.exceptions.RequestException as e:
            logger.error(f"[AviationWeather] SIGMET Error: {e}")
            return []


aviationstack = AviationStackClient()
adsbexchange = ADSBExchangeClient()
openweathermap = OpenWeatherMapClient()
aviationweather = AviationWeatherClient()


def fetch_external_flight_data(bounds: Optional[Dict] = None) -> List[Dict]:
    """
    Fetch flight data from available sources with fallback mechanism
    Priority: AviationStack -> ADSBexchange -> Simulation
    
    Args:
        bounds: Optional bounding box for RDC airspace
    
    Returns:
        List of flight position dictionaries
    """
    if bounds is None:
        bounds = {
            'min_lat': -14.0,
            'max_lat': 6.0,
            'min_lon': 12.0,
            'max_lon': 32.0
        }
    
    if aviationstack.is_configured():
        flights = aviationstack.get_real_time_flights(bounds=bounds)
        if flights:
            logger.info(f"[FlightData] Using AviationStack: {len(flights)} flights")
            return flights
    
    if adsbexchange.is_configured():
        center_lat = (bounds['min_lat'] + bounds['max_lat']) / 2
        center_lon = (bounds['min_lon'] + bounds['max_lon']) / 2
        flights = adsbexchange.get_flights_in_area(center_lat, center_lon, radius_nm=500)
        if flights:
            logger.info(f"[FlightData] Using ADSBexchange: {len(flights)} flights")
            return flights
    
    logger.warning("[FlightData] No flight API configured, returning empty list")
    return []


def get_api_status() -> Dict[str, Any]:
    """Get status of all configured APIs"""
    return {
        'aviationstack': {
            'configured': aviationstack.is_configured(),
            'base_url': aviationstack.base_url
        },
        'adsbexchange': {
            'configured': adsbexchange.is_configured(),
            'base_url': adsbexchange.base_url
        },
        'openweathermap': {
            'configured': openweathermap.is_configured(),
            'base_url': openweathermap.base_url
        },
        'aviationweather': {
            'configured': True,
            'base_url': aviationweather.base_url
        }
    }
