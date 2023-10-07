"""Cross-repo search — code, filenames, commits, issues."""

import requests as req
from .api import GitHubAPI
from .colors import C
from .i18n import t


def search_menu(gh: GitHubAPI):
    while True:
        print(f"""
  {C.BOLD}{'=' * 50}{C.RESET}
  {C.BOLD}{C.CYAN}CROSS-REPO SEARCH{C.RESET}
  {C.BOLD}{'=' * 50}{C.RESET}

  {C.GREEN}1{C.RESET}  Search code (file contents)
  {C.GREEN}2{C.RESET}  Search filenames
  {C.GREEN}3{C.RESET}  Search commits
  {C.GREEN}4{C.RESET}  Search issues & PRs
  {C.GREEN}0{C.RESET}  {t('back')}
""")
        choice = input(f"  {C.YELLOW}> Option: {C.RESET}").strip()
        if choice == "0":
            break
        query = input(f"  {C.YELLOW}> Search: {C.RESET}").strip()
        if not query:
            continue

        if choice == "1":
            _search_code(gh, query)
        elif choice == "2":
            _search_filenames(gh, query)
        elif choice == "3":
            _search_commits(gh, query)
        elif choice == "4":
            _search_issues(gh, query)

        input(f"\n  {C.DIM}{t('press_enter')}{C.RESET}")


def _search_code(gh, query):
    print(f"\n  {C.DIM}{t('searching')}{C.RESET}")
    r = req.get(f"{gh.BASE_URL}/search/code", headers=gh.headers,
                params={"q": f"user:{gh.username} {query}", "per_page": 20})
    if r.status_code != 200:
        print(f"  {C.RED}x Search failed ({r.status_code}).{C.RESET}"); return
    items = r.json().get("items", [])
    total = r.json().get("total_count", 0)
    if not items:
        print(f"  {C.YELLOW}{t('no_results')}{C.RESET}"); return

    print(f"\n  {C.BOLD}Found {total} results:{C.RESET}\n")
    for item in items:
        repo = item["repository"]["name"]
        path = item["path"]
        # Get text matches if available
        matches = item.get("text_matches", [])
        fragment = ""
        if matches:
            fragment = matches[0].get("fragment", "")[:80]
        print(f"  {C.CYAN}{repo}{C.RESET}/{C.YELLOW}{path}{C.RESET}")
        if fragment:
            print(f"    {C.DIM}{fragment}{C.RESET}")


def _search_filenames(gh, query):
    print(f"\n  {C.DIM}{t('searching')}{C.RESET}")
    r = req.get(f"{gh.BASE_URL}/search/code", headers=gh.headers,
                params={"q": f"user:{gh.username} filename:{query}", "per_page": 20})
    if r.status_code != 200:
        print(f"  {C.RED}x Search failed.{C.RESET}"); return
    items = r.json().get("items", [])
    if not items:
        print(f"  {C.YELLOW}{t('no_results')}{C.RESET}"); return

    print(f"\n  {C.BOLD}Found {r.json().get('total_count', 0)} files:{C.RESET}\n")
    for item in items:
        repo = item["repository"]["name"]
        path = item["path"]
        print(f"  {C.CYAN}{repo}{C.RESET}/{path}")


def _search_commits(gh, query):
    print(f"\n  {C.DIM}{t('searching')}{C.RESET}")
    headers = {**gh.headers, "Accept": "application/vnd.github.cloak-preview+json"}
    r = req.get(f"{gh.BASE_URL}/search/commits", headers=headers,
                params={"q": f"author:{gh.username} {query}", "per_page": 20})
    if r.status_code != 200:
        print(f"  {C.RED}x Search failed.{C.RESET}"); return
    items = r.json().get("items", [])
    if not items:
        print(f"  {C.YELLOW}{t('no_results')}{C.RESET}"); return

    print(f"\n  {C.BOLD}Found {r.json().get('total_count', 0)} commits:{C.RESET}\n")
    for item in items:
        sha = item["sha"][:7]
        msg = item["commit"]["message"].split("\n")[0][:60]
        repo = item["repository"]["name"]
        date = item["commit"]["author"]["date"][:10]
        print(f"  {C.YELLOW}{sha}{C.RESET} {C.CYAN}{repo:<20}{C.RESET} {msg:<60} {C.DIM}{date}{C.RESET}")


def _search_issues(gh, query):
    print(f"\n  {C.DIM}{t('searching')}{C.RESET}")
    r = req.get(f"{gh.BASE_URL}/search/issues", headers=gh.headers,
                params={"q": f"user:{gh.username} {query}", "per_page": 20})
    if r.status_code != 200:
        print(f"  {C.RED}x Search failed.{C.RESET}"); return
    items = r.json().get("items", [])
    if not items:
        print(f"  {C.YELLOW}{t('no_results')}{C.RESET}"); return

    print(f"\n  {C.BOLD}Found {r.json().get('total_count', 0)} issues/PRs:{C.RESET}\n")
    for item in items:
        num = item["number"]
        title = item["title"][:55]
        state = item["state"]
        repo_url = item["repository_url"]
        repo = repo_url.split("/")[-1]
        sc = C.GREEN if state == "open" else C.RED
        kind = "PR" if "pull_request" in item else "Issue"
        print(f"  {sc}#{num:<5}{C.RESET} {C.CYAN}{repo:<18}{C.RESET} [{kind}] {title}")
