import pytest
import uuid
from app import app as flask_app
from database.db import init_db, seed_db, get_db
from database.queries import (
    get_user_by_id,
    get_recent_transactions,
    get_summary_spending_stats,
    get_category_breakdown,
)


@pytest.fixture
def app():
    flask_app.config["TESTING"] = True
    flask_app.config["SECRET_KEY"] = "test-secret"
    with flask_app.app_context():
        init_db()
        seed_db()
    yield flask_app


@pytest.fixture
def client(app):
    return app.test_client()


@pytest.fixture
def empty_user_id(app):
    """Insert a user with no expenses; return their id."""
    unique_email = f"nospend-{uuid.uuid4().hex[:8]}@test.com"
    with app.app_context():
        db = get_db()
        cursor = db.execute(
            "INSERT INTO users (name, email, password_hash) VALUES (?, ?, ?)",
            ("No Spend", unique_email, "x")
        )
        uid = cursor.lastrowid
        db.commit()
        db.close()
    return uid


# ------------------------------------------------------------------ #
# get_user_by_id                                                      #
# ------------------------------------------------------------------ #

def test_get_user_by_id_returns_correct_fields(app):
    with app.app_context():
        db = get_db()
        seed_user_id = db.execute("SELECT id FROM users WHERE email = ?", ("demo@spendly.com",)).fetchone()["id"]
        db.close()
        user = get_user_by_id(seed_user_id)
    assert user["name"] == "Demo User"
    assert user["email"] == "demo@spendly.com"
    assert user["member_since"] != ""


def test_get_user_by_id_returns_none_for_missing(app):
    with app.app_context():
        result = get_user_by_id(999999)
    assert result is None


# ------------------------------------------------------------------ #
# get_summary_spending_stats                                          #
# ------------------------------------------------------------------ #

def test_get_summary_spending_stats_correct_values(app):
    with app.app_context():
        db = get_db()
        seed_user_id = db.execute("SELECT id FROM users WHERE email = ?", ("demo@spendly.com",)).fetchone()["id"]
        db.close()
        stats = get_summary_spending_stats(seed_user_id)
    assert stats["total_spent"] == "326.50"
    assert stats["transaction_count"] == 8
    assert stats["top_category"] == "Bills"


def test_get_summary_spending_stats_zero_expenses(app, empty_user_id):
    with app.app_context():
        stats = get_summary_spending_stats(empty_user_id)
    assert stats["total_spent"] == "0.00"
    assert stats["transaction_count"] == 0
    assert stats["top_category"] == "—"


# ------------------------------------------------------------------ #
# get_recent_transactions                                             #
# ------------------------------------------------------------------ #

def test_get_recent_transactions_returns_correct_count(app):
    with app.app_context():
        db = get_db()
        seed_user_id = db.execute("SELECT id FROM users WHERE email = ?", ("demo@spendly.com",)).fetchone()["id"]
        db.close()
        result = get_recent_transactions(seed_user_id)
    assert len(result) == 8


def test_get_recent_transactions_descending_order(app):
    with app.app_context():
        db = get_db()
        seed_user_id = db.execute("SELECT id FROM users WHERE email = ?", ("demo@spendly.com",)).fetchone()["id"]
        db.close()
        result = get_recent_transactions(seed_user_id)
    assert result[0]["description"] == "Restaurant dinner"


def test_get_recent_transactions_respects_limit(app):
    with app.app_context():
        db = get_db()
        seed_user_id = db.execute("SELECT id FROM users WHERE email = ?", ("demo@spendly.com",)).fetchone()["id"]
        db.close()
        result = get_recent_transactions(seed_user_id, limit=3)
    assert len(result) == 3


def test_get_recent_transactions_has_required_keys(app):
    with app.app_context():
        db = get_db()
        seed_user_id = db.execute("SELECT id FROM users WHERE email = ?", ("demo@spendly.com",)).fetchone()["id"]
        db.close()
        result = get_recent_transactions(seed_user_id)
    assert all({"date", "description", "category", "amount"} <= set(r.keys()) for r in result)


def test_get_recent_transactions_empty_for_zero_expenses(app, empty_user_id):
    with app.app_context():
        result = get_recent_transactions(empty_user_id)
    assert result == []


# ------------------------------------------------------------------ #
# get_category_breakdown                                              #
# ------------------------------------------------------------------ #

def test_get_category_breakdown_ordered_by_total(app):
    with app.app_context():
        db = get_db()
        seed_user_id = db.execute("SELECT id FROM users WHERE email = ?", ("demo@spendly.com",)).fetchone()["id"]
        db.close()
        result = get_category_breakdown(seed_user_id)
    assert result[0]["name"] == "Bills"
    assert isinstance(result[0]["pct"], int)


def test_get_category_breakdown_pct_sums_near_100(app):
    with app.app_context():
        db = get_db()
        seed_user_id = db.execute("SELECT id FROM users WHERE email = ?", ("demo@spendly.com",)).fetchone()["id"]
        db.close()
        result = get_category_breakdown(seed_user_id)
    total_pct = sum(c["pct"] for c in result)
    assert 98 <= total_pct <= 102


def test_get_category_breakdown_empty_for_zero_expenses(app, empty_user_id):
    with app.app_context():
        result = get_category_breakdown(empty_user_id)
    assert result == []


# ------------------------------------------------------------------ #
# Route: GET /profile                                                 #
# ------------------------------------------------------------------ #

def test_profile_redirect_when_unauthenticated(client):
    r = client.get("/profile")
    assert r.status_code == 302
    assert "/login" in r.headers["Location"]


def test_profile_shows_real_user_data(client):
    client.post("/login", data={"email": "demo@spendly.com", "password": "demo123"})
    r = client.get("/profile")
    assert r.status_code == 200
    assert b"Demo User" in r.data
    assert b"demo@spendly.com" in r.data
    assert b"326.50" in r.data
    assert b"Bills" in r.data
    assert b"Electricity bill" in r.data
    assert b"$" in r.data
