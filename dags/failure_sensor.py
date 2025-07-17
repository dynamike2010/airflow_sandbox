from datetime import datetime, timedelta
from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.operators.trigger_dagrun import TriggerDagRunOperator
from sensors.recent_external_task_sensor import RecentExternalTaskSensor, Trigger
import time

default_args = {
    'owner': 'airflow',
    'depends_on_past': False,
    'email_on_failure': False,
    'email_on_retry': False,
    'retries': 1,
    'retry_delay': timedelta(minutes=1),
}

LOOK_BACK_HOURS = 1

dag = DAG(
    'etl_failure_sensor',
    default_args=default_args,
    description='A DAG that waits for ETL DAG to fail and then executes',
    start_date=datetime(2000, 1, 1),
    schedule_interval=None,
    catchup=False,
    tags=['sensor'],
)

wait_for_etl_failure = RecentExternalTaskSensor(
    task_id='wait_for_etl_failure',
    external_dag_id='dbt_build_monolith',
    external_task_id='fail_task',
    trigger_when=Trigger.OnFailure,
    lookback_hours=LOOK_BACK_HOURS,
    mode='reschedule',
    poke_interval=30,
    dag=dag,
)

def print_message():
    print("Running after FAILURE of ETL DAG!")
    print(f"Current time: {datetime.now()}")
    return "Failure message printed"

perform_task = PythonOperator(
    task_id='perform_task',
    python_callable=print_message,
    dag=dag,
)

def delay_task():
    print(f"Delaying for {LOOK_BACK_HOURS} hours...")
    time.sleep(LOOK_BACK_HOURS * 3600)
    print("Delay complete.")

delay = PythonOperator(
    task_id='delay_task',
    python_callable=delay_task,
    dag=dag,
)

restart_self = TriggerDagRunOperator(
    task_id='restart_self',
    trigger_dag_id='etl_failure_sensor',
    reset_dag_run=True,
    wait_for_completion=False,
    dag=dag
)
wait_for_etl_failure >> perform_task >> delay >> restart_self
