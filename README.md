# بسم الله الرحمن الرحيم

# GitPulse v8.0 — Buraq ✦

**The complete GitHub repository manager — CLI + Web UI**

Powered by [workshop-diy.org](http://workshop-diy.org)

---

## Table of Contents

- [Quick Start](#quick-start)
- [Installation](#installation)
- [Getting a GitHub Token](#getting-a-github-token)
- [CLI Usage](#cli-usage)
- [Web UI Usage](#web-ui-usage)
- [Demo Mode](#demo-mode)
- [Features](#features)
- [Themes](#themes)
- [Languages & Modes](#languages--modes)
- [Configuration](#configuration)
- [Portable USB Mode](#portable-usb-mode)
- [How To...](#how-to)
- [FAQ](#faq)
- [Troubleshooting](#troubleshooting)
- [Project Structure](#project-structure)
- [License](#license)

---

## Quick Start

```bash
bash gitpulse.sh                    # Install (MSYS2/Git Bash/Linux/macOS)
python gitpulse.py                  # Run CLI
python gitpulse.py --web            # Run Web UI (opens browser)
python gitpulse.py --demo           # Demo mode (no token)
python gitpulse.py --web --demo     # Web demo
```

**Only dependency:** `requests` (auto-installed by gitpulse.sh)

---

## Installation

### Option A: Installer Script (recommended)

```bash
bash gitpulse.sh
```

The installer detects your platform (MSYS2/Git Bash/Linux/macOS), checks Python 3.8+, installs `requests`, and creates a `gp` alias. After install, type `gp` from anywhere.

### Option B: Manual

```bash
pip install requests
python gitpulse.py
```

### Option C: Portable USB (no install)

Copy `gitpulse/` to USB. Double-click `portable/run.bat` (Windows) or `./portable/run.sh` (Linux). Config stays on the USB.

---

## Getting a GitHub Token

1. Go to https://github.com/settings/tokens
2. Click **"Generate new token (classic)"**
3. Name it `GitPulse`
4. Select scopes:
   - ✅ `repo` (full control of private repositories)
   - ✅ `read:user` (read user profile data)
   - ✅ `delete_repo` (if you want delete features)
   - ✅ `workflow` (if you want Actions monitor)
5. Click **Generate token**, copy the `ghp_...` string
6. Paste when GitPulse asks, or set environment variable:

```bash
export GITHUB_TOKEN="ghp_your_token_here"
```

**Where is my token stored?** `~/.gitpulse/config.json` with chmod 600. Never sent anywhere except `api.github.com`.

---

## CLI Usage

```bash
python gitpulse.py           # Interactive CLI
python gitpulse.py --demo    # Demo mode
```

### First launch:
1. Choose language: English / Français / العربية
2. Choose mode: 🐣 Beginner (8 items) or 🔥 Advanced (29 items)
3. Enter GitHub token (or type `demo`)

### Navigation:
- Type number + Enter to select
- `0` = exit
- Ctrl+C = cancel current operation
- Empty Enter = go back

### Beginner Mode (8 items)
```
1  View my projects     5  Edit a project
2  Search projects      6  Download a project
3  Project details      7  Quick overview
4  Create a project     8  Settings
```

### Advanced Mode (29 items)
```
REPOS                  SENTINEL
 1  List repos          23  Danger zone
 2  Search repos        24  Git archaeology
 3  Repo details        25  Smart repo grouper
 4  Create repo        RHYTHM
 5  Delete repo         26  Commit rhythm analyzer
 6  Edit repo           27  Multi-account manager
 7  Clone repo         ---
GIT INFO               28  Quick stats
 8  Commits             29  Settings
 9  Branches
POWER TOOLS
 10  Backup manager
 11  Health dashboard
 12  Bulk operations
GIT DEEP
 13  Interactive git log
 14  Cross-repo search
DEVOPS
 15  Actions monitor
 16  Release manager
TOOLKIT
 17  Repo templates
 18  SSH key manager
 19  Timestamp editor
INSIGHTS
 20  Analytics & traffic
 21  Dependency scanner
AI / SUMMARY
 22  AI summaries
```

---

## Web UI Usage

```bash
python gitpulse.py --web             # Start server
python gitpulse.py --web --demo      # Demo mode
```

Server starts on `http://127.0.0.1:5000`, browser opens automatically.

If no token → **Welcome page** appears with:
- **Browse by username** (public repos, read-only)
- **Connect GitHub** (paste token for full access)
- **★ Try Demo Mode** (one click)
- **📖 Read Tutorial**

### All Web Pages

| Page | URL | Description |
|------|-----|-------------|
| Welcome | `/welcome` | Connect token or start demo |
| Dashboard | `/` | Stats overview + quick access |
| Repos | `/repos` | Browse and search all repos |
| Repo Detail | `/repo/{name}` | Languages, commits, branches, edit all fields |
| Health | `/health` | Score repos on best practices |
| Backup | `/backup` | Backup manager |
| Danger Zone | `/danger` | Secret scanner + risk check |
| Archaeology | `/archaeology` | Dead branches, TODOs, large files |
| Grouper | `/grouper` | Auto-categorize repos |
| Rhythm | `/rhythm` | Coding pattern analysis |
| Analytics | `/analytics` | Traffic, views, clones |
| Time Machine | `/timemachine/{name}` | Scrub through commits |
| DNA | `/dna` | Repo visual fingerprint |
| Graph | `/graph` | Repo relationship map |
| Radar | `/radar` | Live event feed (30s refresh) |
| Voice | `/voice` | Speech commands (Chrome/Edge) |
| Ambient | `/ambient` | Fullscreen always-on display |
| Tutorial | `/tutorial` | Complete feature guide |
| Settings | `/settings` | Theme, language, mode |

### Change port:
```json
// ~/.gitpulse/config.json
{ "web_port": 8080, "web_host": "0.0.0.0" }
```

---

## Demo Mode

Try everything without a GitHub account.

| Method | How |
|--------|-----|
| CLI flag | `python gitpulse.py --demo` |
| Web flag | `python gitpulse.py --web --demo` |
| At prompt | Type `demo` instead of token |
| Web UI | Click **★ Try Demo Mode** on welcome page |

**17 sample repos** included: IoT (smart-garden-iot, weather-station), Web (portfolio-site, quran-search), Python (prayer-times-api), ML (ml-plant-disease), Mobile (recipe-app), Hardware (pcb-library, 3d-printer-mods), and more. All features work with mock data.

---

## Features

### 📦 Repos (1-7)
- **List**: all repos, sort by name/date/stars, filter public/private
- **Search**: by name, description, topic, language
- **Details**: languages (%), commits, branches, clone URL, topics
- **Create**: with name, description, visibility, auto-init README
- **Delete**: permanent with double confirmation (hidden in beginner)
- **Edit**: name, description, visibility, topics, default branch, homepage, wiki, issues, archived
- **Clone**: clone to local directory via git

### 🔀 Git Info (8-9)
- **Commits**: SHA, message, author, date
- **Branches**: list with protection status

### ⚡ Power Tools (10-12)
- **Backup**: clone ALL repos at once, compress to .zip
- **Health**: score 0-100% (README, LICENSE, .gitignore, desc, topics)
- **Bulk Ops**: visibility (all private/public), archive, metadata (description/topics), clone all, delete — with sub-menus

### 🔬 Git Deep (13-14)
- **Git Log**: graph view, color branches, author/date filters
- **Search**: code, filenames, commits, issues across ALL repos

### 🚀 DevOps (15-16)
- **Actions**: workflow runs, pass/fail status, duration
- **Releases**: create tags, releases, upload assets

### 🛠️ Toolkit (17-19)
- **Templates**: Python/Node/ESP32/static boilerplates
- **SSH Keys**: generate ed25519, upload, test
- **Timestamps**: view/shift/randomize commit dates

### 📊 Insights (20-21)
- **Analytics**: 14-day views, clones, referrers
- **Dependencies**: outdated/vulnerable packages

### 🤖 AI (22)
- **Summaries**: plain-English repo overview (OpenAI optional)
- **Diff Story**: commits → narrative (pattern-based, no AI)

### 🛡️ Sentinel (23-25)
- **Danger Zone**: 14 secret patterns + 5 risk indicators
- **Archaeology**: dead branches, large files, TODO/FIXME, stale PRs
- **Grouper**: auto-sort into 10 categories

### 💓 Rhythm (26-27)
- **Analyzer**: peak hour, time split, style profile
- **Multi-Account**: add/switch/remove (personal/work/client)

### 🌐 Web-Only
- **Clone All**: bulk clone from repos page with progress bar
- **All Private / All Public**: bulk visibility toggle with progress
- **Time Machine**: commit slider + file tree
- **DNA**: unique SVG fingerprint per repo
- **Graph**: force-directed repo relationship map
- **Radar**: live event feed (30s refresh)
- **Voice**: speak commands (Chrome/Edge)
- **Ambient**: fullscreen clock + stats + feed

---

## Themes

7 Islamic art themes in Settings:

| Theme | Arabic | Vibe | Mode |
|-------|--------|------|------|
| Masjid | المسجد | Turquoise domes, marble | Dark |
| Andalus | الأندلس | Gold, zellige, Cordoba red | Dark |
| Al-Hamra | الحمراء | Terracotta, earth, garden | Dark |
| Nur | نور | Parchment, gold ink, lapis | Light |
| Raqsh | رقش | Cream, indigo, tulip red | Light |
| Sahra | صحراء | Desert sky, sand, twilight | Dark |
| Zahra | زهرة | Ocean, emerald, jade | Dark |

---

## Languages & Modes

**Languages:** English (`en`) · Français (`fr`) · العربية (`ar`, RTL)

**Modes:** 🐣 Beginner (8 items, safe) · 🔥 Advanced (29 items, full power)

Change anytime from Settings without restarting.

---

## Configuration

File: `~/.gitpulse/config.json`

| Key | Default | Description |
|-----|---------|-------------|
| `token` | — | GitHub token |
| `mode` | `advanced` | `beginner` or `advanced` |
| `language` | `en` | `en`, `fr`, `ar` |
| `web_theme` | `masjid` | Theme name |
| `web_port` | `5000` | Server port |
| `web_host` | `127.0.0.1` | Bind address |
| `web_auto_open` | `true` | Auto-open browser |
| `clone_directory` | `~/repos` | Clone destination |
| `commits_count` | `10` | Commits to show |
| `default_sort` | `updated` | Sort order |
| `default_direction` | `desc` | Sort direction |
| `default_repo_type` | `all` | Filter |

---

## Portable USB Mode

```
USB/
├── gitpulse/
│   ├── gitpulse.py
│   ├── lib/, web/
│   ├── portable/
│   │   ├── run.bat     ← double-click (Windows)
│   │   ├── run.sh      ← chmod +x && run (Linux)
│   │   └── python/     ← optional: WinPython here
│   └── config/         ← created on first run
```

No admin, no PATH changes, nothing written to host machine.

---

## How To...

### Back up all repos
CLI option 10 → "Clone all" → choose folder → optional .zip

### Find leaked secrets
CLI option 23 or Web `/danger` → enter repo name → scans 14 secret patterns (AWS, GitHub, Slack, Stripe, etc.)

### Check repo health
CLI option 11 or Web `/health` → scores every repo 0-100% on README, LICENSE, .gitignore, description, topics

### Clean up dead branches
CLI option 24 → "Dead branches" → shows branches 6+ months stale

### See coding patterns
CLI option 26 or Web `/rhythm` → peak hour, morning/evening %, style (Night Owl, Early Bird, etc.)

### Switch accounts
CLI option 27 → add account with label + token → switch instantly

### Change theme
Web `/settings` → pick from 7 themes → Save

### Change language
CLI option 29 or Web `/settings` → English / Français / العربية

### Use voice commands
Web `/voice` → click mic → say "list repos", "health check", "danger scan", "dashboard", "settings"

### Create from template
CLI option 17 → Python / Node / ESP32 / Static → auto-generates README, .gitignore, LICENSE

### View traffic
CLI option 20 or Web `/analytics` → enter repo name → 14-day views, clones, referrers (requires repo owner)

### Use ambient mode
Web `/ambient` → fullscreen clock + stats + live feed, auto-dims at night

### Generate DNA fingerprint
Web `/dna` → enter repo name → unique SVG art from languages, commits, stars, creation date

### Auto-categorize repos
CLI option 25 or Web `/grouper` → sorts repos into: Web, Mobile, IoT, API, Library, ML, DevOps, Docs, Learning, Tool

### Run on locked-down PC
Copy to USB → `portable/run.bat` (Windows) or `portable/run.sh` (Linux)

### Expose on LAN
Set `"web_host": "0.0.0.0"` in config → access from `http://YOUR_IP:5000`

### Use time machine
Web `/timemachine/{repo}` → drag slider through commits → see file tree at each point

---

## FAQ

**Q: Is my token secure?**
A: Stored in `~/.gitpulse/config.json` (chmod 600). Only sent to `api.github.com`.

**Q: Does GitPulse modify my repos?**
A: Only on write actions (create/delete/edit/archive). Read operations never modify anything. Edit supports: name, description, visibility, topics, default branch, homepage, wiki, issues, and archive status.

**Q: Can I use it without GitHub?**
A: Yes — demo mode works without any account.

**Q: What Python version?**
A: 3.9+. Tested on 3.9 through 3.12.

**Q: Dependencies?**
A: Only `requests`. Optional: `openai` for AI summaries.

**Q: Windows support?**
A: Yes — MSYS2, Git Bash, WSL, native cmd/PowerShell.

**Q: macOS support?**
A: Yes — Homebrew detected automatically by the installer.

**Q: Works offline?**
A: Demo mode works offline. Real data needs internet.

**Q: Voice not working?**
A: Requires Chrome or Edge. Firefox/Safari don't support Web Speech API.

**Q: Port 5000 busy?**
A: Set `"web_port": 8080` in config.

**Q: Rate limit exceeded?**
A: GitHub allows 5,000 req/hour. Wait for reset or reduce scan scope.

**Q: What secrets are detected?**
A: GitHub tokens, AWS keys, Slack tokens/webhooks, private keys (RSA/DSA/EC), API keys, passwords, Heroku, Sendgrid, Twilio, Google, Stripe.

**Q: Are tokens encrypted?**
A: File-level permissions (chmod 600), not encrypted. Use env vars for higher security.

**Q: Can demo mode break anything?**
A: No. Fake data in memory, resets on restart.

**Q: How many accounts?**
A: No limit. Each gets a label.

**Q: Expose to internet?**
A: Not recommended — no auth on web UI. Use reverse proxy with auth if needed.

---

## Troubleshooting

| Problem | Solution |
|---------|----------|
| `No module named requests` | `pip install requests` or `pip install requests --break-system-packages` or `brew install python-requests` (macOS) |
| Permission denied on token | `chmod 600 ~/.gitpulse/config.json` |
| Address already in use | Change `"web_port"` in config |
| Some features fail | Check token scopes: `repo`, `read:user`, `delete_repo`, `workflow` |
| Rate limit exceeded | Wait for reset or reduce scan scope |
| Blank web page | Check terminal for errors, clear browser cache |
| MSYS2 installer fails | Run `pacman -Syu && pacman -S python python-pip` first |

---

## Project Structure

```
gitpulse/                         72 files
├── gitpulse.py                   Entry (CLI + --web + --demo)
├── gitpulse.sh                   Installer
├── README.md                     Documentation
├── ROADMAP.md                    Dev history & architecture
├── lib/                          25 modules
│   ├── accounts.py               Multi-account
│   ├── actions.py                Core menu actions
│   ├── ai.py                     AI summaries + diff story
│   ├── analytics.py              Traffic stats
│   ├── api.py                    GitHub API client
│   ├── archaeology.py            Dead branches, TODOs
│   ├── backup.py                 Clone all, compress
│   ├── bulk.py                   Mass operations
│   ├── colors.py                 ANSI colors
│   ├── config.py                 Config management
│   ├── danger.py                 Security scanner
│   ├── demo.py                   Demo mode (17 repos)
│   ├── deps.py                   Dependency scanner
│   ├── gitlog.py                 Interactive log
│   ├── grouper.py                Auto-categorize
│   ├── health.py                 Health scoring
│   ├── i18n.py                   EN/FR/AR
│   ├── releases.py               Release manager
│   ├── rhythm.py                 Commit patterns
│   ├── search.py                 Cross-repo search
│   ├── sshkeys.py                SSH keys
│   ├── templates.py              Repo boilerplates
│   ├── timestamps.py             Date editor
│   ├── ui.py                     Menus, banner
│   └── workflows.py              Actions monitor
├── web/                          Server + 22 templates
│   ├── server.py                 HTTPServer
│   ├── router.py                 URL dispatch
│   ├── templating.py             Template engine
│   ├── routes/__init__.py        All routes
│   ├── static/css/style.css      7 themes
│   ├── static/js/app.js          Client JS
│   └── templates/                22 HTML files
└── portable/
    ├── run.bat                   Windows
    └── run.sh                    Linux
```

---

## License

MIT

---

*بسم الله الرحمن الرحيم*
