# Preprocessor YAML File Error Handling

## Overview

When you specify a `preprocessor_queries` file in your config but the file is missing, invalid, or cannot be read, you now get a **clear, actionable error message** that tells you exactly what went wrong and how to fix it.

## Error Messages

### 1. File Not Found

**When it happens:**
- Preprocessor YAML file path is specified in config but the file doesn't exist
- Path is wrong or file was deleted

**Error Message:**

```
FileNotFoundError: Preprocessor queries file not found: /path/to/preprocessor_queries.yml
Please ensure the file exists at the specified path.
Config key: 'preprocessor_queries' in block 'block_name'
```

**Example in config:**
```yaml
my_block:
  source:
    database_type: gcpbq
    gcp:
      project_id: my-project
      dataset_id: my_dataset
  target:
    database_type: gcpbq
    gcp:
      project_id: my-project
      dataset_id: my_dataset
  other:
    validation_script: tests.yml
    preprocessor_queries: /path/to/preprocessor_queries.yml  # ← File doesn't exist
```

**How to fix:**
1. Check the file path in the `preprocessor_queries` config key
2. Verify the file exists at that location
3. If using relative path, make sure it's relative to your current working directory
4. Run the command again

---

### 2. Invalid YAML File

**When it happens:**
- Preprocessor YAML file has syntax errors
- File is not valid YAML format

**Error Message:**

```
RuntimeError: Error loading preprocessor queries from /path/to/preprocessor_queries.yml:
YAMLError: mapping values are not allowed here
```

**Example - Invalid YAML file:**
```yaml
# Bad YAML - duplicate colons
test_query: SELECT 1
another_query: SELECT : : 2
```

**How to fix:**
1. Open the preprocessor YAML file
2. Check for YAML syntax errors
3. Valid YAML should look like:
   ```yaml
   query_key_1: "SELECT * FROM table1"
   query_key_2: "SELECT * FROM table2"
   ```
4. Use a YAML validator if unsure
5. Run the command again

---

### 3. File Reading Error

**When it happens:**
- File exists but cannot be read (permission denied)
- Disk read error
- File encoding issue

**Error Message:**

```
RuntimeError: Error loading preprocessor queries from /path/to/preprocessor_queries.yml:
PermissionError: [Errno 13] Permission denied: '/path/to/preprocessor_queries.yml'
```

**How to fix:**
1. Check file permissions: `ls -la /path/to/preprocessor_queries.yml`
2. Ensure your user has read permission
3. Fix permissions if needed: `chmod 644 /path/to/preprocessor_queries.yml`
4. Run the command again

---

## Validation Happens At

### 1. Configuration Load Time (cli.py)

```python
if preprocessor_queries_path:
    # Resolve relative path
    if not os.path.isabs(preprocessor_queries_path):
        preprocessor_queries_path = os.path.abspath(preprocessor_queries_path)

    # Validate that preprocessor file exists
    if not os.path.exists(preprocessor_queries_path):
        raise FileNotFoundError(
            f"Preprocessor queries file not found: {preprocessor_queries_path}\n"
            f"Please ensure the file exists at the specified path.\n"
            f"Config key: 'preprocessor_queries' in block '{block_name}'"
        )
```

**When:** Before any tests are executed, when the block is being prepared

**Benefit:** You get the error immediately, before wasting time on test execution

---

### 2. Preprocessor Initialization (preprocessor.py)

```python
def _load_preprocessor_queries(self) -> None:
    """Load preprocessor queries from YAML file."""
    if not os.path.exists(self.preprocessor_queries_path):
        raise FileNotFoundError(
            f"Preprocessor queries file not found: {self.preprocessor_queries_path}\n"
            f"Please ensure the file exists at the specified path.\n"
            f"Expected format: YAML file with preprocessor query definitions."
        )

    try:
        with open(self.preprocessor_queries_path, "r") as file:
            self.preprocessor_queries = yaml.safe_load(file) or {}
    except FileNotFoundError:
        raise
    except Exception as e:
        raise RuntimeError(
            f"Error loading preprocessor queries from {self.preprocessor_queries_path}:\n"
            f"{type(e).__name__}: {str(e)}"
        )
```

**When:** During executor initialization

**Benefit:** Provides detailed error type and message for debugging

---

## Example Error Flow

### Scenario: Missing preprocessor_queries.yml

**Command:**
```bash
dataqe-run --config config.yml --all-blocks
```

**Output:**
```
FileNotFoundError: Preprocessor queries file not found: /home/user/project/preprocessor_queries.yml
Please ensure the file exists at the specified path.
Config key: 'preprocessor_queries' in block 'default_block'
```

**Steps to Fix:**
1. Check if file exists: `ls -la /home/user/project/preprocessor_queries.yml`
2. If not found, create the file or update the path in config.yml
3. Run again: `dataqe-run --config config.yml --all-blocks`

---

## Valid Preprocessor YAML Format

### Example preprocessor_queries.yml:
```yaml
# Key: config_query_key (used in config)
# Value: SQL query to get dataset mappings
get_dataset_mappings: |
  SELECT
    source_name as source,
    current_release_dataset as current_release,
    previous_release_dataset as previous_release
  FROM dataset_mapping_table
  WHERE active = true

another_mapping: |
  SELECT
    source_name as source,
    current_release_dataset as current_release,
    previous_release_dataset as previous_release
  FROM another_mapping_table
```

### Config that references it:
```yaml
my_block:
  source:
    database_type: gcpbq
    gcp:
      project_id: my-project
      dataset_id: my_dataset
      config_query_key: get_dataset_mappings  # Points to key in preprocessor YAML
  target:
    database_type: gcpbq
    gcp:
      project_id: my-project
      dataset_id: my_dataset
      config_query_key: get_dataset_mappings
  other:
    validation_script: tests.yml
    preprocessor_queries: ./preprocessor_queries.yml  # Path to this file
```

---

## Test Coverage

The following error scenarios are tested:

✅ **test_missing_preprocessor_file_raises_error**
- Verifies FileNotFoundError is raised
- Checks error message contains helpful information

✅ **test_preprocessor_file_exists**
- Verifies file loads successfully when it exists

✅ **test_invalid_yaml_file_raises_error**
- Verifies RuntimeError is raised for invalid YAML
- Checks error message indicates parsing problem

---

## Troubleshooting Checklist

| Issue | Check | Fix |
|-------|-------|-----|
| FileNotFoundError | File path in config | Update path, create file, or check location |
| YAMLError | YAML syntax | Validate file syntax, use proper indentation |
| PermissionError | File permissions | `chmod 644 preprocessor_queries.yml` |
| Empty file | File has content | Add valid query definitions to file |
| Wrong format | YAML structure | Follow format: `key: "SELECT ..."` |

---

## When Preprocessor is Optional

If you **don't** use preprocessor queries:
- Don't include `preprocessor_queries` key in config
- Or set it to `null`
- Framework will skip preprocessing entirely
- **No error messages** will be generated

---

## Summary

**Error messages for missing/invalid preprocessor files now:**
✅ Appear immediately, not during test execution
✅ Tell you exactly what's wrong (file missing, invalid YAML, permission denied)
✅ Show where to look in your config
✅ Suggest how to fix it

**This prevents wasted time debugging and makes the user experience much better.**
