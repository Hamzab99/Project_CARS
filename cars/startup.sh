#!/bin/bash
echo "==================================="
echo "Starting EV Trip Planner on Render"
echo "==================================="

# Lancer le service SOAP
echo "Starting SOAP service on port 8000..."
python cars/soap_service.py &
SOAP_PID=$!
echo "SOAP service started with PID: $SOAP_PID"

# Attendre 5 secondes pour que SOAP démarre
sleep 5

# Lancer Flask avec Gunicorn
echo "Starting Flask API on port $PORT..."
gunicorn --bind 0.0.0.0:$PORT --timeout 600 --workers=2 cars.app:app
