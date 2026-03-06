# Execution Metadata in Reports - v0.3.0

## Overview

The DataQE Framework v0.3.0 adds execution metadata to all generated reports (HTML and CSV), helping users easily identify which configuration file, configuration block, and test YAML file was used for each report. This feature significantly improves report traceability and audit trails.

## What is Execution Metadata?

Execution metadata is contextual information captured during test execution that helps identify:
- **Configuration File**: Which config YAML was used (e.g., `config.yml`)
- **Blocks Executed**: Which configuration blocks were executed (e.g., `config_block_1, config_block_2`)
- **Test Script**: Which test cases file was used (e.g., `tests.yml`)
- **Execution Timestamp**: When the tests were executed (e.g., `2026-03-06 14:23:45`)

## Reports with Metadata

### 1. ExecutionReport.html

The HTML report now includes a **collapsible metadata section** at the top:

```html
<details class="metadata-section">
    <summary>📋 Execution Metadata (Click to expand)</summary>
    <div class="metadata-content">
        <p><strong>Configuration File:</strong> config.yml</p>
        <p><strong>Blocks Executed:</strong> config_block_1, config_block_2</p>
        <p><strong>Test Script:</strong> tests.yml</p>
        <p><strong>Execution Time:</strong> 2026-03-06 14:23:45</p>
    </div>
</details>
```

**Features:**
- Click the summary to expand/collapse the metadata
- Appears after the header, before the summary cards
- Styled with a blue left border (#3498db) for visibility
- Easy to identify the execution context at a glance

### 2. ExecutionReport.csv

The CSV report now includes a **metadata section at the end**:

```
(all test results)

EXECUTION SUMMARY
Total Tests,100
Passed,95
Failed,5
(etc.)

EXECUTION METADATA
Configuration File,config.yml
Blocks Executed,config_block_1, config_block_2
Test Script,tests.yml
Execution Timestamp,2026-03-06 14:23:45
```

**Features:**
- Metadata appears after the execution summary
- Key-value pairs for easy parsing
- Useful for automated report processing

### 3. FailedExecutionReport.html

The failed execution report includes metadata in **both scenarios**:

- **Failed tests view**: Collapsible metadata section above the failed tests table
- **All-passed view**: Collapsible metadata section in the all-passed message

## Usage

### Automatic Metadata Capture

Metadata is **automatically captured and added to all reports** - no additional configuration needed!

```bash
# Single block execution
dataqe-run --config config.yml
# Metadata shows: config_block_1

# All blocks execution
dataqe-run --config config.yml --all-blocks
# Metadata shows: config_block_1, config_block_2, config_block_3

# Specific block
dataqe-run --config config.yml --block config_block_1
# Metadata shows: config_block_1
```

All three reports (HTML, CSV, Failed) will include the metadata automatically.

## Benefits

### For Users
- ✅ Easily identify which config and test files generated each report
- ✅ Track execution history across multiple runs
- ✅ Correlate results back to source configuration
- ✅ Better organization when managing many reports
- ✅ Professional appearance with additional context

### For Stakeholders
- ✅ Clear audit trail of what was tested
- ✅ Understand execution parameters at a glance
- ✅ Confidence in report authenticity and traceability

### For CI/CD Systems
- ✅ Automated report identification and archiving
- ✅ Better logging and monitoring integration
- ✅ Easier troubleshooting of execution issues

## Implementation Details

### ExecutionMetadata Class

Located in `src/dataqe_framework/reporter.py`:

```python
class ExecutionMetadata:
    def __init__(
        self,
        config_file: str,
        config_blocks: List[str],
        test_yaml_file: str,
        execution_timestamp: Optional[datetime] = None
    ):
        """Store execution metadata."""
        ...

    def get_block_list(self) -> str:
        """Return comma-separated block names."""
        ...

    def get_timestamp_str(self) -> str:
        """Return formatted timestamp (YYYY-MM-DD HH:MM:SS)."""
        ...
```

### Reporter Updates

All reporters now accept optional metadata:

```python
# HTMLReporter
html_reporter.generate_report(results, summary, metadata=None)

# CSVReporter
csv_reporter.generate_report(results, summary, metadata=None)

# FailedExecutionReporter
failed_reporter.generate_report(results, summary, metadata=None)
```

### CLI Integration

The `cli.py` automatically:
1. Extracts block names from the execution order
2. Gets the test YAML file from the first block's `validation_script`
3. Resolves relative paths to absolute for clarity
4. Creates an `ExecutionMetadata` instance
5. Passes metadata to all reporters

## Backward Compatibility

✅ **Fully backward compatible** - no breaking changes!

- All metadata parameters are **optional**
- Reports work perfectly without metadata
- Graceful degradation:
  - HTML: Omits the metadata section if no metadata provided
  - CSV: Omits metadata rows if no metadata provided
- Existing code continues to work unchanged
- No performance impact

## Technical Architecture

### Files Modified

1. **src/dataqe_framework/reporter.py**
   - New `ExecutionMetadata` class (~40 lines)
   - Updated `ExecutionSummary.__init__()` to accept metadata
   - Updated `HTMLReporter.generate_report()` and `_build_html()`
   - Updated `CSVReporter.generate_report()`
   - Updated `FailedExecutionReporter.generate_report()`, `_build_failed_tests_html()`, `_build_all_passed_html()`

2. **src/dataqe_framework/cli.py**
   - Import `ExecutionMetadata`
   - Capture execution metadata after block execution (~30 lines)
   - Pass metadata to all three reporters

3. **Version Files**
   - `pyproject.toml`: 0.2.9 → 0.3.0
   - `src/dataqe_framework/__init__.py`: 0.2.9 → 0.3.0

### HTML Styling

The metadata section uses:
- `.metadata-section`: Container styling (light gray background, blue border)
- `.metadata-section summary`: Click-to-expand styling
- `.metadata-content`: Content area styling with proper spacing
- All colors match existing design palette

## Examples

### Single Block Execution

```bash
$ dataqe-run --config config.yml
```

**Metadata in report:**
```
Configuration File: config.yml
Blocks Executed: config_block_validation
Test Script: tests.yml
Execution Time: 2026-03-06 14:23:45
```

### Multi-Block Execution

```bash
$ dataqe-run --config config.yml --all-blocks
```

**Metadata in report:**
```
Configuration File: config.yml
Blocks Executed: config_block_1, config_block_2, config_block_3
Test Script: tests.yml
Execution Time: 2026-03-06 14:23:45
```

### Specific Block Execution

```bash
$ dataqe-run --config config.yml --block config_block_2
```

**Metadata in report:**
```
Configuration File: config.yml
Blocks Executed: config_block_2
Test Script: tests.yml
Execution Time: 2026-03-06 14:23:45
```

## Testing

All changes have been tested:
- ✅ 30 existing unit tests pass
- ✅ Integration tests verify metadata in HTML reports
- ✅ Integration tests verify metadata in CSV reports
- ✅ Backward compatibility tests (reports without metadata)
- ✅ Metadata formatting and timestamp tests

## Installation

```bash
# Install version 0.3.0
pip install dataqe-framework==0.3.0

# Or upgrade to latest
pip install --upgrade dataqe-framework
```

## FAQ

**Q: Do I need to do anything to enable metadata?**
A: No! Metadata is captured and added to reports automatically. No configuration needed.

**Q: What if I don't want metadata in my reports?**
A: The metadata sections are non-intrusive:
  - HTML: Collapsible (collapsed by default in browsers)
  - CSV: Appears at the end after summary

  You can ignore the metadata if not needed.

**Q: Will metadata slow down report generation?**
A: No, metadata capture and formatting has negligible performance impact (< 1ms).

**Q: Are relative paths converted to absolute?**
A: Yes, file paths are resolved to absolute paths for clarity and reproducibility.

**Q: Can I customize the metadata?**
A: Metadata is automatically captured from your execution. Future versions may support custom metadata fields.

## Support

For questions or issues with the metadata feature:
1. Check the [ENHANCEMENTS_SUMMARY.md](ENHANCEMENTS_SUMMARY.md) for feature overview
2. Review [CONFIGURATION.md](CONFIGURATION.md) for config file structure
3. Check [QUICK_START.md](QUICK_START.md) for quick reference

## Version History

- **v0.3.0** (2026-03-06): Initial release of execution metadata feature
