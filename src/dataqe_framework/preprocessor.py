import yaml
import os
import logging
from typing import Dict, Any, Optional, List
from dataqe_framework.connectors import get_connector

logger = logging.getLogger(__name__)


class QueryPreprocessor:
    """
    Handles dynamic query preprocessing using config_query_key from configuration.

    Loads preprocessor queries from a YAML file, executes them to get dataset mappings,
    and replaces placeholders in test queries with actual dataset names.
    """

    def __init__(self, preprocessor_queries_path: str = None, preprocessor_config: Dict[str, Any] = None, config_details: Any = None):
        """
        Initialize the QueryPreprocessor.

        Args:
            preprocessor_queries_path: Path to preprocessor_queries.yml file.
            preprocessor_config: Configuration dict with config_query_key and replace_dataset settings.
            config_details: Config details object from castlight_common_lib for dataset lookups.

        Raises:
            FileNotFoundError: If preprocessor_queries_path is provided but file doesn't exist
            RuntimeError: If YAML file is invalid or cannot be parsed
        """
        self.preprocessor_queries_path = preprocessor_queries_path
        self.preprocessor_config = preprocessor_config or {}
        self.preprocessor_queries = {}
        self.dataset_mappings = {}
        self.release_labels_cache = None
        self.config_details = config_details
        self._replace_dataset_cache = {}  # Cache for resolved placeholders

        if self.preprocessor_queries_path:
            self._load_preprocessor_queries()

    def replace_dataset_placeholders(self, query: str) -> str:
        """
        Replace dataset/project placeholders using mapping from config.

        Supports two formats:
        1. List of dicts with fallback:
           [{"project_name": "pd", "dataset_name": "cdw_metadata", "bq_project_id": "my-project"}]
           - Generates placeholder PD_CDW_METADATA from project_name and dataset_name
           - If config_details available: looks up actual project_id from castlight config
           - If config_details NOT available: uses bq_project_id directly
        2. Dict format (legacy): {"EDW_PRCD_PROJECT": "actual-project-id-edw"}
           - Direct placeholder to project_id mapping

        Args:
            query: Original query with placeholders

        Returns:
            Query with dataset placeholders replaced by actual values
        """
        replace_dataset = self.preprocessor_config.get("replace_dataset")
        if not replace_dataset:
            return query

        # Build placeholder mappings based on format
        placeholder_mappings = self._build_placeholder_mappings(replace_dataset)

        if not placeholder_mappings:
            return query

        modified_query = query
        for placeholder, actual_value in placeholder_mappings.items():
            # Handle both PLACEHOLDER and placeholder formats
            modified_query = modified_query.replace(placeholder, actual_value)
            # Also try lowercase version if different
            if placeholder.lower() != placeholder:
                modified_query = modified_query.replace(placeholder.lower(), actual_value)

        if modified_query != query:
            logger.debug(
                f"Replaced dataset placeholders in query. "
                f"Replacements: {list(placeholder_mappings.keys())}"
            )

        return modified_query

    def _build_placeholder_mappings(self, replace_dataset) -> Dict[str, str]:
        """
        Build placeholder to project_id mappings from replace_dataset config.

        Supports both list of dicts and dict formats.

        For list format:
        - If config_details available: looks up project_id from castlight config
        - If config_details NOT available: uses bq_project_id as fallback
        - If both unavailable: logs warning and skips

        Args:
            replace_dataset: Either list of {"project_name": ..., "dataset_name": ..., "bq_project_id": ...}
                           or dict of {"PLACEHOLDER": "project_id"}

        Returns:
            Dict mapping placeholders to actual project IDs
        """
        mappings = {}

        if isinstance(replace_dataset, list):
            # New format: list of objects with project_name and dataset_name
            for item in replace_dataset:
                if not isinstance(item, dict):
                    logger.warning(f"Invalid replace_dataset item (not a dict): {item}")
                    continue

                project_name = item.get("project_name")
                dataset_name = item.get("dataset_name")
                bq_project_id = item.get("bq_project_id")

                if not project_name or not dataset_name:
                    logger.warning(
                        f"Invalid replace_dataset item (missing project_name or dataset_name): {item}"
                    )
                    continue

                # Generate placeholder from project_name and dataset_name
                placeholder = f"{project_name.upper()}_{dataset_name.upper()}"

                # Try to lookup from config_details first, fallback to bq_project_id
                project_id = self._lookup_project_id(project_name, dataset_name)

                if not project_id and bq_project_id:
                    # Use bq_project_id as fallback
                    project_id = bq_project_id
                    logger.debug(
                        f"Resolved placeholder {placeholder} to {project_id} "
                        f"using bq_project_id fallback"
                    )

                if project_id:
                    mappings[placeholder] = project_id
                    if self.config_details:
                        logger.debug(
                            f"Resolved placeholder {placeholder} to {project_id} "
                            f"from config_details for {project_name}.{dataset_name}"
                        )
                else:
                    logger.warning(
                        f"Failed to resolve placeholder {placeholder}: "
                        f"no project_id from config_details and bq_project_id not provided"
                    )

        elif isinstance(replace_dataset, dict):
            # Legacy format: direct placeholder to project_id mapping
            mappings = replace_dataset

        else:
            logger.warning(f"Invalid replace_dataset format: {type(replace_dataset)}")

        return mappings

    def _lookup_project_id(self, project_name: str, dataset_name: str) -> Optional[str]:
        """
        Lookup actual BigQuery project_id from config_details.

        Args:
            project_name: Project name (e.g., "pd", "edw")
            dataset_name: Dataset name (e.g., "cdw_prcd_metadata")

        Returns:
            The actual BigQuery project_id, or None if not found
        """
        # Check cache first
        cache_key = f"{project_name}_{dataset_name}"
        if cache_key in self._replace_dataset_cache:
            return self._replace_dataset_cache[cache_key]

        # If no config_details, cannot lookup
        if not self.config_details:
            logger.debug(
                f"Cannot lookup project_id for {project_name}.{dataset_name}: "
                f"config_details not available"
            )
            return None

        try:
            # Lookup: config_details.data['bigquery'][project_name]['datasets'][dataset_name]['project_id']
            project_id = self.config_details.data['bigquery'][project_name]['datasets'][dataset_name]['project_id']
            self._replace_dataset_cache[cache_key] = project_id
            return project_id
        except (KeyError, TypeError, AttributeError) as e:
            logger.warning(
                f"Failed to lookup project_id for {project_name}.{dataset_name}: {str(e)}"
            )
            return None

    def _load_preprocessor_queries(self) -> None:
        """Load preprocessor queries from YAML file."""
        if not os.path.exists(self.preprocessor_queries_path):
            raise FileNotFoundError(
                f"Preprocessor queries file not found: {self.preprocessor_queries_path}\n"
                f"Please ensure the file exists at the specified path.\n"
                f"Expected format: YAML file with preprocessor query definitions."
            )

        try:
            with open(self.preprocessor_queries_path, "r") as file:
                self.preprocessor_queries = yaml.safe_load(file) or {}
            logger.info(
                f"Loaded preprocessor queries from: {self.preprocessor_queries_path}"
            )
        except FileNotFoundError:
            raise
        except Exception as e:
            logger.error(f"Failed to load preprocessor queries: {str(e)}")
            raise RuntimeError(
                f"Error loading preprocessor queries from {self.preprocessor_queries_path}:\n"
                f"{type(e).__name__}: {str(e)}"
            )

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
            # if mappings:
            #     logger.info("=" * 60)
            #     logger.info("PREPROCESSOR QUERY RESULTS:")
            #     for source, mapping in mappings.items():
            #         logger.info(f"  Source: {source}")
            #         logger.info(f"    Current Release: {mapping.get('current_release')}")
            #         logger.info(f"    Previous Release: {mapping.get('previous_release')}")
            #     logger.info("=" * 60)
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

    def replace_release_labels(self, query: str, connector: Any) -> str:
        """
        Automatically replace all release label placeholders in query without needing
        source_name or config_query_key specified per query.

        This method executes the preprocessor query defined in preprocessor_config,
        gets all release label mappings, and replaces all SOURCE_CURR_WEEK and SOURCE_PREV_WEEK
        placeholders in the query.

        Args:
            query: Original query string with placeholders like SOURCE_CURR_WEEK, SOURCE_PREV_WEEK
            connector: Database connector for executing preprocessor query

        Returns:
            Processed query with all placeholders replaced by actual dataset names
        """
        # If no preprocessor config or config_query_key, return original query
        if not self.preprocessor_config or not self.preprocessor_config.get("config_query_key"):
            return query

        # Get release labels (cache to avoid multiple queries)
        if self.release_labels_cache is None:
            config_query_key = self.preprocessor_config.get("config_query_key")
            release_labels = self.get_dataset_mappings(config_query_key, connector)

            if not release_labels:
                return query

            # Convert mappings to list format for easier iteration
            self.release_labels_cache = [
                {
                    "source": source,
                    "curr_release_label": mapping.get("current_release"),
                    "prev_release_label": mapping.get("previous_release")
                }
                for source, mapping in release_labels.items()
            ]

        # Replace all placeholders in query
        return self._replace_all_release_labels(query, self.release_labels_cache)

    def _replace_all_release_labels(self, query: str, release_labels: List[Dict[str, str]]) -> str:
        """
        Replace all SOURCE_CURR_WEEK and SOURCE_PREV_WEEK placeholders in query.

        Args:
            query: Original query string
            release_labels: List of release label mappings

        Returns:
            Query with all placeholders replaced
        """
        modified_query = query

        if not release_labels:
            logger.debug("No release labels to replace")
            return modified_query

        replacements_made = False
        for label in release_labels:
            source = label.get("source", "").upper()
            curr_label = label.get("curr_release_label")
            prev_label = label.get("prev_release_label")

            if not source or not curr_label or not prev_label:
                logger.debug(f"Skipping incomplete label for source '{source}'")
                continue

            # Check if placeholders exist in query before replacing
            curr_placeholder = f"{source}_CURR_WEEK"
            prev_placeholder = f"{source}_PREV_WEEK"

            if curr_placeholder in modified_query or prev_placeholder in modified_query:
                replacements_made = True
                modified_query = modified_query.replace(curr_placeholder, curr_label).replace(prev_placeholder, prev_label)
                # logger.info(
                #     f"Replaced placeholders for '{source}': "
                #     f"{curr_placeholder} → {curr_label}, "
                #     f"{prev_placeholder} → {prev_label}"
                # )
            # else:
                # logger.debug(f"No placeholders found for '{source}'")

        # if not replacements_made:
        #     logger.info("No placeholder replacements made - query returned unchanged")

        return modified_query
