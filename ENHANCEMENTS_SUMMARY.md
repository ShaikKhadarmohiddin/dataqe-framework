# DataQE Framework Enhancements Summary

## Overview

The dataqe-framework has been enhanced to support environment-based credential extraction using the `SPRING_PROFILES_ACTIVE` environment variable. This enables seamless deployment across local development and multiple Kubernetes environments (QA, Pre-Production, Production).

## What Changed

### 1. MySQL Connector Enhancement

**File**: `src/dataqe_framework/connectors/mysql_connector.py`

#### Added Features:
- Comprehensive logging for connection lifecycle
- Error handling with detailed error messages
- Connection state validation
- Query execution tracking

#### Changes:
```python
# Added logging support
import logging
logger = logging.getLogger(__name__)

# Constructor now logs initialization
def __init__(self, host, port, user, password, database):
    logger.info(f"MySQLConnector initialized for host={host}, database={database}")

# Connect method includes try-except with logging
def connect(self):
    logger.info(f"Establishing MySQL connection to {self.host}:{self.port}/{self.database}")
    try:
        # connection code
        logger.info("MySQL connection established successfully")
    except Exception as e:
        logger.error(f"Failed to connect to MySQL: {str(e)}")
        raise

# Execute query includes logging and error handling
def execute_query(self, query: str):
    logger.debug(f"Executing query: {query[:100]}...")
    try:
        # query execution
        logger.info(f"Query executed successfully, returned {len(result)} rows")
    except Exception as e:
        logger.error(f"Failed to execute MySQL query: {str(e)}")
        raise

# Close includes logging
def close(self):
    logger.info("Closing MySQL connection")
```

### 2. BigQuery Connector Enhancement

**File**: `src/dataqe_framework/connectors/bigquery_connector.py`

#### Improved PHI Detection:
```python
def _setup_encryption(self):
    """
    Setup KMS encryption configuration for PHI data.

    Detects PHI data based on project_id pattern containing '-h-' or '-p-'
    and applies Customer-Managed Encryption Keys (CMEK) if enabled.
    """
    is_phi = "-h-" in self.project_id or "-p-" in self.project_id

    if not self.use_encryption or not is_phi:
        if is_phi:
            logger.warning(f"PHI project detected ({self.project_id}) but encryption is disabled")
        return

    # Apply KMS encryption for PHI data
```

#### Benefits:
- More robust PHI detection (checks both `-h-` and `-p-` patterns)
- Warning logged if PHI detected but encryption disabled
- Better documentation of encryption behavior

### 3. New Credentials Extractor Module

**File**: `src/dataqe_framework/credentials_extractor.py`

A new utility module for extracting credentials based on `SPRING_PROFILES_ACTIVE`:

#### Key Methods:

```python
class CredentialsExtractor:

    @staticmethod
    def get_profile() -> str:
        """Get the execution profile from SPRING_PROFILES_ACTIVE environment variable."""

    @staticmethod
    def extract_mysql_config(config_details: Dict, database_name: str) -> Dict[str, Any]:
        """Extract MySQL configuration for a specific database."""

    @staticmethod
    def extract_bigquery_config(config_details: Dict, project_name: str, dataset_name: str) -> Dict[str, Any]:
        """Extract BigQuery configuration for a specific dataset."""

    @staticmethod
    def extract_service_account(config_details: Dict, service_account_name: str) -> str:
        """Extract GCP service account credentials."""

    @staticmethod
    def save_service_account_json(sa_key: Any, output_path: str) -> str:
        """Save service account credentials to a JSON file with proper permissions."""
```

#### Features:
- Abstraction for external configuration library integration
- Works with castlight_common_lib or any similar config library
- Comprehensive error handling and logging
- Secure file permissions (0o600) for credential files

#### Usage Example:

```python
from dataqe_framework.credentials_extractor import CredentialsExtractor
import castlight_common_lib.configfunctions as cfg

# Get profile and load configuration
profile = CredentialsExtractor.get_profile()  # Returns: MYLOCAL, gcpqa, gcppreprod, or gcpprod
config = cfg.Config('service_config_file', [profile])

# Extract credentials
mysql_creds = CredentialsExtractor.extract_mysql_config(config, 'ventana')
bq_config = CredentialsExtractor.extract_bigquery_config(config, 'myproject', 'ventana')
sa_key = CredentialsExtractor.extract_service_account(config, 'dataqe-sa')

# Create connectors with extracted credentials
mysql_connector = MySQLConnector(
    host=mysql_creds['host'],
    port=mysql_creds['port'],
    user=mysql_creds['user'],
    password=mysql_creds['password'],
    database=mysql_creds['database']
)
```

## Environment Profiles Supported

| Profile | Environment | Configuration Source |
|---------|-------------|----------------------|
| `MYLOCAL` | Local Development | YAML configuration file |
| `gcpqa` | GCP QA | castlight_common_lib |
| `gcppreprod` | GCP Pre-Prod | castlight_common_lib |
| `gcpprod` | GCP Production | castlight_common_lib |

## Configuration Structure

### For Local Development (MYLOCAL)

```yaml
# config.yaml
database:
  source:
    database_type: mysql
    db_host: localhost
    db_port: 3306
    db_user: root
    db_password: password
    db_name: ventana

  target:
    database_type: gcpbq
    project_id: my-project-dev
    dataset_id: ventana
    credentials_path: ./config/service_account.json
    location: us-central1
```

### For Kubernetes (with castlight_common_lib)

External configuration library provides:

```
config_details.data['mysql']['ventana'] = {
    'db_host': 'mysql.gcpqa.internal',
    'db_port': 3306,
    'db_user': 'db_user',
    'db_password': 'encrypted_password',
    'db_name': 'ventana'
}

config_details.data['bigquery']['myproject']['datasets']['ventana'] = {
    'project_id': 'my-project-qa',
    'location': 'us-central1'
}

config_details.data['gcp']['dataqe-sa'] = {
    'type': 'service_account',
    'project_id': 'my-project-qa',
    'private_key_id': '...',
    # ... rest of service account JSON
}
```

## Usage Patterns

### Local Development

```bash
export SPRING_PROFILES_ACTIVE='MYLOCAL'
python your_script.py
```

### Kubernetes Deployment

```yaml
apiVersion: v1
kind: Pod
metadata:
  name: dataqe-pod
spec:
  containers:
  - name: dataqe-container
    image: your-image:tag
    env:
    - name: SPRING_PROFILES_ACTIVE
      value: "gcpqa"  # or gcppreprod, gcpprod
```

### Code Example

```python
from dataqe_framework.credentials_extractor import CredentialsExtractor
from dataqe_framework.connectors.mysql_connector import MySQLConnector
from dataqe_framework.connectors.bigquery_connector import BigQueryConnector
import castlight_common_lib.configfunctions as cfg

# Get profile and load configuration
profile = CredentialsExtractor.get_profile()
config = cfg.Config('service_config_file', [profile])

# MySQL connection
mysql_creds = CredentialsExtractor.extract_mysql_config(config, 'ventana')
mysql = MySQLConnector(
    host=mysql_creds['host'],
    port=mysql_creds['port'],
    user=mysql_creds['user'],
    password=mysql_creds['password'],
    database=mysql_creds['database']
)
mysql.connect()
source_data = mysql.execute_query("SELECT * FROM your_table")
mysql.close()

# BigQuery connection
bq_config = CredentialsExtractor.extract_bigquery_config(config, 'myproject', 'ventana')
sa_key = CredentialsExtractor.extract_service_account(config, 'dataqe-sa')
creds_path = CredentialsExtractor.save_service_account_json(sa_key, '/tmp/gcp_creds.json')
bq_config['credentials_path'] = creds_path

bq = BigQueryConnector(bq_config)
bq.connect()
target_data = bq.execute_query("SELECT * FROM your_table")
bq.close()
```

## Logging Output

### MySQL Connector Logs

```
MySQLConnector - INFO - 2024-01-15 10:30:45 - MySQLConnector initialized for host=localhost, database=ventana
MySQLConnector - INFO - 2024-01-15 10:30:46 - Establishing MySQL connection to localhost:3306/ventana
MySQLConnector - INFO - 2024-01-15 10:30:46 - MySQL connection established successfully
MySQLConnector - DEBUG - 2024-01-15 10:30:47 - Executing query: SELECT * FROM your_table
MySQLConnector - INFO - 2024-01-15 10:30:47 - Query executed successfully, returned 42 rows
MySQLConnector - INFO - 2024-01-15 10:30:48 - Closing MySQL connection
```

### BigQuery Connector Logs

```
BigQueryConnector - INFO - 2024-01-15 10:31:00 - BigQuery connection established (with encryption)
BigQueryConnector - INFO - 2024-01-15 10:31:01 - KMS encryption configured for PHI data
```

### Credentials Extractor Logs

```
CredentialsExtractor - INFO - Execution profile: gcpqa
CredentialsExtractor - INFO - MySQL config extracted for database: ventana
CredentialsExtractor - INFO - BigQuery config extracted for project: myproject, dataset: ventana
CredentialsExtractor - INFO - Service account credentials extracted: dataqe-sa
CredentialsExtractor - INFO - Service account credentials saved to: /tmp/gcp_creds.json
```

## Benefits

1. **Unified Codebase**: Single code path for all environments
2. **Better Debugging**: Comprehensive logging for troubleshooting
3. **Kubernetes Ready**: Seamless integration with external config libraries
4. **Security**: Proper credential handling with secure file permissions
5. **Error Handling**: Clear error messages for misconfigurations
6. **Backwards Compatible**: Works with existing configuration format

## Documentation

See `KUBERNETES_CREDENTIALS_GUIDE.md` for:
- Detailed configuration examples
- Kubernetes deployment patterns
- PHI data handling
- Troubleshooting guide
- Best practices

## Files Modified/Created

### Modified:
- `src/dataqe_framework/connectors/mysql_connector.py` - Added logging and error handling
- `src/dataqe_framework/connectors/bigquery_connector.py` - Improved PHI detection

### Created:
- `src/dataqe_framework/credentials_extractor.py` - New credentials extraction utility
- `KUBERNETES_CREDENTIALS_GUIDE.md` - Comprehensive usage guide
- `ENHANCEMENTS_SUMMARY.md` - This file

## Testing

### Local Testing

```bash
export SPRING_PROFILES_ACTIVE='MYLOCAL'
python -m pytest tests/
```

### Verify Profile Detection

```python
from dataqe_framework.credentials_extractor import CredentialsExtractor

profile = CredentialsExtractor.get_profile()
print(f"Current profile: {profile}")
```

### Test MySQL Connection

```python
from dataqe_framework.connectors.mysql_connector import MySQLConnector

mysql = MySQLConnector('localhost', 3306, 'root', 'password', 'ventana')
mysql.connect()
print("MySQL connection successful")
mysql.close()
```

### Test BigQuery Connection

```python
from dataqe_framework.connectors.bigquery_connector import BigQueryConnector

config = {
    'project_id': 'my-project',
    'dataset_id': 'ventana',
    'credentials_path': './config/service_account.json',
    'location': 'us-central1'
}

bq = BigQueryConnector(config)
bq.connect()
print("BigQuery connection successful")
bq.close()
```

## Next Steps

1. Review the changes in the framework
2. Read `KUBERNETES_CREDENTIALS_GUIDE.md` for detailed usage
3. Test locally with SPRING_PROFILES_ACTIVE=MYLOCAL
4. Verify castlight_common_lib configuration for Kubernetes profiles
5. Deploy to Kubernetes environments (QA, Pre-Prod, Prod)
6. Monitor logs for proper profile detection and credential extraction
