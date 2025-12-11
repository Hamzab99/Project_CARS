#!/bin/bash
# startup.sh
# Script de démarrage pour Azure Web App

echo "==================================="
echo "Starting EV Trip Planner on Azure"
echo "==================================="

# Démarrer le service SOAP en arrière-plan
echo "Starting SOAP service on port 8000..."
python soap_service.py &
SOAP_PID=$!
echo "SOAP service started with PID: $SOAP_PID"

# Attendre que le service SOAP soit prêt
sleep 5

# Démarrer l'application Flask principale
echo "Starting Flask API on port 8080..."
gunicorn --bind=0.0.0.0:8080 --timeout 600 --workers=2 app:app