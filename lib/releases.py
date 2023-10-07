"""Release manager — create tags, releases, upload assets."""

import os
import requests as req
from .api import GitHubAPI
from .colors import C
from .ui import pick_repo
from .i18n import t
from .ui import format_date


def releases_menu(gh: GitHubAPI):
    while True:
        print(f"""
  {C.BOLD}{'=' * 50}{C.RESET}
  {C.BOLD}{C.CYAN}RELEASE MANAGER{C.RESET}
  {C.BOLD}{'=' * 50}{C.RESET}

  {C.GREEN}1{C.RESET}  List releases for a repo
  {C.GREEN}2{C.RESET}  Create new release
  {C.GREEN}3{C.RESET}  Upload asset to release
  {C.GREEN}4{C.RESET}  Delete a release
  {C.GREEN}0{C.RESET}  {t('back')}
""")
        choice = input(f"  {C.YELLOW}> Option: {C.RESET}").strip()
        if choice == "0": break
        elif choice == "1": _list_releases(gh)
        elif choice == "2": _create_release(gh)
        elif choice == "3": _upload_asset(gh)
        elif choice == "4": _delete_release(gh)
        if choice in ("1","2","3","4"):
            input(f"\n  {C.DIM}{t('press_enter')}{C.RESET}")


def _list_releases(gh):
    name = pick_repo(gh)
    if not name: return
    r = req.get(f"{gh.BASE_URL}/repos/{gh.username}/{name}/releases",
                headers=gh.headers, params={"per_page": 15})
    if r.status_code != 200:
        print(f"  {C.RED}x Failed.{C.RESET}"); return
    rels = r.json()
    if not rels:
        print(f"  {C.YELLOW}No releases.{C.RESET}"); return

    print(f"\n  {C.BOLD}Releases for {name}:{C.RESET}\n")
    for rel in rels:
        tag = rel.get("tag_name", "?")
        title = rel.get("name", "")[:40]
        draft = f" {C.YELLOW}[draft]{C.RESET}" if rel.get("draft") else ""
        pre = f" {C.YELLOW}[pre-release]{C.RESET}" if rel.get("prerelease") else ""
        date = format_date(rel.get("published_at") or rel.get("created_at", ""))
        assets = len(rel.get("assets", []))
        print(f"  {C.GREEN}{tag:<15}{C.RESET} {title:<40} {date} {assets} assets{draft}{pre}")
        print(f"    {C.DIM}ID: {rel['id']}{C.RESET}")


def _create_release(gh):
    name = pick_repo(gh)
    if not name: return
    tag = input(f"  {C.YELLOW}> Tag (e.g. v1.0.0): {C.RESET}").strip()
    if not tag: return
    title = input(f"  {C.YELLOW}> Title [{tag}]: {C.RESET}").strip() or tag
    body = input(f"  {C.YELLOW}> Description: {C.RESET}").strip()
    draft = input(f"  {C.YELLOW}> Draft? [y/N]: {C.RESET}").strip().lower() == "y"
    pre = input(f"  {C.YELLOW}> Pre-release? [y/N]: {C.RESET}").strip().lower() == "y"

    # Auto-generate changelog
    gen = input(f"  {C.YELLOW}> Auto-generate changelog from commits? [Y/n]: {C.RESET}").strip().lower()
    if gen != "n" and not body:
        body = _generate_changelog(gh, name, tag)

    print(f"  {C.DIM}Creating release...{C.RESET}")
    r = req.post(f"{gh.BASE_URL}/repos/{gh.username}/{name}/releases",
                 headers=gh.headers,
                 json={"tag_name": tag, "name": title, "body": body,
                        "draft": draft, "prerelease": pre})
    if r.status_code == 201:
        print(f"  {C.GREEN}+ Release {tag} created!{C.RESET}")
        print(f"  {C.DIM}URL: {r.json()['html_url']}{C.RESET}")
    else:
        print(f"  {C.RED}x Failed: {r.json().get('message', r.status_code)}{C.RESET}")


def _generate_changelog(gh, name, tag):
    r = req.get(f"{gh.BASE_URL}/repos/{gh.username}/{name}/commits",
                headers=gh.headers, params={"per_page": 20})
    if r.status_code != 200:
        return ""
    commits = r.json()
    lines = [f"## What's Changed\n"]
    for c in commits[:15]:
        msg = c["commit"]["message"].split("\n")[0]
        sha = c["sha"][:7]
        lines.append(f"- {msg} ({sha})")
    return "\n".join(lines)


def _upload_asset(gh):
    name = pick_repo(gh)
    if not name: return
    rel_id = input(f"  {C.YELLOW}> Release ID: {C.RESET}").strip()
    if not rel_id: return
    filepath = input(f"  {C.YELLOW}> File path: {C.RESET}").strip()
    if not filepath or not os.path.isfile(filepath): 
        print(f"  {C.RED}x File not found.{C.RESET}"); return

    filename = os.path.basename(filepath)
    size = os.path.getsize(filepath)
    print(f"  {C.DIM}Uploading {filename} ({size/1024:.1f} KB)...{C.RESET}")

    upload_url = f"https://uploads.github.com/repos/{gh.username}/{name}/releases/{rel_id}/assets"
    headers = {**gh.headers, "Content-Type": "application/octet-stream"}
    with open(filepath, "rb") as f:
        r = req.post(upload_url, headers=headers, params={"name": filename}, data=f)
    if r.status_code == 201:
        print(f"  {C.GREEN}+ Uploaded {filename}{C.RESET}")
        print(f"  {C.DIM}URL: {r.json()['browser_download_url']}{C.RESET}")
    else:
        print(f"  {C.RED}x Failed ({r.status_code}).{C.RESET}")


def _delete_release(gh):
    name = pick_repo(gh)
    if not name: return
    rel_id = input(f"  {C.YELLOW}> Release ID: {C.RESET}").strip()
    if not rel_id: return
    confirm = input(f"  {C.RED}> Delete release {rel_id}? [y/N]: {C.RESET}").strip().lower()
    if confirm != "y": return
    r = req.delete(f"{gh.BASE_URL}/repos/{gh.username}/{name}/releases/{rel_id}", headers=gh.headers)
    print(f"  {C.GREEN}+ Deleted.{C.RESET}" if r.status_code == 204 else f"  {C.RED}x Failed.{C.RESET}")
