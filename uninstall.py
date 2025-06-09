#!/usr/bin/env python3
import subprocess
import sys
from pathlib import Path


def run_command(cmd: list[str]) -> None:
    """Run a command and print its output."""
    print(f"Running: {' '.join(cmd)}")
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        print(f"Error: {result.stderr}")
        sys.exit(1)
    print(result.stdout)


def main() -> None:
    """Uninstall project dependencies and cleanup."""
    # Ensure we're in the project root
    project_root = Path(__file__).parent
    if not (project_root / "pyproject.toml").exists():
        print("Error: Must run uninstall.py from project root directory")
        sys.exit(1)

    # Get project name from pyproject.toml
    try:
        import tomli

        with open("pyproject.toml", "rb") as f:
            pyproject = tomli.load(f)
            project_name = pyproject["project"]["name"]
    except Exception as e:
        print(f"Error reading pyproject.toml: {e}")
        sys.exit(1)

    # Uninstall the project
    print(f"Uninstalling {project_name}...")
    run_command(["uv", "pip", "uninstall", project_name])

    # Clean up any remaining build artifacts
    print("\nCleaning up build artifacts...")
    for path in [".build", "dist", "*.egg-info"]:
        run_command(["rm", "-rf", path])

    print("\nUninstallation complete!")


if __name__ == "__main__":
    main()
