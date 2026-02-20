import yaml
import os
import re


def load_config(config_path: str) -> dict:
    """
    Loads YAML configuration file with support for environment variable substitution.

    Supports ${VAR_NAME} and ${VAR_NAME:default_value} syntax for environment variables.
    """

    if not os.path.exists(config_path):
        raise FileNotFoundError(f"Config file not found: {config_path}")

    with open(config_path, "r") as file:
        config_content = file.read()

    # Substitute environment variables
    config_content = _substitute_env_vars(config_content)

    config = yaml.safe_load(config_content)

    return config


def _substitute_env_vars(content: str) -> str:
    """
    Replace environment variable placeholders in config content.

    Supports:
    - ${VAR_NAME}: Requires VAR_NAME to be set
    - ${VAR_NAME:default}: Uses default if VAR_NAME is not set
    """

    def replace_var(match):
        var_expr = match.group(1)

        # Check if default value is provided
        if ":" in var_expr:
            var_name, default_value = var_expr.split(":", 1)
        else:
            var_name = var_expr
            default_value = None

        value = os.environ.get(var_name, default_value)

        if value is None:
            raise ValueError(
                f"Environment variable '{var_name}' is not set and no default provided"
            )

        return value

    # Replace ${VAR_NAME} and ${VAR_NAME:default}
    pattern = r"\$\{([^}]+)\}"
    return re.sub(pattern, replace_var, content)

