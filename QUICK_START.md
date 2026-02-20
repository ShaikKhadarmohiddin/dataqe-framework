# Quick Start: Kubernetes Credentials Guide

## TL;DR

The dataqe-framework now supports environment-based credential extraction using `SPRING_PROFILES_ACTIVE`.

### Environment Profiles

```bash
export SPRING_PROFILES_ACTIVE='MYLOCAL'      # Local development
export SPRING_PROFILES_ACTIVE='gcpqa'        # Kubernetes QA
export SPRING_PROFILES_ACTIVE='gcppreprod'   # Kubernetes Pre-Prod
export SPRING_PROFILES_ACTIVE='gcpprod'      # Kubernetes Production
```

## Local Development

### 1. Set Profile

```bash
export SPRING_PROFILES_ACTIVE='MYLOCAL'
```

### 2. Create Configuration File

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

### 3. Use Connectors

```python
from dataqe_framework.connectors.mysql_connector import MySQLConnector

mysql = MySQLConnector(
    host='localhost',
    port=3306,
    user='root',
    password='password',
    database='ventana'
)
mysql.connect()
results = mysql.execute_query("SELECT * FROM table")
mysql.close()
```

## Kubernetes Deployment

### 1. Set Environment Variable in Pod

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
      value: "gcpqa"
```

### 2. Extract Credentials

Use `CredentialsExtractor` to get credentials from castlight_common_lib:

```python
from dataqe_framework.credentials_extractor import CredentialsExtractor
from dataqe_framework.connectors.mysql_connector import MySQLConnector
import castlight_common_lib.configfunctions as cfg

# Load configuration based on SPRING_PROFILES_ACTIVE
profile = CredentialsExtractor.get_profile()  # Returns: gcpqa, gcppreprod, or gcpprod
config = cfg.Config('service_config_file', [profile])

# Extract MySQL credentials
mysql_creds = CredentialsExtractor.extract_mysql_config(config, 'ventana')

# Create connector
mysql = MySQLConnector(
    host=mysql_creds['host'],
    port=mysql_creds['port'],
    user=mysql_creds['user'],
    password=mysql_creds['password'],
    database=mysql_creds['database']
)

mysql.connect()
results = mysql.execute_query("SELECT * FROM table")
mysql.close()
```

### 3. For BigQuery

```python
from dataqe_framework.credentials_extractor import CredentialsExtractor
from dataqe_framework.connectors.bigquery_connector import BigQueryConnector

# Get profile and load configuration
profile = CredentialsExtractor.get_profile()
config = cfg.Config('service_config_file', [profile])

# Extract BigQuery configuration
bq_config = CredentialsExtractor.extract_bigquery_config(
    config,
    project_name='myproject',
    dataset_name='ventana'
)

# Extract and save service account credentials
sa_key = CredentialsExtractor.extract_service_account(config, 'dataqe-sa')
creds_path = CredentialsExtractor.save_service_account_json(
    sa_key,
    '/tmp/gcp_credentials.json'
)

# Create BigQuery connector
bq_config['credentials_path'] = creds_path

bq = BigQueryConnector(bq_config)
bq.connect()
results = bq.execute_query("SELECT * FROM table")
bq.close()
```

## What's New

### 1. Enhanced MySQL Connector
- Added logging for all operations
- Error handling with clear messages
- Connection state validation

### 2. Improved BigQuery Connector
- Better PHI detection (checks `-h-` and `-p-` patterns)
- Warning if PHI detected but encryption disabled
- Improved documentation

### 3. New Credentials Extractor
- Utility to extract credentials from external config libraries
- Support for MySQL, BigQuery, and GCP service accounts
- Secure file handling (permissions 0o600)
- Comprehensive error handling

## Files Changed

### Modified Files
- `src/dataqe_framework/connectors/mysql_connector.py` - Added logging
- `src/dataqe_framework/connectors/bigquery_connector.py` - Improved PHI detection

### New Files
- `src/dataqe_framework/credentials_extractor.py` - Credentials extraction utility
- `KUBERNETES_CREDENTIALS_GUIDE.md` - Detailed guide
- `ENHANCEMENTS_SUMMARY.md` - Full summary
- `QUICK_START.md` - This file

## Troubleshooting

### Check Current Profile
```bash
echo $SPRING_PROFILES_ACTIVE
```

### See Detailed Logs
```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

### Verify Configuration
```python
from dataqe_framework.credentials_extractor import CredentialsExtractor

profile = CredentialsExtractor.get_profile()
print(f"Profile: {profile}")
```

## Documentation

- **ENHANCEMENTS_SUMMARY.md** - Complete technical overview
- **KUBERNETES_CREDENTIALS_GUIDE.md** - Detailed usage guide with examples
- **QUICK_START.md** - This quick reference

## Support

For detailed information, see:
1. `KUBERNETES_CREDENTIALS_GUIDE.md` - Configuration examples and best practices
2. `ENHANCEMENTS_SUMMARY.md` - Technical details of all changes
3. Code comments in `credentials_extractor.py` and connectors
