from pydantic import BaseModel


class ConfigMessage(BaseModel):
    dag_id: str
    command: str
    date_time: str
