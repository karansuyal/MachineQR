from app.models import AuditLog, User

from .constants import PASSWORD

NEW_USER = {
    "username": "Ravi.Kumar",
    "email": "Ravi@Example.com",
    "full_name": "Ravi Kumar",
    "password": "Strong-pass-123",
    "role": "technician",
}


def test_admin_can_create_user(users, client, auth):
    res = client.post("/api/users", headers=auth("admin"), json=NEW_USER)
    body = res.get_json()["user"]
    assert res.status_code == 201
    assert body["username"] == "ravi.kumar"
    assert body["email"] == "ravi@example.com"
    assert body["role"] == "technician"
    assert "password" not in body and "password_hash" not in body
    assert AuditLog.query.filter_by(action="user_created").count() == 1


def test_only_admin_can_manage_users(users, client, auth):
    for role in ("technician", "operator"):
        headers = auth(role)
        assert client.get("/api/users", headers=headers).status_code == 403
        assert client.post("/api/users", headers=headers, json=NEW_USER).status_code == 403
        assert client.patch(f"/api/users/{users['admin'].id}", headers=headers, json={}).status_code == 403
        assert client.post(
            f"/api/users/{users['admin'].id}/reset-password",
            headers=headers,
            json={"new_password": "Strong-pass-123"},
        ).status_code == 403


def test_unauthenticated_requests_are_rejected(users, client):
    assert client.get("/api/users").status_code == 401
    assert client.post("/api/users", json=NEW_USER).status_code == 401


def test_duplicate_username_and_email_return_409(users, client, auth):
    headers = auth("admin")
    dup_username = {**NEW_USER, "username": "operator"}
    assert client.post("/api/users", headers=headers, json=dup_username).status_code == 409
    dup_email = {**NEW_USER, "email": "operator@example.com"}
    assert client.post("/api/users", headers=headers, json=dup_email).status_code == 409


def test_create_user_validation(users, client, auth):
    headers = auth("admin")
    cases = [
        {**NEW_USER, "role": "superuser"},
        {**NEW_USER, "password": "short1"},
        {**NEW_USER, "password": "onlyletterspassword"},
        {**NEW_USER, "email": "not-an-email"},
        {**NEW_USER, "username": "bad name!"},
        {**NEW_USER, "is_active": False},
    ]
    for payload in cases:
        assert client.post("/api/users", headers=headers, json=payload).status_code == 400


def test_admin_can_update_role_and_status(users, client, auth):
    headers = auth("admin")
    target = users["operator"].id
    res = client.patch(
        f"/api/users/{target}", headers=headers, json={"role": "technician", "is_active": False}
    )
    body = res.get_json()["user"]
    assert res.status_code == 200
    assert body["role"] == "technician" and body["is_active"] is False


def test_admin_cannot_deactivate_or_demote_self(users, client, auth):
    headers = auth("admin")
    me = users["admin"].id
    assert client.patch(f"/api/users/{me}", headers=headers, json={"is_active": False}).status_code == 400
    assert client.patch(f"/api/users/{me}", headers=headers, json={"role": "operator"}).status_code == 400


def test_role_change_takes_effect_on_existing_token(users, client, auth):
    other_admin = client.post(
        "/api/users", headers=auth("admin"), json={**NEW_USER, "role": "admin"}
    ).get_json()["user"]
    login_res = client.post(
        "/api/auth/login", json={"username": "ravi.kumar", "password": NEW_USER["password"]}
    )
    token_headers = {"Authorization": f"Bearer {login_res.get_json()['access_token']}"}
    assert client.get("/api/users", headers=token_headers).status_code == 200
    client.patch(f"/api/users/{other_admin['id']}", headers=auth("admin"), json={"role": "operator"})
    assert client.get("/api/users", headers=token_headers).status_code == 403


def test_get_missing_user_returns_404(users, client, auth):
    assert client.get("/api/users/9999", headers=auth("admin")).status_code == 404


def test_admin_reset_password(users, client, auth, login):
    res = client.post(
        f"/api/users/{users['operator'].id}/reset-password",
        headers=auth("admin"),
        json={"new_password": "Reset-pass-456"},
    )
    assert res.status_code == 200
    assert login("operator", PASSWORD).status_code == 401
    assert login("operator", "Reset-pass-456").status_code == 200


def test_list_users_filters_and_paginates(users, client, auth):
    headers = auth("admin")
    res = client.get("/api/users?role=operator", headers=headers).get_json()
    assert res["total"] == 1 and res["items"][0]["username"] == "operator"
    res = client.get("/api/users?per_page=2&page=2", headers=headers).get_json()
    assert res["total"] == 3 and len(res["items"]) == 1
    res = client.get("/api/users?search=tech", headers=headers).get_json()
    assert [u["username"] for u in res["items"]] == ["technician"]
    assert client.get("/api/users?per_page=1000", headers=headers).status_code == 400


def test_unknown_query_params_are_rejected(users, client, auth):
    assert client.get("/api/users?bogus=1", headers=auth("admin")).status_code == 400
