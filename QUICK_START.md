# Quick Start Guide

DataQE Framework quick reference for common use cases.

## TL;DR - Latest Features (v0.3.5)

The dataqe-framework v0.3.5 includes aggregated replacement tracking, multi-block configuration, and dynamic variable replacement.

### Quick Variable Replacement

```bash
# Replace ENVIRONMENT (auto from SPRING_PROFILES_ACTIVE, default: gcpqa)
dataqe-run --config config.yml

# Replace with custom environment
export SPRING_PROFILES_ACTIVE=production
dataqe-run --config config.yml

# Replace custom variables
dataqe-run --config config.yml --replace "@employerID,5" --replace "@storeID,10"

# Custom output directory
dataqe-run --config config.yml --output-dir /reports/custom
```

### Variable Replacement in Tests

```yaml
# Test script
- test_with_variables:
    source:
      query: |
        SELECT COUNT(*) FROM MySQL_ENVIRONMENT.companies
        WHERE employer_id = @employerID
```

Running:
```bash
dataqe-run --config config.yml --replace "@employerID,5"
```

Becomes:
```sql
SELECT COUNT(*) FROM MySQL_gcpqa.companies WHERE employer_id = 5
```

---

## TL;DR - Multi-Block Configuration (v0.2.7)

The dataqe-framework v0.2.7 also supports multiple configuration blocks in a single config file.

### Quick Commands

```bash
# Run first block (default)
dataqe-run --config config.yml

# Run specific block
dataqe-run --config config.yml --block validation_qa

# Run all blocks
dataqe-run --config config.yml --all-blocks
```

### Quick Example

```yaml
config_block_qa:
  source:
    database_type: mysql
    mysql:
      host: qa-db.local
      port: 3306
      user: user
      password: pass
      database: qa_db
  target:
    database_type: gcpbq
    gcp:
      project_id: project-qa
      dataset_id: qa
      credentials_path: ./creds.json
  other:
    validation_script: tests/qa.yml

config_block_prod:
  source:
    database_type: mysql
    mysql:
      host: prod-db.local
      port: 3306
      user: user
      password: pass
      database: prod_db
  target:
    database_type: gcpbq
    gcp:
      project_id: project-prod
      dataset_id: prod
      credentials_path: ./creds.json
  other:
    validation_script: tests/prod.yml
```

Then execute:
```bash
dataqe-run --config config.yml --all-blocks
```

## Kubernetes Credentials Guide

The dataqe-framework also supports environment-based credential extraction using `SPRING_PROFILES_ACTIVE`.

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
    db_name: mysql

  target:
    database_type: gcpbq
    project_id: my-project-dev
    dataset_id: mysql
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
    database='mysql'
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
mysql_creds = CredentialsExtractor.extract_mysql_config(config, 'mysql')

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
    dataset_name='mysql'
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

## Files Changed (Latest)

### Modified (v0.3.5)
- `src/dataqe_framework/reporter.py` - Aggregated replacement tracking in all reporters
- `tests/test_replacement_tracking.py` - Updated tests for metadata-level replacements
- `pyproject.toml` - Version bumped to 0.3.5
- `README.md` - Version and release notes updated

### Modified (v0.3.4)
- `src/dataqe_framework/executor.py` - Replacement tracking in results
- `src/dataqe_framework/preprocessor.py` - Return replacement mappings

### Modified (v0.2.8)
- `src/dataqe_framework/cli.py` - Variable replacement, output directory control

### Modified (v0.2.7)
- `src/dataqe_framework/executor.py` - Block name tracking

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

- **README.md** - Main project documentation with all features
- **CONFIGURATION.md** - Detailed configuration reference
- **PREPROCESSOR.md** - Dynamic dataset replacement guide
- **ARCHITECTURE.md** - Technical architecture and design
- **GETTING_STARTED.md** - Detailed setup and examples

## Support

For detailed information, see:
1. `README.md` - Overview and quick start
2. `CONFIGURATION.md` - Configuration reference
3. `PREPROCESSOR.md` - Dynamic replacement guide
4. `ARCHITECTURE.md` - System design
5. `GETTING_STARTED.md` - Detailed tutorials
