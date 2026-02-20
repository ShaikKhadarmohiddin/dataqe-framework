# Implementation Pattern: Using Enhanced Connectors

## Pattern Overview

The enhanced connectors follow a consistent pattern for both local and Kubernetes environments.

## Local Development Pattern

### MySQL in Local Environment

```python
from dataqe_framework.connectors.mysql_connector import MySQLConnector

# Step 1: Create connector with direct credentials
connector = MySQLConnector(
    host='localhost',           # From your config file
    port=3306,
    user='root',
    password='password',
    database='ventana'
)

# Step 2: Connect
connector.connect()

# Step 3: Execute queries
results = connector.execute_query("SELECT * FROM table")

# Step 4: Close
connector.close()

# Output logs:
# MySQLConnector - INFO - MySQLConnector initialized for host=localhost, database=ventana
# MySQLConnector - INFO - Establishing MySQL connection to localhost:3306/ventana
# MySQLConnector - INFO - MySQL connection established successfully
# MySQLConnector - INFO - Query executed successfully, returned N rows
# MySQLConnector - INFO - Closing MySQL connection
```

### BigQuery in Local Environment

```python
from dataqe_framework.connectors.bigquery_connector import BigQueryConnector

# Step 1: Prepare config
config = {
    "project_id": "my-project-dev",
    "dataset_id": "ventana",
    "credentials_path": "./config/service_account.json",
    "location": "us-central1",
    "use_encryption": False  # Not needed for non-PHI
}

# Step 2: Create connector
connector = BigQueryConnector(config)

# Step 3: Connect
connector.connect()

# Step 4: Execute queries
results = connector.execute_query("SELECT * FROM table")

# Step 5: Close
connector.close()

# Output logs:
# BigQueryConnector - INFO - BigQuery connection established (non-PHI)
```

## Kubernetes Pattern with CredentialsExtractor

### MySQL in Kubernetes Environment

```python
# Step 0: Ensure SPRING_PROFILES_ACTIVE=gcpqa (or gcppreprod, gcpprod)

from dataqe_framework.credentials_extractor import CredentialsExtractor
from dataqe_framework.connectors.mysql_connector import MySQLConnector
import castlight_common_lib.configfunctions as cfg

# Step 1: Get execution profile
profile = CredentialsExtractor.get_profile()
# Returns: 'gcpqa', 'gcppreprod', or 'gcpprod'

# Step 2: Load configuration based on profile
config = cfg.Config('service_config_file', [profile])

# Step 3: Extract MySQL credentials
mysql_creds = CredentialsExtractor.extract_mysql_config(config, 'ventana')

# Step 4: Create connector with extracted credentials
connector = MySQLConnector(
    host=mysql_creds['host'],
    port=mysql_creds['port'],
    user=mysql_creds['user'],
    password=mysql_creds['password'],
    database=mysql_creds['database']
)

# Step 5: Connect
connector.connect()

# Step 6: Execute queries
results = connector.execute_query("SELECT * FROM table")

# Step 7: Close
connector.close()

# Output logs:
# CredentialsExtractor - INFO - Execution profile: gcpqa
# CredentialsExtractor - INFO - MySQL config extracted for database: ventana
# MySQLConnector - INFO - MySQLConnector initialized for host=mysql.gcpqa.internal, database=ventana
# MySQLConnector - INFO - MySQL connection established successfully
# MySQLConnector - INFO - Query executed successfully, returned N rows
```

### BigQuery in Kubernetes Environment

```python
# Step 0: Ensure SPRING_PROFILES_ACTIVE=gcpqa (or gcppreprod, gcpprod)

from dataqe_framework.credentials_extractor import CredentialsExtractor
from dataqe_framework.connectors.bigquery_connector import BigQueryConnector
import castlight_common_lib.configfunctions as cfg

# Step 1: Get execution profile
profile = CredentialsExtractor.get_profile()

# Step 2: Load configuration based on profile
config = cfg.Config('service_config_file', [profile])

# Step 3: Extract BigQuery configuration
bq_config = CredentialsExtractor.extract_bigquery_config(
    config,
    project_name='myproject',
    dataset_name='ventana'
)

# Step 4: Extract and save service account credentials
sa_key = CredentialsExtractor.extract_service_account(config, 'dataqe-sa')
credentials_path = CredentialsExtractor.save_service_account_json(
    sa_key,
    '/tmp/gcp_service_account.json'
)

# Step 5: Add credentials path to config
bq_config['credentials_path'] = credentials_path

# Step 6: Create connector
connector = BigQueryConnector(bq_config)

# Step 7: Connect
connector.connect()

# Step 8: Execute queries
results = connector.execute_query("SELECT * FROM table")

# Step 9: Close
connector.close()

# Output logs:
# CredentialsExtractor - INFO - Execution profile: gcpqa
# CredentialsExtractor - INFO - BigQuery config extracted for project: myproject, dataset: ventana
# CredentialsExtractor - INFO - Service account credentials extracted: dataqe-sa
# CredentialsExtractor - INFO - Service account credentials saved to: /tmp/gcp_service_account.json
# BigQueryConnector - INFO - BigQuery connection established (with encryption)
# BigQueryConnector - INFO - KMS encryption configured for PHI data: projects/my-project-h/locations/us-central1/...
```

## Comparison: Local vs Kubernetes

### MySQL Connector Initialization

```
LOCAL (MYLOCAL)              │  KUBERNETES (gcpqa/gcppreprod/gcpprod)
─────────────────────────────┼──────────────────────────────────────
MySQLConnector(              │  mysql_creds = CredentialsExtractor.
  host='localhost',          │    extract_mysql_config(config, 'ventana')
  port=3306,                 │  MySQLConnector(
  user='root',               │    host=mysql_creds['host'],
  password='password',       │    port=mysql_creds['port'],
  database='ventana'         │    user=mysql_creds['user'],
)                            │    password=mysql_creds['password'],
                             │    database=mysql_creds['database']
                             │  )
```

### BigQuery Connector Initialization

```
LOCAL (MYLOCAL)              │  KUBERNETES (gcpqa/gcppreprod/gcpprod)
─────────────────────────────┼──────────────────────────────────────
config = {                   │  bq_config = CredentialsExtractor.
  'project_id': 'my-proj',   │    extract_bigquery_config(
  'dataset_id': 'ventana',   │      config, 'myproject', 'ventana'
  'credentials_path':        │    )
    './config/sa.json',      │  sa_key = CredentialsExtractor.
  'location': 'us-central1'  │    extract_service_account(
}                            │      config, 'dataqe-sa'
BigQueryConnector(config)    │    )
                             │  creds_path = CredentialsExtractor.
                             │    save_service_account_json(
                             │      sa_key, '/tmp/sa.json'
                             │    )
                             │  bq_config['credentials_path'] = creds_path
                             │  BigQueryConnector(bq_config)
```

## Error Handling Pattern

### MySQL Errors

```python
from dataqe_framework.connectors.mysql_connector import MySQLConnector
import logging

logger = logging.getLogger(__name__)

try:
    connector = MySQLConnector(host, port, user, password, database)
    connector.connect()
    results = connector.execute_query(query)
except Exception as e:
    logger.error(f"MySQL operation failed: {e}")
    # Handle error
finally:
    connector.close()

# Possible errors logged:
# - Failed to connect to MySQL: Unable to connect to host
# - Failed to execute MySQL query: Syntax error in query
```

### BigQuery Errors

```python
from dataqe_framework.connectors.bigquery_connector import BigQueryConnector
import logging

logger = logging.getLogger(__name__)

try:
    connector = BigQueryConnector(config)
    connector.connect()
    results = connector.execute_query(query)
except Exception as e:
    logger.error(f"BigQuery operation failed: {e}")
    # Handle error
finally:
    connector.close()

# Possible errors logged:
# - Failed to connect to BigQuery: Invalid credentials
# - Failed to setup KMS encryption: Key not found
# - Failed to execute BigQuery query: Invalid query
```

### Credentials Extraction Errors

```python
from dataqe_framework.credentials_extractor import CredentialsExtractor
import logging

logger = logging.getLogger(__name__)

try:
    mysql_creds = CredentialsExtractor.extract_mysql_config(
        config, 'ventana'
    )
except KeyError as e:
    logger.error(f"MySQL configuration not found: {e}")
except ValueError as e:
    logger.error(f"Invalid MySQL configuration: {e}")

# Possible errors:
# - MySQL configuration not found for database: ventana
# - Missing required MySQL field: host
# - Project 'myproject' not found. Available: [...]
# - Dataset 'ventana' not found in project 'myproject'
# - Service account 'dataqe-sa' not found
```

## Complete Application Pattern

### Full End-to-End Example

```python
import os
import logging
from dataqe_framework.credentials_extractor import CredentialsExtractor
from dataqe_framework.connectors.mysql_connector import MySQLConnector
from dataqe_framework.connectors.bigquery_connector import BigQueryConnector
import castlight_common_lib.configfunctions as cfg

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(name)s - %(levelname)s - %(asctime)s - %(message)s'
)
logger = logging.getLogger(__name__)

def main():
    try:
        # Step 1: Get execution profile
        profile = CredentialsExtractor.get_profile()
        logger.info(f"Running in {profile} environment")

        # Step 2: Load configuration
        config = cfg.Config('service_config_file', [profile])

        # Step 3: Setup MySQL connection
        mysql_creds = CredentialsExtractor.extract_mysql_config(config, 'ventana')
        mysql = MySQLConnector(
            host=mysql_creds['host'],
            port=mysql_creds['port'],
            user=mysql_creds['user'],
            password=mysql_creds['password'],
            database=mysql_creds['database']
        )
        mysql.connect()

        # Step 4: Setup BigQuery connection
        bq_config = CredentialsExtractor.extract_bigquery_config(
            config, 'myproject', 'ventana'
        )
        sa_key = CredentialsExtractor.extract_service_account(config, 'dataqe-sa')
        creds_path = CredentialsExtractor.save_service_account_json(
            sa_key, '/tmp/gcp_sa.json'
        )
        bq_config['credentials_path'] = creds_path

        bq = BigQueryConnector(bq_config)
        bq.connect()

        # Step 5: Execute data validation
        source_query = "SELECT * FROM source_table LIMIT 100"
        target_query = "SELECT * FROM target_table LIMIT 100"

        logger.info("Executing source query...")
        source_results = mysql.execute_query(source_query)

        logger.info("Executing target query...")
        target_results = bq.execute_query(target_query)

        # Step 6: Compare results
        logger.info(f"Source rows: {len(source_results)}")
        logger.info(f"Target rows: {len(target_results)}")

        # Step 7: Cleanup
        mysql.close()
        bq.close()

        logger.info("Data validation completed successfully")

    except Exception as e:
        logger.error(f"Data validation failed: {e}")
        raise

if __name__ == "__main__":
    main()
```

## Testing the Pattern

### Unit Test Example

```python
import pytest
from dataqe_framework.connectors.mysql_connector import MySQLConnector
from unittest.mock import patch, MagicMock

def test_mysql_connector_local():
    """Test MySQL connector in local environment"""
    connector = MySQLConnector(
        host='localhost',
        port=3306,
        user='root',
        password='password',
        database='ventana'
    )

    # Verify initialization
    assert connector.host == 'localhost'
    assert connector.database == 'ventana'

@patch('castlight_common_lib.configfunctions.Config')
def test_mysql_connector_kubernetes(mock_config):
    """Test MySQL connector with credentials extractor in Kubernetes"""
    from dataqe_framework.credentials_extractor import CredentialsExtractor

    # Mock configuration
    mock_config.return_value.data = {
        'mysql': {
            'ventana': {
                'db_host': 'mysql.gcpqa.internal',
                'db_port': 3306,
                'db_user': 'dbuser',
                'db_password': 'dbpass',
                'db_name': 'ventana'
            }
        }
    }

    # Extract credentials
    creds = CredentialsExtractor.extract_mysql_config(
        mock_config.return_value, 'ventana'
    )

    # Create connector
    connector = MySQLConnector(
        host=creds['host'],
        port=creds['port'],
        user=creds['user'],
        password=creds['password'],
        database=creds['database']
    )

    assert connector.host == 'mysql.gcpqa.internal'
```

## Kubernetes Deployment Example

```yaml
apiVersion: batch/v1
kind: Job
metadata:
  name: dataqe-validation-job
spec:
  template:
    spec:
      containers:
      - name: dataqe
        image: dataqe:latest
        imagePullPolicy: Always

        # Set environment profile
        env:
        - name: SPRING_PROFILES_ACTIVE
          value: "gcpqa"

        # Mount configuration
        volumeMounts:
        - name: config
          mountPath: /etc/dataqe/config

        # Run validation
        command: ["python", "-m", "dataqe.main"]
        args:
        - "--config"
        - "/etc/dataqe/config/config.yaml"

      volumes:
      - name: config
        configMap:
          name: dataqe-config

      restartPolicy: Never
```

## Summary

This pattern ensures:
1. ✅ Single codebase for all environments
2. ✅ Clear credential extraction logic
3. ✅ Comprehensive logging for debugging
4. ✅ Proper error handling
5. ✅ Secure credential management
6. ✅ Easy testing
7. ✅ Kubernetes-ready deployment
