from datetime import datetime
from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.settings import Session
from airflow.models.dagrun import DagRun
from airflow.models.taskinstance import TaskInstance

def clear_dag_and_task_runs():
    session = Session()
    # Delete all TaskInstance records
    task_instances = session.query(TaskInstance).all()
    for ti in task_instances:
        print(f"Deleting TaskInstance: {ti.dag_id} - {ti.task_id} - {ti.execution_date}")
        session.delete(ti)
    # Delete all DagRun records
    dag_runs = session.query(DagRun).all()
    for dr in dag_runs:
        print(f"Deleting DagRun: {dr.dag_id} - {dr.execution_date}")
        session.delete(dr)
    session.commit()
    session.close()

dag = DAG(
    'clear_dag_runs',
    start_date=datetime(2000, 1, 1),
    schedule_interval=None,
    catchup=False,
    tags=['maintenance'],
)

clear_dag_runs_task = PythonOperator(
    task_id='clear_dag_and_task_runs',
    python_callable=clear_dag_and_task_runs,
    dag=dag,
)

clear_dag_runs_task
