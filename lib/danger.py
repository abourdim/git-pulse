"""Danger Zone Dashboard — security scanner for repos."""

import re
import requests as req
from .api import GitHubAPI
from .colors import C
from .ui import pick_repo
from .i18n import t

# Patterns for leaked secrets
SECRET_PATTERNS = [
    ("GitHub Token",        r"ghp_[A-Za-z0-9]{36}"),
    ("GitHub OAuth",        r"gho_[A-Za-z0-9]{36}"),
    ("AWS Access Key",      r"AKIA[A-Z0-9]{16}"),
    ("AWS Secret Key",      r"(?i)aws.{0,20}['\"][0-9a-zA-Z/+]{40}['\"]"),
    ("Slack Token",         r"xox[bpors]-[0-9a-zA-Z-]{10,}"),
    ("Slack Webhook",       r"https://hooks\.slack\.com/services/T[A-Z0-9]+/B[A-Z0-9]+/[a-zA-Z0-9]+"),
    ("Private Key",         r"-----BEGIN (?:RSA |DSA |EC )?PRIVATE KEY-----"),
    ("Generic API Key",     r"(?i)(?:api[_-]?key|apikey)\s*[:=]\s*['\"]?[A-Za-z0-9_\-]{20,}"),
    ("Generic Secret",      r"(?i)(?:secret|password|passwd|pwd)\s*[:=]\s*['\"]?[^\s'\"]{8,}"),
    ("Heroku API Key",      r"[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}"),
    ("Sendgrid Key",        r"SG\.[A-Za-z0-9_\-]{22}\.[A-Za-z0-9_\-]{43}"),
    ("Twilio Key",          r"SK[0-9a-fA-F]{32}"),
    ("Google API Key",      r"AIza[0-9A-Za-z_\-]{35}"),
    ("Stripe Key",          r"(?:sk|pk)_(?:test|live)_[0-9a-zA-Z]{24,}"),
]


def scan_repo_secrets(gh: GitHubAPI, name: str, max_files: int = 50) -> list:
    """Scan repo content for leaked secrets. Returns list of findings."""
    if getattr(gh, 'is_demo', False):
        # Mock data for demo mode
        import random
        random.seed(hash(name))
        if random.random() < 0.3:
            return [{"file": "config/settings.py", "type": "Generic Secret", "count": 1, "preview": "password=s3cr3t..."},
                    {"file": ".env.example", "type": "Generic API Key", "count": 1, "preview": "api_key=DEMO_K..."}]
        return []
    findings = []
    # Get file tree
    r = req.get(f"{gh.BASE_URL}/repos/{gh.username}/{name}/git/trees/HEAD?recursive=1",
                headers=gh.headers, timeout=10)
    if r.status_code != 200:
        return findings
    tree = r.json().get("tree", [])

    scannable = [f for f in tree if f.get("type") == "blob"
                 and f.get("size", 0) < 100_000
                 and not any(f["path"].endswith(ext) for ext in
                            (".png", ".jpg", ".gif", ".ico", ".woff", ".ttf",
                             ".zip", ".tar", ".gz", ".bin", ".exe", ".pdf",
                             ".svg", ".mp3", ".mp4", ".webp"))][:max_files]

    for f in scannable:
        r2 = req.get(f"{gh.BASE_URL}/repos/{gh.username}/{name}/contents/{f['path']}",
                     headers={**gh.headers, "Accept": "application/vnd.github.v3.raw"},
                     timeout=5)
        if r2.status_code != 200:
            continue
        content = r2.text
        for label, pattern in SECRET_PATTERNS:
            matches = re.findall(pattern, content)
            if matches:
                findings.append({
                    "file": f["path"],
                    "type": label,
                    "count": len(matches),
                    "preview": matches[0][:20] + "..." if len(matches[0]) > 20 else matches[0],
                })
    return findings


def scan_repo_risks(gh: GitHubAPI, name: str) -> dict:
    """Check various risk indicators for a repo."""
    if getattr(gh, 'is_demo', False):
        repo = gh.get_repo(name)
        return {
            "no_gitignore": True,
            "public_no_license": not (repo or {}).get("private", False) and not (repo or {}).get("license"),
            "large_repo": (repo or {}).get("size", 0) > 500_000,
            "no_description": not (repo or {}).get("description"),
            "unprotected_default": True,
        }
    risks = {}
    repo = gh.get_repo(name)
    if not repo:
        return risks

    # No .gitignore
    r = req.get(f"{gh.BASE_URL}/repos/{gh.username}/{name}/contents/.gitignore",
                headers=gh.headers, timeout=3)
    risks["no_gitignore"] = r.status_code != 200

    # Public with no license
    if not repo.get("private"):
        r2 = req.get(f"{gh.BASE_URL}/repos/{gh.username}/{name}/contents/LICENSE",
                     headers=gh.headers, timeout=3)
        risks["public_no_license"] = r2.status_code != 200

    # Large repo (>500MB)
    risks["large_repo"] = repo.get("size", 0) > 500_000

    # No description
    risks["no_description"] = not repo.get("description")

    # Default branch not protected
    branch = repo.get("default_branch", "main")
    r3 = req.get(f"{gh.BASE_URL}/repos/{gh.username}/{name}/branches/{branch}/protection",
                 headers=gh.headers, timeout=3)
    risks["unprotected_default"] = r3.status_code != 200

    return risks


def danger_menu(gh: GitHubAPI):
    """CLI menu for danger zone scanning."""
    print(f"\n  {C.RED}{C.BOLD}=== DANGER ZONE ==={C.RESET}\n")
    print(f"  {C.GREEN}1{C.RESET}  Scan a repo for leaked secrets")
    print(f"  {C.GREEN}2{C.RESET}  Scan a repo for risk indicators")
    print(f"  {C.GREEN}3{C.RESET}  Scan ALL repos (quick risk check)")
    print(f"  {C.GREEN}0{C.RESET}  {t('back')}")

    choice = input(f"\n  {C.YELLOW}> {t('choose')}: {C.RESET}").strip()

    if choice == "1":
        name = pick_repo(gh)
        if not name:
            return
        print(f"\n  {C.DIM}Scanning {name} for secrets (may take a moment)...{C.RESET}")
        findings = scan_repo_secrets(gh, name)
        if not findings:
            print(f"\n  {C.GREEN}+ No leaked secrets found!{C.RESET}")
        else:
            print(f"\n  {C.RED}{C.BOLD}! Found {len(findings)} potential secrets:{C.RESET}\n")
            for f in findings:
                print(f"    {C.RED}!{C.RESET} {f['file']}: {C.YELLOW}{f['type']}{C.RESET} ({f['count']}x) — {C.DIM}{f['preview']}{C.RESET}")

    elif choice == "2":
        name = pick_repo(gh)
        if not name:
            return
        print(f"\n  {C.DIM}Checking {name}...{C.RESET}")
        risks = scan_repo_risks(gh, name)
        print(f"\n  {C.BOLD}Risk Report for {name}:{C.RESET}\n")
        labels = {
            "no_gitignore": "Missing .gitignore",
            "public_no_license": "Public repo without LICENSE",
            "large_repo": "Repo > 500MB",
            "no_description": "No description set",
            "unprotected_default": "Default branch not protected",
        }
        for key, label in labels.items():
            if key in risks:
                icon = f"{C.RED}!" if risks[key] else f"{C.GREEN}✓"
                status = "RISK" if risks[key] else "OK"
                print(f"    {icon}{C.RESET}  {label}: {status}")

    elif choice == "3":
        print(f"\n  {C.DIM}{t('fetching')}{C.RESET}")
        repos = gh.list_repos(repo_type="owner")
        print(f"\n  {C.BOLD}Quick risk scan — {len(repos)} repos:{C.RESET}\n")
        for repo in repos:
            score = 0
            issues = []
            if not repo.get("description"):
                issues.append("no desc")
                score += 1
            if repo.get("size", 0) > 500_000:
                issues.append(">500MB")
                score += 1
            if not repo.get("private") and not repo.get("license"):
                issues.append("public+no license")
                score += 1
            icon = f"{C.GREEN}✓{C.RESET}" if score == 0 else f"{C.RED}!{C.RESET}"
            detail = f" — {', '.join(issues)}" if issues else ""
            print(f"    {icon} {C.CYAN}{repo['name']}{C.RESET}{detail}")
