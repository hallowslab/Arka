import os
import sys
import subprocess
from pathlib import Path

ENABLED_APPS = ["AERA", "PYMAP", "DBTOOL", "NETTOOLS", "MXR"]


def load_env(env_path):
    """
    Manually load environment variables from a .env file.
    """
    if not env_path.exists():
        print(f"Warning: {env_path} not found.")
        return
    with open(env_path) as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            if "=" not in line:
                continue
            key, value = line.split("=", 1)
            # Remove surrounding quotes from value
            value = value.strip('"').strip("'")
            os.environ[key] = value


def main():
    # Identify project paths
    script_dir = Path(__file__).resolve().parent
    root_dir = script_dir.parent
    src_dir = root_dir / "src"
    env_file = root_dir / ".env"

    print(f"[*] ARKA Migration Helper Script")
    print(f"[*] Root directory: {root_dir}")

    # 1. Load .env
    if env_file.exists():
        print(f"[*] Loading environment variables from {env_file}...")
        load_env(env_file)
    else:
        # Fallback to dev.env if .env doesn't exist
        dev_env = root_dir / "dev.env"
        if dev_env.exists():
            print(f"[*] .env not found, loading from {dev_env}...")
            load_env(dev_env)

    # 2. Set mandatory environment variables for local migrations
    os.environ["DJANGO_ENV"] = "migrations"
    os.environ["ENABLED_APPS"] = ",".join(ENABLED_APPS)
    local_log_dir = root_dir / "ARKA_LOGS"
    local_log_dir.mkdir(exist_ok=True)
    os.environ["ARKA_LOGDIR"] = str(local_log_dir)

    print(f"[*] DJANGO_ENV set to 'migrations' (using SQLite)")
    print(f"[*] ARKA_LOGDIR set to {local_log_dir}")
    print(f"[*] Modular apps enabled: {', '.join(ENABLED_APPS)}")

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
