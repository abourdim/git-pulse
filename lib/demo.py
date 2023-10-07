"""Demo mode — mock GitHub API with realistic fake data."""
from __future__ import annotations

from datetime import datetime, timedelta
import random
import hashlib
import os


_REPOS = [
    {"name": "smart-garden-iot", "language": "C++", "private": False, "description": "ESP32-based automated garden monitoring system", "topics": ["esp32", "iot", "arduino"], "stargazers_count": 12, "forks_count": 3, "size": 2400, "open_issues_count": 2, "default_branch": "main"},
    {"name": "portfolio-site", "language": "HTML", "private": False, "description": "Personal portfolio with Islamic geometric patterns", "topics": ["web", "portfolio"], "stargazers_count": 5, "forks_count": 1, "size": 850, "open_issues_count": 0, "default_branch": "main"},
    {"name": "prayer-times-api", "language": "Python", "private": False, "description": "REST API for accurate prayer time calculations", "topics": ["api", "python", "islam"], "stargazers_count": 28, "forks_count": 7, "size": 1200, "open_issues_count": 4, "default_branch": "main"},
    {"name": "home-automation", "language": "Python", "private": True, "description": "Home assistant configs and custom integrations", "topics": ["iot", "home-assistant"], "stargazers_count": 0, "forks_count": 0, "size": 3400, "open_issues_count": 1, "default_branch": "main"},
    {"name": "dotfiles", "language": "Shell", "private": True, "description": "My terminal setup — zsh, nvim, tmux", "topics": ["dotfiles", "linux"], "stargazers_count": 0, "forks_count": 0, "size": 180, "open_issues_count": 0, "default_branch": "master"},
    {"name": "ml-plant-disease", "language": "Jupyter Notebook", "private": False, "description": "CNN model to detect plant diseases from leaf images", "topics": ["machine-learning", "deep-learning", "agriculture"], "stargazers_count": 34, "forks_count": 11, "size": 45000, "open_issues_count": 3, "default_branch": "main"},
    {"name": "quran-search", "language": "JavaScript", "private": False, "description": "Full-text Quran search engine with tajweed highlighting", "topics": ["quran", "search", "react"], "stargazers_count": 19, "forks_count": 4, "size": 5600, "open_issues_count": 1, "default_branch": "main"},
    {"name": "firmware-updater", "language": "C", "private": True, "description": "OTA firmware update service for ESP32 devices", "topics": ["esp32", "ota", "embedded"], "stargazers_count": 0, "forks_count": 0, "size": 780, "open_issues_count": 0, "default_branch": "main"},
    {"name": "budget-tracker", "language": "TypeScript", "private": True, "description": "Personal finance tracker with halal investment filtering", "topics": ["finance", "react", "typescript"], "stargazers_count": 0, "forks_count": 0, "size": 4200, "open_issues_count": 5, "default_branch": "main"},
    {"name": "pcb-library", "language": "None", "private": False, "description": "KiCad footprints and symbols for common IoT components", "topics": ["kicad", "pcb", "hardware"], "stargazers_count": 8, "forks_count": 2, "size": 12000, "open_issues_count": 0, "default_branch": "main"},
    {"name": "recipe-app", "language": "Dart", "private": False, "description": "Halal recipe app with meal planning — Flutter", "topics": ["flutter", "mobile", "food"], "stargazers_count": 6, "forks_count": 1, "size": 3800, "open_issues_count": 2, "default_branch": "main"},
    {"name": "gitpulse", "language": "Python", "private": False, "description": "GitHub repo manager — CLI + Web UI", "topics": ["github", "cli", "python", "tool"], "stargazers_count": 3, "forks_count": 0, "size": 94, "open_issues_count": 0, "default_branch": "main"},
    {"name": "notes-archive", "language": None, "private": True, "description": "", "topics": [], "stargazers_count": 0, "forks_count": 0, "size": 0, "open_issues_count": 0, "default_branch": "main"},
    {"name": "old-website", "language": "HTML", "private": True, "description": "First website attempt from 2019", "topics": [], "stargazers_count": 0, "forks_count": 0, "size": 340, "open_issues_count": 0, "default_branch": "master"},
    {"name": "3d-printer-mods", "language": "OpenSCAD", "private": False, "description": "Custom Ender 3 mods and enclosure design", "topics": ["3d-printing", "openscad"], "stargazers_count": 15, "forks_count": 5, "size": 8900, "open_issues_count": 1, "default_branch": "main"},
    {"name": "ansible-homelab", "language": "Shell", "private": True, "description": "Ansible playbooks for my home server stack", "topics": ["ansible", "devops", "homelab"], "stargazers_count": 0, "forks_count": 0, "size": 560, "open_issues_count": 0, "default_branch": "main"},
    {"name": "weather-station", "language": "C++", "private": False, "description": "Solar-powered ESP32 weather station with LoRa", "topics": ["esp32", "iot", "lora", "weather"], "stargazers_count": 22, "forks_count": 6, "size": 1800, "open_issues_count": 3, "default_branch": "main"},
]

_DEMO_USER = "demo-user"

_MESSAGES = [
    "fix: resolve sensor timeout on high humidity",
    "feat: add dark mode toggle to settings",
    "docs: update installation instructions",
    "refactor: extract API client into separate module",
    "chore: bump dependencies to latest",
    "fix: correct prayer time calculation for high latitudes",
    "feat: implement search autocomplete",
    "style: apply consistent indentation",
    "test: add unit tests for auth module",
    "feat: add export to CSV functionality",
    "fix: handle null response from API gracefully",
    "docs: add Arabic translation for README",
    "perf: optimize database queries for large datasets",
    "feat: voice command support for basic navigation",
    "fix: memory leak in WebSocket handler",
    "chore: update CI pipeline to use Python 3.12",
    "feat: add OTA progress bar on LCD display",
    "fix: timezone offset bug in date formatter",
    "refactor: move config to YAML format",
    "feat: implement multi-language support",
]

_AUTHORS = ["Abdellah", "demo-user", "contributor-1"]
_BRANCH_NAMES = ["main", "develop", "feature/dark-mode", "fix/sensor-bug", "release/v2.0"]


def _make_date(days_ago: int, hour: int = 14) -> str:
    dt = datetime.utcnow() - timedelta(days=days_ago, hours=random.randint(0, 8))
    dt = dt.replace(hour=hour, minute=random.randint(0, 59), second=random.randint(0, 59))
    return dt.strftime("%Y-%m-%dT%H:%M:%SZ")


def _enrich_repo(repo: dict) -> dict:
    """Add computed fields to match real GitHub API shape."""
    base = _make_date(random.randint(30, 800))
    updated = _make_date(random.randint(0, 60))
    pushed = _make_date(random.randint(0, 30))
    return {
        **repo,
        "full_name": f"{_DEMO_USER}/{repo['name']}",
        "html_url": f"https://github.com/{_DEMO_USER}/{repo['name']}",
        "clone_url": f"https://github.com/{_DEMO_USER}/{repo['name']}.git",
        "created_at": base,
        "updated_at": updated,
        "pushed_at": pushed,
        "fork": False,
        "license": {"name": "MIT"} if not repo["private"] and random.random() > 0.3 else None,
        "homepage": repo.get("homepage", ""),
        "has_wiki": repo.get("has_wiki", True),
        "has_issues": repo.get("has_issues", True),
        "archived": repo.get("archived", False),
        "visibility": "private" if repo["private"] else "public",
    }


class DemoAPI:
    """Drop-in replacement for GitHubAPI using fake data."""

    BASE_URL = "https://api.github.com"
    is_demo = True

    def __init__(self):
        self.headers = {}
        self.token = "demo"
        self._repos = [_enrich_repo(r) for r in _REPOS]
        self.user = {
            "login": _DEMO_USER,
            "name": "Demo User",
            "followers": 42,
            "following": 18,
            "public_repos": sum(1 for r in _REPOS if not r["private"]),
        }

    @property
    def username(self) -> str:
        return _DEMO_USER

    def list_repos(self, sort="updated", direction="desc", repo_type="all") -> list:
        repos = list(self._repos)
        if repo_type == "owner":
            repos = [r for r in repos if not r.get("fork")]
        elif repo_type == "public":
            repos = [r for r in repos if not r["private"]]
        elif repo_type == "private":
            repos = [r for r in repos if r["private"]]
        if sort == "updated":
            repos.sort(key=lambda r: r["updated_at"], reverse=(direction == "desc"))
        elif sort == "created":
            repos.sort(key=lambda r: r["created_at"], reverse=(direction == "desc"))
        elif sort == "full_name":
            repos.sort(key=lambda r: r["name"].lower(), reverse=(direction == "desc"))
        return repos

    def get_repo(self, name: str) -> dict | None:
        for r in self._repos:
            if r["name"] == name:
                return r
        return None

    def create_repo(self, name: str, description: str = "", private: bool = True, init: bool = True) -> tuple[dict, int]:
        new = _enrich_repo({
            "name": name, "language": None, "private": private,
            "description": description, "topics": [],
            "stargazers_count": 0, "forks_count": 0, "size": 0,
            "open_issues_count": 0, "default_branch": "main",
        })
        self._repos.insert(0, new)
        return new, 201

    def delete_repo(self, name: str) -> int:
        for i, r in enumerate(self._repos):
            if r["name"] == name:
                self._repos.pop(i)
                return 204
        return 404

    def update_repo(self, name: str, **kwargs) -> tuple[dict, int]:
        for r in self._repos:
            if r["name"] == name:
                r.update(kwargs)
                return r, 200
        return {}, 404

    def list_branches(self, name: str) -> list:
        n = 3 if name in ("dotfiles", "notes-archive") else 5
        return [{"name": b, "protected": b == "main",
                 "commit": {"sha": hashlib.md5(f"{name}{b}".encode()).hexdigest()}}
                for b in _BRANCH_NAMES[:n]]

    def list_commits(self, name: str, count: int = 10) -> list:
        commits = []
        for i in range(min(count, 20)):
            sha = hashlib.md5(f"{name}{i}".encode()).hexdigest()
            author = random.choice(_AUTHORS)
            msg = _MESSAGES[i % len(_MESSAGES)]
            date = _make_date(i * 2 + random.randint(0, 3), random.choice([9, 10, 14, 15, 21, 22, 23]))
            commits.append({
                "sha": sha,
                "commit": {
                    "message": msg,
                    "author": {"name": author, "date": date},
                    "committer": {"name": author, "date": date},
                },
            })
        return commits

    def search_repos(self, query: str) -> list:
        q = query.lower()
        return [r for r in self._repos
                if q in r["name"].lower()
                or q in (r.get("description") or "").lower()
                or q in str(r.get("topics", [])).lower()]

    def get_languages(self, name: str) -> dict:
        lang_sets = {
            "smart-garden-iot": {"C++": 45000, "C": 12000, "Python": 3000},
            "portfolio-site": {"HTML": 8000, "CSS": 5000, "JavaScript": 2000},
            "prayer-times-api": {"Python": 18000, "Shell": 500},
            "quran-search": {"JavaScript": 25000, "HTML": 4000, "CSS": 3000},
            "ml-plant-disease": {"Jupyter Notebook": 80000, "Python": 15000},
            "budget-tracker": {"TypeScript": 32000, "CSS": 4000, "HTML": 1500},
            "recipe-app": {"Dart": 28000, "Swift": 2000},
            "weather-station": {"C++": 38000, "C": 8000, "Python": 1500},
            "gitpulse": {"Python": 20000, "HTML": 5000, "CSS": 3000, "JavaScript": 2000},
        }
        repo = self.get_repo(name)
        if repo and name in lang_sets:
            return lang_sets[name]
        lang = (repo or {}).get("language")
        if lang and lang != "None":
            return {lang: 10000}
        return {}

    def clone_repo(self, name: str, dest: str = ".") -> tuple[bool, str]:
        return True, ""

    def get_tree(self, name: str) -> list:
        """Mock file tree for a repo."""
        trees = {
            "smart-garden-iot": [
                {"path": "src/main.cpp", "type": "blob", "size": 4200},
                {"path": "src/sensors.cpp", "type": "blob", "size": 2800},
                {"path": "src/wifi_manager.cpp", "type": "blob", "size": 1900},
                {"path": "include/config.h", "type": "blob", "size": 450},
                {"path": "platformio.ini", "type": "blob", "size": 320},
                {"path": "README.md", "type": "blob", "size": 2100},
                {"path": "LICENSE", "type": "blob", "size": 1060},
                {"path": ".gitignore", "type": "blob", "size": 180},
                {"path": "docs/wiring.md", "type": "blob", "size": 900},
                {"path": "data/calibration.json", "type": "blob", "size": 250},
            ],
            "prayer-times-api": [
                {"path": "app.py", "type": "blob", "size": 3400},
                {"path": "calculations.py", "type": "blob", "size": 5800},
                {"path": "models.py", "type": "blob", "size": 1200},
                {"path": "requirements.txt", "type": "blob", "size": 85},
                {"path": "Dockerfile", "type": "blob", "size": 340},
                {"path": "tests/test_prayer.py", "type": "blob", "size": 2100},
                {"path": "README.md", "type": "blob", "size": 3200},
                {"path": "LICENSE", "type": "blob", "size": 1060},
                {"path": ".gitignore", "type": "blob", "size": 210},
            ],
        }
        default = [
            {"path": "README.md", "type": "blob", "size": 1500},
            {"path": "LICENSE", "type": "blob", "size": 1060},
            {"path": ".gitignore", "type": "blob", "size": 150},
            {"path": "src/main.py", "type": "blob", "size": 2000},
            {"path": "src/utils.py", "type": "blob", "size": 800},
            {"path": "tests/test_main.py", "type": "blob", "size": 600},
        ]
        return trees.get(name, default)

    def get_health_checks(self, name: str) -> dict:
        """Mock health check results."""
        repo = self.get_repo(name)
        if not repo:
            return {}
        has_desc = bool(repo.get("description"))
        has_topics = bool(repo.get("topics"))
        # Simulate: most repos have README, some lack LICENSE or .gitignore
        seed = hash(name) % 10
        return {
            "description": has_desc,
            "topics": has_topics,
            "README.md": seed != 7,  # notes-archive missing README
            "LICENSE": not repo["private"] and seed < 8,
            ".gitignore": seed < 9,
        }

    def get_events(self) -> list:
        """Mock GitHub events feed."""
        types = ["PushEvent", "PullRequestEvent", "IssuesEvent", "WatchEvent",
                 "ForkEvent", "CreateEvent", "IssueCommentEvent"]
        actors = ["contributor-1", "open-source-fan", "code-reviewer", "demo-user", "iot-enthusiast"]
        events = []
        for i in range(15):
            events.append({
                "type": random.choice(types),
                "repo": {"name": f"{_DEMO_USER}/{random.choice(_REPOS)['name']}"},
                "actor": {"login": random.choice(actors)},
                "created_at": _make_date(0, random.randint(8, 22)),
            })
        return events

    def get_traffic(self, name: str) -> dict:
        """Mock traffic analytics."""
        views_data = []
        clones_data = []
        for i in range(14):
            date = (datetime.utcnow() - timedelta(days=13 - i)).strftime("%Y-%m-%dT00:00:00Z")
            v = random.randint(0, 25)
            c = random.randint(0, 5)
            views_data.append({"timestamp": date, "count": v, "uniques": max(1, v // 3)})
            clones_data.append({"timestamp": date, "count": c, "uniques": max(0, c // 2)})
        total_views = sum(v["count"] for v in views_data)
        total_clones = sum(c["count"] for c in clones_data)
        referrers = [
            {"referrer": "github.com", "count": 45, "uniques": 20},
            {"referrer": "google.com", "count": 12, "uniques": 8},
            {"referrer": "reddit.com", "count": 6, "uniques": 4},
        ]
        return {
            "views": {"count": total_views, "uniques": total_views // 3, "views": views_data},
            "clones": {"count": total_clones, "uniques": total_clones // 2, "clones": clones_data},
            "referrers": referrers,
        }

    def get_file_content(self, repo_name: str, path: str) -> dict:
        """Mock file content for demo repos."""
        mock_files = {
            "README.md": "# {repo}\n\n> Built with ❤️\n\n## Overview\n\nThis project is part of the Workshop DIY collection.\n\n## Installation\n\n```bash\ngit clone https://github.com/demo-user/{repo}.git\ncd {repo}\n```\n\n## Usage\n\nSee the documentation for details.\n\n## License\n\nMIT License\n",
            "LICENSE": "MIT License\n\nCopyright (c) 2024 demo-user\n\nPermission is hereby granted, free of charge, to any person obtaining a copy\nof this software and associated documentation files.\n",
            ".gitignore": "# Python\n__pycache__/\n*.pyc\n.venv/\n\n# IDE\n.idea/\n.vscode/\n*.swp\n\n# OS\n.DS_Store\nThumbs.db\n\n# Env\n.env\n.env.local\n",
            "src/main.py": "#!/usr/bin/env python3\n\"\"\"Main entry point.\"\"\"\n\nimport os\nimport sys\nfrom utils import setup_logging\n\n# TODO: Add proper CLI argument parsing\n# FIXME: Error handling needs improvement\n\ndef main():\n    \"\"\"Run the application.\"\"\"\n    setup_logging()\n    print(\"Starting application...\")\n    # Main logic here\n    return 0\n\nif __name__ == \"__main__\":\n    sys.exit(main())\n",
            "src/utils.py": "\"\"\"Utility functions.\"\"\"\n\nimport logging\n\ndef setup_logging(level=logging.INFO):\n    logging.basicConfig(\n        level=level,\n        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'\n    )\n\ndef format_size(bytes_val):\n    for unit in ['B', 'KB', 'MB', 'GB']:\n        if bytes_val < 1024:\n            return f\"{bytes_val:.1f} {unit}\"\n        bytes_val /= 1024\n    return f\"{bytes_val:.1f} TB\"\n",
            "src/main.cpp": '#include <Arduino.h>\n#include "config.h"\n#include "sensors.h"\n\n// TODO: Add OTA update support\n// FIXME: WiFi reconnection logic is flaky\n\nvoid setup() {\n    Serial.begin(115200);\n    initSensors();\n    connectWiFi();\n    Serial.println("Smart Garden v1.0 ready");\n}\n\nvoid loop() {\n    float moisture = readSoilMoisture();\n    float temp = readTemperature();\n    float humidity = readHumidity();\n\n    if (moisture < MOISTURE_THRESHOLD) {\n        activatePump(PUMP_DURATION);\n    }\n\n    sendTelemetry(moisture, temp, humidity);\n    delay(SENSOR_INTERVAL);\n}\n',
            "include/config.h": '#pragma once\n\n#define WIFI_SSID "MyNetwork"\n#define WIFI_PASS "secret123"\n#define API_KEY "demo-api-key-12345"\n\n#define MOISTURE_THRESHOLD 30.0\n#define PUMP_DURATION 5000\n#define SENSOR_INTERVAL 60000\n',
            "app.py": "from flask import Flask, jsonify, request\nfrom calculations import calculate_prayer_times\nfrom models import Location\n\napp = Flask(__name__)\n\n# TODO: Add caching for prayer times\n# HACK: Hardcoded timezone offset\n\n@app.route('/api/times', methods=['GET'])\ndef get_times():\n    lat = request.args.get('lat', type=float)\n    lng = request.args.get('lng', type=float)\n    loc = Location(lat, lng)\n    times = calculate_prayer_times(loc)\n    return jsonify(times)\n\nif __name__ == '__main__':\n    app.run(debug=True)\n",
            "requirements.txt": "flask>=2.0\nrequests>=2.28\nnumpy>=1.20\n",
            "Dockerfile": "FROM python:3.11-slim\nWORKDIR /app\nCOPY requirements.txt .\nRUN pip install --no-cache-dir -r requirements.txt\nCOPY . .\nEXPOSE 5000\nCMD [\"python\", \"app.py\"]\n",
            "tests/test_main.py": "import pytest\nfrom src.main import main\n\ndef test_main_returns_zero():\n    assert main() == 0\n\ndef test_setup_logging():\n    from src.utils import setup_logging\n    setup_logging()  # Should not raise\n",
            "tests/test_prayer.py": "import pytest\nfrom calculations import calculate_prayer_times\nfrom models import Location\n\ndef test_mecca_prayer_times():\n    loc = Location(21.4225, 39.8262)\n    times = calculate_prayer_times(loc)\n    assert 'fajr' in times\n    assert 'dhuhr' in times\n    assert 'asr' in times\n",
            "platformio.ini": "[env:esp32]\nplatform = espressif32\nboard = esp32dev\nframework = arduino\nmonitor_speed = 115200\nlib_deps =\n    adafruit/DHT sensor library@^1.4\n    bblanchon/ArduinoJson@^6.20\n",
            "data/calibration.json": '{\n  "soil_sensor": {\n    "dry_value": 4095,\n    "wet_value": 1200,\n    "offset": 0\n  },\n  "temperature": {\n    "offset": -0.5\n  }\n}\n',
            "docs/wiring.md": "# Wiring Guide\n\n## Components\n- ESP32 DevKit v1\n- DHT22 sensor\n- Soil moisture sensor\n- 5V relay module\n- Water pump\n\n## Connections\n| Component | ESP32 Pin |\n|-----------|----------|\n| DHT22     | GPIO 4   |\n| Soil      | GPIO 34  |\n| Relay     | GPIO 5   |\n",
            "calculations.py": '"""Islamic prayer time calculations."""\n\nimport math\nfrom datetime import datetime, timedelta\n\ndef calculate_prayer_times(location, date=None):\n    """Calculate prayer times for a location."""\n    if date is None:\n        date = datetime.utcnow()\n    # Simplified calculation\n    return {\n        "fajr": "05:23",\n        "sunrise": "06:45",\n        "dhuhr": "12:15",\n        "asr": "15:30",\n        "maghrib": "18:05",\n        "isha": "19:30",\n    }\n',
            "models.py": '"""Data models."""\n\nclass Location:\n    def __init__(self, lat, lng, tz_offset=0):\n        self.lat = lat\n        self.lng = lng\n        self.tz_offset = tz_offset\n\n    def __repr__(self):\n        return f"Location({self.lat}, {self.lng})"\n',
        }
        # Replace {repo} placeholder
        content = mock_files.get(path, f"# File: {path}\n# Content not available in demo mode\n")
        content = content.replace("{repo}", repo_name)
        import base64
        return {
            "name": os.path.basename(path),
            "path": path,
            "content": base64.b64encode(content.encode()).decode(),
            "encoding": "base64",
            "size": len(content),
            "sha": hashlib.md5(content.encode()).hexdigest(),
        }

    def create_or_update_file(self, repo_name, path, content, message, sha=None):
        """Mock file create/update — always succeeds in demo."""
        return True, {"content": {"path": path, "sha": "demo"}}

    def delete_file(self, repo_name, path, message, sha):
        """Mock file delete — always succeeds in demo."""
        return True, {}
