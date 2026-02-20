# DataQE Framework - Data Quality and Equality Testing

A powerful Python framework for validating data quality and ensuring data consistency between source and target databases. Designed for data migration projects, ETL validation, and cross-database reconciliation.

**Version**: 0.0.1

## Overview

DataQE Framework enables organizations to:
- **Validate data migration quality** between different database systems
- **Ensure data consistency** across source and target environments
- **Run comprehensive test suites** with flexible comparison modes
- **Generate detailed reports** for compliance and audit trails
- **Support dynamic dataset replacement** for multi-release environments

## Key Features

### Multi-Database Support
- **MySQL** - Relational database validation
- **Google BigQuery** - Cloud data warehouse validation
- Extensible connector architecture for adding more databases

### Flexible Test Configuration
- YAML-based test definitions
- Single-source validation with expected conditions
- Source vs Target equality checks
- Threshold-based comparisons (percentage and absolute)
- Support for multiple test cases in a single execution

### Dynamic Dataset Replacement
- Replace dataset placeholders with actual release names
- Centralized configuration for dataset mappings
- Support for multiple sources with different release versions

### Comprehensive Reporting
- **ExecutionReport.html** - Full test results with detailed execution times
- **FailedExecutionReport.html** - Failed tests or confirmation of all tests passing
- **ExecutionReport.csv** - Structured test results for further analysis
- **AutomationData.csv** - CI/CD integration data
- Real-time console output with progress tracking

### Enterprise Features
- PHI data protection with KMS encryption support
- Detailed execution timing metrics
- Environment-based configuration
- Flexible credential management

## Installation

### Prerequisites
- Python 3.8+
- pip

### Install from Source

```bash
git clone <repository-url>
cd dataqe-framework
pip install -e .
```

### Verify Installation

```bash
dataqe-run --help
```

## Quick Start

### 1. Create Configuration File

Create `config.yml`:

```yaml
config_block_validation:
  source:
    database_type: mysql
    mysql:
      host: source-db.example.com
      port: 3306
      user: db_user
      password: db_password
      database: source_db

  target:
    database_type: gcpbq
    gcp:
      project_id: my-gcp-project
      dataset_id: target_dataset
      credentials_path: /path/to/credentials.json

  other:
    validation_script: test_suite.yml
    preprocessor_queries: preprocessor_queries.yml
```

### 2. Create Test Suite

Create `test_suite.yml`:

```yaml
- test_row_count:
    severity: critical
    source:
      query: |
        SELECT COUNT(*) as value FROM users
    target:
      query: |
        SELECT COUNT(*) as value FROM users
    comparisons:
      comment: "User count must match between source and target"

- test_with_threshold:
    severity: high
    source:
      query: |
        SELECT SUM(amount) as value FROM transactions
    target:
      query: |
        SELECT SUM(amount) as value FROM transactions
    comparisons:
      threshold:
        value: percentage
        limit: 1
      comment: "Transaction amounts must match within 1%"
```

### 3. Run Validation

```bash
dataqe-run --config config.yml
```

Check output directory for reports:
```
./output/ExecutionReport.html
./output/ExecutionReport.csv
./output/FailedExecutionReport.html
```

## Configuration

### Config Block Structure

```yaml
config_block_<name>:
  source:
    database_type: mysql|gcpbq
    mysql: {...}
    gcp: {...}
    config_query_key: optional_query_key
    source_name: optional_source_name

  target:
    database_type: mysql|gcpbq
    mysql: {...}
    gcp: {...}
    config_query_key: optional_query_key
    source_name: optional_source_name

  other:
    validation_script: path/to/test_suite.yml
    preprocessor_queries: path/to/preprocessor_queries.yml
```

### Database Configuration

#### MySQL
```yaml
mysql:
  host: hostname
  port: 3306
  user: username
  password: password
  database: database_name
```

#### Google BigQuery
```yaml
gcp:
  project_id: my-project
  dataset_id: my-dataset
  credentials_path: /path/to/service-account.json
  location: us-central1
  use_encryption: false
```

See [CONFIGURATION.md](CONFIGURATION.md) for detailed configuration options.

## Test Suite Definition

Each test case has the following structure:

```yaml
- test_name:
    severity: critical|high|medium|low

    source:
      query: |
        SELECT COUNT(*) as value FROM table
      config_query_key: optional_key
      source_name: optional_source_name

    target:
      query: |
        SELECT COUNT(*) as value FROM table
      config_query_key: optional_key
      source_name: optional_source_name

    comparisons:
      expected: optional_expected_value
      threshold:
        value: percentage|absolute
        limit: number
      comment: "Description of this test"
```

### Comparison Modes

#### 1. Source vs Target Equality
```yaml
comparisons:
  comment: "Values must match exactly"
```

#### 2. Expected Value Check
```yaml
comparisons:
  expected: ">=1000"
  comment: "Count must be at least 1000"
```

#### 3. Percentage Threshold
```yaml
comparisons:
  threshold:
    value: percentage
    limit: 5
  comment: "Target can vary up to 5% from source"
```

#### 4. Absolute Difference
```yaml
comparisons:
  threshold:
    value: absolute
    limit: 100
  comment: "Target can differ by max 100 units"
```

## Dynamic Dataset Replacement

Replace dataset placeholders with actual release names:

### 1. Create Preprocessor Queries File

Create `preprocessor_queries.yml`:

```yaml
get_releases: |
  SELECT source, current_release, previous_release
  FROM release_metadata
  WHERE is_active = TRUE

get_bcbsa_releases: |
  SELECT 'bcbsa' as source, 'bcbsa_export1' as current_release, 'bcbsa_export3' as previous_release
```

### 2. Update Configuration

Add to `config.yml`:

```yaml
other:
  validation_script: test_suite.yml
  preprocessor_queries: preprocessor_queries.yml
```

### 3. Update Test Suite

Use placeholders in queries and specify the preprocessor key:

```yaml
- test_current_release:
    source:
      query: |
        SELECT COUNT(*) as value FROM BCBSA_CURR_WEEK.users
      config_query_key: get_bcbsa_releases
      source_name: bcbsa
```

The framework will:
1. Execute `get_bcbsa_releases` query
2. Get current_release value (`bcbsa_export1`)
3. Replace `BCBSA_CURR_WEEK` → `bcbsa_export1`
4. Run the modified query

See [PREPROCESSOR.md](PREPROCESSOR.md) for detailed examples.

## Report Generation

### ExecutionReport.html
Full test execution report with:
- Test results (PASS/FAIL)
- Source and target values
- Execution timestamps
- Query execution times
- Comparison methods

### FailedExecutionReport.html
Summary of failed tests or confirmation of all tests passing

### ExecutionReport.csv
Structured test results for import into analysis tools:
- Test name
- Status
- Severity
- Source/Target values
- Execution time

### AutomationData.csv
CI/CD integration data:
- App name
- Branch
- Platform
- Owner
- Test report path

## Environment Variables

Configure the framework behavior using environment variables:

```bash
# Output directory for reports (default: ./output)
export DATAQE_OUTPUT_DIR=/path/to/output

# CI/CD metadata (used in AutomationData.csv)
export DATAQE_APP_NAME=my-app
export DATAQE_BRANCH=main
export DATAQE_PLATFORM=kubernetes
export DATAQE_OWNER=team-name
```

## Command Line Usage

### Basic Execution
```bash
dataqe-run --config /path/to/config.yml
```

### With Custom Output Directory
```bash
export DATAQE_OUTPUT_DIR=/custom/output
dataqe-run --config /path/to/config.yml
```

### CI/CD Integration
```bash
export DATAQE_APP_NAME=ecommerce-platform
export DATAQE_BRANCH=feature-branch
export DATAQE_PLATFORM=kubernetes
export DATAQE_OWNER=data-team

dataqe-run --config /path/to/config.yml
```

## Project Structure

```
dataqe-framework/
├── src/dataqe_framework/
│   ├── __init__.py
│   ├── cli.py                 # Command-line interface
│   ├── config_loader.py       # YAML config loading
│   ├── executor.py            # Test execution engine
│   ├── preprocessor.py        # Query preprocessing
│   ├── reporter.py            # Report generation
│   ├── comparison/
│   │   ├── comparator.py      # Comparison logic
│   │   └── threshold.py       # Threshold calculations
│   └── connectors/
│       ├── base_connector.py  # Base connector interface
│       ├── mysql_connector.py # MySQL implementation
│       └── bigquery_connector.py # BigQuery implementation
├── example_preprocessor_config.yml
├── example_preprocessor_queries.yml
├── example_preprocessor_test_script.yml
├── README.md
├── CONFIGURATION.md
├── PREPROCESSOR.md
└── pyproject.toml
```

## Examples

### Example 1: Simple Row Count Validation

Test if row counts match between MySQL and BigQuery:

```yaml
- users_row_count:
    severity: critical
    source:
      query: SELECT COUNT(*) as value FROM users
    target:
      query: SELECT COUNT(*) as value FROM users
    comparisons:
      comment: "User count must match exactly"
```

### Example 2: Multi-Release Dataset Validation

Validate current and previous release datasets:

```yaml
- current_release_sales:
    severity: high
    source:
      query: |
        SELECT SUM(amount) as value FROM BCBSA_CURR_WEEK.sales
      config_query_key: get_bcbsa_releases
      source_name: bcbsa

- previous_release_sales:
    severity: medium
    source:
      query: |
        SELECT SUM(amount) as value FROM BCBSA_PREV_WEEK.sales
      config_query_key: get_bcbsa_releases
      source_name: bcbsa
```

### Example 3: Threshold-Based Comparison

Allow data variations within acceptable ranges:

```yaml
- transaction_amounts:
    severity: high
    source:
      query: SELECT SUM(amount) as value FROM transactions
    target:
      query: SELECT SUM(amount) as value FROM transactions
    comparisons:
      threshold:
        value: percentage
        limit: 2
      comment: "Amounts must match within 2%"
```

## Troubleshooting

### Connection Issues

**MySQL Connection Refused**
```bash
# Check connectivity
mysql -h <host> -u <user> -p<password> <database>

# Verify in config.yml:
# - host is correct
# - port is 3306 (or custom port)
# - user/password are correct
```

**BigQuery Authentication Failed**
```bash
# Verify credentials file
gcloud auth application-default print-access-token

# Check in config.yml:
# - credentials_path points to valid service account JSON
# - credentials file has BigQuery permissions
```

### Query Execution Issues

**Query Timeout**
- Increase database timeout settings
- Optimize query performance
- Check database load

**Dataset Not Found**
- For preprocessor queries: verify `config_query_key` matches a key in `preprocessor_queries.yml`
- For dynamic replacement: verify placeholder format matches expected convention

### Report Generation Issues

**Output directory not writable**
```bash
chmod -R 755 ./output
```

**No output files generated**
- Check logs for errors
- Verify `DATAQE_OUTPUT_DIR` has write permissions
- Ensure test suite has valid queries

## Performance Considerations

- **Large result sets**: Memory usage scales with query result size
- **Many tests**: Execution time is cumulative
- **Database load**: Run during off-peak hours for production databases
- **Network latency**: BigQuery queries may take longer than MySQL

## Security

### Sensitive Data Handling
- Never commit credentials files
- Use environment variables for secrets
- Enable KMS encryption for PHI data in BigQuery

### Best Practices
- Use dedicated read-only database accounts
- Limit query timeout duration
- Monitor execution logs for suspicious patterns
- Review generated reports for sensitive data exposure

## Contributing

For bug reports and feature requests, please open an issue on the repository.

## Installation via pip

### From PyPI (Coming Soon)

```bash
pip install dataqe-framework
```

### From GitHub

```bash
pip install git+https://github.com/ShaikKhadarmohiddin/dataqe-framework.git
```

### From Source

```bash
git clone https://github.com/ShaikKhadarmohiddin/dataqe-framework.git
cd dataqe-framework
pip install -e .
```

## Author

**Khadar Shaik**
- Email: khadarmohiddin.shaik@apree.health
- GitHub: [@ShaikKhadarmohiddin](https://github.com/ShaikKhadarmohiddin)

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

MIT License - You are free to use this project for personal, educational, or commercial purposes.

## Support

For support and questions:
- Check documentation in the project repository
- Open an issue on [GitHub Issues](https://github.com/ShaikKhadarmohiddin/dataqe-framework/issues)
- Review troubleshooting section in [GETTING_STARTED.md](GETTING_STARTED.md)
- Consult test output and logs for error details

## Version History

### 0.0.1 (Initial Release)
- Multi-database support (MySQL, BigQuery)
- YAML-based test configuration
- Flexible comparison modes
- Dynamic dataset replacement
- Comprehensive reporting
- PHI data protection
- CI/CD integration support
