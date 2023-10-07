"""Multi-Account Support — switch between personal/work/client accounts."""
from __future__ import annotations

import json
from pathlib import Path
from .api import GitHubAPI
from .colors import C
from .config import CONFIG_DIR, load as load_config, save as save_config
from .i18n import t

ACCOUNTS_FILE = CONFIG_DIR / "accounts.json"


def load_accounts() -> dict:
    if ACCOUNTS_FILE.exists():
        try:
            return json.loads(ACCOUNTS_FILE.read_text())
        except (json.JSONDecodeError, IOError):
            pass
    return {}


def save_accounts(accounts: dict):
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    ACCOUNTS_FILE.write_text(json.dumps(accounts, indent=2))
    try:
        ACCOUNTS_FILE.chmod(0o600)
    except OSError:
        pass


def add_account(label: str, token: str) -> tuple[bool, str]:
    """Add or update an account. Returns (success, username)."""
    try:
        gh = GitHubAPI(token)
        accounts = load_accounts()
        accounts[label] = {
            "token": token,
            "username": gh.username,
        }
        save_accounts(accounts)
        return True, gh.username
    except SystemExit:
        return False, ""


def remove_account(label: str) -> bool:
    accounts = load_accounts()
    if label in accounts:
        del accounts[label]
        save_accounts(accounts)
        return True
    return False


def switch_account(label: str) -> GitHubAPI | None:
    """Switch to an account. Returns new GitHubAPI or None."""
    accounts = load_accounts()
    if label not in accounts:
        return None
    token = accounts[label]["token"]
    config = load_config()
    config["token"] = token
    config["active_account"] = label
    save_config(config)
    return GitHubAPI(token)


def list_accounts() -> list:
    """List all configured accounts."""
    accounts = load_accounts()
    config = load_config()
    active = config.get("active_account", "")
    result = []
    for label, info in accounts.items():
        result.append({
            "label": label,
            "username": info.get("username", "?"),
            "active": label == active,
        })
    return result


def accounts_menu(gh: GitHubAPI) -> GitHubAPI:
    """CLI menu for multi-account management. Returns (possibly new) gh."""
    while True:
        accounts = list_accounts()

        print(f"\n  {C.BOLD}{C.CYAN}=== MULTI-ACCOUNT ==={C.RESET}\n")
        print(f"  {C.BOLD}Current:{C.RESET} {C.GREEN}{gh.username}{C.RESET}\n")

        if accounts:
            print(f"  {C.BOLD}Saved accounts:{C.RESET}")
            for i, acc in enumerate(accounts, 1):
                active = f" {C.GREEN}(active){C.RESET}" if acc["active"] else ""
                print(f"    {C.GREEN}{i}{C.RESET}  {acc['label']} — {C.CYAN}{acc['username']}{C.RESET}{active}")
            print()

        print(f"  {C.GREEN}a{C.RESET}  Add account")
        print(f"  {C.GREEN}s{C.RESET}  Switch account")
        print(f"  {C.GREEN}r{C.RESET}  Remove account")
        print(f"  {C.GREEN}0{C.RESET}  {t('back')}")

        choice = input(f"\n  {C.YELLOW}> {t('choose')}: {C.RESET}").strip().lower()

        if choice == "0":
            break
        elif choice == "a":
            label = input(f"  {C.YELLOW}> Account label (e.g. 'work'): {C.RESET}").strip()
            if not label: continue
            token = input(f"  {C.YELLOW}> GitHub token: {C.RESET}").strip()
            if not token: continue
            print(f"\n  {C.DIM}{t('authenticating')}{C.RESET}")
            ok, username = add_account(label, token)
            if ok:
                print(f"  {C.GREEN}+ Added '{label}' ({username}){C.RESET}")
            else:
                print(f"  {C.RED}x Invalid token.{C.RESET}")

        elif choice == "s":
            if not accounts:
                print(f"  {C.YELLOW}No accounts saved yet.{C.RESET}"); continue
            label = input(f"  {C.YELLOW}> Account label: {C.RESET}").strip()
            print(f"\n  {C.DIM}Switching...{C.RESET}")
            new_gh = switch_account(label)
            if new_gh:
                gh = new_gh
                print(f"  {C.GREEN}+ Switched to {gh.username}{C.RESET}")
            else:
                print(f"  {C.RED}x Account '{label}' not found.{C.RESET}")

        elif choice == "r":
            label = input(f"  {C.YELLOW}> Account label to remove: {C.RESET}").strip()
            if remove_account(label):
                print(f"  {C.GREEN}+ Removed '{label}'.{C.RESET}")
            else:
                print(f"  {C.RED}x Not found.{C.RESET}")

    return gh
