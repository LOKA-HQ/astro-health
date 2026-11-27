// Pure formatting and label helpers. Functions that need translations take
// the active strings object (t) as their first argument.

// snake_case identifier to Title Case words.
export const pretty = (s) =>
  (s || '').replaceAll('_', ' ').replace(/\b\w/g, (c) => c.toUpperCase());

// Number with n decimals; null/undefined renders as an em dash.
export const fmt = (v, n = 1) => (v == null ? '—' : Number(v).toFixed(n));

// Pill tone for an alert level (critical/warning/other).
export const levelColor = (l) => (l === 'critical' ? 'red' : l === 'warning' ? 'amber' : 'blue');

// Pill tone for a forecast risk (high/moderate/low).
export const riskTone = (r) => (r === 'high' ? 'red' : r === 'moderate' ? 'amber' : 'green');

// Pill tone for an assessment status (critical/warning/nominal/other).
export const statusTone = (s) =>
  s === 'critical' ? 'red' : s === 'warning' ? 'amber' : s === 'nominal' ? 'green' : 'blue';

// Threshold limits as a compact string, e.g. "warn>85.1 · crit>89.6 · crit<58.4".
export const limitStr = (o) =>
  Object.entries(o || {})
    .map(
      ([k, v]) =>
        (k.startsWith('warning') ? 'warn' : k.startsWith('critical') ? 'crit' : k) +
        (k.endsWith('high') ? '>' : k.endsWith('low') ? '<' : '') +
        fmt(v),
    )
    .join(' · ');

// Breadcrumb label for a page key.
export const pageLabel = (t, p) =>
  t[
    {
      Overview: 'navOverview',
      Body: 'navBody',
      Thresholds: 'navThresholds',
      Labs: 'navLabs',
      Environment: 'navEnv',
    }[p]
  ];

// Translated radiation status; unknown values pass through untranslated.
export const radStatus = (t, s) =>
  s
    ? {
        NOMINAL: t.nominal,
        'Below S1': t.belowS1,
        'no data': t.noDataSentence,
        'quiet (below S1)': t.quietBelowS1,
        'S1 Minor': t.s1Minor,
        'S2 Moderate': t.s2Moderate,
        'S3 Strong': t.s3Strong,
        'S4 Severe': t.s4Severe,
        'S5 Extreme': t.s5Extreme,
      }[s] || s
    : t.noData;

// Translated NOAA S-scale label (S1 Minor .. S5 Extreme).
export const sScaleLabel = (t, k) =>
  ({
    'S1 Minor': t.s1Minor,
    'S2 Moderate': t.s2Moderate,
    'S3 Strong': t.s3Strong,
    'S4 Severe': t.s4Severe,
    'S5 Extreme': t.s5Extreme,
  })[k] || k;

// Translated lab result status.
export const labStatus = (t, s) =>
  ({
    high: t.high,
    low: t.low,
    baseline_deviation: t.baselineDeviation,
    baseline: t.baselineDeviation,
  })[s] || pretty(s);

// Translated label for a 7-day report stat key.
export const statLabel = (t, k) =>
  ({
    avg_resting_hr: t.avgHr,
    avg_sleep_hours: t.avgSleep,
    avg_stress: t.avgStress,
    min_spo2: t.minSpo2,
  })[k] || pretty(k.replace('avg_', 'Average '));

// Translated vital-sign indicator name; falls back to the raw key.
export const indName = (t, k) => t['ind_' + k] || pretty(k);

// Translated assessment status (nominal/warning/critical).
export const statusLabel = (t, s) => (s === 'nominal' ? t.nominalWord : t['level_' + s] || s);
