"""Pydantic response models.

Models define the exact shape of API responses and power the OpenAPI docs
at /docs. Environment endpoints (space weather, radiation, thresholds,
omics) return free-form dicts and are not modeled here.
"""

from pydantic import BaseModel


class LabRecord(BaseModel):
    crew: str
    timepoint: str
    phase: str
    panel: str
    study: str
    indicator: str
    unit: str
    value: float
    # Clinical panels have reference ranges; immune panels have a personal
    # baseline median instead. Exactly one of the two is set.
    ref_min: float | None = None
    ref_max: float | None = None
    baseline_median: float | None = None
    status: str


class VitalsAlert(BaseModel):
    indicator: str
    level: str
    message: str


class VitalsDay(BaseModel):
    date: str
    mission_day: int
    resting_heart_rate_bpm: int
    sleep_hours: float
    sleep_quality: int
    steps: int
    spo2_percent: float
    stress_score: int
    blood_pressure_systolic_mmhg: int
    blood_pressure_diastolic_mmhg: int
    body_temperature_c: float
    mood_score: int
    status: str
    alerts: list[VitalsAlert]


class Alert(BaseModel):
    level: str  # critical | warning | info
    type: str  # lab | vitals | radiation
    message: str
    # Provenance of the underlying data: "real" (NASA OSDR Inspiration4),
    # "real_live" (NOAA/NASA live feeds) or "synthetic" (generated demo
    # vitals). Lets clients label synthetic alerts in the UI.
    data_source: str | None = None
    crew_id: str | None = None
    timepoint: str | None = None
    indicator: str | None = None
    value: float | None = None
    unit: str | None = None
    ref_range: list[float | None] | None = None
    date: str | None = None
    mission_day: int | None = None
    alerts: list[VitalsAlert] | None = None
    source: str | None = None
    latest_flux_pfu: float | None = None
    status: str | None = None


class CrewListItem(BaseModel):
    crew_id: str
    lab_records: int
    flagged: int
    clinical_out_of_range: int
    timepoints: list[str]


class CrewListResponse(BaseModel):
    crew: list[CrewListItem]


class FlaggedIndicator(BaseModel):
    indicator: str
    count: int


class VitalsSummary(BaseModel):
    source: str
    days: int
    latest: VitalsDay
    alert_days: int
    avg_resting_hr: float
    avg_sleep_hours: float
    avg_body_temperature_c: float
    avg_mood_score: float


class CrewSummary(BaseModel):
    crew_id: str
    lab_records: int
    flagged_total: int
    clinical_out_of_range: int
    top_flagged_indicators: list[FlaggedIndicator]
    vitals: VitalsSummary


class LabsResponse(BaseModel):
    crew_id: str
    total: int
    limit: int
    offset: int
    records: list[LabRecord]


class VitalsResponse(BaseModel):
    crew_id: str
    source: str
    days: list[VitalsDay]


class ReportVitals7d(BaseModel):
    avg_resting_hr: float
    avg_sleep_hours: float
    avg_stress: float
    avg_body_temperature_c: float
    avg_mood_score: float
    min_spo2: float
    alert_days: int


class ReportLabs(BaseModel):
    flagged_total: int
    clinical_out_of_range: int
    top_flagged_indicators: list[FlaggedIndicator]


class CrewReport(BaseModel):
    crew_id: str
    period: str
    vitals_7d: ReportVitals7d
    labs: ReportLabs
    overall_status: str


class ForecastIndicator(BaseModel):
    indicator: str
    direction: str  # high | low: which side of the threshold is bad
    threshold: float
    current_fit: float
    projected: float
    slope_per_day: float
    days_to_breach: int | None = None  # None: no breach within the horizon
    risk: str  # low | moderate | high


class CrewForecast(BaseModel):
    crew_id: str
    profile: str = "generic"
    environment: str = "earth_ground"
    method: str
    window_days: int
    horizon_days: int
    data_source: str
    disclaimer: str
    overall_risk: str
    indicators: list[ForecastIndicator]


class ThresholdIndicator(BaseModel):
    threshold_key: str
    source: str  # generic | personal | generic_fallback
    generic: dict[str, float]  # the fixed thresholds for comparison
    thresholds: dict[str, float]  # the limits actually in force
    environment_shift: float
    # Personal profile only:
    baseline_median: float | None = None
    baseline_days: int | None = None
    expected_value: float | None = None  # baseline moved to this environment
    sigma: float | None = None  # robust spread used for the limits
    baseline_outside_generic_normal: bool | None = None
    baseline_note: str | None = None


class CrewThresholds(BaseModel):
    crew_id: str
    profile: str  # generic | personal
    environment: str
    baseline_environment: str
    days_in_environment: int | None = None
    baseline_days: int  # 0 when the generic thresholds are used
    indicators: dict[str, ThresholdIndicator]


class AssessmentIndicator(BaseModel):
    indicator: str
    value: float
    status: str  # nominal | warning | critical
    side: str | None = None  # high | low, when not nominal
    limit: float | None = None
    deviation_sigma: float | None = None  # personal profile only
    message: str


class AssessmentDay(BaseModel):
    date: str
    mission_day: int
    status: str
    indicators: list[AssessmentIndicator]


class CrewAssessment(BaseModel):
    crew_id: str
    profile: str
    environment: str
    baseline_environment: str
    days_in_environment: int | None = None
    data_source: str
    latest_status: str
    days: list[AssessmentDay]


class AlertsResponse(BaseModel):
    alerts: list[Alert]
    count: int
    profile: str | None = None
    environment: str | None = None


class HealthResponse(BaseModel):
    status: str
    crew: int
    lab_records: int
    flagged_total: int
    space_weather_fetched_at: str | None = None
    radiation_fetched_at: str | None = None
