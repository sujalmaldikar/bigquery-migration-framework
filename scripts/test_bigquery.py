
import os
from google.cloud import bigquery

# Read the GCP project ID from environment variables
PROJECT_ID = os.environ.get("GCP_PROJECT_ID")

if not PROJECT_ID:
    raise ValueError("GCP_PROJECT_ID environment variable is not set")

# Create BigQuery client
client = bigquery.Client(project=PROJECT_ID)

print("Successfully connected to BigQuery!")

# Execute a test query
query = """
SELECT
    'Hello from Python' AS message,
    CURRENT_TIMESTAMP() AS execution_time
"""

query_job = client.query(query)

# Get query results
results = query_job.result()

for row in results:
    print("Message:", row.message)
    print("Execution time:", row.execution_time)

print("BigQuery connection test completed!")
