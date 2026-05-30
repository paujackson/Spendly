from flask import Flask, render_template, request, redirect, url_for, session, flash
from werkzeug.security import generate_password_hash, check_password_hash
from database.db import get_db, init_db, seed_db

app = Flask(__name__)
app.secret_key = "spendly-dev-secret"

with app.app_context():
    init_db()
    seed_db()


# ------------------------------------------------------------------ #
# Routes                                                              #
# ------------------------------------------------------------------ #

@app.route("/")
def landing():
    return render_template("landing.html")


@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "GET":
        return render_template("register.html")

    name = request.form.get("name", "").strip()
    email = request.form.get("email", "").strip()
    password = request.form.get("password", "")
    confirm_password = request.form.get("confirm_password", "")

    if not name or not email or not password or not confirm_password:
        return render_template("register.html", error="All fields are required.")

    if len(name) > 100:
        return render_template("register.html", error="Name must be 100 characters or fewer.")
    if "@" not in email or "." not in email.split("@")[-1] or len(email) > 254:
        return render_template("register.html", error="Enter a valid email address.")
    if len(password) < 8:
        return render_template("register.html", error="Password must be at least 8 characters.")

    if password != confirm_password:
        return render_template("register.html", error="Passwords do not match.")

    db = get_db()
    existing = db.execute("SELECT id FROM users WHERE email = ?", (email,)).fetchone()
    if existing:
        db.close()
        return render_template("register.html", error="Email already registered.")

    db.execute(
        "INSERT INTO users (name, email, password_hash) VALUES (?, ?, ?)",
        (name, email, generate_password_hash(password))
    )
    db.commit()
    db.close()

    return redirect(url_for("login"))


@app.route("/login", methods=["GET", "POST"])
def login():
    if session.get("user_id"):
        return redirect(url_for("profile"))

    if request.method == "GET":
        return render_template("login.html")

    email = request.form.get("email", "").strip()
    password = request.form.get("password", "")

    if not email or not password:
        return render_template("login.html", error="Invalid email or password")

    db = get_db()
    user = db.execute(
        "SELECT id, name, password_hash FROM users WHERE email = ?", (email,)
    ).fetchone()

    if not user or not check_password_hash(user["password_hash"], password):
        db.close()
        return render_template("login.html", error="Invalid email or password")

    session.clear()
    session["user_id"] = user["id"]
    session["user_name"] = user["name"]
    db.close()
    return redirect(url_for("profile"))


# ------------------------------------------------------------------ #
# Placeholder routes — students will implement these                  #
# ------------------------------------------------------------------ #

@app.route("/terms")
def terms():
    return render_template("terms.html")


@app.route("/privacy")
def privacy():
    return render_template("privacy.html")


@app.route("/logout", methods=["POST"])
def logout():
    session.clear()
    return redirect(url_for("landing"))


@app.route("/profile")
def profile():
    if not session.get("user_id"):
        return redirect(url_for("login"))

    user = {
        "name": "Alex Rivera",
        "email": "alex@example.com",
        "member_since": "May, 2026",
        "initials": "AR",
    }
    stats = {
        "total_spent": "326.50",
        "transaction_count": 8,
        "top_category": "Bills",
    }
    transactions = [
        {"date": "May 17", "description": "Restaurant dinner",      "category": "Food",          "amount": "22.00"},
        {"date": "May 15", "description": "Miscellaneous",          "category": "Other",         "amount": "9.00"},
        {"date": "May 13", "description": "New shoes",              "category": "Shopping",      "amount": "65.00"},
        {"date": "May 10", "description": "Streaming subscription", "category": "Entertainment", "amount": "18.00"},
        {"date": "May 08", "description": "Pharmacy",               "category": "Health",        "amount": "45.00"},
        {"date": "May 05", "description": "Electricity bill",       "category": "Bills",         "amount": "120.00"},
        {"date": "May 03", "description": "Monthly bus pass",       "category": "Transport",     "amount": "35.00"},
        {"date": "May 01", "description": "Grocery run",            "category": "Food",          "amount": "12.50"},
    ]
    categories = [
        {"name": "Bills",         "count": 1, "total": "120.00", "pct": 37},
        {"name": "Shopping",      "count": 1, "total": "65.00",  "pct": 20},
        {"name": "Health",        "count": 1, "total": "45.00",  "pct": 14},
        {"name": "Transport",     "count": 1, "total": "35.00",  "pct": 11},
        {"name": "Food",          "count": 2, "total": "34.50",  "pct": 11},
        {"name": "Entertainment", "count": 1, "total": "18.00",  "pct": 6},
        {"name": "Other",         "count": 1, "total": "9.00",   "pct": 3},
    ]
    return render_template("profile.html", user=user, stats=stats,
                           transactions=transactions, categories=categories)


@app.route("/expenses/add")
def add_expense():
    return "Add expense — coming in Step 7"


@app.route("/expenses/<int:id>/edit")
def edit_expense(id):
    return "Edit expense — coming in Step 8"


@app.route("/expenses/<int:id>/delete")
def delete_expense(id):
    return "Delete expense — coming in Step 9"


if __name__ == "__main__":
    app.run(debug=True, use_reloader=False,port=5001)
