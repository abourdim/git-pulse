"""Smart Repo Grouper — auto-categorize repos by type."""

import re
from .api import GitHubAPI
from .colors import C
from .ui import pick_repo
from .i18n import t

# Detection rules: (category, indicators)
CATEGORY_RULES = [
    ("Web App",     {"language": ["JavaScript", "TypeScript", "HTML", "CSS", "Vue", "Svelte"],
                     "files": ["package.json", "index.html", "webpack.config", "vite.config"],
                     "topics": ["web", "frontend", "react", "vue", "angular", "nextjs"]}),
    ("Mobile",      {"language": ["Swift", "Kotlin", "Dart", "Objective-C"],
                     "files": ["Podfile", "build.gradle", "pubspec.yaml", "AndroidManifest.xml"],
                     "topics": ["ios", "android", "mobile", "flutter", "react-native"]}),
    ("IoT / HW",    {"language": ["C", "C++", "MicroPython"],
                     "files": ["platformio.ini", "arduino.ino", ".ino", "CMakeLists.txt"],
                     "topics": ["esp32", "arduino", "iot", "raspberry-pi", "embedded", "hardware"]}),
    ("API / Backend",{"language": ["Go", "Rust", "Java", "Python", "Ruby", "PHP"],
                     "files": ["Dockerfile", "docker-compose.yml", "Procfile", "wsgi.py", "manage.py"],
                     "topics": ["api", "backend", "server", "microservice", "rest", "graphql"]}),
    ("Library",     {"language": [],
                     "files": ["setup.py", "pyproject.toml", "Cargo.toml", "build.gradle", "pom.xml"],
                     "topics": ["library", "sdk", "package", "module", "framework"]}),
    ("Data / ML",   {"language": ["Jupyter Notebook", "R"],
                     "files": [".ipynb", "requirements-ml.txt", "model.py"],
                     "topics": ["machine-learning", "data-science", "ai", "deep-learning", "nlp"]}),
    ("DevOps",      {"language": ["Shell", "HCL", "Dockerfile"],
                     "files": [".github/workflows", "Jenkinsfile", "terraform", ".gitlab-ci.yml", "k8s"],
                     "topics": ["devops", "ci-cd", "terraform", "kubernetes", "docker"]}),
    ("Docs",        {"language": [],
                     "files": ["mkdocs.yml", "docs/", "SUMMARY.md", "book.toml", "docusaurus.config"],
                     "topics": ["documentation", "docs", "wiki", "tutorial", "guide"]}),
    ("Learning",    {"language": [],
                     "files": [],
                     "topics": ["learning", "tutorial", "course", "exercise", "practice", "bootcamp"]}),
    ("Tool / CLI",  {"language": ["Python", "Go", "Rust", "Shell"],
                     "files": ["cli.py", "main.go", "src/main.rs", "bin/"],
                     "topics": ["cli", "tool", "utility", "script", "automation"]}),
]


def categorize_repo(repo: dict) -> str:
    """Determine category of a single repo."""
    lang = repo.get("language", "") or ""
    topics = repo.get("topics", []) or []
    name = (repo.get("name", "") or "").lower()
    desc = (repo.get("description", "") or "").lower()

    best_score = 0
    best_cat = "Other"

    for cat, rules in CATEGORY_RULES:
        score = 0
        # Language match
        if lang in rules.get("language", []):
            score += 3
        # Topic match
        for tp in topics:
            if tp.lower() in rules.get("topics", []):
                score += 2
        # Name/desc hint
        for tp in rules.get("topics", []):
            if tp in name or tp in desc:
                score += 1
        if score > best_score:
            best_score = score
            best_cat = cat

    return best_cat


def group_repos(gh: GitHubAPI) -> dict:
    """Group all repos by auto-detected category."""
    repos = gh.list_repos(repo_type="owner")
    groups = {}
    for repo in repos:
        cat = categorize_repo(repo)
        groups.setdefault(cat, []).append(repo)
    return dict(sorted(groups.items()))


def grouper_menu(gh: GitHubAPI):
    """CLI menu for repo grouper."""
    print(f"\n  {C.BOLD}{C.CYAN}=== SMART REPO GROUPER ==={C.RESET}\n")
    print(f"  {C.GREEN}1{C.RESET}  Auto-group all repos")
    print(f"  {C.GREEN}2{C.RESET}  Categorize a single repo")
    print(f"  {C.GREEN}0{C.RESET}  {t('back')}")

    choice = input(f"\n  {C.YELLOW}> {t('choose')}: {C.RESET}").strip()

    if choice == "1":
        print(f"\n  {C.DIM}{t('fetching')}{C.RESET}")
        groups = group_repos(gh)
        total = sum(len(v) for v in groups.values())
        print(f"\n  {C.BOLD}Grouped {total} repos into {len(groups)} categories:{C.RESET}\n")

        icons = {"Web App": "🌐", "Mobile": "📱", "IoT / HW": "🔌", "API / Backend": "⚙️",
                 "Library": "📦", "Data / ML": "🧠", "DevOps": "🔧", "Docs": "📚",
                 "Learning": "🎓", "Tool / CLI": "🛠️", "Other": "📂"}

        for cat, repos in groups.items():
            icon = icons.get(cat, "📂")
            print(f"  {icon} {C.BOLD}{cat}{C.RESET} ({len(repos)})")
            for r in repos:
                vis = f"{C.RED}●{C.RESET}" if r["private"] else f"{C.GREEN}●{C.RESET}"
                lang = r.get("language") or ""
                print(f"      {vis} {C.CYAN}{r['name']}{C.RESET}  {C.DIM}{lang}{C.RESET}")
            print()

    elif choice == "2":
        name = pick_repo(gh)
        if not name: return
        repo = gh.get_repo(name)
        if not repo:
            print(f"\n  {C.RED}x {t('not_found')}{C.RESET}"); return
        cat = categorize_repo(repo)
        print(f"\n  {C.BOLD}{name}{C.RESET} → {C.CYAN}{cat}{C.RESET}")
