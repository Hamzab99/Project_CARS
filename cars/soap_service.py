# soap_service.py
"""
Service SOAP pour calcul de temps de trajet véhicules électriques
Compatible Azure Web App
"""

from spyne import Application, rpc, ServiceBase, Float, Integer
from spyne.protocol.soap import Soap11
from spyne.server.wsgi import WsgiApplication
from wsgiref.simple_server import make_server
import logging
import os

# Configuration du logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class TravelTimeService(ServiceBase):
    """Service SOAP pour calculs liés aux trajets EV"""
    
    @rpc(Float, Float, Float, _returns=Float)
    def calculate_travel_time(ctx, distance, autonomy, charge_time):
        """
        Calcule le temps total de voyage avec recharges
        
        Args:
            distance: Distance totale en km
            autonomy: Autonomie du véhicule en km
            charge_time: Temps de recharge en heures
            
        Returns:
            Temps total en heures
        """
        try:
            AVERAGE_SPEED = 90  # km/h
            SAFETY_MARGIN = 0.85  # 85% de l'autonomie
            
            effective_range = autonomy * SAFETY_MARGIN
            
            # Nombre d'arrêts
            if distance <= effective_range:
                number_of_stops = 0
            else:
                number_of_stops = int((distance - effective_range) / effective_range) + 1
            
            # Temps de conduite
            driving_time = distance / AVERAGE_SPEED
            
            # Temps de recharge total
            total_charge_time = number_of_stops * charge_time
            
            # Temps total
            total_time = driving_time + total_charge_time
            
            logger.info(f"Calcul: {distance}km, {number_of_stops} arrêts, {total_time:.2f}h")
            
            return total_time
            
        except Exception as e:
            logger.error(f"Erreur calculate_travel_time: {e}")
            return -1.0
    
    @rpc(Float, Float, _returns=Integer)
    def calculate_number_of_stops(ctx, distance, autonomy):
        """
        Calcule le nombre d'arrêts nécessaires
        
        Args:
            distance: Distance en km
            autonomy: Autonomie en km
            
        Returns:
            Nombre d'arrêts
        """
        try:
            SAFETY_MARGIN = 0.85
            effective_range = autonomy * SAFETY_MARGIN
            
            if distance <= effective_range:
                return 0
            else:
                stops = int((distance - effective_range) / effective_range) + 1
                return stops
                
        except Exception as e:
            logger.error(f"Erreur calculate_number_of_stops: {e}")
            return -1
    
    @rpc(Float, Float, _returns=Float)
    def calculate_driving_time(ctx, distance, average_speed):
        """
        Calcule le temps de conduite seul
        
        Args:
            distance: Distance en km
            average_speed: Vitesse moyenne en km/h
            
        Returns:
            Temps de conduite en heures
        """
        try:
            if average_speed <= 0:
                return -1.0
            return distance / average_speed
        except Exception as e:
            logger.error(f"Erreur calculate_driving_time: {e}")
            return -1.0
    
    @rpc(Float, Integer, Float, _returns=Float)
    def calculate_charge_time(ctx, distance, autonomy, charge_time_per_stop):
        """
        Calcule le temps de recharge total
        
        Args:
            distance: Distance en km
            autonomy: Autonomie en km
            charge_time_per_stop: Temps par recharge en heures
            
        Returns:
            Temps de recharge total en heures
        """
        try:
            SAFETY_MARGIN = 0.85
            effective_range = autonomy * SAFETY_MARGIN
            
            if distance <= effective_range:
                stops = 0
            else:
                stops = int((distance - effective_range) / effective_range) + 1
            
            return float(stops * charge_time_per_stop)
            
        except Exception as e:
            logger.error(f"Erreur calculate_charge_time: {e}")
            return -1.0


# Configuration de l'application SOAP
application = Application(
    [TravelTimeService],
    tns='fr.usmb.info802.evtrip.soap',
    in_protocol=Soap11(validator='lxml'),
    out_protocol=Soap11()
)

wsgi_application = WsgiApplication(application)


if __name__ == '__main__':
    # Port pour Azure ou local
    PORT = int(os.environ.get('SOAP_PORT', 8000))
    HOST = os.environ.get('SOAP_HOST', '0.0.0.0')
    
    print("=" * 70)
    print("🔵 SERVICE SOAP - EV TRIP PLANNER")
    print("=" * 70)
    print(f"🌐 URL     : http://{HOST}:{PORT}")
    print(f"📄 WSDL    : http://{HOST}:{PORT}/?wsdl")
    print(f"⚡ Service : Calcul de temps de trajet véhicules électriques")
    print("=" * 70)
    
    server = make_server(HOST, PORT, wsgi_application)
    
    try:
        logger.info(f"Service SOAP démarré sur {HOST}:{PORT}")
        server.serve_forever()
    except KeyboardInterrupt:
        print("\n🛑 Arrêt du service SOAP")
        logger.info("Service SOAP arrêté")