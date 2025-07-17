# Airflow Testing Project

This project provides a simple setup for testing Apache Airflow 2.6.3 using Docker Compose.

## Prerequisites

- Docker and Docker Compose installed on your machine
- Minimum requirements:
  - 4GB of RAM
  - 2 CPU cores
  - 10GB of disk space

## Project Structure

```
/
├── docker-compose.yaml          # Docker Compose configuration
├── dags/                        # Place your DAG files here
│   ├── dbt_build_monolith.py    # Example DAG for testing dependencies
│   ├── success_sensor.py        # DAG triggered on success of dbt_build_monolith.py
│   ├── failure_sensor.py        # DAG triggered on failure of dbt_build_monolith.py
│   └── data_ops.py              # DAG for data operations pipeline
├── logs/                        # Airflow logs - docker mapped
├── plugins/                     # Airflow plugins
└── config/                      # Airflow configuration
```

## Getting Started

> **Note:**  
> To install the required dependencies, run:
>
> ```bash
> pip install uv
> uv venv venv
> source venv/bin/activate
> uv pip install -r requirements.txt
> ```

1. Start the Airflow services:

```bash
./airflow.sh start
```

2. Access the Airflow web UI at http://localhost:8080
   - Username: airflow@airflow.com
   - Password: airflow

3. Trigger the example DAG to test task dependencies:
   - Go to the DAGs page
   - Find "dbt_build_monolith"
   - Toggle the switch to unpause the DAG
   - Click on the "Trigger DAG" button

## Testing DAG Dependencies

The example DAGs demonstrate dependency patterns between DAGs:

1. `dbt_build_monolith.py` (DAG ID: `dbt_build_monolith`): Base DAG that branches based on odd/even minutes
2. `success_sensor.py` (DAG ID: `etl_success_sensor`): Triggered when DAG 1 succeeds
3. `failure_sensor.py` (DAG ID: `etl_failure_sensor`): Triggered when DAG 1 fails
4. `data_ops.py` (DAG ID: `data_ops`): DAG for data operations pipeline

You can visualize this dependency graph in the Airflow UI by clicking on the DAG name and then viewing the Graph view.

## Stopping the Environment

To stop all services:

```bash
./airflow.sh stop
```

To stop all services and delete volumes (this will delete the database):

```bash
./airflow.sh stop-clean
```

## Creating Your Own DAGs

To create your own DAGs, simply add Python files to the `dags/` directory. Any file containing a DAG object will be automatically picked up by Airflow.
