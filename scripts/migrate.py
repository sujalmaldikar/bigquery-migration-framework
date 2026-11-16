
import os
import re
import argparse
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

BASE_DIR = Path(__file__).resolve().parent.parent
MIGRATIONS_DIR = BASE_DIR / "migrations"

DATASET_REF = f"{PROJECT_ID}.{DATASET_ID}"


# --------------------------------------------------
# 2. Migration tracking
# --------------------------------------------------

def get_marker_table_name(migration_id):
    name = Path(migration_id).stem
    safe_name = re.sub(r"[^A-Za-z0-9_]", "_", name)
    return f"migration_{safe_name}"


def get_executed_migrations():
    tables = client.list_tables(DATASET_REF)

    return {
        table.table_id
        for table in tables
        if table.table_id.startswith("migration_")
    }


def record_migration(migration_id):
    marker_name = get_marker_table_name(migration_id)
    marker_table = f"`{PROJECT_ID}.{DATASET_ID}.{marker_name}`"

    query = f"""
    CREATE TABLE IF NOT EXISTS {marker_table} AS
    SELECT
        @migration_id AS migration_id,
        CURRENT_TIMESTAMP() AS executed_at
    """

    config = bigquery.QueryJobConfig(
        query_parameters=[
            bigquery.ScalarQueryParameter(
                "migration_id", "STRING", migration_id
            )
        ]
    )

    client.query(query, job_config=config).result()


def remove_migration_record(migration_id):
    marker_name = get_marker_table_name(migration_id)
    marker_table = f"`{PROJECT_ID}.{DATASET_ID}.{marker_name}`"

    client.query(f"DROP TABLE IF EXISTS {marker_table}").result()


# --------------------------------------------------
# 3. Parse UP and DOWN sections
# --------------------------------------------------

def get_migration_sections(migration_file):
    content = migration_file.read_text()

    up_match = re.search(
        r"(?ims)^\s*--\s*UP\s*$([\s\S]*?)^\s*--\s*DOWN\s*$",
        content
    )

    down_match = re.search(
        r"(?ims)^\s*--\s*DOWN\s*$([\s\S]*)$",
        content
    )

    if not up_match or not down_match:
        raise ValueError(
            f"{migration_file.name} must contain -- UP and -- DOWN sections"
        )

    up_sql = up_match.group(1).strip()
    down_sql = down_match.group(1).strip()

    if not up_sql:
        raise ValueError(f"Empty UP section: {migration_file.name}")

    if not down_sql:
        raise ValueError(f"Empty DOWN section: {migration_file.name}")

    return up_sql, down_sql


# --------------------------------------------------
# 4. Apply migrations
# --------------------------------------------------

def run_migrations():
    executed = get_executed_migrations()
    migration_files = sorted(MIGRATIONS_DIR.glob("*.sql"))

    for migration_file in migration_files:
        migration_id = migration_file.name
        marker_name = get_marker_table_name(migration_id)

        if marker_name in executed:
            print(f"SKIPPED: {migration_id}")
            continue

        up_sql, _ = get_migration_sections(migration_file)

        print(f"RUNNING: {migration_id}")

        client.query(up_sql).result()
        record_migration(migration_id)

        print(f"SUCCESS: {migration_id}")


# --------------------------------------------------
# 5. Rollback migrations
# --------------------------------------------------

def rollback_migrations(rollback_all=False):
    migration_files = sorted(
        MIGRATIONS_DIR.glob("*.sql"),
        reverse=True
    )

    executed = get_executed_migrations()
    pending_rollbacks = []

    for migration_file in migration_files:
        migration_id = migration_file.name
        marker_name = get_marker_table_name(migration_id)

        if marker_name in executed:
            _, down_sql = get_migration_sections(migration_file)

            pending_rollbacks.append(
                (migration_id, down_sql)
            )

            if not rollback_all:
                break

    if not pending_rollbacks:
        print("No executed migrations to roll back.")
        return

    print("\nMigrations selected for rollback:")

    for migration_id, _ in pending_rollbacks:
        print(f"  {migration_id}")

    confirmation = input(
        "\nThis operation can permanently delete data. "
        "Continue? Type YES: "
    )

    if confirmation != "YES":
        print("Rollback cancelled.")
        return

    for migration_id, down_sql in pending_rollbacks:
        print(f"\nROLLING BACK: {migration_id}")

        client.query(down_sql).result()
        remove_migration_record(migration_id)

        print(f"ROLLBACK SUCCESS: {migration_id}")


# --------------------------------------------------
# 6. Migration status
# --------------------------------------------------

def show_status():
    executed = get_executed_migrations()
    migration_files = sorted(MIGRATIONS_DIR.glob("*.sql"))

    print("\nMIGRATION STATUS")
    print("-" * 45)

    for migration_file in migration_files:
        migration_id = migration_file.name
        marker_name = get_marker_table_name(migration_id)

        status = (
            "EXECUTED"
            if marker_name in executed
            else "PENDING"
        )

        print(f"{migration_id}: {status}")

    print("-" * 45)


# --------------------------------------------------
# 7. Main entry point
# --------------------------------------------------

if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="BigQuery Migration Framework"
    )

    parser.add_argument(
        "--rollback",
        action="store_true",
        help="Rollback the latest executed migration"
    )

    parser.add_argument(
        "--rollback-all",
        action="store_true",
        help="Rollback all executed migrations"
    )

    parser.add_argument(
        "--status",
        action="store_true",
        help="Display migration status"
    )

    args = parser.parse_args()

    print("\nStarting BigQuery Migration Engine...\n")

    if args.rollback and args.rollback_all:
        parser.error("Choose either --rollback or --rollback-all")

    if args.rollback:
        rollback_migrations()

    elif args.rollback_all:
        rollback_migrations(rollback_all=True)

    elif args.status:
        show_status()

    else:
        run_migrations()

    print("\nMigration process completed.")
