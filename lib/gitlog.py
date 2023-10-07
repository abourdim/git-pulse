"""Interactive git log — commit graph in terminal."""

import subprocess
from .api import GitHubAPI
from .colors import C
from .ui import pick_repo
from .i18n import t
from .ui import format_date


def git_log_interactive(gh: GitHubAPI):
    name = pick_repo(gh)
    if not name:
        return

    print(f"\n  {C.BOLD}Commit log for {name}:{C.RESET}")
    print(f"  {C.DIM}(Fetching from GitHub API){C.RESET}\n")

    page = 1
    per_page = 20

    while True:
        commits = _fetch_commits(gh, name, page, per_page)
        if not commits:
            if page == 1:
                print(f"  {C.YELLOW}{t('no_results')}{C.RESET}")
            else:
                print(f"  {C.DIM}No more commits.{C.RESET}")
            break

        for i, c in enumerate(commits):
            sha = c["sha"][:7]
            msg = c["commit"]["message"].split("\n")[0][:55]
            author = c["commit"]["author"]["name"][:15]
            date = format_date(c["commit"]["author"]["date"])
            parents = len(c.get("parents", []))

            # Graph character
            if parents > 1:
                graph = f"{C.YELLOW}⑂{C.RESET}"  # merge
            elif parents == 0:
                graph = f"{C.GREEN}●{C.RESET}"  # root
            else:
                graph = f"{C.CYAN}│{C.RESET}"

            print(f"  {graph} {C.YELLOW}{sha}{C.RESET} {msg:<55} {C.DIM}{author} {date}{C.RESET}")

        print(f"\n  {C.DIM}Page {page} ({len(commits)} commits){C.RESET}")
        nav = input(f"  {C.YELLOW}> [n]ext / [d]etail <hash> / [q]uit: {C.RESET}").strip().lower()

        if nav == "q" or nav == "0":
            break
        elif nav == "n":
            page += 1
        elif nav.startswith("d ") or nav.startswith("d"):
            sha = nav.split(maxsplit=1)[-1].strip() if " " in nav else ""
            if sha:
                _show_commit_detail(gh, name, sha)
            else:
                sha = input(f"  {C.YELLOW}> Commit hash: {C.RESET}").strip()
                if sha:
                    _show_commit_detail(gh, name, sha)


def _fetch_commits(gh, name, page, per_page):
    import requests as req
    url = f"{gh.BASE_URL}/repos/{gh.username}/{name}/commits"
    r = req.get(url, headers=gh.headers, params={"per_page": per_page, "page": page})
    return r.json() if r.status_code == 200 and isinstance(r.json(), list) else []


def _show_commit_detail(gh, name, sha):
    import requests as req
    url = f"{gh.BASE_URL}/repos/{gh.username}/{name}/commits/{sha}"
    r = req.get(url, headers=gh.headers)
    if r.status_code != 200:
        print(f"  {C.RED}x Commit not found.{C.RESET}")
        return

    c = r.json()
    msg = c["commit"]["message"]
    author = c["commit"]["author"]["name"]
    date = format_date(c["commit"]["author"]["date"])
    stats = c.get("stats", {})
    files = c.get("files", [])

    print(f"""
  {C.BOLD}{'=' * 55}{C.RESET}
  {C.YELLOW}{c['sha'][:12]}{C.RESET}  {author}  {date}

  {msg}

  {C.GREEN}+{stats.get('additions', 0)}{C.RESET} {C.RED}-{stats.get('deletions', 0)}{C.RESET} in {stats.get('total', 0)} changes, {len(files)} files
  {C.BOLD}{'=' * 55}{C.RESET}
""")
    for f in files[:15]:
        status_c = {
            "added": C.GREEN, "removed": C.RED, "modified": C.YELLOW,
            "renamed": C.CYAN
        }.get(f.get("status", ""), C.DIM)
        print(f"    {status_c}{f.get('status', '?'):>8}{C.RESET}  {f['filename']}"
              f"  {C.GREEN}+{f.get('additions', 0)}{C.RESET}/{C.RED}-{f.get('deletions', 0)}{C.RESET}")

    if len(files) > 15:
        print(f"    {C.DIM}... and {len(files) - 15} more files{C.RESET}")
    input(f"\n  {C.DIM}{t('press_enter')}{C.RESET}")
