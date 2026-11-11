"""Run pytest for enabled Django apps only.

Reads ENABLED_APPS from dev.env/.env and runs tests found in each app's
tests/ package.  Falls back to running all discoverable tests if no apps
are specified.

Convention: each app's tests live at
    src/modular_apps/{NAME}/{name_lower}/tests/

Usage:
    uv run python scripts/dev_test.py            # enabled apps only
    uv run python scripts/dev_test.py mimir      # specific app(s)
    uv run python scripts/dev_test.py -- -x      # pass extra args to pytest
"""

import subprocess
import sys
from pathlib import Path

from env import get_enabled_apps, load_project_env

PROJECT_ROOT = Path(__file__).resolve().parent.parent
APPS_DIR = PROJECT_ROOT / "src" / "modular_apps"


def discover_test_dir(app_name):
    """Find the tests/ package for an app by convention.

    Looks for: src/modular_apps/{NAME}/{name_lower}/tests/
    Returns the Path if it exists and contains test files, else None.
    """
    upper = app_name.upper()
    lower = upper.lower()
    test_dir = APPS_DIR / upper / lower / "tests"
    if not test_dir.is_dir():
        return None
    # Must contain at least one test_*.py file
    has_tests = any(test_dir.glob("test_*.py"))
    conftest = test_dir / "conftest.py"
    if not has_tests and not conftest.exists():
        return None
    return test_dir


def main():
    load_project_env(PROJECT_ROOT)

    # Positional args = app names; everything after -- goes to pytest
    app_args = []
    pytest_args = []
    pass_through = False
    for arg in sys.argv[1:]:
        if arg == "--":
            pass_through = True
            continue
        if pass_through:
            pytest_args.append(arg)
        else:
            app_args.append(arg)

    # Determine which apps to test
    if app_args:
        apps_to_test = [a.upper() for a in app_args]
    else:
        apps_to_test = get_enabled_apps()

    if not apps_to_test:
        print("[*] No apps specified and ENABLED_APPS is empty.")
        print("    Running all discoverable tests...")
        test_dirs = []
    else:
        test_dirs = []
        skipped = []
        for app_name in apps_to_test:
            test_dir = discover_test_dir(app_name)
            if test_dir is None:
                skipped.append(app_name)
                continue
            test_dirs.append(str(test_dir))

        if skipped:
            print(f"[*] Skipping (no tests/ found): {', '.join(skipped)}")

        if not test_dirs:
            print("[!] No test directories found for any of the requested apps.")
            sys.exit(1)

    cmd = [sys.executable, "-m", "pytest", "-v", *test_dirs, *pytest_args]
    print(f"[*] {' '.join(cmd)}")
    result = subprocess.run(cmd, cwd=PROJECT_ROOT)
    sys.exit(result.returncode)


if __name__ == "__main__":
    main()
