from datetime import datetime, timedelta
import logging
from dataqe_framework.connectors import get_connector
from dataqe_framework.comparison.comparator import compare_values
from dataqe_framework.preprocessor import QueryPreprocessor

logger = logging.getLogger(__name__)


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

        # Initialize preprocessors if path is provided
        if preprocessor_queries_path:
            # Extract config_query_key from source config (under gcp/mysql/etc)
            src_config = self._extract_preprocessor_config(source_config)
            self.source_preprocessor = QueryPreprocessor(preprocessor_queries_path, src_config)

            # Extract config_query_key from target config (under gcp/mysql/etc)
            tgt_config = self._extract_preprocessor_config(target_config)
            self.target_preprocessor = QueryPreprocessor(preprocessor_queries_path, tgt_config)

    def _extract_preprocessor_config(self, config: dict) -> dict:
        """
        Extract preprocessor config (config_query_key) from database-specific config.

        Args:
            config: Source or target config block

        Returns:
            Dictionary with config_query_key if found, empty dict otherwise
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

        # Extract config_query_key if present
        config_query_key = db_config.get("config_query_key")
        if config_query_key:
            return {"config_query_key": config_query_key}

        return {}

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

        for test in self.test_cases:

            test_start = datetime.now()
            test_name = list(test.keys())[0]
            test_config = test[test_name]

            source_value = None
            target_value = None
            source_query_time_ms = 0.0
            target_query_time_ms = 0.0

            # Run Source
            if "source" in test_config:
                source_query = test_config["source"]["query"]

                # Process query with source preprocessor (automatic replacement of all release labels)
                source_query = self._process_query_with_preprocessor(
                    source_query, self.source_connector, self.source_preprocessor
                )

                source_query_start = datetime.now()
                source_result = self.source_connector.execute_query(source_query)
                source_query_time_ms = self._calculate_duration_ms(source_query_start)
                source_value = self._extract_value(source_result)

            # Run Target
            if "target" in test_config:
                target_query = test_config["target"]["query"]

                # Process query with target preprocessor (automatic replacement of all release labels)
                target_query = self._process_query_with_preprocessor(
                    target_query, self.target_connector, self.target_preprocessor
                )

                target_query_start = datetime.now()
                target_result = self.target_connector.execute_query(target_query)
                target_query_time_ms = self._calculate_duration_ms(target_query_start)
                target_value = self._extract_value(target_result)

            # Compare
            comparison_start = datetime.now()
            status = compare_values(
                source_value,
                target_value,
                test_config
            )
            comparison_time_ms = self._calculate_duration_ms(comparison_start)

            test_end = datetime.now()
            execution_time_ms = self._calculate_duration_ms(test_start)

            results.append({
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
                "script_name": script_name
            })

        return results

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
        Process query with preprocessor to replace all release label placeholders.

        Automatically replaces all SOURCE_CURR_WEEK and SOURCE_PREV_WEEK placeholders
        without needing per-test configuration.

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
            # Process query through preprocessor with automatic replacement
            processed_query = preprocessor.replace_release_labels(query, connector)
            return processed_query
        except Exception as e:
            logger.error(f"Error processing query with preprocessor: {str(e)}")
            # Return original query on error
            return query

