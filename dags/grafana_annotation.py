from datetime import datetime
from airflow import DAG
from airflow.operators.python import PythonOperator
import requests
import os

def send_grafana_annotation(**context):
    grafana_url = os.environ.get('GRAFANA_URL', 'http://grafana:3000')
    # Hardcoded for demo purposes; go to administration > users > service accounts > create service account (editor) > add token
    api_key = None
    api_key_path = '/shared/grafana_api_key'
    if os.path.exists(api_key_path):
        with open(api_key_path) as f:
            api_key = f.read().strip()
    else:
        api_key = os.getenv('GRAFANA_API_KEY', '')
    headers = {
        'Authorization': f'Bearer {api_key}',
        'Content-Type': 'application/json',
    }
    # Alternate text between 'CI/CD started' and 'CI/CD finished' based on even/odd second
    now = datetime.now()
    text = "CI/CD started" if now.second % 2 == 0 else "CI/CD finished"
    payload = {
        "dashboardUID": "791199cf-d989-41e8-8613-e2b629a0dba4",
        # "panelId": None,
        "time": int(now.timestamp() * 1000),
        "tags": ["dwh", "ci/cd"],
        "text": text
    }
    response = requests.post(f"{grafana_url}/api/annotations", json=payload, headers=headers)
    print(f"Grafana annotation response: {response.status_code} {response.text}")

dag = DAG(
    'grafana_annotations',
    start_date=datetime(2000, 1, 1),
    schedule_interval='*/10 * * * *',
    catchup=False,
    tags=['dwh', 'data_ops'],
)

send_annotation_task = PythonOperator(
    task_id='send_grafana_annotation',
    python_callable=send_grafana_annotation,
    provide_context=True,
    dag=dag,
)

send_annotation_task

