from app.extensions import db
from app.models import AuditLog, User

from .constants import PASSWORD


def test_login_success_returns_tokens_and_user(users, login):
    res = login("admin")
    body = res.get_json()
    assert res.status_code == 200
    assert body["access_token"] and body["refresh_token"]
    assert body["user"]["role"] == "admin"
    assert "password_hash" not in body["user"]


def test_login_is_case_insensitive_for_username(users, login):
    assert login("ADMIN").status_code == 200


def test_wrong_password_and_unknown_user_give_same_message(users, login):
    wrong = login("admin", "Wrong-pass-123")
    unknown = login("ghost", "Wrong-pass-123")
    assert wrong.status_code == unknown.status_code == 401
    assert wrong.get_json()["error"] == unknown.get_json()["error"]


def test_account_locks_after_max_attempts(users, login, app):
    for _ in range(app.config["LOGIN_MAX_ATTEMPTS"]):
        assert login("operator", "Wrong-pass-123").status_code == 401
    assert login("operator").status_code == 423


def test_successful_login_resets_failed_counter(users, login):
    login("operator", "Wrong-pass-123")
    login("operator", "Wrong-pass-123")
    assert login("operator").status_code == 200
    assert db.session.get(User, users["operator"].id).failed_login_count == 0


def test_inactive_user_cannot_login(users, login):
    users["operator"].is_active = False
    db.session.commit()
    assert login("operator").status_code == 403


def test_login_validation_error(client):
    res = client.post("/api/auth/login", json={"username": "admin"})
    assert res.status_code == 400
    assert "password" in res.get_json()["details"]


def test_me_requires_token(client):
    assert client.get("/api/auth/me").status_code == 401


def test_me_returns_current_user(users, client, auth):
    res = client.get("/api/auth/me", headers=auth("technician"))
    assert res.get_json()["user"]["username"] == "technician"


def test_logout_revokes_access_token(users, client, login):
    tokens = login("admin").get_json()
    headers = {"Authorization": f"Bearer {tokens['access_token']}"}
    assert client.post("/api/auth/logout", headers=headers, json={}).status_code == 200
    assert client.get("/api/auth/me", headers=headers).status_code == 401


def test_logout_revokes_refresh_token_too(users, client, login):
    tokens = login("admin").get_json()
    headers = {"Authorization": f"Bearer {tokens['access_token']}"}
    client.post("/api/auth/logout", headers=headers, json={"refresh_token": tokens["refresh_token"]})
    refresh = client.post(
        "/api/auth/refresh", headers={"Authorization": f"Bearer {tokens['refresh_token']}"}
    )
    assert refresh.status_code == 401


def test_refresh_issues_new_access_token(users, client, login):
    tokens = login("admin").get_json()
    res = client.post(
        "/api/auth/refresh", headers={"Authorization": f"Bearer {tokens['refresh_token']}"}
    )
    assert res.status_code == 200
    new_headers = {"Authorization": f"Bearer {res.get_json()['access_token']}"}
    assert client.get("/api/auth/me", headers=new_headers).status_code == 200


def test_refresh_token_cannot_access_protected_routes(users, client, login):
    tokens = login("admin").get_json()
    headers = {"Authorization": f"Bearer {tokens['refresh_token']}"}
    assert client.get("/api/auth/me", headers=headers).status_code == 401


def test_access_token_cannot_be_used_to_refresh(users, client, login):
    tokens = login("admin").get_json()
    headers = {"Authorization": f"Bearer {tokens['access_token']}"}
    assert client.post("/api/auth/refresh", headers=headers).status_code == 401


def test_deactivated_user_token_is_rejected(users, client, auth):
    headers = auth("operator")
    users["operator"].is_active = False
    db.session.commit()
    assert client.get("/api/auth/me", headers=headers).status_code == 401


def test_change_password_flow(users, client, auth, login):
    headers = auth("technician")
    bad = client.post(
        "/api/auth/change-password",
        headers=headers,
        json={"current_password": "Wrong-pass-123", "new_password": "Brand-new-pass9"},
    )
    assert bad.status_code == 400
    ok = client.post(
        "/api/auth/change-password",
        headers=headers,
        json={"current_password": PASSWORD, "new_password": "Brand-new-pass9"},
    )
    assert ok.status_code == 200
    assert login("technician", PASSWORD).status_code == 401
    assert login("technician", "Brand-new-pass9").status_code == 200


def test_change_password_rejects_weak_password(users, client, auth):
    res = client.post(
        "/api/auth/change-password",
        headers=auth("technician"),
        json={"current_password": PASSWORD, "new_password": "short1"},
    )
    assert res.status_code == 400


def test_login_events_are_audited(users, login):
    login("admin")
    login("admin", "Wrong-pass-123")
    actions = {row.action for row in AuditLog.query.all()}
    assert {"login_success", "login_failed"} <= actions
