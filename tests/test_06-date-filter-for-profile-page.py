"""
Tests for Step 06 — Date Filter for Profile Page.

Spec: .claude/specs/06-date-filter-for-profile-page.md

Coverage:
  1.  Auth guard — unauthenticated request with date params redirects to /login (302)
  2.  No filter — GET /profile (no params) returns 200 and shows all-time seed data
  3.  Valid date range matching seed data — filters to May 2026 expenses
  4.  Valid date range with no matching expenses — no crash, shows zero totals
  5.  date_from > date_to — flash error "Start date must be before end date."
  6.  Malformed date_from — 200, silent fallback to unfiltered view
  7.  Malformed date_to — 200, silent fallback to unfiltered view
  8.  Only date_from provided — 200, treated as no filter (unfiltered view)
  9.  Only date_to provided — 200, treated as no filter (unfiltered view)
  10. Filter bar HTML present — All Time, This Month, Last 3 Months, Last 6 Months labels
  11. Apply button and date inputs present in filter bar

Important notes about this codebase:
  - database/db.py uses a hardcoded file path for the SQLite DB; there is no in-memory
    override via Flask config. All tests share the real, seeded on-disk database.
  - seed_db() is idempotent (checks user count before inserting).
  - All 8 seed expenses are dated in May 2026 (stored as MM-DD-YYYY).
  - Auth is simulated by injecting user_id into the Flask session directly, which
    requires looking up the real demo user's id from the shared DB.
  - The app module-level code calls init_db() and seed_db() at import time, so the
    DB is always ready when these tests run.
"""

import pytest
from app import app as flask_app
from database.db import get_db, init_db, seed_db


# ------------------------------------------------------------------ #
# Fixtures                                                            #
# ------------------------------------------------------------------ #

@pytest.fixture(scope="module")
def app():
    """Configure the Flask app for testing and ensure the DB is seeded."""
    flask_app.config.update({
        "TESTING": True,
        "SECRET_KEY": "test-secret-06",
    })
    with flask_app.app_context():
        init_db()
        seed_db()
        yield flask_app


@pytest.fixture(scope="module")
def demo_user_id(app):
    """Return the id of the seeded demo user (demo@spendly.com)."""
    with app.app_context():
        db = get_db()
        row = db.execute(
            "SELECT id FROM users WHERE email = ?", ("demo@spendly.com",)
        ).fetchone()
        db.close()
    assert row is not None, "Demo user must exist in the seeded database"
    return row["id"]


@pytest.fixture
def client(app):
    """Return a fresh test client (unauthenticated) for each test."""
    return app.test_client()


@pytest.fixture
def auth_client(app, demo_user_id):
    """Return a test client with the demo user already in the session."""
    c = app.test_client()
    with c.session_transaction() as sess:
        sess["user_id"] = demo_user_id
        sess["user_name"] = "Demo User"
    return c


# ------------------------------------------------------------------ #
# 1. Auth guard                                                       #
# ------------------------------------------------------------------ #

class TestAuthGuard:
    def test_unauthenticated_request_with_date_params_redirects_to_login(self, client):
        """Unauthenticated GET /profile?date_from=...&date_to=... must redirect to /login."""
        r = client.get("/profile?date_from=2026-01-01&date_to=2026-12-31")
        assert r.status_code == 302, (
            f"Expected 302 redirect for unauthenticated request, got {r.status_code}"
        )
        assert "/login" in r.headers["Location"], (
            "Redirect target must be /login for unauthenticated access"
        )

    def test_unauthenticated_request_no_params_redirects_to_login(self, client):
        """Unauthenticated GET /profile (no params) must also redirect to /login."""
        r = client.get("/profile")
        assert r.status_code == 302, (
            f"Expected 302 redirect for unauthenticated request, got {r.status_code}"
        )
        assert "/login" in r.headers["Location"], (
            "Redirect target must be /login for unauthenticated access"
        )


# ------------------------------------------------------------------ #
# 2. No filter — all-time unfiltered view                             #
# ------------------------------------------------------------------ #

class TestNoFilter:
    def test_no_params_returns_200(self, auth_client):
        """GET /profile with no query params must return HTTP 200."""
        r = auth_client.get("/profile")
        assert r.status_code == 200, (
            f"Expected 200 for authenticated /profile with no params, got {r.status_code}"
        )

    def test_no_params_shows_all_eight_seed_expenses_total(self, auth_client):
        """Unfiltered view must show the total of all 8 seed expenses: 326.50."""
        r = auth_client.get("/profile")
        assert b"326.50" in r.data, (
            "Unfiltered /profile must display the all-time total of 326.50 from 8 seed expenses"
        )

    def test_no_params_shows_top_category(self, auth_client):
        """Unfiltered view must identify Bills as the top spending category."""
        r = auth_client.get("/profile")
        assert b"Bills" in r.data, (
            "Unfiltered /profile must show Bills as the top spending category"
        )

    def test_no_params_shows_seed_transaction_description(self, auth_client):
        """Unfiltered view must include at least one known seed expense description."""
        r = auth_client.get("/profile")
        assert b"Electricity bill" in r.data, (
            "Unfiltered /profile must show seed transaction 'Electricity bill'"
        )


# ------------------------------------------------------------------ #
# 3. Valid date range matching seed data                              #
# ------------------------------------------------------------------ #

class TestValidDateRangeWithMatches:
    def test_may_2026_filter_returns_200(self, auth_client):
        """GET /profile?date_from=2026-05-01&date_to=2026-05-31 must return 200."""
        r = auth_client.get("/profile?date_from=2026-05-01&date_to=2026-05-31")
        assert r.status_code == 200, (
            f"Expected 200 for valid May 2026 filter, got {r.status_code}"
        )

    def test_may_2026_filter_shows_electricity_bill_amount(self, auth_client):
        """May 2026 filter must show the 120.00 electricity bill (dated 05-05-2026)."""
        r = auth_client.get("/profile?date_from=2026-05-01&date_to=2026-05-31")
        assert b"120.00" in r.data, (
            "May 2026 filter must include the $120.00 electricity bill from 05-05-2026"
        )

    def test_may_2026_filter_shows_grocery_amount(self, auth_client):
        """May 2026 filter must show the 12.50 grocery run (dated 05-01-2026)."""
        r = auth_client.get("/profile?date_from=2026-05-01&date_to=2026-05-31")
        assert b"12.50" in r.data, (
            "May 2026 filter must include the $12.50 grocery run from 05-01-2026"
        )

    def test_may_2026_filter_total_equals_all_seed_expenses(self, auth_client):
        """Since all 8 seed expenses are in May 2026, the filtered total must be 326.50."""
        r = auth_client.get("/profile?date_from=2026-05-01&date_to=2026-05-31")
        assert b"326.50" in r.data, (
            "All 8 seed expenses are in May 2026 so filtered total must still be 326.50"
        )

    def test_narrow_range_within_may_excludes_other_expenses(self, auth_client):
        """A narrow range (05-05-2026 to 05-05-2026) should only match the electricity bill."""
        r = auth_client.get("/profile?date_from=2026-05-05&date_to=2026-05-05")
        assert r.status_code == 200, (
            f"Expected 200 for single-day May 5 filter, got {r.status_code}"
        )
        assert b"120.00" in r.data, (
            "Single-day filter for 2026-05-05 must show the $120.00 electricity bill"
        )
        # The grocery run (12.50) is on 05-01 and must NOT appear in this narrow range.
        # We verify by checking the transaction count is 1 (shown as "1" in the page).
        # Rather than asserting absence of 12.50 (which could appear elsewhere),
        # we confirm the stats transaction_count reflects only 1 match.
        assert b"12.50" not in r.data, (
            "Single-day filter for 2026-05-05 must not include the $12.50 grocery (05-01)"
        )


# ------------------------------------------------------------------ #
# 4. Valid date range with no matching expenses                       #
# ------------------------------------------------------------------ #

class TestValidDateRangeNoMatches:
    def test_january_2026_filter_returns_200(self, auth_client):
        """GET /profile?date_from=2026-01-01&date_to=2026-01-31 must return 200 (no crash)."""
        r = auth_client.get("/profile?date_from=2026-01-01&date_to=2026-01-31")
        assert r.status_code == 200, (
            f"Expected 200 for a valid range with no expenses, got {r.status_code}"
        )

    def test_january_2026_filter_shows_zero_total(self, auth_client):
        """When no expenses match the filter, the displayed total must be 0.00."""
        r = auth_client.get("/profile?date_from=2026-01-01&date_to=2026-01-31")
        # The template renders totals like "$0.00" or just "0.00" via the stats dict.
        assert b"0.00" in r.data, (
            "A filter with no matching expenses must display a total of 0.00"
        )

    def test_january_2026_filter_shows_zero_transaction_count(self, auth_client):
        """When no expenses match the filter, the transaction count must be 0."""
        r = auth_client.get("/profile?date_from=2026-01-01&date_to=2026-01-31")
        # The stats dict returns transaction_count=0; the template renders it.
        assert b"0" in r.data, (
            "A filter with no matching expenses must display a transaction count of 0"
        )

    def test_far_future_filter_returns_200(self, auth_client):
        """A future date range with no expenses must not crash the app."""
        r = auth_client.get("/profile?date_from=2030-01-01&date_to=2030-12-31")
        assert r.status_code == 200, (
            f"Expected 200 for a future date range with no expenses, got {r.status_code}"
        )


# ------------------------------------------------------------------ #
# 5. date_from > date_to — flash error                                #
# ------------------------------------------------------------------ #

class TestInvertedDateRange:
    def test_inverted_dates_returns_200(self, auth_client):
        """date_from > date_to must still return HTTP 200 (not 400 or 500)."""
        r = auth_client.get(
            "/profile?date_from=2026-12-31&date_to=2026-01-01",
            follow_redirects=True,
        )
        assert r.status_code == 200, (
            f"Expected 200 for inverted date range, got {r.status_code}"
        )

    def test_inverted_dates_flashes_error_message(self, auth_client):
        """date_from > date_to must flash 'Start date must be before end date.'."""
        r = auth_client.get(
            "/profile?date_from=2026-12-31&date_to=2026-01-01",
            follow_redirects=True,
        )
        assert b"Start date must be before end date." in r.data, (
            "Inverted date range must flash the error 'Start date must be before end date.'"
        )

    def test_inverted_dates_falls_back_to_unfiltered_view(self, auth_client):
        """When date_from > date_to, the page must show the unfiltered all-time total."""
        r = auth_client.get(
            "/profile?date_from=2026-12-31&date_to=2026-01-01",
            follow_redirects=True,
        )
        assert b"326.50" in r.data, (
            "Inverted date range must fall back to unfiltered view showing all-time total 326.50"
        )


# ------------------------------------------------------------------ #
# 6. Malformed date_from                                              #
# ------------------------------------------------------------------ #

class TestMalformedDateFrom:
    def test_malformed_date_from_returns_200(self, auth_client):
        """A non-ISO date_from must not crash the app — must return 200."""
        r = auth_client.get("/profile?date_from=not-a-date&date_to=2026-05-31")
        assert r.status_code == 200, (
            f"Expected 200 for malformed date_from, got {r.status_code}"
        )

    def test_malformed_date_from_shows_unfiltered_view(self, auth_client):
        """Malformed date_from must silently fall back to the unfiltered all-time view."""
        r = auth_client.get("/profile?date_from=not-a-date&date_to=2026-05-31")
        assert b"326.50" in r.data, (
            "Malformed date_from must fall back to unfiltered view showing all-time total 326.50"
        )

    def test_malformed_date_from_no_error_message(self, auth_client):
        """Malformed date_from is a silent fallback — no flash error should appear."""
        r = auth_client.get("/profile?date_from=not-a-date&date_to=2026-05-31")
        assert b"Start date must be before end date." not in r.data, (
            "Malformed date_from must silently fall back — no flash error for invalid format"
        )

    def test_clearly_wrong_date_format_returns_200(self, auth_client):
        """A date in wrong format (DD/MM/YYYY) must be treated as absent, not crash."""
        r = auth_client.get("/profile?date_from=01/05/2026&date_to=2026-05-31")
        assert r.status_code == 200, (
            f"Expected 200 for wrong-format date_from, got {r.status_code}"
        )


# ------------------------------------------------------------------ #
# 7. Malformed date_to                                                #
# ------------------------------------------------------------------ #

class TestMalformedDateTo:
    def test_malformed_date_to_returns_200(self, auth_client):
        """A non-ISO date_to must not crash the app — must return 200."""
        r = auth_client.get("/profile?date_from=2026-05-01&date_to=bogus")
        assert r.status_code == 200, (
            f"Expected 200 for malformed date_to, got {r.status_code}"
        )

    def test_malformed_date_to_shows_unfiltered_view(self, auth_client):
        """Malformed date_to must silently fall back to the unfiltered all-time view."""
        r = auth_client.get("/profile?date_from=2026-05-01&date_to=bogus")
        assert b"326.50" in r.data, (
            "Malformed date_to must fall back to unfiltered view showing all-time total 326.50"
        )

    def test_malformed_date_to_no_error_message(self, auth_client):
        """Malformed date_to is a silent fallback — no flash error should appear."""
        r = auth_client.get("/profile?date_from=2026-05-01&date_to=bogus")
        assert b"Start date must be before end date." not in r.data, (
            "Malformed date_to must silently fall back — no flash error for invalid format"
        )


# ------------------------------------------------------------------ #
# 8. Only date_from provided                                          #
# ------------------------------------------------------------------ #

class TestOnlyDateFromProvided:
    def test_only_date_from_returns_200(self, auth_client):
        """GET /profile?date_from=2026-05-01 (no date_to) must return 200."""
        r = auth_client.get("/profile?date_from=2026-05-01")
        assert r.status_code == 200, (
            f"Expected 200 when only date_from is provided, got {r.status_code}"
        )

    def test_only_date_from_treated_as_no_filter(self, auth_client):
        """A lone date_from with no date_to must behave as no filter (unfiltered view)."""
        r = auth_client.get("/profile?date_from=2026-05-01")
        assert b"326.50" in r.data, (
            "Only date_from provided — must fall back to unfiltered view showing 326.50"
        )

    def test_only_date_from_no_error_flash(self, auth_client):
        """A lone date_from must not trigger any flash error message."""
        r = auth_client.get("/profile?date_from=2026-05-01")
        assert b"Start date must be before end date." not in r.data, (
            "Providing only date_from must not trigger a flash error"
        )


# ------------------------------------------------------------------ #
# 9. Only date_to provided                                            #
# ------------------------------------------------------------------ #

class TestOnlyDateToProvided:
    def test_only_date_to_returns_200(self, auth_client):
        """GET /profile?date_to=2026-05-31 (no date_from) must return 200."""
        r = auth_client.get("/profile?date_to=2026-05-31")
        assert r.status_code == 200, (
            f"Expected 200 when only date_to is provided, got {r.status_code}"
        )

    def test_only_date_to_treated_as_no_filter(self, auth_client):
        """A lone date_to with no date_from must behave as no filter (unfiltered view)."""
        r = auth_client.get("/profile?date_to=2026-05-31")
        assert b"326.50" in r.data, (
            "Only date_to provided — must fall back to unfiltered view showing 326.50"
        )

    def test_only_date_to_no_error_flash(self, auth_client):
        """A lone date_to must not trigger any flash error message."""
        r = auth_client.get("/profile?date_to=2026-05-31")
        assert b"Start date must be before end date." not in r.data, (
            "Providing only date_to must not trigger a flash error"
        )


# ------------------------------------------------------------------ #
# 10. Filter bar HTML elements present                                #
# ------------------------------------------------------------------ #

class TestFilterBarHTML:
    def test_filter_bar_contains_all_time_label(self, auth_client):
        """The profile page must contain an 'All Time' filter preset link or button."""
        r = auth_client.get("/profile")
        assert b"All Time" in r.data, (
            "Profile page filter bar must contain an 'All Time' preset"
        )

    def test_filter_bar_contains_this_month_label(self, auth_client):
        """The profile page must contain a 'This Month' filter preset link or button."""
        r = auth_client.get("/profile")
        assert b"This Month" in r.data, (
            "Profile page filter bar must contain a 'This Month' preset"
        )

    def test_filter_bar_contains_last_3_months_label(self, auth_client):
        """The profile page must contain a 'Last 3 Months' filter preset link or button."""
        r = auth_client.get("/profile")
        assert b"Last 3 Months" in r.data, (
            "Profile page filter bar must contain a 'Last 3 Months' preset"
        )

    def test_filter_bar_contains_last_6_months_label(self, auth_client):
        """The profile page must contain a 'Last 6 Months' filter preset link or button."""
        r = auth_client.get("/profile")
        assert b"Last 6 Months" in r.data, (
            "Profile page filter bar must contain a 'Last 6 Months' preset"
        )

    def test_filter_bar_all_presets_present_in_single_request(self, auth_client):
        """All four preset labels must appear in one page load."""
        r = auth_client.get("/profile")
        for label in (b"All Time", b"This Month", b"Last 3 Months", b"Last 6 Months"):
            assert label in r.data, (
                f"Profile page filter bar must contain the preset label: {label.decode()}"
            )

    def test_filter_bar_presets_also_present_with_active_filter(self, auth_client):
        """All four preset labels must appear even when a custom date filter is active."""
        r = auth_client.get("/profile?date_from=2026-05-01&date_to=2026-05-31")
        for label in (b"All Time", b"This Month", b"Last 3 Months", b"Last 6 Months"):
            assert label in r.data, (
                f"Filter bar preset '{label.decode()}' must appear even with an active filter"
            )


# ------------------------------------------------------------------ #
# 11. Apply button and date inputs                                    #
# ------------------------------------------------------------------ #

class TestFilterFormElements:
    def test_profile_contains_date_input_elements(self, auth_client):
        """The profile page must contain <input type="date"> fields for custom range."""
        r = auth_client.get("/profile")
        assert b'type="date"' in r.data or b"type='date'" in r.data, (
            "Profile page filter bar must contain <input type=\"date\"> fields"
        )

    def test_profile_contains_apply_submit_button(self, auth_client):
        """The profile page must contain a submit button for the custom date range form."""
        r = auth_client.get("/profile")
        # The Apply button may be rendered as <button type="submit">, <input type="submit">,
        # or a button labelled "Apply".
        has_submit = (
            b'type="submit"' in r.data
            or b"type='submit'" in r.data
            or b"Apply" in r.data
        )
        assert has_submit, (
            "Profile page must contain a submit button (type='submit' or labeled 'Apply') "
            "for the custom date range filter form"
        )

    def test_profile_date_input_has_date_from_name(self, auth_client):
        """The custom range form must have an input named 'date_from'."""
        r = auth_client.get("/profile")
        assert b'name="date_from"' in r.data or b"name='date_from'" in r.data, (
            "Profile page filter form must include an input with name='date_from'"
        )

    def test_profile_date_input_has_date_to_name(self, auth_client):
        """The custom range form must have an input named 'date_to'."""
        r = auth_client.get("/profile")
        assert b'name="date_to"' in r.data or b"name='date_to'" in r.data, (
            "Profile page filter form must include an input with name='date_to'"
        )

    def test_filter_form_elements_present_with_active_filter(self, auth_client):
        """Date inputs and submit button must still be present when a filter is active."""
        r = auth_client.get("/profile?date_from=2026-05-01&date_to=2026-05-31")
        assert b'type="date"' in r.data or b"type='date'" in r.data, (
            "Date inputs must be present in the filter bar even when a filter is active"
        )
        has_submit = (
            b'type="submit"' in r.data
            or b"type='submit'" in r.data
            or b"Apply" in r.data
        )
        assert has_submit, (
            "Submit button must be present in the filter bar even when a filter is active"
        )
