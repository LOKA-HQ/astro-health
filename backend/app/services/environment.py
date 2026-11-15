"""Live environment data: DONKI space weather and GOES radiation.

The prepared snapshots in data/ are served by default. refresh_*() fetch
fresh data from NASA DONKI and NOAA SWPC, rebuild the snapshots in the
same format, and persist them through the loader.

Notes:
- DONKI FLR endpoint returns 404; SEP/CME/GST/notifications work.
  Date range is capped at 30 days per request.
- DONKI works with DEMO_KEY; set NASA_API_KEY for higher rate limits.
- GOES proton flux needs no key.
"""

import logging
from datetime import UTC, date, datetime, timedelta

import httpx

from ..config import DONKI_BASE_URL, GOES_PROTONS_URL, NASA_API_KEY
from ..data import loader

logger = logging.getLogger(__name__)

HTTP_TIMEOUT = 30.0

# Max CME entries kept in the space-weather snapshot.
MAX_CME_SAMPLE = 20

# NOAA solar radiation storm scale (S-scale) thresholds for >=10 MeV
# integral proton flux, in pfu.
S_SCALE = {
    "S1 Minor": 10,
    "S2 Moderate": 100,
    "S3 Strong": 1000,
    "S4 Severe": 10000,
    "S5 Extreme": 100000,
}


def _now_iso():
    return datetime.now(UTC).isoformat()


def _s_scale(flux_pfu):
    """NOAA S-scale label for a >=10 MeV proton flux value."""
    if flux_pfu is None:
        return "no data"
    for label, threshold in sorted(S_SCALE.items(), key=lambda kv: -kv[1]):
        if flux_pfu >= threshold:
            return label
    return "quiet (below S1)"


def _donki(endpoint: str, start: date, end: date):
    """One DONKI request. Returns the parsed JSON list."""
    url = (
        f"{DONKI_BASE_URL}/{endpoint}"
        f"?startDate={start.isoformat()}&endDate={end.isoformat()}"
        f"&api_key={NASA_API_KEY}"
    )
    resp = httpx.get(url, timeout=HTTP_TIMEOUT)
    resp.raise_for_status()
    data = resp.json()
    if isinstance(data, dict):  # API error payload, e.g. bad date range
        raise ValueError(data.get("error") or data.get("msg") or str(data))
    return data


def refresh_space_weather():
    """Fetch the last 30 days of DONKI SEP/CME/GST events and rebuild the
    space-weather snapshot, preserving the demo case and alert mapping."""
    end = date.today()
    start = end - timedelta(days=30)
    sep = _donki("SEP", start, end)
    cme = _donki("CME", start, end)
    gst = _donki("GST", start, end)

    strongest_gst = None
    if gst:
        best = max(
            gst,
            key=lambda g: max(
                (k["kpIndex"] for k in g.get("allKpIndex", [])), default=0
            ),
        )
        kps = [k["kpIndex"] for k in best.get("allKpIndex", [])]
        strongest_gst = {
            "startTime": best.get("startTime"),
            "maxKp": max(kps) if kps else None,
            "link": best.get("link"),
        }

    cmes = [
        {
            "startTime": c.get("startTime"),
            "speed_kms": (c.get("cmeAnalyses") or [{}])[0].get("speed"),
            "sourceLocation": c.get("sourceLocation"),
            "note": (c.get("note") or "")[:120],
        }
        for c in cme
    ]

    prev = loader.SPACE_WEATHER
    snapshot = {
        "source": prev.get("source"),
        "note": prev.get("note"),
        "fetched_at": _now_iso(),
        "recent_30d": {
            "window": f"{start.isoformat()} to {end.isoformat()}",
            "sep_events": len(sep),
            "cme_events": len(cme),
            "gst_events": len(gst),
            "strongest_gst": strongest_gst,
            "cmes": cmes[:MAX_CME_SAMPLE],
        },
        "demo_radiation_alert_case": prev.get("demo_radiation_alert_case"),
        "alert_mapping": prev.get("alert_mapping"),
    }
    loader.set_space_weather(snapshot)
    logger.info(
        "space weather refreshed: %d SEP, %d CME, %d GST events",
        len(sep),
        len(cme),
        len(gst),
    )
    return {
        "status": "ok",
        "sep_events": len(sep),
        "cme_events": len(cme),
        "gst_events": len(gst),
        "fetched_at": snapshot["fetched_at"],
    }


def refresh_radiation():
    """Fetch 7 days of GOES-18 integral proton flux and rebuild the
    radiation snapshot, preserving the S-scale thresholds and published
    reference dose rates."""
    resp = httpx.get(GOES_PROTONS_URL, timeout=HTTP_TIMEOUT)
    resp.raise_for_status()
    raw = resp.json()

    # Hourly >=10 MeV flux (the NOAA S-scale channel).
    ch10 = sorted(
        (r for r in raw if r.get("energy") == ">=10 MeV"),
        key=lambda r: r["time_tag"],
    )
    hourly = {}
    for r in ch10:
        hourly.setdefault(r["time_tag"][:13], []).append(r["flux"])
    series = [
        {"time": h + ":00Z", "flux_pfu": round(sum(v) / len(v), 3)}
        for h, v in sorted(hourly.items())
    ]
    latest = series[-1]["flux_pfu"] if series else None
    peak = max((s["flux_pfu"] for s in series), default=None)

    prev = loader.RADIATION
    snapshot = {
        "source": prev.get("source"),
        "channel": prev.get("channel"),
        "fetched_at": _now_iso(),
        "window": ("7 days ending " + ch10[-1]["time_tag"]) if ch10 else None,
        "latest_flux_pfu": latest,
        "latest_status": _s_scale(latest),
        "peak_7d_flux_pfu": peak,
        "peak_status": _s_scale(peak),
        "noaa_s_scale_thresholds_pfu": prev.get("noaa_s_scale_thresholds_pfu"),
        "reference_dose_rates_published": prev.get("reference_dose_rates_published"),
        "hourly_flux_pfu": series,
    }
    loader.set_radiation(snapshot)
    logger.info(
        "radiation refreshed: %d hourly points, latest %s pfu (%s)",
        len(series),
        latest,
        _s_scale(latest),
    )
    return {
        "status": "ok",
        "hourly_points": len(series),
        "latest_flux_pfu": latest,
        "latest_status": _s_scale(latest),
        "fetched_at": snapshot["fetched_at"],
    }


def refresh_all():
    """Refresh both live snapshots. Each source is attempted independently;
    a failure in one does not block the other."""
    results = {}
    for name, fn in (
        ("space_weather", refresh_space_weather),
        ("radiation", refresh_radiation),
    ):
        try:
            results[name] = fn()
        except Exception as e:  # noqa: BLE001 - error surfaced in the response
            logger.warning("refresh failed for %s: %s", name, e)
            results[name] = {"status": "error", "error": str(e)}
    return results
