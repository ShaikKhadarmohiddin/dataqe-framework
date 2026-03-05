"""
Tests for error handling and invalid test marking features.
"""
import unittest
import tempfile
import os
from unittest.mock import MagicMock, patch
from dataqe_framework.executor import ValidationExecutor, _should_skip_test
from dataqe_framework.reporter import ExecutionSummary
from dataqe_framework.preprocessor import QueryPreprocessor


class TestShouldSkipTest(unittest.TestCase):
    """Test cases for _should_skip_test function."""

    def test_skip_test_with_invalid_true(self):
        """Test that test with invalid=true is skipped."""
        test_config = {"invalid": True}
        self.assertTrue(_should_skip_test(test_config))

    def test_skip_test_with_invalid_false(self):
        """Test that test with invalid=false is not skipped."""
        test_config = {"invalid": False}
        self.assertFalse(_should_skip_test(test_config))

    def test_skip_test_without_invalid_field(self):
        """Test that test without invalid field is not skipped."""
        test_config = {"severity": "high"}
        self.assertFalse(_should_skip_test(test_config))


class TestExecutionSummaryErrorHandling(unittest.TestCase):
    """Test cases for ExecutionSummary with error and skipped statuses."""

    def test_summary_counts_errors(self):
        """Test that ExecutionSummary counts ERROR status tests."""
        results = [
            {"status": "PASS", "execution_time_ms": 100},
            {"status": "ERROR", "execution_time_ms": 100},
            {"status": "FAIL", "execution_time_ms": 100},
        ]
        summary = ExecutionSummary(results)
        self.assertEqual(summary.error, 1)

    def test_summary_counts_skipped(self):
        """Test that ExecutionSummary counts SKIPPED status tests."""
        results = [
            {"status": "PASS", "execution_time_ms": 100},
            {"status": "SKIPPED", "execution_time_ms": 0},
            {"status": "SKIPPED", "execution_time_ms": 0},
        ]
        summary = ExecutionSummary(results)
        self.assertEqual(summary.skipped, 2)

    def test_summary_total_tests_includes_all_statuses(self):
        """Test that total_tests includes all status types."""
        results = [
            {"status": "PASS", "execution_time_ms": 100},
            {"status": "FAIL", "execution_time_ms": 100},
            {"status": "ERROR", "execution_time_ms": 100},
            {"status": "SKIPPED", "execution_time_ms": 0},
        ]
        summary = ExecutionSummary(results)
        self.assertEqual(summary.total_tests, 4)
        self.assertEqual(summary.passed, 1)
        self.assertEqual(summary.failed, 1)
        self.assertEqual(summary.error, 1)
        self.assertEqual(summary.skipped, 1)


class TestValidationExecutorErrorHandling(unittest.TestCase):
    """Test cases for ValidationExecutor error handling."""

    def test_executor_catches_source_query_error(self):
        """Test that executor catches and handles source query errors."""
        # Mock test case
        test_cases = [
            {
                "ERROR_TEST": {
                    "severity": "high",
                    "source": {"query": "SELECT * FROM nonexistent_table"},
                    "comparisons": {}
                }
            }
        ]

        # Mock connector that raises an error
        mock_source_connector = MagicMock()
        mock_source_connector.execute_query.side_effect = Exception("Table not found")

        executor = ValidationExecutor({}, {}, test_cases)
        executor.source_connector = mock_source_connector
        executor.target_connector = None

        results = executor.run()

        # Verify error was caught
        self.assertEqual(len(results), 1)
        result = results[0]
        self.assertEqual(result["status"], "ERROR")
        self.assertEqual(result["error_type"], "Exception")
        self.assertTrue(result["error_occurred"])
        self.assertIn("Table not found", result["error_message"])

    def test_executor_continues_after_error(self):
        """Test that executor continues to next test after an error."""
        test_cases = [
            {
                "FAILING_TEST": {
                    "severity": "high",
                    "source": {"query": "SELECT * FROM nonexistent_table"},
                    "comparisons": {}
                }
            },
            {
                "SECOND_TEST": {
                    "severity": "high",
                    "source": {"query": "SELECT 1"},
                    "comparisons": {}
                }
            }
        ]

        # Mock connector: first query fails, second succeeds
        mock_connector = MagicMock()
        mock_connector.execute_query.side_effect = [
            Exception("First query failed"),
            [{"result": 1}]
        ]

        executor = ValidationExecutor({}, {}, test_cases)
        executor.source_connector = mock_connector
        executor.target_connector = None

        results = executor.run()

        # Both tests should be in results
        self.assertEqual(len(results), 2)
        # First has error
        self.assertEqual(results[0]["status"], "ERROR")
        # Second has a status (even if it can't complete comparison)
        self.assertIsNotNone(results[1]["status"])

    def test_result_includes_error_fields(self):
        """Test that error result includes error_type and error_message."""
        test_cases = [
            {
                "TEST": {
                    "severity": "high",
                    "source": {"query": "SELECT * FROM bad_table"},
                    "comparisons": {}
                }
            }
        ]

        mock_connector = MagicMock()
        error = ValueError("Invalid SQL syntax")
        mock_connector.execute_query.side_effect = error

        executor = ValidationExecutor({}, {}, test_cases)
        executor.source_connector = mock_connector

        results = executor.run()
        result = results[0]

        self.assertTrue(result["error_occurred"])
        self.assertEqual(result["error_type"], "ValueError")
        self.assertEqual(result["error_message"], "Invalid SQL syntax")
        self.assertIsNone(result["source_value"])
        self.assertIsNone(result["target_value"])


class TestPreprocessorErrorHandling(unittest.TestCase):
    """Test cases for preprocessor file validation."""

    def test_missing_preprocessor_file_raises_error(self):
        """Test that missing preprocessor file raises FileNotFoundError."""
        nonexistent_path = "/nonexistent/path/preprocessor_queries.yml"
        with self.assertRaises(FileNotFoundError) as context:
            QueryPreprocessor(nonexistent_path, {})

        # Check error message contains helpful information
        error_msg = str(context.exception)
        self.assertIn("not found", error_msg)
        self.assertIn(nonexistent_path, error_msg)

    def test_preprocessor_file_exists(self):
        """Test that preprocessor loads successfully when file exists."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yml', delete=False) as f:
            f.write("test_query: SELECT 1")
            temp_file = f.name

        try:
            preprocessor = QueryPreprocessor(temp_file, {})
            self.assertEqual(preprocessor.preprocessor_queries.get("test_query"), "SELECT 1")
        finally:
            os.unlink(temp_file)

    def test_invalid_yaml_file_raises_error(self):
        """Test that invalid YAML file raises RuntimeError."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yml', delete=False) as f:
            # Write invalid YAML
            f.write("invalid: : : yaml: content")
            temp_file = f.name

        try:
            with self.assertRaises(RuntimeError) as context:
                QueryPreprocessor(temp_file, {})

            error_msg = str(context.exception)
            self.assertIn("Error loading preprocessor queries", error_msg)
        finally:
            os.unlink(temp_file)


if __name__ == "__main__":
    unittest.main()
