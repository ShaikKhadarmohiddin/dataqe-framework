import logging
import csv
from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Dict, Any, Optional


logger = logging.getLogger(__name__)


class ExecutionMetadata:
    """Stores and formats execution metadata for report identification."""

    def __init__(
        self,
        config_file: str,
        config_blocks: List[str],
        test_yaml_file: str,
        execution_timestamp: Optional[datetime] = None
    ):
        """
        Initialize execution metadata.

        Args:
            config_file: Path to configuration YAML file
            config_blocks: List of block names executed
            test_yaml_file: Path to test cases YAML file
            execution_timestamp: When execution started (defaults to now)
        """
        self.config_file = config_file
        self.config_blocks = config_blocks
        self.test_yaml_file = test_yaml_file
        self.execution_timestamp = execution_timestamp or datetime.now()

    def get_block_list(self) -> str:
        """Return comma-separated block names."""
        return ", ".join(self.config_blocks) if self.config_blocks else "N/A"

    def get_timestamp_str(self) -> str:
        """Return formatted timestamp string (YYYY-MM-DD HH:MM:SS)."""
        return self.execution_timestamp.strftime('%Y-%m-%d %H:%M:%S')


class ExecutionSummary:
    """Aggregates test execution results and calculates summary metrics."""

    def __init__(self, results: List[Dict[str, Any]], metadata: Optional['ExecutionMetadata'] = None):
        """
        Initialize summary with test results.

        Args:
            results: List of test result dictionaries from ValidationExecutor
            metadata: Optional ExecutionMetadata instance with execution context
        """
        self.results = results
        self.metadata = metadata
        self.total_tests = len(results)
        self.passed = sum(1 for r in results if r["status"] == "PASS")
        self.failed = sum(1 for r in results if r["status"] == "FAIL")
        self.invalid = sum(1 for r in results if r["status"] == "INVALID")
        self.error = sum(1 for r in results if r["status"] == "ERROR")
        self.skipped = sum(1 for r in results if r["status"] == "SKIPPED")
        self.critical_failed = sum(
            1 for r in results
            if r["status"] == "FAIL" and r.get("severity", "").lower() == "critical"
        )
        self.total_execution_time_ms = sum(r.get("execution_time_ms", 0) for r in results)

    def pass_percentage(self) -> float:
        """Calculate percentage of passing tests."""
        if self.total_tests == 0:
            return 0.0
        return (self.passed / self.total_tests) * 100

    def fail_percentage(self) -> float:
        """Calculate percentage of failing tests."""
        if self.total_tests == 0:
            return 0.0
        return (self.failed / self.total_tests) * 100

    def format_duration(self, milliseconds: float) -> str:
        """Format milliseconds to human-readable format (e.g., 1m 23s 456ms)."""
        total_seconds = int(milliseconds // 1000)
        remaining_ms = int(milliseconds % 1000)

        minutes = total_seconds // 60
        seconds = total_seconds % 60

        if minutes > 0:
            return f"{minutes}m {seconds}s {remaining_ms}ms"
        elif seconds > 0:
            return f"{seconds}s {remaining_ms}ms"
        else:
            return f"{remaining_ms}ms"


class ConsoleReporter:
    """Prints execution progress and summary to console."""

    def __init__(self):
        """Initialize console reporter with logging."""
        self.logger = logging.getLogger("dataqe_framework.console")
        # Disable propagation to prevent duplicate messages from parent logger
        self.logger.propagate = False
        # Only add handler if none exist (to avoid duplicates)
        if not self.logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter(
                "%(name)s - %(levelname)s - %(asctime)s - %(message)s"
            )
            handler.setFormatter(formatter)
            self.logger.addHandler(handler)
            self.logger.setLevel(logging.INFO)

    def report_test_execution(self, test_name: str, result: Dict[str, Any]) -> None:
        """
        Report individual test execution result.

        Args:
            test_name: Name of the test
            result: Test result dictionary with status and timing
        """
        status = result["status"]
        execution_time_ms = result.get("execution_time_ms", 0)
        summary = ExecutionSummary([result])
        formatted_time = summary.format_duration(execution_time_ms)

        message = f"Test: {test_name} - Status: {status} (Execution time: {formatted_time})"

        # Append detailed error message if present
        if result.get("error_occurred"):
            error_type = result.get("error_type", "Unknown")
            error_msg = result.get("error_message", "Unknown")
            message += f"\n  └─ ERROR: {error_type} - {error_msg}"
            self.logger.error(message)
        else:
            self.logger.info(message)

    def report_summary(self, summary: ExecutionSummary) -> None:
        """
        Report overall execution summary.

        Args:
            summary: ExecutionSummary instance with aggregated metrics
        """
        self.logger.info("=" * 60)
        self.logger.info("EXECUTION SUMMARY")
        self.logger.info("=" * 60)
        self.logger.info(f"Total Test Cases: {summary.total_tests}")
        self.logger.info(f"Passed: {summary.passed} ({summary.pass_percentage():.1f}%)")
        self.logger.info(f"Failed: {summary.failed} ({summary.fail_percentage():.1f}%)")
        self.logger.info(f"Errors: {summary.error}")
        self.logger.info(f"Invalid: {summary.invalid}")
        self.logger.info(f"Skipped: {summary.skipped}")

        formatted_time = summary.format_duration(summary.total_execution_time_ms)
        self.logger.info(f"Total Execution Time: {formatted_time}")
        self.logger.info("=" * 60)


class HTMLReporter:
    """Generates HTML report with styled test results."""

    def __init__(self, output_dir: str = "./output"):
        """
        Initialize HTML reporter.

        Args:
            output_dir: Directory to save HTML reports
        """
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def generate_report(self, results: List[Dict[str, Any]], summary: ExecutionSummary, metadata: Optional[ExecutionMetadata] = None) -> str:
        """
        Generate HTML report and save to file as ExecutionReport.html.

        Args:
            results: List of test results
            summary: ExecutionSummary instance
            metadata: Optional ExecutionMetadata instance with execution context

        Returns:
            Path to generated HTML file
        """
        filename = "ExecutionReport.html"
        filepath = self.output_dir / filename

        html_content = self._build_html(results, summary, metadata)

        with open(filepath, "w") as f:
            f.write(html_content)

        return str(filepath)

    def _build_html(self, results: List[Dict[str, Any]], summary: ExecutionSummary, metadata: Optional[ExecutionMetadata] = None) -> str:
        """Build HTML content for the report."""
        rows = []
        for result in results:
            status_class = self._get_status_class(result["status"])
            execution_time = summary.format_duration(result.get("execution_time_ms", 0))

            # Build error message display if error occurred
            error_display = ""
            if result.get("error_occurred"):
                error_type = result.get("error_type", "Unknown")
                error_msg = result.get("error_message", "Unknown")
                # Truncate long error messages for display
                if len(error_msg) > 100:
                    error_msg = error_msg[:97] + "..."
                error_display = f"<br/><small style='color: #c0392b; font-weight: bold;'>{error_type}: {error_msg}</small>"

            rows.append(
                f"""
                <tr class="{status_class}">
                    <td>{result['test_name']}</td>
                    <td>{result.get('severity', 'N/A')}</td>
                    <td>{self._safe_str(result.get('source_value'))}</td>
                    <td>{self._safe_str(result.get('target_value'))}</td>
                    <td>{result['status']}{error_display}</td>
                    <td>{execution_time}</td>
                </tr>
                """
            )

        rows_html = "\n".join(rows)

        # Build metadata section if available
        metadata_html = ""
        if metadata:
            metadata_html = f"""
    <details class="metadata-section">
        <summary>📋 Execution Metadata (Click to expand)</summary>
        <div class="metadata-content">
            <p><strong>Configuration File:</strong> {metadata.config_file}</p>
            <p><strong>Blocks Executed:</strong> {metadata.get_block_list()}</p>
            <p><strong>Test Script:</strong> {metadata.test_yaml_file}</p>
            <p><strong>Execution Time:</strong> {metadata.get_timestamp_str()}</p>
        </div>
    </details>
"""

        return f"""<!DOCTYPE html>
<html>
<head>
    <title>Test Report - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</title>
    <style>
        body {{
            font-family: Arial, sans-serif;
            margin: 20px;
            background-color: #f5f5f5;
        }}
        .header {{
            background-color: #2c3e50;
            color: white;
            padding: 20px;
            border-radius: 5px;
            margin-bottom: 20px;
        }}
        .metadata-section {{
            background-color: #ecf0f1;
            padding: 15px;
            border-radius: 5px;
            margin-bottom: 20px;
            border-left: 4px solid #3498db;
        }}
        .metadata-section summary {{
            cursor: pointer;
            font-weight: bold;
            color: #2c3e50;
            user-select: none;
        }}
        .metadata-section summary:hover {{
            color: #3498db;
        }}
        .metadata-content {{
            margin-top: 15px;
            padding-top: 15px;
            border-top: 1px solid #bdc3c7;
        }}
        .metadata-content p {{
            margin: 8px 0;
            line-height: 1.6;
        }}
        .metadata-content strong {{
            color: #2c3e50;
            min-width: 150px;
            display: inline-block;
        }}
        .summary {{
            display: grid;
            grid-template-columns: repeat(4, 1fr);
            gap: 15px;
            margin-bottom: 20px;
        }}
        .summary-card {{
            background-color: white;
            padding: 15px;
            border-radius: 5px;
            box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
        }}
        .summary-card h3 {{
            margin: 0 0 10px 0;
            color: #2c3e50;
        }}
        .summary-card .value {{
            font-size: 24px;
            font-weight: bold;
            color: #27ae60;
        }}
        table {{
            width: 100%;
            border-collapse: collapse;
            background-color: white;
            box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
        }}
        th {{
            background-color: #34495e;
            color: white;
            padding: 12px;
            text-align: left;
            border-bottom: 2px solid #2c3e50;
        }}
        td {{
            padding: 12px;
            border-bottom: 1px solid #ecf0f1;
        }}
        tr.pass {{
            background-color: #d5f4e6;
        }}
        tr.fail {{
            background-color: #fadbd8;
        }}
        tr.invalid {{
            background-color: #f4ecf7;
        }}
        tr.error {{
            background-color: #fef5e7;
        }}
        tr.skipped {{
            background-color: #d5d8dc;
        }}
        tr:hover {{
            background-color: #ecf0f1;
        }}
    </style>
</head>
<body>
    <div class="header">
        <h1>Test Execution Report</h1>
        <p>Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
    </div>

    {metadata_html}

    <div class="summary">
        <div class="summary-card">
            <h3>Total Tests</h3>
            <div class="value">{summary.total_tests}</div>
        </div>
        <div class="summary-card">
            <h3>Passed</h3>
            <div class="value">{summary.passed} ({summary.pass_percentage():.1f}%)</div>
        </div>
        <div class="summary-card">
            <h3>Failed</h3>
            <div class="value">{summary.failed} ({summary.fail_percentage():.1f}%)</div>
        </div>
        <div class="summary-card">
            <h3>Errors</h3>
            <div class="value">{summary.error}</div>
        </div>
        <div class="summary-card">
            <h3>Invalid</h3>
            <div class="value">{summary.invalid}</div>
        </div>
        <div class="summary-card">
            <h3>Skipped</h3>
            <div class="value">{summary.skipped}</div>
        </div>
    </div>

    <table>
        <thead>
            <tr>
                <th>Test Name</th>
                <th>Severity</th>
                <th>Source Value</th>
                <th>Target Value</th>
                <th>Status</th>
                <th>Execution Time</th>
            </tr>
        </thead>
        <tbody>
            {rows_html}
        </tbody>
    </table>
</body>
</html>
"""

    def _get_status_class(self, status: str) -> str:
        """Get CSS class for status."""
        status_map = {
            "PASS": "pass",
            "FAIL": "fail",
            "INVALID": "invalid",
            "ERROR": "error",
            "SKIPPED": "skipped"
        }
        return status_map.get(status, "invalid")

    def _safe_str(self, value: Any) -> str:
        """Safely convert value to string for HTML."""
        if value is None:
            return "None"
        return str(value)


class CSVReporter:
    """Generates CSV report with test results."""

    def __init__(self, output_dir: str = "./output"):
        """
        Initialize CSV reporter.

        Args:
            output_dir: Directory to save CSV reports
        """
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def generate_report(self, results: List[Dict[str, Any]], summary: ExecutionSummary, metadata: Optional[ExecutionMetadata] = None) -> str:
        """
        Generate CSV report and save to file as ExecutionReport.csv.

        Args:
            results: List of test results
            summary: ExecutionSummary instance
            metadata: Optional ExecutionMetadata instance with execution context

        Returns:
            Path to generated CSV file
        """
        filename = "ExecutionReport.csv"
        filepath = self.output_dir / filename

        with open(filepath, "w", newline="") as f:
            writer = csv.writer(f)

            # Write headers
            writer.writerow([
                "Test Name",
                "Severity",
                "Source Value",
                "Target Value",
                "Status",
                "Error Type",
                "Error Message",
                "Execution Time (ms)",
                "Source Query Time (ms)",
                "Target Query Time (ms)",
                "Comparison Time (ms)"
            ])

            # Write test results
            for result in results:
                # Create status with error details if applicable
                status_display = result["status"]
                error_type_display = ""
                error_msg_display = ""

                if result.get("error_occurred"):
                    error_type_display = result.get("error_type", "Unknown")
                    error_msg_display = result.get("error_message", "Unknown")

                writer.writerow([
                    result["test_name"],
                    result.get("severity", "N/A"),
                    result.get("source_value", ""),
                    result.get("target_value", ""),
                    status_display,
                    error_type_display,
                    error_msg_display,
                    f"{result.get('execution_time_ms', 0):.2f}",
                    f"{result.get('source_query_time_ms', 0):.2f}",
                    f"{result.get('target_query_time_ms', 0):.2f}",
                    f"{result.get('comparison_time_ms', 0):.2f}"
                ])

            # Write summary section
            writer.writerow([])
            writer.writerow(["EXECUTION SUMMARY"])
            writer.writerow(["Total Tests", summary.total_tests])
            writer.writerow(["Passed", summary.passed, f"{summary.pass_percentage():.1f}%"])
            writer.writerow(["Failed", summary.failed, f"{summary.fail_percentage():.1f}%"])
            writer.writerow(["Errors", summary.error])
            writer.writerow(["Invalid", summary.invalid])
            writer.writerow(["Skipped", summary.skipped])
            writer.writerow(["Total Execution Time (ms)", f"{summary.total_execution_time_ms:.2f}"])

            # Write metadata section if available
            if metadata:
                writer.writerow([])
                writer.writerow(["EXECUTION METADATA"])
                writer.writerow(["Configuration File", metadata.config_file])
                writer.writerow(["Blocks Executed", metadata.get_block_list()])
                writer.writerow(["Test Script", metadata.test_yaml_file])
                writer.writerow(["Execution Timestamp", metadata.get_timestamp_str()])

        return str(filepath)


class AutomationDataReporter:
    """Generates AutomationData.csv with execution summary in a single row."""

    def __init__(self, output_dir: str = "./output"):
        """
        Initialize AutomationData reporter.

        Args:
            output_dir: Directory to save AutomationData.csv
        """
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def generate_report(
        self,
        results: List[Dict[str, Any]],
        summary: ExecutionSummary,
        app: str = "default_app",
        branch: str = "default_branch",
        platform: str = "default_platform",
        owner: str = "default_owner",
        test_report_path: str = ""
    ) -> str:
        """
        Generate AutomationData.csv with single row summary.

        Args:
            results: List of test results
            summary: ExecutionSummary instance
            app: Application name
            branch: Branch name
            platform: Platform/environment name
            owner: Owner/executor name
            test_report_path: Path to the test report file

        Returns:
            Path to generated CSV file
        """
        filepath = self.output_dir / "AutomationData.csv"

        # Convert milliseconds to seconds for duration
        duration_seconds = int(summary.total_execution_time_ms / 1000)

        with open(filepath, "w", newline="") as f:
            writer = csv.writer(f)

            # Write header
            writer.writerow([
                "test_type",
                "app",
                "branch",
                "exec_date",
                "platform",
                "duration",
                "tc_count",
                "tc_pass",
                "tc_fail",
                "tc_critical_fail",
                "report_location",
                "owner"
            ])

            # Write single data row
            writer.writerow([
                "Data_Testing_Summary",
                app,
                branch,
                datetime.now().strftime("%Y-%m-%d"),
                platform,
                duration_seconds,
                summary.total_tests,
                summary.passed,
                summary.failed,
                summary.critical_failed,
                test_report_path,
                owner
            ])

        return str(filepath)


class FailedExecutionReporter:
    """Generates HTML report for failed test cases or all-passed message."""

    def __init__(self, output_dir: str = "./output"):
        """
        Initialize FailedExecution reporter.

        Args:
            output_dir: Directory to save FailedExecutionReport.html
        """
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def generate_report(self, results: List[Dict[str, Any]], summary: ExecutionSummary, metadata: Optional[ExecutionMetadata] = None) -> str:
        """
        Generate FailedExecutionReport.html with failed tests or all-passed message.

        Args:
            results: List of test results
            summary: ExecutionSummary instance
            metadata: Optional ExecutionMetadata instance with execution context

        Returns:
            Path to generated HTML file
        """
        filename = "FailedExecutionReport.html"
        filepath = self.output_dir / filename

        # Filter failed and error tests
        failed_tests = [r for r in results if r["status"] == "FAIL"]
        error_tests = [r for r in results if r["status"] == "ERROR"]
        all_problem_tests = failed_tests + error_tests

        if all_problem_tests:
            html_content = self._build_failed_tests_html(all_problem_tests, summary, metadata)
        else:
            html_content = self._build_all_passed_html(summary, metadata)

        with open(filepath, "w") as f:
            f.write(html_content)

        return str(filepath)

    def _build_failed_tests_html(self, failed_tests: List[Dict[str, Any]], summary: ExecutionSummary, metadata: Optional[ExecutionMetadata] = None) -> str:
        """Build HTML content for failed tests."""
        rows = []
        for result in failed_tests:
            execution_time = summary.format_duration(result.get("execution_time_ms", 0))
            status_class = "fail" if result["status"] == "FAIL" else "error"

            # Build error message display if error occurred
            error_display = ""
            if result.get("error_occurred"):
                error_type = result.get("error_type", "Unknown")
                error_msg = result.get("error_message", "Unknown")
                # Truncate long error messages for display
                if len(error_msg) > 100:
                    error_msg = error_msg[:97] + "..."
                error_display = f"<br/><small style='color: #c0392b; font-weight: bold;'>{error_type}: {error_msg}</small>"

            rows.append(
                f"""
                <tr class="{status_class}">
                    <td>{result['test_name']}</td>
                    <td>{result.get('severity', 'N/A')}</td>
                    <td>{self._safe_str(result.get('source_value'))}</td>
                    <td>{self._safe_str(result.get('target_value'))}</td>
                    <td>{result['status']}{error_display}</td>
                    <td>{execution_time}</td>
                </tr>
                """
            )

        rows_html = "\n".join(rows)

        # Build metadata section if available
        metadata_html = ""
        if metadata:
            metadata_html = f"""
    <details class="metadata-section">
        <summary>📋 Execution Metadata (Click to expand)</summary>
        <div class="metadata-content">
            <p><strong>Configuration File:</strong> {metadata.config_file}</p>
            <p><strong>Blocks Executed:</strong> {metadata.get_block_list()}</p>
            <p><strong>Test Script:</strong> {metadata.test_yaml_file}</p>
            <p><strong>Execution Time:</strong> {metadata.get_timestamp_str()}</p>
        </div>
    </details>
"""

        return f"""<!DOCTYPE html>
<html>
<head>
    <title>Failed Execution Report - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</title>
    <style>
        body {{
            font-family: Arial, sans-serif;
            margin: 20px;
            background-color: #f5f5f5;
        }}
        .header {{
            background-color: #c0392b;
            color: white;
            padding: 20px;
            border-radius: 5px;
            margin-bottom: 20px;
        }}
        .metadata-section {{
            background-color: #ecf0f1;
            padding: 15px;
            border-radius: 5px;
            margin-bottom: 20px;
            border-left: 4px solid #3498db;
        }}
        .metadata-section summary {{
            cursor: pointer;
            font-weight: bold;
            color: #2c3e50;
            user-select: none;
        }}
        .metadata-section summary:hover {{
            color: #3498db;
        }}
        .metadata-content {{
            margin-top: 15px;
            padding-top: 15px;
            border-top: 1px solid #bdc3c7;
        }}
        .metadata-content p {{
            margin: 8px 0;
            line-height: 1.6;
        }}
        .metadata-content strong {{
            color: #2c3e50;
            min-width: 150px;
            display: inline-block;
        }}
        .summary {{
            display: grid;
            grid-template-columns: repeat(4, 1fr);
            gap: 15px;
            margin-bottom: 20px;
        }}
        .summary-card {{
            background-color: white;
            padding: 15px;
            border-radius: 5px;
            box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
        }}
        .summary-card h3 {{
            margin: 0 0 10px 0;
            color: #2c3e50;
        }}
        .summary-card .value {{
            font-size: 24px;
            font-weight: bold;
            color: #c0392b;
        }}
        table {{
            width: 100%;
            border-collapse: collapse;
            background-color: white;
            box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
        }}
        th {{
            background-color: #c0392b;
            color: white;
            padding: 12px;
            text-align: left;
            border-bottom: 2px solid #a93226;
        }}
        td {{
            padding: 12px;
            border-bottom: 1px solid #ecf0f1;
        }}
        tr.fail {{
            background-color: #fadbd8;
        }}
        tr.error {{
            background-color: #fef5e7;
        }}
        tr:hover {{
            background-color: #f5b7b1;
        }}
    </style>
</head>
<body>
    <div class="header">
        <h1>⚠️ Failed Test Execution Report</h1>
        <p>Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
        <p>Total Problem Tests: <strong>{len(failed_tests)}</strong></p>
    </div>

    {metadata_html}

    <div class="summary">
        <div class="summary-card">
            <h3>Total Tests</h3>
            <div class="value">{summary.total_tests}</div>
        </div>
        <div class="summary-card">
            <h3>Passed</h3>
            <div class="value">{summary.passed}</div>
        </div>
        <div class="summary-card">
            <h3>Failed</h3>
            <div class="value">{summary.failed}</div>
        </div>
        <div class="summary-card">
            <h3>Errors</h3>
            <div class="value">{summary.error}</div>
        </div>
        <div class="summary-card">
            <h3>Invalid</h3>
            <div class="value">{summary.invalid}</div>
        </div>
        <div class="summary-card">
            <h3>Skipped</h3>
            <div class="value">{summary.skipped}</div>
        </div>
    </div>

    <table>
        <thead>
            <tr>
                <th>Test Name</th>
                <th>Severity</th>
                <th>Source Value</th>
                <th>Target Value</th>
                <th>Status</th>
                <th>Execution Time</th>
            </tr>
        </thead>
        <tbody>
            {rows_html}
        </tbody>
    </table>
</body>
</html>
"""

    def _build_all_passed_html(self, summary: ExecutionSummary, metadata: Optional[ExecutionMetadata] = None) -> str:
        """Build HTML content for all-passed message."""
        # Build metadata section if available
        metadata_html = ""
        if metadata:
            metadata_html = f"""
    <details class="metadata-section">
        <summary>📋 Execution Metadata (Click to expand)</summary>
        <div class="metadata-content">
            <p><strong>Configuration File:</strong> {metadata.config_file}</p>
            <p><strong>Blocks Executed:</strong> {metadata.get_block_list()}</p>
            <p><strong>Test Script:</strong> {metadata.test_yaml_file}</p>
            <p><strong>Execution Time:</strong> {metadata.get_timestamp_str()}</p>
        </div>
    </details>
"""

        return f"""<!DOCTYPE html>
<html>
<head>
    <title>Failed Execution Report - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</title>
    <style>
        body {{
            font-family: Arial, sans-serif;
            margin: 20px;
            background-color: #f5f5f5;
        }}
        .header {{
            background-color: #27ae60;
            color: white;
            padding: 40px;
            border-radius: 5px;
            margin-bottom: 20px;
            text-align: center;
        }}
        .header h1 {{
            font-size: 2.5em;
            margin: 10px 0;
        }}
        .metadata-section {{
            background-color: #ecf0f1;
            padding: 15px;
            border-radius: 5px;
            margin-bottom: 20px;
            border-left: 4px solid #3498db;
        }}
        .metadata-section summary {{
            cursor: pointer;
            font-weight: bold;
            color: #2c3e50;
            user-select: none;
        }}
        .metadata-section summary:hover {{
            color: #3498db;
        }}
        .metadata-content {{
            margin-top: 15px;
            padding-top: 15px;
            border-top: 1px solid #bdc3c7;
        }}
        .metadata-content p {{
            margin: 8px 0;
            line-height: 1.6;
        }}
        .metadata-content strong {{
            color: #2c3e50;
            min-width: 150px;
            display: inline-block;
        }}
        .summary {{
            display: grid;
            grid-template-columns: repeat(4, 1fr);
            gap: 15px;
            margin-bottom: 20px;
        }}
        .summary-card {{
            background-color: white;
            padding: 15px;
            border-radius: 5px;
            box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
        }}
        .summary-card h3 {{
            margin: 0 0 10px 0;
            color: #2c3e50;
        }}
        .summary-card .value {{
            font-size: 24px;
            font-weight: bold;
            color: #27ae60;
        }}
    </style>
</head>
<body>
    <div class="header">
        <h1>✅ All Tests Passed!</h1>
        <p>Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
        <p>No failed tests detected in this execution</p>
    </div>

    {metadata_html}

    <div class="summary">
        <div class="summary-card">
            <h3>Total Tests</h3>
            <div class="value">{summary.total_tests}</div>
        </div>
        <div class="summary-card">
            <h3>Passed</h3>
            <div class="value">{summary.passed}</div>
        </div>
        <div class="summary-card">
            <h3>Failed</h3>
            <div class="value">{summary.failed}</div>
        </div>
        <div class="summary-card">
            <h3>Invalid</h3>
            <div class="value">{summary.invalid}</div>
        </div>
    </div>
</body>
</html>
"""

    def _safe_str(self, value: Any) -> str:
        """Safely convert value to string for HTML."""
        if value is None:
            return "None"
        return str(value)
