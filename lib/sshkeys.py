"""SSH key manager — generate, upload, test, manage."""

import subprocess
import os
from pathlib import Path
import requests as req
from .api import GitHubAPI
from .colors import C
from .i18n import t


def ssh_menu(gh: GitHubAPI):
    while True:
        print(f"""
  {C.BOLD}{'=' * 50}{C.RESET}
  {C.BOLD}{C.CYAN}SSH KEY MANAGER{C.RESET}
  {C.BOLD}{'=' * 50}{C.RESET}

  {C.GREEN}1{C.RESET}  List SSH keys on GitHub
  {C.GREEN}2{C.RESET}  Generate new SSH key
  {C.GREEN}3{C.RESET}  Upload key to GitHub
  {C.GREEN}4{C.RESET}  Test SSH connection
  {C.GREEN}5{C.RESET}  Remove key from GitHub
  {C.GREEN}0{C.RESET}  {t('back')}
""")
        choice = input(f"  {C.YELLOW}> Option: {C.RESET}").strip()
        if choice == "0": break
        elif choice == "1": _list_keys(gh)
        elif choice == "2": _generate_key()
        elif choice == "3": _upload_key(gh)
        elif choice == "4": _test_connection()
        elif choice == "5": _remove_key(gh)
        if choice in ("1","2","3","4","5"):
            input(f"\n  {C.DIM}{t('press_enter')}{C.RESET}")


def _list_keys(gh):
    r = req.get(f"{gh.BASE_URL}/user/keys", headers=gh.headers)
    if r.status_code != 200:
        print(f"  {C.RED}x Failed.{C.RESET}"); return
    keys = r.json()
    if not keys:
        print(f"  {C.YELLOW}No SSH keys.{C.RESET}"); return
    print(f"\n  {C.BOLD}SSH keys on GitHub:{C.RESET}\n")
    for k in keys:
        fingerprint = k["key"][-20:]
        print(f"  {C.GREEN}ID:{k['id']}{C.RESET}  {k['title']:<30}  ...{fingerprint}")


def _generate_key():
    ssh_dir = Path.home() / ".ssh"
    ssh_dir.mkdir(exist_ok=True)
    algo = input(f"  {C.YELLOW}> Type (ed25519/rsa) [ed25519]: {C.RESET}").strip() or "ed25519"
    name = input(f"  {C.YELLOW}> Filename [id_{algo}_github]: {C.RESET}").strip() or f"id_{algo}_github"
    email = input(f"  {C.YELLOW}> Email: {C.RESET}").strip()
    filepath = ssh_dir / name
    if filepath.exists():
        print(f"  {C.YELLOW}Key already exists: {filepath}{C.RESET}"); return
    cmd = ["ssh-keygen", "-t", algo, "-f", str(filepath), "-C", email or "", "-N", ""]
    r = subprocess.run(cmd, capture_output=True, text=True)
    if r.returncode == 0:
        print(f"  {C.GREEN}+ Generated: {filepath}{C.RESET}")
        print(f"  {C.GREEN}+ Public:    {filepath}.pub{C.RESET}")
    else:
        print(f"  {C.RED}x Failed: {r.stderr}{C.RESET}")


def _upload_key(gh):
    ssh_dir = Path.home() / ".ssh"
    pubs = sorted(ssh_dir.glob("*.pub"))
    if not pubs:
        print(f"  {C.YELLOW}No .pub files found in {ssh_dir}{C.RESET}"); return
    print(f"\n  {C.BOLD}Available public keys:{C.RESET}")
    for i, p in enumerate(pubs, 1):
        print(f"  {C.GREEN}{i}{C.RESET}  {p.name}")
    choice = input(f"  {C.YELLOW}> Key to upload: {C.RESET}").strip()
    if not choice.isdigit() or not (1 <= int(choice) <= len(pubs)):
        return
    pubfile = pubs[int(choice) - 1]
    key_content = pubfile.read_text().strip()
    title = input(f"  {C.YELLOW}> Title [{pubfile.stem}]: {C.RESET}").strip() or pubfile.stem
    r = req.post(f"{gh.BASE_URL}/user/keys", headers=gh.headers,
                 json={"title": title, "key": key_content})
    if r.status_code == 201:
        print(f"  {C.GREEN}+ Uploaded '{title}' to GitHub{C.RESET}")
    else:
        print(f"  {C.RED}x Failed: {r.json().get('message', r.status_code)}{C.RESET}")


def _test_connection():
    print(f"  {C.DIM}Testing ssh -T git@github.com ...{C.RESET}")
    r = subprocess.run(["ssh", "-T", "git@github.com"], capture_output=True, text=True)
    output = r.stderr or r.stdout
    if "successfully authenticated" in output.lower():
        print(f"  {C.GREEN}+ {output.strip()}{C.RESET}")
    else:
        print(f"  {C.YELLOW}{output.strip()}{C.RESET}")


def _remove_key(gh):
    key_id = input(f"\n  {C.YELLOW}> Key ID to remove: {C.RESET}").strip()
    if not key_id: return
    confirm = input(f"  {C.RED}> Remove key {key_id}? [y/N]: {C.RESET}").strip().lower()
    if confirm != "y": return
    r = req.delete(f"{gh.BASE_URL}/user/keys/{key_id}", headers=gh.headers)
    print(f"  {C.GREEN}+ Removed.{C.RESET}" if r.status_code == 204 else f"  {C.RED}x Failed.{C.RESET}")
