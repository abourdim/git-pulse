"""Commit Rhythm Analyzer — discover coding patterns and habits."""

import requests as req
from datetime import datetime
from collections import Counter
from .api import GitHubAPI
from .colors import C
from .i18n import t


def fetch_all_commits(gh: GitHubAPI, max_repos: int = 10, max_per_repo: int = 50) -> list:
    """Fetch recent commits across repos for rhythm analysis."""
    repos = gh.list_repos(repo_type="owner")[:max_repos]
    all_commits = []
    for repo in repos:
        commits = gh.list_commits(repo["name"], max_per_repo)
        for c in commits:
            author = c.get("commit", {}).get("author", {})
            if author.get("name") and author.get("date"):
                all_commits.append({
                    "repo": repo["name"],
                    "date": author["date"],
                    "message": c.get("commit", {}).get("message", ""),
                })
    return all_commits


def analyze_rhythm(commits: list) -> dict:
    """Analyze coding patterns from commit timestamps."""
    hours = Counter()
    weekdays = Counter()
    months = Counter()
    daily_counts = Counter()
    burst_streaks = []

    day_names = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]

    for c in commits:
        try:
            dt = datetime.strptime(c["date"], "%Y-%m-%dT%H:%M:%SZ")
            hours[dt.hour] += 1
            weekdays[dt.weekday()] += 1
            months[dt.month] += 1
            daily_counts[dt.strftime("%Y-%m-%d")] += 1
        except ValueError:
            pass

    # Peak hour
    peak_hour = hours.most_common(1)[0] if hours else (12, 0)

    # Coding style detection
    morning = sum(hours.get(h, 0) for h in range(6, 12))
    afternoon = sum(hours.get(h, 0) for h in range(12, 18))
    evening = sum(hours.get(h, 0) for h in range(18, 24))
    night = sum(hours.get(h, 0) for h in range(0, 6))

    total = max(morning + afternoon + evening + night, 1)
    morning_pct = morning / total * 100
    evening_pct = evening / total * 100
    night_pct = night / total * 100

    # Bimodal detection
    bimodal = morning_pct > 20 and evening_pct > 20

    # Style
    if night_pct > 30:
        style = "Night Owl 🦉"
    elif morning_pct > 40:
        style = "Early Bird 🐦"
    elif evening_pct > 40:
        style = "Evening Warrior 🌙"
    elif bimodal:
        style = "Dual Mode 🔄 (morning + evening)"
    else:
        style = "Steady Coder ⚡"

    # Weekday vs weekend
    weekday_total = sum(weekdays.get(d, 0) for d in range(5))
    weekend_total = sum(weekdays.get(d, 0) for d in range(5, 7))
    weekend_pct = weekend_total / max(weekday_total + weekend_total, 1) * 100

    # Burst detection (days with 5+ commits)
    burst_days = sum(1 for d, c in daily_counts.items() if c >= 5)

    # Average commits per active day
    avg_per_day = len(commits) / max(len(daily_counts), 1)

    return {
        "total_commits": len(commits),
        "active_days": len(daily_counts),
        "avg_per_day": round(avg_per_day, 1),
        "peak_hour": peak_hour[0],
        "style": style,
        "bimodal": bimodal,
        "hours": dict(hours),
        "weekdays": {day_names[k]: v for k, v in sorted(weekdays.items())},
        "morning_pct": round(morning_pct, 1),
        "afternoon_pct": round(afternoon / total * 100, 1),
        "evening_pct": round(evening_pct, 1),
        "night_pct": round(night_pct, 1),
        "weekend_pct": round(weekend_pct, 1),
        "burst_days": burst_days,
    }


def rhythm_menu(gh: GitHubAPI):
    """CLI menu for rhythm analysis."""
    print(f"\n  {C.BOLD}{C.CYAN}=== COMMIT RHYTHM ANALYZER ==={C.RESET}\n")
    print(f"  {C.DIM}Analyzing your coding patterns...{C.RESET}\n")

    commits = fetch_all_commits(gh)
    if not commits:
        print(f"  {C.YELLOW}No commits found to analyze.{C.RESET}")
        return

    r = analyze_rhythm(commits)

    print(f"  {C.BOLD}{'=' * 50}{C.RESET}")
    print(f"  {C.BOLD}{C.CYAN}Your Coding Profile{C.RESET}")
    print(f"  {C.BOLD}{'=' * 50}{C.RESET}\n")

    print(f"  {C.BOLD}Style:{C.RESET}            {r['style']}")
    print(f"  {C.BOLD}Total commits:{C.RESET}    {r['total_commits']}")
    print(f"  {C.BOLD}Active days:{C.RESET}      {r['active_days']}")
    print(f"  {C.BOLD}Avg per day:{C.RESET}      {r['avg_per_day']}")
    print(f"  {C.BOLD}Peak hour:{C.RESET}        {r['peak_hour']}:00")
    print(f"  {C.BOLD}Burst days:{C.RESET}       {r['burst_days']} (5+ commits)")

    print(f"\n  {C.BOLD}Time Distribution:{C.RESET}")
    print(f"    Morning (6-12):   {C.CYAN}{'#' * int(r['morning_pct'] / 3)}{C.RESET} {r['morning_pct']}%")
    print(f"    Afternoon (12-18):{C.CYAN}{'#' * int(r['afternoon_pct'] / 3)}{C.RESET} {r['afternoon_pct']}%")
    print(f"    Evening (18-24):  {C.CYAN}{'#' * int(r['evening_pct'] / 3)}{C.RESET} {r['evening_pct']}%")
    print(f"    Night (0-6):      {C.CYAN}{'#' * int(r['night_pct'] / 3)}{C.RESET} {r['night_pct']}%")

    print(f"\n  {C.BOLD}Weekday Activity:{C.RESET}")
    for day, count in r["weekdays"].items():
        bar = "#" * min(count, 30)
        print(f"    {day:3s} {C.CYAN}{bar}{C.RESET} {count}")

    print(f"\n  {C.BOLD}Weekend coding:{C.RESET}   {r['weekend_pct']}%")
    if r["bimodal"]:
        print(f"  {C.YELLOW}Bimodal pattern detected — you code both morning & evening!{C.RESET}")
