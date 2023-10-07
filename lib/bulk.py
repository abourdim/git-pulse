"""Bulk operations — mass changes across repos."""

import os

from .api import GitHubAPI
from .colors import C
from .config import load as load_config
from .i18n import t


def bulk_menu(gh: GitHubAPI):
    while True:
        print(f"""
  {C.BOLD}{'=' * 40}{C.RESET}
  {C.BOLD}{C.CYAN}BULK OPERATIONS{C.RESET}
  {C.BOLD}{'=' * 40}{C.RESET}

  {C.GREEN}1{C.RESET}  Visibility   {C.DIM}(private / public){C.RESET}
  {C.GREEN}2{C.RESET}  Archive      {C.DIM}(archive / unarchive){C.RESET}
  {C.GREEN}3{C.RESET}  Metadata     {C.DIM}(description / topics){C.RESET}
  {C.GREEN}4{C.RESET}  Clone        {C.DIM}(download repos){C.RESET}
  {C.GREEN}5{C.RESET}  Pages        {C.DIM}(GitHub Pages on / off){C.RESET}
  {C.GREEN}6{C.RESET}  {C.RED}Delete{C.RESET}       {C.DIM}(permanent){C.RESET}
  {C.GREEN}0{C.RESET}  {t('back')}
""")
        choice = input(f"  {C.YELLOW}> Action: {C.RESET}").strip()
        if choice == "0":
            break
        elif choice == "1":
            _sub_visibility(gh)
        elif choice == "2":
            _sub_archive(gh)
        elif choice == "3":
            _sub_metadata(gh)
        elif choice == "4":
            _sub_clone(gh)
        elif choice == "5":
            _sub_pages(gh)
        elif choice == "6":
            _sub_delete(gh)
        else:
            continue
        input(f"\n  {C.DIM}{t('press_enter')}{C.RESET}")


# ─── SUB-MENUS ───────────────────────────────────────────────

def _sub_visibility(gh):
    print(f"""
  {C.BOLD}Visibility{C.RESET}
  {C.GREEN}1{C.RESET}  All private
  {C.GREEN}2{C.RESET}  All public
  {C.GREEN}3{C.RESET}  Select repos
  {C.GREEN}0{C.RESET}  {t('back')}""")
    c = input(f"\n  {C.YELLOW}> Choice: {C.RESET}").strip()
    if c == "1":
        repos = _fetch_all(gh)
        if repos:
            _bulk_apply(gh, repos, "Make private", lambda gh, r: gh.update_repo(r["name"], private=True))
    elif c == "2":
        repos = _fetch_all(gh)
        if repos:
            _bulk_apply(gh, repos, "Make public", lambda gh, r: gh.update_repo(r["name"], private=False))
    elif c == "3":
        private = input(f"  {C.YELLOW}> Make [p]rivate or pu[b]lic? {C.RESET}").strip().lower()
        if private in ("p", "private"):
            selected = _select_repos(gh, "Make private")
            if selected:
                _bulk_apply(gh, selected, "Make private", lambda gh, r: gh.update_repo(r["name"], private=True))
        elif private in ("b", "public"):
            selected = _select_repos(gh, "Make public")
            if selected:
                _bulk_apply(gh, selected, "Make public", lambda gh, r: gh.update_repo(r["name"], private=False))


def _sub_archive(gh):
    print(f"""
  {C.BOLD}Archive{C.RESET}
  {C.GREEN}1{C.RESET}  Archive all
  {C.GREEN}2{C.RESET}  Unarchive all
  {C.GREEN}3{C.RESET}  Select repos
  {C.GREEN}0{C.RESET}  {t('back')}""")
    c = input(f"\n  {C.YELLOW}> Choice: {C.RESET}").strip()
    if c == "1":
        repos = _fetch_all(gh)
        if repos:
            _bulk_apply(gh, repos, "Archive", lambda gh, r: gh.update_repo(r["name"], archived=True))
    elif c == "2":
        repos = _fetch_all(gh)
        if repos:
            _bulk_apply(gh, repos, "Unarchive", lambda gh, r: gh.update_repo(r["name"], archived=False))
    elif c == "3":
        action = input(f"  {C.YELLOW}> [a]rchive or [u]narchive? {C.RESET}").strip().lower()
        if action in ("a", "archive"):
            selected = _select_repos(gh, "Archive")
            if selected:
                _bulk_apply(gh, selected, "Archive", lambda gh, r: gh.update_repo(r["name"], archived=True))
        elif action in ("u", "unarchive"):
            selected = _select_repos(gh, "Unarchive")
            if selected:
                _bulk_apply(gh, selected, "Unarchive", lambda gh, r: gh.update_repo(r["name"], archived=False))


def _sub_metadata(gh):
    print(f"""
  {C.BOLD}Metadata{C.RESET}
  {C.GREEN}1{C.RESET}  Set description
  {C.GREEN}2{C.RESET}  Add topics
  {C.GREEN}0{C.RESET}  {t('back')}""")
    c = input(f"\n  {C.YELLOW}> Choice: {C.RESET}").strip()
    if c == "1":
        selected = _select_repos(gh, "Set description")
        if selected:
            _bulk_description(gh, selected)
    elif c == "2":
        selected = _select_repos(gh, "Add topics")
        if selected:
            _bulk_topics(gh, selected)


def _sub_clone(gh):
    print(f"""
  {C.BOLD}Clone{C.RESET}
  {C.GREEN}1{C.RESET}  Clone all repos
  {C.GREEN}2{C.RESET}  Select repos
  {C.GREEN}0{C.RESET}  {t('back')}""")
    c = input(f"\n  {C.YELLOW}> Choice: {C.RESET}").strip()
    if c == "1":
        repos = _fetch_all(gh)
        if repos:
            _bulk_clone(gh, repos)
    elif c == "2":
        selected = _select_repos(gh, "Clone")
        if selected:
            _bulk_clone(gh, selected)


def _sub_pages(gh):
    print(f"""
  {C.BOLD}GitHub Pages{C.RESET}
  {C.GREEN}1{C.RESET}  Disable all
  {C.GREEN}2{C.RESET}  Enable all
  {C.GREEN}3{C.RESET}  Select repos
  {C.GREEN}0{C.RESET}  {t('back')}""")
    c = input(f"\n  {C.YELLOW}> Choice: {C.RESET}").strip()
    if c == "1":
        repos = _fetch_all(gh)
        if repos:
            _bulk_pages(gh, repos, enable=False)
    elif c == "2":
        repos = _fetch_all(gh)
        if repos:
            _bulk_pages(gh, repos, enable=True)
    elif c == "3":
        action = input(f"  {C.YELLOW}> [e]nable or [d]isable? {C.RESET}").strip().lower()
        if action in ("e", "enable"):
            selected = _select_repos(gh, "Enable Pages")
            if selected:
                _bulk_pages(gh, selected, enable=True)
        elif action in ("d", "disable"):
            selected = _select_repos(gh, "Disable Pages")
            if selected:
                _bulk_pages(gh, selected, enable=False)


def _sub_delete(gh):
    selected = _select_repos(gh, "Delete")
    if selected:
        _bulk_delete(gh, selected)


# ─── HELPERS ─────────────────────────────────────────────────

def _fetch_all(gh):
    print(f"\n  {C.DIM}{t('fetching')}{C.RESET}")
    repos = gh.list_repos()
    if not repos:
        print(f"  {C.YELLOW}{t('no_results')}{C.RESET}")
        return []
    print(f"  {C.BOLD}{len(repos)} repos found{C.RESET}")
    return repos


def _select_repos(gh, action_name):
    print(f"\n  {C.DIM}{t('fetching')}{C.RESET}")
    repos = gh.list_repos()
    if not repos:
        print(f"  {C.YELLOW}{t('no_results')}{C.RESET}")
        return []

    print(f"\n  {C.BOLD}Select repos for: {action_name}{C.RESET}")
    print(f"  {C.DIM}Numbers, range '1-5', or 'a' for all{C.RESET}\n")

    for i, r in enumerate(repos, 1):
        vis = f"{C.RED}priv{C.RESET}" if r["private"] else f"{C.GREEN}pub {C.RESET}"
        arch = f" {C.YELLOW}[archived]{C.RESET}" if r.get("archived") else ""
        print(f"  {C.GREEN}{i:>3}{C.RESET}  {vis} {r['name']}{arch}")

    sel = input(f"\n  {C.YELLOW}> Select: {C.RESET}").strip()
    if not sel:
        return []

    indices = set()
    if sel.lower() == "a":
        indices = set(range(len(repos)))
    else:
        for part in sel.split():
            if "-" in part:
                try:
                    a, b = part.split("-", 1)
                    indices.update(range(int(a) - 1, int(b)))
                except ValueError:
                    pass
            elif part.isdigit():
                indices.add(int(part) - 1)

    selected = [repos[i] for i in sorted(indices) if 0 <= i < len(repos)]
    if selected:
        print(f"\n  {C.BOLD}Selected {len(selected)} repos:{C.RESET} {', '.join(r['name'] for r in selected)}")
    return selected


def _bulk_apply(gh, repos, action_name, action_fn):
    confirm = input(f"\n  {C.YELLOW}> Apply '{action_name}' to {len(repos)} repos? [y/N]: {C.RESET}").strip().lower()
    if confirm != "y":
        print(f"  {C.YELLOW}{t('cancelled')}{C.RESET}")
        return

    ok = fail = 0
    for r in repos:
        print(f"  {r['name']}...", end=" ", flush=True)
        try:
            _, status = action_fn(gh, r)
            if status == 200:
                print(f"{C.GREEN}done{C.RESET}")
                ok += 1
            else:
                print(f"{C.RED}failed ({status}){C.RESET}")
                fail += 1
        except Exception as e:
            print(f"{C.RED}error: {e}{C.RESET}")
            fail += 1
    print(f"\n  {C.GREEN}+ {ok} success, {fail} failed{C.RESET}")


def _bulk_description(gh, repos):
    desc = input(f"\n  {C.YELLOW}> New description: {C.RESET}").strip()
    if not desc:
        return
    confirm = input(f"  {C.YELLOW}> Set on {len(repos)} repos? [y/N]: {C.RESET}").strip().lower()
    if confirm != "y":
        return
    ok = fail = 0
    for r in repos:
        print(f"  {r['name']}...", end=" ", flush=True)
        _, status = gh.update_repo(r["name"], description=desc)
        if status == 200:
            print(f"{C.GREEN}done{C.RESET}"); ok += 1
        else:
            print(f"{C.RED}failed{C.RESET}"); fail += 1
    print(f"\n  {C.GREEN}+ {ok} success, {fail} failed{C.RESET}")


def _bulk_topics(gh, repos):
    topics_str = input(f"\n  {C.YELLOW}> Topics (comma-separated): {C.RESET}").strip()
    if not topics_str:
        return
    topics = [t.strip().lower().replace(" ", "-") for t in topics_str.split(",") if t.strip()]
    confirm = input(f"  {C.YELLOW}> Add {topics} to {len(repos)} repos? [y/N]: {C.RESET}").strip().lower()
    if confirm != "y":
        return

    import requests as req
    ok = fail = 0
    for r in repos:
        print(f"  {r['name']}...", end=" ", flush=True)
        url = f"https://api.github.com/repos/{gh.username}/{r['name']}/topics"
        headers = {**gh.headers, "Accept": "application/vnd.github.mercy-preview+json"}
        resp = req.get(url, headers=headers)
        existing = resp.json().get("names", []) if resp.status_code == 200 else []
        merged = list(set(existing + topics))
        resp2 = req.put(url, headers=headers, json={"names": merged})
        if resp2.status_code == 200:
            print(f"{C.GREEN}done{C.RESET}"); ok += 1
        else:
            print(f"{C.RED}failed{C.RESET}"); fail += 1
    print(f"\n  {C.GREEN}+ {ok} success, {fail} failed{C.RESET}")


def _bulk_delete(gh, repos):
    print(f"\n  {C.RED}{C.BOLD}WARNING: This will permanently delete {len(repos)} repos!{C.RESET}")
    confirm = input(f"  {C.RED}> Type 'DELETE ALL' to confirm: {C.RESET}").strip()
    if confirm != "DELETE ALL":
        print(f"  {C.YELLOW}{t('cancelled')}{C.RESET}")
        return
    ok = fail = 0
    for r in repos:
        print(f"  {r['name']}...", end=" ", flush=True)
        status = gh.delete_repo(r["name"])
        if status == 204:
            print(f"{C.GREEN}deleted{C.RESET}"); ok += 1
        else:
            print(f"{C.RED}failed ({status}){C.RESET}"); fail += 1
    print(f"\n  {C.GREEN}+ {ok} deleted, {fail} failed{C.RESET}")


def _bulk_pages(gh, repos, enable=False):
    action = "Enable" if enable else "Disable"
    confirm = input(f"\n  {C.YELLOW}> {action} GitHub Pages on {len(repos)} repos? [y/N]: {C.RESET}").strip().lower()
    if confirm != "y":
        print(f"  {C.YELLOW}{t('cancelled')}{C.RESET}")
        return

    ok = skip = fail = 0
    for r in repos:
        name = r["name"]
        print(f"  {name}...", end=" ", flush=True)
        try:
            pages = gh.get_pages(name)
            if enable:
                if pages is not None:
                    print(f"{C.YELLOW}already enabled{C.RESET}")
                    skip += 1
                    continue
                branch = r.get("default_branch", "main")
                _, status = gh.enable_pages(name, branch)
                if status in (201, 409):
                    print(f"{C.GREEN}enabled{C.RESET}")
                    ok += 1
                else:
                    print(f"{C.RED}failed ({status}){C.RESET}")
                    fail += 1
            else:
                if pages is None:
                    print(f"{C.YELLOW}no pages{C.RESET}")
                    skip += 1
                    continue
                status = gh.disable_pages(name)
                if status == 204:
                    print(f"{C.GREEN}disabled{C.RESET}")
                    ok += 1
                else:
                    print(f"{C.RED}failed ({status}){C.RESET}")
                    fail += 1
        except Exception as e:
            print(f"{C.RED}error: {e}{C.RESET}")
            fail += 1
    print(f"\n  {C.GREEN}+ {ok} {action.lower()}d, {skip} skipped, {fail} failed{C.RESET}")


def _bulk_clone(gh, repos):
    config = load_config()
    default_dir = config.get("clone_directory", os.path.expanduser("~/repos"))
    dest = input(f"\n  {C.YELLOW}> Clone directory [{default_dir}]: {C.RESET}").strip() or default_dir
    os.makedirs(dest, exist_ok=True)

    confirm = input(f"  {C.YELLOW}> Clone {len(repos)} repos to {dest}? [y/N]: {C.RESET}").strip().lower()
    if confirm != "y":
        print(f"  {C.YELLOW}{t('cancelled')}{C.RESET}")
        return

    ok = skip = fail = 0
    for r in repos:
        name = r["name"]
        target = os.path.join(dest, name)
        print(f"  {name}...", end=" ", flush=True)
        if os.path.exists(target):
            print(f"{C.YELLOW}skipped (already exists){C.RESET}")
            skip += 1
            continue
        try:
            success, err = gh.clone_repo(name, dest)
            if success:
                print(f"{C.GREEN}done{C.RESET}")
                ok += 1
            else:
                print(f"{C.RED}failed: {err.strip()}{C.RESET}")
                fail += 1
        except Exception as e:
            print(f"{C.RED}error: {e}{C.RESET}")
            fail += 1
    print(f"\n  {C.GREEN}+ {ok} cloned, {skip} skipped, {fail} failed{C.RESET}")
