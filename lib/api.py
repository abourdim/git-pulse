"""GitHub REST API client."""
from __future__ import annotations

import subprocess
import sys

import requests


class GitHubAPI:
    BASE_URL = "https://api.github.com"

    def __init__(self, token: str):
        self.token = token
        self.headers = {
            "Authorization": f"token {token}",
            "Accept": "application/vnd.github.v3+json",
        }
        self.user = self._get_user()

    def _get_user(self) -> dict:
        r = requests.get(f"{self.BASE_URL}/user", headers=self.headers)
        if r.status_code != 200:
            from .colors import C
            from .i18n import t
            print(f"\n  {C.RED}x {t('failed')}: Authentication. Check your token.{C.RESET}")
            sys.exit(1)
        return r.json()

    @property
    def username(self) -> str:
        return self.user["login"]

    def list_repos(self, sort="updated", direction="desc", repo_type="all") -> list:
        repos, page = [], 1
        while True:
            r = requests.get(f"{self.BASE_URL}/user/repos", headers=self.headers,
                             params={"sort": sort, "direction": direction,
                                     "type": repo_type, "per_page": 100, "page": page})
            data = r.json()
            if not data:
                break
            repos.extend(data)
            page += 1
        return repos

    def get_repo(self, name: str) -> dict | None:
        r = requests.get(f"{self.BASE_URL}/repos/{self.username}/{name}", headers=self.headers)
        return r.json() if r.status_code == 200 else None

    def create_repo(self, name: str, description: str = "", private: bool = True, init: bool = True) -> tuple[dict, int]:
        r = requests.post(f"{self.BASE_URL}/user/repos", headers=self.headers,
                          json={"name": name, "description": description,
                                "private": private, "auto_init": init})
        return r.json(), r.status_code

    def delete_repo(self, name: str) -> int:
        r = requests.delete(f"{self.BASE_URL}/repos/{self.username}/{name}", headers=self.headers)
        return r.status_code

    def update_repo(self, name: str, **kwargs) -> tuple[dict, int]:
        r = requests.patch(f"{self.BASE_URL}/repos/{self.username}/{name}",
                           headers=self.headers, json=kwargs)
        return r.json(), r.status_code

    def list_branches(self, name: str) -> list:
        r = requests.get(f"{self.BASE_URL}/repos/{self.username}/{name}/branches", headers=self.headers)
        return r.json() if r.status_code == 200 else []

    def list_commits(self, name: str, count: int = 10) -> list:
        r = requests.get(f"{self.BASE_URL}/repos/{self.username}/{name}/commits",
                         headers=self.headers, params={"per_page": count})
        return r.json() if r.status_code == 200 else []

    def search_repos(self, query: str) -> list:
        r = requests.get(f"{self.BASE_URL}/search/repositories", headers=self.headers,
                         params={"q": f"user:{self.username} {query}", "per_page": 30})
        return r.json().get("items", []) if r.status_code == 200 else []

    def get_languages(self, name: str) -> dict:
        r = requests.get(f"{self.BASE_URL}/repos/{self.username}/{name}/languages", headers=self.headers)
        return r.json() if r.status_code == 200 else {}

    def get_pages(self, name: str) -> dict | None:
        r = requests.get(f"{self.BASE_URL}/repos/{self.username}/{name}/pages", headers=self.headers)
        return r.json() if r.status_code == 200 else None

    def disable_pages(self, name: str) -> int:
        r = requests.delete(f"{self.BASE_URL}/repos/{self.username}/{name}/pages", headers=self.headers)
        return r.status_code

    def enable_pages(self, name: str, branch: str = "main", path: str = "/") -> tuple[dict, int]:
        r = requests.post(f"{self.BASE_URL}/repos/{self.username}/{name}/pages",
                          headers=self.headers,
                          json={"source": {"branch": branch, "path": path}})
        return r.json() if r.status_code in (201, 409) else {}, r.status_code

    def squash_all_commits(self, name: str, message: str = "Initial commit") -> tuple[bool, str]:
        """Squash all commits into one by creating an orphan commit with the current tree."""
        base = f"{self.BASE_URL}/repos/{self.username}/{name}"
        repo = requests.get(base, headers=self.headers).json()
        branch = repo.get("default_branch", "main")
        ref = requests.get(f"{base}/git/ref/heads/{branch}", headers=self.headers)
        if ref.status_code != 200:
            return False, f"Branch '{branch}' not found"
        commit_sha = ref.json()["object"]["sha"]
        commit = requests.get(f"{base}/git/commits/{commit_sha}", headers=self.headers).json()
        tree_sha = commit["tree"]["sha"]
        new_commit = requests.post(f"{base}/git/commits", headers=self.headers,
                                   json={"message": message, "tree": tree_sha, "parents": []})
        if new_commit.status_code != 201:
            return False, new_commit.json().get("message", "Failed to create commit")
        new_sha = new_commit.json()["sha"]
        update = requests.patch(f"{base}/git/refs/heads/{branch}", headers=self.headers,
                                json={"sha": new_sha, "force": True})
        if update.status_code == 200:
            return True, new_sha
        return False, update.json().get("message", "Failed to update ref")

    def clone_repo(self, name: str, dest: str = ".") -> tuple[bool, str]:
        url = f"https://x-access-token:{self.token}@github.com/{self.username}/{name}.git"
        result = subprocess.run(["git", "clone", url], cwd=dest, capture_output=True, text=True)
        return result.returncode == 0, result.stderr

    def get_file_content(self, name: str, path: str) -> dict:
        r = requests.get(f"{self.BASE_URL}/repos/{self.username}/{name}/contents/{path}",
                         headers=self.headers, timeout=10)
        return r.json() if r.status_code == 200 else {}

    def create_or_update_file(self, name, path, content, message, sha=None):
        import base64
        data = {"message": message, "content": base64.b64encode(content.encode()).decode()}
        if sha:
            data["sha"] = sha
        r = requests.put(f"{self.BASE_URL}/repos/{self.username}/{name}/contents/{path}",
                         headers=self.headers, json=data, timeout=15)
        return r.status_code in (200, 201), r.json() if r.status_code in (200, 201) else {}

    def delete_file(self, name, path, message, sha):
        r = requests.delete(f"{self.BASE_URL}/repos/{self.username}/{name}/contents/{path}",
                            headers=self.headers, json={"message": message, "sha": sha}, timeout=10)
        return r.status_code == 200, r.json() if r.status_code == 200 else {}


class PublicAPI:
    """Read-only GitHub API client using just a username (no token, public repos only)."""
    BASE_URL = "https://api.github.com"

    def __init__(self, username: str):
        self._username = username
        self.headers = {"Accept": "application/vnd.github.v3+json"}
        self.user = self._get_user()

    def _get_user(self) -> dict:
        r = requests.get(f"{self.BASE_URL}/users/{self._username}", headers=self.headers)
        if r.status_code != 200:
            raise ValueError(f"GitHub user '{self._username}' not found")
        return r.json()

    @property
    def username(self) -> str:
        return self.user["login"]

    def list_repos(self, sort="updated", direction="desc", repo_type="all") -> list:
        repos, page = [], 1
        while True:
            r = requests.get(f"{self.BASE_URL}/users/{self._username}/repos",
                             headers=self.headers,
                             params={"sort": sort, "direction": direction,
                                     "type": "public", "per_page": 100, "page": page})
            data = r.json()
            if not data or not isinstance(data, list):
                break
            repos.extend(data)
            page += 1
        return repos

    def get_repo(self, name: str) -> dict | None:
        r = requests.get(f"{self.BASE_URL}/repos/{self._username}/{name}", headers=self.headers)
        return r.json() if r.status_code == 200 else None

    def search_repos(self, query: str) -> list:
        r = requests.get(f"{self.BASE_URL}/search/repositories", headers=self.headers,
                         params={"q": f"user:{self._username} {query}", "per_page": 30})
        return r.json().get("items", []) if r.status_code == 200 else []

    def list_branches(self, name: str) -> list:
        r = requests.get(f"{self.BASE_URL}/repos/{self._username}/{name}/branches", headers=self.headers)
        return r.json() if r.status_code == 200 else []

    def list_commits(self, name: str, count: int = 10) -> list:
        r = requests.get(f"{self.BASE_URL}/repos/{self._username}/{name}/commits",
                         headers=self.headers, params={"per_page": count})
        return r.json() if r.status_code == 200 else []

    def get_languages(self, name: str) -> dict:
        r = requests.get(f"{self.BASE_URL}/repos/{self._username}/{name}/languages", headers=self.headers)
        return r.json() if r.status_code == 200 else {}

    def get_file_content(self, name: str, path: str) -> dict:
        r = requests.get(f"{self.BASE_URL}/repos/{self._username}/{name}/contents/{path}",
                         headers=self.headers, timeout=10)
        return r.json() if r.status_code == 200 else {}

    def clone_repo(self, name: str, dest: str = ".") -> tuple[bool, str]:
        import subprocess
        url = f"https://github.com/{self._username}/{name}.git"
        result = subprocess.run(["git", "clone", url], cwd=dest, capture_output=True, text=True)
        return result.returncode == 0, result.stderr

    # Write operations — not supported without a token
    def create_repo(self, *a, **kw):
        raise PermissionError("Cannot create repos without a token")

    def delete_repo(self, *a, **kw):
        raise PermissionError("Cannot delete repos without a token")

    def update_repo(self, *a, **kw):
        raise PermissionError("Cannot update repos without a token")

    def create_or_update_file(self, *a, **kw):
        raise PermissionError("Cannot modify files without a token")

    def delete_file(self, *a, **kw):
        raise PermissionError("Cannot delete files without a token")
