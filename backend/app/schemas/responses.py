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


class AlertsResponse(BaseModel):
    alerts: list[Alert]
    count: int


class HealthResponse(BaseModel):
    status: str
    crew: int
    lab_records: int
    flagged_total: int
    space_weather_fetched_at: str | None = None
    radiation_fetched_at: str | None = None
