"""
Configuration loader for Sigen API credentials.
Loads credentials from secrets.json file or environment variables.
"""

import json
import os
from typing import Dict, Optional


def load_from_secrets(secrets_file: str = "secrets.json") -> Dict[str, str]:
    """
    Load Sigen API configuration from a secrets JSON file.

    Args:
        secrets_file: Path to the secrets JSON file

    Returns:
        Dictionary with configuration keys: base_url, username, password
    """
    with open(secrets_file, 'r') as f:
        secrets = json.load(f)

    sigen_config = secrets.get('sigen', {})
    return {
        'base_url': sigen_config.get('base_url'),
        'username': sigen_config.get('username'),
        'password': sigen_config.get('password')
    }


def load_from_env() -> Dict[str, str]:
    """
    Load Sigen API configuration from environment variables.

    Expected environment variables:
    - SIGEN_BASE_URL
    - SIGEN_USERNAME
    - SIGEN_PASSWORD

    Returns:
        Dictionary with configuration keys: base_url, username, password
    """
    config = {
        'base_url': os.getenv('SIGEN_BASE_URL'),
        'username': os.getenv('SIGEN_USERNAME'),
        'password': os.getenv('SIGEN_PASSWORD')
    }

    # Filter out None values
    return {k: v for k, v in config.items() if v is not None}


def get_config(secrets_file: Optional[str] = None) -> Dict[str, str]:
    """
    Get Sigen API configuration from available sources.
    Tries secrets.json file first, then falls back to environment variables.

    Args:
        secrets_file: Optional path to secrets JSON file (default: secrets.json)

    Returns:
        Dictionary with configuration keys

    Raises:
        ValueError: If no valid configuration is found
    """
    # Try loading from secrets file
    secrets_path = secrets_file or "secrets.json"
    if os.path.exists(secrets_path):
        try:
            config = load_from_secrets(secrets_path)
            if config.get('base_url') and config.get('username') and config.get('password'):
                return config
        except Exception:
            pass

    # Fall back to environment variables
    config = load_from_env()
    if config.get('base_url') and config.get('username') and config.get('password'):
        return config

    raise ValueError(
        "No valid Sigen API configuration found. "
        "Please create a secrets.json file (see secrets.json.example) or set environment variables "
        "(SIGEN_BASE_URL, SIGEN_USERNAME, SIGEN_PASSWORD)."
    )
