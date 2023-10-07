"""Git Archaeology — discover dead branches, TODOs, large files, stale PRs."""

import requests as req
from datetime import datetime, timedelta
from .api import GitHubAPI
from .colors import C
from .ui import pick_repo
from .i18n import t


def find_dead_branches(gh: GitHubAPI, name: str, days: int = 180) -> list:
    """Find branches not updated in N days and not merged."""
    if getattr(gh, 'is_demo', False):
        import random; random.seed(hash(name))
        if random.random() < 0.5:
            return [{"name": "feature/old-ui", "last_commit": "2025-03-15T10:00:00Z", "age_days": 340},
                    {"name": "hotfix/legacy", "last_commit": "2025-06-01T08:00:00Z", "age_days": 260}]
        return []
    branches = gh.list_branches(name)
    cutoff = datetime.utcnow() - timedelta(days=days)
    dead = []
    for b in branches:
        sha = b.get("commit", {}).get("sha", "")
        if not sha:
            continue
        r = req.get(f"{gh.BASE_URL}/repos/{gh.username}/{name}/commits/{sha}",
                    headers=gh.headers, timeout=5)
        if r.status_code != 200:
            continue
        date_str = r.json().get("commit", {}).get("committer", {}).get("date", "")
        if not date_str:
            continue
        try:
            dt = datetime.strptime(date_str, "%Y-%m-%dT%H:%M:%SZ")
            if dt < cutoff:
                dead.append({"name": b["name"], "last_commit": date_str, "age_days": (datetime.utcnow() - dt).days})
        except ValueError:
            pass
    return dead


def find_large_files(gh: GitHubAPI, name: str, min_kb: int = 1024) -> list:
    """Find files larger than min_kb in the repo tree."""
    if getattr(gh, 'is_demo', False):
        import random; random.seed(hash(name) + 1)
        if random.random() < 0.4:
            return [{"path": "data/dataset.csv", "size_kb": 4500}, {"path": "models/weights.bin", "size_kb": 12000}]
        return []
    r = req.get(f"{gh.BASE_URL}/repos/{gh.username}/{name}/git/trees/HEAD?recursive=1",
                headers=gh.headers, timeout=10)
    if r.status_code != 200:
        return []
    tree = r.json().get("tree", [])
    large = [{"path": f["path"], "size_kb": f["size"] // 1024}
             for f in tree if f.get("type") == "blob" and f.get("size", 0) > min_kb * 1024]
    return sorted(large, key=lambda x: x["size_kb"], reverse=True)


def find_todos(gh: GitHubAPI, name: str, max_files: int = 40) -> list:
    """Search for TODO/FIXME/HACK/XXX comments in code."""
    if getattr(gh, 'is_demo', False):
        import random; random.seed(hash(name) + 2)
        if random.random() < 0.6:
            return [{"file": "src/main.py", "keyword": "TODO", "name": "main.py"},
                    {"file": "lib/utils.py", "keyword": "FIXME", "name": "utils.py"},
                    {"file": "tests/test_api.py", "keyword": "HACK", "name": "test_api.py"}]
        return []
    results = []
    for keyword in ("TODO", "FIXME", "HACK", "XXX"):
        r = req.get(f"{gh.BASE_URL}/search/code",
                    headers=gh.headers, timeout=10,
                    params={"q": f"{keyword} repo:{gh.username}/{name}", "per_page": 10})
        if r.status_code == 200:
            items = r.json().get("items", [])
            for item in items:
                results.append({"file": item.get("path", "?"), "keyword": keyword,
                                "name": item.get("name", "")})
    return results


def find_stale_prs(gh: GitHubAPI, name: str, days: int = 90) -> list:
    """Find open PRs not updated in N days."""
    if getattr(gh, 'is_demo', False):
        import random; random.seed(hash(name) + 3)
        if random.random() < 0.3:
            return [{"title": "Add dark mode support", "number": 12, "age_days": 145, "author": "contributor1"},
                    {"title": "Fix mobile layout", "number": 8, "age_days": 210, "author": "contributor2"}]
        return []
    r = req.get(f"{gh.BASE_URL}/repos/{gh.username}/{name}/pulls",
                headers=gh.headers, params={"state": "open", "per_page": 30}, timeout=10)
    if r.status_code != 200:
        return []
    cutoff = datetime.utcnow() - timedelta(days=days)
    stale = []
    for pr in r.json():
        updated = pr.get("updated_at", "")
        try:
            dt = datetime.strptime(updated, "%Y-%m-%dT%H:%M:%SZ")
            if dt < cutoff:
                stale.append({"number": pr["number"], "title": pr["title"],
                              "updated": updated, "age_days": (datetime.utcnow() - dt).days})
        except ValueError:
            pass
    return stale


def find_empty_repos(gh: GitHubAPI) -> list:
    """Find repos with zero size or no commits."""
    repos = gh.list_repos(repo_type="owner")
    return [r["name"] for r in repos if r.get("size", 0) == 0]


def archaeology_menu(gh: GitHubAPI):
    """CLI menu for git archaeology."""
    print(f"\n  {C.BOLD}{C.CYAN}=== GIT ARCHAEOLOGY ==={C.RESET}\n")
    print(f"  {C.GREEN}1{C.RESET}  Find dead branches (>6 months)")
    print(f"  {C.GREEN}2{C.RESET}  Find large files (>1MB)")
    print(f"  {C.GREEN}3{C.RESET}  Find TODO/FIXME comments")
    print(f"  {C.GREEN}4{C.RESET}  Find stale pull requests")
    print(f"  {C.GREEN}5{C.RESET}  Find empty repos")
    print(f"  {C.GREEN}0{C.RESET}  {t('back')}")

    choice = input(f"\n  {C.YELLOW}> {t('choose')}: {C.RESET}").strip()

    if choice == "1":
        name = pick_repo(gh)
        if not name: return
        print(f"\n  {C.DIM}Searching dead branches...{C.RESET}")
        dead = find_dead_branches(gh, name)
        if not dead:
            print(f"\n  {C.GREEN}+ No dead branches!{C.RESET}")
        else:
            print(f"\n  {C.BOLD}Found {len(dead)} dead branches:{C.RESET}\n")
            for b in dead:
                print(f"    {C.RED}x{C.RESET} {C.CYAN}{b['name']}{C.RESET} — {b['age_days']} days old")

    elif choice == "2":
        name = pick_repo(gh)
        if not name: return
        print(f"\n  {C.DIM}Scanning file sizes...{C.RESET}")
        large = find_large_files(gh, name)
        if not large:
            print(f"\n  {C.GREEN}+ No large files (>1MB)!{C.RESET}")
        else:
            print(f"\n  {C.BOLD}Found {len(large)} large files:{C.RESET}\n")
            for f in large[:20]:
                print(f"    {C.YELLOW}!{C.RESET} {f['path']} — {f['size_kb']} KB")

    elif choice == "3":
        name = pick_repo(gh)
        if not name: return
        print(f"\n  {C.DIM}Searching code...{C.RESET}")
        todos = find_todos(gh, name)
        if not todos:
            print(f"\n  {C.GREEN}+ No TODO/FIXME found!{C.RESET}")
        else:
            print(f"\n  {C.BOLD}Found {len(todos)} items:{C.RESET}\n")
            for t_ in todos:
                print(f"    {C.YELLOW}{t_['keyword']}{C.RESET} in {C.CYAN}{t_['file']}{C.RESET}")

    elif choice == "4":
        name = pick_repo(gh)
        if not name: return
        print(f"\n  {C.DIM}Checking PRs...{C.RESET}")
        stale = find_stale_prs(gh, name)
        if not stale:
            print(f"\n  {C.GREEN}+ No stale PRs!{C.RESET}")
        else:
            print(f"\n  {C.BOLD}Found {len(stale)} stale PRs:{C.RESET}\n")
            for pr in stale:
                print(f"    {C.RED}#{pr['number']}{C.RESET} {pr['title']} — {pr['age_days']} days")

    elif choice == "5":
        print(f"\n  {C.DIM}{t('fetching')}{C.RESET}")
        empties = find_empty_repos(gh)
        if not empties:
            print(f"\n  {C.GREEN}+ No empty repos!{C.RESET}")
        else:
            print(f"\n  {C.BOLD}Found {len(empties)} empty repos:{C.RESET}\n")
            for name in empties:
                print(f"    {C.DIM}-{C.RESET} {C.CYAN}{name}{C.RESET}")
