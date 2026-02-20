import os
import logging
from google.cloud import bigquery
from google.oauth2 import service_account
from .base_connector import BaseConnector

logger = logging.getLogger(__name__)


class BigQueryConnector(BaseConnector):
    """
    BigQuery connector for executing queries and fetching results.
    Supports both service account authentication and default application credentials.
    Includes support for KMS encryption for PHI data and environment-based configuration.
    """

    def __init__(self, config: dict):
        """
        Initialize BigQuery connector.

        Args:
            config: Dictionary containing BigQuery configuration with keys:
                - project_id: GCP project ID
                - dataset_id: BigQuery dataset ID
                - service_account (optional): Service account name for credential lookup
                - credentials_path (optional): Path to service account JSON file
                - location (optional): BigQuery location (default: us-central1)
                - location_map (optional): Dict mapping environment to location
                - infra_core (optional): Infrastructure core name
                - infra_core_map (optional): Dict mapping environment to infra-core
        """
        self.project_id = config.get("project_id")
        self.dataset_id = config.get("dataset_id")
        self.credentials_path = config.get("credentials_path")
        self.service_account_name = config.get("service_account")

        # Get execution environment
        self.execution_env = os.environ.get("SPRING_PROFILES_ACTIVE", "mylocal").upper()

        # Get location with fallback to default
        location_map = config.get("location_map", {})
        self.location = location_map.get(
            os.environ.get("SPRING_PROFILES_ACTIVE", "mylocal"),
            config.get("location", "us-central1")
        )

        # Get infra-core with fallback to default
        infra_core_map = config.get("infra_core_map", {})
        self.infra_core = infra_core_map.get(
            os.environ.get("SPRING_PROFILES_ACTIVE", "mylocal"),
            config.get("infra_core", "infra-core-us-central1")
        )

        # KMS encryption settings for PHI data
        self.use_encryption = config.get("use_encryption", False)
        self.kms_key_ring = config.get("kms_key_ring", "infra-default-cmek")
        self.client = None
        self._encryption_config = None
        self._query_job_config = None

    def _setup_encryption(self):
        """
        Setup KMS encryption configuration for PHI data.

        Detects PHI data based on project_id pattern containing '-h-' or '-p-'
        and applies Customer-Managed Encryption Keys (CMEK) if enabled.
        """
        is_phi = "-h-" in self.project_id or "-p-" in self.project_id

        if not self.use_encryption or not is_phi:
            if is_phi:
                logger.warning(f"PHI project detected ({self.project_id}) but encryption is disabled")
            return

        try:
            kms_key_name = (
                f"projects/{self.project_id}/locations/{self.location.lower()}/"
                f"keyRings/{self.infra_core.lower()}/cryptoKeys/{self.kms_key_ring}"
            )
            self._encryption_config = bigquery.EncryptionConfiguration(
                kms_key_name=kms_key_name
            )
            self._query_job_config = bigquery.QueryJobConfig(
                destination_encryption_configuration=self._encryption_config
            )
            logger.info(f"KMS encryption configured for PHI data: {kms_key_name}")
        except Exception as e:
            logger.warning(f"Failed to setup KMS encryption: {str(e)}")

    def connect(self):
        """Establish connection to BigQuery."""
        try:
            credentials = None

            # Try to get credentials from credentials_path
            if self.credentials_path and os.path.exists(self.credentials_path):
                logger.info(f"Using service account credentials from: {self.credentials_path}")
                credentials = service_account.Credentials.from_service_account_file(
                    self.credentials_path
                )
            else:
                # Use default application credentials
                logger.info("Using default application credentials")

            # Setup encryption if needed
            self._setup_encryption()

            # Create BigQuery client
            if self._query_job_config:
                self.client = bigquery.Client(
                    credentials=credentials,
                    project=self.project_id,
                    location=self.location,
                    default_query_job_config=self._query_job_config
                )
                logger.info(f"BigQuery PHI connection established (with encryption)")
            else:
                self.client = bigquery.Client(
                    credentials=credentials,
                    project=self.project_id,
                    location=self.location
                )
                logger.info(f"BigQuery connection established (non-PHI)")

        except Exception as e:
            logger.error(f"Failed to connect to BigQuery: {str(e)}")
            raise ConnectionError(f"Failed to connect to BigQuery: {str(e)}")

    def execute_query(self, query: str):
        """
        Execute a BigQuery query and return results.

        Args:
            query: SQL query string

        Returns:
            List of result rows as dictionaries
        """
        if not self.client:
            self.connect()

        try:
            logger.info(f"Executing query: {query[:100]}..." if len(query) > 100 else f"Executing query: {query}")
            query_job = self.client.query(query)
            logger.info(f"Query submitted, job ID: {query_job.job_id}")
            results = query_job.result(timeout=120)
            logger.info(f"Query execution completed")

            # Convert to list of dictionaries
            rows = []
            for row in results:
                rows.append(dict(row))

            logger.info(f"Query executed successfully, returned {len(rows)} rows")
            return rows
        except Exception as e:
            logger.error(f"Failed to execute BigQuery query: {str(e)}")
            raise RuntimeError(f"Failed to execute BigQuery query: {str(e)}")

    def close(self):
        """Close the BigQuery client connection."""
        if self.client:
            self.client.close()
            logger.info("BigQuery connection closed")
