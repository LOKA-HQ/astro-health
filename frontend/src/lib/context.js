// Personal thresholds and environment awareness: the pure logic behind the
// "Thresholds" page. No React and no network, so it can be tested directly.
// It returns data (keys, numbers); the page turns it into translated text.

export const DEFAULT_ENVIRONMENT = 'earth_ground';
export const MAX_DAYS_IN_ENVIRONMENT = 3650; // same bound as the API

export const INDICATOR_UNITS = {
  resting_heart_rate_bpm: 'bpm',
  sleep_hours: 'h',
  sleep_quality: '%',
  spo2_percent: '%',
  stress_score: '',
  blood_pressure_systolic_mmhg: 'mmHg',
  blood_pressure_diastolic_mmhg: 'mmHg',
  body_temperature_c: '°C',
  mood_score: '/ 10',
};

/**
 * "Days in environment" as typed by the user -> whole number the API accepts,
 * or null when it is blank or not a number (the API then applies no gradual
 * shifts). Negative values become 0 and large ones are capped.
 */
export function parseDays(value) {
  if (value === '' || value == null) return null;
  const n = Number(value);
  if (!Number.isFinite(n)) return null;
  return Math.min(MAX_DAYS_IN_ENVIRONMENT, Math.max(0, Math.trunc(n)));
}

/**
 * Where the personal baseline was recorded. "preflight": on Earth, before the
 * crew member reached this environment. "inplace": in the environment itself,
 * so the person is already adapted and no shift is applied.
 */
export const baselineEnvironmentFor = (environment, mode) =>
  mode === 'inplace' ? environment : DEFAULT_ENVIRONMENT;

/**
 * Query string for the threshold-aware endpoints (thresholds, assessment).
 * `ctx` is { profile, environment, baselineMode, daysInEnvironment }; `extra`
 * adds endpoint parameters such as { days: 7 }.
 */
export function contextQuery(ctx, extra = {}) {
  const params = new URLSearchParams({
    profile: ctx.profile,
    environment: ctx.environment,
    baseline_environment: baselineEnvironmentFor(ctx.environment, ctx.baselineMode),
  });
  const days = parseDays(ctx.daysInEnvironment);
  if (days !== null) params.set('days_in_environment', String(days));
  for (const [k, v] of Object.entries(extra)) params.set(k, String(v));
  return '?' + params.toString();
}

/** Query string for GET /environments/detect. */
export function detectQuery({ body = 'earth', altitudeKm = 0, accelG = 1 }) {
  const params = new URLSearchParams({
    body,
    altitude_km: String(Math.max(0, Number(altitudeKm) || 0)),
    accel_g: String(Math.max(0, Number(accelG) || 0)),
  });
  return '?' + params.toString();
}

/** Environment definition with this key, from GET /environments. */
export const findEnvironment = (list, key) =>
  (list?.environments || []).find((e) => e.key === key) || null;

/**
 * True when the environment has a shift that develops gradually (core
 * temperature in microgravity ramps in over 75 days). Only then does "days
 * in environment" change anything, so only then is it worth asking for.
 */
export const hasRamp = (env) =>
  Object.values(env?.shifts || {}).some(
    (s) => s !== null && typeof s === 'object' && 'ramp_days' in s,
  );

const fmtLimit = (v) => String(Number(Number(v).toFixed(2)));

/**
 * A limit pair as text: "< 55 or > 90", "> 90" or "< 94" ("—" if neither).
 * `low` is the lower limit, `high` the upper one; a value outside is flagged.
 * `orWord` is the word between the two limits (translated by the page).
 */
export function limitsText(low, high, orWord = 'or') {
  const parts = [];
  if (low != null) parts.push(`< ${fmtLimit(low)}`);
  if (high != null) parts.push(`> ${fmtLimit(high)}`);
  return parts.length ? parts.join(` ${orWord} `) : '—';
}

/** "71 ± 7.4": the person's own typical value and spread; "—" for generic. */
export const baselineText = (rec) =>
  rec?.baseline_median == null || rec?.sigma == null
    ? '—'
    : `${fmtLimit(rec.baseline_median)} ± ${fmtLimit(rec.sigma)}`;

/** "+1.2 σ" / "-0.4 σ" for a deviation from the personal baseline. */
export const deviationText = (d) => (d == null ? '—' : `${d > 0 ? '+' : ''}${d.toFixed(1)} σ`);

/** Latest assessed status of one indicator, or null when not loaded. */
export function latestIndicator(assessment, field) {
  const day = assessment?.days?.at(-1);
  return day?.indicators?.find((i) => i.indicator === field) || null;
}

/**
 * Rows of the limits table: one per vitals indicator, combining the limits in
 * force (GET /thresholds) with the latest day's judgement (GET /assessment).
 */
export function thresholdRows(thresholds, assessment, orWord = 'or') {
  return Object.entries(thresholds?.indicators || {}).map(([field, rec]) => {
    const th = rec.thresholds || {};
    const generic = rec.generic || {};
    const latest = latestIndicator(assessment, field);
    return {
      field,
      unit: INDICATOR_UNITS[field] ?? '',
      personal: rec.source === 'personal',
      source: rec.source,
      baseline: baselineText(rec),
      shift: rec.environment_shift || 0,
      tolerance: rec.environment_tolerance_high || 0,
      warning: limitsText(th.warning_low, th.warning_high, orWord),
      critical: limitsText(th.critical_low, th.critical_high, orWord),
      genericWarning: limitsText(generic.warning_low, generic.warning_high, orWord),
      value: latest ? latest.value : null,
      status: latest ? latest.status : null,
      deviation: latest?.deviation_sigma ?? null,
      note: rec.baseline_note || null,
    };
  });
}

/**
 * Which sentence describes the limits in force: { key, n }. The page looks
 * `key` up in its strings and fills in `n` (days of history).
 */
export function summaryKind(thresholds) {
  if (!thresholds) return null;
  const n = thresholds.baseline_days || 0;
  if (thresholds.profile === 'personal') {
    return { key: n > 0 ? 'th_sumPersonal' : 'th_sumFewDays', n };
  }
  return { key: 'th_sumGeneric', n };
}

/** Telemetry examples for the "detect environment" panel. */
export const DETECT_PRESETS = [
  { key: 'ground', body: 'earth', altitudeKm: 0, accelG: 1 },
  { key: 'aircraft', body: 'earth', altitudeKm: 10, accelG: 1 },
  { key: 'launch', body: 'earth', altitudeKm: 60, accelG: 3 },
  { key: 'station', body: 'earth', altitudeKm: 408, accelG: 0 },
  { key: 'deepSpace', body: 'earth', altitudeKm: 400000, accelG: 0 },
  { key: 'marsSurface', body: 'mars', altitudeKm: 0, accelG: 0.38 },
];

/**
 * Horizontal limit lines for the chart of one indicator: the limits in force
 * (tone "warning" or "critical") and the generic warning limits for comparison
 * (tone "generic") when they differ. Each line has a `side`, "high" or "low".
 */
export function chartLimits(rec) {
  if (!rec) return [];
  const th = rec.thresholds || {};
  const generic = rec.generic || {};
  const lines = [];
  for (const side of ['high', 'low']) {
    const warn = th[`warning_${side}`];
    const crit = th[`critical_${side}`];
    const gen = generic[`warning_${side}`];
    if (crit != null) lines.push({ y: crit, tone: 'critical', side });
    if (warn != null) lines.push({ y: warn, tone: 'warning', side });
    if (gen != null && warn != null && Math.abs(gen - warn) > 0.005) {
      lines.push({ y: gen, tone: 'generic', side });
    }
  }
  return lines;
}

/** A number with its sign: "+1", "−0.5" (a real minus sign), "0". */
export const signed = (n) => `${n > 0 ? '+' : n < 0 ? '−' : ''}${fmtLimit(Math.abs(n))}`;

/** `text` followed by the indicator's unit, when it has one. */
export const withUnit = (field, text) => {
  const unit = INDICATOR_UNITS[field];
  return unit ? `${text} ${unit}` : text;
};

/**
 * What an environment changes, as data the page can word in any language:
 * - shifts:     [{ field, value, rampDays }] expected value moves (rampDays is
 *               null for an immediate shift)
 * - tolerances: [{ field, high }] upper limits move, lower limits do not
 * - limits:     [{ field, side, value }] hard limits that are always critical
 */
export function environmentFacts(env) {
  const shifts = Object.entries(env?.shifts || {}).map(([field, s]) =>
    s !== null && typeof s === 'object'
      ? { field, value: s.value, rampDays: s.ramp_days ?? null }
      : { field, value: s, rampDays: null },
  );
  const tolerances = Object.entries(env?.tolerances || {})
    .filter(([, t]) => t.high != null)
    .map(([field, t]) => ({ field, high: t.high }));
  const limits = [];
  for (const [field, o] of Object.entries(env?.absolute_overrides || {})) {
    if (o.high != null) limits.push({ field, side: 'high', value: o.high });
    if (o.low != null) limits.push({ field, side: 'low', value: o.low });
  }
  return { shifts, tolerances, limits };
}

/** "Hello {name}" with { name: 'x' } -> "Hello x". Unknown names are left as written. */
export const fill = (template, values = {}) =>
  String(template ?? '').replace(/\{(\w+)\}/g, (m, k) => (k in values ? values[k] : m));
