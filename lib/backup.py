"""Backup manager — clone all repos, compress, schedule."""

import os
import shutil
import subprocess
from datetime import datetime
from pathlib import Path

from .api import GitHubAPI
from .colors import C
from .ui import pick_repo
from .config import load as load_config, save as save_config
from .i18n import t


def _backup_dir(config: dict) -> Path:
    return Path(config.get("backup_directory", str(Path.home() / "github-backups")))


def backup_menu(gh: GitHubAPI):
    config = load_config()
    bdir = _backup_dir(config)
    while True:
        last_run = config.get("backup_last_run", "Never")
        print(f"""
  {C.BOLD}{'=' * 50}{C.RESET}
  {C.BOLD}{C.CYAN}BACKUP MANAGER{C.RESET}
  {C.BOLD}{'=' * 50}{C.RESET}

  Backup dir:  {C.DIM}{bdir}{C.RESET}
  Last backup: {C.DIM}{last_run}{C.RESET}

  {C.GREEN}1{C.RESET}  Backup all repos (clone/pull)
  {C.GREEN}2{C.RESET}  Backup single repo
  {C.GREEN}3{C.RESET}  Compress backups (.tar.gz)
  {C.GREEN}4{C.RESET}  List backups
  {C.GREEN}5{C.RESET}  Change backup directory
  {C.GREEN}0{C.RESET}  {t('back')}
""")
        choice = input(f"  {C.YELLOW}> Option: {C.RESET}").strip()
        if choice == "0":
            break
        elif choice == "1":
            _backup_all(gh, config, bdir)
        elif choice == "2":
            _backup_single(gh, bdir)
        elif choice == "3":
            _compress_backups(bdir)
        elif choice == "4":
            _list_backups(bdir)
        elif choice == "5":
            new_dir = input(f"  {C.YELLOW}> New backup directory: {C.RESET}").strip()
            if new_dir:
                config["backup_directory"] = new_dir
                save_config(config)
                bdir = Path(new_dir)
                print(f"  {C.GREEN}+ Saved.{C.RESET}")
        if choice in ("1", "2", "3", "4", "5"):
            input(f"\n  {C.DIM}{t('press_enter')}{C.RESET}")


def _backup_all(gh, config, bdir):
    print(f"\n  {C.DIM}{t('fetching')}{C.RESET}")
    repos = gh.list_repos()
    if not repos:
        print(f"  {C.YELLOW}{t('no_results')}{C.RESET}"); return
    bdir.mkdir(parents=True, exist_ok=True)
    print(f"\n  {C.BOLD}Backing up {len(repos)} repos to {bdir}{C.RESET}\n")
    ok = fail = 0
    for i, repo in enumerate(repos, 1):
        name = repo["name"]
        dest = bdir / name
        print(f"  [{i}/{len(repos)}] {name}...", end=" ", flush=True)
        if dest.exists() and (dest / ".git").exists():
            r = subprocess.run(["git", "pull", "--quiet"], cwd=str(dest), capture_output=True, text=True)
            print(f"{C.GREEN}pulled{C.RESET}" if r.returncode == 0 else f"{C.RED}pull failed{C.RESET}")
        else:
            r = subprocess.run(["git", "clone", "--quiet", repo["clone_url"], str(dest)], capture_output=True, text=True)
            print(f"{C.GREEN}cloned{C.RESET}" if r.returncode == 0 else f"{C.RED}clone failed{C.RESET}")
        ok += 1 if r.returncode == 0 else 0
        fail += 0 if r.returncode == 0 else 1
    config["backup_last_run"] = datetime.now().isoformat()
    save_config(config)
    print(f"\n  {C.GREEN}+ Done: {ok} success, {fail} failed{C.RESET}")


def _backup_single(gh, bdir):
    name = pick_repo(gh)
    if not name: return
    bdir.mkdir(parents=True, exist_ok=True)
    dest = bdir / name
    if dest.exists() and (dest / ".git").exists():
        print(f"  {C.DIM}Pulling updates...{C.RESET}")
        r = subprocess.run(["git", "pull", "--quiet"], cwd=str(dest), capture_output=True, text=True)
        print(f"  {C.GREEN}+ Updated{C.RESET}" if r.returncode == 0 else f"  {C.RED}x Failed{C.RESET}")
    else:
        print(f"  {C.DIM}Cloning...{C.RESET}")
        url = f"https://github.com/{gh.username}/{name}.git"
        r = subprocess.run(["git", "clone", "--quiet", url, str(dest)], capture_output=True, text=True)
        print(f"  {C.GREEN}+ Cloned{C.RESET}" if r.returncode == 0 else f"  {C.RED}x Failed: {r.stderr}{C.RESET}")


def _compress_backups(bdir):
    if not bdir.exists():
        print(f"  {C.YELLOW}No backups to compress.{C.RESET}"); return
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    archive = bdir.parent / f"github-backup-{stamp}"
    print(f"  {C.DIM}Compressing...{C.RESET}")
    shutil.make_archive(str(archive), "gztar", str(bdir.parent), bdir.name)
    size_mb = os.path.getsize(f"{archive}.tar.gz") / (1024 * 1024)
    print(f"  {C.GREEN}+ {archive}.tar.gz ({size_mb:.1f} MB){C.RESET}")


def _list_backups(bdir):
    if not bdir.exists():
        print(f"  {C.YELLOW}No backups found.{C.RESET}"); return
    dirs = sorted([d for d in bdir.iterdir() if d.is_dir() and (d / ".git").exists()])
    if not dirs:
        print(f"  {C.YELLOW}Empty.{C.RESET}"); return
    print(f"\n  {C.BOLD}Backups ({len(dirs)} repos):{C.RESET}\n")
    for d in dirs:
        r = subprocess.run(["git", "log", "-1", "--format=%ai"], cwd=str(d), capture_output=True, text=True)
        date = r.stdout.strip()[:19] if r.returncode == 0 else "?"
        size = sum(f.stat().st_size for f in d.rglob("*") if f.is_file()) / (1024 * 1024)
        print(f"    {C.CYAN}{d.name:<30}{C.RESET}  {date}  {size:.1f} MB")
