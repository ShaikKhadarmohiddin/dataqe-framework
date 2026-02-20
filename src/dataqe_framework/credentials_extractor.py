"""
Credentials extractor for handling database and GCP credentials extraction
based on SPRING_PROFILES_ACTIVE environment variable.

Supports both local development and Kubernetes environment configurations.
"""

import os
import json
import logging
from typing import Dict, Optional, Any

logger = logging.getLogger(__name__)


class CredentialsExtractor:
    """
    Extracts database and GCP credentials based on SPRING_PROFILES_ACTIVE environment variable.

    Supports:
    - MySQL: hostname, port, username, password, database
    - BigQuery: project_id, dataset_id, service account credentials
    - Environment profiles: MYLOCAL, gcpqa, gcppreprod, gcpprod

    This class works with configuration objects from external libraries
    (e.g., castlight_common_lib) to extract environment-specific credentials.
    """

    # Default profile for local development
    DEFAULT_LOCAL_PROFILE = "MYLOCAL"

    # Environment variable for profile
    PROFILE_ENV_VAR = "SPRING_PROFILES_ACTIVE"

    @staticmethod
    def get_profile() -> str:
        """
        Get the execution profile from environment variable.

        Returns:
            Profile name (MYLOCAL, gcpqa, gcppreprod, or gcpprod)
        """
        profile = os.environ.get(CredentialsExtractor.PROFILE_ENV_VAR,
                                CredentialsExtractor.DEFAULT_LOCAL_PROFILE).lower()
        logger.info(f"Execution profile: {profile}")
        return profile

    @staticmethod
    def extract_mysql_config(config_details: Dict, database_name: str) -> Dict[str, Any]:
        """
        Extract MySQL configuration from config object.

        Args:
            config_details: Configuration object containing mysql section
                          Expected structure: config_details.data['mysql'][database_name]
            database_name: Database name (ventana, ventanaqe, ventanapurge, etc.)

        Returns:
            Dictionary with keys: host, port, user, password, database

        Raises:
            KeyError: If required MySQL configuration is missing
            ValueError: If database configuration is invalid
        """
        try:
            mysql_config = config_details.data['mysql'].get(database_name)

            if not mysql_config:
                raise KeyError(f"MySQL configuration not found for database: {database_name}")

            # Extract connection details
            credentials = {
                "host": mysql_config.get('db_host'),
                "port": mysql_config.get('db_port', 3306),
                "user": mysql_config.get('db_user'),
                "password": mysql_config.get('db_password'),
                "database": database_name,
            }

            # Validate required fields
            required_fields = ["host", "user", "password"]
            for field in required_fields:
                if not credentials[field]:
                    raise ValueError(f"Missing required MySQL field: {field}")

            logger.info(f"MySQL config extracted for database: {database_name}")
            return credentials

        except Exception as e:
            logger.error(f"Failed to extract MySQL configuration: {str(e)}")
            raise

    @staticmethod
    def extract_bigquery_config(
        config_details: Dict,
        project_name: str,
        dataset_name: str
    ) -> Dict[str, Any]:
        """
        Extract BigQuery configuration from config object.

        Args:
            config_details: Configuration object containing bigquery section
                          Expected structure: config_details.data['bigquery'][project_name]['datasets'][dataset_name]
            project_name: GCP project name (e.g., 'myproject')
            dataset_name: BigQuery dataset name (e.g., 'ventana', 'ventanaqe')

        Returns:
            Dictionary with keys: project_id, dataset_id, location

        Raises:
            KeyError: If required BigQuery configuration is missing
            ValueError: If specified project/dataset doesn't exist
        """
        try:
            # Navigate to dataset configuration
            bigquery_config = config_details.data.get('bigquery', {})

            if project_name not in bigquery_config:
                raise ValueError(
                    f"Project '{project_name}' not found. Available: {list(bigquery_config.keys())}"
                )

            project_config = bigquery_config[project_name]
            datasets = project_config.get('datasets', {})

            if dataset_name not in datasets:
                raise ValueError(
                    f"Dataset '{dataset_name}' not found in project '{project_name}'. "
                    f"Available: {list(datasets.keys())}"
                )

            dataset_config = datasets[dataset_name]

            # Extract BigQuery details
            credentials = {
                "project_id": dataset_config.get("project_id"),
                "dataset_id": dataset_name,
                "location": dataset_config.get("location", "us-central1"),
            }

            # Validate project_id
            if not credentials["project_id"]:
                raise ValueError(f"Missing project_id for dataset '{dataset_name}'")

            logger.info(f"BigQuery config extracted for project: {project_name}, dataset: {dataset_name}")
            return credentials

        except Exception as e:
            logger.error(f"Failed to extract BigQuery configuration: {str(e)}")
            raise

    @staticmethod
    def extract_service_account(
        config_details: Dict,
        service_account_name: str
    ) -> str:
        """
        Extract GCP service account credentials from config object.

        Args:
            config_details: Configuration object containing gcp section
                          Expected structure: config_details.data['gcp'][service_account_name]
            service_account_name: Service account name

        Returns:
            Service account JSON string or dict

        Raises:
            KeyError: If service account not found
        """
        try:
            gcp_config = config_details.data.get('gcp', {})

            if service_account_name not in gcp_config:
                raise KeyError(
                    f"Service account '{service_account_name}' not found. "
                    f"Available: {list(gcp_config.keys())}"
                )

            sa_key = gcp_config[service_account_name]
            logger.info(f"Service account credentials extracted: {service_account_name}")
            return sa_key

        except Exception as e:
            logger.error(f"Failed to extract service account credentials: {str(e)}")
            raise

    @staticmethod
    def save_service_account_json(
        sa_key: Any,
        output_path: str
    ) -> str:
        """
        Save service account credentials to a JSON file.

        Args:
            sa_key: Service account key (dict or JSON string)
            output_path: Path where to save the credentials file

        Returns:
            Path to the saved credentials file

        Raises:
            Exception: If file writing fails
        """
        try:
            # Ensure output directory exists
            os.makedirs(os.path.dirname(output_path) or ".", exist_ok=True)

            # Write credentials to file
            with open(output_path, "w") as f:
                if isinstance(sa_key, dict):
                    json.dump(sa_key, f, indent=2)
                else:
                    # Assume it's already JSON string
                    f.write(sa_key)

            # Restrict file permissions to owner only (600)
            os.chmod(output_path, 0o600)

            logger.info(f"Service account credentials saved to: {output_path}")
            return output_path

        except Exception as e:
            logger.error(f"Failed to save service account file: {str(e)}")
            raise
