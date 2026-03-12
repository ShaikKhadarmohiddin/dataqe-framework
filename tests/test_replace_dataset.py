"""
Tests for replace_dataset feature.
"""
import unittest
import tempfile
import os
from unittest.mock import MagicMock, patch
from dataqe_framework.preprocessor import QueryPreprocessor
from dataqe_framework.executor import ValidationExecutor


class TestReplaceDatasetPlaceholders(unittest.TestCase):
    """Test cases for replace_dataset_placeholders method."""

    def test_replace_single_placeholder(self):
        """Test replacing a single dataset placeholder."""
        preprocessor_config = {
            "replace_dataset": {
                "EDW_PRCD_PROJECT": "actual-project-id-edw"
            }
        }
        preprocessor = QueryPreprocessor(None, preprocessor_config)

        query = "SELECT * FROM EDW_PRCD_PROJECT.table_name"
        result = preprocessor.replace_dataset_placeholders(query)

        self.assertEqual(result, "SELECT * FROM actual-project-id-edw.table_name")

    def test_replace_multiple_placeholders(self):
        """Test replacing multiple dataset placeholders in same query."""
        preprocessor_config = {
            "replace_dataset": {
                "EDW_PRCD_PROJECT": "actual-project-id-edw",
                "PD_CDW_METADATA": "actual-project-id-pd"
            }
        }
        preprocessor = QueryPreprocessor(None, preprocessor_config)

        query = """
            SELECT * FROM EDW_PRCD_PROJECT.table1
            UNION ALL
            SELECT * FROM PD_CDW_METADATA.table2
        """
        result = preprocessor.replace_dataset_placeholders(query)

        self.assertIn("actual-project-id-edw.table1", result)
        self.assertIn("actual-project-id-pd.table2", result)
        self.assertNotIn("EDW_PRCD_PROJECT", result)
        self.assertNotIn("PD_CDW_METADATA", result)

    def test_replace_with_empty_config(self):
        """Test that query is unchanged with empty replace_dataset config."""
        preprocessor_config = {"replace_dataset": {}}
        preprocessor = QueryPreprocessor(None, preprocessor_config)

        query = "SELECT * FROM EDW_PRCD_PROJECT.table_name"
        result = preprocessor.replace_dataset_placeholders(query)

        self.assertEqual(result, query)

    def test_replace_with_no_config(self):
        """Test that query is unchanged with no replace_dataset config."""
        preprocessor_config = {}
        preprocessor = QueryPreprocessor(None, preprocessor_config)

        query = "SELECT * FROM EDW_PRCD_PROJECT.table_name"
        result = preprocessor.replace_dataset_placeholders(query)

        self.assertEqual(result, query)

    def test_replace_with_none_config(self):
        """Test that query is unchanged with None config."""
        preprocessor = QueryPreprocessor(None, None)

        query = "SELECT * FROM EDW_PRCD_PROJECT.table_name"
        result = preprocessor.replace_dataset_placeholders(query)

        self.assertEqual(result, query)

    def test_replace_multiple_occurrences_of_same_placeholder(self):
        """Test replacing multiple occurrences of same placeholder."""
        preprocessor_config = {
            "replace_dataset": {
                "EDW_PRCD_PROJECT": "actual-edw"
            }
        }
        preprocessor = QueryPreprocessor(None, preprocessor_config)

        query = """
            SELECT a.* FROM EDW_PRCD_PROJECT.table1 a
            JOIN EDW_PRCD_PROJECT.table2 b ON a.id = b.id
        """
        result = preprocessor.replace_dataset_placeholders(query)

        self.assertEqual(result.count("actual-edw"), 2)
        self.assertNotIn("EDW_PRCD_PROJECT", result)

    def test_replace_with_complex_project_ids(self):
        """Test replacing with complex project IDs containing hyphens and numbers."""
        preprocessor_config = {
            "replace_dataset": {
                "PLACEHOLDER_1": "my-project-prod-2024-q1",
                "PLACEHOLDER_2": "data_lake_v2_staging"
            }
        }
        preprocessor = QueryPreprocessor(None, preprocessor_config)

        query = "SELECT * FROM PLACEHOLDER_1.dataset1 UNION ALL SELECT * FROM PLACEHOLDER_2.dataset2"
        result = preprocessor.replace_dataset_placeholders(query)

        self.assertIn("my-project-prod-2024-q1", result)
        self.assertIn("data_lake_v2_staging", result)

    def test_replace_preserves_non_matching_text(self):
        """Test that non-matching text is preserved."""
        preprocessor_config = {
            "replace_dataset": {
                "EDW_PRCD_PROJECT": "actual-edw"
            }
        }
        preprocessor = QueryPreprocessor(None, preprocessor_config)

        query = """
            SELECT 'EDW_PRCD_PROJECT' AS comment,
                   col1,
                   col2
            FROM EDW_PRCD_PROJECT.table_name
            WHERE description LIKE '%EDW_PRCD_PROJECT%'
        """
        result = preprocessor.replace_dataset_placeholders(query)

        # The string literal and LIKE pattern should also be replaced (expected behavior)
        self.assertIn("actual-edw.table_name", result)

    def test_replace_case_sensitivity(self):
        """Test that replacement handles case variations."""
        preprocessor_config = {
            "replace_dataset": {
                "EDW_PRCD_PROJECT": "actual-edw"
            }
        }
        preprocessor = QueryPreprocessor(None, preprocessor_config)

        # Test with uppercase (should match)
        query_upper = "SELECT * FROM EDW_PRCD_PROJECT.table_name"
        result_upper = preprocessor.replace_dataset_placeholders(query_upper)
        self.assertIn("actual-edw", result_upper)


class TestExecutorExtractPreprocessorConfig(unittest.TestCase):
    """Test cases for _extract_preprocessor_config method."""

    def test_extract_config_query_key_only(self):
        """Test extracting config_query_key from GCP config."""
        config = {
            "database_type": "gcpbq",
            "gcp": {
                "project_id": "my-project",
                "config_query_key": "get_releases"
            }
        }
        executor = ValidationExecutor(config, {}, [])
        result = executor._extract_preprocessor_config(config)

        self.assertEqual(result.get("config_query_key"), "get_releases")
        self.assertNotIn("replace_dataset", result)

    def test_extract_replace_dataset_only(self):
        """Test extracting replace_dataset from config."""
        config = {
            "database_type": "gcpbq",
            "gcp": {
                "project_id": "my-project",
                "replace_dataset": {
                    "EDW_PRCD_PROJECT": "actual-edw"
                }
            }
        }
        executor = ValidationExecutor(config, {}, [])
        result = executor._extract_preprocessor_config(config)

        self.assertIn("replace_dataset", result)
        self.assertEqual(result["replace_dataset"]["EDW_PRCD_PROJECT"], "actual-edw")
        self.assertNotIn("config_query_key", result)

    def test_extract_both_config_query_key_and_replace_dataset(self):
        """Test extracting both config_query_key and replace_dataset."""
        config = {
            "database_type": "gcpbq",
            "gcp": {
                "project_id": "my-project",
                "config_query_key": "get_releases",
                "replace_dataset": {
                    "EDW_PRCD_PROJECT": "actual-edw"
                }
            }
        }
        executor = ValidationExecutor(config, {}, [])
        result = executor._extract_preprocessor_config(config)

        self.assertEqual(result.get("config_query_key"), "get_releases")
        self.assertIn("replace_dataset", result)

    def test_extract_mysql_replace_dataset(self):
        """Test extracting replace_dataset from MySQL config."""
        config = {
            "database_type": "mysql",
            "mysql": {
                "host": "localhost",
                "replace_dataset": {
                    "PROD_DB": "staging_db"
                }
            }
        }
        executor = ValidationExecutor(config, {}, [])
        result = executor._extract_preprocessor_config(config)

        self.assertIn("replace_dataset", result)
        self.assertEqual(result["replace_dataset"]["PROD_DB"], "staging_db")

    def test_extract_with_invalid_replace_dataset_type(self):
        """Test that non-dict replace_dataset is ignored."""
        config = {
            "database_type": "gcpbq",
            "gcp": {
                "project_id": "my-project",
                "replace_dataset": "invalid_string"
            }
        }
        executor = ValidationExecutor(config, {}, [])
        result = executor._extract_preprocessor_config(config)

        self.assertNotIn("replace_dataset", result)

    def test_extract_with_empty_config(self):
        """Test extracting from empty config."""
        executor = ValidationExecutor({}, {}, [])
        result = executor._extract_preprocessor_config({})

        self.assertEqual(result, {})

    def test_extract_with_none_config(self):
        """Test extracting from None config."""
        executor = ValidationExecutor({}, {}, [])
        result = executor._extract_preprocessor_config(None)

        self.assertEqual(result, {})


class TestPreprocessorIntegration(unittest.TestCase):
    """Integration tests for preprocessor with replace_dataset."""

    def test_dataset_replacement_before_release_labels(self):
        """Test that dataset replacement happens before release label replacement."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yml', delete=False) as f:
            f.write("""
get_releases:
  SELECT 'my_source' as source, 'release_v1' as current_release, 'release_v0' as previous_release
""")
            temp_file = f.name

        try:
            preprocessor_config = {
                "config_query_key": "get_releases",
                "replace_dataset": {
                    "EDW_PRCD_PROJECT": "actual-edw"
                }
            }
            preprocessor = QueryPreprocessor(temp_file, preprocessor_config)

            query = "SELECT * FROM EDW_PRCD_PROJECT.MY_SOURCE_CURR_WEEK"

            # Mock connector
            mock_connector = MagicMock()
            mock_connector.execute_query.return_value = [
                {"source": "my_source", "current_release": "release_v1", "previous_release": "release_v0"}
            ]

            # First replace dataset placeholders
            query_after_dataset = preprocessor.replace_dataset_placeholders(query)
            self.assertIn("actual-edw", query_after_dataset)
            self.assertNotIn("EDW_PRCD_PROJECT", query_after_dataset)

            # Then replace release labels
            query_after_labels = preprocessor.replace_release_labels(query_after_dataset, mock_connector)
            self.assertIn("actual-edw", query_after_labels)
            self.assertIn("release_v1", query_after_labels)
        finally:
            os.unlink(temp_file)

    @patch('dataqe_framework.executor.get_connector')
    def test_executor_processes_dataset_replacement(self, mock_get_connector):
        """Test that executor processes dataset replacement in query."""
        test_cases = [
            {
                "TEST": {
                    "severity": "high",
                    "source": {"query": "SELECT * FROM EDW_PRCD_PROJECT.table_name"},
                    "comparisons": {}
                }
            }
        ]

        source_config = {
            "database_type": "gcpbq",
            "gcp": {
                "project_id": "my-project",
                "replace_dataset": {
                    "EDW_PRCD_PROJECT": "actual-edw"
                }
            }
        }

        # Mock connector
        mock_connector = MagicMock()
        mock_connector.execute_query.return_value = [{"result": 42}]
        mock_get_connector.return_value = mock_connector

        executor = ValidationExecutor(source_config, {}, test_cases)

        # Test that preprocessor config was extracted correctly
        self.assertIsNotNone(executor.source_preprocessor)

        # Run test
        results = executor.run()

        # Verify that the processed query was called (with replacement)
        self.assertEqual(len(results), 1)
        # The mock should have been called with the processed query
        mock_connector.execute_query.assert_called()

        # Get the actual query that was passed to execute_query
        called_query = mock_connector.execute_query.call_args[0][0]
        # The query should have the placeholder replaced
        self.assertIn("actual-edw", called_query)


class TestBackwardCompatibility(unittest.TestCase):
    """Test backward compatibility of replace_dataset feature."""

    def test_config_without_replace_dataset_still_works(self):
        """Test that old configs without replace_dataset work normally."""
        config = {
            "database_type": "gcpbq",
            "gcp": {
                "project_id": "my-project",
                "config_query_key": "get_releases"
            }
        }
        executor = ValidationExecutor(config, {}, [])
        extracted = executor._extract_preprocessor_config(config)

        # Should have config_query_key but not replace_dataset
        self.assertIn("config_query_key", extracted)
        self.assertNotIn("replace_dataset", extracted)

    def test_preprocessor_without_replace_dataset_config(self):
        """Test preprocessor works when replace_dataset is not configured."""
        preprocessor = QueryPreprocessor(None, {"config_query_key": "some_key"})
        query = "SELECT * FROM EDW_PRCD_PROJECT.table_name"

        # Should return original query unchanged
        result = preprocessor.replace_dataset_placeholders(query)
        self.assertEqual(result, query)

    @patch('dataqe_framework.executor.get_connector')
    def test_executor_with_no_preprocessor_path(self, mock_get_connector):
        """Test executor works without preprocessor queries file."""
        test_cases = [
            {
                "TEST": {
                    "severity": "high",
                    "source": {"query": "SELECT 1"},
                    "comparisons": {}
                }
            }
        ]

        config = {
            "database_type": "gcpbq",
            "gcp": {
                "project_id": "my-project",
                "replace_dataset": {
                    "EDW_PRCD_PROJECT": "actual-edw"
                }
            }
        }

        # Mock connector
        mock_connector = MagicMock()
        mock_connector.execute_query.return_value = [{"result": 1}]
        mock_get_connector.return_value = mock_connector

        # Initialize without preprocessor_queries_path
        executor = ValidationExecutor(config, {}, test_cases)

        # Should still have initialized preprocessor with config
        self.assertIsNotNone(executor.source_preprocessor)

        results = executor.run()
        self.assertEqual(len(results), 1)


class TestReplaceDatasetWithConfigDetails(unittest.TestCase):
    """Test cases for replace_dataset with config_details lookup."""

    def test_replace_with_list_format_and_config_details(self):
        """Test replacing using list format with config_details lookup."""
        # Mock config_details
        mock_config_details = MagicMock()
        mock_config_details.data = {
            'bigquery': {
                'pd': {
                    'datasets': {
                        'cdw_prcd_metadata': {
                            'project_id': 'pd-project-cdw-prod'
                        },
                        'cdw_metadata': {
                            'project_id': 'pd-project-metadata-prod'
                        }
                    }
                }
            }
        }

        preprocessor_config = {
            "replace_dataset": [
                {"project_name": "pd", "dataset_name": "cdw_prcd_metadata"},
                {"project_name": "pd", "dataset_name": "cdw_metadata"}
            ]
        }
        preprocessor = QueryPreprocessor(None, preprocessor_config, mock_config_details)

        query = """
            SELECT a.* FROM PD_CDW_PRCD_METADATA.bcbsa_export_1.resulting_qmetrics a
            JOIN PD_CDW_METADATA.bcbsa_export_2.resulting_qmetrics_min b
            ON a.id = b.id
        """
        result = preprocessor.replace_dataset_placeholders(query)

        # Check that placeholders are replaced with actual project IDs
        self.assertIn("pd-project-cdw-prod", result)
        self.assertIn("pd-project-metadata-prod", result)
        self.assertNotIn("PD_CDW_PRCD_METADATA", result)
        self.assertNotIn("PD_CDW_METADATA", result)

    def test_replace_with_mixed_case_dataset_name(self):
        """Test that dataset names with underscores are handled correctly."""
        mock_config_details = MagicMock()
        mock_config_details.data = {
            'bigquery': {
                'edw': {
                    'datasets': {
                        'prcd_metadata': {
                            'project_id': 'edw-prod-project'
                        }
                    }
                }
            }
        }

        preprocessor_config = {
            "replace_dataset": [
                {"project_name": "edw", "dataset_name": "prcd_metadata"}
            ]
        }
        preprocessor = QueryPreprocessor(None, preprocessor_config, mock_config_details)

        query = "SELECT * FROM EDW_PRCD_METADATA.table_name"
        result = preprocessor.replace_dataset_placeholders(query)

        self.assertIn("edw-prod-project", result)
        self.assertNotIn("EDW_PRCD_METADATA", result)

    def test_replace_with_multiple_datasets_same_project(self):
        """Test replacing multiple datasets from the same project."""
        mock_config_details = MagicMock()
        mock_config_details.data = {
            'bigquery': {
                'pd': {
                    'datasets': {
                        'cdw_prcd_metadata': {'project_id': 'pd-prod-1'},
                        'cdw_metadata': {'project_id': 'pd-prod-2'}
                    }
                }
            }
        }

        preprocessor_config = {
            "replace_dataset": [
                {"project_name": "pd", "dataset_name": "cdw_prcd_metadata"},
                {"project_name": "pd", "dataset_name": "cdw_metadata"}
            ]
        }
        preprocessor = QueryPreprocessor(None, preprocessor_config, mock_config_details)

        query = "SELECT * FROM PD_CDW_PRCD_METADATA.t1 UNION ALL SELECT * FROM PD_CDW_METADATA.t2"
        result = preprocessor.replace_dataset_placeholders(query)

        self.assertIn("pd-prod-1", result)
        self.assertIn("pd-prod-2", result)

    def test_replace_without_config_details(self):
        """Test that list format fails gracefully without config_details."""
        preprocessor_config = {
            "replace_dataset": [
                {"project_name": "pd", "dataset_name": "cdw_prcd_metadata"}
            ]
        }
        # No config_details passed
        preprocessor = QueryPreprocessor(None, preprocessor_config, None)

        query = "SELECT * FROM PD_CDW_PRCD_METADATA.table_name"
        result = preprocessor.replace_dataset_placeholders(query)

        # Query should be unchanged (no lookup possible)
        self.assertEqual(result, query)

    def test_replace_with_missing_config_details_key(self):
        """Test handling of missing keys in config_details."""
        mock_config_details = MagicMock()
        # Missing 'bigquery' key
        mock_config_details.data = {}

        preprocessor_config = {
            "replace_dataset": [
                {"project_name": "pd", "dataset_name": "cdw_prcd_metadata"}
            ]
        }
        preprocessor = QueryPreprocessor(None, preprocessor_config, mock_config_details)

        query = "SELECT * FROM PD_CDW_PRCD_METADATA.table_name"
        result = preprocessor.replace_dataset_placeholders(query)

        # Query should be unchanged (lookup failed)
        self.assertEqual(result, query)

    def test_placeholder_caching(self):
        """Test that placeholder lookups are cached."""
        mock_config_details = MagicMock()
        mock_config_details.data = {
            'bigquery': {
                'pd': {
                    'datasets': {
                        'cdw_metadata': {'project_id': 'pd-prod'}
                    }
                }
            }
        }

        preprocessor_config = {
            "replace_dataset": [
                {"project_name": "pd", "dataset_name": "cdw_metadata"}
            ]
        }
        preprocessor = QueryPreprocessor(None, preprocessor_config, mock_config_details)

        query1 = "SELECT * FROM PD_CDW_METADATA.table1"
        query2 = "SELECT * FROM PD_CDW_METADATA.table2"

        result1 = preprocessor.replace_dataset_placeholders(query1)
        result2 = preprocessor.replace_dataset_placeholders(query2)

        # Both should be replaced
        self.assertIn("pd-prod", result1)
        self.assertIn("pd-prod", result2)

        # Verify that cache was used (lookup happened)
        self.assertIn("pd_cdw_metadata", preprocessor._replace_dataset_cache)

    def test_replace_invalid_list_item(self):
        """Test handling of invalid items in replace_dataset list."""
        mock_config_details = MagicMock()
        mock_config_details.data = {
            'bigquery': {
                'pd': {
                    'datasets': {
                        'cdw_metadata': {'project_id': 'pd-prod'}
                    }
                }
            }
        }

        preprocessor_config = {
            "replace_dataset": [
                {"project_name": "pd", "dataset_name": "cdw_metadata"},
                {"project_name": "pd"},  # Missing dataset_name
                {"dataset_name": "cdw_metadata"},  # Missing project_name
                "invalid_string"  # Not a dict
            ]
        }
        preprocessor = QueryPreprocessor(None, preprocessor_config, mock_config_details)

        query = "SELECT * FROM PD_CDW_METADATA.table_name"
        result = preprocessor.replace_dataset_placeholders(query)

        # Valid replacement should still work
        self.assertIn("pd-prod", result)

    def test_mixed_format_not_supported(self):
        """Test that list format with incomplete config_details fails gracefully."""
        preprocessor_config = {
            # List format but config_details doesn't have the data structure
            "replace_dataset": [
                {"project_name": "pd", "dataset_name": "cdw_metadata"}
            ]
        }
        mock_config_details = MagicMock()
        # Set up incomplete data structure (missing bigquery key)
        mock_config_details.data = {}
        preprocessor = QueryPreprocessor(None, preprocessor_config, mock_config_details)

        query = "SELECT * FROM PD_CDW_METADATA.table_name"
        # Should use list format logic but fail to lookup
        result = preprocessor.replace_dataset_placeholders(query)

        # Should return unchanged since config_details lookup failed
        self.assertEqual(result, query)

    def test_replace_with_valid_list_and_valid_dict(self):
        """Test that dict format still works alongside list format support."""
        # Test dict format independently
        preprocessor_config = {
            "replace_dataset": {
                "LEGACY_PLACEHOLDER": "legacy-project-id"
            }
        }
        preprocessor = QueryPreprocessor(None, preprocessor_config, None)

        query = "SELECT * FROM LEGACY_PLACEHOLDER.table_name"
        result = preprocessor.replace_dataset_placeholders(query)

        self.assertIn("legacy-project-id", result)
        self.assertNotIn("LEGACY_PLACEHOLDER", result)


if __name__ == "__main__":
    unittest.main()
