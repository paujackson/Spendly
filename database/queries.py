from database.db import get_db
from datetime import datetime


def get_user_by_id(user_id):
    db = get_db()
    row = db.execute(
        "SELECT name, email, created_at FROM users WHERE id = ?",
        (user_id,)
    ).fetchone()
    db.close()
    if row is None:
        return None
    user = dict(row)
    try:
        dt = datetime.strptime(user["created_at"][:10], "%Y-%m-%d")
        user["member_since"] = dt.strftime("%B, %Y")
    except (ValueError, TypeError):
        user["member_since"] = ""
    return user


def get_recent_transactions(user_id, limit=10):
    db = get_db()
    rows = db.execute(
        """
        SELECT
            date AS raw_date,
            description,
            category,
            printf('%.2f', amount) AS amount
        FROM expenses
        WHERE user_id = ?
        ORDER BY substr(date,7,4)||'-'||substr(date,1,2)||'-'||substr(date,4,2) DESC
        LIMIT ?
        """,
        (user_id, limit)
    ).fetchall()
    db.close()
    result = []
    for r in rows:
        row = dict(r)
        try:
            dt = datetime.strptime(row["raw_date"], "%m-%d-%Y")
            row["date"] = dt.strftime("%b-%d-%Y")
        except (ValueError, TypeError):
            row["date"] = row["raw_date"]
        del row["raw_date"]
        result.append(row)
    return result


def get_summary_spending_stats(user_id):
    db = get_db()
    row = db.execute(
        """
        SELECT printf('%.2f', COALESCE(SUM(amount), 0)) AS total_spent,
               COUNT(*) AS transaction_count
        FROM expenses WHERE user_id = ?
        """,
        (user_id,)
    ).fetchone()
    top = db.execute(
        """
        SELECT category FROM expenses WHERE user_id = ?
        GROUP BY category ORDER BY SUM(amount) DESC LIMIT 1
        """,
        (user_id,)
    ).fetchone()
    db.close()
    return {
        "total_spent": row["total_spent"],
        "transaction_count": row["transaction_count"],
        "top_category": top["category"] if top else "—",
    }


def get_category_breakdown(user_id):
    db = get_db()
    rows = db.execute(
        """
        SELECT category AS name, COUNT(*) AS count, SUM(amount) AS total_raw
        FROM expenses WHERE user_id = ?
        GROUP BY category ORDER BY total_raw DESC
        """,
        (user_id,)
    ).fetchall()
    db.close()
    if not rows:
        return []
    grand = sum(r["total_raw"] for r in rows)
    return [
        {
            "name": r["name"],
            "count": r["count"],
            "total": "{:.2f}".format(r["total_raw"]),
            "pct": int(round(r["total_raw"] / grand * 100)),
        }
        for r in rows
    ]
