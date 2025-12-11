# soap_client.py
"""
Client SOAP pour tester le service de calcul de temps de trajet
"""

from zeep import Client
import logging

# Configuration du logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class TravelTimeClient:
    """Client pour interroger le service SOAP de calcul de temps de trajet"""
    
    def __init__(self, wsdl_url='http://localhost:8000/?wsdl'):
        """
        Initialise le client SOAP
        
        Args:
            wsdl_url: URL du fichier WSDL du service
        """
        try:
            self.client = Client(wsdl_url)
            logger.info(f"✓ Client SOAP connecté à {wsdl_url}")
        except Exception as e:
            logger.error(f"✗ Erreur de connexion au service SOAP: {e}")
            raise
    
    def calculate_travel_time(self, distance, autonomy, charge_time):
        """
        Calcule le temps total de voyage
        
        Args:
            distance: Distance en km
            autonomy: Autonomie du véhicule en km
            charge_time: Temps de recharge en heures
            
        Returns:
            Temps total en heures
        """
        try:
            result = self.client.service.calculate_travel_time(
                distance=float(distance),
                autonomy=float(autonomy),
                charge_time=float(charge_time)
            )
            logger.info(f"Temps total calculé: {result:.2f} heures")
            return result
        except Exception as e:
            logger.error(f"Erreur lors du calcul: {e}")
            return None
    
    def calculate_number_of_stops(self, distance, autonomy, safety_margin=0.85):
        """
        Calcule le nombre d'arrêts nécessaires
        
        Args:
            distance: Distance en km
            autonomy: Autonomie en km
            safety_margin: Marge de sécurité (0.85 = 85%)
            
        Returns:
            Nombre d'arrêts
        """
        try:
            result = self.client.service.calculate_number_of_stops(
                distance=float(distance),
                autonomy=float(autonomy),
                safety_margin=float(safety_margin)
            )
            logger.info(f"Nombre d'arrêts: {int(result)}")
            return int(result)
        except Exception as e:
            logger.error(f"Erreur lors du calcul: {e}")
            return None
    
    def calculate_driving_time(self, distance, average_speed=90):
        """
        Calcule le temps de conduite seul
        
        Args:
            distance: Distance en km
            average_speed: Vitesse moyenne en km/h
            
        Returns:
            Temps de conduite en heures
        """
        try:
            result = self.client.service.calculate_driving_time(
                distance=float(distance),
                average_speed=float(average_speed)
            )
            logger.info(f"Temps de conduite: {result:.2f} heures")
            return result
        except Exception as e:
            logger.error(f"Erreur lors du calcul: {e}")
            return None


def test_service():
    """Fonction de test du service SOAP"""
    
    print("=" * 60)
    print("TEST DU SERVICE SOAP - CALCUL TEMPS DE TRAJET")
    print("=" * 60)
    
    try:
        # Connexion au service
        client = TravelTimeClient()
        
        # Test 1: Paris - Lyon (465 km)
        print("\n📍 Test 1: Paris → Lyon")
        print("-" * 40)
        distance = 465
        autonomy = 395  # Renault Zoe
        charge_time = 0.75
        
        total_time = client.calculate_travel_time(distance, autonomy, charge_time)
        stops = client.calculate_number_of_stops(distance, autonomy)
        driving_time = client.calculate_driving_time(distance)
        
        print(f"Distance: {distance} km")
        print(f"Autonomie véhicule: {autonomy} km")
        print(f"Temps de recharge: {charge_time} h")
        print(f"→ Nombre d'arrêts: {stops}")
        print(f"→ Temps de conduite: {driving_time:.2f} h")
        print(f"→ Temps total: {total_time:.2f} h")
        
        # Test 2: Paris - Marseille (775 km)
        print("\n📍 Test 2: Paris → Marseille")
        print("-" * 40)
        distance = 775
        autonomy = 580  # Tesla Model 3
        charge_time = 0.5
        
        total_time = client.calculate_travel_time(distance, autonomy, charge_time)
        stops = client.calculate_number_of_stops(distance, autonomy)
        driving_time = client.calculate_driving_time(distance)
        
        print(f"Distance: {distance} km")
        print(f"Autonomie véhicule: {autonomy} km")
        print(f"Temps de recharge: {charge_time} h")
        print(f"→ Nombre d'arrêts: {stops}")
        print(f"→ Temps de conduite: {driving_time:.2f} h")
        print(f"→ Temps total: {total_time:.2f} h")
        
        # Test 3: Lyon - Nice (470 km)
        print("\n📍 Test 3: Lyon → Nice")
        print("-" * 40)
        distance = 470
        autonomy = 340  # Peugeot e-208
        charge_time = 0.8
        
        total_time = client.calculate_travel_time(distance, autonomy, charge_time)
        stops = client.calculate_number_of_stops(distance, autonomy)
        driving_time = client.calculate_driving_time(distance)
        
        print(f"Distance: {distance} km")
        print(f"Autonomie véhicule: {autonomy} km")
        print(f"Temps de recharge: {charge_time} h")
        print(f"→ Nombre d'arrêts: {stops}")
        print(f"→ Temps de conduite: {driving_time:.2f} h")
        print(f"→ Temps total: {total_time:.2f} h")
        
        print("\n" + "=" * 60)
        print("✓ TESTS TERMINÉS AVEC SUCCÈS")
        print("=" * 60)
        
    except Exception as e:
        print(f"\n✗ Erreur lors des tests: {e}")
        print("Assurez-vous que le service SOAP est démarré!")


if __name__ == '__main__':
    test_service()