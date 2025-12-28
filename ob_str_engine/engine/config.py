"""Engine configuration loading with validation and error handling."""

import json
from pathlib import Path
from typing import Dict, Any


def load_engine_config(path: Path) -> Dict[str, Any]:
    """
    Load and validate engine configuration from JSON file.

    Args:
        path: Path to engine configuration JSON file

    Returns:
        Engine configuration dictionary

    Raises:
        FileNotFoundError: If config file doesn't exist
        ValueError: If JSON is invalid or required keys are missing
        PermissionError: If file cannot be read due to permissions
    """
    if not isinstance(path, Path):
        path = Path(path)

    # Check file exists
    if not path.exists():
        raise FileNotFoundError(
            f"Engine configuration file not found: {path}\n"
            f"Expected location: {path.absolute()}"
        )

    # Check file is readable
    if not path.is_file():
        raise ValueError(f"Path exists but is not a file: {path}")

    try:
        with open(path, "r", encoding="utf-8") as f:
            config = json.load(f)
    except PermissionError as e:
        raise PermissionError(
            f"Permission denied reading config file: {path}"
        ) from e
    except json.JSONDecodeError as e:
        raise ValueError(
            f"Invalid JSON in engine config file: {path}\n"
            f"Error at line {e.lineno}, column {e.colno}: {e.msg}"
        ) from e
    except Exception as e:
        raise ValueError(
            f"Unexpected error reading config file: {path}\n"
            f"Error: {e}"
        ) from e

    # Basic validation - check for required top-level keys
    required_keys = ['constants', 'calendar', 'banking', 'market']
    missing_keys = [key for key in required_keys if key not in config]

    if missing_keys:
        raise ValueError(
            f"Engine config missing required keys: {missing_keys}\n"
            f"File: {path}\n"
            f"Required keys: {required_keys}"
        )

    return config
