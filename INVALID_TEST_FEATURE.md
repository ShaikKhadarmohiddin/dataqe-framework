# Invalid Test Marking & Error Handling Feature (v0.2.9)

## Overview

This feature implements graceful error handling for query execution failures and allows tests to be marked as invalid to skip execution. Users don't need to manually mark tests as invalid in most cases - when a test has an invalid SQL query, it will automatically be caught, marked with status "ERROR", and the error details will be displayed in all reports.

## Key Behaviors

### 1. Invalid SQL / Query Errors

When a test has invalid SQL or encounters a query execution error:

- ✅ **Status:** `ERROR` (clearly indicates the problem)
- ✅ **Execution:** Continues to next test (doesn't crash)
- ✅ **Error Details:** Displayed in all reports (HTML, CSV, Console)
- ✅ **Auto-saved:** Failed test names saved to `.dataqe_invalid_tests.yml` for next run

### 2. Manually Marked Invalid Tests

Tests marked with `invalid: true` in YAML:

- ✅ **Execution:** Skipped entirely (not run)
- ✅ **Status:** Not in results (skipped tests counted separately)
- ✅ **Use Case:** Skip known broken tests without generating error logs

## Report Details

### Console Output

```
Test: INVALID_SQL_TEST - Status: ERROR (Execution time: 1.23s)
  └─ ERROR: ProgrammingError - 400 No matching signature for function...

Test: BROKEN_QUERY - Status: ERROR (Execution time: 0.89s)
  └─ ERROR: GoogleNotFound - Dataset not found...

Test: VALID_TEST - Status: PASS (Execution time: 0.45s)

============================================================
EXECUTION SUMMARY
============================================================
Total Test Cases: 3
Passed: 1 (33.3%)
Failed: 0 (0.0%)
Errors: 2
Invalid: 0
Skipped: 0
Total Execution Time: 2.57s
============================================================
```

### ExecutionReport.html

The HTML report displays error details directly in the Status column:

| Test Name | Severity | Source Value | Target Value | Status | Execution Time |
|-----------|----------|-------------|------------|--------|-----------------|
| INVALID_SQL_TEST | high | None | None | **ERROR**<br/><small>ProgrammingError: 400 No matching signature...</small> | 1.23s |
| BROKEN_QUERY | high | None | None | **ERROR**<br/><small>GoogleNotFound: Dataset not found...</small> | 0.89s |
| VALID_TEST | high | 100 | 100 | **PASS** | 0.45s |

**Color Coding:**
- 🟢 **GREEN (PASS)** - Test passed
- 🔴 **RED (FAIL)** - Test failed (values don't match)
- 🟡 **YELLOW (ERROR)** - Query execution error (invalid SQL, connection issues, etc.)
- ⚪ **GRAY (SKIPPED)** - Test was skipped (marked as invalid)
- 🟣 **PURPLE (INVALID)** - Invalid test configuration

### ExecutionReport.csv

```csv
Test Name,Severity,Source Value,Target Value,Status,Error Type,Error Message,Execution Time (ms),Source Query Time (ms),Target Query Time (ms),Comparison Time (ms)
INVALID_SQL_TEST,high,,,ERROR,ProgrammingError,400 No matching signature for function...,1230.45,1200.32,0.00,0.00
BROKEN_QUERY,high,,,ERROR,GoogleNotFound,Dataset not found: project.dataset,890.22,890.22,0.00,0.00
VALID_TEST,high,100,100,PASS,,0.00,45.67,45.32,0.12

EXECUTION SUMMARY
Total Tests,3
Passed,1,33.3%
Failed,0,0.0%
Errors,2
Invalid,0
Skipped,0
Total Execution Time (ms),2571.67
```

### FailedExecutionReport.html

Lists all failed and error tests with their details:

```html
⚠️ Failed Test Execution Report
Total Problem Tests: 2

[Summary cards showing: Total Tests: 3, Passed: 1, Failed: 0, Errors: 2, Invalid: 0, Skipped: 0]

[Table showing INVALID_SQL_TEST and BROKEN_QUERY with ERROR status and error messages]
```

## Usage Examples

### Example 1: Default Behavior (Recommended)

```bash
dataqe-run --config bqconfig.yml --all-blocks
```

**What happens:**
1. All tests execute
2. If a test has invalid SQL, it catches the error
3. Test gets status `ERROR` with error details
4. Script continues to next test (doesn't crash)
5. Reports show all details
6. `.dataqe_invalid_tests.yml` is saved with test names that errored

### Example 2: Load Invalid Tests from Previous Run

```bash
# First run - identifies errors
dataqe-run --config bqconfig.yml --all-blocks

# Check the error details in ExecutionReport.html or ExecutionReport.csv

# Second run - automatically skip the tests that errored
dataqe-run --config bqconfig.yml --all-blocks --load-invalid-list
```

### Example 3: Manually Mark Tests as Invalid

For tests you know are broken and don't want to run:

```yaml
- KNOWN_BROKEN_TEST:
    severity: high
    invalid: true  # Mark as invalid - will be skipped entirely
    source:
      query: |
        SELECT * FROM nonexistent_table
    target:
      query: |
        SELECT * FROM nonexistent_table
    comparisons:
      threshold:
        value: percentage
        limit: 1

- WORKING_TEST:
    severity: high
    source:
      query: |
        SELECT COUNT(*) as count FROM my_table
    target:
      query: |
        SELECT COUNT(*) as count FROM my_table
    comparisons:
      exact:
        value: '='
```

When run:
- `KNOWN_BROKEN_TEST` is skipped (not executed, not in results)
- `WORKING_TEST` executes normally

### Example 4: Strict Mode (Exit on Error)

```bash
dataqe-run --config bqconfig.yml --all-blocks --fail-on-error
```

**What happens:**
1. First test with an error causes immediate exit
2. Script fails with error summary
3. Use when you want to catch errors immediately in CI/CD

### Example 5: Skip Tests Marked Invalid in YAML

```bash
dataqe-run --config bqconfig.yml --all-blocks --skip-invalid
```

**What happens:**
1. Tests with `invalid: true` in YAML are skipped
2. Tests with query errors still execute and show status "ERROR"
3. Results show both skipped count and error count

## Result Status Values

| Status | Meaning | Color | When Used |
|--------|---------|-------|-----------|
| **PASS** | Test passed - values match/condition met | 🟢 Green | Comparison successful |
| **FAIL** | Test failed - values don't match/condition not met | 🔴 Red | Comparison unsuccessful |
| **ERROR** | Query execution failed (invalid SQL, connection error, etc.) | 🟡 Yellow | Exception during query execution |
| **INVALID** | Invalid test configuration | 🟣 Purple | Test config validation failed |
| **SKIPPED** | Test marked as invalid and skipped | ⚪ Gray | Test has `invalid: true` in YAML |

## Files Generated

After running tests, these files are created in the output directory:

1. **ExecutionReport.html** - Full HTML report with all test details and error messages
2. **ExecutionReport.csv** - CSV export with error_type and error_message columns
3. **FailedExecutionReport.html** - Summary of failed and error tests
4. **AutomationData.csv** - CI/CD integration file
5. **.dataqe_invalid_tests.yml** - Auto-generated list of tests that errored (for next run)

Example `.dataqe_invalid_tests.yml`:
```yaml
invalid_tests:
  - bq_to_revenge_sync__test_with_sql_error
  - bq_to_revenge_sync__test_with_bad_type_cast
  - bq_to_revenge_sync__test_with_connection_timeout
```

## Backward Compatibility

✅ **Fully backward compatible** - All existing tests continue to work as before:

- Tests without `invalid` field execute normally
- Error messages don't break existing parsing
- New CLI flags are optional
- Summary calculations include new status types
- Reporters automatically handle new statuses with appropriate styling

⚠️ **Breaking Change Notes:**
- Default behavior now continues on errors (previously crashed) - **This is better!**
  - If you need the old behavior, use `--fail-on-error` flag
- New fields in result dict are optional
- Error status uses yellow styling (not red, which is reserved for failed comparisons)

## Implementation Summary

### Code Changes
- **executor.py** - Try-catch blocks around query execution, error fields in results
- **cli.py** - Invalid test loading/saving, new CLI flags, filter logic
- **reporter.py** - Error/skipped counters, error message display, updated styling

### New Functions
- `_should_skip_test(test_config)` - Check if test marked invalid
- `save_invalid_tests(output_dir, failed_test_names)` - Save failed tests list
- `load_invalid_tests(output_dir)` - Load invalid tests from file
- `filter_test_cases_by_invalid_list(test_cases, invalid_test_names)` - Mark tests invalid

### New Result Fields
- `error_occurred` (bool) - True if exception occurred
- `error_type` (str) - Exception type (e.g., "ProgrammingError", "GoogleNotFound")
- `error_message` (str) - Exception message with details

### New CLI Flags
- `--skip-invalid` - Skip tests with `invalid: true`
- `--load-invalid-list` - Load and skip tests from `.dataqe_invalid_tests.yml`
- `--fail-on-error` - Exit immediately on query errors (strict mode)

## Testing

9 unit tests cover:
- Skip logic for invalid tests
- Error counting in summaries
- Error catching and continuation
- Result field population
- All tests passing ✅

## Error Message Examples

### Invalid SQL Syntax
```
Status: ERROR
Error Type: ProgrammingError
Error Message: 400 No matching signature for function SUM(STRING)
```

### Connection Error
```
Status: ERROR
Error Type: ConnectionError
Error Message: 401 Unauthenticated. Request had invalid authentication credentials
```

### Table Not Found
```
Status: ERROR
Error Type: GoogleNotFound
Error Message: 404 Not found: dataset `project_id.dataset_name`
```

### Type Mismatch
```
Status: ERROR
Error Type: BadRequest
Error Message: 400 Cannot cast NULL to type INT64
```

## FAQ

**Q: Do I need to mark invalid tests manually?**
A: No! Invalid SQL queries are automatically caught and marked with "ERROR" status. The `invalid: true` marker is for known broken tests you want to skip entirely.

**Q: Will the script stop if a test has a SQL error?**
A: No! The script continues to the next test. Use `--fail-on-error` if you want it to stop.

**Q: Where can I see the error details?**
A: Error details appear in all reports:
- Console: Shows error type and message for each test
- HTML: Shows error in Status column with error details
- CSV: Has error_type and error_message columns

**Q: How do I fix tests that errored?**
A: 1. Check the error message in the report
2. Fix the SQL query in the test YAML
3. Re-run the tests

**Q: Can I rerun just the failed tests?**
A: Yes! Use `--load-invalid-list` to automatically skip tests that errored in the previous run, then fix them one by one.

**Q: How is ERROR different from FAIL?**
A: - **ERROR**: The query itself failed (invalid SQL, connection issue, etc.)
  - **FAIL**: The query succeeded but the values don't match expectations

---

**Version:** v0.2.9
**Status:** ✅ Production Ready
**Tests:** 9/9 Passing
