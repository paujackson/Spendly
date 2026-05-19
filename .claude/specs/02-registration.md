# Spec: Registration

## Overview
Implement user registration so new visitors can create a Spendly account. The `/register` route currently renders the form but does not process submissions. This step wires up the `POST /register` handler: validate the form fields, check for duplicate emails, hash the password, inserts the new user into the `users` table. On success the user is shown with a success message and then redirected to the login page. It is the first step that writes user data to the database and the entry point for all authenticated features that follow.

## Depends on
- Step 01 — Database Setup (`get_db()`, `init_db()`, and the `users` table must exist)

## Routes
- `POST /register` — process the registration form, create user, redirect to `/login` — public

## Database changes
No database changes. The `users` table already exists with the correct schema:
- `id` INTEGER PRIMARY KEY AUTOINCREMENT
- `name` TEXT NOT NULL
- `email` TEXT UNIQUE NOT NULL
- `password_hash` TEXT NOT NULL
- `created_at` TIMESTAMP DEFAULT CURRENT_TIMESTAMP

## Templates
- Modify: `templates/register.html` — add inline error display for validation failures (duplicate email, missing fields, password mismatch). Use Jinja2 `{{ error }}` variable passed from the route.

## Files to change
- `app.py` — add `POST` to the `/register` route decorator; implement the POST handler logic

## Files to create
No new files.

## New dependencies
No new dependencies. `werkzeug.security` is already available via Flask.

## Server-side validation
All validation runs in the POST handler before any DB write. On failure, re-render `register.html` with an `error` variable — never redirect.

| Field | Rule |
|---|---|
| `name` | Required; 1–100 characters after stripping whitespace |
| `email` | Required; must contain `@` and a `.` after it; max 254 characters |
| `password` | Required; minimum 8 characters |
| `confirm_password` | Must match `password` exactly |
| `email` (DB) | Must not already exist in the `users` table — return a user-friendly "Email already registered" message |

Validation order: blank-field checks first, format checks second, password-match third, DB uniqueness last (avoid unnecessary DB hits when earlier checks fail).

## Rules for implementation
- No SQLAlchemy or ORMs — raw SQL with `get_db()` only
- Parameterised queries only — never f-strings in SQL
- Passwords hashed with `werkzeug.security.generate_password_hash` before inserting
- Use CSS variables — never hardcode hex values
- All templates extend `base.html`
- On any validation failure, re-render `register.html` with a clear `error` message — do not crash or redirect
- On success, redirect to `/login` using `url_for('login')`
- Use `abort()` for unexpected server errors, not bare string returns
- Route function has one responsibility: validate input, write to DB, redirect or re-render

## Definition of done
- [ ] Submitting the form with valid data creates a new row in the `users` table
- [ ] The stored password is a hash, not the plaintext value
- [ ] Submitting with an already-registered email re-renders the form with an error message
- [ ] Submitting with mismatched passwords re-renders the form with an error message
- [ ] Submitting with any empty required field re-renders the form with an error message
- [ ] Successful registration redirects the browser to `/login`
- [ ] The `/register` page still loads correctly via `GET /register`
- [ ] All existing tests continue to pass (`pytest`)
