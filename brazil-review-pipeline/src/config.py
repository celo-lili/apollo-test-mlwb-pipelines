"""Configuration loading.

Loads config.yaml fresh on every call (no caching) so that changes — e.g. toggling
``ingestion.write_back`` — take effect without restarting the kernel. Do NOT add
``@lru_cache`` here; see the skill guide.
"""
from __future__ import annotations

import os
import yaml

# Default config path: project root, regardless of the caller's cwd.
_DEFAULT_CONFIG_PATH = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "config.yaml"
)


def get_config(path: str | None = None) -> dict:
    """Return the parsed config.yaml as a dict.

    Args:
        path: optional explicit path; defaults to config.yaml at the project root.
    """
    with open(path or _DEFAULT_CONFIG_PATH) as f:
        return yaml.safe_load(f)
