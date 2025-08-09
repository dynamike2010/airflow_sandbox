from datetime import datetime
from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.settings import Session
from airflow.models.dag import DagTag
from airflow.models.dagbag import DagBag

def clean_tags():
    session = Session()
    dagbag = DagBag()
    active_dag_ids = {dag.dag_id for dag in dagbag.dags.values()}
    q = session.query(DagTag).filter(~DagTag.dag_id.in_(active_dag_ids))
    for tag in q:
        print(f"Deleting tag: {tag.name} for DAG: {tag.dag_id}")
        session.delete(tag)
    session.commit()
    session.close()

dag = DAG(
    'clean_tags',
    start_date=datetime(2000, 1, 1),
    schedule_interval=None,
    catchup=False,
    tags=['maintenance'],
)

clean_tags_task = PythonOperator(
    task_id='clean_dag_tags',
    python_callable=clean_tags,
    dag=dag,
)

clean_tags_task

