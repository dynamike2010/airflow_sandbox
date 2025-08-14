from datetime import datetime, timedelta
import random
import time
from airflow import DAG
from airflow.operators.python import PythonOperator

def extract_data():
    print("Extracting data from source...")
    time.sleep(random.uniform(2, 10))
    print("Data extracted.")
    return "extract_done"

def transform_data():
    print("Transforming data...")
    time.sleep(random.uniform(6, 8))
    print("Data transformed.")
    return "transform_done"

def load_data():
    print("Loading data into warehouse...")
    time.sleep(random.uniform(1, 4))
    print("Data loaded.")
    return "load_done"

def validate_data():
    print("Validating loaded data...")
    time.sleep(random.uniform(3, 5))
    print("Data validation complete.")
    return "validate_done"

def notify_success():
    print("ETL pipeline completed successfully!")
    return "notified"

default_args = {
    'owner': 'airflow',
    'depends_on_past': False,
    'email_on_failure': False,
    'email_on_retry': False,
    'retries': 1,
    'retry_delay': timedelta(minutes=2),
}

dag = DAG(
    'domain_b_etl',
    default_args=default_args,
    description='Sample DWH domain_b ETL pipeline for metrics testing',
    start_date=datetime(2000, 1, 1),
    schedule_interval='*/3 * * * *',
    catchup=False,
    tags=['dwh', 'etl', 'domain_b'],
)

extract = PythonOperator(
    task_id='extract_data',
    python_callable=extract_data,
    dag=dag,
)

transform = PythonOperator(
    task_id='transform_data',
    python_callable=transform_data,
    dag=dag,
)

load = PythonOperator(
    task_id='load_data',
    python_callable=load_data,
    dag=dag,
)

validate = PythonOperator(
    task_id='validate_data',
    python_callable=validate_data,
    dag=dag,
)

notify = PythonOperator(
    task_id='notify_success',
    python_callable=notify_success,
    dag=dag,
    trigger_rule='all_success',
)

extract >> transform >> load >> validate >> notify
