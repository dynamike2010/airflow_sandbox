import logging
from datetime import datetime, timedelta
from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.settings import Session
from airflow.models import DagModel, DagRun, TaskInstance
from airflow.utils.state import State
from statsd import StatsClient
from datetime import timezone

# Configurable
ENV = "prod"
CUTOFF_HOURS = 24


statsd = StatsClient(host="statsd-exporter", port=9125)

def send_metrics():
    session = Session()
    now = datetime.now(timezone.utc)
    since = now - timedelta(hours=CUTOFF_HOURS)

    dag_models = session.query(DagModel).filter(DagModel.is_active == True).all()

    for dag in dag_models:
        # Use dot-separated tags to match mapping file: dwh.dag.enabled.env.domain.dag.type
        env = ENV
        # Extract domain from dag tags (first tag.name starting with "domain")
        domain = next((tag.name for tag in (dag.get_default_view() and dag.tags or []) if hasattr(tag, 'name') and tag.name.startswith("domain")), None)
        dag_id = dag.dag_id
        mtype = "etl"

        # Enabled
        metric_name = f"dwh.dag.enabled.{env}.{domain}.{dag_id}.{mtype}"
        enabled_value = 1 if dag.is_paused is False else 0
        statsd.gauge(metric_name, enabled_value)

        # Last DagRun
        last_run = (
            session.query(DagRun)
            .filter(DagRun.dag_id == dag.dag_id)
            .filter(DagRun.execution_date >= since)
            .order_by(DagRun.execution_date.desc())
            .first()
        )

        if last_run:
            # Status enum: 0=success, 1=running, 2=failed, 3=other
            status_map = {
                State.SUCCESS: 0,
                State.RUNNING: 1,
                State.FAILED: 2,
            }
            run_status = status_map.get(last_run.state, 3)
            metric_name = f"dwh.dag.status.{env}.{domain}.{dag_id}.{mtype}"
            statsd.gauge(metric_name, run_status)

            if last_run.start_date and last_run.end_date:
                duration = (last_run.end_date - last_run.start_date).total_seconds()
                metric_name = f"dwh.dag.duration_seconds.{env}.{domain}.{dag_id}.{mtype}"
                statsd.gauge(metric_name, duration)

            if last_run.execution_date:
                metric_name = f"dwh.dag.execution_time.{env}.{domain}.{dag_id}.{mtype}"
                exec_time = last_run.execution_date.timestamp()
                statsd.gauge(metric_name, exec_time)

            # TaskInstances
            task_instances = (
                session.query(TaskInstance)
                .filter(TaskInstance.dag_id == dag.dag_id)
                .filter(TaskInstance.run_id == last_run.run_id)
                .all()
            )

            for ti in task_instances:
                task_id = ti.task_id
                # dwh.task.status.env.domain.dag.type.task
                metric_name = f"dwh.task.status.{env}.{domain}.{dag_id}.{mtype}.{task_id}"
                task_status = status_map.get(ti.state, 3)
                statsd.gauge(metric_name, task_status)

                if ti.start_date and ti.end_date:
                    task_duration = (ti.end_date - ti.start_date).total_seconds()
                    metric_name = f"dwh.task.duration_seconds.{env}.{domain}.{dag_id}.{mtype}.{task_id}"
                    statsd.gauge(metric_name, task_duration)
                    metric_name = f"dwh.task.execution_time.{env}.{domain}.{dag_id}.{mtype}.{task_id}"
                    exec_time = ti.start_date.timestamp()
                    statsd.gauge(metric_name, exec_time)

                retry_count = max(0, ti.try_number - 1)
                metric_name = f"dwh.task.retry_count.{env}.{domain}.{dag_id}.{mtype}.{task_id}"
                statsd.gauge(metric_name, retry_count)

    session.close()

# DAG definition
dag = DAG(
    'data_ops_metrics',
    start_date=datetime(2000, 1, 1),
    schedule_interval='*/1 * * * *',
    catchup=False,
    tags=['data_ops'],
)

send_metrics_task = PythonOperator(
    task_id='send_metrics',
    python_callable=send_metrics,
    dag=dag,
)

send_metrics_task
