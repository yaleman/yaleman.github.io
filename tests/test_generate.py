from __future__ import annotations

from generate import (
    SEARCH_SCRIPT_CONTENT,
    STYLESHEET_CONTENT,
    Repository,
    parse_repository,
    render_page,
)


def test_parse_repository_skips_private_repos() -> None:
    payload: dict[str, object] = {
        "private": True,
        "name": "hidden",
        "html_url": "https://example.invalid/hidden",
    }

    assert parse_repository(payload) is None


def test_parse_repository_handles_missing_optional_fields() -> None:
    payload: dict[str, object] = {
        "private": False,
        "name": "public-repo",
        "html_url": "https://github.com/example/public-repo",
        "description": None,
        "language": None,
        "stargazers_count": 3,
        "pushed_at": "2026-02-10T12:00:00Z",
    }

    repository = parse_repository(payload)
    assert repository is not None
    assert repository.description == ""
    assert repository.language == ""
    assert repository.stargazers_count == 3
    assert repository.updated_at == "2026-02-10T12:00:00Z"


def test_render_page_escapes_html() -> None:
    repositories = [
        Repository(
            name="<repo>",
            html_url="https://github.com/example/repo?x=<script>",
            description="<script>alert(1)</script>",
            language="Python",
            stargazers_count=5,
            updated_at="2026-01-01T12:30:00Z",
            fork=False,
            archived=False,
        )
    ]

    page = render_page(
        "test-user",
        repositories,
        stylesheet_href="assets/style.css",
        script_src="assets/search.js",
    )
    assert "Public repositories: 1" in page
    assert '<link rel="stylesheet" href="assets/style.css">' in page
    assert '<script src="assets/search.js" defer></script>' in page
    assert "<body>" in page
    assert "<style>" not in page
    assert "&lt;repo&gt;" in page
    assert "<script>" not in page
    assert "&lt;script&gt;alert(1)&lt;/script&gt;" in page
    assert 'data-repo-name="&lt;repo&gt;"' in page
    assert 'data-repo-description="&lt;script&gt;alert(1)&lt;/script&gt;"' in page


def test_render_page_empty_state() -> None:
    page = render_page("test-user", [])
    assert "No active repositories found." in page
    assert "No archived repositories found." in page


def test_render_page_archived_repos_in_trailing_section() -> None:
    repositories = [
        Repository(
            name="active-repo",
            html_url="https://github.com/example/active-repo",
            description="normal",
            language="Python",
            stargazers_count=1,
            updated_at="2026-02-01T00:00:00Z",
            fork=False,
            archived=False,
        ),
        Repository(
            name="archived-repo",
            html_url="https://github.com/example/archived-repo",
            description="old",
            language="Rust",
            stargazers_count=2,
            updated_at="2026-01-01T00:00:00Z",
            fork=False,
            archived=True,
        ),
    ]

    page = render_page("test-user", repositories)
    active_heading = page.index("Active repositories")
    archived_heading = page.index("Archived repositories")
    active_repo = page.index(">active-repo<")
    archived_repo = page.index(">archived-repo<")

    assert active_heading < archived_heading
    assert active_heading < active_repo < archived_heading
    assert archived_heading < archived_repo


def test_asset_content_has_expected_theme_tokens() -> None:
    assert "--bg-start: #f2eaff;" in STYLESHEET_CONTENT
    assert "radial-gradient(circle at 0% 0%" in STYLESHEET_CONTENT
    assert "repo-search" in SEARCH_SCRIPT_CONTENT
    assert "dataset.repoLanguage" in SEARCH_SCRIPT_CONTENT
