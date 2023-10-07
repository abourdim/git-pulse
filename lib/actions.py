"""Menu actions for GitPulse."""
from __future__ import annotations

import os
from .api import GitHubAPI
from .colors import C
from .config import CONFIG_FILE, VERSION, load as load_config, save as save_config
from .i18n import t, set_language
from .ui import format_date, format_size, visibility_badge, pick_repo, clear_repo_cache


# ─── 1. List Repos ────────────────────────────────────────────

def list_repos(gh: GitHubAPI):
    config = load_config()
    sort = config.get("default_sort", "updated")
    direction = config.get("default_direction", "desc")
    repo_type = config.get("default_repo_type", "all")

    print(f"\n  {C.DIM}{t('fetching')}{C.RESET}")
    repos = gh.list_repos(sort=sort, direction=direction, repo_type=repo_type)

    if not repos:
        print(f"\n  {C.YELLOW}{t('no_results')}{C.RESET}")
        return

    print(f"\n  {C.BOLD}Found {len(repos)} repositories:{C.RESET}\n")
    print(f"  {C.BOLD}{'#':>3}  {'Name':<30} {'Vis':>10}  {'Updated':<18} {'*':>3}  {'Size':>8}{C.RESET}")
    print(f"  {'-' * 85}")

    for i, repo in enumerate(repos, 1):
        name = repo["name"][:28]
        vis = "private" if repo["private"] else "public"
        vis_c = C.RED if repo["private"] else C.GREEN
        updated = format_date(repo.get("updated_at", ""))
        stars = repo.get("stargazers_count", 0)
        size = format_size(repo.get("size", 0))
        lang = repo.get("language") or ""
        print(f"  {C.DIM}{i:>3}{C.RESET}  {C.CYAN}{name:<30}{C.RESET} "
              f"{vis_c}{vis:>10}{C.RESET}  {updated:<18} "
              f"{stars:>3}  {size:>8}  {C.DIM}{lang}{C.RESET}")

    # Let user pick one for details
    print(f"\n  {C.DIM}Pick a number to see details, or Enter to go back{C.RESET}")
    choice = input(f"  {C.YELLOW}> {C.RESET}").strip()
    if choice.isdigit():
        idx = int(choice) - 1
        if 0 <= idx < len(repos):
            _show_repo_details(gh, repos[idx]["name"])


# ─── 2. Search ────────────────────────────────────────────────

def search_repos(gh: GitHubAPI):
    query = input(f"\n  {C.YELLOW}> Search: {C.RESET}").strip()
    if not query:
        return
    print(f"\n  {C.DIM}{t('searching')}{C.RESET}")
    repos = gh.search_repos(query)
    if not repos:
        print(f"\n  {C.YELLOW}{t('no_results')}{C.RESET}")
        return
    print(f"\n  {C.BOLD}Found {len(repos)} results:{C.RESET}\n")
    for i, repo in enumerate(repos, 1):
        desc = (repo.get("description") or "")[:60]
        print(f"  {C.GREEN}{i:>3}{C.RESET}  {C.CYAN}{repo['name']:<30}{C.RESET}  {C.DIM}{desc}{C.RESET}")

    # Let user pick one for details
    print(f"\n  {C.DIM}Pick a number to see details, or Enter to go back{C.RESET}")
    choice = input(f"  {C.YELLOW}> {C.RESET}").strip()
    if choice.isdigit():
        idx = int(choice) - 1
        if 0 <= idx < len(repos):
            _show_repo_details(gh, repos[idx]["name"])


# ─── Helper: show repo details ───────────────────────────────

def _show_repo_details(gh: GitHubAPI, name: str):
    repo = gh.get_repo(name)
    if not repo or "message" in repo:
        print(f"\n  {C.RED}x {t('not_found')}{C.RESET}")
        return
    langs = gh.get_languages(name)
    total_bytes = sum(langs.values()) or 1

    print(f"""
  {C.BOLD}{'=' * 50}{C.RESET}
  {C.BOLD}{C.CYAN}{repo['full_name']}{C.RESET}  {visibility_badge(repo['private'])}
  {C.BOLD}{'=' * 50}{C.RESET}

  {C.BOLD}Description:{C.RESET}  {repo.get('description') or 'N/A'}
  {C.BOLD}URL:{C.RESET}          {repo['html_url']}
  {C.BOLD}Clone:{C.RESET}        {repo['clone_url']}
  {C.BOLD}Created:{C.RESET}      {format_date(repo['created_at'])}
  {C.BOLD}Updated:{C.RESET}      {format_date(repo['updated_at'])}
  {C.BOLD}Pushed:{C.RESET}       {format_date(repo.get('pushed_at', ''))}
  {C.BOLD}Size:{C.RESET}         {format_size(repo['size'])}
  {C.BOLD}Stars:{C.RESET}        {repo['stargazers_count']}
  {C.BOLD}Forks:{C.RESET}        {repo['forks_count']}
  {C.BOLD}Open Issues:{C.RESET}  {repo['open_issues_count']}
  {C.BOLD}Default:{C.RESET}      {repo['default_branch']}
  {C.BOLD}License:{C.RESET}      {(repo.get('license') or {}).get('name', 'None')}""")

    if langs:
        print(f"\n  {C.BOLD}Languages:{C.RESET}")
        for lang, bytes_ in sorted(langs.items(), key=lambda x: x[1], reverse=True):
            pct = bytes_ / total_bytes * 100
            bar = "#" * int(pct / 3)
            print(f"    {lang:<15} {C.CYAN}{bar}{C.RESET} {pct:.1f}%")


# ─── 3. Repo Details ──────────────────────────────────────────

def repo_details(gh: GitHubAPI):
    name = pick_repo(gh)
    if not name:
        return
    _show_repo_details(gh, name)


# ─── 4. Create Repo ───────────────────────────────────────────

def create_repo(gh: GitHubAPI):
    name = input(f"\n  {C.YELLOW}> Repo name: {C.RESET}").strip()
    if not name: return
    desc = input(f"  {C.YELLOW}> Description: {C.RESET}").strip()
    priv = input(f"  {C.YELLOW}> Private? [Y/n]: {C.RESET}").strip().lower()
    init = input(f"  {C.YELLOW}> Init with README? [Y/n]: {C.RESET}").strip().lower()

    print(f"\n  {C.DIM}Creating '{name}'...{C.RESET}")
    result, status = gh.create_repo(name, desc, priv != "n", init != "n")
    if status == 201:
        print(f"\n  {C.GREEN}+ {t('created')}{C.RESET}")
        print(f"  {C.BOLD}URL:{C.RESET} {result['html_url']}")
        clear_repo_cache()
    else:
        print(f"\n  {C.RED}x {t('failed')}: {result.get('message', 'Unknown')}{C.RESET}")
        for err in result.get("errors", []):
            print(f"    {C.RED}- {err.get('message', err)}{C.RESET}")


# ─── 5. Delete Repo ───────────────────────────────────────────

def delete_repo(gh: GitHubAPI):
    name = pick_repo(gh, "Repo to DELETE")
    if not name: return
    print(f"\n  {C.RED}{C.BOLD}WARNING: Permanently deletes '{gh.username}/{name}'!{C.RESET}")
    confirm = input(f"  {C.RED}> Type repo name to confirm: {C.RESET}").strip()
    if confirm != name:
        print(f"\n  {C.YELLOW}{t('cancelled')}{C.RESET}")
        return
    status = gh.delete_repo(name)
    clear_repo_cache()
    msgs = {204: f"\n  {C.GREEN}+ {t('deleted')}{C.RESET}",
            404: f"\n  {C.RED}x {t('not_found')}{C.RESET}",
            403: f"\n  {C.RED}x Permission denied. Token needs 'delete_repo' scope.{C.RESET}"}
    print(msgs.get(status, f"\n  {C.RED}x {t('failed')} (HTTP {status}).{C.RESET}"))


# ─── 6. Edit Repo ─────────────────────────────────────────────

def edit_repo(gh: GitHubAPI):
    name = pick_repo(gh, "Repo to edit")
    if not name: return
    repo = gh.get_repo(name)
    if not repo or "message" in repo:
        print(f"\n  {C.RED}x {t('not_found')}{C.RESET}"); return

    cur_topics = ", ".join(repo.get("topics", []))
    cur_homepage = repo.get("homepage") or ""

    print(f"\n  {C.BOLD}Current:{C.RESET}")
    print(f"    Name:           {repo['name']}")
    print(f"    Description:    {repo.get('description') or 'N/A'}")
    print(f"    Visibility:     {'private' if repo['private'] else 'public'}")
    print(f"    Default branch: {repo.get('default_branch', 'main')}")
    print(f"    Topics:         {cur_topics or 'N/A'}")
    print(f"    Homepage:       {cur_homepage or 'N/A'}")
    print(f"    Wiki:           {'on' if repo.get('has_wiki', True) else 'off'}")
    print(f"    Issues:         {'on' if repo.get('has_issues', True) else 'off'}")
    print(f"    Archived:       {'yes' if repo.get('archived', False) else 'no'}")
    pages_info = gh.get_pages(name) if hasattr(gh, 'get_pages') else None
    pages_on = pages_info is not None
    pages_url = pages_info.get("html_url", "") if pages_info else ""
    print(f"    GitHub Pages:   {'on' if pages_on else 'off'}{' — ' + pages_url if pages_url else ''}")

    print(f"\n  {C.DIM}Leave blank to keep current.{C.RESET}")
    new_name = input(f"  {C.YELLOW}> New name [{repo['name']}]: {C.RESET}").strip()
    new_desc = input(f"  {C.YELLOW}> New description: {C.RESET}").strip()
    cur_vis = "private" if repo["private"] else "public"
    new_vis = input(f"  {C.YELLOW}> Visibility (public/private) [{cur_vis}]: {C.RESET}").strip().lower()
    new_branch = input(f"  {C.YELLOW}> Default branch [{repo.get('default_branch', 'main')}]: {C.RESET}").strip()
    new_topics = input(f"  {C.YELLOW}> Topics (comma-separated) [{cur_topics}]: {C.RESET}").strip()
    new_homepage = input(f"  {C.YELLOW}> Homepage URL [{cur_homepage}]: {C.RESET}").strip()
    new_wiki = input(f"  {C.YELLOW}> Wiki on/off [{'on' if repo.get('has_wiki', True) else 'off'}]: {C.RESET}").strip().lower()
    new_issues = input(f"  {C.YELLOW}> Issues on/off [{'on' if repo.get('has_issues', True) else 'off'}]: {C.RESET}").strip().lower()
    new_archived = input(f"  {C.YELLOW}> Archived yes/no [{'yes' if repo.get('archived', False) else 'no'}]: {C.RESET}").strip().lower()
    new_pages = input(f"  {C.YELLOW}> GitHub Pages on/off [{'on' if pages_on else 'off'}]: {C.RESET}").strip().lower()

    updates = {}
    if new_name: updates["name"] = new_name
    if new_desc: updates["description"] = new_desc
    if new_vis in ("public", "private"): updates["private"] = new_vis == "private"
    if new_branch: updates["default_branch"] = new_branch
    if new_topics:
        updates["topics"] = [t.strip().lower().replace(" ", "-") for t in new_topics.split(",") if t.strip()]
    if new_homepage is not None and new_homepage != "":
        updates["homepage"] = new_homepage
    if new_wiki in ("on", "off"): updates["has_wiki"] = new_wiki == "on"
    if new_issues in ("on", "off"): updates["has_issues"] = new_issues == "on"
    if new_archived in ("yes", "no"): updates["archived"] = new_archived == "yes"

    if not updates:
        print(f"\n  {C.YELLOW}No changes.{C.RESET}"); return

    # Topics use a separate API endpoint
    topics_list = updates.pop("topics", None)

    if updates:
        repo_name = updates.pop("name", name)
        result, status = gh.update_repo(repo_name, **updates)
        if status == 200:
            print(f"\n  {C.GREEN}+ {t('updated')}{C.RESET}")
        else:
            print(f"\n  {C.RED}x {t('failed')}: {result.get('message', 'Unknown')}{C.RESET}")

    if topics_list is not None:
        import requests as req
        url = f"https://api.github.com/repos/{gh.username}/{new_name or name}/topics"
        headers = {**gh.headers, "Accept": "application/vnd.github.mercy-preview+json"}
        resp = req.put(url, headers=headers, json={"names": topics_list})
        if resp.status_code == 200:
            print(f"  {C.GREEN}+ Topics updated{C.RESET}")
        else:
            print(f"  {C.RED}x Topics failed: {resp.json().get('message', 'Unknown')}{C.RESET}")

    if new_pages in ("on", "off") and hasattr(gh, 'get_pages'):
        target_name = new_name or name
        if new_pages == "on" and not pages_on:
            branch = repo.get("default_branch", "main")
            _, status = gh.enable_pages(target_name, branch)
            if status in (201, 409):
                print(f"  {C.GREEN}+ GitHub Pages enabled{C.RESET}")
            else:
                print(f"  {C.RED}x Pages failed (HTTP {status}){C.RESET}")
        elif new_pages == "off" and pages_on:
            status = gh.disable_pages(target_name)
            if status == 204:
                print(f"  {C.GREEN}+ GitHub Pages disabled{C.RESET}")
            else:
                print(f"  {C.RED}x Pages failed (HTTP {status}){C.RESET}")


# ─── 7. Clone ─────────────────────────────────────────────────

def clone_repo(gh: GitHubAPI):
    name = pick_repo(gh, "Repo to clone")
    if not name: return
    config = load_config()
    default_dir = config.get("clone_directory", os.getcwd())
    dest = input(f"  {C.YELLOW}> Destination [{default_dir}]: {C.RESET}").strip() or default_dir

    print(f"\n  {C.DIM}Cloning {gh.username}/{name}...{C.RESET}")
    ok, err = gh.clone_repo(name, dest)
    if ok:
        print(f"\n  {C.GREEN}+ Cloned to {dest}/{name}{C.RESET}")
    else:
        print(f"\n  {C.RED}x Clone failed: {err}{C.RESET}")


# ─── 8. Commits ───────────────────────────────────────────────

def view_commits(gh: GitHubAPI):
    name = pick_repo(gh)
    if not name: return
    config = load_config()
    default_count = config.get("commits_count", 10)

    commits = gh.list_commits(name, default_count)
    if not commits:
        print(f"\n  {C.YELLOW}{t('no_results')}{C.RESET}"); return

    print(f"\n  {C.BOLD}Recent commits for {name}:{C.RESET}\n")
    for c in commits:
        sha = c["sha"][:7]
        msg = c["commit"]["message"].split("\n")[0][:60]
        author = c["commit"]["author"]["name"]
        date = format_date(c["commit"]["author"]["date"])
        print(f"  {C.YELLOW}{sha}{C.RESET}  {msg:<60}  {C.DIM}{author} - {date}{C.RESET}")


# ─── 9. Branches ──────────────────────────────────────────────

def view_branches(gh: GitHubAPI):
    name = pick_repo(gh)
    if not name: return
    branches = gh.list_branches(name)
    if not branches:
        print(f"\n  {C.YELLOW}{t('no_results')}{C.RESET}"); return

    print(f"\n  {C.BOLD}Branches for {name}:{C.RESET}\n")
    for b in branches:
        prot = f" {C.RED}(protected){C.RESET}" if b.get("protected") else ""
        print(f"    {C.CYAN}-{C.RESET} {b['name']}{prot}")


# ─── 10. Quick Stats ──────────────────────────────────────────

def quick_stats(gh: GitHubAPI):
    print(f"\n  {C.DIM}{t('fetching')}{C.RESET}")
    repos = gh.list_repos()
    total = len(repos)
    public = sum(1 for r in repos if not r["private"])
    private = total - public
    forks = sum(1 for r in repos if r["fork"])
    total_stars = sum(r.get("stargazers_count", 0) for r in repos)
    total_size = sum(r.get("size", 0) for r in repos)

    lang_count: dict[str, int] = {}
    for r in repos:
        lang = r.get("language")
        if lang: lang_count[lang] = lang_count.get(lang, 0) + 1

    most_recent = repos[0] if repos else None

    print(f"""
  {C.BOLD}{'=' * 50}{C.RESET}
  {C.BOLD}{C.CYAN}Account Overview: {gh.username}{C.RESET}
  {C.BOLD}{'=' * 50}{C.RESET}

  {C.BOLD}Repositories:{C.RESET}   {total} total ({C.GREEN}{public} public{C.RESET}, {C.RED}{private} private{C.RESET})
  {C.BOLD}Forked:{C.RESET}         {forks}
  {C.BOLD}Total Stars:{C.RESET}    {total_stars}
  {C.BOLD}Total Size:{C.RESET}     {format_size(total_size)}
  {C.BOLD}Followers:{C.RESET}      {gh.user.get('followers', 0)}
  {C.BOLD}Following:{C.RESET}      {gh.user.get('following', 0)}""")

    if most_recent:
        print(f"  {C.BOLD}Last Updated:{C.RESET}   {most_recent['name']} ({format_date(most_recent['updated_at'])})")
    if lang_count:
        print(f"\n  {C.BOLD}Top Languages:{C.RESET}")
        for lang, count in sorted(lang_count.items(), key=lambda x: x[1], reverse=True)[:8]:
            bar = "#" * count
            print(f"    {lang:<15} {C.CYAN}{bar}{C.RESET} {count}")


# ─── 11. Settings ─────────────────────────────────────────────

def settings(config: dict) -> dict:
    while True:
        token_display = ("****" + config["token"][-4:] if len(config.get("token", "")) > 4 else "(not set)")
        mode_icon = "\U0001f423" if config.get("mode") == "beginner" else "\U0001f525"
        lang_map = {"en": "English", "fr": "Fran\u00e7ais", "ar": "\u0627\u0644\u0639\u0631\u0628\u064a\u0629"}

        print(f"""
  {C.BOLD}{'=' * 50}{C.RESET}
  {C.BOLD}{C.CYAN}GitPulse {t('a_settings')}{C.RESET}
  {C.BOLD}{'=' * 50}{C.RESET}

  Config: {C.DIM}{CONFIG_FILE}{C.RESET}

  {C.GREEN} 1{C.RESET}  Token:           {C.DIM}{token_display}{C.RESET}
  {C.GREEN} 2{C.RESET}  Default sort:    {config.get('default_sort', 'updated')}
  {C.GREEN} 3{C.RESET}  Sort direction:  {config.get('default_direction', 'desc')}
  {C.GREEN} 4{C.RESET}  Repo type:       {config.get('default_repo_type', 'all')}
  {C.GREEN} 5{C.RESET}  Clone directory: {config.get('clone_directory', '~/repos')}
  {C.GREEN} 6{C.RESET}  Commits count:   {config.get('commits_count', 10)}
  {C.GREEN} 7{C.RESET}  Mode:            {mode_icon} {config.get('mode', 'advanced')}
  {C.GREEN} 8{C.RESET}  Language:        {lang_map.get(config.get('language', 'en'), 'English')}
  {C.GREEN} 9{C.RESET}  Theme (web):     {config.get('web_theme', 'masjid')}
  {C.GREEN}10{C.RESET}  {C.RED}Reset token{C.RESET}
  {C.GREEN} 0{C.RESET}  {t('back')}
""")
        choice = input(f"  {C.YELLOW}> Option: {C.RESET}").strip()

        if choice == "0":
            break
        elif choice == "1":
            val = input(f"  {C.YELLOW}> New token: {C.RESET}").strip()
            if val:
                config["token"] = val
                save_config(config)
                print(f"  {C.GREEN}+ Token updated. Restart to apply.{C.RESET}")
        elif choice == "2":
            print(f"  Options: updated, created, pushed, full_name")
            val = input(f"  {C.YELLOW}> Sort [{config['default_sort']}]: {C.RESET}").strip()
            if val in ("updated", "created", "pushed", "full_name"):
                config["default_sort"] = val; save_config(config)
                print(f"  {C.GREEN}+ Saved.{C.RESET}")
        elif choice == "3":
            val = input(f"  {C.YELLOW}> Direction (desc/asc) [{config['default_direction']}]: {C.RESET}").strip()
            if val in ("desc", "asc"):
                config["default_direction"] = val; save_config(config)
                print(f"  {C.GREEN}+ Saved.{C.RESET}")
        elif choice == "4":
            print(f"  Options: all, owner, public, private, forks")
            val = input(f"  {C.YELLOW}> Type [{config['default_repo_type']}]: {C.RESET}").strip()
            if val in ("all", "owner", "public", "private", "forks"):
                config["default_repo_type"] = val; save_config(config)
                print(f"  {C.GREEN}+ Saved.{C.RESET}")
        elif choice == "5":
            val = input(f"  {C.YELLOW}> Directory [{config['clone_directory']}]: {C.RESET}").strip()
            if val:
                config["clone_directory"] = val; save_config(config)
                print(f"  {C.GREEN}+ Saved.{C.RESET}")
        elif choice == "6":
            val = input(f"  {C.YELLOW}> Count [{config['commits_count']}]: {C.RESET}").strip()
            if val.isdigit():
                config["commits_count"] = int(val); save_config(config)
                print(f"  {C.GREEN}+ Saved.{C.RESET}")
        elif choice == "7":
            print(f"  {C.GREEN}1{C.RESET} \U0001f423 Beginner   {C.GREEN}2{C.RESET} \U0001f525 Advanced")
            val = input(f"  {C.YELLOW}> Mode [{config.get('mode', 'advanced')}]: {C.RESET}").strip()
            if val == "1": config["mode"] = "beginner"; save_config(config); print(f"  {C.GREEN}+ Saved.{C.RESET}")
            elif val == "2": config["mode"] = "advanced"; save_config(config); print(f"  {C.GREEN}+ Saved.{C.RESET}")
        elif choice == "8":
            print(f"  {C.GREEN}1{C.RESET} English  {C.GREEN}2{C.RESET} Fran\u00e7ais  {C.GREEN}3{C.RESET} \u0627\u0644\u0639\u0631\u0628\u064a\u0629")
            val = input(f"  {C.YELLOW}> Language: {C.RESET}").strip()
            lang_set = {"1": "en", "2": "fr", "3": "ar"}
            if val in lang_set:
                config["language"] = lang_set[val]; save_config(config)
                set_language(lang_set[val])
                print(f"  {C.GREEN}+ Saved. Restart for full effect.{C.RESET}")
        elif choice == "9":
            themes = ["andalus", "masjid", "alhamra", "nur", "raqsh", "sahra", "zahra"]
            for i, th in enumerate(themes, 1):
                print(f"  {C.GREEN}{i}{C.RESET}  {th}")
            val = input(f"  {C.YELLOW}> Theme [{config.get('web_theme', 'masjid')}]: {C.RESET}").strip()
            if val.isdigit() and 1 <= int(val) <= len(themes):
                config["web_theme"] = themes[int(val) - 1]; save_config(config)
                print(f"  {C.GREEN}+ Saved.{C.RESET}")
        elif choice == "10":
            confirm = input(f"  {C.RED}> Remove token? [y/N]: {C.RESET}").strip().lower()
            if confirm == "y":
                config["token"] = ""; save_config(config)
                print(f"  {C.GREEN}+ Token removed.{C.RESET}")

    return config
