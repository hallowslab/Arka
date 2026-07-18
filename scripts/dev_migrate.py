import os
import sys
import subprocess
from pathlib import Path

from env import load_project_env, get_enabled_apps


def main():
    script_dir = Path(__file__).resolve().parent
    root_dir = script_dir.parent
    src_dir = root_dir / "src"

    print(f"[*] ARKA Migration Helper Script")
    print(f"[*] Root directory: {root_dir}")

    # 1. Load .env
    load_project_env(root_dir)

    # 2. Set mandatory environment variables for local management commands
    os.environ["DJANGO_ENV"] = "migrations"
    local_log_dir = root_dir / "ARKA_LOGS"
    local_log_dir.mkdir(exist_ok=True)
    os.environ["ARKA_LOGDIR"] = str(local_log_dir)

    print(f"[*] DJANGO_ENV set to 'migrations' (using SQLite)")
    print(f"[*] ARKA_LOGDIR set to {local_log_dir}")
    print(f"[*] Modular apps enabled: {', '.join(get_enabled_apps())}")

    if not src_dir.exists():
        print(f"[!] Error: 'src' directory not found at {src_dir}")
        sys.exit(1)

    manage_py = str(root_dir / "src" / "manage.py")
    if not os.path.exists(manage_py):
        print(f"[!] Error: {manage_py} not found in {os.getcwd()}")
        sys.exit(1)

    python_exe = sys.executable

    # 4. Run Django management commands
    try:
        print("\n[>] Step 1: Running makemigrations...")
        subprocess.run(
            [python_exe, str(root_dir / "src" / "manage.py"), "makemigrations"],
            check=True,
        )

        print("\n[>] Step 2: Running migrate...")
        subprocess.run(
            [python_exe, str(root_dir / "src" / "manage.py"), "migrate"], check=True
        )

        print("\n[+] SUCCESS: Migrations completed successfully.")
    except subprocess.CalledProcessError as e:
        print(f"\n[!] ERROR: Command failed with return code {e.returncode}")
        sys.exit(e.returncode)
    except Exception as e:
        print(f"\n[!] UNEXPECTED ERROR: {str(e)}")
        sys.exit(1)


if __name__ == "__main__":
    main()
