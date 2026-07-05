# HW01-C Airflow Scheduled Pipeline

- DAG id: `qbc12_hw01_8727_airbnb_pipeline`
- Airflow URL: http://185.50.38.163:33013
- Schedule: daily at 06:00 UTC
- Refreshed object: `student_ali_ghanbari.mv_airbnb_neighbourhood_summary`
- Validation checks: row_count > 0, null_neighbourhoods == 0, bad_prices == 0, bad_availability == 0
- Local syntax check: passed by `py_compile`
- Shared Airflow run timestamp: pending manual/shared-Airflow trigger
- Graph screenshot path: `screenshots/airflow_dag_graph.png`
- Successful run screenshot path: `screenshots/airflow_success_run.png`

The DAG reads database credentials from Airflow Variables: `QBC12_DB_HOST`, `QBC12_DB_PORT`, `QBC12_DB_NAME`, `QBC12_DB_USER`, and `QBC12_DB_PASSWORD`. It recreates the materialized view in Postgres, validates the resulting summary, then branches to a success or failure report task.
