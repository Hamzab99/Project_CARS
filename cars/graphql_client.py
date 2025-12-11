# graphql_client.py
"""
Client GraphQL pour interroger l'API Chargetrip
Récupère la liste des véhicules électriques avec leurs caractéristiques
"""

import requests
import json
import logging
from typing import List, Dict, Optional

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class ChargeTripClient:
    """Client pour l'API GraphQL Chargetrip"""
    
    def __init__(self, api_key: str, client_id: str = None):
        """
        Initialise le client GraphQL
        
        Args:
            api_key: Clé API Chargetrip
            client_id: ID client Chargetrip (optionnel)
        """
        self.url = 'https://api.chargetrip.io/graphql'
        self.headers = {
            'x-client-id': client_id or 'YOUR_CLIENT_ID',
            'x-app-id': api_key,
            'Content-Type': 'application/json'
        }
    
    def get_vehicles(self, 
                     size: int = 20, 
                     min_range: Optional[int] = None,
                     brand: Optional[str] = None) -> List[Dict]:
        """
        Récupère la liste des véhicules électriques
        
        Args:
            size: Nombre de véhicules à récupérer
            min_range: Autonomie minimale en km
            brand: Marque du véhicule
            
        Returns:
            Liste des véhicules avec leurs caractéristiques
        """
        query = """
        query vehicleList($size: Int, $page: Int) {
          vehicleList(size: $size, page: $page) {
            id
            naming {
              make
              model
              version
              edition
              chargetrip_version
            }
            battery {
              usable_kwh
              full_kwh
            }
            range {
              chargetrip_range {
                best
                worst
              }
            }
            performance {
              acceleration
              top_speed
            }
            charging {
              time
              ports {
                standard
                max_electric_power
              }
            }
            media {
              image {
                thumbnail_url
              }
            }
          }
        }
        """
        
        variables = {
            'size': size,
            'page': 0
        }
        
        try:
            response = requests.post(
                self.url,
                json={'query': query, 'variables': variables},
                headers=self.headers,
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                vehicles = self._parse_vehicles(data)
                
                # Appliquer les filtres
                if min_range:
                    vehicles = [v for v in vehicles if v.get('autonomy', 0) >= min_range]
                if brand:
                    vehicles = [v for v in vehicles if v.get('brand', '').lower() == brand.lower()]
                
                logger.info(f"✓ {len(vehicles)} véhicules récupérés")
                return vehicles
            else:
                logger.error(f"✗ Erreur API: {response.status_code}")
                return []
                
        except Exception as e:
            logger.error(f"✗ Erreur lors de la requête GraphQL: {e}")
            return []
    
    def get_vehicle_by_id(self, vehicle_id: str) -> Optional[Dict]:
        """
        Récupère un véhicule spécifique par son ID
        
        Args:
            vehicle_id: ID du véhicule
            
        Returns:
            Détails du véhicule ou None
        """
        query = """
        query vehicle($id: ID!) {
          vehicle(id: $id) {
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
            charging {
              time
            }
          }
        }
        """
        
        variables = {'id': vehicle_id}
        
        try:
            response = requests.post(
                self.url,
                json={'query': query, 'variables': variables},
                headers=self.headers,
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                if 'data' in data and 'vehicle' in data['data']:
                    return self._parse_vehicle(data['data']['vehicle'])
            
            return None
            
        except Exception as e:
            logger.error(f"✗ Erreur: {e}")
            return None
    
    def _parse_vehicles(self, response_data: Dict) -> List[Dict]:
        """Parse la réponse de l'API en format standardisé"""
        vehicles = []
        
        if 'data' not in response_data or 'vehicleList' not in response_data['data']:
            return vehicles
        
        for vehicle_data in response_data['data']['vehicleList']:
            vehicle = self._parse_vehicle(vehicle_data)
            if vehicle:
                vehicles.append(vehicle)
        
        return vehicles
    
    def _parse_vehicle(self, vehicle_data: Dict) -> Optional[Dict]:
        """Parse un véhicule individuel"""
        try:
            naming = vehicle_data.get('naming', {})
            battery = vehicle_data.get('battery', {})
            range_data = vehicle_data.get('range', {}).get('chargetrip_range', {})
            charging = vehicle_data.get('charging', {})
            
            # Calculer l'autonomie moyenne
            best_range = range_data.get('best', 0)
            worst_range = range_data.get('worst', 0)
            avg_range = (best_range + worst_range) / 2 if best_range and worst_range else 0
            
            # Temps de charge (convertir en heures)
            charge_time = charging.get('time', 0) / 60 if charging.get('time') else 0.75
            
            return {
                'id': vehicle_data.get('id'),
                'name': f"{naming.get('make', '')} {naming.get('model', '')}".strip(),
                'brand': naming.get('make', ''),
                'model': naming.get('model', ''),
                'version': naming.get('version', ''),
                'autonomy': int(avg_range) if avg_range > 0 else 350,
                'battery': battery.get('usable_kwh', 0),
                'chargeTime': round(charge_time, 2),
                'type': 'Electric'
            }
        except Exception as e:
            logger.warning(f"Erreur lors du parsing: {e}")
            return None


def test_graphql_client():
    """Fonction de test du client GraphQL"""
    
    print("=" * 60)
    print("TEST CLIENT GRAPHQL - CHARGETRIP API")
    print("=" * 60)
    
    # Note: Vous devez avoir une clé API valide
    # Inscrivez-vous sur https://chargetrip.com/
    api_key = "YOUR_API_KEY_HERE"
    
    if api_key == "YOUR_API_KEY_HERE":
        print("\n⚠️  Clé API manquante!")
        print("Inscrivez-vous sur https://chargetrip.com/ pour obtenir une clé")
        print("\nUtilisation de données de démonstration...")
        
        # Données de démonstration
        demo_vehicles = [
            {
                'id': 'demo1',
                'name': 'Tesla Model 3',
                'brand': 'Tesla',
                'autonomy': 580,
                'battery': 75,
                'chargeTime': 0.5
            },
            {
                'id': 'demo2',
                'name': 'Renault Zoe',
                'brand': 'Renault',
                'autonomy': 395,
                'battery': 52,
                'chargeTime': 0.75
            }
        ]
        
        print(f"\n✓ {len(demo_vehicles)} véhicules de démonstration chargés")
        for v in demo_vehicles:
            print(f"\n  • {v['name']}")
            print(f"    Autonomie: {v['autonomy']} km")
            print(f"    Batterie: {v['battery']} kWh")
            print(f"    Temps de charge: {v['chargeTime']} h")
        
        return
    
    try:
        client = ChargeTripClient(api_key=api_key)
        
        print("\n📡 Récupération des véhicules...")
        vehicles = client.get_vehicles(size=10)
        
        if vehicles:
            print(f"\n✓ {len(vehicles)} véhicules récupérés:\n")
            for v in vehicles[:5]:  # Afficher les 5 premiers
                print(f"  • {v['name']}")
                print(f"    Autonomie: {v['autonomy']} km")
                print(f"    Batterie: {v['battery']} kWh")
                print(f"    Temps de charge: {v['chargeTime']} h")
                print()
        else:
            print("\n✗ Aucun véhicule récupéré")
        
        print("=" * 60)
        
    except Exception as e:
        print(f"\n✗ Erreur: {e}")


if __name__ == '__main__':
    test_graphql_client()