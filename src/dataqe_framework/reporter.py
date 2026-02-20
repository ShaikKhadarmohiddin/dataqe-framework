import logging
import csv
from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Dict, Any


logger = logging.getLogger(__name__)


class ExecutionSummary:
    """Aggregates test execution results and calculates summary metrics."""

    def __init__(self, results: List[Dict[str, Any]]):
        """
        Initialize summary with test results.

        Args:
            results: List of test result dictionaries from ValidationExecutor
        """
        self.results = results
        self.total_tests = len(results)
        self.passed = sum(1 for r in results if r["status"] == "PASS")
        self.failed = sum(1 for r in results if r["status"] == "FAIL")
        self.invalid = sum(1 for r in results if r["status"] == "INVALID")
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

        self.logger.info(f"Test: {test_name} - Status: {status} (Execution time: {formatted_time})")

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
        self.logger.info(f"Invalid: {summary.invalid}")

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

    def generate_report(self, results: List[Dict[str, Any]], summary: ExecutionSummary) -> str:
        """
        Generate HTML report and save to file as ExecutionReport.html.

        Args:
            results: List of test results
            summary: ExecutionSummary instance

        Returns:
            Path to generated HTML file
        """
        filename = "ExecutionReport.html"
        filepath = self.output_dir / filename

        html_content = self._build_html(results, summary)

        with open(filepath, "w") as f:
            f.write(html_content)

        return str(filepath)

    def _build_html(self, results: List[Dict[str, Any]], summary: ExecutionSummary) -> str:
        """Build HTML content for the report."""
        rows = []
        for result in results:
            status_class = self._get_status_class(result["status"])
            execution_time = summary.format_duration(result.get("execution_time_ms", 0))
            rows.append(
                f"""
                <tr class="{status_class}">
                    <td>{result['test_name']}</td>
                    <td>{result.get('severity', 'N/A')}</td>
                    <td>{self._safe_str(result.get('source_value'))}</td>
                    <td>{self._safe_str(result.get('target_value'))}</td>
                    <td>{result['status']}</td>
                    <td>{execution_time}</td>
                </tr>
                """
            )

        rows_html = "\n".join(rows)

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
            <h3>Invalid</h3>
            <div class="value">{summary.invalid}</div>
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
            "INVALID": "invalid"
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

    def generate_report(self, results: List[Dict[str, Any]], summary: ExecutionSummary) -> str:
        """
        Generate CSV report and save to file as ExecutionReport.csv.

        Args:
            results: List of test results
            summary: ExecutionSummary instance

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
                "Execution Time (ms)",
                "Source Query Time (ms)",
                "Target Query Time (ms)",
                "Comparison Time (ms)"
            ])

            # Write test results
            for result in results:
                writer.writerow([
                    result["test_name"],
                    result.get("severity", "N/A"),
                    result.get("source_value"),
                    result.get("target_value"),
                    result["status"],
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
            writer.writerow(["Invalid", summary.invalid])
            writer.writerow(["Total Execution Time (ms)", f"{summary.total_execution_time_ms:.2f}"])

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

    def generate_report(self, results: List[Dict[str, Any]], summary: ExecutionSummary) -> str:
        """
        Generate FailedExecutionReport.html with failed tests or all-passed message.

        Args:
            results: List of test results
            summary: ExecutionSummary instance

        Returns:
            Path to generated HTML file
        """
        filename = "FailedExecutionReport.html"
        filepath = self.output_dir / filename

        # Filter failed tests
        failed_tests = [r for r in results if r["status"] == "FAIL"]

        if failed_tests:
            html_content = self._build_failed_tests_html(failed_tests, summary)
        else:
            html_content = self._build_all_passed_html(summary)

        with open(filepath, "w") as f:
            f.write(html_content)

        return str(filepath)

    def _build_failed_tests_html(self, failed_tests: List[Dict[str, Any]], summary: ExecutionSummary) -> str:
        """Build HTML content for failed tests."""
        rows = []
        for result in failed_tests:
            execution_time = summary.format_duration(result.get("execution_time_ms", 0))
            rows.append(
                f"""
                <tr class="fail">
                    <td>{result['test_name']}</td>
                    <td>{result.get('severity', 'N/A')}</td>
                    <td>{self._safe_str(result.get('source_value'))}</td>
                    <td>{self._safe_str(result.get('target_value'))}</td>
                    <td>{result['status']}</td>
                    <td>{execution_time}</td>
                </tr>
                """
            )

        rows_html = "\n".join(rows)

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
        tr:hover {{
            background-color: #f5b7b1;
        }}
    </style>
</head>
<body>
    <div class="header">
        <h1>⚠️ Failed Test Execution Report</h1>
        <p>Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
        <p>Total Failed Tests: <strong>{len(failed_tests)}</strong></p>
    </div>

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

    def _build_all_passed_html(self, summary: ExecutionSummary) -> str:
        """Build HTML content for all-passed message."""
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
