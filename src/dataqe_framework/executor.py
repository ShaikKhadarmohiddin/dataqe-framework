from datetime import datetime, timedelta
import os
import logging
from dataqe_framework.connectors import get_connector
from dataqe_framework.comparison.comparator import compare_values
from dataqe_framework.preprocessor import QueryPreprocessor

logger = logging.getLogger(__name__)

# Try to import config_details from castlight_common_lib
try:
    import castlight_common_lib.configfunctions as cfg
    _config_details = None
    if 'SPRING_PROFILES_ACTIVE' in os.environ:
        _config_details = cfg.Config('dataqeteam', [os.environ.get('SPRING_PROFILES_ACTIVE')])
except ImportError:
    _config_details = None


def _should_skip_test(test_config: dict) -> bool:
    """
    Check if a test should be skipped based on invalid marker.

    Args:
        test_config: Test configuration dictionary

    Returns:
        bool: True if test has 'invalid: true', False otherwise
    """
    return test_config.get("invalid", False) is True


class ValidationExecutor:

    def __init__(self, source_config, target_config, test_cases, preprocessor_queries_path: str = None):
        self.source_config = source_config
        self.target_config = target_config
        self.test_cases = test_cases
        self.preprocessor_queries_path = preprocessor_queries_path

        self.source_connector = None
        self.target_connector = None
        self.source_preprocessor = None
        self.target_preprocessor = None

        # Extract preprocessor config from source and target
        src_config = self._extract_preprocessor_config(source_config)
        tgt_config = self._extract_preprocessor_config(target_config)

        # Initialize preprocessors if path is provided or if there's preprocessor config
        # (for features like replace_dataset that don't require preprocessor_queries_path)
        if preprocessor_queries_path or src_config:
            self.source_preprocessor = QueryPreprocessor(preprocessor_queries_path, src_config, _config_details)

        if preprocessor_queries_path or tgt_config:
            self.target_preprocessor = QueryPreprocessor(preprocessor_queries_path, tgt_config, _config_details)

    def _extract_preprocessor_config(self, config: dict) -> dict:
        """
        Extract preprocessor config from database-specific config.

        Args:
            config: Source or target config block

        Returns:
            Dictionary with config_query_key and replace_dataset if found, empty dict otherwise
        """
        if not config:
            return {}

        # Get database type from config
        db_type = config.get("database_type")
        if not db_type:
            return {}

        # Map database type to config key (gcpbq uses "gcp" config key)
        config_key = "gcp" if db_type == "gcpbq" else db_type

        # Extract database-specific config (gcp, mysql, etc.)
        db_config = config.get(config_key)
        if not db_config or not isinstance(db_config, dict):
            return {}

        preprocessor_config = {}

        # Extract config_query_key if present
        config_query_key = db_config.get("config_query_key")
        if config_query_key:
            preprocessor_config["config_query_key"] = config_query_key

        # Extract replace_dataset if present (supports both list and dict formats)
        replace_dataset = db_config.get("replace_dataset")
        if replace_dataset:
            # Accept list of dicts or dict format
            if isinstance(replace_dataset, (list, dict)):
                preprocessor_config["replace_dataset"] = replace_dataset

        return preprocessor_config

    def setup_connectors(self):
        if self.source_config:
            self.source_connector = get_connector(self.source_config)

        if self.target_config:
            self.target_connector = get_connector(self.target_config)

    def run(self, script_name: str = "default"):
        """
        Execute validation tests with timing and detailed result tracking.

        Args:
            script_name: Name of the validation script being executed

        Returns:
            List of test results with execution timing details
        """
        execution_start = datetime.now()
        self.setup_connectors()
        results = []

        try:
            for test in self.test_cases:
                test_start = datetime.now()
                test_name = list(test.keys())[0]
                test_config = test[test_name]

                # Skip tests marked as invalid
                if _should_skip_test(test_config):
                    logger.info(f"Skipping test '{test_name}' (marked as invalid)")
                    continue

                source_value = None
                target_value = None
                source_query_time_ms = 0.0
                target_query_time_ms = 0.0
                error_message = None
                error_type = None
                error_occurred = False

                # Run Source
                if "source" in test_config:
                    source_query = test_config["source"]["query"]

                    # Process query with source preprocessor (automatic replacement of all release labels)
                    source_query = self._process_query_with_preprocessor(
                        source_query, self.source_connector, self.source_preprocessor
                    )

                    try:
                        source_query_start = datetime.now()
                        source_result = self.source_connector.execute_query(source_query)
                        source_query_time_ms = self._calculate_duration_ms(source_query_start)
                        source_value = self._extract_value(source_result)
                    except Exception as e:
                        source_query_time_ms = self._calculate_duration_ms(source_query_start)
                        error_occurred = True
                        error_type = type(e).__name__
                        error_message = str(e)
                        logger.error(f"Error executing source query for test '{test_name}': {error_type} - {error_message}")

                # Run Target (only if source succeeded or no source)
                if "target" in test_config and not error_occurred:
                    target_query = test_config["target"]["query"]

                    # Process query with target preprocessor (automatic replacement of all release labels)
                    target_query = self._process_query_with_preprocessor(
                        target_query, self.target_connector, self.target_preprocessor
                    )

                    try:
                        target_query_start = datetime.now()
                        target_result = self.target_connector.execute_query(target_query)
                        target_query_time_ms = self._calculate_duration_ms(target_query_start)
                        target_value = self._extract_value(target_result)
                    except Exception as e:
                        target_query_time_ms = self._calculate_duration_ms(target_query_start)
                        error_occurred = True
                        error_type = type(e).__name__
                        error_message = str(e)
                        logger.error(f"Error executing target query for test '{test_name}': {error_type} - {error_message}")

                # Compare (skip if error occurred)
                status = "ERROR" if error_occurred else None
                comparison_time_ms = 0.0

                if not error_occurred:
                    comparison_start = datetime.now()
                    status = compare_values(
                        source_value,
                        target_value,
                        test_config
                    )
                    comparison_time_ms = self._calculate_duration_ms(comparison_start)

                test_end = datetime.now()
                execution_time_ms = self._calculate_duration_ms(test_start)

                result_dict = {
                    "test_name": test_name,
                    "severity": test_config.get("severity"),
                    "source_value": source_value,
                    "target_value": target_value,
                    "status": status,
                    "start_time": test_start,
                    "end_time": test_end,
                    "execution_time_ms": execution_time_ms,
                    "source_query_time_ms": source_query_time_ms,
                    "target_query_time_ms": target_query_time_ms,
                    "comparison_time_ms": comparison_time_ms,
                    "script_name": script_name,
                    "error_occurred": error_occurred,
                    "error_type": error_type,
                    "error_message": error_message
                }

                results.append(result_dict)

            return results
        finally:
            # Cleanup temporary credentials files
            self._cleanup_temp_credentials()

    def _calculate_duration_ms(self, start_time: datetime) -> float:
        """Calculate duration in milliseconds from start_time to now."""
        duration = datetime.now() - start_time
        return duration.total_seconds() * 1000

    def _extract_value(self, result):
        if not result:
            return None

        # assuming single value queries
        return list(result[0].values())[0]

    def _process_query_with_preprocessor(self, query: str, connector, preprocessor) -> str:
        """
        Process query with preprocessor to replace dataset placeholders and release labels.

        Automatically replaces dataset placeholders (e.g., EDW_PRCD_PROJECT) and
        all SOURCE_CURR_WEEK and SOURCE_PREV_WEEK placeholders without needing
        per-test configuration.

        Args:
            query: Original query string
            connector: Database connector to use
            preprocessor: QueryPreprocessor instance (source or target)

        Returns:
            Processed query (with replacements if applicable) or original query
        """
        if not preprocessor or not connector:
            # Preprocessor not initialized or no connector, return original query
            return query

        try:
            # Step 1: Replace dataset placeholders first (e.g., EDW_PRCD_PROJECT)
            processed_query = preprocessor.replace_dataset_placeholders(query)

            # Step 2: Replace release label placeholders (e.g., SOURCE_CURR_WEEK)
            processed_query = preprocessor.replace_release_labels(processed_query, connector)

            return processed_query
        except Exception as e:
            logger.error(f"Error processing query with preprocessor: {str(e)}")
            # Return original query on error
            return query

    def _cleanup_temp_credentials(self):
        """
        Cleanup temporary credentials files created by connectors.

        Iterates through source and target connectors, retrieves any temporary
        credentials files, and safely deletes them. Errors during cleanup are
        logged but do not stop execution.
        """
        for connector in [self.source_connector, self.target_connector]:
            if not connector:
                continue

            try:
                # Safely call get_temp_credentials_file() if it exists
                temp_file = getattr(connector, 'get_temp_credentials_file', lambda: None)()

                if temp_file and os.path.exists(temp_file):
                    try:
                        os.remove(temp_file)
                        logger.info(f"Cleaned up temporary credentials file: {temp_file}")
                    except Exception as e:
                        logger.warning(f"Failed to delete temporary credentials file {temp_file}: {str(e)}")
            except Exception as e:
                logger.warning(f"Error during credentials cleanup: {str(e)}")

