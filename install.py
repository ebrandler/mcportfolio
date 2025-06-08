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


def get_config_paths() -> tuple[Path, Path]:
    """Get the config file paths for Claude Desktop and Cursor"""
    system = platform.system()

    if system == "Darwin":  # macOS
        claude_config = (
            Path.home()
            / "Library/Application Support/Claude/claude_desktop_config.json"
        )
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


def run_command(cmd: list[str]) -> None:
    """Run a command and print its output."""
    print(f"Running: {' '.join(cmd)}")
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        print(f"Error: {result.stderr}")
        sys.exit(1)
    print(result.stdout)


def main() -> None:
    """Install project dependencies and setup."""
    # Ensure we're in the project root
    project_root = Path(__file__).parent
    if not (project_root / "pyproject.toml").exists():
        print("Error: Must run install.py from project root directory")
        sys.exit(1)

    # Install dependencies
    print("Installing dependencies...")
    run_command(["uv", "pip", "install", "-e", "."])

    # Install development dependencies
    print("\nInstalling development dependencies...")
    run_command(["uv", "pip", "install", "-e", ".[dev]"])

    print("\nInstallation complete! You can now run the server with:")
    print("  uv run mcportfolio/server/main.py")
    print("or")
    print("  uvicorn mcportfolio.server.main:asgi_app --host 0.0.0.0 --port 8001")


if __name__ == "__main__":
    main()
