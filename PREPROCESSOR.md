# Dynamic Dataset Replacement (Preprocessor Feature)

This guide explains how to use the dynamic dataset replacement feature for validating multiple releases or environment-specific datasets.

## Overview

The preprocessor feature allows you to:
- Replace dataset name placeholders with actual release names
- Maintain single test suite for multiple data versions
- Support multi-release environments
- Centralize dataset mapping configuration

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

## Configuration

### Step 1: Create Preprocessor Queries File

Create a YAML file with queries that return dataset mappings:

```yaml
# preprocessor_queries.yml

get_bcbsa_releases: |
  SELECT source, current_release, previous_release
  FROM release_metadata
  WHERE source = 'bcbsa' AND is_active = TRUE

get_provider_directory_releases: |
  SELECT source, current_release, previous_release
  FROM release_metadata
  WHERE source = 'provider_directory' AND is_active = TRUE

get_all_releases: |
  SELECT source, current_release, previous_release
  FROM release_metadata
  WHERE is_active = TRUE
```

### Step 2: Add Preprocessor Path to Config

```yaml
config_block_validation:
  source:
    database_type: gcpbq
    gcp:
      project_id: my-project
      dataset_id: source_dataset
      credentials_path: /path/to/credentials.json

  target:
    database_type: gcpbq
    gcp:
      project_id: my-project
      dataset_id: target_dataset
      credentials_path: /path/to/credentials.json

  other:
    validation_script: test_suite.yml
    preprocessor_queries: preprocessor_queries.yml  # Add this
```

### Step 3: Add Preprocessor Config to Test Suite

```yaml
- test_current_release:
    severity: critical
    source:
      query: |
        SELECT COUNT(*) as value FROM BCBSA_CURR_WEEK.users
      config_query_key: get_bcbsa_releases    # Add this
      source_name: bcbsa                      # Add this

    target:
      query: |
        SELECT COUNT(*) as value FROM BCBSA_CURR_WEEK.users
      config_query_key: get_bcbsa_releases
      source_name: bcbsa

    comparisons:
      comment: "User count must match"
```

## Execution Flow

```
┌─────────────────────────────────────┐
│ 1. Load Configuration File          │
│    - Config block                   │
│    - Preprocessor queries path      │
└─────────────────────────────────────┘
                  ↓
┌─────────────────────────────────────┐
│ 2. Load Test Suite                  │
│    - Test definitions with          │
│      config_query_key               │
│      source_name                    │
└─────────────────────────────────────┘
                  ↓
┌─────────────────────────────────────┐
│ 3. For Each Test with config_query_key:
│    - Execute preprocessor query     │
│    - Get dataset mappings           │
│    - Find matching source_name      │
│    - Extract current_release value  │
└─────────────────────────────────────┘
                  ↓
┌─────────────────────────────────────┐
│ 4. Replace Placeholders             │
│    - BCBSA_CURR_WEEK → bcbsa_export1
│    - BCBSA_PREV_WEEK → bcbsa_export3
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

The framework recognizes uppercase placeholders with the source name prefix:

### Supported Formats

```yaml
# Current Release (two formats supported)
{SOURCE_NAME}_CURR_WEEK
{SOURCE_NAME}_CURRENT

# Previous Release (two formats supported)
{SOURCE_NAME}_PREV_WEEK
{SOURCE_NAME}_PREVIOUS
```

### Examples

```yaml
# For source_name: bcbsa
BCBSA_CURR_WEEK        # Replaced with current_release value
BCBSA_PREV_WEEK        # Replaced with previous_release value
BCBSA_CURRENT          # Replaced with current_release value
BCBSA_PREVIOUS         # Replaced with previous_release value

# For source_name: provider_directory
PROVIDER_DIRECTORY_CURR_WEEK
PROVIDER_DIRECTORY_PREV_WEEK

# For source_name: claims
CLAIMS_CURR_WEEK
CLAIMS_PREV_WEEK
```

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

get_release_mappings: |
  SELECT
    source,
    current_release,
    previous_release
  FROM `project.dataset.release_metadata`
  WHERE is_active = TRUE
    AND environment = 'production'
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

  target:
    database_type: gcpbq
    gcp:
      project_id: my-project
      dataset_id: target_data
      credentials_path: /path/to/credentials.json

  other:
    validation_script: test_suite.yml
    preprocessor_queries: preprocessor_queries.yml
```

### 3. Test Suite

```yaml
# test_suite.yml

- bcbsa_current_user_count:
    severity: critical
    source:
      query: |
        SELECT COUNT(*) as value
        FROM BCBSA_CURR_WEEK.users
      config_query_key: get_release_mappings
      source_name: bcbsa

    target:
      query: |
        SELECT COUNT(*) as value
        FROM BCBSA_CURR_WEEK.users
      config_query_key: get_release_mappings
      source_name: bcbsa

    comparisons:
      comment: "User count must match between releases"

- bcbsa_previous_transaction_sum:
    severity: high
    source:
      query: |
        SELECT SUM(amount) as value
        FROM BCBSA_PREV_WEEK.transactions
        WHERE transaction_date >= CURRENT_DATE() - 7
      config_query_key: get_release_mappings
      source_name: bcbsa

    target:
      query: |
        SELECT SUM(amount) as value
        FROM BCBSA_PREV_WEEK.transactions
        WHERE transaction_date >= CURRENT_DATE() - 7
      config_query_key: get_release_mappings
      source_name: bcbsa

    comparisons:
      threshold:
        value: percentage
        limit: 1
      comment: "Transaction amounts within 1%"

- provider_directory_current:
    severity: critical
    source:
      query: |
        SELECT COUNT(DISTINCT provider_id) as value
        FROM PROVIDER_DIR_CURR_WEEK.providers
      config_query_key: get_release_mappings
      source_name: provider_directory

    target:
      query: |
        SELECT COUNT(DISTINCT provider_id) as value
        FROM PROVIDER_DIR_CURR_WEEK.providers
      config_query_key: get_release_mappings
      source_name: provider_directory

    comparisons:
      comment: "Provider count must match"
```

### 4. Execution

```bash
dataqe-run --config config.yml
```

### 5. What Happens

1. Framework loads configuration and `preprocessor_queries.yml`
2. For test `bcbsa_current_user_count`:
   - Executes query for key `get_release_mappings`
   - Gets result: `source='bcbsa', current_release='bcbsa_export1'`
   - Replaces `BCBSA_CURR_WEEK` with `bcbsa_export1` in query
   - Runs: `SELECT COUNT(*) FROM bcbsa_export1.users`
3. For test `bcbsa_previous_transaction_sum`:
   - Same process, but uses `previous_release='bcbsa_export3'`
   - Runs: `SELECT SUM(amount) FROM bcbsa_export3.transactions ...`
4. For test `provider_directory_current`:
   - Finds `source_name: provider_directory`
   - Gets result with `current_release='prov_v2'`
   - Runs: `SELECT COUNT(*) FROM prov_v2.providers`

## Testing Without Preprocessor

Tests without `config_query_key` run as-is without replacement:

```yaml
- test_static_table:
    severity: medium
    source:
      query: |
        SELECT COUNT(*) as value
        FROM static_configuration_table
      # No config_query_key, so no replacement

    comparisons:
      expected: ">=1"
      comment: "Configuration table must exist"
```

## Troubleshooting

### Query Replacement Not Working

**Problem**: Placeholders not being replaced

**Causes & Solutions**:
1. Check `config_query_key` matches key in `preprocessor_queries.yml`
2. Verify `source_name` matches value returned by query
3. Ensure placeholder format matches convention: `{SOURCE_NAME}_CURR_WEEK`
4. Check that preprocessor query runs successfully

**Debug**:
```bash
# Check logs for:
# - "Executing preprocessor query for key: ..."
# - "Generated dataset mappings: ..."
# - "Replaced placeholders for '...'"
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
3. Check BigQuery logs for specific error

### Multiple Sources Confusion

**Problem**: Wrong dataset selected

**Check**:
1. Query returns correct source name (case-sensitive)
2. `source_name` in config exactly matches returned value
3. Multiple results for same source name

**Example of correct mapping**:
```yaml
# Query returns:
source='bcbsa', current_release='bcbsa_export1'

# Config has:
source_name: bcbsa  # Must match exactly

# Query uses:
BCBSA_CURR_WEEK     # Uppercase placeholder
```

## Best Practices

1. **Keep preprocessor queries simple** - Use SELECT with WHERE conditions
2. **Document source names** - List all valid source names for team reference
3. **Cache stable mappings** - Update preprocessor queries only when datasets change
4. **Test queries first** - Verify preprocessor queries work in BigQuery console
5. **Use descriptive keys** - Name preprocessor query keys clearly
6. **Monitor replacement** - Check logs to confirm placeholders are replaced
7. **Validate permissions** - Ensure database has access to all datasets

## Limitations

- Placeholders must be uppercase
- Source names must match exactly (case-sensitive)
- Only single-word placeholders are supported (no spaces)
- Preprocessor query must return exactly one row per source
- Only works with `config_query_key` and `source_name` in source/target blocks

## Performance Notes

- Preprocessor queries execute for each test with `config_query_key`
- Consider caching if preprocessor queries are slow
- BigQuery queries can take longer than MySQL
- Network latency affects execution time
