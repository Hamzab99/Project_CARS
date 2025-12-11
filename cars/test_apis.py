#!/usr/bin/env python3
# test_apis.py
"""
Script pour tester toutes les APIs externes
Vérifie si les clés API fonctionnent et affiche les données
"""

import requests
import json
import os
from dotenv import load_dotenv

# Charger les variables d'environnement
load_dotenv()

# Couleurs pour le terminal
class Colors:
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    END = '\033[0m'
    BOLD = '\033[1m'

def print_header(text):
    print(f"\n{Colors.BOLD}{Colors.BLUE}{'='*70}{Colors.END}")
    print(f"{Colors.BOLD}{Colors.BLUE}{text}{Colors.END}")
    print(f"{Colors.BOLD}{Colors.BLUE}{'='*70}{Colors.END}\n")

def print_success(text):
    print(f"{Colors.GREEN}✓ {text}{Colors.END}")

def print_error(text):
    print(f"{Colors.RED}✗ {text}{Colors.END}")

def print_warning(text):
    print(f"{Colors.YELLOW}⚠ {text}{Colors.END}")

def print_info(text):
    print(f"  {text}")


# ==================== TEST 1: API IRVE (Bornes de recharge) ====================

def test_irve_api():
    print_header("TEST 1: API IRVE - Bornes de recharge")
    
    url = "https://opendata.reseaux-energies.fr/api/records/1.0/search/"
    
    # Test 1: Recherche autour de Paris
    params = {
        'dataset': 'bornes-irve',
        'geofilter.distance': '48.8566,2.3522,5000',  # Paris, rayon 5km
        'rows': 5
    }
    
    try:
        print_info("Recherche de bornes autour de Paris...")
        response = requests.get(url, params=params, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            
            if 'records' in data and len(data['records']) > 0:
                print_success(f"API IRVE fonctionne ! {len(data['records'])} bornes trouvées")
                
                # Afficher les 3 premières bornes
                print_info("\nExemples de bornes:")
                for i, record in enumerate(data['records'][:3], 1):
                    fields = record.get('fields', {})
                    print_info(f"\n  {i}. {fields.get('n_station', 'Station inconnue')}")
                    print_info(f"     Adresse: {fields.get('ad_station', 'N/A')}")
                    print_info(f"     Puissance: {fields.get('puiss_max', 'N/A')} kW")
                    print_info(f"     Statut: {fields.get('statut', 'N/A')}")
                
                return True
            else:
                print_warning("API répond mais aucune borne trouvée")
                return False
        else:
            print_error(f"Erreur HTTP {response.status_code}")
            return False
            
    except Exception as e:
        print_error(f"Erreur: {e}")
        return False


# ==================== TEST 2: API Chargetrip (GraphQL) ====================

def test_chargetrip_api():
    print_header("TEST 2: API Chargetrip - Véhicules électriques (GraphQL)")
    
    api_key = os.getenv('CHARGETRIP_API_KEY', '')
    client_id = os.getenv('CHARGETRIP_CLIENT_ID', '5e8c22366f9c5f23ab0eff39')
    
    if not api_key or api_key == 'YOUR_API_KEY':
        print_warning("Clé API Chargetrip non configurée dans .env")
        print_info("1. Aller sur https://chargetrip.com/")
        print_info("2. Créer un compte gratuit")
        print_info("3. Dashboard > API Keys")
        print_info("4. Ajouter CHARGETRIP_API_KEY dans .env")
        return False
    
    url = "https://api.chargetrip.io/graphql"
    
    query = """
    query vehicleList {
      vehicleList(page: 0, size: 5) {
        id
        naming {
          make
          model
          version
        }
        battery {
          usable_kwh
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
        'x-client-id': client_id,
        'x-app-id': api_key,
        'Content-Type': 'application/json'
    }
    
    try:
        print_info(f"Test avec API Key: {api_key[:10]}...")
        response = requests.post(url, json={'query': query}, headers=headers, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            
            if 'errors' in data:
                print_error("Erreur GraphQL:")
                print_info(f"  {data['errors']}")
                return False
            
            if 'data' in data and 'vehicleList' in data['data']:
                vehicles = data['data']['vehicleList']
                print_success(f"API Chargetrip fonctionne ! {len(vehicles)} véhicules récupérés")
                
                # Afficher les véhicules
                print_info("\nExemples de véhicules:")
                for i, vehicle in enumerate(vehicles, 1):
                    naming = vehicle.get('naming', {})
                    battery = vehicle.get('battery', {})
                    range_data = vehicle.get('range', {}).get('chargetrip_range', {})
                    
                    name = f"{naming.get('make', '')} {naming.get('model', '')}"
                    autonomy = (range_data.get('best', 0) + range_data.get('worst', 0)) / 2
                    
                    print_info(f"\n  {i}. {name}")
                    print_info(f"     Batterie: {battery.get('usable_kwh', 'N/A')} kWh")
                    print_info(f"     Autonomie: ~{int(autonomy)} km")
                
                return True
            else:
                print_error("Réponse API invalide")
                print_info(f"  {json.dumps(data, indent=2)}")
                return False
        else:
            print_error(f"Erreur HTTP {response.status_code}")
            print_info(f"  {response.text}")
            return False
            
    except Exception as e:
        print_error(f"Erreur: {e}")
        return False


# ==================== TEST 3: API OpenRouteService ====================

def test_openroute_api():
    print_header("TEST 3: API OpenRouteService - Calcul d'itinéraires")
    
    api_key = os.getenv('OPENROUTE_API_KEY', '')
    
    if not api_key or api_key == 'YOUR_OPENROUTE_KEY':
        print_warning("Clé API OpenRouteService non configurée dans .env")
        print_info("1. Aller sur https://openrouteservice.org/")
        print_info("2. S'inscrire gratuitement")
        print_info("3. Dashboard > Request a token")
        print_info("4. Ajouter OPENROUTE_API_KEY dans .env")
        return False
    
    url = "https://api.openrouteservice.org/v2/directions/driving-car"
    
    headers = {
        'Authorization': api_key,
        'Content-Type': 'application/json'
    }
    
    # Itinéraire Paris -> Lyon
    body = {
        'coordinates': [
            [2.3522, 48.8566],  # Paris (lon, lat)
            [4.8357, 45.7640]   # Lyon
        ]
    }
    
    try:
        print_info("Calcul d'itinéraire Paris -> Lyon...")
        response = requests.post(url, json=body, headers=headers, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            
            if 'routes' in data and len(data['routes']) > 0:
                route = data['routes'][0]
                distance = route['summary']['distance'] / 1000  # km
                duration = route['summary']['duration'] / 3600  # heures
                
                print_success("API OpenRouteService fonctionne !")
                print_info(f"\n  Itinéraire Paris -> Lyon:")
                print_info(f"  Distance: {distance:.1f} km")
                print_info(f"  Durée estimée: {duration:.1f} heures")
                
                return True
            else:
                print_error("Réponse API invalide")
                return False
        else:
            print_error(f"Erreur HTTP {response.status_code}")
            print_info(f"  {response.text}")
            return False
            
    except Exception as e:
        print_error(f"Erreur: {e}")
        return False


# ==================== TEST 4: API geo.gouv.fr (Villes) ====================

def test_geo_api():
    print_header("TEST 4: API geo.gouv.fr - Villes françaises")
    
    base_url = "https://geo.api.gouv.fr/communes"
    city_codes = ['75056', '69123', '13055', '33063', '06088']  # Paris, Lyon, Marseille, Bordeaux, Nice
    
    cities = []

    print_info("Récupération des grandes villes françaises...")

    try:
        for code in city_codes:
            params = {
                'code': code,
                'fields': 'nom,code,centre,population',
                'format': 'json'
            }

            response = requests.get(base_url, params=params, timeout=10)

            if response.status_code == 200 and len(response.json()) > 0:
                cities.append(response.json()[0])

        if len(cities) > 0:
            print_success(f"API geo.gouv.fr fonctionne ! {len(cities)} villes récupérées")

            print_info("\nExemples de villes:")
            for i, city in enumerate(cities, 1):
                name = city.get('nom', '')
                coords = city.get('centre', {}).get('coordinates', [])
                pop = city.get('population', 0)

                print_info(f"\n  {i}. {name}")
                if len(coords) == 2:
                    print_info(f"     Coordonnées: {coords[1]:.4f}, {coords[0]:.4f}")
                print_info(f"     Population: {pop:,} habitants")

            return True

        else:
            print_warning("API répond mais aucune ville trouvée")
            return False

    except Exception as e:
        print_error(f"Erreur: {e}")
        return False



# ==================== TEST 5: Service SOAP Local ====================

def test_soap_service():
    print_header("TEST 5: Service SOAP Local")
    
    soap_url = "http://localhost:8000/?wsdl"
    
    try:
        print_info("Tentative de connexion au service SOAP...")
        
        # Test simple HTTP
        response = requests.get(soap_url, timeout=5)
        
        if response.status_code == 200 and 'wsdl' in response.text.lower():
            print_success("Service SOAP fonctionne !")
            print_info(f"  WSDL accessible sur {soap_url}")
            
            # Test avec Zeep
            try:
                from zeep import Client
                client = Client(soap_url)
                
                # Test d'un calcul
                result = client.service.calculate_travel_time(
                    distance=500.0,
                    autonomy=400.0,
                    charge_time=0.75
                )
                
                print_info(f"  Test de calcul: 500km / 400km autonomie")
                print_info(f"  Temps total: {result:.2f} heures")
                
            except Exception as e:
                print_warning(f"Zeep non disponible ou erreur: {e}")
            
            return True
        else:
            print_error("Service SOAP ne répond pas correctement")
            print_info("  Assurez-vous que soap_service.py est lancé:")
            print_info("  $ python soap_service.py")
            return False
            
    except requests.exceptions.ConnectionError:
        print_error("Impossible de se connecter au service SOAP")
        print_info("  Le service n'est pas démarré. Lancez-le:")
        print_info("  $ python soap_service.py")
        return False
    except Exception as e:
        print_error(f"Erreur: {e}")
        return False


# ==================== RÉSUMÉ ====================

def print_summary(results):
    print_header("RÉSUMÉ DES TESTS")
    
    total = len(results)
    success = sum(1 for r in results.values() if r)
    
    for name, result in results.items():
        status = "✓ OK" if result else "✗ ÉCHEC"
        color = Colors.GREEN if result else Colors.RED
        print(f"{color}{status}{Colors.END} - {name}")
    
    print(f"\n{Colors.BOLD}Score: {success}/{total} APIs fonctionnelles{Colors.END}")
    
    if success == total:
        print(f"\n{Colors.GREEN}{Colors.BOLD}🎉 Toutes les APIs fonctionnent !{Colors.END}")
        print(f"{Colors.GREEN}Vous pouvez lancer l'application:{Colors.END}")
        print(f"  $ python app.py")
    elif success > 0:
        print(f"\n{Colors.YELLOW}⚠️  Certaines APIs ne fonctionnent pas{Colors.END}")
        print(f"{Colors.YELLOW}L'application utilisera des données de fallback{Colors.END}")
    else:
        print(f"\n{Colors.RED}❌ Aucune API ne fonctionne{Colors.END}")
        print(f"{Colors.RED}Vérifiez votre connexion internet et vos clés API{Colors.END}")


# ==================== MAIN ====================

def main():
    print(f"\n{Colors.BOLD}{Colors.BLUE}")
    print("╔════════════════════════════════════════════════════════════════════╗")
    print("║              TEST DES APIs - EV TRIP PLANNER                       ║")
    print("╚════════════════════════════════════════════════════════════════════╝")
    print(f"{Colors.END}\n")
    
    results = {}
    
    # Test 1: API IRVE (pas de clé nécessaire)
    results["API IRVE (Bornes)"] = test_irve_api()
    
    # Test 2: API Chargetrip
    results["API Chargetrip (Véhicules)"] = test_chargetrip_api()
    
    # Test 3: API OpenRouteService
    results["API OpenRouteService (Routes)"] = test_openroute_api()
    
    # Test 4: API geo.gouv.fr (Villes)
    results["API geo.gouv.fr (Villes)"] = test_geo_api()
    
    # Test 5: Service SOAP local
    results["Service SOAP (Local)"] = test_soap_service()
    
    # Résumé
    print_summary(results)
    
    print("\n")


if __name__ == '__main__':
    main()