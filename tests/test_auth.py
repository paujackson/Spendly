def test_login_get(client):
    r = client.get("/login")
    assert r.status_code == 200


def test_login_success(client):
    r = client.post("/login", data={"email": "demo@spendly.com", "password": "demo123"})
    assert r.status_code == 302
    assert "/profile" in r.headers["Location"]
    with client.session_transaction() as sess:
        assert "user_id" in sess


def test_login_already_logged_in(client):
    client.post("/login", data={"email": "demo@spendly.com", "password": "demo123"})
    r = client.get("/login")
    assert r.status_code == 302
    assert "/profile" in r.headers["Location"]


def test_login_wrong_password(client):
    r = client.post("/login", data={"email": "demo@spendly.com", "password": "wrongpass"})
    assert r.status_code == 200
    assert b"Invalid email or password" in r.data


def test_login_unknown_email(client):
    r = client.post("/login", data={"email": "nobody@example.com", "password": "anything"})
    assert r.status_code == 200
    assert b"Invalid email or password" in r.data


def test_login_empty_fields(client):
    r = client.post("/login", data={"email": "", "password": ""})
    assert r.status_code == 200
    assert b"Invalid email or password" in r.data


def test_logout(client):
    client.post("/login", data={"email": "demo@spendly.com", "password": "demo123"})
    r = client.post("/logout")
    assert r.status_code == 302
    assert r.headers["Location"].endswith("/")
    with client.session_transaction() as sess:
        assert "user_id" not in sess
