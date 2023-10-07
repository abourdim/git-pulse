"""GitHub Actions monitor — workflow runs across repos."""

import requests as req
from .api import GitHubAPI
from .colors import C
from .ui import pick_repo
from .i18n import t
from .ui import format_date


def workflows_menu(gh: GitHubAPI):
    while True:
        print(f"""
  {C.BOLD}{'=' * 50}{C.RESET}
  {C.BOLD}{C.CYAN}GITHUB ACTIONS MONITOR{C.RESET}
  {C.BOLD}{'=' * 50}{C.RESET}

  {C.GREEN}1{C.RESET}  View recent runs (all repos)
  {C.GREEN}2{C.RESET}  View runs for specific repo
  {C.GREEN}3{C.RESET}  Re-run failed workflow
  {C.GREEN}0{C.RESET}  {t('back')}
""")
        choice = input(f"  {C.YELLOW}> Option: {C.RESET}").strip()
        if choice == "0":
            break
        elif choice == "1":
            _all_runs(gh)
        elif choice == "2":
            _repo_runs(gh)
        elif choice == "3":
            _rerun_failed(gh)
        if choice in ("1", "2", "3"):
            input(f"\n  {C.DIM}{t('press_enter')}{C.RESET}")


def _all_runs(gh):
    print(f"\n  {C.DIM}{t('fetching')}{C.RESET}")
    repos = gh.list_repos(repo_type="owner")
    all_runs = []
    for repo in repos[:20]:
        name = repo["name"]
        r = req.get(f"{gh.BASE_URL}/repos/{gh.username}/{name}/actions/runs",
                    headers=gh.headers, params={"per_page": 3})
        if r.status_code == 200:
            for run in r.json().get("workflow_runs", []):
                run["_repo"] = name
                all_runs.append(run)

    all_runs.sort(key=lambda x: x.get("created_at", ""), reverse=True)
    if not all_runs:
        print(f"  {C.YELLOW}No workflow runs found.{C.RESET}"); return

    print(f"\n  {C.BOLD}Recent workflow runs:{C.RESET}\n")
    print(f"  {'Repo':<18} {'Workflow':<20} {'Status':>8} {'Time':>8} {'ID':>12}")
    print(f"  {'-' * 72}")
    for run in all_runs[:25]:
        repo = run["_repo"][:17]
        wf = run.get("name", "?")[:19]
        status = run.get("conclusion") or run.get("status", "?")
        sc = {"success": C.GREEN, "failure": C.RED, "in_progress": C.YELLOW,
              "cancelled": C.DIM}.get(status, C.DIM)
        dur = ""
        run_id = run["id"]
        print(f"  {C.CYAN}{repo:<18}{C.RESET} {wf:<20} {sc}{status:>8}{C.RESET} {dur:>8} {run_id:>12}")


def _repo_runs(gh):
    name = pick_repo(gh)
    if not name: return
    print(f"\n  {C.DIM}{t('fetching')}{C.RESET}")
    r = req.get(f"{gh.BASE_URL}/repos/{gh.username}/{name}/actions/runs",
                headers=gh.headers, params={"per_page": 15})
    if r.status_code != 200:
        print(f"  {C.RED}x Failed.{C.RESET}"); return
    runs = r.json().get("workflow_runs", [])
    if not runs:
        print(f"  {C.YELLOW}No runs found.{C.RESET}"); return

    print(f"\n  {C.BOLD}Runs for {name}:{C.RESET}\n")
    for run in runs:
        status = run.get("conclusion") or run.get("status", "?")
        sc = {"success": C.GREEN, "failure": C.RED, "in_progress": C.YELLOW}.get(status, C.DIM)
        date = format_date(run.get("created_at", ""))
        print(f"  {sc}{status:>10}{C.RESET}  {run.get('name', '?'):<25} {date}  ID:{run['id']}")


def _rerun_failed(gh):
    name = pick_repo(gh)
    if not name: return
    run_id = input(f"  {C.YELLOW}> Run ID: {C.RESET}").strip()
    if not run_id: return

    print(f"  {C.DIM}Re-running...{C.RESET}")
    r = req.post(f"{gh.BASE_URL}/repos/{gh.username}/{name}/actions/runs/{run_id}/rerun",
                 headers=gh.headers)
    if r.status_code == 201:
        print(f"  {C.GREEN}+ Re-run triggered!{C.RESET}")
    else:
        print(f"  {C.RED}x Failed ({r.status_code}).{C.RESET}")
