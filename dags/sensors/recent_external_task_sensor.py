from datetime import timedelta
from airflow.sensors.base import BaseSensorOperator
from airflow.utils.session import provide_session
from airflow.models import TaskInstance, DagRun
import pendulum
from enum import Enum, auto

class Trigger(Enum):
    OnSuccess = auto()    # Trigger when task succeeded
    OnFailure = auto()    # Trigger when task failed

class RecentExternalTaskSensor(BaseSensorOperator):
    """
    Sensor that waits for a task in another DAG to complete within a specific time window.
    This is more flexible than the standard ExternalTaskSensor as it can check for 
    task completion within a time range rather than an exact execution date.
    """

    def __init__(
        self,
        *,
        external_dag_id: str,
        external_task_id: str,
        trigger_when: Trigger = Trigger.OnSuccess,
        lookback_hours: int = 2,
        **kwargs
    ):
        super().__init__(**kwargs)
        self.external_dag_id = external_dag_id
        self.external_task_id = external_task_id
        self.trigger_states = ['success'] if trigger_when == Trigger.OnSuccess else ['failed']
        self.time_window = timedelta(hours=lookback_hours)
        
    @provide_session
    def poke(self, context, session=None):
        # Get timezone-aware datetime objects
        current_time = pendulum.now('UTC')
        earliest_time = current_time.subtract(seconds=int(self.time_window.total_seconds()))
        
        self.log.info(
            f"Poking for {self.external_dag_id}.{self.external_task_id} between "
            f"{earliest_time} and {current_time}, looking for states: {self.trigger_states}"
        )
        
        # Find task instances within time window
        TI = TaskInstance
        DR = DagRun
        
        # Query for task instances in the specified DAG that completed within our time window
        query = (
            session.query(TI)
            .join(DR, TI.dag_id == DR.dag_id)
            .filter(TI.dag_id == self.external_dag_id)
            .filter(TI.task_id == self.external_task_id)
            .filter(TI.state.in_(self.trigger_states))
            .filter(TI.end_date >= earliest_time)
            .filter(TI.end_date <= current_time)
            .order_by(TI.end_date.desc())
        )
        
        # Get the most recent task instance
        task_instances = query.all()
        if not task_instances:
            self.log.info("No matching task instances found within the time window.")
            return False
        
        # Check the state of the most recent task instance
        most_recent_ti = task_instances[0]
        self.log.info(
            f"Found task instance {most_recent_ti} "
            f"with state {most_recent_ti.state} "
            f"(end_date: {most_recent_ti.end_date})"
        )
        
        # Return True if the state is in the allowed_states
        return most_recent_ti.state in self.trigger_states
