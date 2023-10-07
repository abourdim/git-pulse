#!/usr/bin/env python3
"""
GitPulse — GitHub repo manager.
Powered by workshop-diy.org

Usage:
    python gitpulse.py          CLI mode
    python gitpulse.py --web    Web UI
    python gitpulse.py --demo   Demo mode (no token needed)
    python gitpulse.py --web --demo   Web UI demo
"""

import os
import sys

# Ensure lib/ is found regardless of working directory
os.chdir(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from lib.colors import C
from lib.config import load, save, VERSION, CODENAME, CONFIG_FILE
from lib.api import GitHubAPI
from lib.i18n import t, set_language
from lib.ui import clear, banner, menu, pause, first_run
from lib import actions
from lib.backup import backup_menu
from lib.health import health_dashboard
from lib.bulk import bulk_menu
from lib.gitlog import git_log_interactive
from lib.search import search_menu
from lib.workflows import workflows_menu
from lib.releases import releases_menu
from lib.templates import templates_menu
from lib.sshkeys import ssh_menu
from lib.timestamps import timestamps_menu
from lib.analytics import analytics_menu
from lib.deps import deps_menu
from lib.ai import ai_menu
from lib.danger import danger_menu
from lib.archaeology import archaeology_menu
from lib.grouper import grouper_menu
from lib.rhythm import rhythm_menu
from lib.accounts import accounts_menu
from lib.gitops import gitops_entry


def authenticate(config: dict) -> tuple:
    from lib.demo import DemoAPI

    # --demo flag
    if "--demo" in sys.argv:
        gh = DemoAPI()
        print(f"  {C.YELLOW}{C.BOLD}★ DEMO MODE{C.RESET} — using 17 sample repos")
        dn = config.get("display_name") or gh.username
        print(f"  {C.GREEN}+ Logged in as {C.BOLD}{dn}{C.RESET}\n")
        return gh, config

    token = config.get("token") or os.environ.get("GITHUB_TOKEN", "")

    if not token:
        print(f"  {C.DIM}{t('create_token')}{C.RESET}")
        print(f"  {C.DIM}{t('token_scopes')}{C.RESET}")
        print(f"  {C.DIM}Type {C.BOLD}demo{C.DIM} to try without a token{C.RESET}\n")
        token = input(f"  {C.YELLOW}> GitHub token: {C.RESET}").strip()

        if token.lower() == "demo":
            gh = DemoAPI()
            print(f"\n  {C.YELLOW}{C.BOLD}★ DEMO MODE{C.RESET} — using 17 sample repos")
            dn = config.get("display_name") or gh.username
            print(f"  {C.GREEN}+ Logged in as {C.BOLD}{dn}{C.RESET}\n")
            return gh, config

        if token:
            yn = input(f"  {C.YELLOW}> {t('save_token')} [Y/n]: {C.RESET}").strip().lower()
            if yn != "n":
                config["token"] = token
                save(config)
                print(f"  {C.GREEN}+ {t('token_saved')} {CONFIG_FILE}{C.RESET}")
    else:
        src = "config" if config.get("token") else "GITHUB_TOKEN env"
        print(f"  {C.DIM}{t('token_from')} {src}{C.RESET}")

    if not token:
        print(f"\n  {C.RED}x {t('no_token')}{C.RESET}")
        sys.exit(1)

    print(f"\n  {C.DIM}{t('authenticating')}{C.RESET}")
    gh = GitHubAPI(token)
    dn = config.get("display_name") or gh.username
    print(f"  {C.GREEN}+ {t('logged_in')} {C.BOLD}{dn}{C.RESET}\n")
    return gh, config


def main():
    clear()
    config = load()
    set_language(config.get("language", "en"))

    if not config.get("mode"):
        mode, language = first_run()
        config["mode"] = mode
        config["language"] = language
        set_language(language)
        save(config)

    mode = config.get("mode", "advanced")

    # Splash
    print(f"\n  {C.BOLD}{t('bismillah')}{C.RESET}\n")
    print(f"{C.CYAN}{C.BOLD}+----------------------------------------------------------+")
    print(f"|  GitPulse v{VERSION} ({CODENAME})")
    print(f"|  {t('powered_by')}")
    print(f"+----------------------------------------------------------+{C.RESET}\n")

    gh, config = authenticate(config)

    # Full dispatch table (advanced mode)
    dispatch_advanced = {
        "1": actions.list_repos,     "2": actions.search_repos,
        "3": actions.repo_details,   "4": actions.create_repo,
        "5": actions.delete_repo,    "6": actions.edit_repo,
        "7": actions.clone_repo,     "8": actions.view_commits,
        "9": actions.view_branches,  "10": backup_menu,
        "11": health_dashboard,      "12": bulk_menu,
        "13": git_log_interactive,   "14": search_menu,
        "15": workflows_menu,        "16": releases_menu,
        "17": templates_menu,        "18": ssh_menu,
        "19": timestamps_menu,       "20": analytics_menu,
        "21": deps_menu,             "22": ai_menu,
        "23": danger_menu,           "24": archaeology_menu,
        "25": grouper_menu,          "26": rhythm_menu,
        # 27 = accounts (special), 28 = gitops (special), 29 = stats
    }

    dispatch_beginner = {
        "1": actions.list_repos,     "2": actions.search_repos,
        "3": actions.repo_details,   "4": actions.create_repo,
        "5": actions.edit_repo,      "6": actions.clone_repo,
        "7": actions.quick_stats,
    }

    settings_key = "30" if mode == "advanced" else "9"

    while True:
        clear()
        banner(gh.username, mode)
        choice = menu(mode)

        if choice == "0":
            print(f"\n  {C.GREEN}{t('bye')}{C.RESET}\n")
            break
        elif choice == settings_key:
            try:
                config = actions.settings(config)
                new_mode = config.get("mode", mode)
                if new_mode != mode:
                    mode = new_mode
                    settings_key = "30" if mode == "advanced" else "9"
            except KeyboardInterrupt:
                pass
            continue

        # Special: multi-account returns new gh
        if mode == "advanced" and choice == "27":
            try:
                gh = accounts_menu(gh)
            except KeyboardInterrupt:
                print(f"\n  {C.YELLOW}{t('cancelled')}{C.RESET}")
            pause()
            continue


        # Git Operations (no gh needed)
        if choice == "28" and mode == "advanced":
            try:
                gitops_entry("advanced")
            except KeyboardInterrupt:
                print(f"\n  {C.YELLOW}{t('cancelled')}{C.RESET}")
            pause()
            continue

        if choice == "8" and mode == "beginner":
            try:
                gitops_entry("beginner")
            except KeyboardInterrupt:
                print(f"\n  {C.YELLOW}{t('cancelled')}{C.RESET}")
            pause()
            continue

        # Quick stats
        if mode == "advanced" and choice == "29":
            try:
                actions.quick_stats(gh)
            except KeyboardInterrupt:
                print(f"\n  {C.YELLOW}{t('cancelled')}{C.RESET}")
            except Exception as e:
                print(f"\n  {C.RED}x Error: {e}{C.RESET}")
            pause()
            continue

        dispatch = dispatch_advanced if mode == "advanced" else dispatch_beginner
        action = dispatch.get(choice)
        if action:
            try:
                action(gh)
            except KeyboardInterrupt:
                print(f"\n  {C.YELLOW}{t('cancelled')}{C.RESET}")
            except Exception as e:
                print(f"\n  {C.RED}x Error: {e}{C.RESET}")
            pause()
        else:
            print(f"\n  {C.RED}Invalid option.{C.RESET}")
            pause()


if __name__ == "__main__":
    if "--web" in sys.argv:
        clear()
        config = load()
        set_language(config.get("language", "en"))
        print(f"\n  {C.BOLD}{t('bismillah')}{C.RESET}\n")
        print(f"{C.CYAN}{C.BOLD}+----------------------------------------------------------+")
        print(f"|  GitPulse v{VERSION} ({CODENAME}) — Web UI")
        print(f"|  {t('powered_by')}")
        print(f"+----------------------------------------------------------+{C.RESET}\n")

        gh = None
        if "--demo" in sys.argv:
            from lib.demo import DemoAPI
            gh = DemoAPI()
            print(f"  {C.YELLOW}{C.BOLD}★ DEMO MODE{C.RESET}\n")
        elif config.get("token"):
            try:
                gh = GitHubAPI(config["token"])
                dn = config.get("display_name") or gh.username
                print(f"  {C.GREEN}+ {t('logged_in')} {C.BOLD}{dn}{C.RESET}\n")
            except SystemExit:
                gh = None

        if not gh:
            print(f"  {C.CYAN}Open browser — connect token or try demo from the welcome page.{C.RESET}\n")

        from web.server import start_server
        start_server(gh, config)
    else:
        main()
