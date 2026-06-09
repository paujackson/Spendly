def test_profile_redirect_when_logged_out(client):
    r = client.get("/profile")
    assert r.status_code == 302
    assert "/login" in r.headers["Location"]


def test_profile_loads_when_logged_in(client):
    client.post("/login", data={"email": "demo@spendly.com", "password": "demo123"})
    r = client.get("/profile")
    assert r.status_code == 200
    assert b"Demo User" in r.data
    assert b"326.50" in r.data
    assert b"Bills" in r.data
    assert b"Electricity bill" in r.data
