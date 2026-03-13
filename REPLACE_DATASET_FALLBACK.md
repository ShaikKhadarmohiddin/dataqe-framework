# Replace Dataset Feature with Fallback (v0.3.3+)

## Overview

The `replace_dataset` feature now supports intelligent fallback behavior for dataset/project placeholder replacement. It uses the list format with a `bq_project_id` fallback field that works in two modes:

1. **With castlight_common_lib (SPRING_PROFILES_ACTIVE set)**: Lookup actual project_id from centralized configuration
2. **Without castlight_common_lib (SPRING_PROFILES_ACTIVE not set)**: Use provided `bq_project_id` directly

## Configuration

### YAML Structure

```yaml
source:
  database_type: gcpbq
  gcp:
    config_query_key: pd_pre_processor_block  # Optional: for release label replacement
    credentials_path: qe_service_account.json
    dataset_id: source_dataset
    project_id: my-project
    replace_dataset:
      - project_name: "pd"
        dataset_name: "cdw_prcd_metadata"
        bq_project_id: "pd-project-id-123"
      - project_name: "pd"
        dataset_name: "cdw_metadata"
        bq_project_id: "pd-project-id-456"
```

## Fields

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `project_name` | string | ✓ | Project name identifier (e.g., "pd", "edw") |
| `dataset_name` | string | ✓ | Dataset name (e.g., "cdw_prcd_metadata") |
| `bq_project_id` | string | ✗ | Fallback BigQuery project ID if config_details not available |

## Behavior

### Mode 1: With castlight_common_lib (Preferred)

**When**: `SPRING_PROFILES_ACTIVE` environment variable is set AND `castlight_common_lib` is installed

**Behavior**:
- Uses `bq_project_id` as fallback only if castlight lookup fails
- Generates placeholder from `project_name` and `dataset_name`: `{PROJECT_NAME}_{DATASET_NAME}`
- Looks up actual project_id from: `config_details.data['bigquery'][project_name]['datasets'][dataset_name]['project_id']`
- Falls back to `bq_project_id` if lookup fails

**Example**:
```yaml
replace_dataset:
  - project_name: "pd"
    dataset_name: "cdw_prcd_metadata"
    bq_project_id: "fallback-project-123"  # Only used if lookup fails
```

Query with placeholder:
```sql
SELECT * FROM PD_CDW_PRCD_METADATA.table WHERE id = 1
```

After replacement (if castlight has the config):
```sql
SELECT * FROM castlight-resolved-project.table WHERE id = 1
```

### Mode 2: Without castlight_common_lib (Fallback)

**When**: `SPRING_PROFILES_ACTIVE` environment variable is NOT set OR `castlight_common_lib` is not installed

**Behavior**:
- Generates placeholder from `project_name` and `dataset_name`
- Skips castlight lookup
- Uses `bq_project_id` directly
- If `bq_project_id` is not provided, placeholder is NOT replaced (logged as warning)

**Example**:
```yaml
replace_dataset:
  - project_name: "pd"
    dataset_name: "cdw_prcd_metadata"
    bq_project_id: "my-gcp-project-pd"  # Used directly
```

Query with placeholder:
```sql
SELECT * FROM PD_CDW_PRCD_METADATA.table WHERE id = 1
```

After replacement (direct substitution):
```sql
SELECT * FROM my-gcp-project-pd.table WHERE id = 1
```

## Complete Configuration Example

```yaml
mongo_deletions:
  other:
    preprocessor_queries: logs/validation_scripts/preprocessor_queries.yml
    validation_script: logs/validation_scripts/mongo_deletion_threshold_validation.yml
  source:
    database_type: gcpbq
    gcp:
      config_query_key: pd_pre_processor_block
      credentials_path: qe_service_account.json
      dataset_id: source_dataset
      k8_db_details: pd_cdw_metadata
      location: us-central1
      project_id: my-project
      replace_dataset:
        - project_name: cdw_prcd_metadata
          dataset_name: prcd_dataset
          bq_project_id: "project-123-prcd"
        - project_name: cdw_metadata
          dataset_name: metadata_dataset
          bq_project_id: "project-456-metadata"
  target:
    database_type: gcpbq
    gcp:
      config_query_key: null
      credentials_path: qe_service_account.json
      dataset_id: target_dataset
      k8_db_details: pd_cdw_metadata
      location: us-central1
      project_id: my-project

mysql_deletions:
  other:
    preprocessor_queries: logs/validation_scripts/preprocessor_queries.yml
    validation_script: logs/validation_scripts/mysql_deletion_threshold_validation.yml
  source:
    database_type: gcpbq
    gcp:
      config_query_key: pd_pre_processor_block
      credentials_path: qe_service_account.json
      dataset_id: source_dataset
      k8_db_details: pd_cdw_metadata
      location: us-central1
      project_id: my-project
      replace_dataset:
        - project_name: cdw_prcd_metadata
          dataset_name: prcd_dataset
          bq_project_id: "project-123-prcd"
        - project_name: cdw_metadata
          dataset_name: metadata_dataset
          bq_project_id: "project-456-metadata"
  target:
    database_type: gcpbq
    gcp:
      config_query_key: null
      credentials_path: qe_service_account.json
      dataset_id: target_dataset
      k8_db_details: pd_cdw_metadata
      location: us-central1
      project_id: my-project
```

## Placeholder Generation

The placeholder is automatically generated from `project_name` and `dataset_name` in UPPERCASE:

```
Placeholder = {PROJECT_NAME}_{DATASET_NAME}
```

Examples:

| project_name | dataset_name | Generated Placeholder |
|---|---|---|
| pd | cdw_prcd_metadata | PD_CDW_PRCD_METADATA |
| edw | hierarchy_dataset | EDW_HIERARCHY_DATASET |
| pd | cdw_metadata | PD_CDW_METADATA |

## Query Replacement

The framework automatically replaces placeholders in both uppercase and lowercase forms:

```sql
-- Uppercase placeholder
SELECT * FROM PD_CDW_PRCD_METADATA.table
↓ REPLACED
SELECT * FROM my-gcp-project-pd.table

-- Lowercase placeholder
SELECT * FROM pd_cdw_prcd_metadata.table
↓ REPLACED
SELECT * FROM my-gcp-project-pd.table

-- Mixed usage (both replaced)
SELECT a.* FROM PD_CDW_PRCD_METADATA.table1 a
JOIN pd_cdw_prcd_metadata.table2 b ON a.id = b.id
↓ REPLACED
SELECT a.* FROM my-gcp-project-pd.table1 a
JOIN my-gcp-project-pd.table2 b ON a.id = b.id
```

## Error Handling & Logging

### When Replacement Succeeds

✅ **From castlight_common_lib**:
```
DEBUG: Resolved placeholder PD_CDW_PRCD_METADATA to castlight-resolved-project from config_details for pd.cdw_prcd_metadata
```

✅ **From bq_project_id fallback**:
```
DEBUG: Resolved placeholder PD_CDW_PRCD_METADATA to my-gcp-project-pd using bq_project_id fallback
```

### When Replacement Fails

❌ **Missing bq_project_id and no config_details**:
```
WARNING: Failed to resolve placeholder PD_CDW_PRCD_METADATA: no project_id from config_details and bq_project_id not provided
```

Query remains unchanged with placeholder - database query will fail with "table not found" error.

## Migration Guide

### From Old Configuration (Direct Project ID)

**Before**:
```yaml
replace_dataset:
  PD_CDW_PRCD_METADATA: "my-gcp-project-pd"
  PD_CDW_METADATA: "my-gcp-project-metadata"
```

**After**:
```yaml
replace_dataset:
  - project_name: "pd"
    dataset_name: "cdw_prcd_metadata"
    bq_project_id: "my-gcp-project-pd"
  - project_name: "pd"
    dataset_name: "cdw_metadata"
    bq_project_id: "my-gcp-project-metadata"
```

## Best Practices

1. **Always provide `bq_project_id`** as fallback - it's your safety net if castlight lookup fails
2. **Match placeholder names** - ensure query placeholders match generated ones (case-insensitive)
3. **Test configuration** - verify replacements work with your environment:
   ```bash
   # With castlight (lookups from config)
   export SPRING_PROFILES_ACTIVE=<your-profile>
   dataqe-run --config pd_configurations_bcbsa.yml

   # Without castlight (uses bq_project_id)
   dataqe-run --config pd_configurations_bcbsa.yml
   ```
4. **Review logs** - check debug logs to confirm which mode is being used
5. **Separate environments** - if using castlight, same config works across environments (lookups adapt)

## Troubleshooting

### Placeholders Not Being Replaced

**Problem**: Query still has placeholder after execution, or gets "table not found" error

**Causes & Solutions**:

1. **Missing `bq_project_id` and no castlight**:
   - ✓ Add `bq_project_id` to config
   - ✓ Or set `SPRING_PROFILES_ACTIVE` if you have castlight_common_lib

2. **Placeholder name mismatch**:
   - ✓ Verify placeholder format: `{PROJECT_NAME}_{DATASET_NAME}` (uppercase)
   - ✓ Check `project_name` and `dataset_name` in config match placeholder

3. **castlight lookup failed silently**:
   - ✓ Check logs for lookup errors
   - ✓ Verify `SPRING_PROFILES_ACTIVE` is set
   - ✓ Fallback to `bq_project_id` if castlight config missing

### Debugging

Enable debug logging to see replacement details:

```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

Look for messages like:
```
DEBUG: Resolved placeholder PD_CDW_PRCD_METADATA to ... using bq_project_id fallback
WARNING: Failed to lookup project_id for pd.cdw_prcd_metadata: ...
```

## Backward Compatibility

✅ The new fallback format is **fully backward compatible**:
- Legacy dict format still works: `{"PLACEHOLDER": "project_id"}`
- New list format with `bq_project_id` works without castlight
- Mix both formats if needed (though not recommended)

## Version History

- **v0.3.3+**: Added `bq_project_id` fallback support
- **v0.3.2**: Introduced list format with castlight_common_lib lookup
- **v0.3.1**: Legacy dict format only
