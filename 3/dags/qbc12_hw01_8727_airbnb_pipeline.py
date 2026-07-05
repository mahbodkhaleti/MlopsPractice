from __future__ import annotations

import json
from datetime import timedelta
from pathlib import Path
from urllib.parse import quote_plus

import pendulum
from airflow.decorators import dag, task
from airflow.models import Variable
from sqlalchemy import create_engine, text

STUDENT_SCHEMA = "student_ali_ghanbari"
MATERIALIZED_VIEW = "mv_airbnb_neighbourhood_summary"
AIRFLOW_URL = "http://185.50.38.163:33013"


def make_engine(config: dict):
    password = quote_plus(config["db_password"])
    user = quote_plus(config["db_user"])
    url = (
        f"postgresql+psycopg2://{user}:{password}@"
        f"{config['db_host']}:{config['db_port']}/{config['db_name']}"
    )
    return create_engine(url, pool_pre_ping=True)


@dag(
    dag_id="qbc12_hw01_8727_airbnb_pipeline",
    description="Refresh and validate the HW01 Airbnb neighbourhood summary materialized view.",
    start_date=pendulum.datetime(2026, 7, 5, tz="UTC"),
    schedule="0 6 * * *",
    catchup=False,
    max_active_runs=1,
    default_args={"owner": "ali_ghanbari", "retries": 1, "retry_delay": timedelta(minutes=2)},
    tags=["qbc12", "hw01", "airbnb", "8727"],
)
def airbnb_pipeline():
    @task
    def read_config() -> dict:
        return {
            "db_host": Variable.get("QBC12_DB_HOST", default_var="185.50.38.163"),
            "db_port": Variable.get("QBC12_DB_PORT", default_var="32112"),
            "db_name": Variable.get("QBC12_DB_NAME", default_var="qbc12_airbnb"),
            "db_user": Variable.get("QBC12_DB_USER"),
            "db_password": Variable.get("QBC12_DB_PASSWORD"),
            "student_schema": Variable.get("QBC12_STUDENT_SCHEMA", default_var=STUDENT_SCHEMA),
            "report_dir": Variable.get("QBC12_REPORT_DIR", default_var="/opt/airflow/reports"),
            "airflow_url": AIRFLOW_URL,
        }

    @task
    def refresh_summary(config: dict) -> dict:
        schema = config["student_schema"]
        refresh_sql = f'''
        CREATE SCHEMA IF NOT EXISTS "{schema}";

        DROP MATERIALIZED VIEW IF EXISTS "{schema}".{MATERIALIZED_VIEW};

        CREATE MATERIALIZED VIEW "{schema}".{MATERIALIZED_VIEW} AS
        with date_bounds as (
            select min(date) as start_date
            from core.calendar_day
        ),
        calendar_30 as (
            select
                cd.listing_id,
                avg(cd.price) filter (where cd.price is not null) as avg_calendar_price_30,
                avg(case when cd.available then 1.0 else 0.0 end) as availability_30_rate
            from core.calendar_day cd
            cross join date_bounds db
            where cd.date >= db.start_date
              and cd.date < db.start_date + interval '30 days'
            group by cd.listing_id
        ),
        calendar_365 as (
            select
                listing_id,
                avg(case when available then 1.0 else 0.0 end) as availability_365_rate
            from core.calendar_day
            group by listing_id
        ),
        review_counts as (
            select
                listing_id,
                count(*)::bigint as total_reviews
            from core.review
            group by listing_id
        )
        select
            n.name as neighbourhood,
            count(*)::bigint as num_listings,
            round(avg(l.listing_price)::numeric, 2) as avg_price,
            round(percentile_cont(0.5) within group (order by l.listing_price)::numeric, 2) as median_price,
            round(avg(l.minimum_nights)::numeric, 2) as avg_minimum_nights,
            coalesce(sum(rc.total_reviews), 0)::bigint as total_reviews,
            round(avg(coalesce(rc.total_reviews, 0))::numeric, 2) as reviews_per_listing,
            round(avg(c30.availability_30_rate)::numeric, 4) as availability_30_rate,
            round(avg(c365.availability_365_rate)::numeric, 4) as availability_365_rate
        from core.listing l
        join core.neighbourhood n on n.neighbourhood_id = l.neighbourhood_id
        left join calendar_30 c30 on c30.listing_id = l.listing_id
        left join calendar_365 c365 on c365.listing_id = l.listing_id
        left join review_counts rc on rc.listing_id = l.listing_id
        where l.listing_price is not null
          and l.listing_price > 0
        group by n.name;

        CREATE UNIQUE INDEX IF NOT EXISTS idx_mv_airbnb_neighbourhood_summary_neighbourhood
        ON "{schema}".{MATERIALIZED_VIEW} (neighbourhood);

        CREATE INDEX IF NOT EXISTS idx_mv_airbnb_neighbourhood_summary_num_listings
        ON "{schema}".{MATERIALIZED_VIEW} (num_listings DESC);

        CREATE INDEX IF NOT EXISTS idx_mv_airbnb_neighbourhood_summary_avg_price
        ON "{schema}".{MATERIALIZED_VIEW} (avg_price);
        '''
        statements = [stmt.strip() for stmt in refresh_sql.split(";") if stmt.strip()]
        engine = make_engine(config)
        with engine.begin() as conn:
            for stmt in statements:
                conn.execute(text(stmt))
            row_count = conn.execute(text(f'select count(*) from "{schema}".{MATERIALIZED_VIEW}')).scalar()
        return {"schema": schema, "object": f"{schema}.{MATERIALIZED_VIEW}", "row_count": int(row_count)}

    @task
    def validate_summary(config: dict) -> dict:
        schema = config["student_schema"]
        validation_sql = f'''
        select
            count(*)::int as row_count,
            count(*) filter (where neighbourhood is null or neighbourhood = '')::int as null_neighbourhoods,
            count(*) filter (where avg_price is null or median_price is null or avg_price <= 0 or median_price <= 0)::int as bad_prices,
            count(*) filter (
                where availability_30_rate is null
                   or availability_365_rate is null
                   or availability_30_rate < 0
                   or availability_30_rate > 1
                   or availability_365_rate < 0
                   or availability_365_rate > 1
            )::int as bad_availability
        from "{schema}".{MATERIALIZED_VIEW}
        '''
        engine = make_engine(config)
        with engine.begin() as conn:
            result = conn.execute(text(validation_sql)).mappings().one()
        checks = dict(result)
        checks["passed"] = (
            checks["row_count"] > 0
            and checks["null_neighbourhoods"] == 0
            and checks["bad_prices"] == 0
            and checks["bad_availability"] == 0
        )
        return checks

    @task.branch
    def choose_report_path(validation: dict) -> str:
        return "write_success_report" if validation["passed"] else "write_failure_report"

    def write_report(config: dict, refresh: dict, validation: dict, status: str) -> str:
        report_dir = Path(config["report_dir"])
        report_dir.mkdir(parents=True, exist_ok=True)
        path = report_dir / "hw01_c_airflow_run_report.md"
        path.write_text(
            "# HW01-C Airflow Run Report\n\n"
            f"- Status: {status}\n"
            f"- Airflow URL: {config['airflow_url']}\n"
            f"- Refreshed object: `{refresh['object']}`\n"
            f"- Row count: {refresh['row_count']}\n"
            f"- Validation: `{json.dumps(validation, sort_keys=True)}`\n"
        )
        return str(path)

    @task
    def write_success_report(validation: dict, refresh: dict, config: dict) -> str:
        return write_report(config, refresh, validation, "success")

    @task
    def write_failure_report(validation: dict, refresh: dict, config: dict) -> str:
        path = write_report(config, refresh, validation, "failure")
        raise ValueError(f"Validation failed; report written to {path}")

    config = read_config()
    refresh = refresh_summary(config)
    validation = validate_summary(config)
    refresh >> validation
    branch = choose_report_path(validation)
    success = write_success_report(validation, refresh, config)
    failure = write_failure_report(validation, refresh, config)
    branch >> [success, failure]


airbnb_pipeline()
