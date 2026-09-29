from __future__ import annotations

import json
import os
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Dict

import requests

from src.config.settings import CACHE_DIR
from src.models.resume import CandidateProfile

CACHE_DIR.mkdir(parents=True, exist_ok=True)
GITHUB_CACHE_FILE = CACHE_DIR / "github_cache.json"
CACHE_VERSION = 2
ACTIVITY_WINDOW_DAYS = 180


def _load_cache() -> Dict[str, Any]:
    if not GITHUB_CACHE_FILE.exists():
        return {}
    try:
        return json.loads(GITHUB_CACHE_FILE.read_text(encoding="utf-8"))
    except Exception:
        return {}


def _save_cache(cache: Dict[str, Any]) -> None:
    GITHUB_CACHE_FILE.write_text(json.dumps(cache, indent=2), encoding="utf-8")


def _is_recently_updated(timestamp: str, now: datetime | None = None) -> bool:
    if not timestamp:
        return False
    try:
        updated_at = datetime.fromisoformat(timestamp.replace("Z", "+00:00"))
    except ValueError:
        return False
    if updated_at.tzinfo is None:
        updated_at = updated_at.replace(tzinfo=timezone.utc)
    current_time = now or datetime.now(timezone.utc)
    if current_time.tzinfo is None:
        current_time = current_time.replace(tzinfo=timezone.utc)
    return current_time - timedelta(days=ACTIVITY_WINDOW_DAYS) <= updated_at <= current_time


def enrich_candidate_github(candidate: CandidateProfile) -> Dict[str, Any]:
    username = candidate.github_username or (candidate.github_url.rstrip("/").split("github.com/")[-1] if candidate.github_url else "")
    if not username:
        return {"score": 0, "status": "missing", "summary": "GitHub not provided.", "username": ""}

    cache = _load_cache()
    cached = cache.get(username, {})
    if isinstance(cached, dict) and cached.get("version") == CACHE_VERSION and isinstance(cached.get("value"), dict):
        return cached["value"]

    token = os.getenv("GITHUB_TOKEN")
    headers = {"User-Agent": "Kasparro-Resume-Screening/1.0", "Accept": "application/vnd.github+json"}
    if token:
        headers["Authorization"] = f"token {token}"

    try:
        user_response = requests.get(f"https://api.github.com/users/{username}", headers=headers, timeout=12)
        user_response.raise_for_status()
        data = user_response.json()

        repos_response = requests.get(f"https://api.github.com/users/{username}/repos?per_page=10&sort=updated", headers=headers, timeout=12)
        repos_response.raise_for_status()
        repos = repos_response.json()

        recent_activity = 0
        maintained = 0
        python_repos = 0
        ai_repos = 0
        for repo in repos[:10]:
            name = (repo.get("name") or "").lower()
            description = (repo.get("description") or "").lower()
            updated = repo.get("pushed_at") or repo.get("updated_at") or ""
            if _is_recently_updated(updated):
                recent_activity += 1
            if repo.get("language") == "Python" or "python" in description or "python" in name:
                python_repos += 1
            if any(keyword in (name + " " + description) for keyword in ["rag", "llm", "agent", "ai", "ml", "gpt", "vector", "langchain", "transformer"]):
                ai_repos += 1
            if repo.get("archived") is False:
                maintained += 1

        activity_score = min(5, recent_activity)
        repository_score = min(5, min(2, maintained) + min(2, python_repos) + min(1, ai_repos))
        score = activity_score + repository_score
        summary = (
            f"GitHub user {username}: {recent_activity} repositories pushed within {ACTIVITY_WINDOW_DAYS} days; "
            f"{python_repos} Python repos and {ai_repos} AI-related repos detected."
        )
        result = {"score": score, "status": "success", "summary": summary, "username": username}
        cache[username] = {"version": CACHE_VERSION, "value": result}
        _save_cache(cache)
        return result
    except Exception as exc:
        result = {"score": 0, "status": "failed", "summary": f"GitHub API failed for {username}: {exc}", "username": username}
        cache[username] = {"version": CACHE_VERSION, "value": result}
        _save_cache(cache)
        return result
