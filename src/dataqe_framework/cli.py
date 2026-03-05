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


def parse_replacements(replace_args: list) -> dict:
    """
    Parse replacement arguments from command line.

    Format: --replace "var1,value1" --replace "var2,value2"
    Or:     --replace "@var1,value1" --replace "@var2,value2"

    Args:
        replace_args: List of replacement strings from argparse

    Returns:
        dict: Mapping of variable name to replacement value

    Raises:
        ValueError: If replacement format is invalid
    """
    replacements = {}
    if not replace_args:
        return replacements

    for arg in replace_args:
        parts = arg.split(",", 1)
        if len(parts) != 2:
            raise ValueError(
                f"Invalid replacement format: '{arg}'. "
                f"Expected format: 'variable,value' or '@variable,value'"
            )

        var_name, var_value = parts
        # Remove @ prefix if present
        if var_name.startswith("@"):
            var_name = var_name[1:]

        replacements[var_name] = var_value

    return replacements


def apply_replacements(test_cases: dict, replacements: dict) -> dict:
    """
    Apply variable replacements to test cases recursively.

    Replaces:
    - ENVIRONMENT with SPRING_PROFILES_ACTIVE env var (default: 'gcpqa')
    - Custom variables with format: variable_name or @variable_name

    Args:
        test_cases: Test cases dictionary loaded from YAML
        replacements: Dictionary of variable -> value replacements

    Returns:
        dict: Test cases with variables replaced
    """
    # Get ENVIRONMENT replacement (default to 'gcpqa')
    environment = os.environ.get("SPRING_PROFILES_ACTIVE", "gcpqa")
    all_replacements = {"ENVIRONMENT": environment}
    all_replacements.update(replacements)

    def replace_in_dict(obj):
        """Recursively replace variables in dictionaries and strings."""
        if isinstance(obj, dict):
            return {k: replace_in_dict(v) for k, v in obj.items()}
        elif isinstance(obj, list):
            return [replace_in_dict(item) for item in obj]
        elif isinstance(obj, str):
            result = obj
            for var_name, var_value in all_replacements.items():
                # Replace both VARIABLE and @VARIABLE formats
                result = result.replace(var_name, str(var_value))
                result = result.replace(f"@{var_name}", str(var_value))
            return result
        else:
            return obj

    return replace_in_dict(test_cases)


def load_test_cases(script_path: str, replacements: dict = None):
    """
    Load test cases from YAML file and apply variable replacements.

    Args:
        script_path: Path to test script YAML file
        replacements: Optional dictionary of variables to replace

    Returns:
        dict: Test cases with replacements applied
    """
    if not os.path.exists(script_path):
        raise FileNotFoundError(f"Test script not found: {script_path}")

    with open(script_path, "r") as file:
        test_cases = yaml.safe_load(file)

    if replacements is None:
        replacements = {}

    return apply_replacements(test_cases, replacements)


def get_output_dir(cli_output_dir: str = None) -> str:
    """
    Get output directory from CLI argument, environment variable, or default.

    Priority order:
    1. CLI argument (--output-dir)
    2. Environment variable (DATAQE_OUTPUT_DIR)
    3. Default (./output)

    Args:
        cli_output_dir: Output directory from CLI argument

    Returns:
        str: Path to output directory
    """
    if cli_output_dir:
        return cli_output_dir
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


def save_invalid_tests(output_dir: str, failed_test_names: list) -> str:
    """
    Save list of failed/errored test names to .dataqe_invalid_tests.yml.

    Args:
        output_dir: Output directory to save the file
        failed_test_names: List of test names that failed

    Returns:
        str: Path to saved file
    """
    if not failed_test_names:
        return None

    filepath = Path(output_dir) / ".dataqe_invalid_tests.yml"

    invalid_list = {"invalid_tests": failed_test_names}

    with open(filepath, "w") as f:
        yaml.dump(invalid_list, f, default_flow_style=False)

    logger.info(f"Saved {len(failed_test_names)} invalid tests to: {filepath}")
    return str(filepath)


def load_invalid_tests(output_dir: str) -> list:
    """
    Load list of invalid test names from .dataqe_invalid_tests.yml.

    Args:
        output_dir: Directory to look for the invalid tests file

    Returns:
        list: List of invalid test names, empty list if file doesn't exist
    """
    filepath = Path(output_dir) / ".dataqe_invalid_tests.yml"

    if not filepath.exists():
        return []

    try:
        with open(filepath, "r") as f:
            data = yaml.safe_load(f)
            invalid_tests = data.get("invalid_tests", []) if data else []
            logger.info(f"Loaded {len(invalid_tests)} invalid tests from: {filepath}")
            return invalid_tests
    except Exception as e:
        logger.warning(f"Error loading invalid tests file: {e}")
        return []


def filter_test_cases_by_invalid_list(test_cases: list, invalid_test_names: list) -> tuple:
    """
    Filter test cases to mark tests in the invalid list with 'invalid: true'.

    Args:
        test_cases: Original list of test case dictionaries
        invalid_test_names: List of test names to mark as invalid

    Returns:
        tuple: (filtered_test_cases, count_of_marked_tests)
    """
    if not invalid_test_names:
        return test_cases, 0

    marked_count = 0
    for test in test_cases:
        test_name = list(test.keys())[0]
        if test_name in invalid_test_names:
            test[test_name]["invalid"] = True
            marked_count += 1

    return test_cases, marked_count


def execute_block(block_name: str, block_config: dict, config_path: str, output_dir: str, replacements: dict = None, invalid_test_names: list = None, fail_on_error: bool = False) -> list:
    """
    Execute a single configuration block.

    Args:
        block_name: Name of the block being executed
        block_config: Configuration for this block
        config_path: Path to the config file (for resolving relative paths)
        output_dir: Output directory for reports
        replacements: Optional dictionary of variables to replace in test cases
        invalid_test_names: Optional list of test names to mark as invalid (skip)
        fail_on_error: If True, raise exception on query execution errors

    Returns:
        list: List of test results from the executor

    Raises:
        RuntimeError: If fail_on_error=True and a test encounters a query error
    """
    # Extract validation script path
    validation_script = block_config["other"]["validation_script"]

    # Resolve validation script path:
    # - If absolute, use as-is
    # - If relative, resolve from current working directory
    if os.path.isabs(validation_script):
        script_path = validation_script
    else:
        script_path = os.path.abspath(validation_script)

    script_name = os.path.basename(script_path)

    test_cases = load_test_cases(script_path, replacements)

    # Mark tests as invalid if they're in the invalid list
    if invalid_test_names:
        test_cases, marked_count = filter_test_cases_by_invalid_list(test_cases, invalid_test_names)
        logger.info(f"Marked {marked_count} tests as invalid (will be skipped)")

    # Extract source and target configurations
    source_config = block_config.get("source")
    target_config = block_config.get("target")

    # Get preprocessor queries path if specified
    preprocessor_queries_path = block_config["other"].get("preprocessor_queries")

    if preprocessor_queries_path:
        # Resolve relative path from current working directory if not absolute
        if not os.path.isabs(preprocessor_queries_path):
            preprocessor_queries_path = os.path.abspath(preprocessor_queries_path)

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

    # Check for errors if fail_on_error is set
    if fail_on_error:
        error_results = [r for r in results if r.get("error_occurred", False)]
        if error_results:
            error_details = "\n".join(
                f"  - {r['test_name']}: {r.get('error_type', 'Unknown')} - {r.get('error_message', 'Unknown')}"
                for r in error_results
            )
            raise RuntimeError(
                f"Query execution errors encountered in block '{block_name}':\n{error_details}\n"
                f"Use --continue-on-error flag to skip this check."
            )

    return results


def main():
    parser = argparse.ArgumentParser(description="DataQE Framework - Data Quality and Validation Tool")
    parser.add_argument("--version", action="version", version=f"%(prog)s {__version__}")
    parser.add_argument("--config", required=True, help="Path to configuration YAML file")
    parser.add_argument(
        "--output-dir",
        help="Output directory for reports (default: ./output or DATAQE_OUTPUT_DIR env var)"
    )
    parser.add_argument(
        "--replace",
        action="append",
        dest="replace",
        help="Replace variables in test scripts (format: variable,value or @variable,value). "
             "ENVIRONMENT is automatically set to SPRING_PROFILES_ACTIVE env var (default: gcpqa). "
             "Can be used multiple times: --replace var1,value1 --replace var2,value2"
    )

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

    # Add error handling flags
    parser.add_argument(
        "--skip-invalid",
        action="store_true",
        help="Skip tests marked with 'invalid: true' in YAML"
    )
    parser.add_argument(
        "--load-invalid-list",
        action="store_true",
        help="Load and skip tests from .dataqe_invalid_tests.yml (auto-generated from previous run errors)"
    )
    parser.add_argument(
        "--fail-on-error",
        action="store_true",
        help="Exit immediately if any query execution error occurs (strict mode)"
    )

    args = parser.parse_args()

    # Parse variable replacements
    replacements = parse_replacements(args.replace or [])
    if replacements:
        logger.info(f"Variable replacements: {', '.join(f'{k}={v}' for k, v in replacements.items())}")

    # Get output directory, create if needed, and clean it
    output_dir = get_output_dir(args.output_dir)
    ensure_output_directory(output_dir)
    clean_output_directory(output_dir)

    # Load invalid tests list if flag is set
    invalid_test_names = []
    if args.load_invalid_list:
        invalid_test_names = load_invalid_tests(output_dir)
        if invalid_test_names:
            logger.info(f"Loaded {len(invalid_test_names)} invalid tests to skip")

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
        results = execute_block(
            block_name,
            block_config,
            args.config,
            output_dir,
            replacements=replacements,
            invalid_test_names=invalid_test_names,
            fail_on_error=args.fail_on_error
        )
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

    # Save list of tests with errors to .dataqe_invalid_tests.yml for next run
    error_test_names = [r["test_name"] for r in all_results if r.get("error_occurred", False)]
    if error_test_names:
        invalid_tests_path = save_invalid_tests(output_dir, error_test_names)
        logger.info(
            f"Next run: Use --load-invalid-list flag to automatically skip these {len(error_test_names)} tests"
        )

