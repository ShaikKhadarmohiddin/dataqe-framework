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
        self.preprocessor = None

        # Initialize preprocessor if path is provided
        if preprocessor_queries_path:
            self.preprocessor = QueryPreprocessor(preprocessor_queries_path)

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

                # Process query with preprocessor if config_query_key exists
                source_query = self._process_query_with_preprocessor(
                    source_query,
                    test_config["source"],
                    self.source_connector
                )

                source_query_start = datetime.now()
                source_result = self.source_connector.execute_query(source_query)
                source_query_time_ms = self._calculate_duration_ms(source_query_start)
                source_value = self._extract_value(source_result)

            # Run Target
            if "target" in test_config:
                target_query = test_config["target"]["query"]

                # Process query with preprocessor if config_query_key exists
                target_query = self._process_query_with_preprocessor(
                    target_query,
                    test_config["target"],
                    self.target_connector
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

    def _process_query_with_preprocessor(self, query: str, config_block: dict, connector) -> str:
        """
        Process query with preprocessor if config_query_key is present in config block.

        Args:
            query: Original query string
            config_block: Configuration block for source or target (should contain query and optionally config_query_key)
            connector: Database connector to use

        Returns:
            Processed query (with replacements if applicable) or original query
        """
        # Check if config_query_key exists in config block
        config_query_key = config_block.get("config_query_key")

        if not config_query_key:
            # No preprocessor query key, return original query
            return query

        if not self.preprocessor:
            # Preprocessor not initialized, return original query
            logger.warning(
                f"config_query_key '{config_query_key}' specified but preprocessor not initialized"
            )
            return query

        # Get source_name from config block if provided
        source_name = config_block.get("source_name")

        try:
            # Process query through preprocessor
            processed_query = self.preprocessor.process_query(
                query,
                config_query_key,
                source_name,
                connector
            )
            return processed_query
        except Exception as e:
            logger.error(f"Error processing query with preprocessor: {str(e)}")
            # Return original query on error
            return query

