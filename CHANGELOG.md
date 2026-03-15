# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.7.0] - 2026-02-27

### Added
- Dark mode with OS detection and manual toggle (persisted in localStorage)
- UnoCSS utility-first CSS framework replacing hand-written CSS
- Inter font served locally (no external Google Fonts requests)
- Color-coded status badges for job states (failed, started, queued, finished, deferred, scheduled)
- SVG icon buttons for delete, requeue, and pagination actions
- Global autorefresh toggle in header (replaces per-page checkboxes)
- Active navigation indicator with underline styling
- Inline table header filters on jobs page (state and queue name)
- Development documentation for UnoCSS workflow in README
- CLAUDE.md with project guidance for AI-assisted development

### Changed
- Replaced jQuery with vanilla JavaScript across all templates
- Redesigned tables with minimal striped style, stronger headers, and row borders
- Modernized button design from solid/outlined to ghost/subtle style
- Moved autorefresh state to localStorage for cross-page persistence
- Sticky header with frosted glass effect
- Sticky footer using flexbox layout

### Removed
- jQuery CDN dependency
- Google Fonts external requests (replaced with local font files)
- Legacy `main.css` (replaced by generated `uno.css` + `custom.css`)
- Per-page autorefresh checkboxes
- Page title headings (active nav link indicates current page)
- Gray card wrapper around page content

### Fixed
- Autorefresh guard blocking manual filter and pagination changes
- `documenr` typo in queues.html error notification
- Variable name mismatch in jobs.html error notification
- `objectName`/`object_name` mismatch in export.html error handler
- Duplicate table cells from broken worker queues loop in workers.html
- Unclosed `<span>` tag in footer.html
- Nested DOCTYPE/html/head/body tags in all child templates
- Filter div incorrectly nested inside table element in jobs.html
- Version mismatch between pyproject.toml and dashboard UI

## [0.6.1] - 2024-12-01

### Added
- CLI entry point (`rq-dashboard-fast` command)
- Standalone mode with `--redis-url`, `--host`, `--port`, `--prefix` flags
- Environment variable support (`REDIS_URL`, `FASTAPI_HOST`, `FASTAPI_PORT`)

## [0.6.0] - 2024-10-01

### Added
- Data export (CSV/JSON) for queues, workers, and jobs
- Export page in dashboard UI

## [0.5.0] - 2024-08-01

### Added
- Pagination on jobs page
- Job requeue functionality

## [0.4.0] - 2024-06-01

### Added
- Workers monitoring page
- Auto-refresh for queues, jobs, and workers pages

## [0.3.0] - 2024-04-01

### Added
- Job detail view with Pygments syntax highlighting for tracebacks
- Job deletion

## [0.2.0] - 2024-03-01

### Added
- Jobs page with state filtering
- Queue name filtering

## [0.1.0] - 2024-02-01

### Added
- Initial release
- FastAPI-based dashboard mountable as sub-application
- Queue monitoring with job count by status
- Docker image support (amd64/arm64)
- PyPI package distribution
