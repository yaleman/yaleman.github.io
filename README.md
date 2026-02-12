# yaleman.github.io

This repo builds a simple static page that lists public GitHub repositories.

## How it works

1. `generate.py` calls the GitHub REST API for a username.
2. It writes `site/index.html` with:
   - active repos first
   - archived repos in a section at the end
3. The page uses static assets in `site/`:
   - `site/style.css`
   - `site/search.js`

The search box filters in real time by:
- repository name
- language
- description

## Run it locally

Generate the page:

```bash
uv run python generate.py --username yaleman --output site/index.html
```

Optional token for higher API limits:

```bash
GITHUB_TOKEN=your_token uv run python generate.py --username yaleman --output site/index.html
```

## Checks

Run all checks:

```bash
just check
```

Run tests:

```bash
just test
```

## Publishing

GitHub Actions workflow: `.github/workflows/publish-site.yml`

It:
- runs daily at 06:00 AEST (UTC+10)
- can also run manually
- generates the page first
- only deploys if generation succeeds
