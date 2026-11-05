import io
import re

from PIL import Image

from app.models import AuditLog, Machine
from app.services import qr_service

from .test_machines import NEW_MACHINE


def pdf_page_count(data):
    return len(re.findall(rb"/Type\s*/Page(?!s)", data))


def test_qr_url_uses_public_base_url_code_and_version(app, make_machine):
    app.config["PUBLIC_BASE_URL"] = "https://qr.example.com/"
    machine = make_machine()
    assert qr_service.build_qr_url(machine) == "https://qr.example.com/machine/M-001?v=1"


def test_qr_payload_is_only_the_url(app, make_machine):
    machine = make_machine(serial_number="SECRET-SN", plc_model="S7-1200")
    url = qr_service.build_qr_url(machine)
    encoded = qr_service.make_qr(url).data_list[0].data
    assert encoded == url.encode()
    assert b"SECRET-SN" not in encoded and b"S7-1200" not in encoded


def test_admin_downloads_png(users, client, auth, make_machine):
    make_machine()
    res = client.get("/api/machines/M-001/qr.png", headers=auth("admin"))
    assert res.status_code == 200 and res.mimetype == "image/png"
    image = Image.open(io.BytesIO(res.data))
    assert image.format == "PNG" and image.width == image.height >= 300
    assert res.headers["Cache-Control"] == "private, no-store"


def test_admin_downloads_single_label_pdf(users, client, auth, make_machine):
    make_machine()
    res = client.get("/api/machines/M-001/qr-label.pdf", headers=auth("admin"))
    assert res.status_code == 200 and res.mimetype == "application/pdf"
    assert res.data.startswith(b"%PDF") and pdf_page_count(res.data) == 1


def test_label_handles_non_latin_and_long_names(users, client, auth, make_machine):
    make_machine(name="प्रेस मशीन Press " + "very long name " * 20)
    res = client.get("/api/machines/M-001/qr-label.pdf", headers=auth("admin"))
    assert res.status_code == 200 and res.data.startswith(b"%PDF")


def test_sheet_paginates_twelve_labels_per_page(users, client, auth, make_machine):
    for number in range(1, 14):
        make_machine(code=f"M-{number:03d}", name=f"Machine {number}")
    res = client.get("/api/machines/qr-sheet.pdf", headers=auth("admin"))
    assert res.status_code == 200 and pdf_page_count(res.data) == 2


def test_sheet_with_selected_codes_and_validation(users, client, auth, make_machine):
    make_machine(code="M-001")
    make_machine(code="M-002", name="B")
    make_machine(code="M-003", name="C", is_active=False)
    headers = auth("admin")
    ok = client.get("/api/machines/qr-sheet.pdf?codes=m-001,M-002", headers=headers)
    assert ok.status_code == 200 and pdf_page_count(ok.data) == 1
    assert client.get("/api/machines/qr-sheet.pdf?codes=M-001,M-404", headers=headers).status_code == 400
    assert client.get("/api/machines/qr-sheet.pdf?codes=M-003", headers=headers).status_code == 400
    too_many = ",".join(f"M-{n:03d}" for n in range(1, 202))
    assert client.get(f"/api/machines/qr-sheet.pdf?codes={too_many}", headers=headers).status_code == 400


def test_empty_sheet_is_rejected(users, client, auth):
    assert client.get("/api/machines/qr-sheet.pdf", headers=auth("admin")).status_code == 400


def test_only_admin_can_use_qr_endpoints(users, client, auth, make_machine, assign):
    machine = make_machine()
    assign(machine, users["technician"], users["operator"])
    urls = [
        ("get", "/api/machines/M-001/qr.png"),
        ("get", "/api/machines/M-001/qr-label.pdf"),
        ("get", "/api/machines/qr-sheet.pdf"),
        ("post", "/api/machines/M-001/qr/regenerate"),
    ]
    for role in ("technician", "operator"):
        for method, url in urls:
            assert getattr(client, method)(url, headers=auth(role)).status_code == 403
    for method, url in urls:
        assert getattr(client, method)(url).status_code == 401


def test_downloads_are_audited(users, client, auth, make_machine):
    make_machine()
    headers = auth("admin")
    client.get("/api/machines/M-001/qr.png", headers=headers)
    client.get("/api/machines/M-001/qr-label.pdf", headers=headers)
    client.get("/api/machines/qr-sheet.pdf", headers=headers)
    assert AuditLog.query.filter_by(action="qr_downloaded").count() == 3


def test_new_machine_has_qr_metadata_for_admin(users, client, auth):
    headers = auth("admin")
    machine = client.post("/api/machines", headers=headers, json=NEW_MACHINE).get_json()["machine"]
    assert machine["qr_version"] == 1 and machine["qr_generated_at"]
    assert machine["qr_url"].endswith("/machine/M-001?v=1")
    assert Machine.query.first().qr_generated_at is not None


def test_qr_metadata_hidden_from_non_admins(users, client, auth, make_machine, assign):
    machine = make_machine()
    assign(machine, users["technician"], users["operator"])
    for role in ("technician", "operator"):
        body = client.get("/api/machines/M-001", headers=auth(role)).get_json()["machine"]
        assert "qr_url" not in body and "qr_version" not in body


def test_regenerate_bumps_version_and_invalidates_old_label(users, client, auth, make_machine, assign):
    machine = make_machine()
    assign(machine, users["technician"])
    admin, tech = auth("admin"), auth("technician")
    assert client.get("/api/machines/M-001?v=1", headers=tech).status_code == 200

    res = client.post("/api/machines/M-001/qr/regenerate", headers=admin)
    body = res.get_json()["machine"]
    assert res.status_code == 200 and body["qr_version"] == 2
    assert body["qr_url"].endswith("?v=2")
    assert AuditLog.query.filter_by(action="machine_qr_regenerated").count() == 1

    old = client.get("/api/machines/M-001?v=1", headers=tech)
    assert old.status_code == 410 and "outdated" in old.get_json()["error"]
    assert client.get("/api/machines/M-001?v=2", headers=tech).status_code == 200
    assert client.get("/api/machines/M-001", headers=tech).status_code == 200


def test_version_check_never_hides_access_errors(users, client, auth, make_machine):
    make_machine()
    assert client.get("/api/machines/M-001?v=99", headers=auth("technician")).status_code == 403
    assert client.get("/api/machines/M-001?v=99").status_code == 401
    assert client.get("/api/machines/M-001?v=abc", headers=auth("admin")).status_code == 400


def test_png_preview_is_not_audited_as_download(users, client, auth, make_machine):
    make_machine()
    headers = auth("admin")
    assert client.get("/api/machines/M-001/qr.png?preview=1", headers=headers).status_code == 200
    assert AuditLog.query.filter_by(action="qr_downloaded").count() == 0
    client.get("/api/machines/M-001/qr.png", headers=headers)
    assert AuditLog.query.filter_by(action="qr_downloaded").count() == 1
