# Invalid Test Marking & Error Handling - Implementation Summary

**Version:** v0.2.9
**Status:** ✅ Complete and Tested
**Commits:** 77cc08d, 848fb39

## What Changed

The DataQE Framework now has **automatic, graceful error handling** that catches invalid SQL queries and other execution errors. Users see exactly what went wrong in the final reports without needing to check YAML files.

## Key Improvement: Reports Show Full Error Context

### Before (v0.2.8)
- Script would crash on invalid SQL
- User had to check logs to understand the error
- No way to skip problematic tests

### After (v0.2.9)
- Script continues on errors
- **All reports show error details** (Console, HTML, CSV)
- Automatic list of failed tests saved for next run
- Users can skip broken tests with a flag

## How It Works in Reports

### 1. ExecutionReport.html - The Main Report Users Check

**What users see:**

```
Test Name: INVALID_SQL_TEST
Status: ERROR
  ├─ Error Type: ProgrammingError
  └─ Error Message: 400 No matching signature for function SUM(STRING)
```

**Visual:**
- Yellow row (not red like failed tests)
- Error details shown directly in Status column
- Error message displayed with formatting

**Example Table:**

| Test Name | Severity | Source | Target | Status |
|-----------|----------|--------|--------|--------|
| VALID_QUERY | high | 1000 | 1000 | PASS |
| **BAD_SQL** | high | - | - | **ERROR**<br/>*ProgrammingError: No matching signature...* |
| MISSING_TABLE | high | - | - | **ERROR**<br/>*GoogleNotFound: Table not found...* |

### 2. ExecutionReport.csv - Detailed Data Export

**Error columns added:**

```csv
Test Name,Status,Error Type,Error Message
INVALID_SQL_TEST,ERROR,ProgrammingError,400 No matching signature for function SUM(STRING)
BROKEN_QUERY,ERROR,GoogleNotFound,404 Dataset not found: project.dataset
VALID_TEST,PASS,,
```

Users can:
- Import into Excel/Sheets
- Filter by Status = "ERROR"
- See exact error messages
- Sort by error type

### 3. Console Output - Immediate Feedback

**When script runs:**

```
dataqe_framework.executor - INFO - Skipping test 'KNOWN_BROKEN' (marked as invalid)
dataqe_framework.cli - INFO - Starting execution of block: default_block (script: tests.yml)
dataqe_framework.executor - ERROR - Test: INVALID_SQL_TEST - Status: ERROR (Execution time: 1.23s)
  └─ ERROR: ProgrammingError - 400 No matching signature for function SUM(STRING)
dataqe_framework.executor - INFO - Test: VALID_TEST - Status: PASS (Execution time: 0.45s)
dataqe_framework.reporter - INFO - ================================================== ==
dataqe_framework.reporter - INFO - EXECUTION SUMMARY
dataqe_framework.reporter - INFO - ================================================== ==
dataqe_framework.reporter - INFO - Total Test Cases: 2
dataqe_framework.reporter - INFO - Passed: 1 (50.0%)
dataqe_framework.reporter - INFO - Failed: 0 (0.0%)
dataqe_framework.reporter - INFO - Errors: 1
dataqe_framework.reporter - INFO - Invalid: 0
dataqe_framework.reporter - INFO - Skipped: 1
dataqe_framework.reporter - INFO - Total Execution Time: 1.68s
```

### 4. FailedExecutionReport.html - Problem Summary

Shows all tests with issues (FAIL and ERROR status):

```html
⚠️ Failed Test Execution Report
Total Problem Tests: 2

[Card Summary]
Total Tests: 3
Passed: 1
Failed: 0
Errors: 2
Skipped: 0

[Problem Details Table]
- INVALID_SQL_TEST: ERROR - ProgrammingError: No matching signature...
- TYPE_MISMATCH_TEST: ERROR - BadRequest: Cannot cast NULL to INT64
```

## Report Status Values and Colors

| Status | Color | Meaning | Example |
|--------|-------|---------|---------|
| **PASS** | 🟢 Green | Query succeeded, values match | Test data validated successfully |
| **FAIL** | 🔴 Red | Query succeeded, values don't match | Expected 100, got 95 |
| **ERROR** | 🟡 Yellow | Query execution failed | Invalid SQL syntax, table not found |
| **SKIPPED** | ⚪ Gray | Test was skipped (marked invalid) | Test marked with `invalid: true` |
| **INVALID** | 🟣 Purple | Invalid test configuration | Malformed test definition |

## Files Generated Per Execution

### 1. **ExecutionReport.html**
```
Output Directory
├── ExecutionReport.html ← Main report with error details
│                          (Error type and message shown for each ERROR test)
```
**Content:**
- Summary cards: Total, Passed, Failed, Errors, Invalid, Skipped
- Full test table with error messages displayed
- Color-coded rows for easy scanning
- Error details visible without hovering

### 2. **ExecutionReport.csv**
```
Output Directory
├── ExecutionReport.csv ← Exportable format with error columns
│                         (Can import to Excel/Sheets)
```
**Content:**
- All test results with error_type and error_message columns
- Summary section at bottom
- Easy to filter and sort

### 3. **.dataqe_invalid_tests.yml** (Auto-Generated)
```
Output Directory
├── .dataqe_invalid_tests.yml ← Auto-saved list of tests that errored
```
**Content:**
```yaml
invalid_tests:
  - test_with_invalid_sql
  - test_with_missing_table
  - test_with_connection_error
```

**Next run:**
```bash
dataqe-run --config config.yml --load-invalid-list
# These tests will be automatically skipped
```

### 4. **FailedExecutionReport.html**
```
Output Directory
├── FailedExecutionReport.html ← Summary of all problem tests
│                                 (Failed AND Error tests)
```

## Usage Patterns

### Pattern 1: Identify Broken Tests (Recommended First Step)

```bash
# Run with all tests
dataqe-run --config config.yml --all-blocks
```

**User sees:**
- Console shows which tests errored
- ExecutionReport.html shows error details in each row
- .dataqe_invalid_tests.yml saved automatically

**User action:**
- Opens ExecutionReport.html
- Reviews error messages
- Decides which tests to fix

### Pattern 2: Skip Broken Tests (Recommended Second Step)

```bash
# Automatically skip tests that errored in previous run
dataqe-run --config config.yml --all-blocks --load-invalid-list
```

**What happens:**
- Tests in .dataqe_invalid_tests.yml are skipped
- User can fix the broken tests one by one
- Running with --load-invalid-list skips the broken ones

### Pattern 3: Mark Known Broken Tests (Optional)

For tests you know are broken and don't want to run:

```yaml
- PERMANENTLY_BROKEN_TEST:
    invalid: true  # Skip this entirely
    source:
      query: SELECT * FROM deleted_table
    target:
      query: SELECT * FROM deleted_table
```

**Result:**
- Test is skipped before execution
- Not counted as error
- Doesn't appear in results

### Pattern 4: Strict Mode (For CI/CD)

```bash
# Exit immediately on any error
dataqe-run --config config.yml --all-blocks --fail-on-error
```

**Use case:**
- CI/CD pipelines that fail on any problem
- Prevents partial test runs
- Useful for blocking deployments

## What Users See vs. What They Don't

### ✅ Users SEE (In Reports)
- Test name
- Severity
- Error type (ProgrammingError, GoogleNotFound, etc.)
- Error message with details
- Execution time
- Whether test passed or failed
- Summary counts (Passed, Failed, Errors, Skipped)

### ❌ Users DON'T Need to Check
- Test YAML file (everything is in the report)
- Server logs (error message is shown)
- Database directly (error message shows what went wrong)
- Console output (full details in HTML report)

## Error Message Examples in Reports

### Example 1: Invalid SQL Syntax
```
Test: test_with_sum_error
Status: ERROR
Error Type: ProgrammingError
Error Message: 400 No matching signature for function SUM(STRING)
```

### Example 2: Table Not Found
```
Test: test_with_missing_table
Status: ERROR
Error Type: GoogleNotFound
Error Message: 404 Not found: dataset 'project.nonexistent_dataset'
```

### Example 3: Type Mismatch
```
Test: test_with_bad_cast
Status: ERROR
Error Type: BadRequest
Error Message: 400 Cannot cast NULL to type INT64
```

### Example 4: Connection Error
```
Test: test_connection_timeout
Status: ERROR
Error Type: ConnectionError
Error Message: 503 Service Unavailable - Database is down
```

## Testing

All functionality tested with 9 unit tests:

```python
✅ test_skip_test_with_invalid_true
✅ test_skip_test_with_invalid_false
✅ test_skip_test_without_invalid_field
✅ test_summary_counts_errors
✅ test_summary_counts_skipped
✅ test_summary_total_tests_includes_all_statuses
✅ test_executor_catches_source_query_error
✅ test_executor_continues_after_error
✅ test_result_includes_error_fields
```

**Coverage:**
- Error catching mechanism
- Skip logic for invalid tests
- Result field population
- Summary calculation with new statuses
- Continuation after errors

## Implementation Details

### Modified Files

#### 1. `src/dataqe_framework/executor.py`
- Added `_should_skip_test()` function
- Wrapped query execution in try-catch
- Added error fields to results
- Continues execution on error

#### 2. `src/dataqe_framework/cli.py`
- Added `save_invalid_tests()` - Saves failed test list
- Added `load_invalid_tests()` - Loads invalid list
- Added `filter_test_cases_by_invalid_list()` - Marks tests invalid
- Added CLI flags: --skip-invalid, --load-invalid-list, --fail-on-error
- Updated execute_block() to handle invalid tests

#### 3. `src/dataqe_framework/reporter.py`
- Updated ExecutionSummary with error and skipped counters
- Enhanced ConsoleReporter to show error messages
- Enhanced HTMLReporter with error display in Status column
- Enhanced CSVReporter with error_type and error_message columns
- Updated FailedExecutionReport to include error tests
- Added CSS classes for ERROR and SKIPPED statuses

#### 4. `pyproject.toml` & `src/dataqe_framework/__init__.py`
- Version bumped to 0.2.9

### New Files
- `tests/test_error_handling.py` - 9 unit tests
- `INVALID_TEST_FEATURE.md` - Comprehensive feature documentation

## Backward Compatibility

✅ **100% Backward Compatible**
- All existing tests run without changes
- New fields are optional in results
- Error display doesn't break parsing
- Reporters handle new statuses gracefully

⚠️ **Only Breaking Change (Positive):**
- Script now continues on errors instead of crashing
- Old behavior available with `--fail-on-error` flag

## Summary

**Before:** Script crashes → User has to debug logs → Slow feedback loop

**After:** Script completes → Error details in HTML report → User sees everything needed

The implementation follows the design principle: **Make it obvious what went wrong without requiring users to check external files.**

---

**Status:** ✅ Production Ready
**All Tests:** Passing (9/9)
**Documentation:** Complete
**Version:** 0.2.9
