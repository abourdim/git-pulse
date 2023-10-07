"""Analytics — traffic stats, stars, referrers, heatmap."""

import requests as req
from .api import GitHubAPI
from .colors import C
from .ui import pick_repo
from .i18n import t
from .ui import format_date


def analytics_menu(gh: GitHubAPI):
    name = pick_repo(gh)
    if not name: return
    print(f"\n  {C.DIM}{t('fetching')}{C.RESET}")

    if getattr(gh, 'is_demo', False):
        # Use DemoAPI mock traffic
        traffic = gh.get_traffic(name) if hasattr(gh, 'get_traffic') else {}
        views = traffic.get("views", {"count": 0, "uniques": 0, "views": []})
        clones = traffic.get("clones", {"count": 0, "uniques": 0})
        ref_list = traffic.get("referrers", [])
        path_list = traffic.get("paths", [])
    else:
        views = req.get(f"{gh.BASE_URL}/repos/{gh.username}/{name}/traffic/views",
                        headers=gh.headers).json() if True else {}
        clones = req.get(f"{gh.BASE_URL}/repos/{gh.username}/{name}/traffic/clones",
                         headers=gh.headers).json() if True else {}
        referrers = req.get(f"{gh.BASE_URL}/repos/{gh.username}/{name}/traffic/popular/referrers",
                            headers=gh.headers)
        paths = req.get(f"{gh.BASE_URL}/repos/{gh.username}/{name}/traffic/popular/paths",
                        headers=gh.headers)
        ref_list = referrers.json() if referrers.status_code == 200 else []
        path_list = paths.json() if paths.status_code == 200 else []

    print(f"""
  {C.BOLD}{'=' * 50}{C.RESET}
  {C.BOLD}{C.CYAN}ANALYTICS: {name}{C.RESET}
  {C.BOLD}{'=' * 50}{C.RESET}

  {C.BOLD}TRAFFIC (last 14 days){C.RESET}
  Views:  {views.get('count', 0)} total ({views.get('uniques', 0)} unique)
  Clones: {clones.get('count', 0)} total ({clones.get('uniques', 0)} unique)
""")

    # Daily breakdown
    view_data = views.get("views", [])
    if view_data:
        print(f"  {C.BOLD}Daily views:{C.RESET}")
        max_count = max(v.get("count", 0) for v in view_data) or 1
        for v in view_data:
            date = v["timestamp"][:10]
            count = v.get("count", 0)
            bar = "#" * int(count / max_count * 30)
            print(f"    {date}  {C.CYAN}{bar}{C.RESET} {count}")

    # Referrers
    if ref_list:
        print(f"\n  {C.BOLD}TOP REFERRERS{C.RESET}")
        for r in ref_list[:5]:
            print(f"    {r['referrer']:<25} {r.get('count', 0)} views ({r.get('uniques', 0)} unique)")

    # Popular paths
    if path_list:
        print(f"\n  {C.BOLD}POPULAR PATHS{C.RESET}")
        for p in path_list[:5]:
            print(f"    {p['path']:<35} {p.get('count', 0)} views")

    # Star count & basic info
    repo = gh.get_repo(name)
    if repo:
        print(f"\n  {C.BOLD}STATS{C.RESET}")
        print(f"  Stars: {repo.get('stargazers_count', 0)}  Forks: {repo.get('forks_count', 0)}  "
              f"Watchers: {repo.get('subscribers_count', 0)}")

    # Contribution heatmap (simple version from commits)
    print(f"\n  {C.BOLD}RECENT COMMIT ACTIVITY{C.RESET}")
    commits = gh.list_commits(name, 50)
    from collections import Counter
    days = Counter()
    for c in commits:
        d = c["commit"]["author"]["date"][:10]
        days[d] += 1
    for date, count in sorted(days.items(), reverse=True)[:14]:
        bar = "#" * count
        print(f"    {date}  {C.GREEN}{bar}{C.RESET} {count}")
