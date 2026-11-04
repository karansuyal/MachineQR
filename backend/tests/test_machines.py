import io

from PIL import Image

from app.extensions import db
from app.models import AuditLog, Machine, MachineSpecification

NEW_MACHINE = {
    "name": "Hydraulic Press",
    "category": "Press",
    "department": "Fabrication",
    "production_line": "Line 1",
    "location": "Bay A",
    "manufacturer": "ACME",
    "model_number": "HP-200",
    "serial_number": "SN-1",
    "installation_date": "2024-01-10",
    "commissioning_date": "2024-02-01",
    "plc_manufacturer": "Siemens",
    "plc_model": "S7-1200",
    "technical_notes": "Demo note",
    "operating_instructions": "Demo instructions",
    "specifications": [
        {"category": "motor", "spec_key": "Power", "spec_value": "5.5", "unit": "kW"},
        {"category": "custom", "spec_key": "Max tonnage", "spec_value": "200", "unit": "t"},
    ],
}


def png_file(name="machine.png"):
    buffer = io.BytesIO()
    Image.new("RGB", (40, 30), "red").save(buffer, "PNG")
    buffer.seek(0)
    return buffer, name


def create(client, headers, **overrides):
    return client.post("/api/machines", headers=headers, json={**NEW_MACHINE, **overrides})


def test_admin_creates_machine_with_sequential_codes(users, client, auth):
    headers = auth("admin")
    first = create(client, headers)
    second = create(client, headers, name="Lathe")
    assert first.status_code == 201
    assert first.get_json()["machine"]["machine_code"] == "M-001"
    assert second.get_json()["machine"]["machine_code"] == "M-002"
    assert AuditLog.query.filter_by(action="machine_created").count() == 2


def test_next_code_follows_highest_existing(users, client, auth, make_machine):
    make_machine(code="M-007")
    res = create(client, auth("admin"))
    assert res.get_json()["machine"]["machine_code"] == "M-008"


def test_create_stores_specifications_grouped(users, client, auth):
    machine = create(client, auth("admin")).get_json()["machine"]
    groups = {g["category"]: g["items"] for g in machine["specifications"]}
    assert groups["motor"][0]["spec_key"] == "Power"
    assert groups["custom"][0]["spec_value"] == "200"
    assert MachineSpecification.query.filter_by(is_custom=True).count() == 1


def test_only_admin_can_create_or_edit(users, client, auth, make_machine):
    make_machine()
    for role in ("technician", "operator"):
        headers = auth(role)
        assert create(client, headers).status_code == 403
        assert client.patch("/api/machines/M-001", headers=headers, json={"name": "X"}).status_code == 403
        assert client.post("/api/machines/M-001/deactivate", headers=headers).status_code == 403
        assert client.put("/api/machines/M-001/assignments", headers=headers, json={"user_ids": []}).status_code == 403
    assert client.post("/api/machines", json=NEW_MACHINE).status_code == 401


def test_create_validation(users, client, auth):
    headers = auth("admin")
    bad_payloads = [
        {**NEW_MACHINE, "name": "   "},
        {**NEW_MACHINE, "status": "exploded"},
        {**NEW_MACHINE, "installation_date": "not-a-date"},
        {**NEW_MACHINE, "machine_code": "M-999"},
        {**NEW_MACHINE, "specifications": [{"category": "magic", "spec_key": "a", "spec_value": "b"}]},
        {**NEW_MACHINE, "specifications": [
            {"category": "motor", "spec_key": "Power", "spec_value": "1"},
            {"category": "motor", "spec_key": "power", "spec_value": "2"},
        ]},
        {**NEW_MACHINE, "commissioning_date": "2023-01-01"},
    ]
    for payload in bad_payloads:
        assert client.post("/api/machines", headers=headers, json=payload).status_code == 400
    assert Machine.query.count() == 0
    no_name = {k: v for k, v in NEW_MACHINE.items() if k != "name"}
    assert client.post("/api/machines", headers=headers, json=no_name).status_code == 400


def test_update_fields_and_specs(users, client, auth):
    headers = auth("admin")
    create(client, headers)
    res = client.patch("/api/machines/M-001", headers=headers, json={"location": "Bay B", "department": ""})
    machine = res.get_json()["machine"]
    assert res.status_code == 200
    assert machine["location"] == "Bay B" and machine["department"] is None
    assert len(machine["specifications"]) == 2

    res = client.patch(
        "/api/machines/M-001", headers=headers,
        json={"specifications": [{"category": "motor", "spec_key": "Power", "spec_value": "7.5", "unit": "kW"}]},
    )
    groups = res.get_json()["machine"]["specifications"]
    assert len(groups) == 1 and groups[0]["items"][0]["spec_value"] == "7.5"


def test_update_validates_dates_against_existing_values(users, client, auth):
    headers = auth("admin")
    create(client, headers)
    res = client.patch("/api/machines/M-001", headers=headers, json={"commissioning_date": "2020-01-01"})
    assert res.status_code == 400


def test_machine_code_lookup_is_case_insensitive_and_missing_is_404(users, client, auth, make_machine):
    make_machine()
    headers = auth("admin")
    assert client.get("/api/machines/m-001", headers=headers).status_code == 200
    assert client.get("/api/machines/M-999", headers=headers).status_code == 404


def test_status_update_permissions(users, client, auth, make_machine, assign):
    machine = make_machine()
    assign(machine, users["technician"], users["operator"])
    ok_admin = client.patch("/api/machines/M-001/status", headers=auth("admin"), json={"status": "running"})
    ok_tech = client.patch("/api/machines/M-001/status", headers=auth("technician"), json={"status": "under_maintenance"})
    assert ok_admin.status_code == 200 and ok_tech.status_code == 200
    assert ok_tech.get_json()["machine"]["status"] == "under_maintenance"
    assert client.patch("/api/machines/M-001/status", headers=auth("operator"), json={"status": "running"}).status_code == 403
    assert client.patch("/api/machines/M-001/status", headers=auth("admin"), json={"status": "bad"}).status_code == 400
    assert AuditLog.query.filter_by(action="machine_status_changed").count() == 2


def test_unassigned_technician_cannot_change_status(users, client, auth, make_machine):
    make_machine()
    res = client.patch("/api/machines/M-001/status", headers=auth("technician"), json={"status": "running"})
    assert res.status_code == 403


def test_list_visibility_by_role(users, client, auth, make_machine, assign):
    first = make_machine(code="M-001")
    make_machine(code="M-002", name="Lathe")
    hidden = make_machine(code="M-003", name="Old", is_active=False)
    assign(first, users["technician"], users["operator"])
    assign(hidden, users["technician"])

    admin_codes = [m["machine_code"] for m in client.get("/api/machines", headers=auth("admin")).get_json()["items"]]
    assert admin_codes == ["M-001", "M-002", "M-003"]
    inactive_only = client.get("/api/machines?is_active=false", headers=auth("admin")).get_json()
    assert [m["machine_code"] for m in inactive_only["items"]] == ["M-003"]
    for role in ("technician", "operator"):
        items = client.get("/api/machines", headers=auth(role)).get_json()["items"]
        assert [m["machine_code"] for m in items] == ["M-001"]


def test_list_filters_search_and_pagination(users, client, auth, make_machine):
    make_machine(code="M-001", name="Hydraulic Press", department="Fab")
    make_machine(code="M-002", name="CNC Lathe", department="Machining")
    make_machine(code="M-010", name="Packer", department="Fab")
    headers = auth("admin")
    assert client.get("/api/machines?search=lathe", headers=headers).get_json()["total"] == 1
    assert client.get("/api/machines?search=M-010", headers=headers).get_json()["total"] == 1
    assert client.get("/api/machines?department=Fab", headers=headers).get_json()["total"] == 2
    page = client.get("/api/machines?per_page=2&page=2", headers=headers).get_json()
    assert page["total"] == 3 and [m["machine_code"] for m in page["items"]] == ["M-010"]
    assert client.get("/api/machines?status=bogus", headers=headers).status_code == 400
    assert client.get("/api/machines?unknown=1", headers=headers).status_code == 400


def test_options_lists_departments_and_categories(users, client, auth, make_machine):
    make_machine(code="M-001", department="Fab", category="Press")
    make_machine(code="M-002", name="B", department="Machining", category="Lathe")
    body = client.get("/api/machines/options", headers=auth("admin")).get_json()
    assert body == {"departments": ["Fab", "Machining"], "categories": ["Lathe", "Press"]}


def test_detail_access_rules(users, client, auth, make_machine, assign):
    machine = make_machine(plc_model="S7-1200", technical_notes="secret", operating_instructions="Wear PPE")
    assign(machine, users["technician"], users["operator"])
    other = make_machine(code="M-002", name="Other")

    tech = client.get("/api/machines/M-001", headers=auth("technician")).get_json()["machine"]
    assert tech["access_level"] == "full" and tech["plc_model"] == "S7-1200"
    assert "assigned_users" not in tech

    operator = client.get("/api/machines/M-001", headers=auth("operator")).get_json()["machine"]
    assert operator["access_level"] == "basic"
    assert operator["operating_instructions"] == "Wear PPE"
    for hidden in ("plc_model", "technical_notes", "specifications"):
        assert hidden not in operator

    admin = client.get("/api/machines/M-001", headers=auth("admin")).get_json()["machine"]
    assert sorted(u["role"] for u in admin["assigned_users"]) == ["operator", "technician"]

    assert client.get(f"/api/machines/{other.machine_code}", headers=auth("technician")).status_code == 403
    assert client.get("/api/machines/M-001").status_code == 401


def test_assignments_replace_and_validate(users, client, auth, make_machine):
    make_machine()
    headers = auth("admin")
    url = "/api/machines/M-001/assignments"
    ok = client.put(url, headers=headers, json={"user_ids": [users["technician"].id, users["operator"].id]})
    assert ok.status_code == 200 and len(ok.get_json()["assigned_users"]) == 2
    assert client.get("/api/machines/M-001", headers=auth("technician")).status_code == 200

    shrink = client.put(url, headers=headers, json={"user_ids": [users["operator"].id]})
    assert [u["role"] for u in shrink.get_json()["assigned_users"]] == ["operator"]
    assert client.get("/api/machines/M-001", headers=auth("technician")).status_code == 403

    assert client.put(url, headers=headers, json={"user_ids": [users["admin"].id]}).status_code == 400
    assert client.put(url, headers=headers, json={"user_ids": [9999]}).status_code == 400
    users["operator"].is_active = False
    db.session.commit()
    assert client.put(url, headers=headers, json={"user_ids": [users["operator"].id]}).status_code == 400
    assert client.put(url, headers=headers, json={}).status_code == 400


def test_deactivate_and_reactivate(users, client, auth, make_machine, assign):
    machine = make_machine()
    assign(machine, users["technician"])
    admin = auth("admin")
    res = client.post("/api/machines/M-001/deactivate", headers=admin)
    assert res.get_json()["machine"]["is_active"] is False
    assert client.get("/api/machines/M-001", headers=auth("technician")).status_code == 404
    assert client.get("/api/machines/M-001", headers=admin).status_code == 200
    assert client.patch("/api/machines/M-001/status", headers=admin, json={"status": "running"}).status_code == 400
    client.post("/api/machines/M-001/reactivate", headers=admin)
    assert client.get("/api/machines/M-001", headers=auth("technician")).status_code == 200
    assert Machine.query.count() == 1


def test_photo_upload_download_and_remove(users, client, auth, make_machine, assign):
    machine = make_machine()
    assign(machine, users["technician"])
    other = make_machine(code="M-002", name="Other")
    assign(other, users["operator"])
    admin = auth("admin")

    file, name = png_file()
    up = client.post("/api/machines/M-001/photo", headers=admin, data={"photo": (file, name)}, content_type="multipart/form-data")
    assert up.status_code == 200 and up.get_json()["machine"]["has_photo"] is True

    for headers in (admin, auth("technician")):
        res = client.get("/api/machines/M-001/photo", headers=headers)
        assert res.status_code == 200 and res.mimetype == "image/jpeg"
        assert Image.open(io.BytesIO(res.data)).format == "JPEG"
    assert client.get("/api/machines/M-001/photo", headers=auth("operator")).status_code == 403
    assert client.get("/api/machines/M-001/photo").status_code == 401

    removed = client.delete("/api/machines/M-001/photo", headers=admin)
    assert removed.get_json()["machine"]["has_photo"] is False
    assert client.get("/api/machines/M-001/photo", headers=admin).status_code == 404


def test_photo_upload_rejects_bad_files(users, client, auth, make_machine):
    make_machine()
    admin = auth("admin")
    url = "/api/machines/M-001/photo"

    def post(file, name):
        return client.post(url, headers=admin, data={"photo": (file, name)}, content_type="multipart/form-data")

    assert post(io.BytesIO(b"not an image at all"), "fake.png").status_code == 400
    file, _ = png_file()
    assert post(file, "image.exe").status_code == 400
    assert post(io.BytesIO(b"<svg></svg>"), "image.svg").status_code == 400
    assert client.post(url, headers=admin).status_code == 400
    file, name = png_file()
    assert client.post(url, headers=auth("technician"), data={"photo": (file, name)}, content_type="multipart/form-data").status_code == 403


def test_replacing_photo_removes_old_file(users, client, auth, make_machine, app):
    import os

    make_machine()
    admin = auth("admin")
    paths = []
    for _ in range(2):
        file, name = png_file()
        client.post("/api/machines/M-001/photo", headers=admin, data={"photo": (file, name)}, content_type="multipart/form-data")
        paths.append(Machine.query.first().photo_path)
    root = app.config["UPLOAD_FOLDER"]
    assert paths[0] != paths[1]
    assert not os.path.exists(os.path.join(root, paths[0]))
    assert os.path.exists(os.path.join(root, paths[1]))
