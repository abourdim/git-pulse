"""Repo health dashboard — score repos on best practices."""

import requests as req
from .api import GitHubAPI
from .colors import C
from .i18n import t


CHECKS = [
    ("README",      lambda r, h: _has_file(r, h, "README.md")),
    ("LICENSE",     lambda r, h: _has_file(r, h, "LICENSE") or _has_file(r, h, "LICENSE.md")),
    (".gitignore",  lambda r, h: _has_file(r, h, ".gitignore")),
    ("Description", lambda r, h: bool(r.get("description"))),
    ("Active",      lambda r, h: _is_active(r)),
    ("Default br",  lambda r, h: r.get("default_branch") == "main"),
    ("Issues<20",   lambda r, h: r.get("open_issues_count", 0) < 20),
    ("Topics",      lambda r, h: bool(r.get("topics"))),
]


def _has_file(repo: dict, headers: dict, filename: str) -> bool:
    url = f"https://api.github.com/repos/{repo['full_name']}/contents/{filename}"
    try:
        r = req.get(url, headers=headers, timeout=5)
        return r.status_code == 200
    except Exception:
        return False


def _is_active(repo: dict) -> bool:
    from datetime import datetime, timedelta
    pushed = repo.get("pushed_at", "")
    if not pushed:
        return False
    try:
        dt = datetime.strptime(pushed, "%Y-%m-%dT%H:%M:%SZ")
        return (datetime.utcnow() - dt) < timedelta(days=180)
    except ValueError:
        return False


def health_dashboard(gh: GitHubAPI):
    print(f"\n  {C.DIM}{t('fetching')}{C.RESET}")
    repos = gh.list_repos(repo_type="owner")
    if not repos:
        print(f"  {C.YELLOW}{t('no_results')}{C.RESET}")
        return

    headers = gh.headers
    results = []

    print(f"  {C.DIM}Scanning {len(repos)} repos...{C.RESET}\n")

    for i, repo in enumerate(repos):
        name = repo["name"]
        print(f"  {C.DIM}[{i+1}/{len(repos)}] {name}...{C.RESET}", end="\r", flush=True)
        checks = {}
        for label, fn in CHECKS:
            try:
                checks[label] = fn(repo, headers)
            except Exception:
                checks[label] = False
        score = sum(checks.values()) / len(CHECKS) * 100
        results.append((name, checks, score))

    # Clear progress line
    print(" " * 60, end="\r")

    # Sort by score
    results.sort(key=lambda x: x[2])
    avg_score = sum(r[2] for r in results) / len(results) if results else 0

    # Header
    labels = [c[0][:3].upper() for c in CHECKS]
    hdr = "  " + f"{'Repo':<25} " + " ".join(f"{l:>4}" for l in labels) + f" {'Score':>6}"
    print(f"\n  {C.BOLD}REPO HEALTH{C.RESET}  Overall: {avg_score:.0f}%\n")
    print(f"{C.BOLD}{hdr}{C.RESET}")
    print(f"  {'-' * (len(hdr) - 2)}")

    for name, checks, score in results:
        row = f"  {C.CYAN}{name:<25}{C.RESET} "
        for label, _ in CHECKS:
            v = checks.get(label, False)
            mark = f"{C.GREEN}  \u2713 {C.RESET}" if v else f"{C.RED}  \u2717 {C.RESET}"
            row += mark
        sc_color = C.GREEN if score >= 75 else (C.YELLOW if score >= 50 else C.RED)
        row += f" {sc_color}{score:>5.0f}%{C.RESET}"
        print(row)

    # Summary
    needs_attention = [r[0] for r in results if r[2] < 50]
    if needs_attention:
        print(f"\n  {C.RED}Needs attention (<50%):{C.RESET} {', '.join(needs_attention)}")

    print(f"\n  {C.DIM}REA=README LIC=License GIT=.gitignore DES=Description{C.RESET}")
    print(f"  {C.DIM}ACT=Active DEF=Default br ISS=Issues<20 TOP=Topics{C.RESET}")
