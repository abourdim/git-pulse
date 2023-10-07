"""Dependency scanner — check outdated packages, vulnerabilities."""

import json
import requests as req
from .api import GitHubAPI
from .colors import C
from .ui import pick_repo
from .i18n import t


DEP_FILES = {
    "requirements.txt": "Python",
    "setup.py": "Python",
    "pyproject.toml": "Python",
    "package.json": "Node.js",
    "platformio.ini": "C/C++ IoT",
    "Cargo.toml": "Rust",
}


def deps_menu(gh: GitHubAPI):
    name = pick_repo(gh)
    if not name: return
    print(f"\n  {C.DIM}Scanning {name} for dependency files...{C.RESET}\n")

    found = []
    for filename, ecosystem in DEP_FILES.items():
        r = req.get(f"{gh.BASE_URL}/repos/{gh.username}/{name}/contents/{filename}",
                    headers=gh.headers)
        if r.status_code == 200:
            found.append((filename, ecosystem, r.json()))

    if not found:
        print(f"  {C.YELLOW}No dependency files found.{C.RESET}"); return

    print(f"  {C.BOLD}DEPENDENCY SCAN: {gh.username}/{name}{C.RESET}\n")

    for filename, ecosystem, data in found:
        print(f"  {C.BOLD}{filename}{C.RESET} ({ecosystem})")

        # Decode content
        import base64
        try:
            content = base64.b64decode(data.get("content", "")).decode()
        except Exception:
            print(f"    {C.DIM}Could not decode.{C.RESET}"); continue

        if filename == "requirements.txt":
            _scan_requirements(content)
        elif filename == "package.json":
            _scan_package_json(content)
        elif filename == "platformio.ini":
            _scan_platformio(content)
        else:
            print(f"    {C.DIM}Listing only (no version check for this format){C.RESET}")
            for line in content.split("\n")[:10]:
                if line.strip():
                    print(f"    {line.strip()}")
        print()

    # Check advisories
    _check_advisories(gh, name)


def _scan_requirements(content):
    for line in content.split("\n"):
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        # Parse name==version or name>=version
        parts = line.split("==")
        if len(parts) == 2:
            name, version = parts[0].strip(), parts[1].strip()
            latest = _pypi_latest(name)
            if latest and latest != version:
                print(f"    {name:<25} {version} → {C.YELLOW}{latest}{C.RESET}  ⚠ update")
            else:
                print(f"    {name:<25} {version:<15} {C.GREEN}✓{C.RESET}")
        else:
            print(f"    {line}")


def _pypi_latest(package):
    try:
        r = req.get(f"https://pypi.org/pypi/{package}/json", timeout=3)
        if r.status_code == 200:
            return r.json()["info"]["version"]
    except Exception:
        pass
    return None


def _scan_package_json(content):
    try:
        pkg = json.loads(content)
    except json.JSONDecodeError:
        print(f"    {C.RED}Invalid JSON{C.RESET}"); return

    for section in ("dependencies", "devDependencies"):
        deps = pkg.get(section, {})
        if deps:
            print(f"    {C.DIM}{section}:{C.RESET}")
            for name, version in deps.items():
                print(f"      {name:<30} {version}")


def _scan_platformio(content):
    for line in content.split("\n"):
        line = line.strip()
        if line.startswith("lib_deps") or line.startswith("platform") or line.startswith("board"):
            print(f"    {line}")


def _check_advisories(gh, name):
    r = req.get(f"{gh.BASE_URL}/repos/{gh.username}/{name}/vulnerability-alerts",
                headers={**gh.headers, "Accept": "application/vnd.github.dorian-preview+json"})
    if r.status_code == 204:
        print(f"  {C.GREEN}✓ Vulnerability alerts enabled, no alerts.{C.RESET}")
    elif r.status_code == 404:
        print(f"  {C.DIM}Vulnerability alerts not enabled.{C.RESET}")
