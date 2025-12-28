"""
Scenario Manager - Save and load scenario configurations
"""

import json
import os
from pathlib import Path
from typing import Dict, Any, List
from datetime import datetime


def get_scenarios_dir() -> Path:
    """Get the scenarios directory path"""
    return Path(__file__).parent.parent / "scenarios"


def list_scenarios() -> List[str]:
    """List all saved scenarios"""
    scenarios_dir = get_scenarios_dir()
    if not scenarios_dir.exists():
        scenarios_dir.mkdir(parents=True, exist_ok=True)
        return []

    return [f.stem for f in scenarios_dir.glob("*.json")]


def save_scenario(name: str, config: Dict[str, Any]) -> Path:
    """
    Save a scenario configuration.

    Args:
        name: Scenario name (will be sanitized for filename)
        config: Configuration dictionary

    Returns:
        Path to saved file
    """
    scenarios_dir = get_scenarios_dir()
    scenarios_dir.mkdir(parents=True, exist_ok=True)

    # Sanitize filename
    safe_name = "".join(c for c in name if c.isalnum() or c in "._- ")
    safe_name = safe_name.strip().replace(" ", "_")

    file_path = scenarios_dir / f"{safe_name}.json"

    # Add metadata
    config_with_meta = config.copy()
    config_with_meta["_metadata"] = {
        "name": name,
        "saved_at": datetime.now().isoformat(),
    }

    with open(file_path, 'w') as f:
        json.dump(config_with_meta, f, indent=2)

    return file_path


def load_scenario(name: str) -> Dict[str, Any]:
    """
    Load a saved scenario configuration.

    Args:
        name: Scenario name (without .json extension)

    Returns:
        Configuration dictionary
    """
    scenarios_dir = get_scenarios_dir()
    file_path = scenarios_dir / f"{name}.json"

    if not file_path.exists():
        raise FileNotFoundError(f"Scenario '{name}' not found")

    with open(file_path, 'r') as f:
        config = json.load(f)

    # Remove metadata before returning
    config.pop("_metadata", None)

    return config


def delete_scenario(name: str) -> bool:
    """
    Delete a saved scenario.

    Args:
        name: Scenario name

    Returns:
        True if deleted, False if not found
    """
    scenarios_dir = get_scenarios_dir()
    file_path = scenarios_dir / f"{name}.json"

    if file_path.exists():
        file_path.unlink()
        return True
    return False


def get_cache_dir() -> Path:
    """Get the cache directory path"""
    return Path(__file__).parent.parent / "cache"


def clear_cache() -> int:
    """
    Clear all cached simulation results.

    Returns:
        Number of files deleted
    """
    cache_dir = get_cache_dir()
    if not cache_dir.exists():
        return 0

    count = 0
    for f in cache_dir.glob("*.pkl"):
        f.unlink()
        count += 1

    return count
