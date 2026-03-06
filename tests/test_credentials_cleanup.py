"""
Tests for secure service account credentials cleanup functionality.

Verifies that temporary credentials files are created with restrictive permissions,
tracked properly, and cleaned up at execution end (both on success and error).
"""

import os
import tempfile
import json
import pytest
from unittest.mock import Mock, MagicMock, patch, mock_open
from dataqe_framework.connectors.bigquery_connector import BigQueryConnector
from dataqe_framework.connectors.mysql_connector import MySQLConnector
from dataqe_framework.executor import ValidationExecutor


class TestBigQueryConnectorCredentialsTracking:
    """Tests for BigQueryConnector credential file tracking."""

    def test_temp_credentials_file_initialized_as_none(self):
        """Test that temp_credentials_file is initialized as None."""
        with patch.dict(os.environ, {'SPRING_PROFILES_ACTIVE': 'MYLOCAL'}):
            connector = BigQueryConnector({"project_id": "test-project"})
            assert connector.temp_credentials_file is None

    def test_extract_service_account_sets_restrictive_permissions(self):
        """Test that extracted service account file gets 0o600 permissions."""
        with patch.dict(os.environ, {'SPRING_PROFILES_ACTIVE': 'MYLOCAL'}):
            connector = BigQueryConnector({"project_id": "test-project"})

            # Create a temporary file to test permissions
            with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.json') as f:
                temp_path = f.name
                f.write('{"test": "credentials"}')

            try:
                # Mock config_details
                mock_config = Mock()
                mock_config.data = {'gcp': {'test_sa': '{"test": "creds"}'}}

                # Call extract_service_account
                connector.extract_service_account(
                    mock_config,
                    temp_path,
                    'test_sa'
                )

                # Verify file has restrictive permissions
                file_stat = os.stat(temp_path)
                file_permissions = oct(file_stat.st_mode)[-3:]
                assert file_permissions == '600', f"Expected 600 permissions, got {file_permissions}"
            finally:
                os.unlink(temp_path)

    def test_extract_service_account_tracks_file_path(self):
        """Test that extract_service_account tracks the file path."""
        with patch.dict(os.environ, {'SPRING_PROFILES_ACTIVE': 'MYLOCAL'}):
            connector = BigQueryConnector({"project_id": "test-project"})

            with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.json') as f:
                temp_path = f.name
                f.write('{"test": "credentials"}')

            try:
                mock_config = Mock()
                mock_config.data = {'gcp': {'test_sa': '{"test": "creds"}'}}

                connector.extract_service_account(mock_config, temp_path, 'test_sa')

                # Verify file path is tracked
                assert connector.temp_credentials_file == temp_path
            finally:
                os.unlink(temp_path)

    def test_get_temp_credentials_file_returns_tracked_path(self):
        """Test that get_temp_credentials_file returns the tracked path."""
        with patch.dict(os.environ, {'SPRING_PROFILES_ACTIVE': 'MYLOCAL'}):
            connector = BigQueryConnector({"project_id": "test-project"})

            # Set temp_credentials_file directly
            connector.temp_credentials_file = "/tmp/test_creds.json"

            # Verify getter returns the path
            assert connector.get_temp_credentials_file() == "/tmp/test_creds.json"

    def test_get_temp_credentials_file_returns_none_when_not_set(self):
        """Test that get_temp_credentials_file returns None when no file was created."""
        with patch.dict(os.environ, {'SPRING_PROFILES_ACTIVE': 'MYLOCAL'}):
            connector = BigQueryConnector({"project_id": "test-project"})

            assert connector.get_temp_credentials_file() is None

    def test_destructor_cleans_up_temp_credentials(self):
        """Test that __del__ destructor cleans up the temp credentials file."""
        with patch.dict(os.environ, {'SPRING_PROFILES_ACTIVE': 'MYLOCAL'}):
            connector = BigQueryConnector({"project_id": "test-project"})

            # Create a temporary file
            with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.json') as f:
                temp_path = f.name
                f.write('{"test": "credentials"}')

            # Verify file exists
            assert os.path.exists(temp_path)

            # Set the temp file on the connector
            connector.temp_credentials_file = temp_path

            # Call destructor
            connector.__del__()

            # Verify file is deleted
            assert not os.path.exists(temp_path)

    def test_destructor_handles_missing_file_gracefully(self):
        """Test that destructor handles missing file without raising exception."""
        with patch.dict(os.environ, {'SPRING_PROFILES_ACTIVE': 'MYLOCAL'}):
            connector = BigQueryConnector({"project_id": "test-project"})

            # Set a non-existent file path
            connector.temp_credentials_file = "/tmp/nonexistent_creds_file_12345.json"

            # Should not raise exception
            connector.__del__()


class TestMySQLConnectorAPIConsistency:
    """Tests for MySQLConnector API consistency."""

    def test_get_temp_credentials_file_returns_none(self):
        """Test that MySQL connector returns None for get_temp_credentials_file."""
        with patch.dict(os.environ, {'SPRING_PROFILES_ACTIVE': 'MYLOCAL'}):
            connector = MySQLConnector(host="localhost", database="test")
            assert connector.get_temp_credentials_file() is None

    def test_get_temp_credentials_file_method_exists(self):
        """Test that get_temp_credentials_file method exists on MySQLConnector."""
        with patch.dict(os.environ, {'SPRING_PROFILES_ACTIVE': 'MYLOCAL'}):
            connector = MySQLConnector(host="localhost", database="test")
            assert hasattr(connector, 'get_temp_credentials_file')
            assert callable(getattr(connector, 'get_temp_credentials_file'))


class TestValidationExecutorCleanup:
    """Tests for ValidationExecutor cleanup mechanism."""

    def test_cleanup_removes_bigquery_temp_credentials(self):
        """Test that cleanup removes BigQuery temporary credentials file."""
        with patch.dict(os.environ, {'SPRING_PROFILES_ACTIVE': 'MYLOCAL'}):
            # Create mock connectors
            source_connector = Mock(spec=BigQueryConnector)
            target_connector = Mock(spec=MySQLConnector)

            # Create temporary file
            with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.json') as f:
                temp_path = f.name
                f.write('{"test": "credentials"}')

            # Setup source connector to return temp file path
            source_connector.get_temp_credentials_file.return_value = temp_path
            target_connector.get_temp_credentials_file.return_value = None

            # Verify file exists before cleanup
            assert os.path.exists(temp_path)

            # Create executor
            executor = ValidationExecutor(
                {"database_type": "gcpbq"},
                {"database_type": "mysql"},
                []
            )
            executor.source_connector = source_connector
            executor.target_connector = target_connector

            # Run cleanup
            executor._cleanup_temp_credentials()

            # Verify file is deleted
            assert not os.path.exists(temp_path)

    def test_cleanup_handles_none_connectors(self):
        """Test that cleanup handles None connectors gracefully."""
        executor = ValidationExecutor(None, None, [])
        executor.source_connector = None
        executor.target_connector = None

        # Should not raise exception
        executor._cleanup_temp_credentials()

    def test_cleanup_handles_connectors_without_method(self):
        """Test that cleanup handles connectors without get_temp_credentials_file method."""
        executor = ValidationExecutor(None, None, [])

        # Create mock connector without get_temp_credentials_file method
        executor.source_connector = Mock()
        executor.target_connector = Mock()
        del executor.source_connector.get_temp_credentials_file
        del executor.target_connector.get_temp_credentials_file

        # Should not raise exception
        executor._cleanup_temp_credentials()

    def test_cleanup_handles_missing_file_gracefully(self):
        """Test that cleanup handles file that doesn't exist."""
        executor = ValidationExecutor(None, None, [])

        # Create mock connector that returns non-existent file
        source_connector = Mock()
        source_connector.get_temp_credentials_file.return_value = "/tmp/nonexistent_file_12345.json"
        executor.source_connector = source_connector
        executor.target_connector = None

        # Should not raise exception
        executor._cleanup_temp_credentials()

    def test_cleanup_called_in_finally_block_on_success(self):
        """Test that cleanup is called even on successful test execution."""
        with patch.dict(os.environ, {'SPRING_PROFILES_ACTIVE': 'MYLOCAL'}):
            # Create mock connectors
            source_connector = Mock()
            target_connector = Mock()
            source_connector.get_temp_credentials_file.return_value = None
            target_connector.get_temp_credentials_file.return_value = None

            # Create executor with empty test cases
            executor = ValidationExecutor(
                {"database_type": "gcpbq"},
                {"database_type": "mysql"},
                []
            )

            # Mock setup_connectors to avoid actual connector creation
            executor.setup_connectors = Mock()
            executor.source_connector = source_connector
            executor.target_connector = target_connector

            # Mock _cleanup_temp_credentials
            executor._cleanup_temp_credentials = Mock()

            # Run with empty test cases (should succeed)
            results = executor.run()

            # Verify cleanup was called
            executor._cleanup_temp_credentials.assert_called_once()
            assert isinstance(results, list)

    def test_cleanup_called_in_finally_block_on_error(self):
        """Test that cleanup is called even when test execution has errors."""
        with patch.dict(os.environ, {'SPRING_PROFILES_ACTIVE': 'MYLOCAL'}):
            # Create mock connectors that will raise error
            source_connector = Mock()
            target_connector = Mock()
            source_connector.get_temp_credentials_file.return_value = None
            target_connector.get_temp_credentials_file.return_value = None

            # Create test case that will trigger error
            test_cases = [
                {
                    "TEST_QUERY": {
                        "source": {"query": "SELECT 1"},
                        "target": {"query": "SELECT 2"}
                    }
                }
            ]

            # Create executor
            executor = ValidationExecutor(
                {"database_type": "gcpbq"},
                {"database_type": "mysql"},
                test_cases
            )

            # Mock setup_connectors to avoid actual connector creation
            executor.setup_connectors = Mock()
            executor.source_connector = source_connector
            executor.target_connector = target_connector

            # Setup connector to raise error during query execution
            source_connector.execute_query.side_effect = RuntimeError("Test error")

            # Mock _cleanup_temp_credentials to track if it's called
            executor._cleanup_temp_credentials = Mock()

            # Run - this will have errors in test execution
            results = executor.run()

            # Verify cleanup was called even though execution had errors
            executor._cleanup_temp_credentials.assert_called_once()
            assert len(results) == 1
            assert results[0]['error_occurred'] is True

    def test_cleanup_does_not_stop_execution_on_file_error(self):
        """Test that cleanup errors don't prevent normal execution flow."""
        executor = ValidationExecutor(None, None, [])

        # Create mock connector that raises error during cleanup
        source_connector = Mock()
        source_connector.get_temp_credentials_file.side_effect = Exception("Cleanup error")
        executor.source_connector = source_connector
        executor.target_connector = None

        # Should not raise exception
        executor._cleanup_temp_credentials()

    def test_cleanup_with_multiple_connectors(self):
        """Test cleanup works correctly with both source and target connectors."""
        with patch.dict(os.environ, {'SPRING_PROFILES_ACTIVE': 'MYLOCAL'}):
            # Create temporary files for both connectors
            source_file = tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='_source.json')
            target_file = tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='_target.json')
            source_file.write('{"source": "creds"}')
            target_file.write('{"target": "creds"}')
            source_file.close()
            target_file.close()

            try:
                # Create mock connectors
                source_connector = Mock()
                target_connector = Mock()
                source_connector.get_temp_credentials_file.return_value = source_file.name
                target_connector.get_temp_credentials_file.return_value = target_file.name

                # Verify files exist
                assert os.path.exists(source_file.name)
                assert os.path.exists(target_file.name)

                # Create executor
                executor = ValidationExecutor(None, None, [])
                executor.source_connector = source_connector
                executor.target_connector = target_connector

                # Run cleanup
                executor._cleanup_temp_credentials()

                # Verify both files are deleted
                assert not os.path.exists(source_file.name)
                assert not os.path.exists(target_file.name)
            finally:
                # Cleanup in case test fails
                for f in [source_file.name, target_file.name]:
                    if os.path.exists(f):
                        os.unlink(f)


class TestIntegrationCredentialsCleanup:
    """Integration tests for credentials cleanup."""

    def test_full_executor_run_cleans_up_credentials(self):
        """Integration test: verify full execution run cleans up credentials."""
        with patch.dict(os.environ, {'SPRING_PROFILES_ACTIVE': 'MYLOCAL'}):
            # Create temporary credentials file
            with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.json') as f:
                cred_file = f.name
                f.write('{"credentials": "data"}')

            try:
                # Verify file exists
                assert os.path.exists(cred_file)

                # Create mock connectors
                source_connector = Mock()
                target_connector = Mock()
                source_connector.get_temp_credentials_file.return_value = cred_file
                target_connector.get_temp_credentials_file.return_value = None

                # Create executor
                executor = ValidationExecutor(
                    {"database_type": "gcpbq"},
                    {"database_type": "mysql"},
                    []
                )

                # Mock setup_connectors to avoid actual connector creation
                executor.setup_connectors = Mock()
                executor.source_connector = source_connector
                executor.target_connector = target_connector

                # Run executor
                results = executor.run()

                # Verify credentials file is cleaned up
                assert not os.path.exists(cred_file)
                assert isinstance(results, list)
            finally:
                # Cleanup just in case
                if os.path.exists(cred_file):
                    os.unlink(cred_file)
