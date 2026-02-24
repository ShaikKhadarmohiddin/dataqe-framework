# Kubernetes Credentials Configuration Guide

## Overview

The dataqe-framework now includes enhanced support for environment-based credential extraction using the `SPRING_PROFILES_ACTIVE` environment variable. This enables seamless deployment across local development and multiple Kubernetes environments (QA, Pre-Production, Production) with a single codebase.

## Environment Profiles

The framework supports the following profiles:

| Profile | Environment | Description |
|---------|-------------|-------------|
| `MYLOCAL` | Local Development | Default for local testing. Reads credentials directly from configuration. |
| `gcpqa` | GCP QA | Kubernetes deployment in QA environment. |
| `gcppreprod` | GCP Pre-Prod | Kubernetes deployment in Pre-Production environment. |
| `gcpprod` | GCP Production | Kubernetes deployment in Production environment. |

## Setting SPRING_PROFILES_ACTIVE

### Local Development

```bash
export SPRING_PROFILES_ACTIVE='MYLOCAL'
python your_script.py
```

### Kubernetes Deployment

#### Using Environment Variable in Pod Spec

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

#### Using ConfigMap

```yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: dataqe-config
data:
  SPRING_PROFILES_ACTIVE: "gcpqa"
---
apiVersion: v1
kind: Pod
metadata:
  name: dataqe-pod
spec:
  containers:
  - name: dataqe-container
    image: your-image:tag
    envFrom:
    - configMapRef:
        name: dataqe-config
```

#### Using Kubernetes Secret

```yaml
apiVersion: v1
kind: Secret
metadata:
  name: dataqe-env
type: Opaque
data:
  SPRING_PROFILES_ACTIVE: Z2NwcWE=  # base64 encoded "gcpqa"
---
apiVersion: v1
kind: Pod
metadata:
  name: dataqe-pod
spec:
  containers:
  - name: dataqe-container
    image: your-image:tag
    envFrom:
    - secretRef:
        name: dataqe-env
```

## MySQL Connector Usage

### Configuration Structure

**Local Execution (MYLOCAL)**:
```yaml
database:
  source:
    database_type: mysql
    mysql:
      host: localhost
      port: 3306
      user: root
      password: password
      database: ventana
```

**Kubernetes Execution (gcpqa|gcppreprod|gcpprod)**:
```yaml
database:
  source:
    database_type: mysql
    k8_db_details: project_ventana  # Format: project_name_database_name
```

### How It Works

**Local Execution (MYLOCAL)**:
- Configuration must include connection details directly in `mysql` section
- Credentials read from config file: `host`, `port`, `user`, `password`, `database`

**Kubernetes Execution (gcpqa|gcppreprod|gcpprod)**:
- Uses external configuration library (castlight_common_lib)
- Uses `k8_db_details` parameter in format: `project_name_database_name`
- Looks up: `config_details.data['mysql'][project][database_name]`
- Returns `db_host`, `db_port`, `db_user`, `db_password`, `db_name`

### Example Usage (Local)

```python
from dataqe_framework.connectors.mysql_connector import MySQLConnector

# Initialize connector with credentials
connector = MySQLConnector(
    host="localhost",
    port=3306,
    user="root",
    password="password",
    database="ventana"
)

# Connect and execute query
connector.connect()
results = connector.execute_query("SELECT * FROM your_table")
connector.close()
```

### Example Usage (Kubernetes)

```python
from dataqe_framework.connectors.mysql_connector import MySQLConnector

# Initialize connector with k8_db_details (will auto-fetch credentials)
connector = MySQLConnector(k8_db_details="project_ventana")

# Connect and execute query
connector.connect()
results = connector.execute_query("SELECT * FROM your_table")
connector.close()
```

### Using CredentialsExtractor

For Kubernetes deployments, use the credentials extractor:

```python
from dataqe_framework.credentials_extractor import CredentialsExtractor
from dataqe_framework.connectors.mysql_connector import MySQLConnector
import external_config_lib  # e.g., castlight_common_lib

# Load configuration based on SPRING_PROFILES_ACTIVE
profile = CredentialsExtractor.get_profile()
config = external_config_lib.Config('service_config_file', [profile])

# Extract MySQL credentials
mysql_creds = CredentialsExtractor.extract_mysql_config(config, 'ventana')

# Create connector with extracted credentials
connector = MySQLConnector(
    host=mysql_creds['host'],
    port=mysql_creds['port'],
    user=mysql_creds['user'],
    password=mysql_creds['password'],
    database=mysql_creds['database']
)

connector.connect()
results = connector.execute_query("SELECT * FROM your_table")
connector.close()
```

## BigQuery Connector Usage

### Configuration Structure

**Local Execution (MYLOCAL)**:
```yaml
database:
  source:
    database_type: gcpbq
    gcp:
      project_id: my-gcp-project
      dataset_id: source_dataset
      credentials_path: /path/to/credentials.json
      location: us-central1

  target:
    database_type: gcpbq
    gcp:
      project_id: my-gcp-project
      dataset_id: target_dataset
      credentials_path: /path/to/credentials.json
      location: us-central1
```

**Kubernetes Execution (gcpqa|gcppreprod|gcpprod)**:
```yaml
database:
  source:
    database_type: gcpbq
    gcp:
      k8_db_details: project_name_source_dataset  # Format: project_name_dataset_name
      location: us-central1

  target:
    database_type: gcpbq
    gcp:
      k8_db_details: project_name_target_dataset
      location: us-central1
```

### BigQuery Connector Initialization

```python
from dataqe_framework.connectors.bigquery_connector import BigQueryConnector

# Local development
config = {
    "project_id": "my-project",
    "dataset_id": "ventana",
    "credentials_path": "config/service_account.json",
    "location": "us-central1"
}

connector = BigQueryConnector(config)
connector.connect()
results = connector.execute_query("SELECT * FROM your_table")
connector.close()
```

### Using CredentialsExtractor for Kubernetes

```python
from dataqe_framework.credentials_extractor import CredentialsExtractor
from dataqe_framework.connectors.bigquery_connector import BigQueryConnector
import external_config_lib

# Get profile and load configuration
profile = CredentialsExtractor.get_profile()
config = external_config_lib.Config('service_config_file', [profile])

# Extract BigQuery configuration
bq_config = CredentialsExtractor.extract_bigquery_config(
    config,
    project_name='myproject',
    dataset_name='ventana'
)

# Extract and save service account credentials
sa_key = CredentialsExtractor.extract_service_account(
    config,
    'dataqe-sa'
)
credentials_path = CredentialsExtractor.save_service_account_json(
    sa_key,
    '/tmp/gcp_credentials.json'
)

# Create BigQuery connector
bq_config['credentials_path'] = credentials_path

connector = BigQueryConnector(bq_config)
connector.connect()
results = connector.execute_query("SELECT * FROM your_table")
connector.close()
```

### PHI Data Handling

The BigQuery connector automatically detects Protected Health Information (PHI) based on project_id:

- **PHI Projects**: Project ID contains `-h-` or `-p-`
  - Automatically applies KMS encryption
  - Requires proper KMS key configuration

- **Non-PHI Projects**: All other projects
  - Standard BigQuery connection

Example:

```python
config = {
    "project_id": "my-project-h-phi",  # Detected as PHI
    "dataset_id": "ventana",
    "use_encryption": True,  # Enable KMS encryption
    "kms_key_ring": "infra-default-cmek",
    "location": "us-central1",
    "infra_core": "infra-core-us-central1"
}

connector = BigQueryConnector(config)
connector.connect()  # Automatically applies KMS encryption
```

## Configuration File Structure

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
    project_id: my-project
    dataset_id: ventana
    credentials_path: ./config/service_account.json
    location: us-central1
```

### For Kubernetes (with external config library)

The framework expects the external configuration library (e.g., castlight_common_lib) to provide:

```python
config_details.data['mysql']['ventana'] = {
    'db_host': 'mysql.gcpqa.internal',
    'db_port': 3306,
    'db_user': 'database_user',
    'db_password': 'encrypted_password',
    'db_name': 'ventana'
}

config_details.data['bigquery']['myproject']['datasets']['ventana'] = {
    'project_id': 'my-project-qa',
    'location': 'us-central1'
}

config_details.data['gcp']['dataqe-sa'] = {
    # Full service account JSON
    'type': 'service_account',
    'project_id': 'my-project-qa',
    'private_key_id': '...',
    # ... rest of service account JSON
}
```

## Logging

Both connectors provide detailed logging for troubleshooting:

```
MySQLConnector - INFO - 2024-01-15 10:30:45 - MySQLConnector initialized for host=localhost, database=ventana
MySQLConnector - INFO - 2024-01-15 10:30:46 - Establishing MySQL connection to localhost:3306/ventana
MySQLConnector - INFO - 2024-01-15 10:30:46 - MySQL connection established successfully
MySQLConnector - INFO - 2024-01-15 10:30:47 - Query executed successfully, returned 42 rows

BigQueryConnector - INFO - 2024-01-15 10:31:00 - BigQuery connection established (with encryption)
BigQueryConnector - INFO - 2024-01-15 10:31:01 - KMS encryption configured for PHI data: projects/my-project-h/locations/us-central1/keyRings/infra-core-us-central1/cryptoKeys/infra-default-cmek
```

## Best Practices

### 1. Environment Separation

Keep separate configuration for each environment:
- Use SPRING_PROFILES_ACTIVE to select correct environment
- Never hardcode environment-specific values

### 2. Credential Security

- Always use external configuration library for Kubernetes
- Restrict file permissions on credential files (0o600)
- Use Kubernetes Secrets for sensitive environment variables
- Regularly rotate service account credentials

### 3. Error Handling

```python
from dataqe_framework.connectors.mysql_connector import MySQLConnector

try:
    connector = MySQLConnector(...)
    connector.connect()
    results = connector.execute_query(query)
except Exception as e:
    logger.error(f"Database operation failed: {e}")
    # Handle error appropriately
finally:
    connector.close()
```

### 4. Testing

```bash
# Test local configuration
export SPRING_PROFILES_ACTIVE='MYLOCAL'
python -m pytest tests/

# Verify Kubernetes deployment
kubectl logs -f pod/dataqe-pod | grep -i "profile"
```

### 5. Validation

Always validate configuration before using connectors:

```python
from dataqe_framework.credentials_extractor import CredentialsExtractor

try:
    profile = CredentialsExtractor.get_profile()
    mysql_creds = CredentialsExtractor.extract_mysql_config(config, 'ventana')

    # Verify required fields
    assert mysql_creds['host']
    assert mysql_creds['user']
    assert mysql_creds['password']

    print(f"Configuration valid for profile: {profile}")
except Exception as e:
    print(f"Configuration validation failed: {e}")
    exit(1)
```

## Troubleshooting

### Issue: "Execution profile: mylocal" but Kubernetes credentials expected

**Cause**: SPRING_PROFILES_ACTIVE not set or has wrong value

**Solution**:
```bash
# Check current value
echo $SPRING_PROFILES_ACTIVE

# Set correct value
export SPRING_PROFILES_ACTIVE='gcpqa'
```

### Issue: "MySQL configuration not found for database"

**Cause**: Database name not in configuration

**Solution**:
1. Verify database name matches configuration
2. Check external configuration library has correct structure
3. Verify SPRING_PROFILES_ACTIVE matches loaded profile

### Issue: "KMS encryption configured for PHI data: ... Error"

**Cause**: KMS key doesn't exist or service account lacks permissions

**Solution**:
1. Verify KMS key exists in GCP project
2. Check service account has `cloudkms.cryptoKeyVersions.useToEncrypt` permission
3. Verify location and infra-core values match KMS key

## Migration Checklist

- [ ] Update YAML configurations with proper database details
- [ ] Set up external configuration library (castlight_common_lib)
- [ ] Test locally with SPRING_PROFILES_ACTIVE=MYLOCAL
- [ ] Configure castlight_common_lib for gcpqa profile
- [ ] Test Kubernetes deployment in QA environment
- [ ] Verify logs show correct profile being used
- [ ] Configure castlight_common_lib for gcppreprod profile
- [ ] Test Pre-Production deployment
- [ ] Configure castlight_common_lib for gcpprod profile
- [ ] Deploy to Production

## Additional Resources

- [Google Cloud KMS Documentation](https://cloud.google.com/kms/docs)
- [BigQuery Encryption Documentation](https://cloud.google.com/bigquery/docs/customer-managed-encryption)
- [Kubernetes ConfigMap Reference](https://kubernetes.io/docs/concepts/configuration/configmap/)
- [Kubernetes Secrets Reference](https://kubernetes.io/docs/concepts/configuration/secret/)
