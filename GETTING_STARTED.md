# Getting Started with DataQE Framework

Quick start guide to set up and run your first data quality validation.

## Prerequisites

- Python 3.8 or higher
- pip package manager
- Access to source and target databases
- (For BigQuery) Service account JSON credentials file

## Installation

### 1. Clone the Repository

```bash
git clone <repository-url>
cd dataqe-framework
```

### 2. Create Virtual Environment

```bash
# Create virtual environment
python -m venv venv

# Activate it
# On macOS/Linux:
source venv/bin/activate

# On Windows:
venv\Scripts\activate
```

### 3. Install Dependencies

```bash
pip install -e .
```

This installs:
- `mysql-connector-python` - MySQL database support
- `google-cloud-bigquery` - BigQuery support
- `pyyaml` - YAML parsing
- `jinja2` - Report generation

### 4. Verify Installation

```bash
dataqe-run --help
```

You should see the help message with available options.

## 5-Minute Quick Start

### Step 1: Create Configuration File

Create a file named `simple_config.yml`:

```yaml
config_block_demo:
  source:
    database_type: mysql
    mysql:
      host: mysql.example.com
      port: 3306
      user: username
      password: password
      database: source_db

  target:
    database_type: mysql
    mysql:
      host: mysql-backup.example.com
      port: 3306
      user: username
      password: password
      database: target_db

  other:
    validation_script: simple_tests.yml
```

### Step 2: Create Test Suite

Create a file named `simple_tests.yml`:

```yaml
- test_users_count:
    severity: critical
    source:
      query: SELECT COUNT(*) as value FROM users

    target:
      query: SELECT COUNT(*) as value FROM users

    comparisons:
      comment: "User count must match"

- test_active_users:
    severity: high
    source:
      query: SELECT COUNT(*) as value FROM users WHERE status = 'active'

    target:
      query: SELECT COUNT(*) as value FROM users WHERE status = 'active'

    comparisons:
      comment: "Active users must match"
```

### Step 3: Run Validation

```bash
dataqe-run --config simple_config.yml
```

### Step 4: Review Results

Open the generated reports:

```bash
# View detailed report
open output/ExecutionReport.html

# View summary report
open output/FailedExecutionReport.html

# View CSV data
cat output/ExecutionReport.csv
```

## Detailed Setup Examples

### Example 1: MySQL to BigQuery Migration Validation

**Scenario**: Validate data migrated from MySQL to BigQuery

**File: mysql_to_bq_config.yml**
```yaml
config_block_migration:
  source:
    database_type: mysql
    mysql:
      host: prod-mysql.example.com
      port: 3306
      user: migrate_user
      password: ${MYSQL_PASSWORD}
      database: production

  target:
    database_type: gcpbq
    gcp:
      project_id: my-gcp-project
      dataset_id: migrated_data
      credentials_path: /path/to/service-account.json
      location: us-central1

  other:
    validation_script: migration_tests.yml
```

**File: migration_tests.yml**
```yaml
- table1_row_count:
    severity: critical
    source:
      query: SELECT COUNT(*) as value FROM table1

    target:
      query: SELECT COUNT(*) as value FROM `my-gcp-project.migrated_data.table1`

    comparisons:
      comment: "Row counts must match exactly"

- table1_unique_ids:
    severity: critical
    source:
      query: SELECT COUNT(DISTINCT id) as value FROM table1

    target:
      query: SELECT COUNT(DISTINCT id) as value FROM `my-gcp-project.migrated_data.table1`

    comparisons:
      comment: "Unique IDs must match"
```

**Run validation**:
```bash
export MYSQL_PASSWORD="your-password"
dataqe-run --config mysql_to_bq_config.yml
```

### Example 2: Multi-Release Validation with Dynamic Replacement

**Scenario**: Validate current and previous release datasets

**File: release_config.yml**
```yaml
config_block_releases:
  source:
    database_type: gcpbq
    gcp:
      project_id: analytics-project
      dataset_id: staging
      credentials_path: /path/to/service-account.json
    config_query_key: get_release_info
    source_name: sales_data

  target:
    database_type: gcpbq
    gcp:
      project_id: analytics-project
      dataset_id: production
      credentials_path: /path/to/service-account.json
    config_query_key: get_release_info
    source_name: sales_data

  other:
    validation_script: release_tests.yml
    preprocessor_queries: release_mappings.yml
```

**File: release_mappings.yml**
```yaml
get_release_info: |
  SELECT
    'sales_data' as source,
    'sales_export_v2' as current_release,
    'sales_export_v1' as previous_release
```

**File: release_tests.yml**
```yaml
- current_release_validation:
    severity: critical
    source:
      query: |
        SELECT COUNT(*) as value FROM SALES_DATA_CURR_WEEK.transactions
      config_query_key: get_release_info
      source_name: sales_data

    target:
      query: |
        SELECT COUNT(*) as value FROM SALES_DATA_CURR_WEEK.transactions
      config_query_key: get_release_info
      source_name: sales_data

    comparisons:
      comment: "Current release must match"

- previous_release_validation:
    severity: high
    source:
      query: |
        SELECT COUNT(*) as value FROM SALES_DATA_PREV_WEEK.transactions
      config_query_key: get_release_info
      source_name: sales_data

    target:
      query: |
        SELECT COUNT(*) as value FROM SALES_DATA_PREV_WEEK.transactions
      config_query_key: get_release_info
      source_name: sales_data

    comparisons:
      comment: "Previous release must match"
```

**Run validation**:
```bash
dataqe-run --config release_config.yml
```

### Example 3: Threshold-Based Validation

**Scenario**: Allow for acceptable variations in aggregated data

**File: threshold_config.yml**
```yaml
config_block_aggregation:
  source:
    database_type: mysql
    mysql:
      host: source.example.com
      port: 3306
      user: reader
      password: ${DB_PASSWORD}
      database: analytics

  target:
    database_type: gcpbq
    gcp:
      project_id: my-bq-project
      dataset_id: analytics
      credentials_path: /path/to/credentials.json

  other:
    validation_script: threshold_tests.yml
```

**File: threshold_tests.yml**
```yaml
- revenue_by_region:
    severity: high
    source:
      query: |
        SELECT SUM(revenue) as value
        FROM sales
        GROUP BY region
        ORDER BY region

    target:
      query: |
        SELECT SUM(revenue) as value
        FROM `my-bq-project.analytics.sales`
        GROUP BY region
        ORDER BY region

    comparisons:
      threshold:
        value: percentage
        limit: 5
      comment: "Revenue within 5% is acceptable"

- product_counts:
    severity: medium
    source:
      query: |
        SELECT COUNT(*) as value FROM products WHERE active = 1

    target:
      query: |
        SELECT COUNT(*) as value FROM `my-bq-project.analytics.products`
        WHERE active = true

    comparisons:
      threshold:
        value: absolute
        limit: 100
      comment: "Allow up to 100 difference in product counts"
```

**Run validation**:
```bash
export DB_PASSWORD="your-password"
dataqe-run --config threshold_config.yml
```

## Common Patterns

### Pattern 1: Source Validation Only

Test source data without target:

```yaml
- check_data_freshness:
    severity: medium
    source:
      query: |
        SELECT COUNT(*) as value
        FROM users
        WHERE last_updated >= CURRENT_DATE()

    comparisons:
      expected: ">=100"
      comment: "At least 100 users updated today"
```

### Pattern 2: Multiple Thresholds

Test multiple conditions in one validation:

```yaml
- comprehensive_check:
    severity: critical
    source:
      query: SELECT COUNT(*) as value FROM transactions

    target:
      query: SELECT COUNT(*) as value FROM transactions

    comparisons:
      threshold:
        value: percentage
        limit: 2
      comment: "2% tolerance for transaction counts"
```

### Pattern 3: Aggregated Data Comparison

Compare aggregated values:

```yaml
- daily_revenue:
    severity: high
    source:
      query: |
        SELECT SUM(amount) as value
        FROM transactions
        WHERE DATE(created_at) = CURRENT_DATE()

    target:
      query: |
        SELECT SUM(amount) as value
        FROM transactions
        WHERE DATE(created_at) = CURRENT_DATE()

    comparisons:
      threshold:
        value: percentage
        limit: 1
      comment: "Daily revenue within 1%"
```

## Environment Setup for CI/CD

### Jenkins

```groovy
pipeline {
    agent any

    environment {
        MYSQL_PASSWORD = credentials('mysql-password')
        GCP_CREDENTIALS = credentials('gcp-sa-credentials')
        DATAQE_OUTPUT_DIR = "${WORKSPACE}/quality-reports"
        DATAQE_APP_NAME = "my-app"
        DATAQE_BRANCH = "${GIT_BRANCH}"
        DATAQE_PLATFORM = "kubernetes"
        DATAQE_OWNER = "data-team"
    }

    stages {
        stage('Run Data Quality Validation') {
            steps {
                sh 'dataqe-run --config config.yml'
            }
        }

        stage('Archive Results') {
            steps {
                publishHTML([
                    reportDir: 'quality-reports',
                    reportFiles: 'ExecutionReport.html',
                    reportName: 'Data Quality Report'
                ])
            }
        }
    }
}
```

### GitHub Actions

```yaml
name: Data Quality Validation

on: [push, pull_request]

jobs:
  validate:
    runs-on: ubuntu-latest

    steps:
      - uses: actions/checkout@v2

      - name: Set up Python
        uses: actions/setup-python@v2
        with:
          python-version: '3.9'

      - name: Install dependencies
        run: pip install -e .

      - name: Run validation
        env:
          MYSQL_PASSWORD: ${{ secrets.MYSQL_PASSWORD }}
          GCP_CREDENTIALS: ${{ secrets.GCP_CREDENTIALS }}
          DATAQE_APP_NAME: ${{ github.repository }}
          DATAQE_BRANCH: ${{ github.ref }}
          DATAQE_PLATFORM: github-actions
          DATAQE_OWNER: data-team
        run: dataqe-run --config config.yml

      - name: Upload report
        uses: actions/upload-artifact@v2
        with:
          name: quality-reports
          path: output/
```

## Troubleshooting

### Issue: "Database connection refused"

**Solution**:
1. Check database host/port is correct
2. Verify firewall rules allow connection
3. Test connection manually: `mysql -h <host> -u <user> -p`

### Issue: "Config file not found"

**Solution**:
1. Use absolute path: `dataqe-run --config /full/path/config.yml`
2. Check file permissions: `ls -l config.yml`

### Issue: "Permission denied" on credentials file

**Solution**:
```bash
chmod 600 /path/to/credentials.json
```

### Issue: "BigQuery authentication failed"

**Solution**:
1. Verify credentials file path
2. Check service account has BigQuery permissions
3. Verify project_id matches credentials file

### Issue: "Query timeout"

**Solution**:
1. Optimize query performance
2. Add WHERE conditions to limit rows
3. Run during off-peak hours
4. Check database load

## Next Steps

1. **Read Configuration Guide**: [CONFIGURATION.md](CONFIGURATION.md)
2. **Learn About Preprocessor**: [PREPROCESSOR.md](PREPROCESSOR.md)
3. **Understand Architecture**: [ARCHITECTURE.md](ARCHITECTURE.md)
4. **Check Examples**: See `example_preprocessor_*.yml` files

## Getting Help

- Check error messages in console output
- Review logs in `./output/` directory
- Read error messages carefully (they provide context)
- Verify config file syntax with YAML validator
- Test queries directly in source/target databases

## Best Practices

1. **Start simple**: Create minimal config and test suite first
2. **Test connections**: Verify database access before full validation
3. **Use read-only accounts**: Limit credentials to SELECT only
4. **Version control**: Commit config files (not credentials)
5. **Document tests**: Add clear comments in test suites
6. **Monitor timing**: Check execution time metrics
7. **Review reports**: Always check generated reports for unexpected results
