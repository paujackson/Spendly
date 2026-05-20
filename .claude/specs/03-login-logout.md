# Spec: Login and Logout

## Overview
Implement user login and logout so registered users can authenticate with Spendly. The `/login` route currently renders the form but does not process submissions. This step wires up `POST /login`: validate credentials against the database, start a Flask session on success, and redirect to the profile page stub. The `/logout` route clears the session and redirects to the landing page. Together these two routes establish the session layer that all protected features (profile, expenses) will depend on. After this step, the app can distinguish logged-in users from guests, which is a prerequisite for all expense features.

## Depends on
- Step 01 — Database Setup (`get_db()`, `users` table must exist)
- Step 02 — Registration (users must be able to exist in the DB with hashed passwords)

## Routes
- `POST /login` — validate email/password, create session, redirect to `/profile` — public
- `POST /logout` (change from GET) — clear session, redirect to `/` — logged-in (no hard enforcement yet, but session is cleared regardless)

## Database changes
No database changes.

## Templates
- **Modify:** `templates/login.html` — add inline error display using a Jinja2 `{{ error }}` variable for invalid credentials or missing fields
- **Modify:** `templates/base.html` — update the logout link/button to point to `url_for('logout')` if not already using it; no structural changes needed

## Files to change
- `app.py` — add `POST` to `/login` route decorator and implement handler; change `/logout` from stub to a working session-clearing route; add `secret_key` to `app.config`; add `session` to Flask imports

## Files to create
No new files.

## New dependencies
No new dependencies. `flask.session` is part of Flask.

## Rules for implementation
- No SQLAlchemy or ORMs — raw SQL with `get_db()` only
- Parameterised queries only — never f-strings in SQL
- Passwords verified with `werkzeug.security.check_password_hash`
- Use CSS variables — never hardcode hex values
- All templates extend `base.html`
- `app.secret_key` must be set before sessions can be used — use a hardcoded dev string for now (e.g. `"spendly-dev-secret"`)
- On login success, store `session['user_id']` and `session['user_name']`
- On any login failure, re-render `login.html` with a **generic** error message ("Invalid email or password") — do not reveal whether the email exists
- Use `abort()` for unexpected server errors, not bare string returns
- `/logout` must call `session.clear()` and redirect to `url_for('landing')`

## Server-side validation (login)

| Field | Rule |
|---|---|
| `email` | Required; non-empty after strip |
| `password` | Required; non-empty |
| credentials | Email must exist in DB and `check_password_hash` must return `True`; use the same generic error for both failure modes |

## Definition of done
- [ ] `GET /login` still renders the login form correctly
- [ ] Submitting valid credentials sets `session['user_id']` and redirects to `/profile`
- [ ] Submitting a wrong password re-renders login with a generic error (no user enumeration)
- [ ] Submitting an unregistered email re-renders login with the same generic error
- [ ] Submitting with empty fields re-renders login with an error
- [ ] Visiting `/logout` clears the session and redirects to the landing page `/`
- [ ] After logout, `session.get('user_id')` is `None`
- [ ] All existing tests continue to pass (`pytest`)
