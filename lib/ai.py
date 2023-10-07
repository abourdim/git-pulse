"""AI summaries + Magic diff storyteller — commit analysis."""

import re
import requests as req
from .api import GitHubAPI
from .colors import C
from .ui import pick_repo
from .i18n import t
from .config import load as load_config


def ai_menu(gh: GitHubAPI):
    while True:
        config = load_config()
        has_ai = bool(config.get("openai_api_key"))
        ai_status = f"{C.GREEN}configured{C.RESET}" if has_ai else f"{C.DIM}not set (using pattern-based){C.RESET}"
        print(f"""
  {C.BOLD}{'=' * 50}{C.RESET}
  {C.BOLD}{C.CYAN}AI SUMMARIES & DIFF STORYTELLER{C.RESET}
  {C.BOLD}{'=' * 50}{C.RESET}
  AI: {ai_status}

  {C.GREEN}1{C.RESET}  Weekly digest (recent commits across repos)
  {C.GREEN}2{C.RESET}  Repo summary
  {C.GREEN}3{C.RESET}  Diff story (human-readable diff)
  {C.GREEN}4{C.RESET}  Compare branches
  {C.GREEN}5{C.RESET}  Configure AI provider
  {C.GREEN}0{C.RESET}  {t('back')}
""")
        choice = input(f"  {C.YELLOW}> Option: {C.RESET}").strip()
        if choice == "0": break
        elif choice == "1": _weekly_digest(gh)
        elif choice == "2": _repo_summary(gh)
        elif choice == "3": _diff_story(gh)
        elif choice == "4": _compare_branches(gh)
        elif choice == "5": _configure_ai(config)
        if choice in ("1","2","3","4","5"):
            input(f"\n  {C.DIM}{t('press_enter')}{C.RESET}")


def _weekly_digest(gh):
    print(f"\n  {C.DIM}{t('fetching')}{C.RESET}")
    repos = gh.list_repos()
    from datetime import datetime, timedelta
    week_ago = (datetime.utcnow() - timedelta(days=7)).strftime("%Y-%m-%dT%H:%M:%SZ")

    all_commits = []
    for repo in repos[:15]:
        r = req.get(f"{gh.BASE_URL}/repos/{gh.username}/{repo['name']}/commits",
                    headers=gh.headers, params={"since": week_ago, "per_page": 20})
        if r.status_code == 200:
            for c in r.json():
                c["_repo"] = repo["name"]
                all_commits.append(c)

    if not all_commits:
        print(f"  {C.YELLOW}No commits this week.{C.RESET}"); return

    # Group by repo
    by_repo = {}
    for c in all_commits:
        by_repo.setdefault(c["_repo"], []).append(c)

    print(f"\n  {C.BOLD}WEEKLY DIGEST ({len(all_commits)} commits across {len(by_repo)} repos){C.RESET}\n")
    for repo, commits in by_repo.items():
        print(f"  {C.CYAN}{repo}{C.RESET} ({len(commits)} commits)")
        summary = _summarize_commits(commits)
        print(f"    {summary}\n")


def _repo_summary(gh):
    name = pick_repo(gh)
    if not name: return
    print(f"\n  {C.DIM}{t('fetching')}{C.RESET}")
    repo = gh.get_repo(name)
    if not repo:
        print(f"  {C.RED}x {t('not_found')}{C.RESET}"); return
    commits = gh.list_commits(name, 20)
    langs = gh.get_languages(name)

    summary = _summarize_commits(commits)
    top_lang = max(langs, key=langs.get) if langs else "unknown"

    print(f"""
  {C.BOLD}REPO SUMMARY: {name}{C.RESET}

  Type:     {top_lang} project
  Activity: {len(commits)} recent commits
  Summary:  {summary}
""")


def _diff_story(gh):
    """Magic diff storyteller — human-readable diff."""
    name = pick_repo(gh)
    if not name: return
    commits = gh.list_commits(name, 5)
    if len(commits) < 2:
        print(f"  {C.YELLOW}Need at least 2 commits.{C.RESET}"); return

    base = commits[1]["sha"]
    head = commits[0]["sha"]
    print(f"  {C.DIM}Comparing {base[:7]}..{head[:7]}{C.RESET}")

    r = req.get(f"{gh.BASE_URL}/repos/{gh.username}/{name}/compare/{base}...{head}",
                headers=gh.headers)
    if r.status_code != 200:
        print(f"  {C.RED}x Failed.{C.RESET}"); return

    data = r.json()
    files = data.get("files", [])
    if not files:
        print(f"  {C.YELLOW}No changes.{C.RESET}"); return

    print(f"\n  {C.BOLD}DIFF STORY: {base[:7]} → {head[:7]}{C.RESET}\n")
    print(f"  {C.BOLD}What changed:{C.RESET}")

    for f in files:
        fname = f["filename"]
        status = f.get("status", "modified")
        adds = f.get("additions", 0)
        dels = f.get("deletions", 0)
        patch = f.get("patch", "")

        story = _analyze_patch(fname, status, patch, adds, dels)
        for line in story:
            print(f"    {line}")

    total_adds = sum(f.get("additions", 0) for f in files)
    total_dels = sum(f.get("deletions", 0) for f in files)
    print(f"\n  {C.BOLD}Summary:{C.RESET} {C.GREEN}+{total_adds}{C.RESET} {C.RED}-{total_dels}{C.RESET} across {len(files)} files")


def _analyze_patch(fname, status, patch, adds, dels):
    """Pattern-match a patch into human-readable lines."""
    lines = []
    if status == "added":
        lines.append(f"{C.GREEN}• Created new file: {fname}{C.RESET}")
    elif status == "removed":
        lines.append(f"{C.RED}• Deleted file: {fname}{C.RESET}")
    elif status == "renamed":
        lines.append(f"{C.CYAN}• Renamed: {fname}{C.RESET}")
    else:
        lines.append(f"{C.YELLOW}• Modified: {fname}{C.RESET} ({C.GREEN}+{adds}{C.RESET}/{C.RED}-{dels}{C.RESET})")

    if not patch:
        return lines

    # Pattern matching on diff content
    for line in patch.split("\n"):
        if line.startswith("+") and not line.startswith("+++"):
            clean = line[1:].strip()
            if re.match(r"^(def |function |class |fn |void |int |pub fn )", clean):
                name = clean.split("(")[0].split("{")[0].strip()
                lines.append(f"  {C.GREEN}+ Added: {name}{C.RESET}")
            elif re.match(r"^(import |from |#include |require|use )", clean):
                lines.append(f"  {C.GREEN}+ Added dependency: {clean[:60]}{C.RESET}")
            elif "TODO" in clean or "FIXME" in clean:
                lines.append(f"  {C.YELLOW}+ Added TODO: {clean[:60]}{C.RESET}")
        elif line.startswith("-") and not line.startswith("---"):
            clean = line[1:].strip()
            if re.match(r"^(def |function |class |fn |void |int |pub fn )", clean):
                name = clean.split("(")[0].split("{")[0].strip()
                lines.append(f"  {C.RED}- Removed: {name}{C.RESET}")
            elif "TODO" in clean or "FIXME" in clean:
                lines.append(f"  {C.GREEN}✓ Completed TODO: {clean[:60]}{C.RESET}")

    return lines


def _compare_branches(gh):
    name = pick_repo(gh)
    if not name: return
    base = input(f"  {C.YELLOW}> Base branch [main]: {C.RESET}").strip() or "main"
    head = input(f"  {C.YELLOW}> Head branch: {C.RESET}").strip()
    if not head: return

    r = req.get(f"{gh.BASE_URL}/repos/{gh.username}/{name}/compare/{base}...{head}",
                headers=gh.headers)
    if r.status_code != 200:
        print(f"  {C.RED}x Failed.{C.RESET}"); return
    data = r.json()
    print(f"""
  {C.BOLD}{base} ← {head}{C.RESET}
  Status: {data.get('status', '?')}
  Ahead by: {data.get('ahead_by', 0)} commits
  Behind by: {data.get('behind_by', 0)} commits
  Files changed: {len(data.get('files', []))}
""")
    for c in data.get("commits", [])[:10]:
        sha = c["sha"][:7]
        msg = c["commit"]["message"].split("\n")[0][:55]
        print(f"  {C.YELLOW}{sha}{C.RESET}  {msg}")


def _summarize_commits(commits):
    """Basic pattern-based summary of a list of commits."""
    if not commits:
        return "No activity."
    msgs = [c["commit"]["message"].split("\n")[0] for c in commits]
    types = {"feat": 0, "fix": 0, "chore": 0, "docs": 0, "refactor": 0, "other": 0}
    for msg in msgs:
        categorized = False
        for key in types:
            if msg.lower().startswith(key):
                types[key] += 1
                categorized = True
                break
        if not categorized:
            types["other"] += 1

    parts = []
    if types["feat"]: parts.append(f"{types['feat']} features")
    if types["fix"]: parts.append(f"{types['fix']} fixes")
    if types["chore"]: parts.append(f"{types['chore']} chores")
    if types["docs"]: parts.append(f"{types['docs']} doc updates")
    if types["refactor"]: parts.append(f"{types['refactor']} refactors")
    if types["other"]: parts.append(f"{types['other']} other")
    return ", ".join(parts) if parts else f"{len(commits)} commits"


def _configure_ai(config):
    from .config import save as save_config
    print(f"\n  {C.DIM}Optional: OpenAI API key for enhanced summaries.{C.RESET}")
    print(f"  {C.DIM}Without it, pattern-based summaries are used.{C.RESET}")
    key = input(f"\n  {C.YELLOW}> OpenAI API key (blank to skip): {C.RESET}").strip()
    if key:
        config["openai_api_key"] = key
        config["ai_provider"] = "openai"
        save_config(config)
        print(f"  {C.GREEN}+ Saved.{C.RESET}")
    model = input(f"  {C.YELLOW}> Model [gpt-4o-mini]: {C.RESET}").strip() or "gpt-4o-mini"
    config["ai_model"] = model
    save_config(config)
