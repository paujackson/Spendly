# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Commands

```bash
# Activate the virtual environment (Windows)
python -m venv .venv
.venv\Scripts\Activate.ps1

# Install dependencies
pip install -r requirements.txt
```

# Run the development server (port 5001)
python app.py

# Run all tests
pytest

# Run a single test file
pytest tests/test_auth.py

# Run a specific test by name
pytest -k "test_name"

# Run tests with output visible
pytest -s

## Architecture

This is **Spendly**, a Flask + SQLite expense tracker app. It is a step-by-step student project — many routes are stubs that are filled in incrementally.

spendly/
├── app.py              # All routes — single file, no blueprints
├── database/
│   └── db.py           # SQLite helpers: get_db(), init_db(), seed_db()
├── templates/
│   ├── base.html       # Shared layout — all templates must extend this
│   └── *.html          # One template per page
├── static/
│   ├── css/
│   │   ├── style.css       # Global styles
│   │   
│   └── js/
│       └── main.js         # Vanilla JS only
└── requirements.txt

**`app.py`** — single-file Flask app. All routes live here. Fully implemented routes: `/`, `/register`, `/login`, `/terms`, `/privacy`. Stub routes (return placeholder strings): `/logout`, `/profile`, `/expenses/add`, `/expenses/<id>/edit`, `/expenses/<id>/delete`.

**`database/db.py`** — student-written module that must export three functions:
- `get_db()` — returns a SQLite connection with `row_factory` set and foreign keys enabled
- `init_db()` — creates all tables using `CREATE TABLE IF NOT EXISTS`
- `seed_db()` — inserts sample data

The SQLite database file is `expense_tracker.db` (gitignored). There is no ORM — raw SQL only.

**`templates/`** — Jinja2 templates. All pages extend `base.html`, which provides the shared navbar, footer, and loads `style.css` and `main.js`. Page-specific scripts go in `{% block scripts %}`.

**`static/css/style.css`** — single stylesheet using CSS custom properties defined in `:root`. Fonts are DM Serif Display (headings, `--font-display`) and DM Sans (body, `--font-body`) loaded from Google Fonts.

**`static/js/main.js`** — vanilla JS only. No JS frameworks or libraries. Page-specific inline scripts belong in `{% block scripts %}` in the relevant template.

## Code style

- Python: PEP 8, snake_case for all variables and functions
- Templates: Jinja2 with url_for() for every internal link — never hardcode URLs
- Route functions: one responsibility only — fetch data, render template, done
- DB queries: always use parameterized queries (? placeholders) — never f-strings in SQL
- Error handling: use abort() for HTTP errors, not bare return "error string"

## Tech constraints

**`Flask only`** — no FastAPI, no Django, no other web frameworks
**`SQLite only`** — no PostgreSQL, no SQLAlchemy ORM, no external DB
**`Vanilla JS only`** — no React, no jQuery, no npm packages
**`No new pip packages`** — work within requirements.txt as-is unless explicitly told otherwise
**`Python 3.10+ assumed`** — f-strings and match statements are fine

## Subagent Policy
- Always use a builtin explore subagent for codebase exploration before implementing any new feature
- Always use a subagent to verify test results after any implementation
- When asked to plan, delegate codebase research to a subagent before presenting the plan
- Always use a builtin plan subagent in plan mode

## Implemented vs stub routes

| Route | Status |
|---|---|
| `GET /` | Implemented — renders `landing.html` |
| `GET /register` | Implemented — renders `register.html` |
| `GET /login` | Implemented — renders `login.html` |
| `GET /logout` | Stub — Step 3 |
| `GET /profile` | Stub — Step 4 |
| `GET /expenses/add` | Stub — Step 7 |
| `GET /expenses/<id>/edit` | Stub — Step 8 |
| `GET /expenses/<id>/delete` | Stub — Step 9 |

**Do not implement a stub route unless the active task explicitly targets that step.**


## Key conventions

- The app runs on **port 5001** (`app.run(debug=True, port=5001)`), not Flask's default 5000.
- No JS frameworks — vanilla JS only.
- Authentication uses Flask sessions (not yet implemented in stubs).
- Passwords must be hashed with `werkzeug.security` (`generate_password_hash` / `check_password_hash`).
- All new pages must extend `base.html` and match the existing warm-paper design system (CSS variables in `:root`).

## Warnings and things to avoid

- **Never use raw string returns for stub routes** once a step is implemented — always render a template
- **Never hardcode URLs** in templates — always use `url_for()`
- **Never put DB logic in route functions** — it belongs in `database/db.py`
- **Never install new packages** mid-feature without flagging it — keep `requirements.txt` in sync
- **Never use JS frameworks** — the frontend is intentionally vanilla
- **`database/db.py` is currently empty** — do not assume helpers exist until the step that implements them
- **FK enforcement is manual** — SQLite foreign keys are off by default; `get_db()` must run `PRAGMA foreign_keys = ON` on every connection
- The app runs on **port 5001**, not the Flask default 5000 — don't change this