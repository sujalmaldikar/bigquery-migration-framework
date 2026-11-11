
import os
import re
from pathlib import Path

from google.cloud import bigquery


# --------------------------------------------------
# 1. Configuration
# --------------------------------------------------

PROJECT_ID = os.environ.get("GCP_PROJECT_ID")
DATASET_ID = os.environ.get("BQ_DATASET", "automation_dataset")

if not PROJECT_ID:
    raise ValueError("GCP_PROJECT_ID is not set")

client = bigquery.Client(project=PROJECT_ID)

MIGRATIONS_DIR = (
    Path(__file__).resolve().parent.parent / "migrations"
)

DATASET_REF = f"{PROJECT_ID}.{DATASET_ID}"


# --------------------------------------------------
# 2. Generate a tracking table name
# --------------------------------------------------

def get_marker_table_name(migration_id):

    name = Path(migration_id).stem

    safe_name = re.sub(r"[^A-Za-z0-9_]", "_", name)

    return f"migration_{safe_name}"


# --------------------------------------------------
# 3. Find executed migrations
# --------------------------------------------------

def get_executed_migrations():

    tables = client.list_tables(DATASET_REF)

    return {
        table.table_id
        for table in tables
        if table.table_id.startswith("migration_")
    }


# --------------------------------------------------
# 4. Record successful migration
# --------------------------------------------------

def record_migration(migration_id):

    marker_name = get_marker_table_name(migration_id)

    marker_table = f"`{PROJECT_ID}.{DATASET_ID}.{marker_name}`"

    query = f"""
    CREATE TABLE IF NOT EXISTS {marker_table} AS
    SELECT
        @migration_id AS migration_id,
        CURRENT_TIMESTAMP() AS executed_at
    """

    job_config = bigquery.QueryJobConfig(
        query_parameters=[
            bigquery.ScalarQueryParameter(
                "migration_id", "STRING", migration_id
            )
        ]
    )

    client.query(
        query,
        job_config=job_config
    ).result()


# --------------------------------------------------
# 5. Run pending migrations
# --------------------------------------------------

def run_migrations():

    executed = get_executed_migrations()

    migration_files = sorted(
        MIGRATIONS_DIR.glob("*.sql")
    )

    if not migration_files:
        print("No SQL migration files found.")
        return

    for migration_file in migration_files:

        migration_id = migration_file.name

        marker_name = get_marker_table_name(migration_id)

        if marker_name in executed:
            print(f"SKIPPED: {migration_id} already executed.")
            continue

        print(f"RUNNING: {migration_id}")

        sql = migration_file.read_text().strip()

        if not sql:
            raise ValueError(
                f"Migration file is empty: {migration_id}"
            )

        # Execute the SQL migration
        client.query(sql).result()

        # Create a marker only after successful execution
        record_migration(migration_id)

        print(f"SUCCESS: {migration_id}")


# --------------------------------------------------
# 6. Main entry point
# --------------------------------------------------

if __name__ == "__main__":

    print("Starting BigQuery Migration Engine...")

    run_migrations()

    print("Migration process completed.")
