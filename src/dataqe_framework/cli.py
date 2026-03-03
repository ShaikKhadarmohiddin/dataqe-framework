import argparse
import yaml
import os
import logging
import shutil
from datetime import datetime
from pathlib import Path

from dataqe_framework import __version__
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


def is_valid_block(block_config):
    """
    Check if a configuration block has the required structure.

    A valid block must have 'source', 'target', and 'other' keys that are all dicts.

    Args:
        block_config: Configuration block to validate

    Returns:
        bool: True if block has required structure, False otherwise
    """
    if not isinstance(block_config, dict):
        return False

    return (
        "source" in block_config and isinstance(block_config["source"], dict) and
        "target" in block_config and isinstance(block_config["target"], dict) and
        "other" in block_config and isinstance(block_config["other"], dict)
    )


def get_all_blocks(full_config: dict) -> dict:
    """
    Extract all valid configuration blocks from the config.

    A block is any top-level key whose value is a valid block config.
    Blocks are returned in their original order (Python 3.7+ dicts preserve insertion order).

    Args:
        full_config: Full configuration dictionary

    Returns:
        dict: Mapping of block_name -> block_config for all valid blocks
    """
    blocks = {}
    for key, value in full_config.items():
        if is_valid_block(value):
            blocks[key] = value
    return blocks


def find_block(full_config: dict, block_name: str) -> tuple:
    """
    Find a specific configuration block by name.

    Args:
        full_config: Full configuration dictionary
        block_name: Name of the block to find

    Returns:
        tuple: (block_name, block_config)

    Raises:
        ValueError: If block not found or invalid
    """
    if block_name not in full_config:
        available_blocks = list(get_all_blocks(full_config).keys())
        raise ValueError(
            f"Block '{block_name}' not found.\n"
            f"Available blocks: {', '.join(available_blocks) if available_blocks else 'None'}"
        )

    block_config = full_config[block_name]
    if not is_valid_block(block_config):
        raise ValueError(
            f"Block '{block_name}' is invalid. Must have 'source', 'target', and 'other' keys."
        )

    return (block_name, block_config)


def get_first_block(full_config: dict) -> tuple:
    """
    Get the first valid configuration block (for backward compatibility).

    Args:
        full_config: Full configuration dictionary

    Returns:
        tuple: (block_name, block_config)

    Raises:
        ValueError: If no valid blocks found
    """
    blocks = get_all_blocks(full_config)
    if not blocks:
        raise ValueError(
            "No valid configuration blocks found in config file.\n"
            "A valid block must have 'source', 'target', and 'other' keys."
        )

    first_name = next(iter(blocks.keys()))
    return (first_name, blocks[first_name])


def execute_block(block_name: str, block_config: dict, config_path: str, output_dir: str) -> list:
    """
    Execute a single configuration block.

    Args:
        block_name: Name of the block being executed
        block_config: Configuration for this block
        config_path: Path to the config file (for resolving relative paths)
        output_dir: Output directory for reports

    Returns:
        list: List of test results from the executor
    """
    # Extract validation script path
    validation_script = block_config["other"]["validation_script"]

    # If script is relative, resolve it relative to config file location
    config_dir = os.path.dirname(config_path)
    script_path = os.path.join(config_dir, validation_script)
    script_name = os.path.basename(script_path)

    test_cases = load_test_cases(script_path)

    # Extract source and target configurations
    source_config = block_config.get("source")
    target_config = block_config.get("target")

    # Get preprocessor queries path if specified
    preprocessor_queries_path = block_config["other"].get("preprocessor_queries")

    if preprocessor_queries_path:
        # Resolve relative path if needed
        if not os.path.isabs(preprocessor_queries_path):
            preprocessor_queries_path = os.path.join(config_dir, preprocessor_queries_path)

    # Execute tests with timing
    logger.info(f"Starting execution of block: {block_name} (script: {script_name})")
    executor = ValidationExecutor(
        source_config,
        target_config,
        test_cases,
        preprocessor_queries_path=preprocessor_queries_path
    )
    results = executor.run(script_name=script_name)

    # Add block_name to results for tracking
    for result in results:
        result["block_name"] = block_name

    return results


def main():
    parser = argparse.ArgumentParser(description="DataQE Framework - Data Quality and Validation Tool")
    parser.add_argument("--version", action="version", version=f"%(prog)s {__version__}")
    parser.add_argument("--config", required=True, help="Path to configuration YAML file")

    # Add mutually exclusive group for block selection
    block_group = parser.add_mutually_exclusive_group()
    block_group.add_argument(
        "--block",
        help="Execute a specific configuration block by name"
    )
    block_group.add_argument(
        "--all-blocks",
        action="store_true",
        help="Execute all configuration blocks found in the config file"
    )

    args = parser.parse_args()

    # Get output directory, create if needed, and clean it
    output_dir = get_output_dir()
    ensure_output_directory(output_dir)
    clean_output_directory(output_dir)

    full_config = load_config(args.config)

    # Determine which blocks to execute
    blocks_to_execute = []

    if args.block:
        # Execute specific block
        block_name, block_config = find_block(full_config, args.block)
        blocks_to_execute = [(block_name, block_config)]
        logger.info(f"Executing block: {block_name}")
    elif args.all_blocks:
        # Execute all blocks
        all_blocks = get_all_blocks(full_config)
        if not all_blocks:
            raise ValueError(
                "No valid configuration blocks found in config file.\n"
                "A valid block must have 'source', 'target', and 'other' keys."
            )
        blocks_to_execute = list(all_blocks.items())
        logger.info(f"Executing {len(blocks_to_execute)} blocks: {', '.join(all_blocks.keys())}")
    else:
        # Execute first block (backward compatibility)
        block_name, block_config = get_first_block(full_config)
        blocks_to_execute = [(block_name, block_config)]
        logger.info(f"Executing first block: {block_name}")

    # Execute all selected blocks and collect results
    all_results = []
    for block_name, block_config in blocks_to_execute:
        results = execute_block(block_name, block_config, args.config, output_dir)
        all_results.extend(results)

    # Generate execution summary
    summary = ExecutionSummary(all_results)

    # Report to console
    console_reporter = ConsoleReporter()
    for result in all_results:
        console_reporter.report_test_execution(result["test_name"], result)
    console_reporter.report_summary(summary)

    # Generate ExecutionReport.html and ExecutionReport.csv
    html_reporter = HTMLReporter(output_dir)
    html_report_path = html_reporter.generate_report(all_results, summary)
    logger.info(f"ExecutionReport.html generated: {html_report_path}")

    csv_reporter = CSVReporter(output_dir)
    csv_report_path = csv_reporter.generate_report(all_results, summary)
    logger.info(f"ExecutionReport.csv generated: {csv_report_path}")

    # Generate FailedExecutionReport.html (with failures or all-passed message)
    failed_reporter = FailedExecutionReporter(output_dir)
    failed_report_path = failed_reporter.generate_report(all_results, summary)
    logger.info(f"FailedExecutionReport.html generated: {failed_report_path}")

    # Generate AutomationData.csv for CI/CD integration
    automation_data_reporter = AutomationDataReporter(output_dir)
    app = os.environ.get("DATAQE_APP_NAME", "default_app")
    branch = os.environ.get("DATAQE_BRANCH", "default_branch")
    platform = os.environ.get("DATAQE_PLATFORM", "default_platform")
    owner = os.environ.get("DATAQE_OWNER", "default_owner")

    automation_data_path = automation_data_reporter.generate_report(
        all_results,
        summary,
        app=app,
        branch=branch,
        platform=platform,
        owner=owner,
        test_report_path=html_report_path
    )
    logger.info(f"AutomationData.csv generated: {automation_data_path}")

