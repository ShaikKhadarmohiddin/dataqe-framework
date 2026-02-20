# Architecture Guide

Technical architecture and design of the DataQE Framework.

## System Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                         CLI Interface                        │
│                     (cli.py / dataqe-run)                   │
└─────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────┐
│                    Config Loader                             │
│              (Loads YAML configuration files)               │
└─────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────┐
│              Validation Executor                             │
│        (Orchestrates test execution pipeline)              │
└─────────────────────────────────────────────────────────────┘
         ↙           ↓           ↓           ↘
┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐
│Connector │  │Preproc.  │  │Query     │  │Reporter  │
│Factory   │  │Processor │  │Executor  │  │Generator │
└──────────┘  └──────────┘  └──────────┘  └──────────┘
    ↙ ↘         ↓               ↓            ↙ ↓ ↓ ↘
  MySQL  BQ   Queries      Results      HTML CSV...
```

## Core Components

### 1. CLI Interface (cli.py)

**Responsibility**: Command-line entry point and workflow orchestration

**Key Functions**:
- Parse command-line arguments
- Load and validate configuration files
- Manage output directory
- Coordinate execution pipeline
- Generate reports

**Flow**:
```
dataqe-run --config <path>
    ↓
Parse arguments
    ↓
Load configuration (config_loader.py)
    ↓
Extract config block, validation script, preprocessor queries
    ↓
Initialize ValidationExecutor
    ↓
Execute tests
    ↓
Generate reports (reporter.py)
```

### 2. Config Loader (config_loader.py)

**Responsibility**: YAML configuration parsing with environment variable substitution

**Key Features**:
- Safe YAML parsing with `yaml.safe_load()`
- Environment variable substitution: `${VAR_NAME}` or `${VAR_NAME:default}`
- Path validation
- Error handling and reporting

**Example**:
```yaml
credentials_path: ${GCP_CREDENTIALS:./credentials.json}
# Replaced with environment variable or default value
```

### 3. Validation Executor (executor.py)

**Responsibility**: Main test execution engine

**Key Methods**:
- `setup_connectors()` - Initialize database connections
- `run()` - Execute all tests with timing
- `_process_query_with_preprocessor()` - Query preprocessing
- `_extract_value()` - Result extraction
- `_calculate_duration_ms()` - Timing metrics

**Execution Loop**:
```python
for test in test_cases:
    1. Extract test configuration
    2. Process source query (with preprocessor if needed)
    3. Execute source query, collect results
    4. Process target query (with preprocessor if needed)
    5. Execute target query, collect results
    6. Compare results
    7. Record timing and status
    8. Append to results list
```

### 4. Query Preprocessor (preprocessor.py)

**Responsibility**: Dynamic dataset placeholder replacement

**Key Methods**:
- `get_dataset_mappings()` - Execute preprocessor query
- `replace_placeholders_in_query()` - Replace placeholders
- `process_query()` - Main processing method

**Flow**:
```
Has config_query_key?
    ↓ Yes
Load preprocessor queries from file
    ↓
Execute query for given key
    ↓
Extract dataset mappings
    ↓
Find mapping for source_name
    ↓
Replace placeholders (BCBSA_CURR_WEEK → bcbsa_export1)
    ↓
Return modified query
```

**Column Mapping**:
```python
# Supports both naming conventions
current_release = row.get("current_release") or row.get("curr_release_label")
previous_release = row.get("previous_release") or row.get("prev_release_label")
```

### 5. Connectors

#### Connector Architecture

```
BaseConnector (Abstract)
    ├── MySQLConnector
    └── BigQueryConnector
```

**BaseConnector Interface**:
```python
class BaseConnector:
    def connect() -> None
    def execute_query(query: str) -> List[Dict]
    def close() -> None
```

#### MySQL Connector

**Responsibility**: Execute queries against MySQL databases

**Implementation**:
- Uses `mysql-connector-python` library
- Connection pooling support
- Automatic reconnection on failure
- Result conversion to list of dictionaries

**Query Execution**:
```python
connection = mysql.connector.connect(
    host=config['host'],
    port=config['port'],
    user=config['user'],
    password=config['password'],
    database=config['database']
)
cursor = connection.cursor(dictionary=True)
cursor.execute(query)
results = cursor.fetchall()
```

#### BigQuery Connector

**Responsibility**: Execute queries against Google BigQuery

**Implementation**:
- Uses `google-cloud-bigquery` library
- Service account authentication
- KMS encryption support for PHI data
- Result streaming with pagination
- Query timeout handling (120 seconds default)

**Features**:
- Location-based query execution
- KMS encryption configuration
- PHI data protection

**Query Execution**:
```python
query_job = client.query(query)
results = query_job.result(timeout=120)
# Convert to list of dictionaries
```

### 6. Comparator (comparison/comparator.py)

**Responsibility**: Compare source and target values based on test configuration

**Comparison Modes**:
1. **Exact Match**: Source equals Target
2. **Expected Value**: Source matches condition (<=, >=, ==, !=, <, >)
3. **Percentage Threshold**: |Target - Source| / Source <= limit%
4. **Absolute Threshold**: |Target - Source| <= limit

**Logic**:
```python
def compare_values(source, target, test_config):
    if 'expected' in comparisons:
        # Check source against expected value
        return evaluate_condition(source, expected)

    elif 'threshold' in comparisons:
        # Calculate difference with threshold
        if threshold['value'] == 'percentage':
            diff = abs(target - source) / source * 100
            return diff <= threshold['limit']
        else:  # absolute
            diff = abs(target - source)
            return diff <= threshold['limit']

    else:
        # Direct equality
        return source == target
```

### 7. Reporter (reporter.py)

**Responsibility**: Generate various report formats from test results

**Report Types**:

#### ExecutionSummary
```python
class ExecutionSummary:
    total_tests: int
    passed_tests: int
    failed_tests: int
    pass_percentage: float
    execution_start_time: datetime
    execution_end_time: datetime
    total_execution_time: float
```

#### Report Generators

**ConsoleReporter**:
- Real-time console output
- Progress tracking
- Execution summary

**HTMLReporter**:
- `ExecutionReport.html` - Detailed test results
- Styled HTML with CSS
- Test metrics and timing

**CSVReporter**:
- `ExecutionReport.csv` - Tabular test results
- Standard CSV format for import

**AutomationDataReporter**:
- `AutomationData.csv` - CI/CD integration
- Metadata: app, branch, platform, owner
- Test report path reference

**FailedExecutionReporter**:
- `FailedExecutionReport.html` - Failed tests summary
- All-passed confirmation if no failures
- Severity-based organization

## Data Flow

### Configuration Flow
```
config.yml
    ↓
ConfigLoader.load_config()
    ↓
{Parsed YAML with env var substitution}
    ↓
CLI extracts:
  - config_block
  - source/target configs
  - validation_script path
  - preprocessor_queries path
```

### Execution Flow
```
test_case from test_suite.yml
    ↓
For Source: Extract query + preprocessor config
    ↓
Preprocessor.process_query()
    ├── Load preprocessor_queries.yml
    ├── Execute preprocessor query
    ├── Extract dataset mappings
    └── Replace placeholders
    ↓
Connector.execute_query(processed_query)
    ├── Connect to database
    ├── Execute query
    └── Convert results to dict list
    ↓
Extract single value from result
    ↓
Same for Target
    ↓
Comparator.compare_values(source, target, config)
    ↓
Record result with timing metrics
    ↓
Append to results list
```

### Report Generation Flow
```
results = [
  {test_name, status, source_value, target_value, timing, ...},
  ...
]
    ↓
ExecutionSummary.generate(results)
    ├── Count pass/fail
    ├── Calculate pass percentage
    ├── Track timing
    ↓
For each reporter:
    ├── ConsoleReporter.report()
    ├── HTMLReporter.generate_report()
    ├── CSVReporter.generate_report()
    ├── AutomationDataReporter.generate_report()
    └── FailedExecutionReporter.generate_report()
```

## Class Hierarchy

### Connectors
```
BaseConnector (abstract)
├── execute_query(query: str) -> List[Dict]
├── connect() -> None
└── close() -> None

MySQLConnector(BaseConnector)
├── __init__(host, port, user, password, database)
├── connect()
├── execute_query(query)
└── close()

BigQueryConnector(BaseConnector)
├── __init__(config)
├── connect()
├── _setup_encryption()
├── execute_query(query)
└── close()
```

### Reporters
```
BaseReporter (abstract)
├── generate_report(results, summary)

ConsoleReporter(BaseReporter)
├── report_test_execution(test_name, result)
└── report_summary(summary)

HTMLReporter(BaseReporter)
├── generate_report(results, summary) -> str

CSVReporter(BaseReporter)
├── generate_report(results, summary) -> str

AutomationDataReporter(BaseReporter)
├── generate_report(results, summary, app, branch, platform, owner) -> str

FailedExecutionReporter(BaseReporter)
├── generate_report(results, summary) -> str
```

## Error Handling

### Connection Errors
```
try:
    connector.connect()
except ConnectionError:
    logger.error("Failed to connect")
    raise
```

### Query Execution Errors
```
try:
    results = connector.execute_query(query)
except Exception as e:
    logger.error(f"Failed to execute query: {e}")
    raise RuntimeError(f"Query execution failed: {e}")
```

### Preprocessor Errors
```
try:
    processed_query = preprocessor.process_query(...)
except Exception as e:
    logger.error(f"Preprocessor error: {e}")
    return original_query  # Fallback to original
```

## Performance Considerations

### Query Execution
- Queries run serially (one test after another)
- Network latency affects execution time
- Large result sets consume memory
- BigQuery queries include network roundtrips

### Preprocessor Overhead
- Executes additional query for each test with `config_query_key`
- Consider query optimization for preprocessor queries
- Results are not cached (re-executed for each test)

### Memory Usage
- Result sets loaded entirely in memory
- Large queries may cause memory issues
- Consider result pagination for very large datasets

## Extensibility

### Adding New Database Types

1. Create new connector class:
```python
class CustomConnector(BaseConnector):
    def connect(self):
        # Initialize connection

    def execute_query(self, query: str):
        # Execute query and return results as List[Dict]

    def close(self):
        # Close connection
```

2. Register in connector factory:
```python
# In connectors/__init__.py
elif db_type == "custom":
    from .custom_connector import CustomConnector
    return CustomConnector(config)
```

### Adding New Report Types

1. Create new reporter class:
```python
class CustomReporter:
    def __init__(self, output_dir):
        self.output_dir = output_dir

    def generate_report(self, results, summary):
        # Generate report in custom format
        # Save to output_dir
        return report_path
```

2. Call in CLI:
```python
custom_reporter = CustomReporter(output_dir)
report_path = custom_reporter.generate_report(results, summary)
logger.info(f"Custom report generated: {report_path}")
```

## Logging

All components use Python's standard `logging` module:

```python
logger = logging.getLogger(__name__)

# Log levels:
logger.debug("Detailed information for diagnostics")
logger.info("General informational messages")
logger.warning("Warning messages (non-critical)")
logger.error("Error messages (issues need attention)")
```

Log format:
```
%(name)s - %(levelname)s - %(asctime)s - %(message)s
```

Example:
```
dataqe_framework.cli - INFO - 2026-02-20 11:35:00,961 - Started execution
dataqe_framework.connectors.bigquery_connector - INFO - 2026-02-20 11:35:01,234 - Query submitted
```

## Configuration as Code

### Environment Variable Substitution

Syntax: `${VARIABLE_NAME:default_value}`

```yaml
# With default
credentials_path: ${GCP_CREDS:./creds.json}

# Required
project_id: ${GCP_PROJECT}  # Fails if not set
```

Used in:
- Database credentials
- File paths
- Any YAML value

## Thread Safety

**Current Implementation**: Single-threaded

- Tests execute sequentially
- No concurrent database operations
- Future versions could implement parallel execution

**Considerations for Parallel Execution**:
- Connection pooling would be needed
- Thread-safe logger configuration required
- Careful resource management for large test suites

## Version Compatibility

**Python**: 3.8+
- Uses standard library features
- Compatible with recent Python versions

**Dependencies**:
- mysql-connector-python
- google-cloud-bigquery
- pyyaml
- jinja2 (for HTML templating)
