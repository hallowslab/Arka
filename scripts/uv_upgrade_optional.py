"""
Upgrade git-sourced optional dependencies to latest branch HEAD, then sync.

uv.lock pins git deps to commits; `uv sync` alone does not move them.
Uses ENABLED_APPS (same as dev_migrate / Django settings) to decide which
extras to refresh: load .env, read ENABLED_APPS from the environment, or
fall back to the ENABLED_APPS list in scripts/dev_migrate.py.

Usage:
  python scripts/uv_upgrade_optional.py [--dry-run]
"""

from __future__ import annotations

import argparse
import os
import subprocess
import sys
from pathlib import Path

# Reuse dev_migrate env loading and default app list.
_script_dir = Path(__file__).resolve().parent
if str(_script_dir) not in sys.path:
    sys.path.insert(0, str(_script_dir))
from dev_migrate import ENABLED_APPS, load_env  # noqa: E402


def resolve_enabled_apps() -> list[str]:
    """Return modular app names (uppercase) from env or dev_migrate defaults."""
    raw = os.environ.get("ENABLED_APPS", "").strip()
    if raw:
        return [name.strip().upper() for name in raw.split(",") if name.strip()]
    return list(ENABLED_APPS)


def app_names_to_packages(app_names: list[str]) -> list[str]:
    """Map ENABLED_APPS entries (AERA, PYMAP, …) to uv extra / package names."""
    return sorted({name.lower() for name in app_names})


def run_cmd(cmd: list[str], *, cwd: Path, dry_run: bool) -> int:
    print(f"[>] {' '.join(cmd)}")
    if dry_run:
        return 0
    result = subprocess.run(cmd, cwd=cwd, check=False)
    return result.returncode


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Upgrade ENABLED_APPS git optional deps in uv.lock and sync"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Print commands without running uv",
    )
    args = parser.parse_args()

    root_dir = _script_dir.parent
    env_file = root_dir / "dev.env"

    print("[*] ARKA optional dependency upgrade")
    print(f"[*] Root directory: {root_dir}")

    if env_file.exists():
        print(f"[*] Loading environment variables from {env_file}...")
        load_env(env_file)
    else:
        dev_env = root_dir / "dev.env"
        if dev_env.exists():
            print(f"[*] .env not found, loading from {dev_env}...")
            load_env(dev_env)

    enabled_apps = resolve_enabled_apps()
    if not enabled_apps:
        print("[!] Error: ENABLED_APPS is empty. Set it in .env or dev_migrate.py.")
        return 1

    packages = app_names_to_packages(enabled_apps)
    print(f"[*] Modular apps enabled: {', '.join(enabled_apps)}")
    print(f"[*] Packages to upgrade: {', '.join(packages)}")

    for package in packages:
        rc = run_cmd(
            ["uv", "lock", "--upgrade-package", package],
            cwd=root_dir,
            dry_run=args.dry_run,
        )
        if rc != 0:
            print(f"[!] Error: uv lock failed for {package} (exit {rc})")
            return rc

    sync_cmd = ["uv", "sync"]
    for package in packages:
        sync_cmd.extend(["--extra", package])

    rc = run_cmd(sync_cmd, cwd=root_dir, dry_run=args.dry_run)
    if rc != 0:
        print("[!] Error: uv sync failed")
        return rc

    print("\n[+] SUCCESS: Optional git dependencies upgraded and synced.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
