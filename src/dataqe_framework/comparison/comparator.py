import re
import logging

logger = logging.getLogger(__name__)


def _parse_expected_condition(expected_str):
    """
    Parse expected condition string like "<=2", ">5", "==10".

    Args:
        expected_str: String like "<=2", ">5", "==10", "!=0"

    Returns:
        Tuple of (operator, value) or (None, None) if not a condition
    """
    if not isinstance(expected_str, str):
        return None, None

    # Match operators: <=, >=, ==, !=, <, >
    match = re.match(r'^(<=|>=|==|!=|<|>)\s*(-?\d+(?:\.\d+)?)\s*$', expected_str.strip())

    if match:
        operator = match.group(1)
        value = float(match.group(2))
        return operator, value

    return None, None


def _apply_operator(value, operator, threshold):
    """
    Apply comparison operator.

    Args:
        value: The actual value to compare
        operator: The operator (<=, >=, <, >, ==, !=)
        threshold: The threshold value to compare against

    Returns:
        True if condition is met, False otherwise
    """
    try:
        if operator == "<=":
            return value <= threshold
        elif operator == ">=":
            return value >= threshold
        elif operator == "<":
            return value < threshold
        elif operator == ">":
            return value > threshold
        elif operator == "==":
            return value == threshold
        elif operator == "!=":
            return value != threshold
    except (TypeError, ValueError):
        logger.warning(f"Cannot compare {value} with {threshold} using operator {operator}")
        return False

    return False


def compare_values(source_value, target_value, test_config):
    """
    Compare source and target values with support for various comparison modes.

    Supported modes:
    1. Source-only with expected condition: "<=2", ">5", etc.
    2. Source vs target equality
    3. Source vs target with threshold (percentage, absolute)
    4. Source vs target with condition operator

    Args:
        source_value: Value from source query
        target_value: Value from target query (can be None for source-only tests)
        test_config: Test configuration dictionary with:
            - source.expected: Expected condition for source (e.g., "<=2")
            - comparisons.threshold: Threshold configuration
            - comparisons.comment: Description of the comparison

    Returns:
        "PASS" or "FAIL"
    """
    comparisons = test_config.get("comparisons", {})
    source_config = test_config.get("source", {})

    # Source-only test (no target)
    if target_value is None:
        expected = source_config.get("expected")

        # Check if expected is a condition like "<=2"
        operator, threshold = _parse_expected_condition(expected)

        if operator and threshold is not None:
            # Condition-based comparison
            if _apply_operator(source_value, operator, threshold):
                logger.debug(f"Source value {source_value} {operator} {threshold}: PASS")
                return "PASS"
            else:
                logger.debug(f"Source value {source_value} {operator} {threshold}: FAIL")
                return "FAIL"
        else:
            # Backward compatibility: if no condition, check if source is truthy
            return "PASS" if source_value else "FAIL"

    # Source and target comparison
    if source_value == target_value:
        return "PASS"

    # Check threshold-based comparison
    threshold = comparisons.get("threshold")

    if threshold:
        condition = threshold.get("condition")
        threshold_value = threshold.get("value")
        threshold_limit = threshold.get("limit")

        # Condition-based threshold (e.g., condition: ">")
        # When condition is specified, FAIL if the condition IS TRUE
        if condition and not threshold_value:
            if _apply_operator(source_value, condition, target_value):
                logger.debug(f"Source {source_value} {condition} Target {target_value}: FAIL")
                return "FAIL"
            else:
                logger.debug(f"Source {source_value} {condition} Target {target_value}: PASS")
                return "PASS"

        # Percentage-based threshold
        if threshold_value == "percentage" and threshold_limit is not None:
            try:
                if target_value == 0:
                    # Can't calculate percentage when target is 0
                    return "FAIL" if source_value != target_value else "PASS"

                percentage_diff = abs((source_value - target_value) / target_value) * 100
                if percentage_diff > threshold_limit:
                    logger.debug(f"Percentage diff {percentage_diff}% > limit {threshold_limit}%: FAIL")
                    return "FAIL"
                else:
                    logger.debug(f"Percentage diff {percentage_diff}% <= limit {threshold_limit}%: PASS")
                    return "PASS"
            except (TypeError, ValueError):
                logger.warning(f"Cannot calculate percentage threshold for {source_value} vs {target_value}")
                return "FAIL"

        # Absolute threshold
        if threshold_value == "absolute" and threshold_limit is not None:
            try:
                absolute_diff = abs(source_value - target_value)
                if absolute_diff > threshold_limit:
                    logger.debug(f"Absolute diff {absolute_diff} > limit {threshold_limit}: FAIL")
                    return "FAIL"
                else:
                    logger.debug(f"Absolute diff {absolute_diff} <= limit {threshold_limit}: PASS")
                    return "PASS"
            except (TypeError, ValueError):
                logger.warning(f"Cannot calculate absolute threshold for {source_value} vs {target_value}")
                return "FAIL"

    # Default: if values don't match and no threshold passes, FAIL
    return "FAIL"

