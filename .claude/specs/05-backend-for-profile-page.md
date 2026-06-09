# Spec: Backend for Profile Page

## Overview
This feature replaces the hardcoded dummy data in the `/profile` route with real database queries. The profile page UI was established in Step 04 using static Python dicts; this step wires it up to the actual `users` and `expenses` tables so the logged-in user sees their own name, email, transaction history, spending stats, and category breakdown. No new routes or templates are created — only the data flowing into `profile.html` changes.

## Depends on
- Step 01 — Database Setup (`get_db()`, `users` and `expenses` tables must exist)
- Step 02 — Registration (users must be creatable and stored in the DB)
- Step 03 — Login and Logout (`session['user_id']` must be set on login)
- Step 04 — Profile Page Design (`templates/profile.html` must exist with the four-sections layout)

## Routes
No new routes. The existing `GET /profile` route is modified to query the database instead of returning hardcoded data.

## Database changes
No database changes. The `users` and `expenses` tables already have all required columns.

## Templates
- **Modify:** `templates/profile.html` 
  — ensure the template renders correctly with live data. The `member_since` variable will now be derived from `users.created_at` (formatted as "Month, Year"). 
  - Amounts must be rendered with $ sign (US Dollar)
  - All four dynamic sections (user info, summary stats, transaction list, category breakdown) are already present - no structural changes needed, only the Jinja variables they consude are now real.
  - Verify category badge CSS classes still work for all seven categories.

## Files to change
- `app.py` — replace hardcoded dicts in the `/profile` route with real DB queries:
  - Fetch the logged-in user row from `users` by `session['user_id']`
  - Fetch all expenses for that user ordered by `date DESC`
  - Compute `total_spent` (SUM of amount), `transaction_count` (COUNT), and `top_category` (category with highest total amount) via SQL aggregation
  - Build the `categories` list via a GROUP BY query returning name, count, total, and percentage
  - Format `member_since` from `users.created_at` using Python's `datetime.strptime` / `strftime`

- `templates/profile.html` - Confirm $ symbol is used for all currency display.

## Files to create
- `database/queries.py` — pure query helpers (no Flask imports) one function per data concern:
  - `get_user_by_id(user_id)` — returns a dict with name, email, member_since by primary key
  - `get_recent_transactions(user_id, limit=10)` — returns list of dicts, each with date, description, category, amount ordered by `date DESC`
  - `get_summary_spending_stats(user_id)` — returns a dict with `total_spent`, `transaction_count`, `top_category`
  - `get_category_breakdown(user_id)` — returns a list of dicts with `name`, `count`, `total`, `pct`

## New dependencies
No new dependencies.

## Rules for implementation
- No SQLAlchemy or ORMs — raw sqlite3 via `get_db()` only
- Parameterised queries only — never f-strings or `.format()` in SQL
- Foreign keys PRAGMA must be enabled on every connection (already done in get_db())
- Passwords hashed with werkzeug (no changes to auth in this step)
- Use CSS variables — never hardcode hex values
- No inline styles
- All templates extend `base.html`
- All Query helper functions live in `database/queries.py`, not in `app.py` and must call get_db() internally and close the connection before returning
- The `/profile` route function must only: authenticate the user, call DB helpers, format data, and render the template — no raw SQL in `app.py`
- If the user has no expenses, the page must render gracefully (zero totals, empty table, no crashes)
- `pct` in the category breakdown must be calculated as integer percentage of total spend (0–100); round to nearest integer
- Currency must always display $ - never ₹ or £
- `member_since` must be formatted as "Month, Year" (e.g. "January, 2026") using Python datetime — not raw ISO string
- `initials` must be derived from the user's name at runtime (first letter of each word, up to 2 letters, uppercased)

## Tests to write

### Unit tests
File: `tests/test_backend_connection.py`

| Function | Input | Expected output |
|---|---|---|
| `get_user_by_id` | valid `user_id` | dict with correct `name`, `email`, `member_since` |
| `get_user_by_id` | non-existent id | `None` |
| `get_summary_spending_stats` | `user_id` with expenses | correct `total_spent`, `transaction_count`, `top_category` |
| `get_summary_spending_stats` | `user_id` with no expenses | `{"total_spent": 0, "transaction_count": 0, "top_category": "—"}` |
| `get_recent_transactions` | `user_id` with expenses | list ordered newest-first, each item has `date`, `description`, `category`, `amount` |
| `get_recent_transactions` | `user_id` with no expenses | empty list |
| `get_category_breakdown` | `user_id` with expenses | list ordered by `amount` desc; `pct` values are integers summing to 100 |
| `get_category_breakdown` | `user_id` with no expenses | empty list |

### Route tests
`GET /profile` — unauthenticated:
- Redirects to `/login` (302)

`GET /profile` — authenticated as seed user:
- Returns 200
- Response contains the seed user's name ("Demo User")
- Response contains the seed user's email ("demo@spendly.com")
- Response contains $ symbol
- `total_spent` matches sum of all seed expenses (346.24)
- `transaction_count` is 8
- `top_category` is "Bills" (highest single-category total)
- Transaction list appears in newest-first order
- Category breakdown contains all 7 categories

## Definition of done
- [ ] Visiting `/profile` while logged in shows the real logged-in user's name and email (not "Alex Rivera")
- [ ] `member_since` on the profile page reflects the actual `created_at` value from the `users` table
- [ ] The transaction history table shows the real expenses from the `expenses` table for that user
- [ ] The transaction history is ordered most-recent first
- [ ] The summary stats (total spent, transaction count, top category) are computed from real DB data
- [ ] The category breakdown reflects the real spending distribution for the logged-in user
- [ ] A user with zero expenses sees the profile page without errors (empty table, zero stats)
- [ ] All DB queries are parameterised — no string interpolation in SQL
- [ ] All SQL helper functions are in `database/queries.py`, not inline in `app.py`
- [ ] Logging in as the seed user (demo@spendly.com / demo123) shows "Demo User" and "demo@spendly.com" on the profile page — not the hardcoded strings
- [ ] Total spent displayed on the profile page equals ₹346.24
- [ ] Transaction count displayed is 8
- [ ] Top category displayed is "Bills"
- [ ] Transaction list shows 8 rows ordered newest date first
- [ ] Category breakdown shows 7 categories with percentages that add up to 100 %
- [ ] All amounts on the page display the ₹ symbol
- [ ] Registering a brand-new user and visiting `/profile` shows $0.00 total spent, 0 transactions, and an empty category breakdown — no errors
- [ ] All existing tests continue to pass (`pytest`)
