# DataQE Framework Enhancements Summary

## Version 0.2.7 - Multi-Block Configuration Support (Latest)

### Overview

The DataQE Framework now supports executing multiple configuration blocks in a single run. This major enhancement allows you to define different database validation scenarios in one config file and execute them flexibly.

### What's New

#### Multi-Block Configuration
Execute different validation configurations without creating separate config files:

```yaml
config_block_qa_validation:
  source: {...}
  target: {...}
  other: {...}

config_block_prod_validation:
  source: {...}
  target: {...}
  other: {...}
```

#### New CLI Options
- **No block option (default)**: Execute first block found
  ```bash
  dataqe-run --config config.yml
  ```

- **`--block NAME`**: Execute specific block
  ```bash
  dataqe-run --config config.yml --block prod_validation
  ```

- **`--all-blocks`**: Execute all blocks sequentially
  ```bash
  dataqe-run --config config.yml --all-blocks
  ```

#### New Functions in cli.py

**`is_valid_block(block_config)`**
```python
def is_valid_block(block_config):
    """
    Check if a configuration block has the required structure.

    A valid block must have 'source', 'target', and 'other' keys that are all dicts.
    """
    if not isinstance(block_config, dict):
        return False

    return (
        "source" in block_config and isinstance(block_config["source"], dict) and
        "target" in block_config and isinstance(block_config["target"], dict) and
        "other" in block_config and isinstance(block_config["other"], dict)
    )
```

**`get_all_blocks(full_config)`**
```python
def get_all_blocks(full_config: dict) -> dict:
    """
    Extract all valid configuration blocks from the config.

    A block is any top-level key whose value is a valid block config.
    Blocks are returned in their original order.
    """
    blocks = {}
    for key, value in full_config.items():
        if is_valid_block(value):
            blocks[key] = value
    return blocks
```

**`find_block(full_config, block_name)`**
```python
def find_block(full_config: dict, block_name: str) -> tuple:
    """
    Find a specific configuration block by name.

    Returns:
        tuple: (block_name, block_config)
    """
    if block_name not in full_config:
        available_blocks = list(get_all_blocks(full_config).keys())
        raise ValueError(
            f"Block '{block_name}' not found.\n"
            f"Available blocks: {', '.join(available_blocks) if available_blocks else 'None'}"
        )
    # ... validation logic
```

**`get_first_block(full_config)`**
```python
def get_first_block(full_config: dict) -> tuple:
    """
    Get the first valid configuration block (for backward compatibility).
    """
    blocks = get_all_blocks(full_config)
    if not blocks:
        raise ValueError(
            "No valid configuration blocks found in config file.\n"
            "A valid block must have 'source', 'target', and 'other' keys."
        )

    first_name = next(iter(blocks.keys()))
    return (first_name, blocks[first_name])
```

**`execute_block(block_name, block_config, config_path, output_dir)`**
```python
def execute_block(block_name: str, block_config: dict, config_path: str, output_dir: str) -> list:
    """
    Execute a single configuration block.

    Returns:
        list: List of test results from the executor
    """
    # ... block execution logic
```

#### Enhanced main() Function

The main CLI handler now:
1. Creates a mutually exclusive group for block selection
2. Determines which blocks to execute based on arguments
3. Iterates through blocks executing each one
4. Aggregates results across all blocks
5. Generates single combined report

```python
# Determine which blocks to execute
blocks_to_execute = []

if args.block:
    # Execute specific block
    block_name, block_config = find_block(full_config, args.block)
    blocks_to_execute = [(block_name, block_config)]

elif args.all_blocks:
    # Execute all blocks
    all_blocks = get_all_blocks(full_config)
    blocks_to_execute = list(all_blocks.items())

else:
    # Execute first block (backward compatibility)
    block_name, block_config = get_first_block(full_config)
    blocks_to_execute = [(block_name, block_config)]

# Execute all selected blocks
all_results = []
for block_name, block_config in blocks_to_execute:
    results = execute_block(block_name, block_config, args.config, output_dir)
    all_results.extend(results)
```

#### Enhanced executor.py

The executor now tracks which block a test belongs to:

```python
# In execute_block function
for result in results:
    result["block_name"] = block_name
```

### Files Modified

**src/dataqe_framework/cli.py**
- Added `is_valid_block()` function
- Added `get_all_blocks()` function
- Added `find_block()` function
- Added `get_first_block()` function
- Added `execute_block()` function
- Enhanced `main()` function with block selection logic
- Added `--block` and `--all-blocks` arguments to argument parser
- Updated logging to show block execution context

**src/dataqe_framework/executor.py**
- Added block name tracking to test results
- Block name included in each test result for reference

**pyproject.toml**
- Version bumped to 0.2.7

### Backward Compatibility

✅ **Fully backward compatible** - existing configurations work without changes:
- Single-block configs execute the first block by default
- All existing scripts continue to work
- No breaking changes to configuration structure

### Use Cases

1. **Multi-Environment Testing**: Validate the same application across QA, Staging, and Production in one config file
2. **Progressive Validation**: Define minimal to comprehensive validation blocks
3. **CI/CD Pipelines**: Select blocks based on deployment environment
4. **Release Testing**: Validate multiple data sources in parallel execution

### Benefits

- 📦 **Single Config File**: Manage multiple validation scenarios in one place
- 🔄 **Flexible Execution**: Run specific blocks or all blocks as needed
- 📊 **Consolidated Reports**: Aggregate results from all blocks
- ✅ **Backward Compatible**: Existing configurations work unchanged
- 🎯 **Clear Block Identification**: Block names appear in logs and results

---

## Version 0.2.5+ - Overview

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

## Version 0.2.5 - Automatic Query Preprocessor Enhancement

### What's New

An enhanced preprocessor feature that automatically replaces ALL release label placeholders in queries without requiring per-test configuration.

**File**: `src/dataqe_framework/preprocessor.py`

#### Key Methods Added:

1. **`replace_release_labels(query, connector)`**
   - Automatically replaces all `SOURCE_CURR_WEEK` and `SOURCE_PREV_WEEK` placeholders
   - No need to specify `source_name` per test
   - Caches results to avoid redundant queries

2. **`_replace_all_release_labels(query, release_labels)`**
   - Iterates through all release labels
   - Performs string replacements for all sources in one pass

#### Configuration Changes:

**Before (v0.2.4)**: Per-test configuration needed
```yaml
source:
  query: SELECT COUNT(*) FROM BCBSA_CURR_WEEK.users
  config_query_key: gcp_pd_prcd_conf      # Per test
  source_name: bcbsa                       # Per test
```

**After (v0.2.5)**: Config-level configuration only
```yaml
source:
  database_type: gcpbq
  gcp:
    config_query_key: gcp_pd_prcd_conf1    # In database config

target:
  database_type: gcpbq
  gcp:
    config_query_key: gcp_pd_prcd_conf2    # In database config

# Test queries only have placeholders, no config needed
```

#### How It Works:

1. Reads `config_query_key` from source and target database configs
2. Executes each query once at test initialization (results cached)
3. Automatically replaces ALL placeholders in ALL test queries
4. Each source/target can use different preprocessor queries

#### Benefits:

- ✅ Cleaner test YAML files (no per-test metadata)
- ✅ Different release mappings for source vs target
- ✅ Automatic replacement for all placeholders
- ✅ Cached results for performance
- ✅ Single test suite works with any release configuration

#### See Also:

- `PREPROCESSOR.md` - Updated with new approach
- `CONFIGURATION.md` - Updated examples

## Next Steps

1. Review the changes in the framework
2. Read `PREPROCESSOR.md` for updated preprocessor documentation
3. Read `CONFIGURATION.md` for updated config examples
4. Update your config files to place `config_query_key` in database-specific sections
5. Simplify your test YAML files by removing per-test preprocessor metadata
6. Test locally with SPRING_PROFILES_ACTIVE=MYLOCAL
7. Deploy to Kubernetes environments (QA, Pre-Prod, Prod)
