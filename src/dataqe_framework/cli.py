import argparse
import yaml
import os
import logging
import shutil
from datetime import datetime
from pathlib import Path

from dataqe_framework.executor import ValidationExecutor
from dataqe_framework.config_loader import load_config
from dataqe_framework.reporter import (
    ExecutionSummary,
    ConsoleReporter,
    HTMLReporter,
    CSVReporter,
    AutomationDataReporter,
    FailedExecutionReporter
)


# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(name)s - %(levelname)s - %(asctime)s - %(message)s"
)
logger = logging.getLogger(__name__)


def load_test_cases(script_path: str):
    if not os.path.exists(script_path):
        raise FileNotFoundError(f"Test script not found: {script_path}")

    with open(script_path, "r") as file:
        return yaml.safe_load(file)


def get_output_dir() -> str:
    """Get output directory from environment or use default."""
    return os.environ.get("DATAQE_OUTPUT_DIR", "./output")


def ensure_output_directory(output_dir: str) -> None:
    """
    Ensure output directory exists, creating it if necessary.

    Args:
        output_dir: Path to output directory to create/ensure
    """
    output_path = Path(output_dir)
    try:
        output_path.mkdir(parents=True, exist_ok=True)
        logger.info(f"Output directory ready: {output_dir}")
    except Exception as e:
        logger.error(f"Failed to create output directory: {e}")
        raise


def clean_output_directory(output_dir: str) -> None:
    """
    Clean output directory by removing all files.

    Args:
        output_dir: Path to output directory to clean
    """
    output_path = Path(output_dir)
    if output_path.exists():
        try:
            for file in output_path.glob("*"):
                if file.is_file():
                    file.unlink()
            logger.info(f"Cleaned output directory: {output_dir}")
        except Exception as e:
            logger.warning(f"Error cleaning output directory: {e}")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", required=True)
    args = parser.parse_args()

    # Get output directory, create if needed, and clean it
    output_dir = get_output_dir()
    ensure_output_directory(output_dir)
    clean_output_directory(output_dir)

    full_config = load_config(args.config)

    # Find the configuration block (handles different naming conventions)
    config_block = None
    for key in full_config:
        if key.startswith("config_block_"):
            config_block = full_config[key]
            break

    if config_block is None:
        raise ValueError("No valid config_block found in configuration. Expected key starting with 'config_block_'")

    # Extract validation script path
    validation_script = config_block["other"]["validation_script"]

    # If script is relative, resolve it relative to config file location
    config_dir = os.path.dirname(args.config)
    script_path = os.path.join(config_dir, validation_script)
    script_name = os.path.basename(script_path)

    test_cases = load_test_cases(script_path)

    # Extract source and target configurations
    source_config = config_block.get("source")
    target_config = config_block.get("target")

    # Get preprocessor queries path if specified
    preprocessor_queries_path = config_block["other"].get("preprocessor_queries")
    if preprocessor_queries_path:
        # Resolve relative path if needed
        if not os.path.isabs(preprocessor_queries_path):
            preprocessor_queries_path = os.path.join(config_dir, preprocessor_queries_path)

    # Execute tests with timing
    logger.info(f"Starting execution of test script: {script_name}")
    executor = ValidationExecutor(
        source_config,
        target_config,
        test_cases,
        preprocessor_queries_path=preprocessor_queries_path
    )
    results = executor.run(script_name=script_name)

    # Generate execution summary
    summary = ExecutionSummary(results)

    # Report to console
    console_reporter = ConsoleReporter()
    for result in results:
        console_reporter.report_test_execution(result["test_name"], result)
    console_reporter.report_summary(summary)

    # Generate ExecutionReport.html and ExecutionReport.csv
    html_reporter = HTMLReporter(output_dir)
    html_report_path = html_reporter.generate_report(results, summary)
    logger.info(f"ExecutionReport.html generated: {html_report_path}")

    csv_reporter = CSVReporter(output_dir)
    csv_report_path = csv_reporter.generate_report(results, summary)
    logger.info(f"ExecutionReport.csv generated: {csv_report_path}")

    # Generate FailedExecutionReport.html (with failures or all-passed message)
    failed_reporter = FailedExecutionReporter(output_dir)
    failed_report_path = failed_reporter.generate_report(results, summary)
    logger.info(f"FailedExecutionReport.html generated: {failed_report_path}")

    # Generate AutomationData.csv for CI/CD integration
    automation_data_reporter = AutomationDataReporter(output_dir)
    app = os.environ.get("DATAQE_APP_NAME", "default_app")
    branch = os.environ.get("DATAQE_BRANCH", "default_branch")
    platform = os.environ.get("DATAQE_PLATFORM", "default_platform")
    owner = os.environ.get("DATAQE_OWNER", "default_owner")

    automation_data_path = automation_data_reporter.generate_report(
        results,
        summary,
        app=app,
        branch=branch,
        platform=platform,
        owner=owner,
        test_report_path=html_report_path
    )
    logger.info(f"AutomationData.csv generated: {automation_data_path}")

