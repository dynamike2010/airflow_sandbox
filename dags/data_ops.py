from datetime import datetime, timedelta
import pytz
import time
from airflow import DAG
from airflow.models import Variable
from airflow.operators.python import PythonOperator
from airflow.operators.empty import EmptyOperator
from messages.dag_models import ConfigMessage

default_args = {
    'retries': 0,
    'minimum_diff': timedelta(minutes=5),
}

dag = DAG(
    'data_ops',
    default_args=default_args,
    description='A DAG that gets triggered by any ETL DAG and uploads dbt artifacts',
    start_date=datetime(2000, 1, 1),
    schedule_interval=None,
    catchup=False,
    max_active_runs=1,
    tags=['data_ops'],
)


def get_last_run(command: str) -> datetime:
    last_run_key = f"last_run_{command}"
    last_run_str = Variable.get(last_run_key, default_var=None)
    if last_run_str:
        dt = datetime.fromisoformat(last_run_str)
        return dt
    return datetime.min.replace(tzinfo=pytz.UTC)


def set_last_run(command: str, current_time: datetime):
    last_run_key = f"last_run_{command}"
    Variable.set(last_run_key, current_time.isoformat())


def process_message(config_message, dag_instance):
    print(f"message: {config_message}")
    
    command = config_message.command
    dag_id = config_message.dag_id
    last_run_time = get_last_run(command)
    minimum_diff = dag_instance.default_args.get('minimum_diff', 1)
    current_time = datetime.now(tz=pytz.UTC)

    if current_time - last_run_time < minimum_diff:
        print(f"Skipping {command} for {dag_id}: Last run was too recent")
        return

    print(f"Current time: {current_time}")
    set_last_run(command, current_time)
    print(f"Uploading dbt artifacts to Secoda for DAG: '{dag_id}'")
    time.sleep(10)
    print("Upload completed successfully")


def execute(**context):
    conf = context['dag_run'].conf
    if not conf:
        print("No config message - skipping...")
        return
    process_message(ConfigMessage.parse_obj(conf), context['dag'])


upload_task = PythonOperator(
    task_id='upload_task',
    python_callable=execute,
    dag=dag,
)

upload_task
