#!/usr/bin/env python3
"""
MCP Server Installer Script
Installs the local MCP server to Claude Desktop and Cursor configurations
"""

import json
import os
import platform
import sys
import subprocess
from pathlib import Path
from typing import Any

SERVER_NAME = "mcportfolio"


def check_python_version() -> bool:
    """Check if Python version meets requirements."""
    current_version = sys.version_info
    required_version = (3, 12)

    if current_version < required_version:
        print(f"ERROR: Python {required_version[0]}.{required_version[1]}+ required")
        print(f"   Current version: {current_version.major}.{current_version.minor}.{current_version.micro}")
        print("\nTo fix this:")
        print("   1. Install Python 3.12+ from https://python.org")
        print("   2. Or use pyenv: pyenv install 3.12 && pyenv local 3.12")
        print("   3. Or use conda: conda install python=3.12")
        print("   4. Or use uv: uv python install 3.12")
        return False

    print(
        f"SUCCESS: Python version {current_version.major}.{current_version.minor}."
        f"{current_version.micro} meets requirements"
    )
    return True


def check_uv_available() -> bool:
    """Check if uv is available."""
    try:
        result = subprocess.run(["uv", "--version"], capture_output=True, text=True)
        if result.returncode == 0:
            print(f"SUCCESS: uv found: {result.stdout.strip()}")
            return True
    except FileNotFoundError:
        pass

    print("ERROR: uv package manager not found")
    print("\nTo install uv:")
    print("   1. Visit: https://github.com/astral-sh/uv")
    print("   2. Or run: curl -LsSf https://astral.sh/uv/install.sh | sh")
    print("   3. Or with pip: pip install uv")
    return False


def get_config_paths() -> tuple[Path, Path]:
    """Get the config file paths for Claude Desktop and Cursor"""
    system = platform.system()

    if system == "Darwin":  # macOS
        claude_config = Path.home() / "Library/Application Support/Claude/claude_desktop_config.json"
        cursor_config = Path.home() / ".cursor/mcp.json"
    elif system == "Windows":
        appdata = os.environ.get("APPDATA", "")
        claude_config = Path(appdata) / "Claude/claude_desktop_config.json"
        cursor_config = Path.home() / ".cursor/mcp.json"
    else:  # Linux and others
        claude_config = Path.home() / ".config/Claude/claude_desktop_config.json"
        cursor_config = Path.home() / ".cursor/mcp.json"

    return claude_config, cursor_config


def load_or_create_config(config_path: Path) -> dict[str, Any]:
    """Load existing config or create a new one"""
    if config_path.exists():
        try:
            with open(config_path) as f:
                return json.load(f)
        except (OSError, json.JSONDecodeError):
            print(f"Warning: Could not read {config_path}, creating new config")

    return {"mcpServers": {}}


def save_config(config_path: Path, config_data: dict[str, Any]) -> None:
    """Save config to file, creating directories if needed"""
    config_path.parent.mkdir(parents=True, exist_ok=True)
    with open(config_path, "w") as f:
        json.dump(config_data, f, indent=2)


def get_uv_command() -> str:
    """Get the uv command path"""
    possible_paths = [
        "/opt/homebrew/bin/uv",  # Homebrew on macOS
        "/usr/local/bin/uv",  # Manual install
        "uv",  # In PATH
    ]

    for path in possible_paths:
        if Path(path).exists() or path == "uv":
            return path

    return "uv"  # Fallback


def install_to_config(config_path: Path, script_dir: Path, server_name: str) -> bool:
    """Install MCP server configuration to a config file"""
    config = load_or_create_config(config_path)

    if "mcpServers" not in config:
        config["mcpServers"] = {}

    # Build server configuration with all required dependencies
    server_config = {
        "command": get_uv_command(),
        "args": [
            "run",
            "--directory",
            str(script_dir),
            "mcportfolio/server/main.py",
        ],
    }

    # Add our server configuration
    config["mcpServers"][server_name] = server_config

    save_config(config_path, config)
    return True


def run_command(cmd: list[str], check_exit: bool = True) -> subprocess.CompletedProcess:
    """Run a command and print its output."""
    print(f"Running: {' '.join(cmd)}")
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        print(f"Error: {result.stderr}")
        if check_exit:
            sys.exit(1)
    elif result.stdout.strip():
        print(result.stdout.strip())
    return result


def main() -> None:
    """Install project dependencies and setup MCP server configuration."""
    print("McPortfolio MCP Server Installation")
    print("=" * 40)

    # Check Python version first
    if not check_python_version():
        sys.exit(1)

    # Check if uv is available
    if not check_uv_available():
        sys.exit(1)

    # Ensure we're in the project root
    project_root = Path(__file__).parent
    if not (project_root / "pyproject.toml").exists():
        print("ERROR: Must run install.py from project root directory")
        print(f"   Current directory: {Path.cwd()}")
        print(f"   Expected to find: {project_root / 'pyproject.toml'}")
        sys.exit(1)

    print(f"SUCCESS: Project root confirmed: {project_root}")
    print()

    # Check if virtual environment exists, create if not
    venv_path = project_root / ".venv"
    if not venv_path.exists():
        print("Creating virtual environment...")
        run_command(["uv", "venv", ".venv"])
        print("SUCCESS: Virtual environment created")
    else:
        print("SUCCESS: Virtual environment already exists")

    # Install dependencies
    print("\nInstalling dependencies...")
    try:
        run_command(["uv", "pip", "install", "-e", "."])
        print("SUCCESS: Main dependencies installed")
    except SystemExit:
        print("ERROR: Failed to install main dependencies")
        return

    # Install development dependencies
    print("\nInstalling development dependencies...")
    try:
        run_command(["uv", "pip", "install", "-e", ".[dev]"])
        print("SUCCESS: Development dependencies installed")
    except SystemExit:
        print("WARNING: Failed to install development dependencies (continuing anyway)")

    # Test that the server can be imported
    print("\nTesting server installation...")
    try:
        result = run_command(
            ["uv", "run", "python", "-c", "import mcportfolio.server.main; print('SUCCESS: Server import successful')"],
            check_exit=False,
        )
        if result.returncode != 0:
            print("ERROR: Server import test failed. Dependencies may not be properly installed.")
            print("   You may need to check your Python environment or dependencies.")
            return
    except Exception as e:
        print(f"ERROR: Server import test failed with error: {e}")
        return

    # Get config paths
    claude_config, cursor_config = get_config_paths()

    print("\nMCP Server configuration options:")
    print(f"   1. Claude Desktop config: {claude_config}")
    print(f"   2. Cursor config: {cursor_config}")
    print("   3. Both")
    print("   4. Skip MCP configuration")

    while True:
        choice = input("\nWhich configuration would you like to install? (1-4): ").strip()
        if choice in ["1", "2", "3", "4"]:
            break
        print("   Please enter 1, 2, 3, or 4")

    success_count = 0

    if choice in ["1", "3"]:  # Claude Desktop
        try:
            print(f"\nInstalling to Claude Desktop config: {claude_config}")
            install_to_config(claude_config, project_root, SERVER_NAME)
            print("SUCCESS: Claude Desktop configuration updated successfully")
            success_count += 1
        except Exception as e:
            print(f"ERROR: Failed to update Claude Desktop config: {e}")

    if choice in ["2", "3"]:  # Cursor
        try:
            print(f"\nInstalling to Cursor config: {cursor_config}")
            install_to_config(cursor_config, project_root, SERVER_NAME)
            print("SUCCESS: Cursor configuration updated successfully")
            success_count += 1
        except Exception as e:
            print(f"ERROR: Failed to update Cursor config: {e}")

    if choice == "4":
        print("\nSkipping MCP configuration as requested.")

    print("\n" + "=" * 50)
    print("INSTALLATION SUMMARY")
    print("=" * 50)
    print("SUCCESS: Dependencies installed")
    print("SUCCESS: Server tested and working")

    if choice != "4":
        if success_count > 0:
            print(f"SUCCESS: {success_count} MCP configuration(s) updated")
            print("\nNEXT STEPS:")
            print("   1. Restart Claude Desktop or Cursor")
            print("   2. Look for the MCP server icon in the chat interface")
            print(f"   3. The server should appear as '{SERVER_NAME}' in your available tools")
            print("   4. Try asking: 'What portfolio optimization tools do you have?'")
        else:
            print("ERROR: MCP configuration failed")

    print("\nMANUAL SERVER OPTIONS:")
    print("   • uv run mcportfolio/server/main.py")
    print("   • uvicorn mcportfolio.server.main:asgi_app --host 0.0.0.0 --port 8001")
    print("\nFor more info, see: README.md")
    print("=" * 50)


if __name__ == "__main__":
    main()
