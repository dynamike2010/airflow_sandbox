from datetime import datetime, timedelta, timezone
import time
from airflow import DAG
from airflow.operators.python import PythonOperator, BranchPythonOperator
from airflow.operators.trigger_dagrun import TriggerDagRunOperator
from messages.dag_models import ConfigMessage


default_args = {
    'owner': 'airflow',
    'depends_on_past': False,
    'email_on_failure': False,
    'email_on_retry': False,
    'retries': 1,
    'retry_delay': timedelta(minutes=5),
}

etl = DAG(
    'dbt_build_monolith',
    default_args=default_args,
    description='A DAG that branches based on odd/even minute and fails or succeeds accordingly',
    schedule_interval=timedelta(minutes=1),
    start_date=datetime(2000, 1, 1),
    catchup=False,
    tags=['etl', 'monolith'],
)

def init_task():
    print("Starting ETL execution")
    return "Init completed"

def process_task():
    print("Processing for 10 seconds...")
    time.sleep(10)
    print("completed")
    return "Processing task completed"

def branch_on_minute():
    current_minute = datetime.now().minute
    if current_minute % 2 == 1:  # Odd minute
        print(f"Current minute is {current_minute} which is odd, going to 'end_task'")
        return 'end_task'
    else:  # Even minute
        print(f"Current minute is {current_minute} which is even, going to 'fail_task'")
        return 'fail_task'

def end_task():
    print("Executing end task - Success path")
    return "End task completed successfully"

def fail_task():
    print("Executing fail task - Failure path")
    print(f"Current time: {datetime.now()}")
    # This will cause the task to be marked as failed
    raise ValueError("This task is designed to fail on even minutes")

init_task = PythonOperator(
    task_id='init_task',
    python_callable=init_task,
    dag=etl,
)

process_task = PythonOperator(
    task_id='process_task',
    python_callable=process_task,
    dag=etl,
)

branch_task = BranchPythonOperator(
    task_id='branch_task',
    python_callable=branch_on_minute,
    dag=etl,
)

end_task = PythonOperator(
    task_id='end_task',
    python_callable=end_task,
    dag=etl,
    trigger_rule='none_failed_or_skipped',
)

fail_task = PythonOperator(
    task_id='fail_task',
    python_callable=fail_task,
    dag=etl,
    trigger_rule='all_done',
    retries=0,
)

trigger_upload = TriggerDagRunOperator(
    task_id='trigger_upload',
    dag=etl,
    trigger_dag_id='data_ops',
    conf=ConfigMessage(dag_id=etl.dag_id, command='upload', date_time=datetime.now(timezone.utc).isoformat()).dict(),
)

# Note: This DAG is monitored by two sensor DAGs:
# 1. etl_success_sensor - Triggered when end_task succeeds (on odd minutes)
# 2. etl_failure_sensor - Triggered when fail_task fails (on even minutes)

init_task >> process_task >> branch_task
branch_task >> [end_task, fail_task]
end_task >> trigger_upload
