"""Web routes — pages and API endpoints for all features."""

import json
import re
import hashlib
import requests as req_lib
from datetime import datetime
from ..server import router, get_gh, get_config
from ..templating import render
from lib.config import VERSION, CODENAME


def _ctx(**extra):
    gh = get_gh()
    config = get_config()
    lang = config.get("language", "en")
    base = {
        "version": VERSION, "codename": CODENAME,
        "username": config.get("display_name") or (gh.username if gh else ""),
        "theme": config.get("web_theme", "masjid"),
        "language": lang,
        "dir": "rtl" if lang == "ar" else "ltr",
        "mode": config.get("mode", "advanced"),
        "page_title": "GitPulse",
        "is_demo": getattr(gh, 'is_demo', False),
    }
    base.update(extra)
    return base


# ─── PAGE ROUTES ──────────────────────────────────────────────

@router.get("/")
def index(**kw):
    gh = get_gh()
    repos = gh.list_repos() if gh else []
    total = len(repos)
    public = sum(1 for r in repos if not r.get("private"))
    private = total - public
    stars = sum(r.get("stargazers_count", 0) for r in repos)
    langs = {}
    for r in repos:
        l = r.get("language")
        if l: langs[l] = langs.get(l, 0) + 1
    top_langs = sorted(langs.items(), key=lambda x: x[1], reverse=True)[:5]
    recent = repos[:5]
    return render("dashboard.html", **_ctx(page_title="Dashboard",
        repos=repos, total=total, public=public, private=private,
        stars=stars, top_langs=top_langs, recent=recent,
    ))


@router.get("/repos")
def repos_page(**kw):
    gh = get_gh()
    repos = gh.list_repos() if gh else []
    for r in repos:
        r["pages_status"] = "Active" if r.get("has_pages") else "Off"
        r["visibility"] = "private" if r.get("private") else "public"
        owner = r.get("owner", {}).get("login", "")
        r["pages_url"] = f"https://{owner}.github.io/{r['name']}" if r.get("has_pages") and owner else ""
        r["pages_display"] = "inline" if r.get("has_pages") else "none"
    return render("repos.html", **_ctx(page_title="Repos",repos=repos, total=len(repos)))


@router.get("/repo/<n>")
def repo_detail(n="", **kw):
    gh = get_gh()
    repo = gh.get_repo(n) if gh else None
    if not repo:
        return render("404.html", **_ctx())
    langs = gh.get_languages(n) if gh else {}
    commits = gh.list_commits(n, 10) if gh else []
    branches = gh.list_branches(n) if gh else []
    total_bytes = sum(langs.values()) or 1
    lang_pcts = [(l, b / total_bytes * 100) for l, b in sorted(langs.items(), key=lambda x: x[1], reverse=True)]
    has_pages = repo.get("has_pages", False)
    pages_url = ""
    if has_pages and hasattr(gh, 'get_pages'):
        pages_info = gh.get_pages(n)
        if pages_info:
            pages_url = pages_info.get("html_url", "")
    return render("repo_detail.html", **_ctx(page_title="Repo Details",
        repo=repo, langs=lang_pcts, commits=commits, branches=branches,
        is_private=repo.get("private", False),
        is_archived=repo.get("archived", False),
        has_wiki=repo.get("has_wiki", True),
        has_issues=repo.get("has_issues", True),
        has_pages=has_pages,
        pages_url=pages_url,
        repo_topics=", ".join(repo.get("topics", [])),
    ))


@router.get("/repo/<n>/files")
def repo_files(n="", **kw):
    gh = get_gh()
    repo = gh.get_repo(n) if gh else None
    if not repo:
        return render("404.html", **_ctx())
    return render("files.html", **_ctx(page_title=f"Files — {n}", repo=repo, repo_name=n))


@router.get("/settings")
def settings_page(**kw):
    config = get_config()
    from lib.accounts import list_accounts
    accounts = list_accounts()
    return render("settings.html", **_ctx(page_title="Settings", config=config,
                  accounts=accounts, accounts_json=json.dumps(accounts)))


@router.get("/health")
def health_page(**kw):
    return render("health.html", **_ctx(page_title="Health"))


@router.get("/backup")
def backup_page(**kw):
    return render("backup.html", **_ctx(page_title="Backup"))


@router.get("/danger")
def danger_page(**kw):
    return render("danger.html", **_ctx(page_title="Security"))


@router.get("/archaeology")
def archaeology_page(**kw):
    return render("archaeology.html", **_ctx(page_title="Archaeology"))


@router.get("/grouper")
def grouper_page(**kw):
    return render("grouper.html", **_ctx(page_title="Grouper"))


@router.get("/rhythm")
def rhythm_page(**kw):
    return render("rhythm.html", **_ctx(page_title="Rhythm"))


@router.get("/analytics")
def analytics_page(**kw):
    return render("analytics.html", **_ctx(page_title="Analytics"))


@router.get("/timemachine/<n>")
def timemachine_page(n="", **kw):
    return render("timemachine.html", **_ctx(repo_name=n))


@router.get("/dna")
def dna_page(**kw):
    return render("dna.html", **_ctx(page_title="DNA"))


@router.get("/graph")
def graph_page(**kw):
    return render("graph.html", **_ctx(page_title="Graph"))


@router.get("/radar")
def radar_page(**kw):
    return render("radar.html", **_ctx(page_title="Radar"))


@router.get("/ambient")
def ambient_page(**kw):
    return render("ambient.html", **_ctx(page_title="Ambient"))


@router.get("/voice")
def voice_page(**kw):
    return render("voice.html", **_ctx(page_title="Voice"))


# ─── API ENDPOINTS ────────────────────────────────────────────

@router.get("/api/repos")
def api_repos(**kw):
    gh = get_gh()
    repos = gh.list_repos() if gh else []
    return {"repos": [{
        "name": r["name"], "private": r["private"],
        "description": r.get("description", ""),
        "language": r.get("language", ""),
        "stars": r.get("stargazers_count", 0),
        "updated": r.get("updated_at", ""),
        "url": r.get("html_url", ""),
        "size": r.get("size", 0),
        "topics": r.get("topics", []),
    } for r in repos]}


@router.get("/api/repo/<n>")
def api_repo(n="", **kw):
    gh = get_gh()
    repo = gh.get_repo(n) if gh else None
    if not repo:
        return {"error": "Not found"}
    return {"repo": repo}


@router.get("/api/repo/<n>/commits")
def api_commits(n="", **kw):
    gh = get_gh()
    commits = gh.list_commits(n, 50) if gh else []
    return {"commits": [{
        "sha": c["sha"][:7],
        "message": c["commit"]["message"].split("\n")[0],
        "author": c["commit"]["author"]["name"],
        "date": c["commit"]["author"]["date"],
    } for c in commits]}


@router.get("/api/repo/<n>/tree")
def api_tree(n="", **kw):
    gh = get_gh()
    if getattr(gh, 'is_demo', False):
        return {"tree": gh.get_tree(n)}
    r = req_lib.get(f"{gh.BASE_URL}/repos/{gh.username}/{n}/git/trees/HEAD?recursive=1",
                    headers=gh.headers, timeout=10)
    if r.status_code != 200:
        return {"tree": []}
    tree = r.json().get("tree", [])
    return {"tree": [{"path": f["path"], "type": f["type"], "size": f.get("size", 0)} for f in tree]}


@router.get("/api/health")
def api_health(**kw):
    gh = get_gh()
    repos = gh.list_repos(repo_type="owner") if gh else []
    results = []
    for repo in repos[:30]:
        if getattr(gh, 'is_demo', False):
            checks = gh.get_health_checks(repo["name"])
        else:
            checks = {"description": bool(repo.get("description")), "topics": bool(repo.get("topics"))}
            for fname in ("README.md", "LICENSE", ".gitignore"):
                r = req_lib.get(f"{gh.BASE_URL}/repos/{repo['full_name']}/contents/{fname}",
                                headers=gh.headers, timeout=3)
                checks[fname] = r.status_code == 200
        score = sum(checks.values()) / max(len(checks), 1) * 100
        results.append({"name": repo["name"], "checks": checks, "score": round(score)})
    return {"repos": results}


@router.get("/api/danger/<n>")
def api_danger(n="", **kw):
    gh = get_gh()
    if getattr(gh, 'is_demo', False):
        # Mock danger scan
        secrets = []
        if n == "old-website":
            secrets = [{"file": "config.js", "type": "Generic API Key", "count": 1, "preview": "api_key=DEMO12345..."}]
        risks = {
            "no_gitignore": n == "notes-archive",
            "public_no_license": n in ("pcb-library",),
            "no_description": n == "notes-archive",
            "unprotected_default": True,
        }
        return {"secrets": secrets, "risks": risks}
    from lib.danger import scan_repo_secrets, scan_repo_risks
    secrets = scan_repo_secrets(gh, n, max_files=30)
    risks = scan_repo_risks(gh, n)
    return {"secrets": secrets, "risks": risks}


@router.get("/api/archaeology/<n>")
def api_archaeology(n="", **kw):
    gh = get_gh()
    if getattr(gh, 'is_demo', False):
        dead = [{"name": "feature/old-ui", "last_commit": "2024-08-15T10:00:00Z", "age_days": 560}] if n != "dotfiles" else []
        large = [{"path": "data/model.h5", "size_kb": 24000}] if n == "ml-plant-disease" else []
        todos = [{"file": "src/main.cpp", "keyword": "TODO", "name": "main.cpp"}] if n == "smart-garden-iot" else []
        return {"dead_branches": dead, "large_files": large, "todos": todos}
    from lib.archaeology import find_dead_branches, find_large_files, find_todos
    return {
        "dead_branches": find_dead_branches(gh, n, 180),
        "large_files": find_large_files(gh, n),
        "todos": find_todos(gh, n),
    }


@router.get("/api/grouper")
def api_grouper(**kw):
    from lib.grouper import group_repos
    gh = get_gh()
    groups = group_repos(gh)
    result = {}
    for cat, repos in groups.items():
        result[cat] = [{"name": r["name"], "language": r.get("language", ""),
                        "private": r["private"]} for r in repos]
    return {"groups": result}


@router.get("/api/rhythm")
def api_rhythm(**kw):
    from lib.rhythm import fetch_all_commits, analyze_rhythm
    gh = get_gh()
    commits = fetch_all_commits(gh)
    if not commits:
        return {"error": "No commits found"}
    return analyze_rhythm(commits)


@router.get("/api/dna/<n>")
def api_dna(n="", **kw):
    """Generate DNA fingerprint data for a repo."""
    gh = get_gh()
    repo = gh.get_repo(n) if gh else None
    if not repo:
        return {"error": "Not found"}
    langs = gh.get_languages(n) if gh else {}
    commits = gh.list_commits(n, 30) if gh else []

    # Create deterministic fingerprint from repo characteristics
    seed = hashlib.md5(f"{n}{repo.get('created_at', '')}".encode()).hexdigest()
    total_bytes = sum(langs.values()) or 1
    lang_pcts = {l: b / total_bytes for l, b in langs.items()}

    # Hour distribution from commits
    hour_dist = [0] * 24
    for c in commits:
        try:
            dt = datetime.strptime(c["commit"]["author"]["date"], "%Y-%m-%dT%H:%M:%SZ")
            hour_dist[dt.hour] += 1
        except (ValueError, KeyError):
            pass

    return {
        "name": n,
        "seed": seed,
        "languages": lang_pcts,
        "hour_distribution": hour_dist,
        "stars": repo.get("stargazers_count", 0),
        "size": repo.get("size", 0),
        "commits_count": len(commits),
        "forks": repo.get("forks_count", 0),
    }


@router.get("/api/graph")
def api_graph(**kw):
    """Build repo relationship graph data."""
    gh = get_gh()
    repos = gh.list_repos(repo_type="owner") if gh else []
    nodes = []
    links = []
    lang_groups = {}

    for r in repos[:40]:
        lang = r.get("language", "Other") or "Other"
        nodes.append({
            "id": r["name"], "language": lang,
            "stars": r.get("stargazers_count", 0),
            "size": r.get("size", 0),
        })
        lang_groups.setdefault(lang, []).append(r["name"])

    # Link repos with same language
    for lang, names in lang_groups.items():
        for i in range(len(names)):
            for j in range(i + 1, min(i + 3, len(names))):
                links.append({"source": names[i], "target": names[j], "type": "same_language"})

    return {"nodes": nodes, "links": links}


@router.get("/api/radar")
def api_radar(**kw):
    """Get recent GitHub events for the user."""
    gh = get_gh()
    if getattr(gh, 'is_demo', False):
        raw = gh.get_events()
        return {"events": [{"type": e["type"], "repo": e["repo"]["name"],
                            "actor": e["actor"]["login"], "created_at": e["created_at"]} for e in raw]}
    r = req_lib.get(f"{gh.BASE_URL}/users/{gh.username}/received_events",
                    headers=gh.headers, params={"per_page": 30}, timeout=10)
    if r.status_code != 200:
        return {"events": []}
    events = []
    for e in r.json():
        events.append({
            "type": e["type"],
            "repo": e.get("repo", {}).get("name", ""),
            "actor": e.get("actor", {}).get("login", ""),
            "created_at": e.get("created_at", ""),
        })
    return {"events": events}


@router.get("/api/analytics/<n>")
def api_analytics(n="", **kw):
    """Get traffic analytics for a repo."""
    gh = get_gh()
    if getattr(gh, 'is_demo', False):
        return gh.get_traffic(n)
    views = req_lib.get(f"{gh.BASE_URL}/repos/{gh.username}/{n}/traffic/views",
                        headers=gh.headers, timeout=5)
    clones = req_lib.get(f"{gh.BASE_URL}/repos/{gh.username}/{n}/traffic/clones",
                         headers=gh.headers, timeout=5)
    referrers = req_lib.get(f"{gh.BASE_URL}/repos/{gh.username}/{n}/traffic/popular/referrers",
                            headers=gh.headers, timeout=5)
    return {
        "views": views.json() if views.status_code == 200 else {},
        "clones": clones.json() if clones.status_code == 200 else {},
        "referrers": referrers.json() if referrers.status_code == 200 else [],
    }


@router.post("/api/repo/create")
def api_create_repo(data=None, **kw):
    gh = get_gh()
    if not data:
        return {"error": "No data"}
    result, status = gh.create_repo(
        data.get("name", ""), data.get("description", ""),
        data.get("private", True), data.get("init", True))
    return {"result": result, "status": status}


@router.post("/api/repo/<n>/delete")
def api_delete_repo(n="", data=None, **kw):
    gh = get_gh()
    status = gh.delete_repo(n)
    return {"status": status, "deleted": status == 204}


@router.post("/api/repo/<n>/visibility")
def api_toggle_visibility(n="", data=None, **kw):
    gh = get_gh()
    if not data or "private" not in data:
        return {"error": "Missing 'private' field"}
    result, status = gh.update_repo(n, private=bool(data["private"]))
    if status == 200:
        return {"ok": True, "private": result.get("private", data["private"])}
    return {"error": result.get("message", "Unknown error"), "status": status}


@router.get("/api/repo/<n>/pages")
def api_get_pages(n="", **kw):
    gh = get_gh()
    pages = gh.get_pages(n) if hasattr(gh, 'get_pages') and gh else None
    if pages:
        return {"enabled": True, "url": pages.get("html_url", ""), "status": pages.get("status", ""),
                "branch": (pages.get("source") or {}).get("branch", ""), "path": (pages.get("source") or {}).get("path", "")}
    return {"enabled": False}


@router.post("/api/repo/<n>/pages")
def api_toggle_pages(n="", data=None, **kw):
    gh = get_gh()
    if not data:
        return {"error": "No data"}
    if data.get("enable"):
        branch = data.get("branch", "main")
        path = data.get("path", "/")
        result, status = gh.enable_pages(n, branch, path)
        if status == 201:
            return {"ok": True, "enabled": True}
        elif status == 409:
            return {"ok": True, "enabled": True, "note": "Already enabled"}
        return {"ok": False, "error": result.get("message", f"Failed ({status})")}
    else:
        status = gh.disable_pages(n)
        if status == 204:
            return {"ok": True, "enabled": False}
        elif status == 404:
            return {"ok": True, "enabled": False, "note": "Pages not enabled"}
        return {"ok": False, "error": f"Failed ({status})"}


@router.post("/api/repo/<n>/squash")
def api_squash_repo(n="", data=None, **kw):
    gh = get_gh()
    msg = (data or {}).get("message", "Initial commit")
    ok, result = gh.squash_all_commits(n, msg)
    if ok:
        return {"ok": True, "sha": result}
    return {"ok": False, "error": result}


@router.post("/api/repo/<n>/edit")
def api_edit_repo(n="", data=None, **kw):
    gh = get_gh()
    if not data:
        return {"error": "No data"}

    # Build updates dict — only include fields that were provided
    updates = {}
    for key in ("name", "description", "homepage", "default_branch"):
        if key in data and data[key] is not None:
            updates[key] = data[key]
    for key in ("private", "has_wiki", "has_issues", "archived"):
        if key in data and data[key] is not None:
            updates[key] = bool(data[key])

    errors = []

    # Topics use a separate GitHub API endpoint
    topics_str = data.get("topics", "")
    if topics_str is not None and isinstance(topics_str, str):
        topics_list = [t.strip().lower().replace(" ", "-") for t in topics_str.split(",") if t.strip()]
        import requests as req
        repo_name = updates.get("name", n)
        url = f"https://api.github.com/repos/{gh.username}/{n}/topics"
        headers = {**gh.headers, "Accept": "application/vnd.github.mercy-preview+json"}
        resp = req.put(url, headers=headers, json={"names": topics_list})
        if resp.status_code != 200:
            errors.append(f"Topics: {resp.json().get('message', 'failed')}")

    if updates:
        repo_name = updates.pop("name", n)
        result, status = gh.update_repo(repo_name, **updates)
        if status != 200:
            errors.append(result.get("message", "Unknown error"))

    if errors:
        return {"ok": False, "error": "; ".join(errors)}
    return {"ok": True}


@router.post("/api/settings")
def api_settings(data=None, **kw):
    from lib.config import save
    config = get_config()
    if data:
        for key in ("web_theme", "language", "mode", "web_port", "display_name"):
            if key in data:
                config[key] = data[key]
        save(config)
    return {"status": "ok", "config": config}


# ─── ACCOUNT MANAGEMENT API ─────────────────────────────────

@router.post("/api/account/switch")
def api_account_switch(data=None, **kw):
    """Switch active GitHub account."""
    from ..server import set_gh
    from lib.accounts import switch_account
    if not data or not data.get("label"):
        return {"ok": False, "error": "No label provided"}
    label = data["label"]
    try:
        new_gh = switch_account(label)
        if new_gh:
            set_gh(new_gh)
            config = get_config()
            dn = config.get("display_name") or new_gh.username
            from lib.colors import C
            print(f"  {C.GREEN}+ Switched to {C.BOLD}{new_gh.username}{C.RESET}")
            return {"ok": True, "username": new_gh.username, "display_name": dn, "label": label}
        return {"ok": False, "error": f"Account '{label}' not found"}
    except Exception as e:
        return {"ok": False, "error": str(e)}


@router.post("/api/account/add")
def api_account_add(data=None, **kw):
    """Add a new GitHub account."""
    from lib.accounts import add_account
    if not data or not data.get("label") or not data.get("token"):
        return {"ok": False, "error": "Label and token required"}
    label = data["label"].strip()
    token = data["token"].strip()
    if not label or not token:
        return {"ok": False, "error": "Label and token required"}
    try:
        ok, username = add_account(label, token)
        if ok:
            from lib.colors import C
            print(f"  {C.GREEN}+ Account added: {C.BOLD}{label} ({username}){C.RESET}")
            return {"ok": True, "username": username, "label": label}
        return {"ok": False, "error": "Invalid token — check scopes (repo, read:user)"}
    except Exception as e:
        return {"ok": False, "error": str(e)}


@router.post("/api/account/delete")
def api_account_delete(data=None, **kw):
    """Remove a saved GitHub account."""
    from lib.accounts import remove_account
    if not data or not data.get("label"):
        return {"ok": False, "error": "No label provided"}
    label = data["label"]
    if remove_account(label):
        return {"ok": True, "removed": label}
    return {"ok": False, "error": f"Account '{label}' not found"}


# ─── FILE WORKSPACE API ──────────────────────────────────────

@router.get("/api/repo/<n>/file/<path>")
def api_get_file(n="", path="", **kw):
    gh = get_gh()
    # Also check query param for nested paths
    query = kw.get("query", {})
    if query.get("path"):
        path = query["path"][0]
    data = gh.get_file_content(n, path) if gh else {}
    return data if data else {"error": "File not found"}


@router.get("/api/repo/<n>/fileget")
def api_get_file_q(n="", **kw):
    """Get file via query param (supports nested paths)."""
    gh = get_gh()
    query = kw.get("query", {})
    path = query.get("path", [""])[0]
    if not path:
        return {"error": "No path specified"}
    data = gh.get_file_content(n, path) if gh else {}
    if not data:
        return {"error": "File not found"}
    # Return only what the client needs (strip GitHub bloat)
    return {
        "content": data.get("content", ""),
        "sha": data.get("sha", ""),
        "size": data.get("size", 0),
        "name": data.get("name", path.split("/")[-1]),
        "encoding": data.get("encoding", "base64"),
    }


@router.post("/api/repo/<n>/file/save")
def api_save_file(n="", data=None, **kw):
    gh = get_gh()
    if not data:
        return {"error": "No data"}
    path = data.get("path", "")
    content = data.get("content", "")
    message = data.get("message", f"Update {path}")
    sha = data.get("sha")
    ok, result = gh.create_or_update_file(n, path, content, message, sha)
    return {"ok": ok, "result": result}


@router.post("/api/repo/<n>/file/create")
def api_create_file(n="", data=None, **kw):
    gh = get_gh()
    if not data:
        return {"error": "No data"}
    path = data.get("path", "")
    content = data.get("content", "")
    message = data.get("message", f"Create {path}")
    ok, result = gh.create_or_update_file(n, path, content, message)
    return {"ok": ok, "result": result}


@router.post("/api/repo/<n>/file/delete")
def api_delete_file(n="", data=None, **kw):
    gh = get_gh()
    if not data:
        return {"error": "No data"}
    path = data.get("path", "")
    sha = data.get("sha", "")
    message = data.get("message", f"Delete {path}")
    ok, result = gh.delete_file(n, path, message, sha)
    return {"ok": ok}


@router.post("/api/repo/<n>/file/upload")
def api_upload_file(n="", data=None, **kw):
    gh = get_gh()
    if not data:
        return {"error": "No data"}
    path = data.get("path", "")
    content_b64 = data.get("content_b64", "")
    message = data.get("message", f"Upload {path}")
    import base64
    try:
        raw = base64.b64decode(content_b64)
        content = raw.decode("utf-8", errors="replace")
    except Exception:
        content = content_b64
    ok, result = gh.create_or_update_file(n, path, content, message)
    return {"ok": ok}


@router.get("/api/repo/<n>/search")
def api_search_files(n="", **kw):
    """Search through repo files for a pattern."""
    gh = get_gh()
    import re as regex_mod
    # Get query from request params
    query = kw.get("query", {})
    q = query.get("q", [""])[0] if isinstance(query.get("q"), list) else query.get("q", "")
    if not q:
        return {"results": [], "error": "No query"}
    tree = gh.get_tree(n) if hasattr(gh, 'get_tree') else []
    if not tree:
        # Try API
        r = req_lib.get(f"{gh.BASE_URL}/repos/{gh.username}/{n}/git/trees/HEAD?recursive=1",
                        headers=gh.headers, timeout=10)
        tree = [{"path": f["path"], "type": f["type"]} for f in r.json().get("tree", [])] if r.status_code == 200 else []
    results = []
    text_exts = {".py", ".js", ".ts", ".cpp", ".c", ".h", ".java", ".rb", ".go", ".rs",
                 ".md", ".txt", ".json", ".yml", ".yaml", ".toml", ".ini", ".cfg",
                 ".html", ".css", ".sh", ".bat", ".xml", ".sql", ".r", ".php"}
    for item in tree:
        if item.get("type") != "blob":
            continue
        ext = "." + item["path"].rsplit(".", 1)[-1] if "." in item["path"] else ""
        if ext.lower() not in text_exts and item["path"] not in ("Makefile", "Dockerfile", "Gemfile"):
            continue
        try:
            data = gh.get_file_content(n, item["path"])
            if not data or "content" not in data:
                continue
            import base64
            content = base64.b64decode(data["content"]).decode("utf-8", errors="replace")
            for i, line in enumerate(content.splitlines(), 1):
                if q.lower() in line.lower():
                    results.append({"path": item["path"], "line": i, "text": line.strip()[:120]})
                    if len(results) >= 50:
                        return {"results": results, "query": q}
        except Exception:
            continue
    return {"results": results, "query": q}


@router.get("/api/repo/<n>/todos")
def api_todos(n="", **kw):
    """Scan for TODO/FIXME/HACK/XXX across all files."""
    gh = get_gh()
    tree = gh.get_tree(n) if hasattr(gh, 'get_tree') else []
    if not tree:
        r = req_lib.get(f"{gh.BASE_URL}/repos/{gh.username}/{n}/git/trees/HEAD?recursive=1",
                        headers=gh.headers, timeout=10)
        tree = [{"path": f["path"], "type": f["type"]} for f in r.json().get("tree", [])] if r.status_code == 200 else []
    todos = []
    keywords = ["TODO", "FIXME", "HACK", "XXX", "BUG", "OPTIMIZE"]
    text_exts = {".py", ".js", ".ts", ".cpp", ".c", ".h", ".java", ".rb", ".go", ".rs", ".md", ".sh", ".php"}
    for item in tree:
        if item.get("type") != "blob":
            continue
        ext = "." + item["path"].rsplit(".", 1)[-1] if "." in item["path"] else ""
        if ext.lower() not in text_exts:
            continue
        try:
            data = gh.get_file_content(n, item["path"])
            if not data or "content" not in data:
                continue
            import base64
            content = base64.b64decode(data["content"]).decode("utf-8", errors="replace")
            for i, line in enumerate(content.splitlines(), 1):
                for kw_str in keywords:
                    if kw_str in line.upper():
                        todos.append({"path": item["path"], "line": i, "keyword": kw_str,
                                      "text": line.strip()[:100]})
                        break
        except Exception:
            continue
    return {"todos": todos}


@router.get("/api/repo/<n>/secrets")
def api_secrets_scan(n="", **kw):
    """Scan files for potential secrets/keys."""
    gh = get_gh()
    tree = gh.get_tree(n) if hasattr(gh, 'get_tree') else []
    if not tree:
        r = req_lib.get(f"{gh.BASE_URL}/repos/{gh.username}/{n}/git/trees/HEAD?recursive=1",
                        headers=gh.headers, timeout=10)
        tree = [{"path": f["path"], "type": f["type"]} for f in r.json().get("tree", [])] if r.status_code == 200 else []
    import re as re2
    secrets = []
    patterns = [
        (r'(?:api[_-]?key|apikey)[\s:=]+["\']?[\w\-]{10,}', "API Key"),
        (r'(?:password|passwd|pwd|PASS)[\s:=]+["\']?.{6,}', "Password"),
        (r'(?:secret|token)[\s:=]+["\']?[\w\-]{10,}', "Secret/Token"),
        (r'(?:aws_access_key_id)[\s:=]+[\w]{16,}', "AWS Key"),
        (r'ghp_[\w]{36}', "GitHub Token"),
        (r'sk-[\w]{32,}', "OpenAI Key"),
        (r'(?:PRIVATE_KEY|private.key)', "Private Key Reference"),
    ]
    for item in tree:
        if item.get("type") != "blob":
            continue
        try:
            data = gh.get_file_content(n, item["path"])
            if not data or "content" not in data:
                continue
            import base64
            content = base64.b64decode(data["content"]).decode("utf-8", errors="replace")
            for line_num, line in enumerate(content.splitlines(), 1):
                for pat, label in patterns:
                    if re2.search(pat, line, re2.IGNORECASE):
                        secrets.append({"path": item["path"], "line": line_num, "type": label,
                                        "preview": line.strip()[:60] + "..."})
                        break
        except Exception:
            continue
    return {"secrets": secrets}


@router.post("/api/repo/<n>/generate-readme")
def api_generate_readme(n="", data=None, **kw):
    """Auto-generate README.md from repo analysis."""
    gh = get_gh()
    repo = gh.get_repo(n) if gh else None
    if not repo:
        return {"error": "Repo not found"}
    langs = gh.get_languages(n) if gh else {}
    tree = gh.get_tree(n) if hasattr(gh, 'get_tree') else []
    if not tree:
        r = req_lib.get(f"{gh.BASE_URL}/repos/{gh.username}/{n}/git/trees/HEAD?recursive=1",
                        headers=gh.headers, timeout=10)
        tree = [{"path": f["path"], "type": f["type"]} for f in r.json().get("tree", [])] if r.status_code == 200 else []

    desc = repo.get("description", "") or "A project by " + (gh.username or "")
    main_lang = max(langs, key=langs.get) if langs else "Unknown"
    files = [f["path"] for f in tree if f.get("type") == "blob"]

    # Detect stack
    has_docker = any("Dockerfile" in f for f in files)
    has_tests = any("test" in f.lower() for f in files)
    has_reqs = any(f in files for f in ("requirements.txt", "package.json", "Cargo.toml", "go.mod"))

    install_cmd = "git clone https://github.com/{user}/{repo}.git\ncd {repo}".format(
        user=gh.username, repo=n)
    if "requirements.txt" in files:
        install_cmd += "\npip install -r requirements.txt"
    elif "package.json" in files:
        install_cmd += "\nnpm install"
    elif "Cargo.toml" in files:
        install_cmd += "\ncargo build"

    readme = f"# {n}\n\n"
    readme += f"> {desc}\n\n"
    readme += f"![Language](https://img.shields.io/badge/language-{main_lang}-blue) "
    if not repo.get("private"):
        readme += f"![License](https://img.shields.io/github/license/{gh.username}/{n}) "
    readme += "\n\n"
    readme += f"## Overview\n\n{desc}\n\n"
    readme += f"## Installation\n\n```bash\n{install_cmd}\n```\n\n"
    if has_tests:
        readme += "## Testing\n\n```bash\npython -m pytest  # or npm test\n```\n\n"
    if has_docker:
        readme += "## Docker\n\n```bash\ndocker build -t {repo} .\ndocker run -p 8080:8080 {repo}\n```\n\n".format(repo=n)
    readme += "## Structure\n\n```\n"
    for f in files[:15]:
        readme += f"{f}\n"
    if len(files) > 15:
        readme += f"... and {len(files)-15} more files\n"
    readme += "```\n\n"
    readme += f"## License\n\nSee [LICENSE](LICENSE) for details.\n\n"
    readme += "---\n*Built with [GitPulse](http://workshop-diy.org)*\n"

    return {"readme": readme}


@router.post("/api/repo/<n>/inject-template")
def api_inject_template(n="", data=None, **kw):
    """Inject template files (.gitignore, LICENSE, etc.)."""
    gh = get_gh()
    if not data:
        return {"error": "No data"}
    template = data.get("template", "")
    templates = {
        "gitignore-python": ("# Python\n__pycache__/\n*.pyc\n*.pyo\n*.egg-info/\ndist/\nbuild/\n.venv/\nvenv/\n.env\n.mypy_cache/\n.pytest_cache/\n\n# IDE\n.idea/\n.vscode/\n*.swp\n\n# OS\n.DS_Store\nThumbs.db\n", ".gitignore"),
        "gitignore-node": ("node_modules/\ndist/\nbuild/\n.env\n*.log\ncoverage/\n\n# IDE\n.idea/\n.vscode/\n\n# OS\n.DS_Store\nThumbs.db\n", ".gitignore"),
        "gitignore-cpp": ("build/\ncmake-build*/\n*.o\n*.so\n*.a\n*.out\n\n# IDE\n.idea/\n.vscode/\n*.swp\n", ".gitignore"),
        "license-mit": ("MIT License\n\nCopyright (c) {year} {user}\n\nPermission is hereby granted, free of charge, to any person obtaining a copy\nof this software and associated documentation files (the \"Software\"), to deal\nin the Software without restriction, including without limitation the rights\nto use, copy, modify, merge, publish, distribute, sublicense, and/or sell\ncopies of the Software, and to permit persons to whom the Software is\nfurnished to do so, subject to the following conditions:\n\nThe above copyright notice and this permission notice shall be included in all\ncopies or substantial portions of the Software.\n\nTHE SOFTWARE IS PROVIDED \"AS IS\", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR\nIMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,\nFITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE\nAUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER\nLIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,\nOUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE\nSOFTWARE.\n".format(year=datetime.now().year, user=gh.username), "LICENSE"),
        "contributing": ("# Contributing to {repo}\n\nThank you for considering contributing!\n\n## How to Contribute\n\n1. Fork the repository\n2. Create a feature branch (`git checkout -b feature/amazing-feature`)\n3. Commit your changes (`git commit -m 'Add amazing feature'`)\n4. Push to the branch (`git push origin feature/amazing-feature`)\n5. Open a Pull Request\n\n## Code of Conduct\n\nPlease be respectful and constructive in all interactions.\n".format(repo=n), "CONTRIBUTING.md"),
    }
    if template not in templates:
        return {"error": "Unknown template"}
    content, filename = templates[template]
    ok, result = gh.create_or_update_file(n, filename, content, f"Add {filename}")
    return {"ok": ok, "filename": filename}


# ─── BULK CLONE API ───────────────────────────────────────────

@router.post("/api/clone")
def api_clone_single(data=None, **kw):
    """Clone a single repo (called repeatedly by frontend)."""
    gh = get_gh()
    if not data or not data.get("name"):
        return {"ok": False, "error": "No repo name"}
    name = data["name"]
    dest = data.get("dest", "").strip()
    if not dest:
        import os
        config = get_config()
        dest = config.get("clone_directory", os.path.expanduser("~/repos"))
    import os
    os.makedirs(dest, exist_ok=True)
    target = os.path.join(dest, name)
    if os.path.exists(target):
        return {"ok": True, "status": "skipped", "name": name}
    try:
        success, err = gh.clone_repo(name, dest)
        if success:
            return {"ok": True, "status": "cloned", "name": name}
        else:
            return {"ok": False, "status": "failed", "name": name, "error": err.strip()}
    except Exception as e:
        return {"ok": False, "status": "failed", "name": name, "error": str(e)}


# ─── WELCOME & CONNECT ───────────────────────────────────────

@router.get("/welcome")
def welcome_page(**kw):
    return render("welcome.html")


@router.get("/tutorial")
def tutorial_page(**kw):
    gh = get_gh()
    if gh:
        return render("tutorial.html", **_ctx(page_title="Tutorial"))
    return render("tutorial.html", version=VERSION, codename=CODENAME,
                  username="", theme="masjid", language="en", dir="ltr",
                  mode="advanced", page_title="Tutorial")


@router.post("/api/connect")
def api_connect(data=None, **kw):
    """Accept a GitHub token or activate demo mode from the browser."""
    from ..server import set_gh

    if not data:
        return {"ok": False, "error": "No data"}

    # Demo mode
    if data.get("demo"):
        from lib.demo import DemoAPI
        set_gh(DemoAPI())
        from lib.colors import C
        print(f"  {C.YELLOW}{C.BOLD}★ DEMO MODE activated from browser{C.RESET}")
        return {"ok": True, "username": "demo-user", "demo": True}

    # Username-only (public repos, read-only)
    username = data.get("username", "").strip()
    if username:
        try:
            from lib.api import PublicAPI
            gh = PublicAPI(username)
            set_gh(gh)
            from lib.colors import C
            print(f"  {C.GREEN}+ Browsing public repos: {C.BOLD}{gh.username}{C.RESET}")
            return {"ok": True, "username": gh.username}
        except ValueError as e:
            return {"ok": False, "error": str(e)}
        except Exception as e:
            return {"ok": False, "error": str(e)}

    # Real token
    token = data.get("token", "").strip()
    if not token:
        return {"ok": False, "error": "No token provided"}

    try:
        from lib.api import GitHubAPI
        gh = GitHubAPI(token)
        set_gh(gh)

        # Save token to config
        from lib.config import save
        config = get_config()
        config["token"] = token
        save(config)

        from lib.colors import C
        print(f"  {C.GREEN}+ Connected: {C.BOLD}{gh.username}{C.RESET}")
        return {"ok": True, "username": gh.username}
    except SystemExit:
        return {"ok": False, "error": "Invalid token — check scopes (repo, read:user)"}
    except Exception as e:
        return {"ok": False, "error": str(e)}
