"""
Tests for replacement tracking feature (v0.3.4+).

Tests that replacements are captured, stored in results, and displayed in reports.
"""
import unittest
import tempfile
import os
from unittest.mock import MagicMock, patch
from datetime import datetime
from pathlib import Path
from dataqe_framework.preprocessor import QueryPreprocessor
from dataqe_framework.executor import ValidationExecutor
from dataqe_framework.reporter import HTMLReporter, CSVReporter, FailedExecutionReporter, ExecutionSummary


class TestPreprocessorReplacementTracking(unittest.TestCase):
    """Test that preprocessor methods return replacement tracking info."""

    def test_replace_dataset_returns_tuple_with_replacements(self):
        """Test that replace_dataset_placeholders returns tuple with replacements."""
        preprocessor_config = {
            "replace_dataset": {
                "EDW_PRCD_PROJECT": "actual-edw"
            }
        }
        preprocessor = QueryPreprocessor(None, preprocessor_config)
        query = "SELECT * FROM EDW_PRCD_PROJECT.table_name"

        result, replacements = preprocessor.replace_dataset_placeholders(query)

        self.assertIsInstance(replacements, dict)
        self.assertEqual(replacements, {"EDW_PRCD_PROJECT": "actual-edw"})
        self.assertEqual(result, "SELECT * FROM actual-edw.table_name")

    def test_replace_dataset_empty_replacements_when_no_match(self):
        """Test that replace_dataset_placeholders returns empty dict when no match."""
        preprocessor_config = {
            "replace_dataset": {
                "EDW_PRCD_PROJECT": "actual-edw"
            }
        }
        preprocessor = QueryPreprocessor(None, preprocessor_config)
        query = "SELECT * FROM OTHER_PROJECT.table_name"

        result, replacements = preprocessor.replace_dataset_placeholders(query)

        self.assertEqual(replacements, {})
        self.assertEqual(result, query)

    def test_replace_dataset_multiple_placeholders_tracking(self):
        """Test that all replaced placeholders are tracked."""
        preprocessor_config = {
            "replace_dataset": {
                "EDW_PRCD_PROJECT": "actual-edw",
                "PD_CDW_METADATA": "actual-pd"
            }
        }
        preprocessor = QueryPreprocessor(None, preprocessor_config)
        query = "SELECT * FROM EDW_PRCD_PROJECT.table1 JOIN PD_CDW_METADATA.table2"

        result, replacements = preprocessor.replace_dataset_placeholders(query)

        self.assertEqual(replacements, {
            "EDW_PRCD_PROJECT": "actual-edw",
            "PD_CDW_METADATA": "actual-pd"
        })

    def test_replace_dataset_partial_match_tracking(self):
        """Test that only matched placeholders are tracked."""
        preprocessor_config = {
            "replace_dataset": {
                "EDW_PRCD_PROJECT": "actual-edw",
                "PD_CDW_METADATA": "actual-pd"
            }
        }
        preprocessor = QueryPreprocessor(None, preprocessor_config)
        query = "SELECT * FROM EDW_PRCD_PROJECT.table1"

        result, replacements = preprocessor.replace_dataset_placeholders(query)

        self.assertEqual(replacements, {"EDW_PRCD_PROJECT": "actual-edw"})

    def test_replace_release_labels_returns_tuple_with_replacements(self):
        """Test that replace_release_labels returns tuple with replacements."""
        preprocessor_config = {
            "config_query_key": "test_query"
        }
        preprocessor_queries = {
            "test_query": "SELECT 'bcbsa' as source, 'bcbsa_export1' as current_release, 'bcbsa_export0' as previous_release"
        }

        with tempfile.NamedTemporaryFile(mode='w', suffix='.yml', delete=False) as f:
            import yaml
            yaml.dump(preprocessor_queries, f)
            temp_file = f.name

        try:
            preprocessor = QueryPreprocessor(temp_file, preprocessor_config)

            # Mock connector
            mock_connector = MagicMock()
            mock_connector.execute_query.return_value = [
                {"source": "bcbsa", "current_release": "bcbsa_export1", "previous_release": "bcbsa_export0"}
            ]

            query = "SELECT * FROM BCBSA_CURR_WEEK"
            result, replacements = preprocessor.replace_release_labels(query, mock_connector)

            self.assertIsInstance(replacements, dict)
            self.assertEqual(replacements, {"BCBSA_CURR_WEEK": "bcbsa_export1"})
            self.assertEqual(result, "SELECT * FROM bcbsa_export1")
        finally:
            os.unlink(temp_file)

    def test_replace_release_labels_multiple_sources(self):
        """Test that multiple sources are tracked in replacements."""
        preprocessor_config = {
            "config_query_key": "test_query"
        }
        preprocessor_queries = {
            "test_query": "SELECT source, current_release, previous_release"
        }

        with tempfile.NamedTemporaryFile(mode='w', suffix='.yml', delete=False) as f:
            import yaml
            yaml.dump(preprocessor_queries, f)
            temp_file = f.name

        try:
            preprocessor = QueryPreprocessor(temp_file, preprocessor_config)

            mock_connector = MagicMock()
            mock_connector.execute_query.return_value = [
                {"source": "bcbsa", "current_release": "bcbsa_export1", "previous_release": "bcbsa_export0"},
                {"source": "src2", "current_release": "src2_v5", "previous_release": "src2_v4"}
            ]

            query = "SELECT * FROM BCBSA_CURR_WEEK JOIN SRC2_PREV_WEEK"
            result, replacements = preprocessor.replace_release_labels(query, mock_connector)

            self.assertEqual(replacements, {
                "BCBSA_CURR_WEEK": "bcbsa_export1",
                "SRC2_PREV_WEEK": "src2_v4"
            })
        finally:
            os.unlink(temp_file)


class TestExecutorReplacementCapture(unittest.TestCase):
    """Test that executor captures replacements in results."""

    def test_executor_captures_dataset_replacements_in_result(self):
        """Test that executor stores dataset replacements in result_dict."""
        source_config = {
            "database_type": "gcpbq",
            "gcp": {
                "replace_dataset": {
                    "EDW_PRCD_PROJECT": "actual-edw"
                }
            }
        }
        target_config = None

        test_cases = [
            {
                "test_1": {
                    "source": {
                        "query": "SELECT * FROM EDW_PRCD_PROJECT.table_name"
                    }
                }
            }
        ]

        mock_source_connector = MagicMock()
        mock_source_connector.execute_query.return_value = [{"count": 10}]

        executor = ValidationExecutor(source_config, target_config, test_cases)
        executor.source_connector = mock_source_connector
        executor.target_connector = None

        results = executor.run()

        self.assertEqual(len(results), 1)
        self.assertIn("replacements", results[0])
        self.assertIn("dataset_placeholders", results[0]["replacements"])
        self.assertEqual(
            results[0]["replacements"]["dataset_placeholders"],
            {"EDW_PRCD_PROJECT": "actual-edw"}
        )

    def test_executor_merges_source_and_target_replacements(self):
        """Test that executor merges replacements from both source and target."""
        source_config = {
            "database_type": "gcpbq",
            "gcp": {
                "replace_dataset": {
                    "EDW_PRCD_PROJECT": "actual-edw"
                }
            }
        }
        target_config = {
            "database_type": "gcpbq",
            "gcp": {
                "replace_dataset": {
                    "PD_CDW_METADATA": "actual-pd"
                }
            }
        }

        test_cases = [
            {
                "test_1": {
                    "source": {
                        "query": "SELECT * FROM EDW_PRCD_PROJECT.table_name"
                    },
                    "target": {
                        "query": "SELECT * FROM PD_CDW_METADATA.table_name"
                    }
                }
            }
        ]

        mock_source_connector = MagicMock()
        mock_source_connector.execute_query.return_value = [{"count": 10}]

        mock_target_connector = MagicMock()
        mock_target_connector.execute_query.return_value = [{"count": 10}]

        executor = ValidationExecutor(source_config, target_config, test_cases)
        # Skip setup_connectors which would try to create real connectors
        executor.source_connector = mock_source_connector
        executor.target_connector = mock_target_connector
        # Patch setup_connectors to do nothing
        with patch.object(executor, 'setup_connectors'):
            results = executor.run()

        self.assertEqual(len(results), 1)
        replacements = results[0]["replacements"]
        self.assertIn("EDW_PRCD_PROJECT", replacements["dataset_placeholders"])
        self.assertIn("PD_CDW_METADATA", replacements["dataset_placeholders"])

    def test_executor_empty_replacements_when_none(self):
        """Test that executor includes empty replacements dict when no replacements."""
        source_config = {
            "database_type": "gcpbq",
            "gcp": {}
        }
        target_config = None

        test_cases = [
            {
                "test_1": {
                    "source": {
                        "query": "SELECT * FROM table_name"
                    }
                }
            }
        ]

        mock_source_connector = MagicMock()
        mock_source_connector.execute_query.return_value = [{"count": 10}]

        executor = ValidationExecutor(source_config, target_config, test_cases)
        executor.source_connector = mock_source_connector
        executor.target_connector = None

        results = executor.run()

        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]["replacements"]["dataset_placeholders"], {})
        self.assertEqual(results[0]["replacements"]["release_labels"], {})


class TestHTMLReporterReplacementDisplay(unittest.TestCase):
    """Test that HTMLReporter displays replacements."""

    def test_html_report_includes_replacements_details(self):
        """Test that HTML report includes collapsible replacements section."""
        with tempfile.TemporaryDirectory() as tmpdir:
            reporter = HTMLReporter(tmpdir)

            results = [
                {
                    "test_name": "test_1",
                    "severity": "high",
                    "source_value": 10,
                    "target_value": 10,
                    "status": "PASS",
                    "start_time": datetime.now(),
                    "end_time": datetime.now(),
                    "execution_time_ms": 100.0,
                    "source_query_time_ms": 50.0,
                    "target_query_time_ms": 50.0,
                    "comparison_time_ms": 0.0,
                    "script_name": "test",
                    "error_occurred": False,
                    "error_type": None,
                    "error_message": None,
                    "replacements": {
                        "dataset_placeholders": {"EDW_PRCD_PROJECT": "actual-edw"},
                        "release_labels": {}
                    }
                }
            ]

            summary = ExecutionSummary(results)
            html_path = reporter.generate_report(results, summary)

            with open(html_path, 'r') as f:
                html_content = f.read()

            self.assertIn("🔄 Replacements", html_content)
            self.assertIn("EDW_PRCD_PROJECT", html_content)
            self.assertIn("actual-edw", html_content)
            self.assertIn("<details", html_content)

    def test_html_report_shows_dataset_and_release_labels(self):
        """Test that HTML report shows both dataset and release label replacements."""
        with tempfile.TemporaryDirectory() as tmpdir:
            reporter = HTMLReporter(tmpdir)

            results = [
                {
                    "test_name": "test_1",
                    "severity": "high",
                    "source_value": 10,
                    "target_value": 10,
                    "status": "PASS",
                    "start_time": datetime.now(),
                    "end_time": datetime.now(),
                    "execution_time_ms": 100.0,
                    "source_query_time_ms": 50.0,
                    "target_query_time_ms": 50.0,
                    "comparison_time_ms": 0.0,
                    "script_name": "test",
                    "error_occurred": False,
                    "error_type": None,
                    "error_message": None,
                    "replacements": {
                        "dataset_placeholders": {"EDW_PRCD_PROJECT": "actual-edw"},
                        "release_labels": {"BCBSA_CURR_WEEK": "bcbsa_export1"}
                    }
                }
            ]

            summary = ExecutionSummary(results)
            html_path = reporter.generate_report(results, summary)

            with open(html_path, 'r') as f:
                html_content = f.read()

            self.assertIn("Dataset Placeholders:", html_content)
            self.assertIn("Release Labels:", html_content)
            self.assertIn("EDW_PRCD_PROJECT", html_content)
            self.assertIn("BCBSA_CURR_WEEK", html_content)

    def test_html_report_without_replacements(self):
        """Test that HTML report works without replacements."""
        with tempfile.TemporaryDirectory() as tmpdir:
            reporter = HTMLReporter(tmpdir)

            results = [
                {
                    "test_name": "test_1",
                    "severity": "high",
                    "source_value": 10,
                    "target_value": 10,
                    "status": "PASS",
                    "start_time": datetime.now(),
                    "end_time": datetime.now(),
                    "execution_time_ms": 100.0,
                    "source_query_time_ms": 50.0,
                    "target_query_time_ms": 50.0,
                    "comparison_time_ms": 0.0,
                    "script_name": "test",
                    "error_occurred": False,
                    "error_type": None,
                    "error_message": None,
                    "replacements": {"dataset_placeholders": {}, "release_labels": {}}
                }
            ]

            summary = ExecutionSummary(results)
            html_path = reporter.generate_report(results, summary)

            with open(html_path, 'r') as f:
                html_content = f.read()

            # Should not have replacement details if empty
            self.assertIn("Test Execution Report", html_content)


class TestCSVReporterReplacementDisplay(unittest.TestCase):
    """Test that CSVReporter displays replacements."""

    def test_csv_report_includes_replacements_column(self):
        """Test that CSV report includes replacements column."""
        with tempfile.TemporaryDirectory() as tmpdir:
            reporter = CSVReporter(tmpdir)

            results = [
                {
                    "test_name": "test_1",
                    "severity": "high",
                    "source_value": 10,
                    "target_value": 10,
                    "status": "PASS",
                    "start_time": datetime.now(),
                    "end_time": datetime.now(),
                    "execution_time_ms": 100.0,
                    "source_query_time_ms": 50.0,
                    "target_query_time_ms": 50.0,
                    "comparison_time_ms": 0.0,
                    "script_name": "test",
                    "error_occurred": False,
                    "error_type": None,
                    "error_message": None,
                    "replacements": {
                        "dataset_placeholders": {"EDW_PRCD_PROJECT": "actual-edw"},
                        "release_labels": {}
                    }
                }
            ]

            summary = ExecutionSummary(results)
            csv_path = reporter.generate_report(results, summary)

            with open(csv_path, 'r') as f:
                csv_content = f.read()

            self.assertIn("Replacements", csv_content)
            self.assertIn("EDW_PRCD_PROJECT→actual-edw", csv_content)

    def test_csv_report_multiple_replacements_semicolon_separated(self):
        """Test that multiple replacements are semicolon-separated in CSV."""
        with tempfile.TemporaryDirectory() as tmpdir:
            reporter = CSVReporter(tmpdir)

            results = [
                {
                    "test_name": "test_1",
                    "severity": "high",
                    "source_value": 10,
                    "target_value": 10,
                    "status": "PASS",
                    "start_time": datetime.now(),
                    "end_time": datetime.now(),
                    "execution_time_ms": 100.0,
                    "source_query_time_ms": 50.0,
                    "target_query_time_ms": 50.0,
                    "comparison_time_ms": 0.0,
                    "script_name": "test",
                    "error_occurred": False,
                    "error_type": None,
                    "error_message": None,
                    "replacements": {
                        "dataset_placeholders": {"EDW_PRCD_PROJECT": "actual-edw", "PD_CDW": "actual-pd"},
                        "release_labels": {"BCBSA_CURR_WEEK": "bcbsa_export1"}
                    }
                }
            ]

            summary = ExecutionSummary(results)
            csv_path = reporter.generate_report(results, summary)

            with open(csv_path, 'r') as f:
                csv_content = f.read()

            # All three replacements should be present
            self.assertIn("EDW_PRCD_PROJECT→actual-edw", csv_content)
            self.assertIn("PD_CDW→actual-pd", csv_content)
            self.assertIn("BCBSA_CURR_WEEK→bcbsa_export1", csv_content)


class TestFailedExecutionReporterReplacementDisplay(unittest.TestCase):
    """Test that FailedExecutionReporter displays replacements."""

    def test_failed_report_includes_replacements_for_failed_tests(self):
        """Test that failed execution report includes replacements for failed tests."""
        with tempfile.TemporaryDirectory() as tmpdir:
            reporter = FailedExecutionReporter(tmpdir)

            results = [
                {
                    "test_name": "test_1",
                    "severity": "high",
                    "source_value": 10,
                    "target_value": 11,
                    "status": "FAIL",
                    "start_time": datetime.now(),
                    "end_time": datetime.now(),
                    "execution_time_ms": 100.0,
                    "source_query_time_ms": 50.0,
                    "target_query_time_ms": 50.0,
                    "comparison_time_ms": 0.0,
                    "script_name": "test",
                    "error_occurred": False,
                    "error_type": None,
                    "error_message": None,
                    "replacements": {
                        "dataset_placeholders": {"EDW_PRCD_PROJECT": "actual-edw"},
                        "release_labels": {}
                    }
                }
            ]

            summary = ExecutionSummary(results)
            html_path = reporter.generate_report(results, summary)

            with open(html_path, 'r') as f:
                html_content = f.read()

            self.assertIn("🔄 Replacements", html_content)
            self.assertIn("EDW_PRCD_PROJECT", html_content)
            self.assertIn("actual-edw", html_content)

    def test_all_passed_report_works_without_replacements(self):
        """Test that all-passed report works without replacements."""
        with tempfile.TemporaryDirectory() as tmpdir:
            reporter = FailedExecutionReporter(tmpdir)

            results = [
                {
                    "test_name": "test_1",
                    "severity": "high",
                    "source_value": 10,
                    "target_value": 10,
                    "status": "PASS",
                    "start_time": datetime.now(),
                    "end_time": datetime.now(),
                    "execution_time_ms": 100.0,
                    "source_query_time_ms": 50.0,
                    "target_query_time_ms": 50.0,
                    "comparison_time_ms": 0.0,
                    "script_name": "test",
                    "error_occurred": False,
                    "error_type": None,
                    "error_message": None,
                    "replacements": {"dataset_placeholders": {}, "release_labels": {}}
                }
            ]

            summary = ExecutionSummary(results)
            html_path = reporter.generate_report(results, summary)

            with open(html_path, 'r') as f:
                html_content = f.read()

            # Should display all passed message
            self.assertIn("All Tests Passed", html_content)


class TestBackwardCompatibilityReplacements(unittest.TestCase):
    """Test backward compatibility for replacement tracking."""

    def test_result_without_replacements_field_still_works(self):
        """Test that reporters work with results missing 'replacements' field."""
        with tempfile.TemporaryDirectory() as tmpdir:
            reporter = HTMLReporter(tmpdir)

            # Old-format result without replacements field
            results = [
                {
                    "test_name": "test_1",
                    "severity": "high",
                    "source_value": 10,
                    "target_value": 10,
                    "status": "PASS",
                    "start_time": datetime.now(),
                    "end_time": datetime.now(),
                    "execution_time_ms": 100.0,
                    "source_query_time_ms": 50.0,
                    "target_query_time_ms": 50.0,
                    "comparison_time_ms": 0.0,
                    "script_name": "test",
                    "error_occurred": False,
                    "error_type": None,
                    "error_message": None
                    # No 'replacements' field
                }
            ]

            summary = ExecutionSummary(results)
            # Should not raise error
            html_path = reporter.generate_report(results, summary)

            with open(html_path, 'r') as f:
                html_content = f.read()

            self.assertIn("Test Execution Report", html_content)

    def test_csv_reporter_handles_missing_replacements_field(self):
        """Test that CSV reporter handles missing replacements field."""
        with tempfile.TemporaryDirectory() as tmpdir:
            reporter = CSVReporter(tmpdir)

            # Old-format result without replacements field
            results = [
                {
                    "test_name": "test_1",
                    "severity": "high",
                    "source_value": 10,
                    "target_value": 10,
                    "status": "PASS",
                    "start_time": datetime.now(),
                    "end_time": datetime.now(),
                    "execution_time_ms": 100.0,
                    "source_query_time_ms": 50.0,
                    "target_query_time_ms": 50.0,
                    "comparison_time_ms": 0.0,
                    "script_name": "test",
                    "error_occurred": False,
                    "error_type": None,
                    "error_message": None
                }
            ]

            summary = ExecutionSummary(results)
            # Should not raise error
            csv_path = reporter.generate_report(results, summary)

            with open(csv_path, 'r') as f:
                csv_content = f.read()

            self.assertIn("Test Name", csv_content)


if __name__ == '__main__':
    unittest.main()
