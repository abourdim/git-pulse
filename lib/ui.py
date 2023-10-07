"""UI helpers: banner, menus, formatting — with bismillah and mode support."""
from __future__ import annotations

import os
from datetime import datetime

from .colors import C
from .config import VERSION, CODENAME
from .i18n import t


def clear():
    os.system("cls" if os.name == "nt" else "clear")


def banner(username: str, mode: str):
    bismillah = t("bismillah")
    powered = t("powered_by")
    mode_icon = "\U0001f423" if mode == "beginner" else "\U0001f525"
    mode_label = t("beginner") if mode == "beginner" else t("advanced")

    print(f"""
  {C.BOLD}{bismillah}{C.RESET}

{C.CYAN}{C.BOLD}+----------------------------------------------------------+
|  GitPulse v{VERSION} ({CODENAME})          {powered:>25s} |
+----------------------------------------------------------+
|  User: {username:<20s}  Mode: {mode_icon} {mode_label:<20s}|
+----------------------------------------------------------+{C.RESET}
""")


def menu_beginner() -> str:
    items = [
        ("1", t("b_view")),
        ("2", t("b_search")),
        ("3", t("b_details")),
        ("4", t("b_create")),
        ("5", t("b_edit")),
        ("6", t("b_download")),
        ("7", t("b_overview")),
        ("8", "Git Operations ⚡"),
        ("9", t("b_settings")),
        ("0", t("exit")),
    ]
    print(f"  {C.BOLD}{t('b_projects')}{C.RESET}")
    print(f"  {C.DIM}{'-' * 45}{C.RESET}")
    for num, label in items:
        print(f"  {C.GREEN}{num:>3}{C.RESET}  {label}")
    print(f"  {C.DIM}{'-' * 45}{C.RESET}")
    return input(f"\n  {C.YELLOW}> {t('choose')}: {C.RESET}").strip()


def menu_advanced() -> str:
    items = [
        ("",   f"{C.BOLD}REPOS{C.RESET}"),
        ("1",  t("a_list")),
        ("2",  t("a_search")),
        ("3",  t("a_details")),
        ("4",  t("a_create")),
        ("5",  t("a_delete")),
        ("6",  t("a_edit")),
        ("7",  t("a_clone")),
        ("",   f"{C.BOLD}GIT INFO{C.RESET}"),
        ("8",  t("a_commits")),
        ("9",  t("a_branches")),
        ("",   f"{C.BOLD}POWER TOOLS{C.RESET}"),
        ("10", "Backup manager"),
        ("11", "Repo health dashboard"),
        ("12", "Bulk operations"),
        ("",   f"{C.BOLD}GIT DEEP{C.RESET}"),
        ("13", "Interactive git log"),
        ("14", "Cross-repo search"),
        ("",   f"{C.BOLD}DEVOPS{C.RESET}"),
        ("15", "GitHub Actions monitor"),
        ("16", "Release manager"),
        ("",   f"{C.BOLD}TOOLKIT{C.RESET}"),
        ("17", "Repo templates"),
        ("18", "SSH key manager"),
        ("19", "Timestamp editor"),
        ("",   f"{C.BOLD}INSIGHTS{C.RESET}"),
        ("20", "Analytics & traffic"),
        ("21", "Dependency scanner"),
        ("",   f"{C.BOLD}AI / SUMMARY{C.RESET}"),
        ("22", "AI summaries & diff story"),
        ("",   f"{C.BOLD}SENTINEL{C.RESET}"),
        ("23", "Danger zone (security)"),
        ("24", "Git archaeology"),
        ("25", "Smart repo grouper"),
        ("",   f"{C.BOLD}RHYTHM{C.RESET}"),
        ("26", "Commit rhythm analyzer"),
        ("27", "Multi-account manager"),
        ("",   ""),
        ("", f"{C.BOLD}LOCAL GIT{C.RESET}"),
        ("28", "Git Operations (41 tools)"),
        ("",   ""),
        ("29", t("a_stats")),
        ("30", t("a_settings")),
        ("0",  t("exit")),
    ]
    print(f"  {C.BOLD}MENU{C.RESET}")
    print(f"  {C.DIM}{'-' * 45}{C.RESET}")
    for num, label in items:
        if not num and not label:
            continue
        if not num:
            print(f"\n  {label}")
            continue
        print(f"  {C.GREEN}{num:>3}{C.RESET}  {label}")
    print(f"  {C.DIM}{'-' * 45}{C.RESET}")
    return input(f"\n  {C.YELLOW}> {t('choose')}: {C.RESET}").strip()


def menu(mode: str) -> str:
    if mode == "beginner":
        return menu_beginner()
    return menu_advanced()


def pause():
    input(f"\n  {C.DIM}{t('press_enter')}{C.RESET}")


def first_run() -> tuple[str, str]:
    """First-run wizard. Returns (mode, language)."""
    clear()
    print(f"\n  {C.BOLD}{t('bismillah')}{C.RESET}\n")
    print(f"  {C.BOLD}{C.CYAN}{t('welcome')}{C.RESET}\n")

    print(f"  {C.GREEN}1{C.RESET}  English")
    print(f"  {C.GREEN}2{C.RESET}  Fran\u00e7ais")
    print(f"  {C.GREEN}3{C.RESET}  \u0627\u0644\u0639\u0631\u0628\u064a\u0629")
    lang_choice = input(f"\n  {C.YELLOW}> Language [1]: {C.RESET}").strip() or "1"
    lang_map = {"1": "en", "2": "fr", "3": "ar"}
    language = lang_map.get(lang_choice, "en")

    print(f"\n  {C.BOLD}{t('mode_prompt')}{C.RESET}\n")
    print(f"  {C.GREEN}1{C.RESET}  \U0001f423 {t('beginner')} \u2014 {t('beginner_desc')}")
    print(f"  {C.GREEN}2{C.RESET}  \U0001f525 {t('advanced')} \u2014 {t('advanced_desc')}")
    print(f"\n  {C.DIM}{t('switch_anytime')}{C.RESET}")
    mode_choice = input(f"\n  {C.YELLOW}> [1]: {C.RESET}").strip() or "1"
    mode = "beginner" if mode_choice != "2" else "advanced"

    return mode, language


# ─── Formatters ───────────────────────────────────────────────

def format_date(iso_str: str) -> str:
    if not iso_str:
        return "N/A"
    try:
        dt = datetime.strptime(iso_str, "%Y-%m-%dT%H:%M:%SZ")
        return dt.strftime("%Y-%m-%d %H:%M")
    except ValueError:
        return iso_str


def format_size(kb: int) -> str:
    if kb < 1024:
        return f"{kb} KB"
    return f"{kb / 1024:.1f} MB"


def visibility_badge(private: bool) -> str:
    if private:
        return f"{C.RED}private{C.RESET}"
    return f"{C.GREEN}public{C.RESET}"


# ─── Repo Picker ─────────────────────────────────────────────

_repo_cache = {"repos": [], "ts": 0}

def pick_repo(gh, prompt="Select repo") -> str:
    """Show numbered repo list + accept number or typed name. Returns name or ''."""
    import time
    # Cache repos for 60s to avoid re-fetching every time
    now = time.time()
    if not _repo_cache["repos"] or now - _repo_cache["ts"] > 60:
        print(f"\n  {C.DIM}Loading your repos...{C.RESET}")
        _repo_cache["repos"] = gh.list_repos(sort="updated", direction="desc") or []
        _repo_cache["ts"] = now

    repos = _repo_cache["repos"]
    if not repos:
        print(f"\n  {C.RED}No repos found. Check your token or create one first.{C.RESET}")
        return ""

    print(f"\n  {C.BOLD}{prompt}:{C.RESET}\n")
    for i, r in enumerate(repos, 1):
        vis = f"{C.RED}prv{C.RESET}" if r["private"] else f"{C.GREEN}pub{C.RESET}"
        lang = r.get("language") or ""
        print(f"  {C.DIM}{i:>3}{C.RESET}  {C.CYAN}{r['name']:<30}{C.RESET} {vis}  {C.DIM}{lang}{C.RESET}")

    print(f"\n  {C.DIM}Pick a number from the list above{C.RESET}")
    choice = input(f"  {C.YELLOW}> {C.RESET}").strip()
    if not choice:
        return ""
    if choice.isdigit():
        idx = int(choice) - 1
        if 0 <= idx < len(repos):
            return repos[idx]["name"]
        print(f"  {C.RED}Invalid number. Pick 1-{len(repos)}{C.RESET}")
        return ""
    return choice


def clear_repo_cache():
    """Call after create/delete to force refresh."""
    _repo_cache["repos"] = []
    _repo_cache["ts"] = 0
