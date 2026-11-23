"""Environment (location) awareness.

Normal vital signs depend on where the crew member is: cabin-altitude air
lowers SpO2, launch and landing loads raise heart rate, and long-duration
microgravity raises core body temperature. The same reading can be normal in
one place and a warning in another.

Each environment carries:
- ``shifts``: how the *expected* value of an indicator moves compared to
  Earth ground level. Added to every threshold (generic profile) or to the
  personal baseline (personal profile). A shift is either a number or
  ``{"value": x, "ramp_days": n}`` when the published data show a gradual
  adaptation (the shift then grows linearly over ``ramp_days``).
- ``spread_factor``: how much wider the personal tolerance band is. It is
  1.0 everywhere because no source supports a different value; the field is
  kept so it can be calibrated.
- ``absolute_overrides``: hard safety limits that differ by environment.
- ``basis`` / ``sources``: the evidence behind the numbers, with ids that
  point into ``REFERENCES`` (full citations are in docs/SOURCES.md).

Principles used to choose the numbers:
1. A shift is only applied where published measurements show a consistent
   change AND relaxing the limit does not risk masking a real problem.
2. Where the evidence is mixed or missing, the shift is 0 and the person's
   own baseline (``baseline_environment``) is the way to adapt.
3. Shifts that make limits more sensitive are preferred over ones that make
   them more lenient when the evidence gives a range.

The numbers are derived from small studies (8 to 11 astronauts) and
historical records; they have not been clinically validated and must be
reviewed by a flight surgeon before any real use.
"""

DEFAULT_ENVIRONMENT = "earth_ground"

# Evidence used below. Full citations: docs/SOURCES.md.
REFERENCES = {
    "stahn2017": {
        "citation": (
            "Stahn AC, Werner A, et al. Increased core body temperature in "
            "astronauts during long-duration space missions. Scientific "
            "Reports 7:16180 (2017)."
        ),
        "url": "https://pmc.ncbi.nlm.nih.gov/articles/PMC5701078",
        "finding": (
            "11 ISS astronauts: resting core temperature +1.01 C versus "
            "pre-flight, reaching a plateau around mission day 75; peak "
            "exercise temperature +1.39 C."
        ),
    },
    "norsk2015": {
        "citation": (
            "Norsk P, Asmar A, Damgaard M, Christensen NJ. Fluid shifts, "
            "vasodilatation and ambulatory blood pressure reduction during "
            "long duration spaceflight. J Physiol (2015)."
        ),
        "url": "https://www.sciencedaily.com/releases/2015/01/150114101638.htm",
        "finding": (
            "8 astronauts on long ISS missions: blood pressure about 10 mmHg "
            "lower in space; heart rate unchanged."
        ),
    },
    "hughson2017": {
        "citation": (
            "Hughson RL, Peterson SD, Yee NJ, Greaves DK. Cardiac output by "
            "pulse contour analysis does not match the increase measured by "
            "rebreathing during human spaceflight. J Appl Physiol "
            "123(5):1145-1149 (2017)."
        ),
        "url": "https://pmc.ncbi.nlm.nih.gov/articles/PMC5792103",
        "finding": (
            "9 astronauts: inflight heart rate 60 bpm vs 62 seated "
            "pre-flight; systolic 126.8 vs 133.8 mmHg seated pre-flight "
            "(not significant); diastolic 71.1 vs 70.5 mmHg."
        ),
    },
    "barger2014": {
        "citation": (
            "Barger LK, et al. Prevalence of sleep deficiency and use of "
            "hypnotic drugs in astronauts before, during, and after "
            "spaceflight. Lancet Neurology (2014)."
        ),
        "url": "https://www.news-medical.net/news/20140810/Space-missions-affect-sleep-patterns-in-astronauts.aspx",
        "finding": (
            "85 astronauts: about 6 h of sleep per night on the ISS against "
            "8.5 h scheduled; under 6.5 h in pre-flight training."
        ),
    },
    "nas2002": {
        "citation": (
            "National Research Council. The Airliner Cabin Environment and "
            "the Health of Passengers and Crew (2002), Table 5-3 and the "
            "discussion of FAR 25.841."
        ),
        "url": "https://www.nationalacademies.org/read/10238/chapter/7",
        "finding": (
            "Cabin pressure altitude is limited to 8,000 ft. Arterial O2 "
            "saturation: 96% at sea level, 95% at 5,000 ft, 93% at 7,500 ft, "
            "89% at 10,000 ft; healthy adults at 8,000 ft stay at or above "
            "90% (PaO2 above 60 mmHg)."
        ),
    },
    "apollo_lsah": {
        "citation": (
            "Petersen D, Charvat J, Somers J, Lee SMC, Pattarini J, Stenger "
            "MB, Van Baalen M. Apollo Commander cardiovascular data during "
            "lunar ascent and descent. NASA LSAH / JSC (NTRS 20200001709)."
        ),
        "url": "https://ntrs.nasa.gov/api/citations/20200001709/downloads/20200001709.pdf",
        "finding": (
            "5 Apollo Commanders: lunar ascent heart rate mean about 88 bpm "
            "(70-109) with a 10-20 bpm spike at liftoff; powered descent "
            "mean about 96 bpm (66-144), peaking near 120 bpm at touchdown "
            "(range 94-153)."
        ),
    },
    "edomp1996": {
        "citation": (
            "Charles JB, Fritsch-Yelle JM, Whitson PA, et al. "
            "Cardiovascular Deconditioning. Extended Duration Orbiter "
            "Medical Project, NASA Johnson Space Center (1996; NTRS "
            "20040201532)."
        ),
        "url": "https://ntrs.nasa.gov/api/citations/20040201532/downloads/20040201532.pdf",
        "finding": (
            "Shuttle crews (34 subjects): heart rate reached high values at "
            "peak gravity and touchdown; the highest value was 160 bpm on "
            "the first stand after landing."
        ),
    },
    "clement2017": {
        "citation": (
            "Clement G. International roadmap for artificial gravity "
            "research. npj Microgravity 3:29 (2017)."
        ),
        "url": "https://www.nature.com/articles/s41526-017-0034-8",
        "finding": (
            "The effects of Mars gravity (0.38 g) on human cardiovascular "
            "and other systems are unknown; the only data are from short "
            "parabolic-flight exposures."
        ),
    },
    "jones2021": {
        "citation": (
            "Jones HW. The Partial Gravity of the Moon and Mars Appears "
            "Insufficient to Maintain Human Health. ICES 2021 (NTRS "
            "20210019591)."
        ),
        "url": "https://ntrs.nasa.gov/citations/20210019591",
        "finding": (
            "Direct evidence of the long-term effects of partial gravity on "
            "humans is not yet available."
        ),
    },
}

_MICROGRAVITY_SHIFTS = {
    # Core temperature rises about 1 C over roughly 75 days (Stahn 2017).
    # Applied only when days_in_environment is known, so early-mission fever
    # is not hidden by a shift that has not developed yet.
    "body_temperature_c": {"value": 1.0, "ramp_days": 75},
    # Blood pressure: about 10 mmHg lower (Norsk 2015) vs 7 mmHg lower seated
    # systolic, not significant (Hughson 2017). The smaller magnitude is
    # applied to systolic only; diastolic did not change in Hughson 2017.
    "blood_pressure_systolic_mmhg": -7,
}
_MICROGRAVITY_BASIS = (
    "Core temperature rises about 1 C over roughly 75 days (applied "
    "gradually, and only when days_in_environment is given). Systolic blood "
    "pressure runs about 7-10 mmHg lower (the smaller figure is used). "
    "Resting heart rate is unchanged and average sleep is about 6 h against "
    "8.5 h scheduled, so neither limit is moved: a sleep shift would hide "
    "the sleep deficiency the data describe."
)
_MICROGRAVITY_SOURCES = ["stahn2017", "norsk2015", "hughson2017", "barger2014"]

ENVIRONMENTS = {
    "earth_ground": {
        "label": "Earth (ground level)",
        "description": "Normal gravity and pressure. Reference environment.",
        "basis": "Reference environment; generic thresholds apply as they are.",
        "sources": [],
        "shifts": {},
        "spread_factor": 1.0,
        "absolute_overrides": {},
    },
    "atmosphere": {
        "label": "Atmosphere (aircraft / high altitude)",
        "description": (
            "Pressurised cabin at altitude (up to 8,000 ft by regulation): "
            "lower oxygen availability gives lower SpO2."
        ),
        "basis": (
            "Arterial O2 saturation falls from 96% at sea level to 93% at "
            "7,500 ft, so SpO2 limits move down by 3 points. The 90% "
            "absolute floor is kept: healthy adults stay at or above it at "
            "8,000 ft. No consistent heart-rate change is documented, so "
            "none is applied."
        ),
        "sources": ["nas2002"],
        "shifts": {"spo2_percent": -3},
        "spread_factor": 1.0,
        "absolute_overrides": {},
    },
    "launch": {
        "label": "Launch / re-entry / landing (dynamic phases)",
        "description": (
            "High acceleration loads and high arousal: heart rate is "
            "expected to be high for a short time."
        ),
        "basis": (
            "Apollo Commanders peaked near 120 bpm (up to 153) during "
            "powered descent and Shuttle crews reached 160 bpm on the first "
            "stand after landing. The heart-rate limits move up by 30 bpm "
            "so that a 120 bpm peak (generic warning 90 + 30) is not "
            "flagged, and the absolute heart-rate ceiling is raised to "
            "160 bpm. No sourced values exist for other indicators, so "
            "they are unchanged."
        ),
        "sources": ["apollo_lsah", "edomp1996"],
        "shifts": {"resting_heart_rate_bpm": 30},
        "spread_factor": 1.0,
        "absolute_overrides": {"resting_heart_rate_bpm": {"high": 160}},
    },
    "iss": {
        "label": "Space station (ISS / low Earth orbit)",
        "description": (
            "Microgravity: core temperature runs about 1 C higher once "
            "adapted and systolic blood pressure is a few mmHg lower; "
            "resting heart rate is about the same."
        ),
        "basis": _MICROGRAVITY_BASIS,
        "sources": _MICROGRAVITY_SOURCES,
        "shifts": dict(_MICROGRAVITY_SHIFTS),
        "spread_factor": 1.0,
        "absolute_overrides": {},
    },
    "mars_transit": {
        "label": "Mars transit (deep space)",
        "description": (
            "Long-duration microgravity. Physiology is assumed to follow "
            "the space-station evidence; the radiation and isolation of "
            "deep space are not captured by the vitals."
        ),
        "basis": (
            _MICROGRAVITY_BASIS
            + " Assumption: deep-space transit is treated like low Earth "
            "orbit because no human vitals data exist beyond it."
        ),
        "sources": _MICROGRAVITY_SOURCES,
        "shifts": dict(_MICROGRAVITY_SHIFTS),
        "spread_factor": 1.0,
        "absolute_overrides": {},
    },
    "mars_surface": {
        "label": "Mars surface (0.38 g)",
        "description": (
            "Partial gravity. There is no human data on how vital signs "
            "behave at 0.38 g, so no shift is applied."
        ),
        "basis": (
            "Published reviews state that the cardiovascular effects of "
            "Mars gravity are unknown and that direct long-term human "
            "evidence is not available. No shift is applied; use "
            "baseline_environment to adapt once the crew member's own "
            "baseline has been recorded on the surface."
        ),
        "sources": ["clement2017", "jones2021"],
        "shifts": {},
        "spread_factor": 1.0,
        "absolute_overrides": {},
    },
}

# Telemetry limits used by detect_environment().
_ATMOSPHERE_MIN_KM = 0.5  # above this altitude we are no longer "on the ground"
_SPACE_MIN_KM = 100.0  # Karman line
_DEEP_SPACE_MIN_KM = 2000.0  # beyond low Earth orbit
_LAUNCH_MIN_G = 2.0  # sustained acceleration typical of ascent / re-entry
_MARS_SURFACE_MAX_KM = 0.5


def shift_for(env, field, days_in_environment=None):
    """Shift of `field` in environment `env` (a dict from ENVIRONMENTS).

    Plain shifts apply fully. A ramped shift grows linearly over its
    ``ramp_days``; when ``days_in_environment`` is unknown it is 0, the
    conservative choice (limits are not relaxed before the adaptation is
    known to have happened).
    """
    shift = env["shifts"].get(field, 0)
    if isinstance(shift, dict):
        if days_in_environment is None:
            return 0.0
        fraction = min(1.0, max(0.0, days_in_environment / shift["ramp_days"]))
        return shift["value"] * fraction
    return shift


def full_shift_for(env, field):
    """Fully developed shift of `field` (ramps completed)."""
    shift = env["shifts"].get(field, 0)
    return shift["value"] if isinstance(shift, dict) else shift


def list_environments():
    """All known environments with their adjustments and evidence."""
    return {
        "default": DEFAULT_ENVIRONMENT,
        "environments": [{"key": key, **env} for key, env in ENVIRONMENTS.items()],
        "references": REFERENCES,
    }


def get_environment(key: str):
    """Environment definition, or KeyError for an unknown key."""
    return ENVIRONMENTS[key]


def detect_environment(
    body: str = "earth", altitude_km: float = 0.0, accel_g: float = 1.0
):
    """Infer the environment from simple telemetry.

    body        "earth" or "mars" (the planet the crew is at or travelling from)
    altitude_km height above the surface of that body
    accel_g     sustained acceleration magnitude (1.0 = standing on Earth)

    Returns {"environment": key, "reason": text}. Sustained high
    acceleration near Earth is classified as launch/re-entry whatever the
    altitude, because it dominates the physiology.
    """
    body = body.lower()
    if body == "mars":
        if altitude_km <= _MARS_SURFACE_MAX_KM:
            return {
                "environment": "mars_surface",
                "reason": "on or near the Martian surface",
            }
        return {
            "environment": "mars_transit",
            "reason": "above the Martian surface, in transit or in orbit",
        }
    if body != "earth":
        raise ValueError(f"unknown body {body!r}; use 'earth' or 'mars'")

    if accel_g >= _LAUNCH_MIN_G:
        return {
            "environment": "launch",
            "reason": f"sustained acceleration of {accel_g:g} g (ascent / re-entry)",
        }
    if altitude_km < _ATMOSPHERE_MIN_KM:
        return {"environment": "earth_ground", "reason": "at ground level"}
    if altitude_km < _SPACE_MIN_KM:
        return {
            "environment": "atmosphere",
            "reason": f"{altitude_km:g} km, inside the atmosphere",
        }
    if altitude_km < _DEEP_SPACE_MIN_KM:
        return {
            "environment": "iss",
            "reason": f"{altitude_km:g} km, low Earth orbit",
        }
    return {
        "environment": "mars_transit",
        "reason": f"{altitude_km:g} km, beyond low Earth orbit (deep space)",
    }
