import os
import subprocess
import sys
from pathlib import Path


def main():
    """
    ARKA Version Exporter Helper
    Automates 'poetry-version-exporter' for the main project and all modular apps.
    """
    # Identify project paths
    script_dir = Path(__file__).resolve().parent
    root_dir = script_dir.parent
    src_dir = root_dir / "src"

    print(f"[*] ARKA Version Exporter Helper")
    print(f"[*] Root directory: {root_dir}")

    if not src_dir.exists():
        print(f"[!] Error: 'src' directory not found at {src_dir}")
        sys.exit(1)

    # Base tasks - Arka is the core monolith
    tasks = [
        {
            "name": "arka",
            "output": src_dir / "arka" / "_version.py",
            "pyproject": root_dir / "pyproject.toml",
        },
    ]

    # Discover modular apps
    modular_apps_dir = src_dir / "modular_apps"
    if modular_apps_dir.exists():
        for app_dir in modular_apps_dir.iterdir():
            # Check for directories with pyproject.toml
            if (
                app_dir.is_dir()
                and not app_dir.name.startswith(".")
                and (app_dir / "pyproject.toml").exists()
            ):
                app_folder_name = app_dir.name
                pkg_name = app_folder_name.lower()

                # Check for package directory inside (e.g. src/modular_apps/AERA/aera/)
                pkg_dir = app_dir / pkg_name
                if pkg_dir.exists():
                    tasks.append(
                        {
                            "name": pkg_name,
                            "output": pkg_dir / "_version.py",
                            "pyproject": app_dir / "pyproject.toml",
                        }
                    )
                else:
                    print(
                        f"[-] Warning: Package directory {pkg_dir} not found for {app_folder_name}. Skipping."
                    )

    print(f"[*] Found {len(tasks)} targets to version.")

    failed = []
    for task in tasks:
        name = task["name"]
        output = task["output"]
        pyproject = task["pyproject"]

        print(f"\n[>] Exporting version for '{name}'...")
        print(f"    Project: {pyproject.relative_to(root_dir)}")
        print(f"    Target:  {output.relative_to(root_dir)}")

        try:
            # Running from root directory for consistent path resolution
            subprocess.run(
                [
                    "uv",
                    "run",
                    "poetry-version-exporter",
                    "-n",
                    name,
                    "-p",
                    str(pyproject),
                    "-o",
                    str(output),
                ],
                check=True,
                cwd=str(root_dir),
                capture_output=True,
                text=True,
            )
            print(f"    [+] Success")
        except subprocess.CalledProcessError as e:
            error_msg = e.stderr.strip() or e.stdout.strip() or str(e)
            print(f"    [!] Error: {error_msg}")
            failed.append(name)
        except FileNotFoundError:
            print(f"    [!] Error: 'uv' command not found. Ensure uv is installed.")
            sys.exit(1)
        except Exception as e:
            print(f"    [!] Unexpected error: {e}")
            failed.append(name)

    if failed:
        print(f"\n[!] COMPLETED WITH ERRORS. Failed apps: {', '.join(failed)}")
        sys.exit(1)
    else:
        print(f"\n[+] SUCCESS: All versions exported successfully.")


if __name__ == "__main__":
    main()
