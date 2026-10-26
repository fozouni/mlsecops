from fastapi.testclient import TestClient
from importlib import import_module

final = import_module("final")
client = TestClient(final.app)


def test_alice_cannot_read_admin_info():
    tok = final.issue(final.USERS["alice"], ["predict"])
    r = client.get("/admin/model-info", headers={"Authorization": f"Bearer {tok}"})
    assert r.status_code == 403


def test_admin_can_read_model_info():
    tok = final.issue(final.USERS["admin"], ["predict", "admin"])
    r = client.get("/admin/model-info", headers={"Authorization": f"Bearer {tok}"})
    assert r.status_code == 200
