#!/bin/bash

# Helper script for Airflow testing environment
function show_usage {
  echo "Usage: ./airflow.sh [command]"
  echo ""
  echo "Commands:"
  echo "  start       - Start Airflow services"
  echo "  stop        - Stop Airflow services"
  echo "  stop-clean  - Stop Airflow services and remove volumes"
  echo "  logs        - Show logs of Airflow services"
  echo "  status      - Show status of Airflow services"
  echo "  help        - Show this help message"
}

case "$1" in
  start)
    echo "Starting Airflow services..."
    docker compose up -d
    echo "Airflow web UI available at: http://localhost:8080"
    echo "Username: airflow@airflow.com"
    echo "Password: airflow"
    ;;
  stop)
    echo "Stopping Airflow services..."
    docker compose down
    ;;
  stop-clean)
    echo "Stopping Airflow services and removing volumes..."
    docker compose down -v
    ;;
  logs)
    docker compose logs -f
    ;;
  status)
    docker compose ps
    ;;
  help|*)
    show_usage
    ;;
esac
