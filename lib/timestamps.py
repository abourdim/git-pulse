"""Commit timestamp editor — view and modify commit dates."""

import subprocess
import re
from datetime import datetime, timedelta
import random
from pathlib import Path
from .colors import C
from .i18n import t
from .api import GitHubAPI


def timestamps_menu(gh: GitHubAPI):
    while True:
        print(f"""
  {C.BOLD}{'=' * 50}{C.RESET}
  {C.BOLD}{C.CYAN}COMMIT TIMESTAMP EDITOR{C.RESET}
  {C.BOLD}{'=' * 50}{C.RESET}

  {C.GREEN}1{C.RESET}  Edit single commit date
  {C.GREEN}2{C.RESET}  Bulk shift (offset ±hours/days)
  {C.GREEN}3{C.RESET}  Spread commits evenly across range
  {C.GREEN}4{C.RESET}  Apply time pattern (working hours etc.)
  {C.GREEN}5{C.RESET}  View commit timestamps
  {C.GREEN}6{C.RESET}  Force push to remote
  {C.GREEN}0{C.RESET}  {t('back')}
""")
        choice = input(f"  {C.YELLOW}> Option: {C.RESET}").strip()
        if choice == "0": break
        repo_path = _get_repo_path()
        if not repo_path: continue
        if choice == "1": _edit_single(repo_path)
        elif choice == "2": _bulk_shift(repo_path)
        elif choice == "3": _spread_evenly(repo_path)
        elif choice == "4": _apply_pattern(repo_path)
        elif choice == "5": _view_timestamps(repo_path)
        elif choice == "6": _force_push(repo_path)
        if choice in ("1","2","3","4","5","6"):
            input(f"\n  {C.DIM}{t('press_enter')}{C.RESET}")


def _get_repo_path():
    path = input(f"\n  {C.YELLOW}> Repo path: {C.RESET}").strip()
    if not path: return None
    p = Path(path).expanduser()
    if not (p / ".git").exists():
        print(f"  {C.RED}x Not a git repo: {p}{C.RESET}"); return None
    return str(p)


def _get_commits(repo_path, n=20):
    r = subprocess.run(["git", "log", f"-{n}", "--format=%H %aI %s"], cwd=repo_path,
                       capture_output=True, text=True)
    if r.returncode != 0: return []
    commits = []
    for line in r.stdout.strip().split("\n"):
        if not line: continue
        parts = line.split(" ", 2)
        if len(parts) >= 3:
            commits.append({"hash": parts[0], "date": parts[1], "msg": parts[2]})
    return commits


def _view_timestamps(repo_path):
    commits = _get_commits(repo_path, 30)
    if not commits:
        print(f"  {C.YELLOW}No commits.{C.RESET}"); return
    print(f"\n  {C.BOLD}{'#':>3}  {'Hash':<9} {'Author Date':<26} Message{C.RESET}")
    print(f"  {'-' * 75}")
    for i, c in enumerate(commits, 1):
        print(f"  {i:>3}  {C.YELLOW}{c['hash'][:7]}{C.RESET}  {c['date'][:25]:<26} {c['msg'][:40]}")


def _edit_single(repo_path):
    _view_timestamps(repo_path)
    commits = _get_commits(repo_path, 20)
    idx = input(f"\n  {C.YELLOW}> Commit # to edit: {C.RESET}").strip()
    if not idx.isdigit() or not (1 <= int(idx) <= len(commits)): return
    c = commits[int(idx) - 1]
    new_date = input(f"  {C.YELLOW}> New date (YYYY-MM-DD HH:MM): {C.RESET}").strip()
    if not new_date: return
    try:
        dt = datetime.strptime(new_date, "%Y-%m-%d %H:%M")
        iso = dt.strftime("%Y-%m-%dT%H:%M:%S")
    except ValueError:
        print(f"  {C.RED}x Invalid date.{C.RESET}"); return

    _backup_branch(repo_path)
    n = int(idx)
    env = f'if [ "$GIT_COMMIT" = "{c["hash"]}" ]; then export GIT_AUTHOR_DATE="{iso}"; export GIT_COMMITTER_DATE="{iso}"; fi'
    r = subprocess.run(["git", "filter-branch", "-f", "--env-filter", env, f"HEAD~{n}..HEAD"],
                       cwd=repo_path, capture_output=True, text=True)
    if r.returncode == 0:
        print(f"  {C.GREEN}+ Commit {c['hash'][:7]} date changed to {new_date}{C.RESET}")
    else:
        print(f"  {C.RED}x Failed: {r.stderr[:200]}{C.RESET}")


def _parse_offset(s):
    """Parse offset like +3h, -1d, +2d6h30m."""
    total_minutes = 0
    sign = -1 if s.startswith("-") else 1
    s = s.lstrip("+-")
    for match in re.finditer(r"(\d+)([dhm])", s):
        val, unit = int(match.group(1)), match.group(2)
        if unit == "d": total_minutes += val * 1440
        elif unit == "h": total_minutes += val * 60
        elif unit == "m": total_minutes += val
    return sign * total_minutes


def _bulk_shift(repo_path):
    n = input(f"\n  {C.YELLOW}> How many commits from HEAD? [10]: {C.RESET}").strip() or "10"
    offset_str = input(f"  {C.YELLOW}> Shift by (e.g. +3h, -1d, +2d6h): {C.RESET}").strip()
    if not offset_str: return
    offset_min = _parse_offset(offset_str)
    if offset_min == 0:
        print(f"  {C.YELLOW}No offset.{C.RESET}"); return

    commits = _get_commits(repo_path, int(n))
    print(f"\n  {C.BOLD}Preview:{C.RESET}")
    for c in commits:
        try:
            old_dt = datetime.fromisoformat(c["date"][:19])
            new_dt = old_dt + timedelta(minutes=offset_min)
            print(f"  {c['hash'][:7]}  {old_dt.strftime('%H:%M')} → {new_dt.strftime('%H:%M')}  {c['msg'][:40]}")
        except Exception:
            pass

    confirm = input(f"\n  {C.YELLOW}> Apply? [y/N]: {C.RESET}").strip().lower()
    if confirm != "y": return

    _backup_branch(repo_path)
    env_script = f"""
import os, datetime
d = os.environ.get('GIT_AUTHOR_DATE','')
if d:
    try:
        dt = datetime.datetime.fromisoformat(d[:19])
        dt += datetime.timedelta(minutes={offset_min})
        os.environ['GIT_AUTHOR_DATE'] = dt.isoformat()
        os.environ['GIT_COMMITTER_DATE'] = dt.isoformat()
    except: pass
"""
    # Use simpler filter-branch
    env = f'export GIT_AUTHOR_DATE="$(date -d "$GIT_AUTHOR_DATE {offset_min} minutes" --iso-8601=seconds 2>/dev/null || echo $GIT_AUTHOR_DATE)"; export GIT_COMMITTER_DATE="$GIT_AUTHOR_DATE"'
    r = subprocess.run(["git", "filter-branch", "-f", "--env-filter", env, f"HEAD~{n}..HEAD"],
                       cwd=repo_path, capture_output=True, text=True)
    if r.returncode == 0:
        print(f"  {C.GREEN}+ Shifted {n} commits by {offset_str}{C.RESET}")
    else:
        print(f"  {C.RED}x Failed. Try git filter-repo for better results.{C.RESET}")


def _spread_evenly(repo_path):
    n = input(f"\n  {C.YELLOW}> How many commits? [5]: {C.RESET}").strip() or "5"
    start = input(f"  {C.YELLOW}> Start date (YYYY-MM-DD HH:MM): {C.RESET}").strip()
    end = input(f"  {C.YELLOW}> End date (YYYY-MM-DD HH:MM): {C.RESET}").strip()
    if not start or not end: return
    try:
        start_dt = datetime.strptime(start, "%Y-%m-%d %H:%M")
        end_dt = datetime.strptime(end, "%Y-%m-%d %H:%M")
    except ValueError:
        print(f"  {C.RED}x Invalid dates.{C.RESET}"); return

    weekdays = input(f"  {C.YELLOW}> Weekdays only? [Y/n]: {C.RESET}").strip().lower() != "n"
    workhours = input(f"  {C.YELLOW}> Working hours (9-18)? [Y/n]: {C.RESET}").strip().lower() != "n"
    jitter = input(f"  {C.YELLOW}> Random jitter? [Y/n]: {C.RESET}").strip().lower() != "n"

    count = int(n)
    commits = _get_commits(repo_path, count)
    commits.reverse()  # oldest first

    dates = _generate_dates(start_dt, end_dt, count, weekdays, workhours, jitter)
    print(f"\n  {C.BOLD}Preview:{C.RESET}")
    for c, d in zip(commits, dates):
        print(f"  {c['hash'][:7]}  → {d.strftime('%Y-%m-%d %H:%M')}  {c['msg'][:40]}")

    confirm = input(f"\n  {C.YELLOW}> Apply? [y/N]: {C.RESET}").strip().lower()
    if confirm != "y": return

    _backup_branch(repo_path)
    # Build filter script
    mapping = {}
    for c, d in zip(commits, dates):
        mapping[c["hash"]] = d.isoformat()
    
    conditions = []
    for h, d in mapping.items():
        conditions.append(f'if [ "$GIT_COMMIT" = "{h}" ]; then export GIT_AUTHOR_DATE="{d}"; export GIT_COMMITTER_DATE="{d}"; fi')
    env = "\n".join(conditions)
    
    r = subprocess.run(["git", "filter-branch", "-f", "--env-filter", env, f"HEAD~{count}..HEAD"],
                       cwd=repo_path, capture_output=True, text=True)
    if r.returncode == 0:
        print(f"  {C.GREEN}+ Spread {count} commits across {start} to {end}{C.RESET}")
    else:
        print(f"  {C.RED}x Failed.{C.RESET}")


def _generate_dates(start, end, count, weekdays, workhours, jitter):
    total_seconds = (end - start).total_seconds()
    dates = []
    for i in range(count):
        frac = i / max(count - 1, 1)
        dt = start + timedelta(seconds=frac * total_seconds)
        if weekdays:
            while dt.weekday() >= 5:
                dt += timedelta(days=1)
        if workhours:
            if dt.hour < 9: dt = dt.replace(hour=9, minute=random.randint(0, 30))
            elif dt.hour >= 18: dt = dt.replace(hour=17, minute=random.randint(0, 59))
        if jitter:
            dt += timedelta(minutes=random.randint(-15, 15))
        dates.append(dt)
    return dates


def _apply_pattern(repo_path):
    print(f"""
  {C.BOLD}PATTERNS{C.RESET}
  {C.GREEN}1{C.RESET}  Working hours (Mon-Fri, 9-18, random)
  {C.GREEN}2{C.RESET}  Night owl (20:00-03:00)
  {C.GREEN}3{C.RESET}  Specific day (all on one date)
""")
    pattern = input(f"  {C.YELLOW}> Pattern [1]: {C.RESET}").strip() or "1"
    n = input(f"  {C.YELLOW}> Last N commits [5]: {C.RESET}").strip() or "5"
    
    if pattern == "1":
        week_start = input(f"  {C.YELLOW}> Week of (YYYY-MM-DD): {C.RESET}").strip()
        if not week_start: return
        try:
            start = datetime.strptime(week_start, "%Y-%m-%d").replace(hour=9)
            end = start + timedelta(days=4, hours=9)
        except ValueError: return
    elif pattern == "2":
        day = input(f"  {C.YELLOW}> Date (YYYY-MM-DD): {C.RESET}").strip()
        if not day: return
        try:
            start = datetime.strptime(day, "%Y-%m-%d").replace(hour=20)
            end = start + timedelta(hours=7)
        except ValueError: return
    elif pattern == "3":
        day = input(f"  {C.YELLOW}> Date (YYYY-MM-DD): {C.RESET}").strip()
        if not day: return
        try:
            start = datetime.strptime(day, "%Y-%m-%d").replace(hour=9)
            end = start.replace(hour=18)
        except ValueError: return
    else:
        return

    count = int(n)
    commits = _get_commits(repo_path, count)
    commits.reverse()
    dates = _generate_dates(start, end, count, pattern == "1", pattern != "2", True)
    
    print(f"\n  {C.BOLD}Preview:{C.RESET}")
    for c, d in zip(commits, dates):
        print(f"  {c['hash'][:7]}  → {d.strftime('%Y-%m-%d %H:%M')}  {c['msg'][:40]}")
    
    confirm = input(f"\n  {C.YELLOW}> Apply? [y/N]: {C.RESET}").strip().lower()
    if confirm != "y": return
    
    _backup_branch(repo_path)
    conditions = []
    for c, d in zip(commits, dates):
        conditions.append(f'if [ "$GIT_COMMIT" = "{c["hash"]}" ]; then export GIT_AUTHOR_DATE="{d.isoformat()}"; export GIT_COMMITTER_DATE="{d.isoformat()}"; fi')
    env = "\n".join(conditions)
    r = subprocess.run(["git", "filter-branch", "-f", "--env-filter", env, f"HEAD~{count}..HEAD"],
                       cwd=repo_path, capture_output=True, text=True)
    print(f"  {C.GREEN}+ Done.{C.RESET}" if r.returncode == 0 else f"  {C.RED}x Failed.{C.RESET}")


def _backup_branch(repo_path):
    subprocess.run(["git", "branch", "-f", "backup/pre-timestamp-edit"], cwd=repo_path,
                   capture_output=True, text=True)
    print(f"  {C.DIM}Backup branch created.{C.RESET}")


def _force_push(repo_path):
    print(f"""
  {C.RED}{C.BOLD}WARNING: Force pushing rewrites remote history!{C.RESET}
  {C.RED}Collaborators will need to re-clone or reset.{C.RESET}
""")
    confirm = input(f"  {C.RED}> Type 'PUSH' to confirm: {C.RESET}").strip()
    if confirm != "PUSH": return
    r = subprocess.run(["git", "push", "--force-with-lease"], cwd=repo_path,
                       capture_output=True, text=True)
    if r.returncode == 0:
        print(f"  {C.GREEN}+ Force pushed.{C.RESET}")
    else:
        print(f"  {C.RED}x {r.stderr[:200]}{C.RESET}")
