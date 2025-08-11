#!/bin/sh
# provision_grafana_service_account.sh
# This script creates a Grafana service account and token using the Grafana HTTP API.
# It waits for Grafana to be up, then creates the account and token, and writes the token to a file.

GRAFANA_URL="${GRAFANA_URL:-http://localhost:3000}"
GRAFANA_ADMIN_USER="${GRAFANA_ADMIN_USER:-admin}"
GRAFANA_ADMIN_PASSWORD="${GRAFANA_ADMIN_PASSWORD:-admin}"
TOKEN_FILE="./shared/grafana_api_key"

# Wait for Grafana to be up
until curl -s "$GRAFANA_URL/api/health" | grep -q '"database": "ok"'; do
  echo "Waiting for Grafana..."
  sleep 2
done

echo "Grafana is up. Creating service account..."

# Create service account
echo '{"name":"airflow","role":"Editor"}' > /tmp/sa_payload.json
SERVICE_ACCOUNT=$(curl -s -X POST "$GRAFANA_URL/api/serviceaccounts" \
  -H "Content-Type: application/json" \
  -u "$GRAFANA_ADMIN_USER:$GRAFANA_ADMIN_PASSWORD" \
  -d @/tmp/sa_payload.json)
SA_ID=$(echo "$SERVICE_ACCOUNT" | grep -o '"id":[0-9]*' | cut -d: -f2)

if [ -z "$SA_ID" ]; then
  echo "Failed to create service account. Response: $SERVICE_ACCOUNT"
  exit 1
fi

echo "Service account created with ID: $SA_ID. Creating token..."

echo '{"name":"airflow-token"}' > /tmp/token_payload.json
TOKEN=$(curl -s -X POST "$GRAFANA_URL/api/serviceaccounts/$SA_ID/tokens" \
  -H "Content-Type: application/json" \
  -u "$GRAFANA_ADMIN_USER:$GRAFANA_ADMIN_PASSWORD" \
  -d @/tmp/token_payload.json | grep -o '"key":"[^"]*"' | cut -d: -f2 | tr -d '"')

if [ -z "$TOKEN" ]; then
  echo "Failed to create token."
  exit 1
fi

echo "Token created. Writing to $TOKEN_FILE."
mkdir -p $(dirname "$TOKEN_FILE")
echo "$TOKEN" > "$TOKEN_FILE"
chmod 600 "$TOKEN_FILE"
echo "Done."
