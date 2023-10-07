# بسم الله الرحمن الرحيم

# GitPulse v8.0 — Roadmap

**Powered by workshop-diy.org**

---

## Architecture

### CLI
- Entry: `gitpulse.py` (--web flag for Web UI)
- 25 modules in `lib/`
- First-run wizard: language → mode selection
- 2 modes: 🐣 Beginner (8 items) / 🔥 Advanced (29 items)
- 3 languages: EN / FR / AR
- Platforms: Linux, MSYS2/Git Bash, macOS (Homebrew)
- Config: `~/.gitpulse/config.json`

### Web UI
- Built on Python `http.server` — zero extra dependencies
- Custom `{{variable}}` template engine (no Jinja2)
- Routes in `web/routes/` call same `lib/` modules as CLI
- Static files: `web/static/`
- 20 HTML templates
- 7 Islamic art themes (CSS variables)
- API endpoints return JSON, pages return HTML

### Project Structure
```
gitpulse/
├── gitpulse.py              # Entry (CLI + --web)
├── gitpulse.sh              # Bash installer (MSYS2/Git Bash/Linux)
├── README.md
├── ROADMAP.md               # ← You are here
├── lib/                     # 24 modules
│   ├── accounts.py          # Multi-account manager
│   ├── actions.py           # Core menu actions
│   ├── ai.py                # AI summaries + diff storyteller
│   ├── analytics.py         # Traffic stats
│   ├── api.py               # GitHub REST API client
│   ├── archaeology.py       # Dead branches, TODOs, large files
│   ├── backup.py            # Clone all, compress
│   ├── bulk.py              # Mass operations
│   ├── colors.py            # ANSI color detection
│   ├── config.py            # Config management
│   ├── danger.py            # Security scanner (14 secret patterns)
│   ├── deps.py              # Dependency scanner
│   ├── gitlog.py            # Interactive git log
│   ├── grouper.py           # Auto-categorize repos (10 rules)
│   ├── health.py            # Repo health scoring
│   ├── i18n.py              # EN/FR/AR translations
│   ├── releases.py          # Tag + release manager
│   ├── rhythm.py            # Commit pattern analyzer
│   ├── search.py            # Cross-repo code search
│   ├── sshkeys.py           # SSH key manager
│   ├── templates.py         # Repo boilerplate
│   ├── timestamps.py        # Commit date editor
│   ├── ui.py                # Banner, menus, formatters
│   └── workflows.py         # GitHub Actions monitor
├── web/
│   ├── server.py            # HTTPServer + handler
│   ├── router.py            # URL dispatch (<param> support)
│   ├── templating.py        # {{var}}, {{for}}, {{if}}, {{include}}
│   ├── routes/__init__.py   # All page + API routes
│   ├── static/css/style.css # 7 themes, responsive, RTL
│   ├── static/js/app.js     # Client-side helpers
│   └── templates/           # 20 HTML templates
└── portable/
    ├── run.bat              # Windows USB launcher
    └── run.sh               # Linux/MSYS2 USB launcher
```

---

## Release Phases (Completed)

| Phase | Version | Codename | What Shipped |
|-------|---------|----------|--------------|
| 0 | 0.1 | Core | CLI repackaged as GitPulse, first-run wizard, beginner/advanced modes, i18n (EN/FR/AR), bismillah branding |
| 1 | 0.2 | Powertools | `backup.py` — clone all repos, compress to zip. `health.py` — score repos on README, LICENSE, .gitignore, description, topics. `bulk.py` — mass rename, visibility toggle, delete, topic management |
| 2 | 0.3 | GitDeep | `gitlog.py` — interactive git log with graph view, color, filters. `search.py` — cross-repo search for code, filenames, commits, issues |
| 3 | 0.4 | DevOps | `workflows.py` — GitHub Actions monitor, workflow run status across repos. `releases.py` — create tags, releases, upload assets |
| 4 | 0.5 | Toolkit | `templates.py` — repo boilerplate creation. `sshkeys.py` — generate, upload, test SSH keys. `timestamps.py` — view, shift, randomize commit dates |
| 5 | 0.6 | Insights | `analytics.py` — traffic views, clones, referrers. `deps.py` — dependency scanner, outdated package detection |
| 6 | 0.7 | Brainstorm | `ai.py` — AI summaries (OpenAI optional) + magic diff storyteller (pure pattern matching, no AI needed) |
| 7 | 0.8 | Portal | Web UI core — `http.server`, router, template engine, dashboard, repos, repo detail, health, backup, settings pages |
| 8 | 0.9 | Horizon | Web pages for analytics, danger, archaeology, grouper, rhythm, time machine, DNA, graph, radar, voice, ambient. Full API layer |
| 9 | 0.10 | Sentinel | `danger.py` — 14 secret patterns (GitHub tokens, AWS keys, Slack, Stripe, etc.), risk indicators (no .gitignore, unprotected branch, public+no license). `archaeology.py` — dead branches, large files, TODO/FIXME scan, stale PRs, empty repos. `grouper.py` — 10 category rules (Web, Mobile, IoT, API, Library, Data/ML, DevOps, Docs, Learning, Tool) |
| 10 | 0.11 | Rhythm | `rhythm.py` — commit hour/weekday distribution, morning/evening/night percentages, bimodal detection, burst days, coding style profile. `accounts.py` — add/switch/remove accounts, separate tokens, active account tracking |
| 11 | 0.12 | Vision | Time Machine — commit slider with file tree. DNA Fingerprint — deterministic SVG from repo seed. Repo Graph — canvas force-directed layout, language-based links |
| 12 | 0.13 | Live | Collaboration Radar — 30s auto-refresh GitHub Events. Voice Control — browser Speech API, natural commands. Ambient Dashboard — full-screen always-on, auto-dim at night |
| 13 | 1.0 | Supernova | Portable USB mode (run.bat + run.sh), demo mode, final polish, README |
| 14 | 6.0 | Noor | Full repo editor (CLI + Web): name, description, visibility, topics, default branch, homepage, wiki, issues, archived. Web edit panel on repo detail page. New API endpoint `/api/repo/<n>/edit`. Demo mode enriched with all fields |
| 15 | 7.0 | Fajr | macOS/Homebrew platform support. Python 3.9 compatibility (`from __future__ import annotations`). Username-only browsing (PublicAPI, no token). Bulk clone with token-authenticated URLs (CLI + Web). Web bulk operations: Clone All, All Private, All Public with progress bars. Restructured TUI bulk menu into sub-menus (visibility, archive, metadata, clone, delete) |
| 16 | 8.0 | Buraq | Repos table: direct GitHub repo link (octocat icon) and GitHub Pages link (globe icon) per repo. Pages link only visible when Pages is active |

---

## Demo Mode

No GitHub token needed. Activate via:
- `python gitpulse.py --demo` (CLI)
- `python gitpulse.py --web --demo` (Web UI)
- Type `demo` at the token prompt

**17 sample repos** with realistic data:
- IoT projects (smart-garden-iot, weather-station, firmware-updater)
- Web apps (portfolio-site, quran-search, budget-tracker)
- Python APIs (prayer-times-api, gitpulse)
- ML/Data (ml-plant-disease)
- Mobile (recipe-app)
- Hardware (pcb-library, 3d-printer-mods)
- Config/Docs (dotfiles, home-automation, ansible-homelab, notes-archive, old-website)

All features work in demo mode — mock data for health checks, security scans, archaeology, analytics, traffic, events feed. Repos can be "created" and "deleted" within the session (resets on restart).

---

## Feature Details

### Core (Phase 0)
- **First-run wizard**: asks language (EN/FR/AR), then mode (beginner/advanced)
- **Beginner mode**: 8 menu items, friendly labels ("projects" not "repos"), dangerous features hidden
- **Advanced mode**: 29 menu items, technical terminology, all features unlocked
- **Bismillah**: `بسم الله الرحمن الرحيم` displayed on every launch (CLI banner + web header)
- **Branding**: "Powered by workshop-diy.org" in banner and web footer

### Danger Zone (Phase 9)
**Secret patterns scanned:**
| # | Type | Pattern |
|---|------|---------|
| 1 | GitHub Token | `ghp_[A-Za-z0-9]{36}` |
| 2 | GitHub OAuth | `gho_[A-Za-z0-9]{36}` |
| 3 | AWS Access Key | `AKIA[A-Z0-9]{16}` |
| 4 | AWS Secret | `aws...{40 chars}` |
| 5 | Slack Token | `xox[bpors]-...` |
| 6 | Slack Webhook | `hooks.slack.com/services/...` |
| 7 | Private Key | `-----BEGIN...PRIVATE KEY-----` |
| 8 | Generic API Key | `api_key/apikey = ...` |
| 9 | Generic Secret | `secret/password/pwd = ...` |
| 10 | Heroku API Key | UUID format |
| 11 | Sendgrid Key | `SG....` |
| 12 | Twilio Key | `SK[0-9a-fA-F]{32}` |
| 13 | Google API Key | `AIza...` |
| 14 | Stripe Key | `sk_live/pk_test_...` |

**Risk indicators:** no .gitignore, public without LICENSE, repo >500MB, no description, unprotected default branch

### Repo Grouper (Phase 9)
**10 detection categories:**
| Category | Detection signals |
|----------|-----------------|
| Web App | JS/TS/HTML, package.json, react/vue/angular topics |
| Mobile | Swift/Kotlin/Dart, Podfile, build.gradle, ios/android topics |
| IoT / HW | C/C++, platformio.ini, .ino files, esp32/arduino topics |
| API / Backend | Go/Rust/Java/Python, Dockerfile, manage.py, api/backend topics |
| Library | setup.py, pyproject.toml, Cargo.toml, library/sdk topics |
| Data / ML | Jupyter/R, .ipynb files, machine-learning topics |
| DevOps | Shell/HCL, workflows, Jenkinsfile, terraform topics |
| Docs | mkdocs.yml, docs/, documentation topics |
| Learning | learning/tutorial/course topics |
| Tool / CLI | cli.py, main.go, cli/tool topics |

### Rhythm Analyzer (Phase 10)
- Analyzes commits across up to 10 repos (50 per repo)
- **Detects:** peak hour, morning/afternoon/evening/night percentages, weekday distribution, weekend coding %, burst days (5+ commits)
- **Bimodal detection:** flags if you code both morning AND evening (>20% each)
- **Style profiles:** Night Owl 🦉, Early Bird 🐦, Evening Warrior 🌙, Dual Mode 🔄, Steady Coder ⚡

### Web UI Themes (Phase 7-8)
| Theme | CSS Class | Colors | Mode |
|-------|-----------|--------|------|
| المسجد Masjid | `theme-masjid` | Night sky, turquoise, moonlight | Dark |
| الأندلس Andalus | `theme-andalus` | Walnut, gold, Cordoba red | Dark |
| الحمراء Al-Hamra | `theme-alhamra` | Earth, terracotta, garden green | Dark |
| نور Nur | `theme-nur` | Aged paper, gold ink, lapis lazuli | Light |
| رقش Raqsh | `theme-raqsh` | Cream, indigo, tulip red | Light |
| صحراء Sahra | `theme-sahra` | Desert sky, sand gold, twilight purple | Dark |
| زهرة Zahra | `theme-zahra` | Ocean, emerald, ruby, jade | Dark |

### Web-Only Features (Phases 11-12)
| Feature | How it works |
|---------|-------------|
| Time Machine | Slider scrubs through commits, file tree updates. Uses `/api/repo/<n>/commits` + `/api/repo/<n>/tree` |
| DNA Fingerprint | MD5 hash of repo name+created_at → deterministic SVG. Circles from seed bytes, language pie from ratios, star indicator |
| Repo Graph | Fetch all repos → nodes. Same-language repos linked. Canvas force simulation: repulsion between all, attraction on links, center gravity. 200 frames |
| Collaboration Radar | Polls `/users/{username}/received_events` every 30s. Maps event types to icons |
| Voice Control | Browser `SpeechRecognition` API (Chrome/Edge). Parses: "list repos", "health check", "dashboard", "settings", "danger scan", "rhythm" |
| Ambient Dashboard | Standalone full-screen page. Clock + date + repo stats + event feed. Auto-dim between 23:00-06:00 |

---

## Dependencies

**Required:** `requests`

**Optional:** `openai` (for AI summaries only)

**Built-in Python (no install):** http.server, json, pathlib, subprocess, hashlib, re, os, sys, datetime, collections, threading, webbrowser, mimetypes

**Browser-side (CDN, web only):** Google Fonts (Amiri, Scheherazade New)

---

## Portable USB Mode

```
USB_DRIVE/
├── gitpulse.py
├── lib/
├── web/
├── portable/
│   ├── run.bat          # Double-click on Windows
│   └── run.sh           # chmod +x && ./run.sh on Linux
├── config/              # Created on first run (stored on USB)
└── python/              # Optional: drop WinPython here for zero-install Windows
```

- `GHM_CONFIG` env var points config to USB instead of `~/.gitpulse/`
- No PATH changes, no admin, no system modifications
- Auto-installs `requests` if missing

---

*بسم الله الرحمن الرحيم*
