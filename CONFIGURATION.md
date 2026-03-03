# Configuration Guide

Complete reference for configuring the DataQE Framework.

## Multi-Block Configuration

The DataQE Framework supports multiple configuration blocks in a single config file, allowing you to validate different environments or database pairs without creating separate configuration files.

### What is a Block?

A configuration block is a complete validation setup consisting of:
- A source database configuration
- A target database configuration
- Validation script and other settings

### How Blocks Are Identified

Blocks must be named with the `config_block_` prefix:

```yaml
config_block_mysql_to_bq:          # Valid block
config_block_prod_validation:       # Valid block
config_block_qa_testing:            # Valid block
source_config:                      # Invalid block (not recognized)
```

Only top-level keys starting with `config_block_` are recognized as configuration blocks.

### Execution Modes

#### 1. Single Block (Default - Backward Compatible)
If no block options are specified, the framework executes the **first valid block** found:
```bash
dataqe-run --config config.yml
```

#### 2. Specific Block
Execute a particular block by its name:
```bash
dataqe-run --config config.yml --block qa_validation
# Executes only the "config_block_qa_validation" block
```

#### 3. All Blocks
Execute all valid blocks sequentially:
```bash
dataqe-run --config config.yml --all-blocks
# Executes all config_block_* blocks in order
```

### Block Validation Rules

A valid configuration block must contain:
- `source`: A dictionary with database configuration
- `target`: A dictionary with database configuration
- `other`: A dictionary with validation settings

**Example of Valid Block:**
```yaml
config_block_example:
  source:
    database_type: mysql
    mysql:
      host: localhost
      port: 3306
      user: root
      password: password
      database: test_db
  target:
    database_type: gcpbq
    gcp:
      project_id: my-project
      dataset_id: test_dataset
      credentials_path: /path/to/creds.json
  other:
    validation_script: tests/test_suite.yml
```

**Invalid blocks** (incomplete or malformed) are automatically skipped with a warning message.

### Multi-Block Example

Create a single config file with multiple blocks for different environments:

```yaml
# QA Environment Validation
config_block_qa_validation:
  source:
    database_type: mysql
    mysql:
      host: qa-mysql.internal
      port: 3306
      user: qa_user
      password: qa_password
      database: qa_database

  target:
    database_type: gcpbq
    gcp:
      project_id: my-project-qa
      dataset_id: qa_dataset
      credentials_path: /secrets/qa-creds.json

  other:
    validation_script: tests/qa_tests.yml
    preprocessor_queries: config/preprocessor.yml

# Production Environment Validation
config_block_prod_validation:
  source:
    database_type: mysql
    mysql:
      host: prod-mysql.internal
      port: 3306
      user: prod_user
      password: prod_password
      database: prod_database

  target:
    database_type: gcpbq
    gcp:
      project_id: my-project-prod
      dataset_id: prod_dataset
      credentials_path: /secrets/prod-creds.json

  other:
    validation_script: tests/prod_tests.yml
    preprocessor_queries: config/preprocessor.yml

# Staging Environment Validation
config_block_staging_validation:
  source:
    database_type: mysql
    mysql:
      host: staging-mysql.internal
      port: 3306
      user: staging_user
      password: staging_password
      database: staging_database

  target:
    database_type: gcpbq
    gcp:
      project_id: my-project-staging
      dataset_id: staging_dataset
      credentials_path: /secrets/staging-creds.json

  other:
    validation_script: tests/staging_tests.yml
    preprocessor_queries: config/preprocessor.yml
```

### Execution Examples

```bash
# Execute first block only (QA)
dataqe-run --config config.yml
# Output: "Executing first block: qa_validation"

# Execute specific block (Production)
dataqe-run --config config.yml --block prod_validation
# Output: "Executing block: prod_validation"

# Execute all blocks sequentially
dataqe-run --config config.yml --all-blocks
# Output: "Executing 3 blocks: qa_validation, prod_validation, staging_validation"
```

### Report Generation

When executing multiple blocks:
- A **single ExecutionReport.html** is generated containing results from all blocks
- Test names include block context for clarity
- Summary statistics aggregate across all blocks
- Each test result includes the block_name field for reference

## Configuration File Structure

Configuration files are YAML-based with the following structure:

```yaml
config_block_<unique_name>:
  source:
    # Source database configuration
  target:
    # Target database configuration
  other:
    # Other settings like validation script path
```

## Config Block Naming

The config block name must start with `config_block_` and can be any unique identifier:

```yaml
config_block_mysql_to_bq:
config_block_prod_validation:
config_block_migration_v2:
```

## Database Configuration

### MySQL Configuration

**Local Development**:
```yaml
source:
  database_type: mysql
  mysql:
    host: database.example.com
    port: 3306
    user: db_user
    password: db_password
    database: production_db
```

**Kubernetes Deployment**:
```yaml
source:
  database_type: mysql
  mysql:
    k8_db_details: project_name_database_name
```

**Parameters**:
- `host` (required for local): MySQL server hostname or IP
- `port` (optional for local): MySQL port, default is 3306
- `user` (required for local): Database username
- `password` (required for local): Database password
- `database` (required for local): Database name to connect to
- `k8_db_details` (required for Kubernetes): Format `project_name_database_name` to fetch credentials from external configuration

**Connection Notes**:
- Ensure the user has SELECT permissions on all required tables
- For production environments, use dedicated read-only accounts
- Test connection before using in tests
- For Kubernetes, use `k8_db_details` to retrieve credentials from `castlight_common_lib`

### Google BigQuery Configuration

**Local Development**:
```yaml
target:
  database_type: gcpbq
  gcp:
    project_id: my-gcp-project
    dataset_id: my_dataset
    credentials_path: /path/to/service-account.json
    location: us-central1
    use_encryption: false
```

**Kubernetes Deployment**:
```yaml
target:
  database_type: gcpbq
  gcp:
    k8_db_details: project_name_dataset_name
```

**Core Parameters (Local)**:
- `project_id` (required): GCP Project ID
- `dataset_id` (required): BigQuery dataset name
- `credentials_path` (required): Path to service account JSON file

**Core Parameters (Kubernetes)**:
- `k8_db_details` (required): Format `project_name_dataset_name` to fetch credentials from external configuration

**Advanced Parameters**:
- `location` (optional): BigQuery location, default is `us-central1`
- `use_encryption` (optional): Enable KMS encryption for PHI data, default is `false`

#### Credential File

The service account JSON file must have BigQuery permissions:

```json
{
  "type": "service_account",
  "project_id": "my-project",
  "private_key_id": "key_id",
  "private_key": "-----BEGIN PRIVATE KEY-----\n...\n-----END PRIVATE KEY-----\n",
  "client_email": "sa@my-project.iam.gserviceaccount.com",
  "client_id": "123456789",
  "auth_uri": "https://accounts.google.com/o/oauth2/auth",
  "token_uri": "https://oauth2.googleapis.com/token",
  "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
  "client_x509_cert_url": "https://www.googleapis.com/robot/v1/metadata/x509/sa%40my-project.iam.gserviceaccount.com"
}
```

**Required Permissions**:
- `bigquery.datasets.get`
- `bigquery.datasets.update`
- `bigquery.tables.get`
- `bigquery.tables.create`
- `bigquery.tables.delete`
- `bigquery.jobs.create`
- `bigquery.jobs.get`
- `bigquery.jobs.listAll`

#### KMS Encryption (PHI Data)

For datasets containing Protected Health Information (PHI):

```yaml
gcp:
  project_id: my-project
  dataset_id: phi_data
  credentials_path: /path/to/credentials.json
  use_encryption: true
  location: us-central1
  kms_key_ring: infra-default-cmek
  infra_core: infra-core-us-central1
```

**PHI Requirements**:
- Project ID must contain `-h-` (PHI indicator)
- KMS key ring must be configured
- Infra core name must be set

## Test Configuration

### Validation Script Path

Point to your YAML test suite file:

```yaml
other:
  validation_script: /path/to/test_suite.yml
```

**Path Options**:
- **Absolute path**: `/Users/user/tests/test_suite.yml`
- **Relative path**: `test_suite.yml` (relative to config file location)

### Preprocessor Queries Path

For dynamic dataset replacement, specify the preprocessor queries file:

```yaml
other:
  validation_script: test_suite.yml
  preprocessor_queries: preprocessor_queries.yml
```

**Path Options**:
- **Absolute path**: `/path/to/preprocessor_queries.yml`
- **Relative path**: `preprocessor_queries.yml` (relative to config file location)

## Dynamic Dataset Replacement

### When to Use

- Multiple environment-specific dataset names
- Release-based naming conventions (e.g., `BCBSA_CURR_WEEK`, `BCBSA_PREV_WEEK`)
- Data that changes based on deployment
- Different release versions for source vs target environments

### Configuration

Add `config_query_key` inside the database-specific config (gcp/mysql):

```yaml
source:
  database_type: gcpbq
  gcp:
    project_id: my-project
    dataset_id: source_dataset
    credentials_path: /path/to/credentials.json
    config_query_key: source_releases_query    # Add this

target:
  database_type: gcpbq
  gcp:
    project_id: my-project
    dataset_id: target_dataset
    credentials_path: /path/to/credentials.json
    config_query_key: target_releases_query    # Add this
```

**Parameters**:
- `config_query_key`: Key to look up in `preprocessor_queries.yml` (different keys can be used for source/target)

### Preprocessor Queries File

Create a separate YAML file with dataset mapping queries:

```yaml
# Query for source environment (e.g., staging)
source_releases_query: |
  SELECT source, current_release, previous_release
  FROM release_metadata
  WHERE environment = 'staging' AND is_active = TRUE

# Query for target environment (e.g., production)
target_releases_query: |
  SELECT source, current_release, previous_release
  FROM release_metadata
  WHERE environment = 'production' AND is_active = TRUE
```

**Query Requirements**:
- Must return `source` column (becomes the basis for placeholders)
- Must return `current_release` or `curr_release_label` column
- Must return `previous_release` or `prev_release_label` column

### How It Works

1. Framework reads `config_query_key` from source and target database configs
2. Executes each query once at test start (results are cached)
3. Automatically replaces ALL `SOURCE_CURR_WEEK` and `SOURCE_PREV_WEEK` placeholders in test queries
4. **No per-test configuration needed** - write tests once with placeholders, they work everywhere

### Placeholder Replacement

The framework replaces uppercase placeholder names:

```yaml
# In test query:
SELECT COUNT(*) FROM BCBSA_CURR_WEEK.users

# With preprocessor result where source='BCBSA' and current_release='bcbsa_export1':
SELECT COUNT(*) FROM bcbsa_export1.users
```

**Placeholder Format**:
- Current release: `{SOURCE_NAME}_CURR_WEEK`
- Previous release: `{SOURCE_NAME}_PREV_WEEK`

**Example Placeholders**:
- `ANTHEM_PF_CURR_WEEK` → replaced with current release value
- `BCBSA_PF_PREV_WEEK` → replaced with previous release value
- `PROVIDER_DIRECTORY_CURR_WEEK` → replaced with current release value

## Environment Variables

Override configuration defaults using environment variables:

### Output Directory
```bash
export DATAQE_OUTPUT_DIR=/custom/output/path
# Default: ./output
```

### CI/CD Metadata
```bash
export DATAQE_APP_NAME=my-application
export DATAQE_BRANCH=main
export DATAQE_PLATFORM=kubernetes
export DATAQE_OWNER=data-engineering-team
# Used in AutomationData.csv for CI/CD integration
```

## Configuration Examples

### Example 1: Simple MySQL to BigQuery (Local)

```yaml
config_block_prod_validation:
  source:
    database_type: mysql
    mysql:
      host: prod-mysql.example.com
      port: 3306
      user: readonly_user
      password: secure_password
      database: production

  target:
    database_type: gcpbq
    gcp:
      project_id: my-gcp-prod
      dataset_id: production_bq
      credentials_path: /etc/secrets/gcp-sa.json

  other:
    validation_script: tests/prod_validation.yml
```

### Example 1b: Simple MySQL to BigQuery (Kubernetes)

```yaml
config_block_prod_validation:
  source:
    database_type: mysql
    k8_db_details: prod_production

  target:
    database_type: gcpbq
    gcp:
      k8_db_details: prod_production_bq

  other:
    validation_script: tests/prod_validation.yml
```

### Example 2: With Dynamic Dataset Replacement (Different Source/Target Releases)

```yaml
config_block_release_validation:
  source:
    database_type: gcpbq
    gcp:
      project_id: my-project
      dataset_id: staging
      credentials_path: /path/to/credentials.json
      config_query_key: source_releases_query    # Staging releases

  target:
    database_type: gcpbq
    gcp:
      project_id: my-project
      dataset_id: production
      credentials_path: /path/to/credentials.json
      config_query_key: target_releases_query    # Production releases

  other:
    validation_script: tests/release_tests.yml
    preprocessor_queries: config/release_queries.yml
```

### Example 3: With PHI Data and Encryption

```yaml
config_block_phi_validation:
  source:
    database_type: gcpbq
    gcp:
      project_id: prj-eng-p-phi-bq-4a3c
      dataset_id: patient_data
      credentials_path: /secure/credentials.json
      use_encryption: true
      location: us-central1
      kms_key_ring: phi-cmek
      infra_core: infra-core-us-central1

  target:
    database_type: gcpbq
    gcp:
      project_id: prj-eng-p-phi-bq-4a3c
      dataset_id: patient_data_backup
      credentials_path: /secure/credentials.json
      use_encryption: true
      location: us-central1
      kms_key_ring: phi-cmek
      infra_core: infra-core-us-central1

  other:
    validation_script: tests/phi_tests.yml
```

## Validation

### Validate Configuration File

Manually check your configuration:

```bash
# Check YAML syntax
python -c "import yaml; yaml.safe_load(open('config.yml'))"

# Try loading configuration
dataqe-run --config config.yml
```

## Troubleshooting

### Configuration Not Found
```
FileNotFoundError: Config file not found: /path/to/config.yml
```
- Verify file path is correct
- Use absolute paths when possible
- Check file permissions

### Invalid YAML Syntax
```
yaml.scanner.ScannerError: ...
```
- Check indentation (use spaces, not tabs)
- Verify all quotes are properly closed
- Validate with YAML linter

### Database Connection Failed
- Test database connectivity separately
- Verify credentials are correct
- Check firewall rules for network access

### BigQuery Authentication Failed
- Verify credentials file exists and is readable
- Check service account has required permissions
- Ensure project_id matches credentials file

### Preprocessor Queries Not Found
```
Preprocessor queries file not found: /path/to/preprocessor_queries.yml
```
- Verify file path in `other.preprocessor_queries`
- Check file permissions
- Use absolute path if relative path doesn't work

## Best Practices

1. **Use relative paths** for validation_script and preprocessor_queries
2. **Store credentials** outside version control
3. **Use environment variables** for sensitive values
4. **Test configurations** before production use
5. **Document custom config blocks** with comments
6. **Version control** config files (except credentials)
7. **Use read-only database accounts** for validation
8. **Enable encryption** for PHI data
