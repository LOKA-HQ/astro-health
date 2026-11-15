"""Light security tests.

The API serves public demo data with no auth, no user input stored, and
no database, so the checks here stay light: unknown identifiers must 404
instead of leaking anything, hostile-looking input must not crash or
alter queries, and error responses must not expose internals.

Run from backend/:  pytest -q tests/test_security.py
"""

from fastapi.testclient import TestClient

from app.main import create_app

client = TestClient(create_app())


def test_traversal_crew_ids_404():
    # Path traversal attempts must 404, never reach the filesystem.
    for crew_id in ("..", "..%2F..%2Fetc", "C001%2F..%2F..%2Fetc%2Fpasswd"):
        r = client.get(f"/api/v1/crew/{crew_id}/summary")
        assert r.status_code == 404, crew_id
        assert "root:" not in r.text  # no /etc/passwd content


def test_injection_strings_are_harmless():
    # SQL/NoSQL-style input is treated as a plain filter value: no crash,
    # no extra rows.
    for query in (
        "panel=blood_count' OR '1'='1",
        "panel=%24where",
        "status=<script>alert(1)</script>",
        "timepoint=R%2B1'; DROP TABLE users;--",
    ):
        r = client.get(f"/api/v1/crew/C001/labs?{query}")
        assert r.status_code == 200, query
        assert r.json()["total"] == 0


def test_error_responses_hide_internals():
    # 404/422 bodies must not include stack traces or filesystem paths.
    for url in (
        "/api/v1/crew/C999/summary",
        "/api/v1/crew/C001/labs?limit=-1",
        "/api/v1/no-such-endpoint",
    ):
        r = client.get(url)
        assert r.status_code in (404, 422), url
        body = r.text.lower()
        assert "traceback" not in body
        assert "/home/" not in body
        assert ".py" not in body


def test_very_long_crew_id_404():
    r = client.get("/api/v1/crew/" + "C" * 1000 + "/summary")
    assert r.status_code == 404


def test_refresh_requires_post():
    # The live-refresh endpoint is POST-only.
    r = client.get("/api/v1/environment/refresh")
    assert r.status_code == 405


def test_api_responses_are_json():
    r = client.get("/api/v1/crew")
    assert r.status_code == 200
    assert r.headers["content-type"].startswith("application/json")


def test_cors_allows_local_frontend_but_not_arbitrary_origins():
    allowed = client.options(
        "/api/v1/crew",
        headers={
            "Origin": "http://localhost:5173",
            "Access-Control-Request-Method": "GET",
        },
    )
    assert allowed.status_code == 200
    assert allowed.headers.get("access-control-allow-origin") == "http://localhost:5173"

    denied = client.options(
        "/api/v1/crew",
        headers={
            "Origin": "https://untrusted.example",
            "Access-Control-Request-Method": "GET",
        },
    )
    assert "access-control-allow-origin" not in denied.headers
