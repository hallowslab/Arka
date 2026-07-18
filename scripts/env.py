"""
Shared environment loading for ARKA scripts.

Provides .env file parsing, project env discovery, and ENABLED_APPS resolution.
"""

import os
from pathlib import Path


def load_env(env_path):
    """Parse a .env file and load variables into os.environ.

    Skips comments, blank lines, and lines without '='.
    Strips surrounding quotes from values.
    """
    if not env_path.exists():
        print(f"Warning: {env_path} not found.")
        return False
    with open(env_path) as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            if "=" not in line:
                continue
            key, value = line.split("=", 1)
            value = value.strip('"').strip("'")
            os.environ[key] = value
    return True


def find_env_file(root_dir):
    """Find the project env file: dev.env → .env → None."""
    root_dir = Path(root_dir)
    for name in ("dev.env", ".env"):
        path = root_dir / name
        if path.exists():
            return path
    return None


def load_project_env(root_dir=None):
    """Discover and load the project env file.

    Returns the Path of the loaded file, or None if not found.
    """
    if root_dir is None:
        root_dir = Path(__file__).resolve().parent.parent
    else:
        root_dir = Path(root_dir)

    env_file = find_env_file(root_dir)
    if env_file is None:
        print(f"[!] No .env or dev.env found in {root_dir}")
        return None

    print(f"[*] Loading environment from {env_file.name}...")
    load_env(env_file)
    return env_file


def get_enabled_apps():
    """Return ENABLED_APPS as a list of uppercase strings."""
    raw = os.environ.get("ENABLED_APPS", "").strip()
    if not raw:
        return []
    return [name.strip().upper() for name in raw.split(",") if name.strip()]
