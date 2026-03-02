# Dynamic Dataset Replacement (Preprocessor Feature)

This guide explains how to use the dynamic dataset replacement feature for validating multiple releases or environment-specific datasets.

## Overview

The preprocessor feature allows you to:
- Replace dataset name placeholders with actual release names **automatically**
- Maintain single test suite for multiple data versions
- Support multi-release environments with different mappings per source/target
- Centralize dataset mapping configuration in the config file

## Use Cases

### Multi-Release Validation
Validate both current and previous release datasets without changing test queries:

```yaml
# Same test query works for both releases
SELECT COUNT(*) FROM BCBSA_CURR_WEEK.users    # Replaced with bcbsa_export1.users
SELECT COUNT(*) FROM BCBSA_PREV_WEEK.users    # Replaced with bcbsa_export3.users
```

### Environment-Specific Datasets
Handle different dataset names across environments:

```yaml
# Staging environment: data_staging_v1
# Production environment: data_prod_v1
# Test query works with both:
SELECT * FROM DATA_CURR_RELEASE.transactions
```

### Multiple Sources
Validate multiple data sources with different release conventions:

```yaml
BCBSA_CURR_WEEK → bcbsa_export1
BCBSA_PREV_WEEK → bcbsa_export3

PROVIDER_DIR_CURR_WEEK → provider_directory_v2
PROVIDER_DIR_PREV_WEEK → provider_directory_v1
```

### Different Preprocessor Configs for Source and Target
Use different dataset mappings for source vs target (e.g., different release versions):

```yaml
source:
  config_query_key: source_releases_query    # Uses current staging releases
target:
  config_query_key: target_releases_query    # Uses current production releases
```

## Configuration

### Step 1: Create Preprocessor Queries File

Create a YAML file with queries that return dataset mappings:

```yaml
# preprocessor_queries.yml

# For source environment
source_releases_query: |
  SELECT source, current_release, previous_release
  FROM release_metadata
  WHERE environment = 'staging' AND is_active = TRUE

# For target environment
target_releases_query: |
  SELECT source, current_release, previous_release
  FROM release_metadata
  WHERE environment = 'production' AND is_active = TRUE
```

### Step 2: Add Preprocessor Path and config_query_key to Config

```yaml
config_block_validation:
  source:
    database_type: gcpbq
    gcp:
      project_id: my-project
      dataset_id: source_dataset
      credentials_path: /path/to/credentials.json
      config_query_key: source_releases_query   # Add this

  target:
    database_type: gcpbq
    gcp:
      project_id: my-project
      dataset_id: target_dataset
      credentials_path: /path/to/credentials.json
      config_query_key: target_releases_query   # Add this

  other:
    validation_script: test_suite.yml
    preprocessor_queries: preprocessor_queries.yml
```

### Step 3: Write Test Queries with Placeholders

Test queries only need the placeholder names. No per-test configuration needed!

```yaml
- test_current_release:
    severity: critical
    source:
      query: |
        SELECT COUNT(*) as value FROM BCBSA_CURR_WEEK.users

    target:
      query: |
        SELECT COUNT(*) as value FROM BCBSA_CURR_WEEK.users

    comparisons:
      comment: "User count must match"
```

That's it! The framework automatically:
1. Executes the preprocessor queries from your config
2. Gets all release label mappings
3. Replaces placeholders in ALL test queries

## Execution Flow

```
┌─────────────────────────────────────┐
│ 1. Load Configuration File          │
│    - Source config_query_key        │
│    - Target config_query_key        │
│    - Preprocessor queries path      │
└─────────────────────────────────────┘
                  ↓
┌─────────────────────────────────────┐
│ 2. Load Test Suite                  │
│    - Test definitions with          │
│      placeholder names              │
│      (no per-test config)           │
└─────────────────────────────────────┘
                  ↓
┌─────────────────────────────────────┐
│ 3. Initialize Preprocessors         │
│    - Source: execute config_query   │
│    - Target: execute config_query   │
│    - Get ALL dataset mappings       │
│    - Cache results                  │
└─────────────────────────────────────┘
                  ↓
┌─────────────────────────────────────┐
│ 4. For Each Test Query              │
│    - Replace ALL SOURCE_CURR_WEEK   │
│    - Replace ALL SOURCE_PREV_WEEK   │
└─────────────────────────────────────┘
                  ↓
┌─────────────────────────────────────┐
│ 5. Execute Modified Query           │
│    - Run against actual dataset     │
│    - Collect results                │
└─────────────────────────────────────┘
                  ↓
┌─────────────────────────────────────┐
│ 6. Compare & Report                 │
│    - Compare source vs target       │
│    - Generate reports               │
└─────────────────────────────────────┘
```

## Placeholder Naming Conventions

The framework recognizes uppercase placeholders with the source name:

### Supported Format

```yaml
{SOURCE_NAME}_CURR_WEEK     # Current release placeholder
{SOURCE_NAME}_PREV_WEEK     # Previous release placeholder
```

### Examples

```yaml
# For source 'bcbsa' returned from preprocessor query
BCBSA_CURR_WEEK        # Replaced with current_release value
BCBSA_PREV_WEEK        # Replaced with previous_release value

# For source 'anthem_pf'
ANTHEM_PF_CURR_WEEK
ANTHEM_PF_PREV_WEEK

# For source 'provider_directory'
PROVIDER_DIRECTORY_CURR_WEEK
PROVIDER_DIRECTORY_PREV_WEEK

# For source 'bcbsa_pf'
BCBSA_PF_CURR_WEEK
BCBSA_PF_PREV_WEEK
```

**Important**: The placeholder source name must match (in uppercase) the `source` value returned by your preprocessor query.

## Query Result Format

Preprocessor queries must return rows with these columns:

```
┌──────────────────┬──────────────────┬──────────────────┐
│ source           │ current_release  │ previous_release │
├──────────────────┼──────────────────┼──────────────────┤
│ bcbsa            │ bcbsa_export1    │ bcbsa_export3    │
│ bcbsa_pf         │ bcbsa_pf_export2 │ bcbsa_export1    │
│ provider_dir     │ prov_v2          │ prov_v1          │
└──────────────────┴──────────────────┴──────────────────┘
```

### Column Names

The framework supports two naming conventions:

**Standard (Recommended)**:
- `source`
- `current_release`
- `previous_release`

**Alternative**:
- `source`
- `curr_release_label`
- `prev_release_label`

## Complete Example

### 1. Preprocessor Queries File

```yaml
# preprocessor_queries.yml

# Query for source environment (staging)
gcp_pd_prcd_conf1: |
  SELECT
    source,
    current_release,
    previous_release
  FROM `project.dataset.release_metadata`
  WHERE environment = 'staging' AND is_active = TRUE

# Query for target environment (production)
gcp_pd_prcd_conf2: |
  SELECT
    source,
    current_release,
    previous_release
  FROM `project.dataset.release_metadata`
  WHERE environment = 'production' AND is_active = TRUE
```

### 2. Configuration File

```yaml
# config.yml

config_block_release_validation:
  source:
    database_type: gcpbq
    gcp:
      project_id: my-project
      dataset_id: source_data
      credentials_path: /path/to/credentials.json
      config_query_key: gcp_pd_prcd_conf1    # Add this

  target:
    database_type: gcpbq
    gcp:
      project_id: my-project
      dataset_id: target_data
      credentials_path: /path/to/credentials.json
      config_query_key: gcp_pd_prcd_conf2    # Add this

  other:
    validation_script: test_suite.yml
    preprocessor_queries: preprocessor_queries.yml
```

### 3. Test Suite (Clean - No Per-Test Config!)

```yaml
# test_suite.yml

- bcbsa_current_user_count:
    severity: critical
    source:
      query: |
        SELECT COUNT(*) as value
        FROM BCBSA_CURR_WEEK.users

    target:
      query: |
        SELECT COUNT(*) as value
        FROM BCBSA_CURR_WEEK.users

    comparisons:
      comment: "User count must match between releases"

- bcbsa_previous_transaction_sum:
    severity: high
    source:
      query: |
        SELECT SUM(amount) as value
        FROM BCBSA_PREV_WEEK.transactions
        WHERE transaction_date >= CURRENT_DATE() - 7

    target:
      query: |
        SELECT SUM(amount) as value
        FROM BCBSA_PREV_WEEK.transactions
        WHERE transaction_date >= CURRENT_DATE() - 7

    comparisons:
      threshold:
        value: percentage
        limit: 1
      comment: "Transaction amounts within 1%"

- anthem_pf_current:
    severity: critical
    source:
      query: |
        SELECT COUNT(DISTINCT provider_id) as value
        FROM ANTHEM_PF_CURR_WEEK.providers

    target:
      query: |
        SELECT COUNT(DISTINCT provider_id) as value
        FROM ANTHEM_PF_CURR_WEEK.providers

    comparisons:
      comment: "Provider count must match"
```

### 4. Execution

```bash
dataqe-run --config config.yml
```

### 5. What Happens

1. Framework loads configuration and `preprocessor_queries.yml`
2. Initializes preprocessors:
   - Source preprocessor executes `gcp_pd_prcd_conf1` → gets staging releases
   - Target preprocessor executes `gcp_pd_prcd_conf2` → gets production releases
3. For test `bcbsa_current_user_count`:
   - Source: Replaces `BCBSA_CURR_WEEK` with staging release (e.g., `bcbsa_raw_1`)
   - Target: Replaces `BCBSA_CURR_WEEK` with production release (e.g., `bcbsa_export1`)
   - Compares results
4. For test `bcbsa_previous_transaction_sum`:
   - Source: Uses `BCBSA_PREV_WEEK` → staging previous release
   - Target: Uses `BCBSA_PREV_WEEK` → production previous release
5. For test `anthem_pf_current`:
   - Source: Uses `ANTHEM_PF_CURR_WEEK` → staging ANTHEM release
   - Target: Uses `ANTHEM_PF_CURR_WEEK` → production ANTHEM release

## Troubleshooting

### Query Replacement Not Working

**Problem**: Placeholders not being replaced

**Causes & Solutions**:
1. Check `config_query_key` in database config matches key in `preprocessor_queries.yml`
2. Ensure placeholder format matches: `{SOURCE_NAME}_CURR_WEEK` or `{SOURCE_NAME}_PREV_WEEK`
3. Verify source names in query match (in uppercase) the `source` values from preprocessor query
4. Check that preprocessor query runs successfully

**Debug**:
```bash
# Check logs for:
# - "Executing preprocessor query for key: ..."
# - "Generated dataset mappings: ..."
# - "Replaced placeholders for '...'"
```

**Example**:
```
Preprocessor returns: source='ANTHEM_PF', current_release='anthem_raw_3'
Your query has:       ANTHEM_PF_CURR_WEEK.table
Result:              anthem_raw_3.table  ✓
```

### Preprocessor Query Fails

**Problem**: `Failed to get dataset mappings`

**Causes**:
1. Query syntax error (test in BigQuery console first)
2. Table doesn't exist
3. Permission denied
4. Network connectivity issue

**Solution**:
1. Test preprocessor query directly in BigQuery
2. Verify credentials have permissions
3. Check database logs for specific error

### Source vs Target Using Different Mappings

**Problem**: Source and target have different release names

**Solution**: This is handled correctly! Each database config specifies its own `config_query_key`:
```yaml
source:
  database_type: gcpbq
  gcp:
    config_query_key: gcp_pd_prcd_conf1  # Staging releases

target:
  database_type: gcpbq
  gcp:
    config_query_key: gcp_pd_prcd_conf2  # Production releases
```

Each preprocessor maintains its own cache, so replacements won't interfere.

## Best Practices

1. **Keep preprocessor queries simple** - Use SELECT with WHERE conditions
2. **Document source names** - List all valid source names returned by your queries
3. **Use consistent naming** - Keep source names uppercase in placeholders
4. **Test queries first** - Verify preprocessor queries work in BigQuery/MySQL console
5. **Use descriptive config_query_key names** - Examples: `source_releases_query`, `target_releases_query`
6. **Monitor replacement** - Check logs to confirm placeholders are replaced
7. **Validate permissions** - Ensure database credentials have access to all datasets
8. **Cache awareness** - Results are cached per preprocessor instance, so different source/target configs won't conflict
9. **Single test suite** - Write tests once with placeholders, they work with any release configuration

## Limitations

- Placeholders must be uppercase: `SOURCE_CURR_WEEK`, not `source_curr_week`
- Only two placeholder formats: `_CURR_WEEK` and `_PREV_WEEK`
- Source names in query must match returned `source` values (uppercase)
- Each preprocessor executes once per test suite run (results cached)
- Currently only for BigQuery and MySQL databases

## Performance Notes

- Preprocessor queries execute once per preprocessor instance (source/target) at test start
- Results are cached to avoid redundant database queries
- First query has slight latency (preprocessor execution)
- Subsequent test queries use cached mappings (fast)
- BigQuery queries may take longer than MySQL
- Network latency affects preprocessor query execution time
