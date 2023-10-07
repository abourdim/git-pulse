"""Git Operations — full local git management with genius features."""

import os
import re
import subprocess
import json
import hashlib
from datetime import datetime, timedelta
from collections import Counter, defaultdict
from pathlib import Path
from .colors import C
from .i18n import t
from .config import load as load_config, save as save_config


# ─── HELPERS ───────────────────────────────────────────────────────────

def _run(cmd, cwd=None, capture=True):
    """Run a git command, return (success, output)."""
    try:
        r = subprocess.run(cmd, cwd=cwd, capture_output=capture,
                           text=True, timeout=30)
        return r.returncode == 0, (r.stdout + r.stderr).strip()
    except subprocess.TimeoutExpired:
        return False, "Command timed out"
    except Exception as e:
        return False, str(e)


def _git(args, cwd=None):
    """Shorthand: _run(['git'] + args, cwd)."""
    return _run(["git"] + args, cwd=cwd)


def _find_repos(extra_dirs=None):
    """Scan common locations for git repos. Returns list of paths."""
    home = Path.home()
    dirs = [home, home / "Documents", home / "Projects", home / "Desktop",
            home / "repos", home / "dev", home / "src", home / "code",
            home / "workspace", home / "github"]
    if extra_dirs:
        dirs.extend(Path(d) for d in extra_dirs)

    repos = []
    seen = set()
    for d in dirs:
        if not d.exists():
            continue
        for item in sorted(d.iterdir()):
            if item.is_dir() and (item / ".git").exists():
                rp = str(item.resolve())
                if rp not in seen:
                    seen.add(rp)
                    repos.append(rp)
    return repos


def _pick_local_repo():
    """Let user pick a local repo from discovered list or type path."""
    config = load_config()
    extra = config.get("local_repo_dirs", [])
    last = config.get("last_local_repo", "")

    repos = _find_repos(extra)

    if not repos and not last:
        print(f"\n  {C.YELLOW}No local repos found.{C.RESET}")
        path = input(f"  {C.YELLOW}> Paste a repo path: {C.RESET}").strip()
        if not path:
            return None
        if not os.path.isdir(os.path.join(path, ".git")):
            print(f"  {C.RED}Not a git repo.{C.RESET}")
            return None
        return path

    print(f"\n  {C.BOLD}Local repos:{C.RESET}\n")
    for i, rp in enumerate(repos, 1):
        name = os.path.basename(rp)
        marker = f" {C.CYAN}(last used){C.RESET}" if rp == last else ""
        print(f"  {C.GREEN}{i:>3}{C.RESET}  {name:<30} {C.DIM}{rp}{C.RESET}{marker}")
    print(f"\n  {C.DIM}  Or type a path{C.RESET}")

    choice = input(f"\n  {C.YELLOW}> Pick: {C.RESET}").strip()
    if not choice:
        return None

    if choice.isdigit():
        idx = int(choice) - 1
        if 0 <= idx < len(repos):
            path = repos[idx]
        else:
            print(f"  {C.RED}Invalid number.{C.RESET}")
            return None
    else:
        path = os.path.expanduser(choice)

    if not os.path.isdir(os.path.join(path, ".git")):
        print(f"  {C.RED}Not a git repo: {path}{C.RESET}")
        return None

    # Remember
    config["last_local_repo"] = path
    save_config(config)
    return path


def _current_branch(cwd):
    ok, out = _git(["rev-parse", "--abbrev-ref", "HEAD"], cwd)
    return out.strip() if ok else "unknown"


def _repo_name(cwd):
    return os.path.basename(os.path.abspath(cwd))


# ─── 1. STATUS ─────────────────────────────────────────────────────────

def git_status(cwd):
    """Color-coded file status."""
    print(f"\n  {C.BOLD}=== STATUS: {_repo_name(cwd)} ({_current_branch(cwd)}) ==={C.RESET}\n")
    ok, out = _git(["status", "--porcelain=v1"], cwd)
    if not ok:
        print(f"  {C.RED}{out}{C.RESET}"); return

    if not out.strip():
        print(f"  {C.GREEN}✓ Working tree clean{C.RESET}"); return

    staged, changed, untracked = [], [], []
    for line in out.splitlines():
        x, y = line[0], line[1]
        fname = line[3:]
        if x in "MADRC" and y == " ":
            staged.append((x, fname))
        elif y in "MADRC":
            changed.append((y, fname))
        elif x == "?" and y == "?":
            untracked.append(fname)
        else:
            if x != " " and x != "?":
                staged.append((x, fname))
            if y != " " and y != "?":
                changed.append((y, fname))

    if staged:
        print(f"  {C.GREEN}{C.BOLD}Staged ({len(staged)}):{C.RESET}")
        for code, f in staged:
            labels = {"M": "modified", "A": "new file", "D": "deleted", "R": "renamed", "C": "copied"}
            print(f"    {C.GREEN}+{C.RESET} {f}  {C.DIM}{labels.get(code, code)}{C.RESET}")
    if changed:
        print(f"\n  {C.RED}{C.BOLD}Changed ({len(changed)}):{C.RESET}")
        for code, f in changed:
            print(f"    {C.RED}~{C.RESET} {f}")
    if untracked:
        print(f"\n  {C.DIM}{C.BOLD}Untracked ({len(untracked)}):{C.RESET}")
        for f in untracked:
            print(f"    {C.DIM}? {f}{C.RESET}")

    total = len(staged) + len(changed) + len(untracked)
    print(f"\n  {total} file(s) · {len(staged)} staged · {len(changed)} changed · {len(untracked)} new")


# ─── 2. PULL ───────────────────────────────────────────────────────────

def git_pull(cwd):
    """Pull with conflict pre-check."""
    branch = _current_branch(cwd)
    print(f"\n  {C.DIM}Checking for conflicts before pulling...{C.RESET}")

    # Check for uncommitted changes
    ok, out = _git(["status", "--porcelain"], cwd)
    if out.strip():
        print(f"  {C.YELLOW}! You have uncommitted changes.{C.RESET}")
        print(f"  {C.YELLOW}  Stash them first? Or commit them?{C.RESET}")
        c = input(f"  {C.YELLOW}> (s)tash / (c)ontinue anyway / (q)uit: {C.RESET}").strip().lower()
        if c == "s":
            _git(["stash", "push", "-m", "auto-stash before pull"], cwd)
            print(f"  {C.GREEN}Stashed ✓{C.RESET}")
        elif c == "q":
            return

    print(f"  {C.DIM}Pulling {branch}...{C.RESET}")
    ok, out = _git(["pull", "--rebase=false"], cwd)
    if ok:
        if "Already up to date" in out:
            print(f"  {C.GREEN}✓ Already up to date.{C.RESET}")
        else:
            print(f"  {C.GREEN}✓ Pulled successfully.{C.RESET}")
            for line in out.splitlines()[:5]:
                print(f"    {line}")
    else:
        if "CONFLICT" in out:
            print(f"  {C.RED}! Merge conflicts detected:{C.RESET}")
            for line in out.splitlines():
                if "CONFLICT" in line:
                    print(f"    {C.RED}{line}{C.RESET}")
            print(f"\n  Use {C.CYAN}Conflict Resolver{C.RESET} to fix them.")
        else:
            print(f"  {C.RED}{out}{C.RESET}")


# ─── 3. STAGE ALL ──────────────────────────────────────────────────────

def git_stage_all(cwd):
    """Stage all changes."""
    ok, out = _git(["add", "."], cwd)
    if ok:
        print(f"\n  {C.GREEN}✓ All files staged.{C.RESET}")
    else:
        print(f"\n  {C.RED}{out}{C.RESET}")


# ─── 4. STAGE PICK ─────────────────────────────────────────────────────

def git_stage_pick(cwd):
    """Stage selected files from numbered list."""
    ok, out = _git(["status", "--porcelain"], cwd)
    if not out.strip():
        print(f"\n  {C.GREEN}Nothing to stage.{C.RESET}"); return

    files = []
    for line in out.splitlines():
        x, y = line[0], line[1]
        fname = line[3:]
        if y in "MD?" or (x == "?" and y == "?"):
            files.append(fname)

    if not files:
        print(f"\n  {C.GREEN}All files already staged.{C.RESET}"); return

    print(f"\n  {C.BOLD}Unstaged files:{C.RESET}\n")
    for i, f in enumerate(files, 1):
        print(f"  {C.GREEN}{i:>3}{C.RESET}  {f}")

    print(f"\n  {C.DIM}Pick: 1,3,5 or 1-4 or 'all'{C.RESET}")
    choice = input(f"  {C.YELLOW}> Stage: {C.RESET}").strip()
    if not choice:
        return

    if choice.lower() == "all":
        indices = list(range(len(files)))
    else:
        indices = _parse_selection(choice, len(files))

    count = 0
    for idx in indices:
        if 0 <= idx < len(files):
            _git(["add", files[idx]], cwd)
            count += 1
    print(f"\n  {C.GREEN}✓ Staged {count} file(s).{C.RESET}")


def _parse_selection(s, max_n):
    """Parse '1,3,5' or '1-4' or '1,3-5' into list of 0-based indices."""
    indices = set()
    for part in s.split(","):
        part = part.strip()
        if "-" in part:
            try:
                a, b = part.split("-", 1)
                for i in range(int(a), int(b) + 1):
                    indices.add(i - 1)
            except ValueError:
                pass
        elif part.isdigit():
            indices.add(int(part) - 1)
    return sorted(i for i in indices if 0 <= i < max_n)


# ─── 5. COMMIT ─────────────────────────────────────────────────────────

def git_commit(cwd):
    """Commit with message prompt."""
    # Check if anything staged
    ok, out = _git(["diff", "--cached", "--stat"], cwd)
    if not out.strip():
        print(f"\n  {C.YELLOW}Nothing staged. Stage files first.{C.RESET}")
        return

    print(f"\n  {C.BOLD}Staged changes:{C.RESET}")
    for line in out.strip().splitlines():
        print(f"    {line}")

    msg = input(f"\n  {C.YELLOW}> Commit message: {C.RESET}").strip()
    if not msg:
        print(f"  {C.YELLOW}{t('cancelled')}{C.RESET}"); return

    ok, out = _git(["commit", "-m", msg], cwd)
    if ok:
        print(f"\n  {C.GREEN}✓ Committed: {msg}{C.RESET}")
    else:
        print(f"\n  {C.RED}{out}{C.RESET}")


# ─── 6. PUSH ──────────────────────────────────────────────────────────

def git_push(cwd):
    """Push to remote."""
    branch = _current_branch(cwd)
    print(f"\n  {C.DIM}Pushing {branch} to origin...{C.RESET}")
    ok, out = _git(["push", "origin", branch], cwd)
    if ok:
        print(f"  {C.GREEN}✓ Pushed to origin/{branch}{C.RESET}")
    else:
        if "no upstream" in out.lower() or "set-upstream" in out.lower():
            print(f"  {C.YELLOW}No upstream set. Setting...{C.RESET}")
            ok2, out2 = _git(["push", "--set-upstream", "origin", branch], cwd)
            if ok2:
                print(f"  {C.GREEN}✓ Pushed & upstream set.{C.RESET}")
            else:
                print(f"  {C.RED}{out2}{C.RESET}")
        else:
            print(f"  {C.RED}{out}{C.RESET}")


# ─── 7. QUICK SYNC ────────────────────────────────────────────────────

def git_quick_sync(cwd):
    """One-shot: stage all + commit + push."""
    print(f"\n  {C.BOLD}{C.CYAN}⚡ QUICK SYNC{C.RESET}\n")

    # Check for changes
    ok, out = _git(["status", "--porcelain"], cwd)
    if not out.strip():
        print(f"  {C.GREEN}Nothing to sync — working tree clean.{C.RESET}")
        return

    # Show what will be synced
    lines = out.strip().splitlines()
    print(f"  {len(lines)} file(s) to sync:\n")
    for line in lines[:15]:
        print(f"    {line}")
    if len(lines) > 15:
        print(f"    {C.DIM}...and {len(lines)-15} more{C.RESET}")

    msg = input(f"\n  {C.YELLOW}> Commit message: {C.RESET}").strip()
    if not msg:
        print(f"  {C.YELLOW}{t('cancelled')}{C.RESET}"); return

    # Stage
    ok, _ = _git(["add", "."], cwd)
    if not ok:
        print(f"  {C.RED}Failed to stage.{C.RESET}"); return

    # Commit
    ok, _ = _git(["commit", "-m", msg], cwd)
    if not ok:
        print(f"  {C.RED}Failed to commit.{C.RESET}"); return

    # Push
    branch = _current_branch(cwd)
    ok, out = _git(["push", "origin", branch], cwd)
    if not ok and "set-upstream" in (out or ""):
        ok, out = _git(["push", "--set-upstream", "origin", branch], cwd)

    if ok:
        print(f"\n  {C.GREEN}✓ Synced! {len(lines)} files → origin/{branch}{C.RESET}")
    else:
        print(f"  {C.GREEN}✓ Committed locally.{C.RESET}")
        print(f"  {C.YELLOW}Push failed: {out}{C.RESET}")


# ─── 8. DIFF ──────────────────────────────────────────────────────────

def git_diff(cwd):
    """Colored diff output."""
    ok, out = _git(["diff", "--stat"], cwd)
    if not out.strip():
        # Try staged
        ok, out = _git(["diff", "--cached", "--stat"], cwd)
        if not out.strip():
            print(f"\n  {C.GREEN}No changes.{C.RESET}"); return
        print(f"\n  {C.BOLD}Staged diff:{C.RESET}")
        ok, full = _git(["diff", "--cached"], cwd)
    else:
        print(f"\n  {C.BOLD}Unstaged diff:{C.RESET}")
        ok, full = _git(["diff"], cwd)

    # Color the diff
    for line in full.splitlines()[:100]:
        if line.startswith("+") and not line.startswith("+++"):
            print(f"  {C.GREEN}{line}{C.RESET}")
        elif line.startswith("-") and not line.startswith("---"):
            print(f"  {C.RED}{line}{C.RESET}")
        elif line.startswith("@@"):
            print(f"  {C.CYAN}{line}{C.RESET}")
        elif line.startswith("diff"):
            print(f"\n  {C.BOLD}{line}{C.RESET}")
        else:
            print(f"  {line}")

    total_lines = len(full.splitlines())
    if total_lines > 100:
        print(f"\n  {C.DIM}...showing 100/{total_lines} lines{C.RESET}")


# ─── 9. UNDO FILE ─────────────────────────────────────────────────────

def git_undo_file(cwd):
    """Restore a file to last committed state."""
    ok, out = _git(["status", "--porcelain"], cwd)
    files = []
    for line in out.splitlines():
        if line[1] in "MD":
            files.append(line[3:])

    if not files:
        print(f"\n  {C.GREEN}No changed files to undo.{C.RESET}"); return

    print(f"\n  {C.BOLD}Changed files:{C.RESET}\n")
    for i, f in enumerate(files, 1):
        print(f"  {C.GREEN}{i:>3}{C.RESET}  {f}")

    choice = input(f"\n  {C.YELLOW}> Undo which file: {C.RESET}").strip()
    if not choice.isdigit():
        return
    idx = int(choice) - 1
    if idx < 0 or idx >= len(files):
        return

    fname = files[idx]
    confirm = input(f"  {C.RED}Discard changes to {fname}? (y/n): {C.RESET}").strip().lower()
    if confirm != "y":
        return

    ok, out = _git(["checkout", "--", fname], cwd)
    if ok:
        print(f"  {C.GREEN}✓ Restored {fname}{C.RESET}")
    else:
        print(f"  {C.RED}{out}{C.RESET}")


# ─── 10. UNDO LAST COMMIT ─────────────────────────────────────────────

def git_undo_commit(cwd):
    """Soft reset last commit (keeps changes staged)."""
    ok, out = _git(["log", "--oneline", "-1"], cwd)
    if not ok:
        print(f"\n  {C.RED}No commits to undo.{C.RESET}"); return

    print(f"\n  Last commit: {C.CYAN}{out}{C.RESET}")
    confirm = input(f"  {C.YELLOW}Undo this commit? Changes stay staged. (y/n): {C.RESET}").strip().lower()
    if confirm != "y":
        return

    ok, out = _git(["reset", "--soft", "HEAD~1"], cwd)
    if ok:
        print(f"  {C.GREEN}✓ Commit undone. Changes are still staged.{C.RESET}")
    else:
        print(f"  {C.RED}{out}{C.RESET}")


# ─── 11. STASH ─────────────────────────────────────────────────────────

def git_stash(cwd):
    """Stash manager: save/pop/list."""
    print(f"\n  {C.BOLD}Stash Manager{C.RESET}\n")
    print(f"  {C.GREEN}1{C.RESET}  Save (pause work)")
    print(f"  {C.GREEN}2{C.RESET}  Pop (resume latest)")
    print(f"  {C.GREEN}3{C.RESET}  List all stashes")
    print(f"  {C.GREEN}4{C.RESET}  Drop a stash")
    print(f"  {C.GREEN}0{C.RESET}  Back")

    c = input(f"\n  {C.YELLOW}> {C.RESET}").strip()
    if c == "1":
        msg = input(f"  {C.YELLOW}> Label (optional): {C.RESET}").strip() or "quick stash"
        ok, out = _git(["stash", "push", "-m", msg], cwd)
        print(f"  {C.GREEN}✓ Stashed: {msg}{C.RESET}" if ok else f"  {C.RED}{out}{C.RESET}")
    elif c == "2":
        ok, out = _git(["stash", "pop"], cwd)
        print(f"  {C.GREEN}✓ Restored from stash.{C.RESET}" if ok else f"  {C.RED}{out}{C.RESET}")
    elif c == "3":
        ok, out = _git(["stash", "list"], cwd)
        if out.strip():
            for line in out.splitlines():
                print(f"    {line}")
        else:
            print(f"  {C.DIM}No stashes.{C.RESET}")
    elif c == "4":
        ok, out = _git(["stash", "list"], cwd)
        if not out.strip():
            print(f"  {C.DIM}No stashes to drop.{C.RESET}"); return
        for i, line in enumerate(out.splitlines()):
            print(f"  {C.GREEN}{i}{C.RESET}  {line}")
        idx = input(f"  {C.YELLOW}> Drop #: {C.RESET}").strip()
        if idx.isdigit():
            _git(["stash", "drop", f"stash@{{{idx}}}"], cwd)
            print(f"  {C.GREEN}✓ Dropped.{C.RESET}")


# ─── 12. CONFLICT RESOLVER ────────────────────────────────────────────

def git_conflict_resolver(cwd):
    """Find and resolve merge conflicts."""
    ok, out = _git(["diff", "--name-only", "--diff-filter=U"], cwd)
    if not out.strip():
        print(f"\n  {C.GREEN}No conflicts found.{C.RESET}"); return

    files = out.strip().splitlines()
    print(f"\n  {C.RED}{C.BOLD}Conflicted files ({len(files)}):{C.RESET}\n")
    for i, f in enumerate(files, 1):
        print(f"  {C.RED}{i:>3}{C.RESET}  {f}")

    choice = input(f"\n  {C.YELLOW}> Pick file to resolve: {C.RESET}").strip()
    if not choice.isdigit():
        return
    idx = int(choice) - 1
    if idx < 0 or idx >= len(files):
        return

    fname = files[idx]
    print(f"\n  {C.BOLD}{fname}:{C.RESET}")
    print(f"  {C.GREEN}1{C.RESET}  Accept MINE (keep your version)")
    print(f"  {C.GREEN}2{C.RESET}  Accept THEIRS (keep remote version)")
    print(f"  {C.GREEN}3{C.RESET}  Show conflict diff")

    r = input(f"\n  {C.YELLOW}> {C.RESET}").strip()
    if r == "1":
        _git(["checkout", "--ours", fname], cwd)
        _git(["add", fname], cwd)
        print(f"  {C.GREEN}✓ Kept your version of {fname}{C.RESET}")
    elif r == "2":
        _git(["checkout", "--theirs", fname], cwd)
        _git(["add", fname], cwd)
        print(f"  {C.GREEN}✓ Kept remote version of {fname}{C.RESET}")
    elif r == "3":
        try:
            with open(os.path.join(cwd, fname)) as fh:
                for line in fh:
                    if line.startswith("<<<<<<<"):
                        print(f"  {C.RED}{line.rstrip()}{C.RESET}")
                    elif line.startswith("======="):
                        print(f"  {C.YELLOW}{line.rstrip()}{C.RESET}")
                    elif line.startswith(">>>>>>>"):
                        print(f"  {C.GREEN}{line.rstrip()}{C.RESET}")
                    else:
                        print(f"  {line.rstrip()}")
        except Exception as e:
            print(f"  {C.RED}{e}{C.RESET}")


# ─── 13. SECRET REWIND ────────────────────────────────────────────────

def git_secret_rewind(cwd):
    """Remove a file from all git history."""
    print(f"\n  {C.RED}{C.BOLD}SECRET REWIND{C.RESET}")
    print(f"  {C.DIM}Removes a file from ALL commits (rewrites history).{C.RESET}\n")

    fname = input(f"  {C.YELLOW}> File to purge (e.g. .env, secrets.json): {C.RESET}").strip()
    if not fname:
        return

    print(f"\n  {C.RED}! This rewrites ALL history. Cannot be undone.{C.RESET}")
    print(f"  {C.RED}! You must force-push after this.{C.RESET}")
    confirm = input(f"  {C.RED}Type '{fname}' to confirm: {C.RESET}").strip()
    if confirm != fname:
        print(f"  {t('cancelled')}"); return

    print(f"  {C.DIM}Purging {fname} from history...{C.RESET}")
    ok, out = _run(["git", "filter-branch", "--force", "--index-filter",
                     f"git rm --cached --ignore-unmatch {fname}",
                     "--prune-empty", "--tag-name-filter", "cat", "--", "--all"], cwd)
    if ok:
        print(f"  {C.GREEN}✓ Purged {fname} from history.{C.RESET}")
        print(f"  {C.YELLOW}Now run: git push --force --all{C.RESET}")
    else:
        print(f"  {C.RED}{out[:300]}{C.RESET}")


# ─── 14. SNAPSHOT ──────────────────────────────────────────────────────

def git_snapshot(cwd):
    """Save/restore named snapshots (lightweight tags + stash)."""
    print(f"\n  {C.BOLD}Snapshot Manager{C.RESET}\n")
    print(f"  {C.GREEN}1{C.RESET}  Save snapshot (bookmark current state)")
    print(f"  {C.GREEN}2{C.RESET}  List snapshots")
    print(f"  {C.GREEN}3{C.RESET}  Restore snapshot")
    print(f"  {C.GREEN}0{C.RESET}  Back")

    c = input(f"\n  {C.YELLOW}> {C.RESET}").strip()
    if c == "1":
        name = input(f"  {C.YELLOW}> Snapshot name: {C.RESET}").strip()
        if not name:
            return
        tag = f"snapshot/{name}"
        # Commit any pending changes first
        ok, status = _git(["status", "--porcelain"], cwd)
        if status.strip():
            _git(["add", "."], cwd)
            _git(["commit", "-m", f"snapshot: {name}"], cwd)
        ok, _ = _git(["tag", tag], cwd)
        if ok:
            print(f"  {C.GREEN}✓ Snapshot '{name}' saved.{C.RESET}")
        else:
            print(f"  {C.RED}Failed. Tag may already exist.{C.RESET}")
    elif c == "2":
        ok, out = _git(["tag", "-l", "snapshot/*"], cwd)
        if out.strip():
            for line in out.splitlines():
                name = line.replace("snapshot/", "")
                ok2, date = _git(["log", "-1", "--format=%ci", line], cwd)
                print(f"    {C.CYAN}{name}{C.RESET}  {C.DIM}{date[:19]}{C.RESET}")
        else:
            print(f"  {C.DIM}No snapshots yet.{C.RESET}")
    elif c == "3":
        ok, out = _git(["tag", "-l", "snapshot/*"], cwd)
        if not out.strip():
            print(f"  {C.DIM}No snapshots.{C.RESET}"); return
        tags = out.strip().splitlines()
        for i, tag in enumerate(tags, 1):
            print(f"  {C.GREEN}{i:>3}{C.RESET}  {tag.replace('snapshot/', '')}")
        idx = input(f"\n  {C.YELLOW}> Restore #: {C.RESET}").strip()
        if idx.isdigit() and 0 < int(idx) <= len(tags):
            tag = tags[int(idx) - 1]
            _git(["checkout", tag], cwd)
            print(f"  {C.GREEN}✓ Restored to {tag}{C.RESET}")
            print(f"  {C.YELLOW}You're in detached HEAD. Use branch manager to go back.{C.RESET}")


# ─── 15. BRANCH MANAGER ───────────────────────────────────────────────

def git_branches(cwd):
    """Create, switch, delete, merge branches."""
    print(f"\n  {C.BOLD}Branch Manager{C.RESET}")
    current = _current_branch(cwd)
    print(f"  Current: {C.CYAN}{current}{C.RESET}\n")
    print(f"  {C.GREEN}1{C.RESET}  List branches")
    print(f"  {C.GREEN}2{C.RESET}  Switch branch")
    print(f"  {C.GREEN}3{C.RESET}  Create branch")
    print(f"  {C.GREEN}4{C.RESET}  Delete branch")
    print(f"  {C.GREEN}5{C.RESET}  Merge into current")
    print(f"  {C.GREEN}0{C.RESET}  Back")

    c = input(f"\n  {C.YELLOW}> {C.RESET}").strip()
    if c == "1":
        ok, out = _git(["branch", "-a", "-v"], cwd)
        for line in out.splitlines():
            if line.startswith("*"):
                print(f"  {C.GREEN}{line}{C.RESET}")
            elif "remotes/" in line:
                print(f"  {C.DIM}{line}{C.RESET}")
            else:
                print(f"  {line}")
    elif c == "2":
        ok, out = _git(["branch", "--list"], cwd)
        branches = [b.strip().lstrip("* ") for b in out.splitlines()]
        for i, b in enumerate(branches, 1):
            marker = f" {C.GREEN}← current{C.RESET}" if b == current else ""
            print(f"  {C.GREEN}{i:>3}{C.RESET}  {b}{marker}")
        idx = input(f"\n  {C.YELLOW}> Switch to: {C.RESET}").strip()
        if idx.isdigit() and 0 < int(idx) <= len(branches):
            ok, out = _git(["checkout", branches[int(idx)-1]], cwd)
            print(f"  {C.GREEN}✓ Switched to {branches[int(idx)-1]}{C.RESET}" if ok else f"  {C.RED}{out}{C.RESET}")
    elif c == "3":
        name = input(f"  {C.YELLOW}> New branch name: {C.RESET}").strip()
        if name:
            ok, out = _git(["checkout", "-b", name], cwd)
            print(f"  {C.GREEN}✓ Created and switched to {name}{C.RESET}" if ok else f"  {C.RED}{out}{C.RESET}")
    elif c == "4":
        ok, out = _git(["branch", "--list"], cwd)
        branches = [b.strip().lstrip("* ") for b in out.splitlines() if b.strip().lstrip("* ") != current]
        if not branches:
            print(f"  {C.YELLOW}No other branches to delete.{C.RESET}"); return
        for i, b in enumerate(branches, 1):
            print(f"  {C.GREEN}{i:>3}{C.RESET}  {b}")
        idx = input(f"\n  {C.YELLOW}> Delete #: {C.RESET}").strip()
        if idx.isdigit() and 0 < int(idx) <= len(branches):
            ok, out = _git(["branch", "-d", branches[int(idx)-1]], cwd)
            print(f"  {C.GREEN}✓ Deleted.{C.RESET}" if ok else f"  {C.RED}{out}{C.RESET}")
    elif c == "5":
        ok, out = _git(["branch", "--list"], cwd)
        branches = [b.strip().lstrip("* ") for b in out.splitlines() if b.strip().lstrip("* ") != current]
        if not branches:
            print(f"  {C.YELLOW}No branches to merge.{C.RESET}"); return
        for i, b in enumerate(branches, 1):
            print(f"  {C.GREEN}{i:>3}{C.RESET}  {b}")
        idx = input(f"\n  {C.YELLOW}> Merge which into {current}: {C.RESET}").strip()
        if idx.isdigit() and 0 < int(idx) <= len(branches):
            ok, out = _git(["merge", branches[int(idx)-1]], cwd)
            print(f"  {C.GREEN}✓ Merged.{C.RESET}" if ok else f"  {C.RED}{out}{C.RESET}")


# ─── 16. LOG GRAPH ────────────────────────────────────────────────────

def git_log_graph(cwd):
    """Pretty commit log with graph."""
    ok, out = _git(["log", "--oneline", "--graph", "--decorate", "--all", "-30"], cwd)
    print(f"\n  {C.BOLD}Commit Graph (last 30):{C.RESET}\n")
    for line in out.splitlines():
        # Color branches
        line = line.replace("*", f"{C.GREEN}*{C.RESET}")
        print(f"  {line}")


# ─── 17. MERGE PREVIEWER ──────────────────────────────────────────────

def git_merge_preview(cwd):
    """Preview what a merge would do without actually merging."""
    current = _current_branch(cwd)
    ok, out = _git(["branch", "--list"], cwd)
    branches = [b.strip().lstrip("* ") for b in out.splitlines() if b.strip().lstrip("* ") != current]
    if not branches:
        print(f"\n  {C.YELLOW}No other branches.{C.RESET}"); return

    print(f"\n  {C.BOLD}Preview merge into {current}:{C.RESET}\n")
    for i, b in enumerate(branches, 1):
        print(f"  {C.GREEN}{i:>3}{C.RESET}  {b}")

    idx = input(f"\n  {C.YELLOW}> Preview which: {C.RESET}").strip()
    if not idx.isdigit() or not (0 < int(idx) <= len(branches)):
        return

    branch = branches[int(idx) - 1]

    # Files that would change
    ok, out = _git(["diff", "--stat", f"{current}...{branch}"], cwd)
    print(f"\n  {C.BOLD}Files affected:{C.RESET}")
    for line in out.splitlines():
        print(f"    {line}")

    # Check for conflicts (dry run)
    ok, base = _git(["merge-base", current, branch], cwd)
    ok, out = _git(["merge-tree", base.strip(), current, branch], cwd)
    if "<<<" in out or "changed in both" in out.lower():
        print(f"\n  {C.RED}! Potential conflicts detected.{C.RESET}")
    else:
        print(f"\n  {C.GREEN}✓ Clean merge expected (no conflicts).{C.RESET}")


# ─── 18. CHERRY-PICK ──────────────────────────────────────────────────

def git_cherry_pick(cwd):
    """Cherry-pick a commit from another branch."""
    current = _current_branch(cwd)
    ok, out = _git(["branch", "--list"], cwd)
    branches = [b.strip().lstrip("* ") for b in out.splitlines() if b.strip().lstrip("* ") != current]

    if not branches:
        print(f"\n  {C.YELLOW}No other branches.{C.RESET}"); return

    print(f"\n  {C.BOLD}Cherry-pick from which branch?{C.RESET}\n")
    for i, b in enumerate(branches, 1):
        print(f"  {C.GREEN}{i:>3}{C.RESET}  {b}")

    idx = input(f"\n  {C.YELLOW}> Branch: {C.RESET}").strip()
    if not idx.isdigit() or not (0 < int(idx) <= len(branches)):
        return
    branch = branches[int(idx) - 1]

    ok, out = _git(["log", "--oneline", branch, "-15"], cwd)
    commits = out.strip().splitlines()
    print(f"\n  {C.BOLD}Commits on {branch}:{C.RESET}\n")
    for i, line in enumerate(commits, 1):
        print(f"  {C.GREEN}{i:>3}{C.RESET}  {line}")

    cidx = input(f"\n  {C.YELLOW}> Pick commit: {C.RESET}").strip()
    if not cidx.isdigit() or not (0 < int(cidx) <= len(commits)):
        return
    sha = commits[int(cidx) - 1].split()[0]
    ok, out = _git(["cherry-pick", sha], cwd)
    print(f"  {C.GREEN}✓ Cherry-picked {sha}{C.RESET}" if ok else f"  {C.RED}{out}{C.RESET}")


# ─── 19. BLAME ────────────────────────────────────────────────────────

def git_blame(cwd):
    """Blame a file — who changed each line."""
    fname = input(f"\n  {C.YELLOW}> File to blame: {C.RESET}").strip()
    if not fname:
        return
    ok, out = _git(["blame", "--date=short", fname], cwd)
    if not ok:
        print(f"  {C.RED}File not found or not tracked.{C.RESET}"); return

    print(f"\n  {C.BOLD}Blame: {fname}{C.RESET}\n")
    for line in out.splitlines()[:50]:
        # Highlight the author
        parts = line.split(")", 1)
        if len(parts) == 2:
            print(f"  {C.DIM}{parts[0]}){C.RESET}{parts[1]}")
        else:
            print(f"  {line}")
    if len(out.splitlines()) > 50:
        print(f"\n  {C.DIM}...showing first 50 lines{C.RESET}")


# ─── 20. BISECT WIZARD ────────────────────────────────────────────────

def git_bisect(cwd):
    """Interactive binary search for bugs."""
    print(f"\n  {C.BOLD}{C.CYAN}BISECT WIZARD{C.RESET}")
    print(f"  {C.DIM}Find the commit that introduced a bug.{C.RESET}\n")

    ok, out = _git(["log", "--oneline", "-20"], cwd)
    commits = out.strip().splitlines()
    print(f"  {C.BOLD}Recent commits:{C.RESET}\n")
    for i, line in enumerate(commits, 1):
        print(f"  {C.GREEN}{i:>3}{C.RESET}  {line}")

    bad = input(f"\n  {C.YELLOW}> Bad commit (first broken, default=1/latest): {C.RESET}").strip() or "1"
    good = input(f"  {C.YELLOW}> Good commit (last working): {C.RESET}").strip()
    if not good.isdigit():
        return

    bad_sha = commits[int(bad) - 1].split()[0]
    good_sha = commits[int(good) - 1].split()[0]

    _git(["bisect", "start"], cwd)
    _git(["bisect", "bad", bad_sha], cwd)
    _git(["bisect", "good", good_sha], cwd)

    print(f"\n  {C.BOLD}Bisecting... answer (g)ood / (b)ad / (s)kip for each commit:{C.RESET}")

    while True:
        ok, out = _git(["log", "--oneline", "-1"], cwd)
        if not out.strip() or "is the first bad" in out:
            break
        print(f"\n  Current: {C.CYAN}{out}{C.RESET}")
        ans = input(f"  {C.YELLOW}> (g)ood / (b)ad / (s)kip / (q)uit: {C.RESET}").strip().lower()
        if ans == "g":
            ok, out = _git(["bisect", "good"], cwd)
        elif ans == "b":
            ok, out = _git(["bisect", "bad"], cwd)
        elif ans == "s":
            ok, out = _git(["bisect", "skip"], cwd)
        elif ans == "q":
            break
        else:
            continue

        if "is the first bad" in out:
            print(f"\n  {C.GREEN}{C.BOLD}Found it!{C.RESET}")
            for line in out.splitlines():
                print(f"  {line}")
            break

    _git(["bisect", "reset"], cwd)
    print(f"  {C.DIM}Bisect finished, back to original state.{C.RESET}")


# ─── 21. TAG MANAGER ──────────────────────────────────────────────────

def git_tags(cwd):
    """Create, list, push, delete tags."""
    print(f"\n  {C.BOLD}Tag Manager{C.RESET}\n")
    print(f"  {C.GREEN}1{C.RESET}  List tags")
    print(f"  {C.GREEN}2{C.RESET}  Create tag")
    print(f"  {C.GREEN}3{C.RESET}  Push tags to remote")
    print(f"  {C.GREEN}4{C.RESET}  Delete tag")
    print(f"  {C.GREEN}0{C.RESET}  Back")

    c = input(f"\n  {C.YELLOW}> {C.RESET}").strip()
    if c == "1":
        ok, out = _git(["tag", "-l", "--sort=-creatordate"], cwd)
        if out.strip():
            for tag in out.splitlines()[:20]:
                ok2, date = _git(["log", "-1", "--format=%ci", tag], cwd)
                print(f"    {C.CYAN}{tag}{C.RESET}  {C.DIM}{date[:10]}{C.RESET}")
        else:
            print(f"  {C.DIM}No tags.{C.RESET}")
    elif c == "2":
        name = input(f"  {C.YELLOW}> Tag name (e.g. v1.0): {C.RESET}").strip()
        msg = input(f"  {C.YELLOW}> Message (optional): {C.RESET}").strip()
        if not name:
            return
        if msg:
            ok, out = _git(["tag", "-a", name, "-m", msg], cwd)
        else:
            ok, out = _git(["tag", name], cwd)
        print(f"  {C.GREEN}✓ Tagged {name}{C.RESET}" if ok else f"  {C.RED}{out}{C.RESET}")
    elif c == "3":
        ok, out = _git(["push", "--tags"], cwd)
        print(f"  {C.GREEN}✓ Tags pushed.{C.RESET}" if ok else f"  {C.RED}{out}{C.RESET}")
    elif c == "4":
        ok, out = _git(["tag", "-l"], cwd)
        tags = out.strip().splitlines()
        if not tags:
            print(f"  {C.DIM}No tags.{C.RESET}"); return
        for i, tag in enumerate(tags, 1):
            print(f"  {C.GREEN}{i:>3}{C.RESET}  {tag}")
        idx = input(f"\n  {C.YELLOW}> Delete #: {C.RESET}").strip()
        if idx.isdigit() and 0 < int(idx) <= len(tags):
            _git(["tag", "-d", tags[int(idx)-1]], cwd)
            print(f"  {C.GREEN}✓ Deleted locally. Push --delete to remove from remote.{C.RESET}")


# ─── 22. AUTO SQUASH ──────────────────────────────────────────────────

def git_auto_squash(cwd):
    """Find and squash 'wip/fix/oops/temp' commits."""
    ok, out = _git(["log", "--oneline", "-30"], cwd)
    commits = out.strip().splitlines()

    wip_patterns = re.compile(r"^[a-f0-9]+\s+(wip|fix typo|oops|temp|fixup|minor|test commit|xxx|todo|lint|format|cleanup)\b", re.I)
    wip_commits = [(i, line) for i, line in enumerate(commits) if wip_patterns.match(line)]

    if not wip_commits:
        print(f"\n  {C.GREEN}No WIP/junk commits found in last 30.{C.RESET}"); return

    print(f"\n  {C.BOLD}Found {len(wip_commits)} squashable commits:{C.RESET}\n")
    for i, line in wip_commits:
        print(f"  {C.YELLOW}  #{i+1}{C.RESET}  {line}")

    print(f"\n  {C.DIM}To squash, use interactive rebase.{C.RESET}")
    print(f"  {C.DIM}This will open: last {len(commits)} commits for reorder/squash.{C.RESET}")
    confirm = input(f"\n  {C.YELLOW}> Start interactive rebase? (y/n): {C.RESET}").strip().lower()
    if confirm == "y":
        n = min(len(commits), 30)
        os.environ["GIT_SEQUENCE_EDITOR"] = "cat"  # Show without editor
        ok, out = _git(["rebase", "-i", f"HEAD~{n}", "--autosquash"], cwd)
        print(f"  {C.DIM}{out[:500]}{C.RESET}")


# ─── 23. TIME TRAVEL ──────────────────────────────────────────────────

def git_time_travel(cwd):
    """Browse any past commit safely."""
    ok, out = _git(["log", "--oneline", "-20"], cwd)
    commits = out.strip().splitlines()
    print(f"\n  {C.BOLD}Time Travel — pick a commit to visit:{C.RESET}\n")
    for i, line in enumerate(commits, 1):
        print(f"  {C.GREEN}{i:>3}{C.RESET}  {line}")

    idx = input(f"\n  {C.YELLOW}> Visit #: {C.RESET}").strip()
    if not idx.isdigit() or not (0 < int(idx) <= len(commits)):
        return

    sha = commits[int(idx) - 1].split()[0]
    _git(["checkout", sha], cwd)
    print(f"\n  {C.CYAN}You are now at {sha}.{C.RESET}")

    # Show file tree
    ok, out = _git(["ls-tree", "--name-only", "-r", "HEAD"], cwd)
    files = out.strip().splitlines()[:30]
    print(f"\n  {C.BOLD}Files at this point ({len(files)}):{C.RESET}")
    for f in files:
        print(f"    {f}")
    if len(out.strip().splitlines()) > 30:
        print(f"    {C.DIM}...{C.RESET}")

    input(f"\n  {C.YELLOW}Press Enter to return to present...{C.RESET}")
    _git(["checkout", "-"], cwd)
    print(f"  {C.GREEN}✓ Back to present.{C.RESET}")


# ─── 24. LOCAL REPO HEALTH ────────────────────────────────────────────

def git_repo_health(cwd):
    """Check local repo health: .gitignore, large files, secrets."""
    name = _repo_name(cwd)
    print(f"\n  {C.BOLD}=== REPO HEALTH: {name} ==={C.RESET}\n")
    score = 0
    total = 0

    # .gitignore
    total += 1
    if os.path.isfile(os.path.join(cwd, ".gitignore")):
        print(f"  {C.GREEN}✓{C.RESET} .gitignore present")
        score += 1
    else:
        print(f"  {C.RED}✗{C.RESET} Missing .gitignore")

    # README
    total += 1
    has_readme = any(os.path.isfile(os.path.join(cwd, f)) for f in ["README.md", "README.txt", "README"])
    if has_readme:
        print(f"  {C.GREEN}✓{C.RESET} README present")
        score += 1
    else:
        print(f"  {C.RED}✗{C.RESET} Missing README")

    # LICENSE
    total += 1
    has_license = any(os.path.isfile(os.path.join(cwd, f)) for f in ["LICENSE", "LICENSE.md", "LICENSE.txt"])
    if has_license:
        print(f"  {C.GREEN}✓{C.RESET} LICENSE present")
        score += 1
    else:
        print(f"  {C.YELLOW}~{C.RESET} No LICENSE file")

    # Large files in tracking
    total += 1
    ok, out = _git(["ls-files"], cwd)
    large = []
    for f in out.splitlines():
        fp = os.path.join(cwd, f)
        try:
            size = os.path.getsize(fp)
            if size > 5_000_000:  # 5MB
                large.append((f, size))
        except OSError:
            pass
    if large:
        print(f"  {C.RED}✗{C.RESET} Large tracked files:")
        for f, s in large[:5]:
            print(f"      {f} ({s // 1_000_000}MB)")
    else:
        print(f"  {C.GREEN}✓{C.RESET} No oversized tracked files")
        score += 1

    # Uncommitted changes
    total += 1
    ok, status = _git(["status", "--porcelain"], cwd)
    if status.strip():
        print(f"  {C.YELLOW}~{C.RESET} {len(status.splitlines())} uncommitted changes")
    else:
        print(f"  {C.GREEN}✓{C.RESET} Clean working tree")
        score += 1

    # Remote configured
    total += 1
    ok, remote = _git(["remote", "-v"], cwd)
    if remote.strip():
        print(f"  {C.GREEN}✓{C.RESET} Remote configured")
        score += 1
    else:
        print(f"  {C.RED}✗{C.RESET} No remote configured")

    pct = int(score / total * 100)
    color = C.GREEN if pct >= 80 else C.YELLOW if pct >= 50 else C.RED
    print(f"\n  Score: {color}{pct}%{C.RESET} ({score}/{total})")


# ─── 25. COMMIT STREAK ────────────────────────────────────────────────

def git_commit_streak(cwd):
    """GitHub-style contribution graph in terminal."""
    ok, out = _git(["log", "--format=%ai", "--all", "--since=90 days ago"], cwd)
    if not out.strip():
        print(f"\n  {C.YELLOW}No commits in last 90 days.{C.RESET}"); return

    days = Counter()
    for line in out.splitlines():
        date = line[:10]
        days[date] += 1

    # Build 90-day grid
    today = datetime.now().date()
    print(f"\n  {C.BOLD}Commit Streak (90 days):{C.RESET}\n")

    current_streak = 0
    max_streak = 0
    streak = 0
    total_commits = sum(days.values())
    active_days = len(days)

    for i in range(89, -1, -1):
        d = (today - timedelta(days=i)).isoformat()
        if d in days:
            streak += 1
            max_streak = max(max_streak, streak)
        else:
            streak = 0

    # Current streak (from today backwards)
    for i in range(90):
        d = (today - timedelta(days=i)).isoformat()
        if d in days:
            current_streak += 1
        else:
            break

    # Visual graph (last 12 weeks)
    weeks = []
    for w in range(12):
        week = []
        for d in range(7):
            date = (today - timedelta(days=(11 - w) * 7 + (6 - d))).isoformat()
            week.append(days.get(date, 0))
        weeks.append(week)

    blocks = " ░▒▓█"
    for row in range(7):
        day_name = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"][row]
        line = f"  {C.DIM}{day_name}{C.RESET} "
        for week in weeks:
            count = week[row]
            if count == 0:
                line += f"{C.DIM}·{C.RESET} "
            elif count <= 2:
                line += f"{C.GREEN}░{C.RESET} "
            elif count <= 5:
                line += f"{C.GREEN}▒{C.RESET} "
            elif count <= 10:
                line += f"{C.GREEN}▓{C.RESET} "
            else:
                line += f"{C.GREEN}█{C.RESET} "
        print(line)

    fire = "🔥" if current_streak >= 7 else "⚡" if current_streak >= 3 else ""
    print(f"\n  {total_commits} commits · {active_days} active days")
    print(f"  Current streak: {C.BOLD}{current_streak} days{C.RESET} {fire}")
    print(f"  Longest streak: {C.BOLD}{max_streak} days{C.RESET}")


# ─── 26. COMMIT MOOD ──────────────────────────────────────────────────

def git_commit_mood(cwd):
    """Analyze commit mood from diffs."""
    ok, out = _git(["log", "--oneline", "--stat", "-20"], cwd)
    print(f"\n  {C.BOLD}Commit Mood (last 20):{C.RESET}\n")

    current = None
    for line in out.splitlines():
        if re.match(r"^[a-f0-9]+ ", line):
            current = line
        elif "insertion" in line or "deletion" in line:
            ins = int(re.search(r"(\d+) insertion", line).group(1)) if "insertion" in line else 0
            dels = int(re.search(r"(\d+) deletion", line).group(1)) if "deletion" in line else 0
            files = int(re.search(r"(\d+) file", line).group(1)) if "file" in line else 0

            if dels > ins * 3:
                mood = "🗑️  Cleanup"
            elif ins > 100 and files > 5:
                mood = "🚀 Big feature"
            elif ins > dels * 3 and files <= 2:
                mood = "✨ Creative burst"
            elif ins < 10 and dels < 10:
                mood = "🔧 Tiny fix"
            elif files == 1 and "readme" in (current or "").lower():
                mood = "📝 Docs update"
            elif dels > 50:
                mood = "💥 Angry commit"
            else:
                mood = "⚡ Regular"

            sha = (current or "").split()[0] if current else ""
            msg = " ".join((current or "").split()[1:])[:40]
            print(f"  {mood:<20} {C.DIM}{sha}{C.RESET} {msg}  {C.GREEN}+{ins}{C.RESET}/{C.RED}-{dels}{C.RESET}")


# ─── 27. BRANCH MAP ───────────────────────────────────────────────────

def git_branch_map(cwd):
    """ASCII branch divergence map."""
    ok, out = _git(["log", "--all", "--graph", "--oneline", "--decorate", "-25"], cwd)
    print(f"\n  {C.BOLD}Branch Map:{C.RESET}\n")
    for line in out.splitlines():
        print(f"  {line}")

    # Ahead/behind info
    print(f"\n  {C.BOLD}Branch status:{C.RESET}")
    ok, out = _git(["branch", "-vv"], cwd)
    for line in out.splitlines():
        if "ahead" in line or "behind" in line:
            print(f"  {C.YELLOW}{line.strip()}{C.RESET}")
        elif line.startswith("*"):
            print(f"  {C.GREEN}{line.strip()}{C.RESET}")
        else:
            print(f"  {line.strip()}")


# ─── 28. PAIR DETECTOR ────────────────────────────────────────────────

def git_pair_detector(cwd):
    """Find files that always change together."""
    ok, out = _git(["log", "--name-only", "--format=COMMIT", "-100"], cwd)
    if not ok:
        print(f"\n  {C.RED}Error reading log.{C.RESET}"); return

    # Parse commits into file groups
    commits = []
    current = []
    for line in out.splitlines():
        if line == "COMMIT":
            if current:
                commits.append(set(current))
            current = []
        elif line.strip():
            current.append(line.strip())
    if current:
        commits.append(set(current))

    # Count co-occurrences
    pairs = Counter()
    file_count = Counter()
    for files in commits:
        for f in files:
            file_count[f] += 1
        flist = sorted(files)
        for i, a in enumerate(flist):
            for b in flist[i + 1:]:
                pairs[(a, b)] += 1

    # Find strong pairs (>3 co-changes, >50% correlation)
    strong = []
    for (a, b), count in pairs.most_common(50):
        min_count = min(file_count[a], file_count[b])
        if min_count > 0 and count >= 3:
            pct = count / min_count * 100
            if pct >= 50:
                strong.append((a, b, count, pct))

    if not strong:
        print(f"\n  {C.GREEN}No strong file pairs found.{C.RESET}"); return

    print(f"\n  {C.BOLD}Coupled files (always change together):{C.RESET}\n")
    for a, b, count, pct in strong[:10]:
        print(f"  {C.CYAN}{a}{C.RESET}")
        print(f"    ↔ {C.CYAN}{b}{C.RESET}  {count} times ({pct:.0f}%)\n")


# ─── 29. SIZE TRACKER ─────────────────────────────────────────────────

def git_size_tracker(cwd):
    """Track repo size over commits."""
    ok, out = _git(["log", "--oneline", "-20"], cwd)
    commits = out.strip().splitlines()

    print(f"\n  {C.BOLD}Size Tracker (last 20 commits):{C.RESET}\n")
    prev_size = 0
    for line in reversed(commits):
        sha = line.split()[0]
        ok, tree = _git(["ls-tree", "-r", "--long", sha], cwd)
        total = 0
        for tline in tree.splitlines():
            parts = tline.split()
            if len(parts) >= 4:
                try:
                    total += int(parts[3])
                except ValueError:
                    pass
        kb = total // 1024
        diff = kb - prev_size
        diff_str = f"{C.RED}+{diff}KB{C.RESET}" if diff > 0 else f"{C.GREEN}{diff}KB{C.RESET}" if diff < 0 else ""
        msg = " ".join(line.split()[1:])[:30]
        bar = "#" * min(kb // 100, 30)
        print(f"  {C.DIM}{sha}{C.RESET} {kb:>6}KB {C.CYAN}{bar}{C.RESET} {diff_str}  {msg}")
        prev_size = kb


# ─── 30. DEAD CODE CEMETERY ────────────────────────────────────────────

def git_dead_code(cwd):
    """Find deleted functions/classes across history."""
    print(f"\n  {C.BOLD}Dead Code Cemetery{C.RESET}")
    print(f"  {C.DIM}Scanning last 50 commits for deleted code...{C.RESET}\n")

    ok, out = _git(["log", "--diff-filter=D", "--name-only", "--oneline", "-50"], cwd)
    deleted = {}
    current_commit = ""
    for line in out.splitlines():
        if re.match(r"^[a-f0-9]+ ", line):
            current_commit = line
        elif line.strip():
            deleted[line.strip()] = current_commit

    if not deleted:
        print(f"  {C.GREEN}No deleted files in recent history.{C.RESET}"); return

    print(f"  {C.RED}Deleted files ({len(deleted)}):{C.RESET}\n")
    for fname, commit in list(deleted.items())[:20]:
        sha = commit.split()[0]
        msg = " ".join(commit.split()[1:])[:30]
        print(f"  {C.RED}†{C.RESET} {fname}")
        print(f"    {C.DIM}Killed in {sha}: {msg}{C.RESET}\n")


# ─── 31. BUS FACTOR ───────────────────────────────────────────────────

def git_bus_factor(cwd):
    """Per-file author concentration — find risky single-author files."""
    ok, out = _git(["ls-files"], cwd)
    files = [f for f in out.splitlines() if not f.startswith(".")][:50]

    print(f"\n  {C.BOLD}Bus Factor Analysis{C.RESET}")
    print(f"  {C.DIM}Files with only 1 contributor = risk{C.RESET}\n")

    risky = []
    for fname in files:
        ok, blame = _git(["shortlog", "-sn", "--", fname], cwd)
        authors = [line.strip() for line in blame.splitlines() if line.strip()]
        if len(authors) == 1:
            author = authors[0].split("\t")[-1] if "\t" in authors[0] else authors[0]
            risky.append((fname, author))

    if not risky:
        print(f"  {C.GREEN}All files have multiple contributors!{C.RESET}")
        return

    print(f"  {C.RED}{len(risky)}/{len(files)} files have only 1 author:{C.RESET}\n")
    for fname, author in risky[:15]:
        print(f"  {C.RED}!{C.RESET} {fname}  {C.DIM}only: {author}{C.RESET}")
    if len(risky) > 15:
        print(f"  {C.DIM}...and {len(risky) - 15} more{C.RESET}")


# ─── 32. SMART COMMIT ─────────────────────────────────────────────────

def git_smart_commit(cwd):
    """Auto-generate commit message from changes."""
    ok, stat = _git(["diff", "--cached", "--stat"], cwd)
    if not stat.strip():
        # Auto-stage
        print(f"  {C.DIM}Nothing staged. Staging all...{C.RESET}")
        _git(["add", "."], cwd)
        ok, stat = _git(["diff", "--cached", "--stat"], cwd)
        if not stat.strip():
            print(f"  {C.GREEN}Nothing to commit.{C.RESET}"); return

    ok, diff = _git(["diff", "--cached", "--name-status"], cwd)
    added, modified, deleted, renamed = [], [], [], []
    for line in diff.splitlines():
        parts = line.split("\t")
        if not parts:
            continue
        code = parts[0][0]
        fname = parts[-1]
        if code == "A":
            added.append(fname)
        elif code == "M":
            modified.append(fname)
        elif code == "D":
            deleted.append(fname)
        elif code == "R":
            renamed.append(fname)

    # Generate message
    parts = []
    if added:
        if len(added) == 1:
            parts.append(f"Add {added[0]}")
        else:
            parts.append(f"Add {len(added)} files")
    if modified:
        if len(modified) == 1:
            parts.append(f"Update {modified[0]}")
        else:
            # Find common directory
            dirs = set(os.path.dirname(f) for f in modified)
            if len(dirs) == 1 and list(dirs)[0]:
                parts.append(f"Update {list(dirs)[0]}/ ({len(modified)} files)")
            else:
                parts.append(f"Update {len(modified)} files")
    if deleted:
        if len(deleted) == 1:
            parts.append(f"Remove {deleted[0]}")
        else:
            parts.append(f"Remove {len(deleted)} files")
    if renamed:
        parts.append(f"Rename {len(renamed)} files")

    suggested = ", ".join(parts) if parts else "Update"

    print(f"\n  {C.BOLD}Suggested message:{C.RESET}")
    print(f"  {C.CYAN}{suggested}{C.RESET}\n")
    msg = input(f"  {C.YELLOW}> Use this? (Enter=yes, or type new): {C.RESET}").strip()
    msg = msg or suggested

    ok, out = _git(["commit", "-m", msg], cwd)
    print(f"  {C.GREEN}✓ Committed: {msg}{C.RESET}" if ok else f"  {C.RED}{out}{C.RESET}")


# ─── 33. CHANGELOG GENERATOR ──────────────────────────────────────────

def git_changelog(cwd):
    """Generate CHANGELOG.md from commits since last tag."""
    ok, last_tag = _git(["describe", "--tags", "--abbrev=0"], cwd)
    if not ok:
        last_tag = ""
        range_spec = "HEAD"
        print(f"  {C.DIM}No tags found. Generating from all commits.{C.RESET}")
    else:
        last_tag = last_tag.strip()
        range_spec = f"{last_tag}..HEAD"
        print(f"  {C.DIM}Changes since {last_tag}:{C.RESET}")

    ok, out = _git(["log", "--oneline", range_spec], cwd)
    if not out.strip():
        print(f"\n  {C.YELLOW}No new commits since {last_tag}.{C.RESET}"); return

    # Categorize by conventional commit prefixes
    categories = {"feat": [], "fix": [], "docs": [], "refactor": [], "test": [], "chore": [], "other": []}
    for line in out.splitlines():
        msg = " ".join(line.split()[1:])
        matched = False
        for prefix in ["feat", "fix", "docs", "refactor", "test", "chore"]:
            if msg.lower().startswith(prefix):
                categories[prefix].append(msg)
                matched = True
                break
        if not matched:
            categories["other"].append(msg)

    today = datetime.now().strftime("%Y-%m-%d")
    labels = {"feat": "✨ Features", "fix": "🐛 Bug Fixes", "docs": "📝 Documentation",
              "refactor": "♻️ Refactoring", "test": "🧪 Tests", "chore": "🔧 Chores", "other": "📦 Other"}

    changelog = f"# Changelog\n\n## [{today}] — Unreleased\n\n"
    for key, label in labels.items():
        items = categories[key]
        if items:
            changelog += f"### {label}\n\n"
            for item in items:
                changelog += f"- {item}\n"
            changelog += "\n"

    print(f"\n{changelog}")

    save = input(f"  {C.YELLOW}> Save to CHANGELOG.md? (y/n): {C.RESET}").strip().lower()
    if save == "y":
        path = os.path.join(cwd, "CHANGELOG.md")
        with open(path, "w") as f:
            f.write(changelog)
        print(f"  {C.GREEN}✓ Saved to CHANGELOG.md{C.RESET}")


# ─── 34. COMMIT SPLITTER ──────────────────────────────────────────────

def git_commit_splitter(cwd):
    """Split staged changes into multiple commits by folder."""
    ok, out = _git(["diff", "--cached", "--name-only"], cwd)
    if not out.strip():
        print(f"\n  {C.YELLOW}Nothing staged.{C.RESET}"); return

    files = out.strip().splitlines()
    by_dir = defaultdict(list)
    for f in files:
        d = os.path.dirname(f) or "(root)"
        by_dir[d].append(f)

    if len(by_dir) <= 1:
        print(f"\n  {C.DIM}All files in one folder — nothing to split.{C.RESET}"); return

    print(f"\n  {C.BOLD}Staged files by folder:{C.RESET}\n")
    for d, flist in sorted(by_dir.items()):
        print(f"  {C.CYAN}{d}/{C.RESET} ({len(flist)} files)")
        for f in flist[:3]:
            print(f"    {f}")
        if len(flist) > 3:
            print(f"    {C.DIM}...{C.RESET}")

    confirm = input(f"\n  {C.YELLOW}> Commit each folder separately? (y/n): {C.RESET}").strip().lower()
    if confirm != "y":
        return

    # Reset all staged
    _git(["reset", "HEAD"], cwd)

    for d, flist in sorted(by_dir.items()):
        for f in flist:
            _git(["add", f], cwd)
        msg = input(f"  {C.YELLOW}> Message for {d}/ ({len(flist)} files): {C.RESET}").strip()
        if not msg:
            msg = f"Update {d}/"
        _git(["commit", "-m", msg], cwd)
        print(f"  {C.GREEN}✓ Committed {d}/{C.RESET}")


# ─── 35. PR DRAFT ─────────────────────────────────────────────────────

def git_pr_draft(cwd):
    """Generate pull request description from commits."""
    branch = _current_branch(cwd)
    ok, default = _git(["symbolic-ref", "refs/remotes/origin/HEAD", "--short"], cwd)
    main_branch = default.replace("origin/", "").strip() if ok else "main"

    ok, out = _git(["log", "--oneline", f"{main_branch}..{branch}"], cwd)
    if not out.strip():
        print(f"\n  {C.YELLOW}No commits ahead of {main_branch}.{C.RESET}"); return

    commits = out.strip().splitlines()
    ok, stat = _git(["diff", "--stat", f"{main_branch}...{branch}"], cwd)

    pr = f"## {branch}\n\n"
    pr += f"### Changes\n\n"
    for line in commits:
        msg = " ".join(line.split()[1:])
        pr += f"- {msg}\n"
    pr += f"\n### Files Changed\n\n```\n{stat}\n```\n"
    pr += f"\n### Testing\n\n- [ ] Manual testing\n- [ ] Unit tests pass\n\n"

    print(f"\n{pr}")
    print(f"  {C.DIM}Copy this into your GitHub PR description.{C.RESET}")


# ─── 36. AUTO .GITIGNORE ──────────────────────────────────────────────

def git_auto_gitignore(cwd):
    """Detect project type and generate .gitignore."""
    detections = {}

    markers = {
        "Python": ["setup.py", "pyproject.toml", "requirements.txt", "*.py"],
        "Node.js": ["package.json", "node_modules"],
        "Rust": ["Cargo.toml"],
        "Go": ["go.mod"],
        "Java": ["pom.xml", "build.gradle"],
        "C/C++": ["CMakeLists.txt", "Makefile", "*.c", "*.cpp"],
        "Flutter": ["pubspec.yaml"],
        "Ruby": ["Gemfile"],
    }

    templates = {
        "Python": "__pycache__/\n*.pyc\n*.pyo\n*.egg-info/\ndist/\nbuild/\n.venv/\nvenv/\n.env\n*.so\n.mypy_cache/\n.pytest_cache/\n",
        "Node.js": "node_modules/\ndist/\nbuild/\n.env\n*.log\nnpm-debug.log*\n.DS_Store\ncoverage/\n",
        "Rust": "target/\nCargo.lock\n**/*.rs.bk\n",
        "Go": "bin/\n*.exe\n*.test\n*.out\nvendor/\n",
        "Java": "target/\n*.class\n*.jar\n*.war\n.settings/\n.classpath\n.project\nbuild/\n",
        "C/C++": "*.o\n*.so\n*.a\n*.out\nbuild/\ncmake-build*/\n",
        "Flutter": ".dart_tool/\n.packages\nbuild/\n*.iml\n.idea/\n",
        "Ruby": "*.gem\n.bundle/\nvendor/bundle\n*.rbc\n",
    }

    # Common patterns for all
    common = "# OS\n.DS_Store\nThumbs.db\n*.swp\n*~\n\n# IDE\n.idea/\n.vscode/\n*.sublime-*\n\n# Secrets\n.env\n.env.local\n*.pem\n*.key\n\n"

    for lang, files in markers.items():
        for f in files:
            if "*" in f:
                import glob
                if glob.glob(os.path.join(cwd, f)):
                    detections[lang] = True
            elif os.path.exists(os.path.join(cwd, f)):
                detections[lang] = True

    detected = list(detections.keys())
    if not detected:
        print(f"\n  {C.YELLOW}Could not auto-detect project type.{C.RESET}"); return

    print(f"\n  {C.BOLD}Detected: {', '.join(detected)}{C.RESET}\n")

    content = f"# Auto-generated by GitPulse\n\n{common}"
    for lang in detected:
        content += f"# {lang}\n{templates.get(lang, '')}\n"

    existing = os.path.isfile(os.path.join(cwd, ".gitignore"))
    if existing:
        print(f"  {C.YELLOW}.gitignore already exists.{C.RESET}")
        c = input(f"  {C.YELLOW}> (a)ppend / (o)verwrite / (s)how only: {C.RESET}").strip().lower()
    else:
        c = input(f"  {C.YELLOW}> Create .gitignore? (y/n): {C.RESET}").strip().lower()
        c = "o" if c == "y" else "s"

    if c == "a":
        with open(os.path.join(cwd, ".gitignore"), "a") as f:
            f.write("\n" + content)
        print(f"  {C.GREEN}✓ Appended to .gitignore{C.RESET}")
    elif c == "o":
        with open(os.path.join(cwd, ".gitignore"), "w") as f:
            f.write(content)
        print(f"  {C.GREEN}✓ Created .gitignore{C.RESET}")
    else:
        print(content)


# ─── 37. DIFF STORYTELLER ─────────────────────────────────────────────

def git_diff_story(cwd):
    """Human-readable explanation of recent changes."""
    ok, out = _git(["diff", "--cached", "--name-status"], cwd)
    if not out.strip():
        ok, out = _git(["diff", "--name-status", "HEAD~1..HEAD"], cwd)
    if not out.strip():
        print(f"\n  {C.YELLOW}No changes to narrate.{C.RESET}"); return

    added, modified, deleted, renamed = [], [], [], []
    for line in out.splitlines():
        parts = line.split("\t")
        code = parts[0][0]
        fname = parts[-1]
        if code == "A": added.append(fname)
        elif code == "M": modified.append(fname)
        elif code == "D": deleted.append(fname)
        elif code == "R": renamed.append(f"{parts[1]} → {parts[2]}" if len(parts) > 2 else fname)

    print(f"\n  {C.BOLD}{C.CYAN}📖 Change Story:{C.RESET}\n")

    if added:
        exts = set(os.path.splitext(f)[1] for f in added)
        if ".py" in exts:
            print(f"  Created {len(added)} new Python files — expanding the codebase.")
        elif ".html" in exts or ".css" in exts:
            print(f"  Added {len(added)} frontend files — working on the UI.")
        elif ".md" in exts or ".txt" in exts:
            print(f"  Added {len(added)} documentation files.")
        else:
            print(f"  Added {len(added)} new files: {', '.join(f[:30] for f in added[:3])}")

    if modified:
        dirs = set(os.path.dirname(f) or "root" for f in modified)
        if len(modified) == 1:
            print(f"  Edited {modified[0]}.")
        elif len(dirs) == 1:
            print(f"  Updated {len(modified)} files in {list(dirs)[0]}/.")
        else:
            print(f"  Touched {len(modified)} files across {len(dirs)} folders.")

    if deleted:
        if len(deleted) == 1:
            print(f"  Removed {deleted[0]}.")
        else:
            print(f"  Cleaned up {len(deleted)} files.")

    if renamed:
        print(f"  Renamed: {', '.join(renamed[:3])}")

    total = len(added) + len(modified) + len(deleted) + len(renamed)
    if total > 10:
        print(f"\n  {C.DIM}A busy session — {total} files affected.{C.RESET}")
    elif total > 3:
        print(f"\n  {C.DIM}Solid progress — {total} files changed.{C.RESET}")
    else:
        print(f"\n  {C.DIM}Quick touch — {total} file(s).{C.RESET}")


# ─── 38. HOOKS MANAGER ────────────────────────────────────────────────

def git_hooks(cwd):
    """Install/manage git hooks."""
    hooks_dir = os.path.join(cwd, ".git", "hooks")
    print(f"\n  {C.BOLD}Git Hooks Manager{C.RESET}\n")

    available = {
        "pre-commit": "#!/bin/sh\n# Pre-commit: lint & format check\necho '🔍 Running pre-commit checks...'\n\n# Python\nif command -v python3 &>/dev/null; then\n  python3 -m py_compile $(git diff --cached --name-only --diff-filter=ACM | grep '.py$') 2>&1\n  if [ $? -ne 0 ]; then\n    echo '❌ Python syntax error. Fix before committing.'\n    exit 1\n  fi\nfi\n\necho '✅ Pre-commit checks passed.'\n",
        "commit-msg": "#!/bin/sh\n# Commit message format check\nMSG=$(cat \"$1\")\nif [ ${#MSG} -lt 5 ]; then\n  echo '❌ Commit message too short (min 5 chars).'\n  exit 1\nfi\necho '✅ Commit message OK.'\n",
        "pre-push": "#!/bin/sh\n# Pre-push: run tests\necho '🧪 Running pre-push checks...'\nif [ -f 'pytest.ini' ] || [ -d 'tests' ]; then\n  python3 -m pytest -q 2>/dev/null\n  if [ $? -ne 0 ]; then\n    echo '❌ Tests failed. Fix before pushing.'\n    exit 1\n  fi\nfi\necho '✅ Pre-push checks passed.'\n",
    }

    # Show status
    for name in available:
        path = os.path.join(hooks_dir, name)
        installed = os.path.isfile(path) and os.access(path, os.X_OK)
        status = f"{C.GREEN}installed{C.RESET}" if installed else f"{C.DIM}not installed{C.RESET}"
        print(f"  {name:<15} {status}")

    print(f"\n  {C.GREEN}1{C.RESET}  Install pre-commit (syntax check)")
    print(f"  {C.GREEN}2{C.RESET}  Install commit-msg (message format)")
    print(f"  {C.GREEN}3{C.RESET}  Install pre-push (run tests)")
    print(f"  {C.GREEN}4{C.RESET}  Install all")
    print(f"  {C.GREEN}5{C.RESET}  Remove all hooks")
    print(f"  {C.GREEN}0{C.RESET}  Back")

    c = input(f"\n  {C.YELLOW}> {C.RESET}").strip()
    names = {"1": ["pre-commit"], "2": ["commit-msg"], "3": ["pre-push"],
             "4": list(available.keys())}

    if c in names:
        for name in names[c]:
            path = os.path.join(hooks_dir, name)
            with open(path, "w") as f:
                f.write(available[name])
            os.chmod(path, 0o755)
            print(f"  {C.GREEN}✓ Installed {name}{C.RESET}")
    elif c == "5":
        for name in available:
            path = os.path.join(hooks_dir, name)
            if os.path.isfile(path):
                os.remove(path)
        print(f"  {C.GREEN}✓ All hooks removed.{C.RESET}")


# ─── 39. GIT ALIASES ──────────────────────────────────────────────────

def git_aliases(cwd):
    """Install useful git aliases."""
    aliases = {
        "gs": "status -sb",
        "ga": "add .",
        "gc": "commit -m",
        "gp": "push",
        "gl": "log --oneline --graph --decorate -15",
        "gd": "diff --stat",
        "gb": "branch -vv",
        "gco": "checkout",
        "gcb": "checkout -b",
        "gpl": "pull --rebase",
        "gst": "stash",
        "gsp": "stash pop",
    }

    print(f"\n  {C.BOLD}Git Aliases Installer{C.RESET}\n")
    for alias, cmd in aliases.items():
        print(f"  {C.CYAN}{alias:<6}{C.RESET} → git {cmd}")

    confirm = input(f"\n  {C.YELLOW}> Install all aliases globally? (y/n): {C.RESET}").strip().lower()
    if confirm != "y":
        return

    for alias, cmd in aliases.items():
        _run(["git", "config", "--global", f"alias.{alias}", cmd])
    print(f"\n  {C.GREEN}✓ {len(aliases)} aliases installed.{C.RESET}")
    print(f"  {C.DIM}Try: git gs, git gl, git gc 'message'{C.RESET}")


# ─── 40. REFLOG RESCUE ────────────────────────────────────────────────

def git_reflog_rescue(cwd):
    """Browse reflog to recover lost commits."""
    ok, out = _git(["reflog", "--oneline", "-30"], cwd)
    if not out.strip():
        print(f"\n  {C.YELLOW}Empty reflog.{C.RESET}"); return

    entries = out.strip().splitlines()
    print(f"\n  {C.BOLD}Reflog (recent history, including 'deleted'):{C.RESET}\n")
    for i, line in enumerate(entries, 1):
        print(f"  {C.GREEN}{i:>3}{C.RESET}  {line}")

    idx = input(f"\n  {C.YELLOW}> Restore to # (or Enter to skip): {C.RESET}").strip()
    if not idx.isdigit() or not (0 < int(idx) <= len(entries)):
        return

    sha = entries[int(idx) - 1].split()[0]
    print(f"\n  {C.GREEN}1{C.RESET}  Create branch from this point")
    print(f"  {C.GREEN}2{C.RESET}  Hard reset to this point (dangerous)")

    c = input(f"\n  {C.YELLOW}> {C.RESET}").strip()
    if c == "1":
        name = input(f"  {C.YELLOW}> Branch name: {C.RESET}").strip() or "recovered"
        ok, out = _git(["checkout", "-b", name, sha], cwd)
        print(f"  {C.GREEN}✓ Created branch '{name}' at {sha}{C.RESET}" if ok else f"  {C.RED}{out}{C.RESET}")
    elif c == "2":
        confirm = input(f"  {C.RED}This will LOSE current uncommitted changes. Sure? (y/n): {C.RESET}").strip().lower()
        if confirm == "y":
            ok, out = _git(["reset", "--hard", sha], cwd)
            print(f"  {C.GREEN}✓ Reset to {sha}{C.RESET}" if ok else f"  {C.RED}{out}{C.RESET}")


# ─── 41. PATCH MANAGER ────────────────────────────────────────────────

def git_patch(cwd):
    """Export/apply changes as patch files."""
    print(f"\n  {C.BOLD}Patch Manager{C.RESET}\n")
    print(f"  {C.GREEN}1{C.RESET}  Export current changes as patch")
    print(f"  {C.GREEN}2{C.RESET}  Export last N commits as patches")
    print(f"  {C.GREEN}3{C.RESET}  Apply a patch file")
    print(f"  {C.GREEN}0{C.RESET}  Back")

    c = input(f"\n  {C.YELLOW}> {C.RESET}").strip()
    if c == "1":
        name = f"changes-{datetime.now().strftime('%Y%m%d-%H%M%S')}.patch"
        ok, out = _git(["diff"], cwd)
        if not out.strip():
            print(f"  {C.YELLOW}No unstaged changes.{C.RESET}"); return
        path = os.path.join(cwd, name)
        with open(path, "w") as f:
            f.write(out)
        print(f"  {C.GREEN}✓ Saved: {name}{C.RESET}")
    elif c == "2":
        n = input(f"  {C.YELLOW}> How many commits: {C.RESET}").strip() or "1"
        ok, out = _git(["format-patch", f"-{n}", "--output-directory", cwd], cwd)
        if ok:
            print(f"  {C.GREEN}✓ Created {n} patch file(s) in repo root.{C.RESET}")
        else:
            print(f"  {C.RED}{out}{C.RESET}")
    elif c == "3":
        fname = input(f"  {C.YELLOW}> Patch file path: {C.RESET}").strip()
        if not fname:
            return
        ok, out = _git(["apply", fname], cwd)
        print(f"  {C.GREEN}✓ Patch applied.{C.RESET}" if ok else f"  {C.RED}{out}{C.RESET}")


# ═══════════════════════════════════════════════════════════════════════
#  MAIN MENU
# ═══════════════════════════════════════════════════════════════════════

def gitops_menu_beginner(cwd):
    """Beginner git operations menu."""
    while True:
        name = _repo_name(cwd)
        branch = _current_branch(cwd)
        print(f"\n  {C.BOLD}{C.CYAN}=== GIT: {name} ({branch}) ==={C.RESET}\n")
        print(f"  {C.GREEN}1{C.RESET}  Status             {C.DIM}See what changed{C.RESET}")
        print(f"  {C.GREEN}2{C.RESET}  Pull               {C.DIM}Download latest{C.RESET}")
        print(f"  {C.GREEN}3{C.RESET}  Quick Sync ⚡       {C.DIM}Save + upload all{C.RESET}")
        print(f"  {C.GREEN}4{C.RESET}  Commit             {C.DIM}Save with message{C.RESET}")
        print(f"  {C.GREEN}5{C.RESET}  Push               {C.DIM}Upload to GitHub{C.RESET}")
        print(f"  {C.GREEN}6{C.RESET}  Undo file          {C.DIM}Restore a file{C.RESET}")
        print(f"  {C.GREEN}7{C.RESET}  Snapshot            {C.DIM}Save game{C.RESET}")
        print(f"  {C.GREEN}8{C.RESET}  Streak 🔥          {C.DIM}Your commit heatmap{C.RESET}")
        print(f"  {C.GREEN}0{C.RESET}  {t('back')}")

        c = input(f"\n  {C.YELLOW}> {C.RESET}").strip()
        if c == "1": git_status(cwd)
        elif c == "2": git_pull(cwd)
        elif c == "3": git_quick_sync(cwd)
        elif c == "4":
            git_stage_all(cwd)
            git_commit(cwd)
        elif c == "5": git_push(cwd)
        elif c == "6": git_undo_file(cwd)
        elif c == "7": git_snapshot(cwd)
        elif c == "8": git_commit_streak(cwd)
        elif c == "0": return
        input(f"\n  {C.DIM}{t('press_enter')}{C.RESET}")


def gitops_menu_advanced(cwd):
    """Full git operations menu."""
    while True:
        name = _repo_name(cwd)
        branch = _current_branch(cwd)
        print(f"\n  {C.BOLD}{C.CYAN}=== GIT OPS: {name} ({branch}) ==={C.RESET}")

        print(f"\n  {C.DIM}BASICS{C.RESET}")
        print(f"   {C.GREEN}1{C.RESET}  Status            {C.GREEN}5{C.RESET}  Commit")
        print(f"   {C.GREEN}2{C.RESET}  Pull              {C.GREEN}6{C.RESET}  Push")
        print(f"   {C.GREEN}3{C.RESET}  Stage all         {C.GREEN}7{C.RESET}  Quick Sync ⚡")
        print(f"   {C.GREEN}4{C.RESET}  Stage pick        {C.GREEN}8{C.RESET}  Diff")

        print(f"\n  {C.DIM}UNDO & SAFETY{C.RESET}")
        print(f"   {C.GREEN}9{C.RESET}  Undo file        {C.GREEN}12{C.RESET}  Conflict resolver")
        print(f"  {C.GREEN}10{C.RESET}  Undo commit      {C.GREEN}13{C.RESET}  Secret Rewind 🧹")
        print(f"  {C.GREEN}11{C.RESET}  Stash            {C.GREEN}14{C.RESET}  Snapshot 💾")

        print(f"\n  {C.DIM}BRANCHES{C.RESET}")
        print(f"  {C.GREEN}15{C.RESET}  Branch manager   {C.GREEN}17{C.RESET}  Merge Preview")
        print(f"  {C.GREEN}16{C.RESET}  Log graph        {C.GREEN}18{C.RESET}  Cherry-pick")

        print(f"\n  {C.DIM}HISTORY{C.RESET}")
        print(f"  {C.GREEN}19{C.RESET}  Blame            {C.GREEN}22{C.RESET}  Auto Squash")
        print(f"  {C.GREEN}20{C.RESET}  Bisect wizard    {C.GREEN}23{C.RESET}  Time travel")
        print(f"  {C.GREEN}21{C.RESET}  Tag manager      {C.GREEN}24{C.RESET}  Reflog rescue")

        print(f"\n  {C.DIM}INSIGHTS{C.RESET}")
        print(f"  {C.GREEN}25{C.RESET}  Commit Streak 🔥 {C.GREEN}29{C.RESET}  Size Tracker")
        print(f"  {C.GREEN}26{C.RESET}  Commit Mood      {C.GREEN}30{C.RESET}  Dead Code Cemetery")
        print(f"  {C.GREEN}27{C.RESET}  Branch Map       {C.GREEN}31{C.RESET}  Bus Factor")
        print(f"  {C.GREEN}28{C.RESET}  Pair Detector")

        print(f"\n  {C.DIM}GENERATORS{C.RESET}")
        print(f"  {C.GREEN}32{C.RESET}  Smart Commit     {C.GREEN}35{C.RESET}  PR Draft")
        print(f"  {C.GREEN}33{C.RESET}  Changelog        {C.GREEN}36{C.RESET}  Auto .gitignore")
        print(f"  {C.GREEN}34{C.RESET}  Commit Splitter  {C.GREEN}37{C.RESET}  Diff Storyteller")

        print(f"\n  {C.DIM}SETUP{C.RESET}")
        print(f"  {C.GREEN}38{C.RESET}  Hooks Manager    {C.GREEN}40{C.RESET}  Git Aliases")
        print(f"  {C.GREEN}39{C.RESET}  Patch Manager    {C.GREEN}41{C.RESET}  Repo Health")

        print(f"\n  {C.GREEN} 0{C.RESET}  {t('back')}")

        c = input(f"\n  {C.YELLOW}> {C.RESET}").strip()
        dispatch = {
            "1": git_status, "2": git_pull, "3": git_stage_all,
            "4": git_stage_pick, "5": git_commit, "6": git_push,
            "7": git_quick_sync, "8": git_diff, "9": git_undo_file,
            "10": git_undo_commit, "11": git_stash, "12": git_conflict_resolver,
            "13": git_secret_rewind, "14": git_snapshot, "15": git_branches,
            "16": git_log_graph, "17": git_merge_preview, "18": git_cherry_pick,
            "19": git_blame, "20": git_bisect, "21": git_tags,
            "22": git_auto_squash, "23": git_time_travel, "24": git_reflog_rescue,
            "25": git_commit_streak, "26": git_commit_mood, "27": git_branch_map,
            "28": git_pair_detector, "29": git_size_tracker, "30": git_dead_code,
            "31": git_bus_factor, "32": git_smart_commit, "33": git_changelog,
            "34": git_commit_splitter, "35": git_pr_draft, "36": git_auto_gitignore,
            "37": git_diff_story, "38": git_hooks, "39": git_patch,
            "40": git_aliases, "41": git_repo_health,
        }

        if c == "0":
            return
        elif c in dispatch:
            dispatch[c](cwd)
        else:
            print(f"  {C.RED}Invalid.{C.RESET}")

        input(f"\n  {C.DIM}{t('press_enter')}{C.RESET}")


def gitops_entry(mode="advanced"):
    """Entry point — pick repo then show menu."""
    cwd = _pick_local_repo()
    if not cwd:
        return
    if mode == "beginner":
        gitops_menu_beginner(cwd)
    else:
        gitops_menu_advanced(cwd)
