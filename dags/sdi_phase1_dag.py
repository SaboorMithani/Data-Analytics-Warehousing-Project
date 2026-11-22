from airflow import DAG
from airflow.operators.bash import BashOperator
from datetime import datetime, timedelta

default_args = {"owner": "pharma_de_team", "depends_on_past": False, "retries": 1, "retry_delay": timedelta(minutes=1)}

with DAG(
    dag_id="pharma_sdi_phase1_pipeline",
    default_args=default_args,
    description="Automated Pharmaceutical SDI Data Mart Pipeline",
    schedule_interval=None,
    start_date=datetime(2026, 11, 1),
    catchup=False,
) as dag:
    t1 = BashOperator(task_id="oversample_source_data", bash_command="python scripts/oversample.py")
    t2 = BashOperator(task_id="ingest_to_staging_ods", bash_command="python scripts/ingest_staging.py")
    t3 = BashOperator(task_id="transform_star_schema_and_query", bash_command="python scripts/transform_mart.py")
    t1 >> t2 >> t3
