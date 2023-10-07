"""Config file management for GitPulse."""

import json
import os
from pathlib import Path


CONFIG_DIR = Path(os.environ.get("GHM_CONFIG", str(Path.home() / ".gitpulse")))
CONFIG_FILE = CONFIG_DIR / "config.json"

DEFAULT_CONFIG = {
    "token": "",
    "mode": "",
    "language": "en",
    "web_theme": "masjid",
    "default_sort": "updated",
    "default_direction": "desc",
    "default_repo_type": "all",
    "clone_directory": str(Path.home() / "repos"),
    "commits_count": 10,
    "web_port": 5000,
    "web_host": "127.0.0.1",
    "web_auto_open": True,
}

VERSION = "8.0"
CODENAME = "Buraq"


def load() -> dict:
    if CONFIG_FILE.exists():
        try:
            with open(CONFIG_FILE, "r") as f:
                saved = json.load(f)
            return {**DEFAULT_CONFIG, **saved}
        except (json.JSONDecodeError, IOError):
            pass
    return DEFAULT_CONFIG.copy()


def save(config: dict):
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    with open(CONFIG_FILE, "w") as f:
        json.dump(config, f, indent=2)
    try:
        CONFIG_FILE.chmod(0o600)
    except OSError:
        pass


def get(key: str, default=None):
    return load().get(key, default)


def set_field(key: str, value):
    config = load()
    config[key] = value
    save(config)


def reset():
    save(DEFAULT_CONFIG.copy())


def get_token() -> str:
    config = load()
    return config.get("token") or os.environ.get("GITHUB_TOKEN", "")
