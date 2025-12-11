# app.py
"""
API REST Flask pour planificateur de voyage EV
VERSION COMPLÈTE AVEC TOUTES LES FONCTIONS
Intégration: SOAP, IRVE, GraphQL Chargetrip, OpenRouteService, geo.gouv.fr
"""

from flask import Flask, request, jsonify, render_template
from flask_cors import CORS
import requests
from zeep import Client
import logging
import os
from functools import lru_cache
from math import radians, sin, cos, sqrt, atan2

# Configuration
app = Flask(__name__, static_folder='static', template_folder='templates')
CORS(app)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# URLs des services
SOAP_SERVICE_URL = os.getenv('SOAP_URL', 'http://localhost:8000/?wsdl')
IRVE_API_URL = 'https://opendata.reseaux-energies.fr/api/records/1.0/search/'
CHARGETRIP_API_URL = 'https://api.chargetrip.io/graphql'

# Clés API
CHARGETRIP_API_KEY = os.getenv('CHARGETRIP_API_KEY', '692a26889b4638ceff6b0f89')
CHARGETRIP_CLIENT_ID = os.getenv('CHARGETRIP_CLIENT_ID', '692a26889b4638ceff6b0f87')
OPENROUTE_API_KEY = os.getenv('OPENROUTE_API_KEY', 'eyJvcmciOiI1YjNjZTM1OTc4NTExMTAwMDFjZjYyNDgiLCJpZCI6ImIzMTgxMjc3OGFiMjQ5MzE4MDQwOGJiYTQ3M2FkMTg2IiwiaCI6Im11cm11cjY0In0')

# ==================== DONNÉES FALLBACK ====================

FALLBACK_VEHICLES = [
    {'id': 1, 'name': 'Tesla Model 3 Long Range', 'brand': 'Tesla', 'model': 'Model 3', 'autonomy': 580, 'battery': 75, 'chargeTime': 0.5, 'seats': 5},
    {'id': 2, 'name': 'Renault Zoe R135', 'brand': 'Renault', 'model': 'Zoe', 'autonomy': 395, 'battery': 52, 'chargeTime': 0.75, 'seats': 5},
    {'id': 3, 'name': 'Nissan Leaf e+ 62kWh', 'brand': 'Nissan', 'model': 'Leaf', 'autonomy': 385, 'battery': 62, 'chargeTime': 0.67, 'seats': 5},
    {'id': 4, 'name': 'Peugeot e-208 GT', 'brand': 'Peugeot', 'model': 'e-208', 'autonomy': 340, 'battery': 50, 'chargeTime': 0.8, 'seats': 5},
    {'id': 5, 'name': 'Volkswagen ID.3 Pro', 'brand': 'Volkswagen', 'model': 'ID.3', 'autonomy': 420, 'battery': 58, 'chargeTime': 0.7, 'seats': 5},
    {'id': 6, 'name': 'Hyundai Kona Electric 64kWh', 'brand': 'Hyundai', 'model': 'Kona Electric', 'autonomy': 484, 'battery': 64, 'chargeTime': 0.65, 'seats': 5},
    {'id': 7, 'name': 'BMW i3 120Ah', 'brand': 'BMW', 'model': 'i3', 'autonomy': 310, 'battery': 42, 'chargeTime': 0.85, 'seats': 4},
    {'id': 8, 'name': 'Audi e-tron 55 quattro', 'brand': 'Audi', 'model': 'e-tron', 'autonomy': 436, 'battery': 95, 'chargeTime': 0.6, 'seats': 5},
    {'id': 9, 'name': 'Mercedes EQC 400', 'brand': 'Mercedes', 'model': 'EQC', 'autonomy': 417, 'battery': 80, 'chargeTime': 0.7, 'seats': 5},
    {'id': 10, 'name': 'Kia e-Niro 64kWh', 'brand': 'Kia', 'model': 'e-Niro', 'autonomy': 455, 'battery': 64, 'chargeTime': 0.65, 'seats': 5},
]

CITIES_COORDINATES = {
    'paris': {'lat': 48.8566, 'lon': 2.3522, 'name': 'Paris', 'population': 2165423},
    'lyon': {'lat': 45.7640, 'lon': 4.8357, 'name': 'Lyon', 'population': 516092},
    'marseille': {'lat': 43.2965, 'lon': 5.3698, 'name': 'Marseille', 'population': 869815},
    'bordeaux': {'lat': 44.8378, 'lon': -0.5792, 'name': 'Bordeaux', 'population': 254436},
    'nice': {'lat': 43.7102, 'lon': 7.2620, 'name': 'Nice', 'population': 340017},
    'toulouse': {'lat': 43.6047, 'lon': 1.4442, 'name': 'Toulouse', 'population': 479553},
    'nantes': {'lat': 47.2184, 'lon': -1.5536, 'name': 'Nantes', 'population': 309346},
    'strasbourg': {'lat': 48.5734, 'lon': 7.7521, 'name': 'Strasbourg', 'population': 280966},
    'montpellier': {'lat': 43.6108, 'lon': 3.8767, 'name': 'Montpellier', 'population': 285121},
    'lille': {'lat': 50.6292, 'lon': 3.0573, 'name': 'Lille', 'population': 232787},
    'rennes': {'lat': 48.1173, 'lon': -1.6778, 'name': 'Rennes', 'population': 216815},
    'reims': {'lat': 49.2583, 'lon': 4.0317, 'name': 'Reims', 'population': 182592},
    'grenoble': {'lat': 45.1885, 'lon': 5.7245, 'name': 'Grenoble', 'population': 158454},
    'dijon': {'lat': 47.3220, 'lon': 5.0415, 'name': 'Dijon', 'population': 155090},
    'angers': {'lat': 47.4784, 'lon': -0.5632, 'name': 'Angers', 'population': 151229}
}


# ==================== RÉCUPÉRATION VILLES ====================

@lru_cache(maxsize=1)
def fetch_cities_from_api(min_population=100000):
    """
    Récupère toutes les grandes villes de France depuis l'API geo.gouv.fr.
    min_population : seuil minimum d'habitants (par défaut : >= 100 000)
    Retour : dictionnaire {key: {lat, lon, name, population}}
    """

    url = "https://geo.api.gouv.fr/communes"
    params = {
        "fields": "nom,code,population,centre",
        "format": "json"
    }

    try:
        logger.info("🔄 Téléchargement de toutes les communes françaises...")

        response = requests.get(url, params=params, timeout=20)
        response.raise_for_status()

        all_cities = response.json()
        cities = {}

        logger.info("🔄 Filtrage des grandes villes...")

        for c in all_cities:
            pop = c.get("population", 0)

            # 🎯 FILTRE AUTOMATIQUE
            if pop < min_population:
                continue

            name = c.get("nom")
            centre = c.get("centre", {})
            coords = centre.get("coordinates", [])

            if len(coords) != 2:
                continue

            lon, lat = coords[0], coords[1]

            # clé unique normalisée
            key = (
                name.lower()
                    .replace("-", "")
                    .replace(" ", "")
                    .replace("'", "")
            )

            cities[key] = {
                "name": name,
                "population": pop,
                "lat": lat,
                "lon": lon,
                "code": c.get("code", "")
            }

        if len(cities) > 0:
            logger.info(f"✅ {len(cities)} grandes villes récupérées (pop >= {min_population})")
            return cities

        logger.warning("⚠️ Aucune ville récupérée → fallback utilisé")
        return CITIES_COORDINATES

    except Exception as e:
        logger.error(f"❌ Erreur API geo.gouv.fr : {e}")
        return CITIES_COORDINATES




# ==================== RÉCUPÉRATION VÉHICULES ====================

@lru_cache(maxsize=1)
def fetch_vehicles_from_chargetrip():
    """Récupère les véhicules depuis Chargetrip avec fallback"""
    
    if not CHARGETRIP_API_KEY or CHARGETRIP_API_KEY == '':
        logger.warning("⚠️  Pas de clé Chargetrip - FALLBACK")
        return FALLBACK_VEHICLES
    
    query = """
    query vehicleList {
      vehicleList(page: 0, size: 50) {
        id
        naming {
          make
          model
          version
        }
        battery {
          usable_kwh
        }
        body {
          seats
        }
        range {
          chargetrip_range {
            best
            worst
          }
        }
      }
    }
    """
    
    headers = {
        'x-client-id': CHARGETRIP_CLIENT_ID,
        'x-app-id': CHARGETRIP_API_KEY,
        'Content-Type': 'application/json'
    }
    
    try:
        response = requests.post(CHARGETRIP_API_URL, json={'query': query}, headers=headers, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            
            if 'data' in data and 'vehicleList' in data['data']:
                vehicles = []
                
                for idx, vehicle_data in enumerate(data['data']['vehicleList'], 1):
                    naming = vehicle_data.get('naming', {})
                    battery = vehicle_data.get('battery', {})
                    range_data = vehicle_data.get('range', {}).get('chargetrip_range', {})
                    
                    best_range = range_data.get('best', 0)
                    worst_range = range_data.get('worst', 0)
                    avg_range = int((best_range + worst_range) / 2) if best_range and worst_range else 350
                    
                    battery_kwh = battery.get('usable_kwh', 50)
                    charge_time = round(battery_kwh / 50, 2)
                    
                    vehicle = {
                        'id': idx,
                        'name': f"{naming.get('make', '')} {naming.get('model', '')}".strip(),
                        'brand': naming.get('make', 'Unknown'),
                        'model': naming.get('model', ''),
                        'autonomy': avg_range,
                        'battery': battery_kwh,
                        'chargeTime': charge_time,
                        'seats': vehicle_data.get('body', {}).get('seats', 5)
                    }
                    
                    if vehicle['autonomy'] > 100 and vehicle['battery'] > 0:
                        vehicles.append(vehicle)
                
                logger.info(f"✅ {len(vehicles)} véhicules depuis Chargetrip")
                return vehicles if vehicles else FALLBACK_VEHICLES
        
        logger.warning("⚠️  Réponse invalide - FALLBACK")
        return FALLBACK_VEHICLES
        
    except Exception as e:
        logger.error(f"❌ Erreur Chargetrip: {e} - FALLBACK")
        return FALLBACK_VEHICLES


# ==================== CALCUL DISTANCE ====================

def calculate_distance_haversine(coords1, coords2):
    """Calcul distance à vol d'oiseau"""
    R = 6371
    
    lat1, lon1 = radians(coords1['lat']), radians(coords1['lon'])
    lat2, lon2 = radians(coords2['lat']), radians(coords2['lon'])
    
    dlat = lat2 - lat1
    dlon = lon2 - lon1
    
    a = sin(dlat/2)**2 + cos(lat1) * cos(lat2) * sin(dlon/2)**2
    c = 2 * atan2(sqrt(a), sqrt(1-a))
    
    distance = R * c * 1.3
    
    return {
        'distance': round(distance, 1),
        'duration': round(distance / 90, 2),
        'geometry': None,
        'coordinates': []
    }


def calculate_distance_and_route(city1, city2):
    """Calcule distance avec OpenRouteService ou fallback"""
    cities_dict = fetch_cities_from_api()
    
    coords1 = cities_dict.get(city1.lower())
    coords2 = cities_dict.get(city2.lower())
    
    if not coords1 or not coords2:
        return None, None
    
    try:
        headers = {
            'Authorization': OPENROUTE_API_KEY,
            'Content-Type': 'application/json'
        }
        
        body = {
            'coordinates': [
                [coords1['lon'], coords1['lat']],
                [coords2['lon'], coords2['lat']]
            ]
        }
        
        response = requests.post('https://api.openrouteservice.org/v2/directions/driving-car', json=body, headers=headers, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            
            if 'routes' in data and len(data['routes']) > 0:
                route = data['routes'][0]
                distance = route['summary']['distance'] / 1000
                duration = route['summary']['duration'] / 3600
                
                logger.info(f"✅ Distance {city1}-{city2}: {distance:.0f} km")
                
                return {
                    'distance': round(distance, 1),
                    'duration': round(duration, 2),
                    'geometry': route.get('geometry'),
                    'coordinates': []
                }, None
        
        logger.warning("⚠️  OpenRoute: fallback Haversine")
        return calculate_distance_haversine(coords1, coords2), None
        
    except Exception as e:
        logger.error(f"❌ OpenRoute: {e} - fallback")
        return calculate_distance_haversine(coords1, coords2), None


# ==================== BORNES IRVE ====================

def find_charging_stations_on_route(coords1, coords2, num_stops):
    """Trouve les bornes sur l'itinéraire"""
    if num_stops == 0:
        return []
    
    stations = []
    
    for i in range(1, num_stops + 1):
        ratio = i / (num_stops + 1)
        lat = coords1['lat'] + (coords2['lat'] - coords1['lat']) * ratio
        lon = coords1['lon'] + (coords2['lon'] - coords1['lon']) * ratio
        
        station = find_nearest_charging_station(lat, lon)
        if station:
            station['stop_number'] = i
            station['distance_from_start'] = round(
                calculate_distance_haversine(coords1, {'lat': lat, 'lon': lon})['distance'], 
                1
            )
            stations.append(station)
    
    return stations


def find_nearest_charging_station(lat, lon, radius_km=20):
    """Trouve la borne la plus proche"""
    try:
        params = {
            'dataset': 'bornes-irve',
            'geofilter.distance': f'{lat},{lon},{radius_km * 1000}',
            'rows': 5,
            'sort': 'dist'
        }
        
        response = requests.get(IRVE_API_URL, params=params, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            
            if 'records' in data and len(data['records']) > 0:
                record = data['records'][0]
                fields = record.get('fields', {})
                
                return {
                    'id': record.get('recordid', ''),
                    'name': fields.get('n_station', 'Station de recharge'),
                    'address': fields.get('ad_station', ''),
                    'city': fields.get('n_amenageur', ''),
                    'power': fields.get('puiss_max', 'N/A'),
                    'connector_type': fields.get('type_prise', 'Type 2'),
                    'lat': fields.get('coordonneesxy', [None, None])[0] or lat,
                    'lon': fields.get('coordonneesxy', [None, None])[1] or lon,
                    'available': True
                }
        
        return {
            'id': f'fallback_{lat}_{lon}',
            'name': 'Station de recharge',
            'address': 'Aire d\'autoroute',
            'power': '50 kW',
            'connector_type': 'Type 2 CCS',
            'lat': lat,
            'lon': lon,
            'available': True
        }
        
    except Exception as e:
        logger.error(f"Erreur IRVE: {e}")
        return None


# ==================== ROUTES API ====================

@app.route('/')
def index():
    return render_template('index.html')


@app.route('/api/info')
def api_info():
    return jsonify({
        'service': 'EV Trip Planner API',
        'version': '2.0',
        'status': 'online',
        'endpoints': {
            'vehicles': '/api/vehicles',
            'cities': '/api/cities',
            'plan_trip': '/api/plan-trip'
        }
    })


@app.route('/api/vehicles', methods=['GET'])
def get_vehicles():
    try:
        vehicles = fetch_vehicles_from_chargetrip()
        
        brand = request.args.get('brand')
        min_autonomy = request.args.get('min_autonomy', type=int)
        
        if brand:
            vehicles = [v for v in vehicles if v['brand'].lower() == brand.lower()]
        if min_autonomy:
            vehicles = [v for v in vehicles if v['autonomy'] >= min_autonomy]
        
        return jsonify({
            'success': True,
            'count': len(vehicles),
            'source': 'Chargetrip GraphQL API',
            'vehicles': vehicles
        })
        
    except Exception as e:
        logger.error(f"Erreur get_vehicles: {e}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/cities', methods=['GET'])
def get_cities():
    try:
        cities_dict = fetch_cities_from_api()
        
        cities = [
            {
                'name': data['name'],
                'key': key,
                'coordinates': {'lat': data['lat'], 'lon': data['lon']},
                'population': data.get('population', 0)
            }
            for key, data in cities_dict.items()
        ]
        
        cities.sort(key=lambda x: x.get('population', 0), reverse=True)
        
        return jsonify({
            'success': True,
            'count': len(cities),
            'source': 'API geo.gouv.fr',
            'cities': cities
        })
        
    except Exception as e:
        logger.error(f"Erreur get_cities: {e}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/plan-trip', methods=['POST'])
def plan_trip():
    try:
        data = request.get_json()
        
        vehicle_id = data.get('vehicle_id')
        departure = data.get('departure', '').lower()
        destination = data.get('destination', '').lower()
        
        if not all([vehicle_id, departure, destination]):
            return jsonify({'error': 'Paramètres manquants'}), 400
        
        vehicles = fetch_vehicles_from_chargetrip()
        vehicle = next((v for v in vehicles if v['id'] == vehicle_id), None)
        
        if not vehicle:
            return jsonify({'error': 'Véhicule non trouvé'}), 404
        
        cities_dict = fetch_cities_from_api()
        
        if departure not in cities_dict or destination not in cities_dict:
            return jsonify({'error': 'Ville non trouvée'}), 400
        
        coords1 = cities_dict[departure]
        coords2 = cities_dict[destination]
        
        route_data, error = calculate_distance_and_route(departure, destination)
        
        if not route_data:
            return jsonify({'error': 'Impossible de calculer l\'itinéraire'}), 400
        
        distance = route_data['distance']
        
        try:
            soap_client = Client(SOAP_SERVICE_URL)
            num_stops = soap_client.service.calculate_number_of_stops(
                distance=float(distance),
                autonomy=float(vehicle['autonomy'])
            )
            
            total_time = soap_client.service.calculate_travel_time(
                distance=float(distance),
                autonomy=float(vehicle['autonomy']),
                charge_time=float(vehicle['chargeTime'])
            )
        except Exception as e:
            logger.warning(f"SOAP indisponible: {e}")
            SAFETY_MARGIN = 0.85
            effective_range = vehicle['autonomy'] * SAFETY_MARGIN
            num_stops = max(0, int((distance - effective_range) / effective_range) + 1) if distance > effective_range else 0
            
            driving_time = distance / 90
            total_time = driving_time + (num_stops * vehicle['chargeTime'])
        
        charging_stations = find_charging_stations_on_route(coords1, coords2, num_stops)
        
        result = {
            'success': True,
            'trip': {
                'vehicle': vehicle,
                'departure': {'city': departure.title(), 'coordinates': coords1},
                'destination': {'city': destination.title(), 'coordinates': coords2},
                'distance': distance,
                'numberOfStops': num_stops,
                'chargingStations': charging_stations,
                'route': route_data.get('coordinates', []),
                'time': {
                    'driving': round(distance / 90, 2),
                    'charging': round(num_stops * vehicle['chargeTime'], 2),
                    'total': round(total_time, 2)
                }
            },
            'sources': {
                'vehicle': 'Chargetrip GraphQL API',
                'route': 'OpenRouteService API',
                'charging_stations': 'IRVE OpenData API',
                'calculations': 'Service SOAP',
                'cities': 'API geo.gouv.fr'
            }
        }
        
        logger.info(f"✅ Trajet: {departure} -> {destination}, {distance}km, {num_stops} arrêts")
        
        return jsonify(result)
        
    except Exception as e:
        logger.error(f"Erreur plan_trip: {e}")
        return jsonify({'error': str(e)}), 500


# ==================== DÉMARRAGE ====================

if __name__ == '__main__':
    PORT = int(os.environ.get('PORT', 5000))
    HOST = os.environ.get('HOST', '0.0.0.0')
    
    print("=" * 70)
    print("🚗 EV TRIP PLANNER - API REST")
    print("=" * 70)
    print(f"🌐 URL: http://{HOST}:{PORT}")
    print(f"📡 Intégrations:")
    print(f"   - GraphQL Chargetrip (véhicules)")
    print(f"   - API IRVE (bornes)")
    print(f"   - API geo.gouv.fr (villes)")
    print(f"   - OpenRouteService (itinéraires)")
    print(f"   - Service SOAP (calculs)")
    print("=" * 70)
    
    app.run(host=HOST, port=PORT, debug=False)