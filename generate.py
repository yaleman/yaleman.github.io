from __future__ import annotations

import argparse
import json
import os
import urllib.error
import urllib.parse
import urllib.request
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from datetime import datetime, timezone
from html import escape
from pathlib import Path
from typing import TypeGuard

DEFAULT_USERNAME = "yaleman"
DEFAULT_OUTPUT = Path("site/index.html")
DEFAULT_STYLESHEET_HREF = "style.css"
DEFAULT_SCRIPT_SRC = "search.js"
GITHUB_API_ROOT = "https://api.github.com"


@dataclass(frozen=True)
class Repository:
    name: str
    html_url: str
    description: str
    language: str
    stargazers_count: int
    updated_at: str
    fork: bool
    archived: bool


def _read_str(data: Mapping[str, object], key: str, default: str = "") -> str:
    value = data.get(key, default)
    return value if isinstance(value, str) else default


def _read_int(data: Mapping[str, object], key: str, default: int = 0) -> int:
    value = data.get(key, default)
    return value if isinstance(value, int) else default


def _is_str_object_mapping(value: object) -> TypeGuard[Mapping[str, object]]:
    return isinstance(value, Mapping) and all(isinstance(key, str) for key in value)


def parse_repository(data: Mapping[str, object]) -> Repository | None:
    if data.get("private") is True:
        return None

    name = _read_str(data, "name").strip()
    html_url = _read_str(data, "html_url").strip()
    if not name or not html_url:
        return None

    description = _read_str(data, "description").strip()
    language = _read_str(data, "language").strip()
    stargazers_count = _read_int(data, "stargazers_count")
    updated_at = _read_str(data, "pushed_at") or _read_str(data, "updated_at")

    return Repository(
        name=name,
        html_url=html_url,
        description=description,
        language=language,
        stargazers_count=stargazers_count,
        updated_at=updated_at,
        fork=data.get("fork") is True,
        archived=data.get("archived") is True,
    )


def _build_repositories_url(username: str, *, page: int, per_page: int) -> str:
    query = urllib.parse.urlencode(
        {
            "type": "public",
            "sort": "updated",
            "direction": "desc",
            "per_page": per_page,
            "page": page,
        }
    )
    return f"{GITHUB_API_ROOT}/users/{urllib.parse.quote(username)}/repos?{query}"


def _fetch_repository_page(
    username: str, *, page: int, per_page: int, token: str | None
) -> list[object]:
    url = _build_repositories_url(username, page=page, per_page=per_page)
    headers: dict[str, str] = {
        "Accept": "application/vnd.github+json",
        "User-Agent": "yaleman-github-io-generator",
    }
    if token:
        headers["Authorization"] = f"Bearer {token}"

    request = urllib.request.Request(url=url, headers=headers)
    try:
        with urllib.request.urlopen(request, timeout=30) as response:
            if response.getcode() != 200:
                raise RuntimeError(
                    f"GitHub API returned status {response.getcode()} for {url}"
                )
            payload = response.read().decode("utf-8")
    except urllib.error.HTTPError as exc:
        raise RuntimeError(f"GitHub API HTTP error {exc.code}: {exc.reason}") from exc
    except urllib.error.URLError as exc:
        raise RuntimeError(f"Failed to reach GitHub API: {exc.reason}") from exc

    parsed: object = json.loads(payload)
    if not isinstance(parsed, list):
        raise RuntimeError("Unexpected GitHub API response shape; expected a list")
    return parsed


def fetch_public_repositories(
    username: str, *, token: str | None = None, per_page: int = 100
) -> list[Repository]:
    repositories: list[Repository] = []
    page = 1
    while True:
        page_data = _fetch_repository_page(
            username, page=page, per_page=per_page, token=token
        )
        if not page_data:
            break

        for item in page_data:
            if not _is_str_object_mapping(item):
                continue
            repository = parse_repository(item)
            if repository is not None:
                repositories.append(repository)

        if len(page_data) < per_page:
            break
        page += 1

    repositories.sort(
        key=lambda repo: (repo.updated_at, repo.name.casefold()),
        reverse=True,
    )
    return repositories


def _format_timestamp(timestamp: str) -> str:
    if not timestamp:
        return "Unknown"
    try:
        parsed = datetime.fromisoformat(timestamp.replace("Z", "+00:00"))
    except ValueError:
        return "Unknown"
    return parsed.strftime("%Y-%m-%d")


def _render_repository_card(repository: Repository) -> str:
    badges: list[str] = []
    if repository.fork:
        badges.append("Fork")
    if repository.archived:
        badges.append("Archived")
    badges_html = "".join(
        f'<span class="badge">{escape(badge)}</span>' for badge in badges
    )

    description = (
        escape(repository.description)
        if repository.description
        else "No description provided."
    )
    language = escape(repository.language) if repository.language else "Unknown"
    data_repo_name = escape(repository.name, quote=True)
    data_repo_language = escape(repository.language, quote=True)
    data_repo_description = escape(repository.description, quote=True)

    return f"""
    <article
      class="repo-card"
      data-repo-name="{data_repo_name}"
      data-repo-language="{data_repo_language}"
      data-repo-description="{data_repo_description}"
    >
      <div class="repo-card-top">
        <h2><a href="{escape(repository.html_url, quote=True)}">{escape(repository.name)}</a></h2>
        <div class="badges">{badges_html}</div>
      </div>
      <p class="repo-description">{description}</p>
      <div class="repo-meta">
        <span>Language: {language}</span>
        <span>Stars: {repository.stargazers_count}</span>
        <span>Updated: {_format_timestamp(repository.updated_at)}</span>
      </div>
    </article>
    """


def _render_repository_section(
    section_id: str, title: str, repositories: Sequence[Repository], empty_message: str
) -> str:
    cards = "\n".join(_render_repository_card(repository) for repository in repositories)
    list_content = cards
    if not list_content:
        list_content = f'<p class="section-empty">{escape(empty_message)}</p>'

    return f"""
    <section class="repo-section" id="{escape(section_id, quote=True)}">
      <h2 class="section-title">{escape(title)}</h2>
      <p class="section-count">Repositories: {len(repositories)}</p>
      <div class="repo-list">
        {list_content}
      </div>
    </section>
    """


def render_page(
    username: str,
    repositories: Sequence[Repository],
    stylesheet_href: str = DEFAULT_STYLESHEET_HREF,
    script_src: str = DEFAULT_SCRIPT_SRC,
) -> str:
    active_repositories = [repo for repo in repositories if not repo.archived]
    archived_repositories = [repo for repo in repositories if repo.archived]

    generated_at = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    escaped_username = escape(username)
    active_section = _render_repository_section(
        "active-repositories",
        "Active repositories",
        active_repositories,
        "No active repositories found.",
    )
    archived_section = _render_repository_section(
        "archived-repositories",
        "Archived repositories",
        archived_repositories,
        "No archived repositories found.",
    )

    return f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{escaped_username} repositories</title>
  <link rel="stylesheet" href="{escape(stylesheet_href, quote=True)}">
</head>
<body>
  <main>
    <header class="hero">
      <h1>{escaped_username}'s repositories</h1>
      <p class="subtitle">Public repositories: {len(repositories)}</p>
    </header>
    <section class="search-panel">
      <label for="repo-search">Search repositories</label>
      <input
        id="repo-search"
        name="repo-search"
        type="search"
        placeholder="Filter by name, language, or description"
        autocomplete="off"
      >
    </section>
    <p id="search-empty" class="search-empty" hidden>No repositories match your search.</p>
    {active_section}
    {archived_section}
    <footer>Generated {generated_at} from the GitHub REST API.</footer>
  </main>
  <script src="{escape(script_src, quote=True)}" defer></script>
</body>
</html>
"""


def write_page(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Generate site/index.html from a GitHub user's public repositories."
    )
    parser.add_argument(
        "--username",
        default=os.environ.get("GITHUB_USERNAME", DEFAULT_USERNAME),
        help="GitHub username to fetch (default: %(default)s or GITHUB_USERNAME).",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=DEFAULT_OUTPUT,
        help="Output HTML file path (default: %(default)s).",
    )
    parser.add_argument(
        "--token",
        default=os.environ.get("GITHUB_TOKEN"),
        help="Optional GitHub token (default: GITHUB_TOKEN).",
    )
    return parser.parse_args(argv)


def main(argv: Sequence[str] | None = None) -> int:
    args = parse_args(argv)
    repositories = fetch_public_repositories(args.username, token=args.token)
    html = render_page(args.username, repositories)
    write_page(args.output, html)
    print(f"Wrote {args.output} with {len(repositories)} repositories for {args.username}.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
