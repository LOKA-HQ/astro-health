"""API smoke tests.

Run from backend/:  pytest -q
Covers every read endpoint, filters, pagination, 404 handling, and the
determinism of generated vitals. The live refresh endpoint is not tested
here because it calls external APIs (NASA DONKI, NOAA SWPC).
"""

from fastapi.testclient import TestClient

from app.main import create_app

client = TestClient(create_app())


def test_root():
    r = client.get("/")
    assert r.status_code == 200
    assert r.json()["crew"] == ["C001", "C002", "C003", "C004"]


def test_health():
    r = client.get("/health")
    assert r.status_code == 200
    body = r.json()
    assert body["status"] == "ok"
    assert body["crew"] == 4
    assert body["lab_records"] == 13193


def test_crew_list():
    r = client.get("/api/v1/crew")
    assert r.status_code == 200
    crew = {c["crew_id"]: c for c in r.json()["crew"]}
    assert len(crew) == 4
    # Known ground truth from the prepared data.
    assert crew["C001"]["clinical_out_of_range"] == 2
    assert crew["C003"]["clinical_out_of_range"] == 20


def test_crew_summary():
    r = client.get("/api/v1/crew/C003/summary")
    assert r.status_code == 200
    body = r.json()
    assert body["flagged_total"] == 456
    assert body["vitals"]["days"] == 30
    assert body["vitals"]["alert_days"] == 2


def test_crew_labs_filters_and_pagination():
    r = client.get("/api/v1/crew/C001/labs?flagged_only=true&limit=2")
    assert r.status_code == 200
    body = r.json()
    assert body["total"] == 241
    assert len(body["records"]) == 2
    assert all(rec["status"] != "normal" for rec in body["records"])

    r = client.get("/api/v1/crew/C001/labs?panel=blood_count&limit=5&offset=5")
    assert r.status_code == 200
    body = r.json()
    assert body["offset"] == 5
    assert all(rec["panel"] == "blood_count" for rec in body["records"])


def test_crew_vitals_deterministic():
    # Generated vitals (C002) must be identical across calls.
    r1 = client.get("/api/v1/crew/C002/vitals")
    r2 = client.get("/api/v1/crew/C002/vitals")
    assert r1.status_code == 200 == r2.status_code
    assert r1.json() == r2.json()
    assert len(r1.json()["days"]) == 30


def test_crew_report():
    r = client.get("/api/v1/crew/C001/report")
    assert r.status_code == 200
    body = r.json()
    assert body["vitals_7d"]["alert_days"] >= 0
    assert body["overall_status"] in ("nominal", "attention")


def test_alerts():
    r = client.get("/api/v1/alerts")
    assert r.status_code == 200
    body = r.json()
    assert body["count"] == len(body["alerts"])
    assert body["count"] == 48  # 38 clinical + 9 vitals days + 1 radiation
    assert any(a["type"] == "radiation" for a in body["alerts"])


def test_environment_endpoints():
    for path in (
        "/api/v1/space-weather",
        "/api/v1/radiation",
        "/api/v1/thresholds",
        "/api/v1/omics",
    ):
        r = client.get(path)
        assert r.status_code == 200, path


def test_unknown_crew_404():
    r = client.get("/api/v1/crew/C999/summary")
    assert r.status_code == 404


def test_labs_invalid_pagination_422():
    # Negative or over-max limit/offset must be rejected, not silently
    # mis-sliced.
    for query in ("limit=-1", "limit=2000", "offset=-5"):
        r = client.get(f"/api/v1/crew/C001/labs?{query}")
        assert r.status_code == 422, query


def test_labs_offset_beyond_total():
    r = client.get("/api/v1/crew/C001/labs?offset=99999")
    assert r.status_code == 200
    body = r.json()
    assert body["total"] == 3047
    assert body["records"] == []


def test_crew_vitals_days_param():
    r = client.get("/api/v1/crew/C002/vitals?days=7")
    assert r.status_code == 200
    days = r.json()["days"]
    assert len(days) == 7
    # The last 7 days of the 30-day series.
    full = client.get("/api/v1/crew/C002/vitals").json()["days"]
    assert days == full[-7:]

    for bad in ("days=0", "days=31", "days=-3"):
        r = client.get(f"/api/v1/crew/C002/vitals?{bad}")
        assert r.status_code == 422, bad


def test_crew_alerts():
    # C003: 20 clinical out-of-range + 2 vitals alert days.
    r = client.get("/api/v1/crew/C003/alerts")
    assert r.status_code == 200
    body = r.json()
    assert body["count"] == 22
    assert all(a["crew_id"] == "C003" for a in body["alerts"])
    # The radiation alert is global, not per-crew.
    assert all(a["type"] != "radiation" for a in body["alerts"])

    r = client.get("/api/v1/crew/C999/alerts")
    assert r.status_code == 404


def test_alerts_sorted_by_severity():
    r = client.get("/api/v1/alerts")
    assert r.status_code == 200
    ranks = {"critical": 0, "warning": 1, "info": 2}
    levels = [ranks[a["level"]] for a in r.json()["alerts"]]
    assert levels == sorted(levels)
    assert r.json()["alerts"][-1]["type"] == "radiation"


def test_vitals_alerts_use_thresholds():
    # Generated vitals alert messages must reference the warning
    # thresholds served by /thresholds, not hardcoded numbers.
    t = client.get("/api/v1/thresholds").json()
    hr = t["resting_heart_rate_bpm"]["warning_high"]
    sleep = t["sleep_hours"]["warning_low"]
    spo2 = t["spo2_percent"]["warning_low"]
    bp_sys = t["blood_pressure_systolic_mmhg"]["warning_high"]
    bp_dia = t["blood_pressure_diastolic_mmhg"]["warning_high"]
    temp = t["body_temperature_c"]["warning_high"]
    days = client.get("/api/v1/crew/C002/vitals").json()["days"]
    alert_msgs = [a["message"] for d in days for a in d["alerts"]]
    assert alert_msgs, "expected at least one vitals alert day"
    for m in alert_msgs:
        assert m in (
            f"Resting heart rate above {hr} BPM",
            f"Sleep under {sleep} hours",
            f"SpO2 below {spo2}%",
            "Stress score elevated",
            f"Blood pressure above {bp_sys}/{bp_dia} mmHg",
            f"Body temperature above {temp} C",
            f"Body temperature below {t['body_temperature_c']['warning_low']} C",
            "Mood score low",
        ), m


def test_vitals_new_indicators():
    # Blood pressure, body temperature, and mood are present for every
    # crew member, in range on normal days and flagged on alert days.
    for crew_id in ("C001", "C002", "C003", "C004"):
        days = client.get(f"/api/v1/crew/{crew_id}/vitals").json()["days"]
        assert len(days) == 30, crew_id
        for d in days:
            assert 90 <= d["blood_pressure_systolic_mmhg"] <= 160, d
            assert 55 <= d["blood_pressure_diastolic_mmhg"] <= 105, d
            assert 35.0 <= d["body_temperature_c"] <= 39.5, d
            assert 1 <= d["mood_score"] <= 10, d
            if d["status"] == "nominal":
                assert d["blood_pressure_systolic_mmhg"] <= 140, d
                assert d["body_temperature_c"] < 38.0, d
                assert d["mood_score"] >= 4, d
        alert_days = [d for d in days if d["status"] != "nominal"]
        assert alert_days, crew_id
        assert any(
            a["indicator"] in ("blood_pressure", "body_temperature", "mood")
            for d in alert_days
            for a in d["alerts"]
        ), crew_id

    # Summary and report carry the new averages.
    s = client.get("/api/v1/crew/C001/summary").json()["vitals"]
    assert 36.0 <= s["avg_body_temperature_c"] <= 38.0
    assert 1 <= s["avg_mood_score"] <= 10
    r = client.get("/api/v1/crew/C001/report").json()["vitals_7d"]
    assert 36.0 <= r["avg_body_temperature_c"] <= 38.0
    assert 1 <= r["avg_mood_score"] <= 10
