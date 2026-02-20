import yaml
import os
import logging
from typing import Dict, Any, Optional
from dataqe_framework.connectors import get_connector

logger = logging.getLogger(__name__)


class QueryPreprocessor:
    """
    Handles dynamic query preprocessing using config_query_key from configuration.

    Loads preprocessor queries from a YAML file, executes them to get dataset mappings,
    and replaces placeholders in test queries with actual dataset names.
    """

    def __init__(self, preprocessor_queries_path: str = None):
        """
        Initialize the QueryPreprocessor.

        Args:
            preprocessor_queries_path: Path to preprocessor_queries.yml file.
                                      If not provided, attempts to load from default location.
        """
        self.preprocessor_queries_path = preprocessor_queries_path
        self.preprocessor_queries = {}
        self.dataset_mappings = {}

        if self.preprocessor_queries_path:
            self._load_preprocessor_queries()

    def _load_preprocessor_queries(self) -> None:
        """Load preprocessor queries from YAML file."""
        if not os.path.exists(self.preprocessor_queries_path):
            logger.warning(
                f"Preprocessor queries file not found: {self.preprocessor_queries_path}"
            )
            return

        try:
            with open(self.preprocessor_queries_path, "r") as file:
                self.preprocessor_queries = yaml.safe_load(file) or {}
            logger.info(
                f"Loaded preprocessor queries from: {self.preprocessor_queries_path}"
            )
        except Exception as e:
            logger.error(f"Failed to load preprocessor queries: {str(e)}")
            raise

    def get_dataset_mappings(
        self, config_query_key: str, connector: Any
    ) -> Dict[str, Dict[str, str]]:
        """
        Execute preprocessor query to get dataset mappings.

        Args:
            config_query_key: Key to look up in preprocessor_queries.yml
            connector: Database connector to use for query execution

        Returns:
            Dictionary mapping source names to their current and previous release datasets.
            Example:
            {
                "bcbsa": {"current_release": "bcbsa_export1", "previous_release": "bcbsa_export3"},
                "bcbsa_pf": {"current_release": "bcbsa_pf_export2", "previous_release": "bcbsa_export1"}
            }
        """
        if not self.preprocessor_queries:
            logger.warning("No preprocessor queries loaded")
            return {}

        if config_query_key not in self.preprocessor_queries:
            logger.warning(
                f"Config query key not found in preprocessor queries: {config_query_key}"
            )
            return {}

        try:
            query = self.preprocessor_queries[config_query_key]
            logger.info(f"Executing preprocessor query for key: {config_query_key}")

            # Execute the query
            results = connector.execute_query(query)

            # Build mappings from results
            mappings = {}
            for row in results:
                if "source" in row:
                    source = row["source"]
                    # Support both naming conventions: current_release/previous_release and curr_release_label/prev_release_label
                    current_release = row.get("current_release") or row.get("curr_release_label")
                    previous_release = row.get("previous_release") or row.get("prev_release_label")

                    mappings[source] = {
                        "current_release": current_release,
                        "previous_release": previous_release,
                    }

            logger.info(f"Generated dataset mappings: {mappings}")
            return mappings

        except Exception as e:
            logger.error(
                f"Failed to get dataset mappings for key '{config_query_key}': {str(e)}"
            )
            raise

    def replace_placeholders_in_query(
        self, query: str, source_name: str, mappings: Dict[str, Dict[str, str]]
    ) -> str:
        """
        Replace placeholder dataset names in query with actual dataset names.

        Args:
            query: Original query with placeholders
            source_name: Source name (e.g., "bcbsa", "bcbsa_pf")
            mappings: Dataset mappings from get_dataset_mappings()

        Returns:
            Query with placeholders replaced by actual dataset names
        """
        if not mappings or source_name not in mappings:
            logger.debug(
                f"No mappings found for source: {source_name}, returning original query"
            )
            return query

        mapping = mappings[source_name]
        current_release = mapping.get("current_release")
        previous_release = mapping.get("previous_release")

        if not current_release or not previous_release:
            logger.warning(
                f"Incomplete mapping for source {source_name}: {mapping}"
            )
            return query

        # Build source name variations (uppercase for placeholder matching)
        source_upper = source_name.upper()

        # Replace placeholders with actual dataset names
        # Format: SOURCE_CURR_WEEK and SOURCE_PREV_WEEK
        modified_query = query.replace(
            f"{source_upper}_CURR_WEEK", current_release
        ).replace(f"{source_upper}_PREV_WEEK", previous_release)

        if modified_query != query:
            logger.debug(
                f"Replaced placeholders for '{source_name}': "
                f"{source_upper}_CURR_WEEK → {current_release}, "
                f"{source_upper}_PREV_WEEK → {previous_release}"
            )

        return modified_query

    def process_query(
        self,
        query: str,
        config_query_key: Optional[str],
        source_name: Optional[str],
        connector: Any,
    ) -> str:
        """
        Process a query by replacing placeholders if config_query_key is provided.

        Args:
            query: Original query string
            config_query_key: Key to look up preprocessor query (optional)
            source_name: Source name for placeholder replacement (optional)
            connector: Database connector for executing preprocessor query

        Returns:
            Processed query (with replacements if applicable, or original query)
        """
        # If no config_query_key, return original query
        if not config_query_key:
            return query

        # Get dataset mappings by executing preprocessor query
        mappings = self.get_dataset_mappings(config_query_key, connector)

        # If no mappings or source_name not provided, return original query
        if not mappings or not source_name:
            return query

        # Replace placeholders in query
        return self.replace_placeholders_in_query(query, source_name, mappings)
