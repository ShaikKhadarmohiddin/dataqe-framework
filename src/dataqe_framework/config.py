"""Configuration module for dataqe-framework."""

import os
from pathlib import Path


# Default output directory for reports
DEFAULT_OUTPUT_DIR = "./output"

# Environment variable for output directory configuration
OUTPUT_DIR_ENV_VAR = "DATAQE_OUTPUT_DIR"


def get_output_directory() -> str:
    """
    Get the output directory for reports.

    Priority:
    1. DATAQE_OUTPUT_DIR environment variable
    2. DEFAULT_OUTPUT_DIR constant

    Returns:
        Path to output directory
    """
    return os.environ.get(OUTPUT_DIR_ENV_VAR, DEFAULT_OUTPUT_DIR)


def ensure_output_directory() -> Path:
    """
    Ensure output directory exists, creating it if necessary.

    Returns:
        Path object to output directory
    """
    output_dir = Path(get_output_directory())
    output_dir.mkdir(parents=True, exist_ok=True)
    return output_dir
