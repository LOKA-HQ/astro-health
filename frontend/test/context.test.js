import { test } from 'node:test';
import assert from 'node:assert/strict';

import {
  DEFAULT_ENVIRONMENT,
  DETECT_PRESETS,
  INDICATOR_UNITS,
  baselineEnvironmentFor,
  baselineText,
  chartLimits,
  contextQuery,
  detectQuery,
  deviationText,
  environmentFacts,
  fill,
  findEnvironment,
  hasRamp,
  latestIndicator,
  limitsText,
  parseDays,
  signed,
  summaryKind,
  thresholdRows,
  withUnit,
} from '../src/lib/context.js';

const ctx = (over = {}) => ({
  profile: 'generic',
  environment: DEFAULT_ENVIRONMENT,
  baselineMode: 'preflight',
  daysInEnvironment: '',
  ...over,
});

test('parseDays: blank and junk mean "unknown"', () => {
  for (const v of ['', null, undefined, 'abc', NaN, Infinity]) assert.equal(parseDays(v), null);
});

test('parseDays: whole days within the API bounds', () => {
  assert.equal(parseDays('12'), 12);
  assert.equal(parseDays('12.9'), 12);
  assert.equal(parseDays('0'), 0);
  assert.equal(parseDays('-5'), 0);
  assert.equal(parseDays('99999'), 3650);
});

test('baselineEnvironmentFor: Earth before the flight, or the environment itself', () => {
  assert.equal(baselineEnvironmentFor('iss', 'preflight'), 'earth_ground');
  assert.equal(baselineEnvironmentFor('iss', 'inplace'), 'iss');
});

test('contextQuery sends the profile and both environments', () => {
  const q = new URLSearchParams(contextQuery(ctx({ profile: 'personal', environment: 'iss' })));
  assert.equal(contextQuery(ctx()).startsWith('?'), true);
  assert.equal(q.get('profile'), 'personal');
  assert.equal(q.get('environment'), 'iss');
  assert.equal(q.get('baseline_environment'), 'earth_ground');
  assert.equal(q.has('days_in_environment'), false);
});

test('contextQuery: an in-place baseline is recorded in the environment', () => {
  const q = new URLSearchParams(
    contextQuery(ctx({ environment: 'mars_transit', baselineMode: 'inplace' })),
  );
  assert.equal(q.get('baseline_environment'), 'mars_transit');
});

test('contextQuery sends days_in_environment, including 0', () => {
  const days = (v) => new URLSearchParams(contextQuery(ctx({ daysInEnvironment: v })));
  assert.equal(days('30').get('days_in_environment'), '30');
  assert.equal(days('0').get('days_in_environment'), '0');
  assert.equal(days('-3').get('days_in_environment'), '0');
  assert.equal(days('junk').has('days_in_environment'), false);
});

test('contextQuery adds endpoint parameters', () => {
  assert.equal(new URLSearchParams(contextQuery(ctx(), { days: 7 })).get('days'), '7');
});

test('detectQuery builds the telemetry query and rejects negatives', () => {
  const q = new URLSearchParams(detectQuery({ body: 'mars', altitudeKm: '-5', accelG: '0.38' }));
  assert.equal(q.get('body'), 'mars');
  assert.equal(q.get('altitude_km'), '0');
  assert.equal(q.get('accel_g'), '0.38');
  const d = new URLSearchParams(detectQuery({}));
  assert.deepEqual([d.get('body'), d.get('altitude_km'), d.get('accel_g')], ['earth', '0', '1']);
});

test('findEnvironment looks an environment up by key', () => {
  const list = { environments: [{ key: 'iss', label: 'ISS' }, { key: 'launch' }] };
  assert.equal(findEnvironment(list, 'iss').label, 'ISS');
  assert.equal(findEnvironment(list, 'nope'), null);
  assert.equal(findEnvironment(null, 'iss'), null);
});

test('hasRamp is true only for environments with a gradual shift', () => {
  const ramp = { shifts: { body_temperature_c: { value: 1, ramp_days: 75 } } };
  assert.equal(hasRamp(ramp), true);
  assert.equal(hasRamp({ shifts: { spo2_percent: -2 } }), false);
  assert.equal(hasRamp({ shifts: { x: { value: 1 } } }), false); // an object without ramp_days
  assert.equal(hasRamp({}), false);
  assert.equal(hasRamp(null), false);
});

test('limitsText', () => {
  assert.equal(limitsText(55, 90), '< 55 or > 90');
  assert.equal(limitsText(null, 90), '> 90');
  assert.equal(limitsText(94, undefined), '< 94');
  assert.equal(limitsText(null, null), '—');
  assert.equal(limitsText(55.456, 90.1), '< 55.46 or > 90.1');
  assert.equal(limitsText(55, 90, 'أو'), '< 55 أو > 90');
});

test('baselineText shows median and spread only for personal limits', () => {
  assert.equal(baselineText({ baseline_median: 71, sigma: 7.436 }), '71 ± 7.44');
  assert.equal(baselineText({ baseline_median: null, sigma: null }), '—');
  assert.equal(baselineText(undefined), '—');
});

test('deviationText is signed and one decimal', () => {
  assert.equal(deviationText(1.24), '+1.2 σ');
  assert.equal(deviationText(-0.4), '-0.4 σ');
  assert.equal(deviationText(0), '0.0 σ');
  assert.equal(deviationText(null), '—');
});

test('signed uses a real minus sign and drops trailing zeros', () => {
  assert.equal(signed(1), '+1');
  assert.equal(signed(-0.5), '−0.5');
  assert.equal(signed(0), '0');
  assert.equal(signed(1.2345), '+1.23');
});

test('withUnit appends the indicator unit when there is one', () => {
  assert.equal(withUnit('resting_heart_rate_bpm', '+30'), '+30 bpm');
  assert.equal(withUnit('stress_score', '+3'), '+3');
  assert.equal(withUnit('unknown_field', '+3'), '+3');
  assert.equal(INDICATOR_UNITS.body_temperature_c, '°C');
});

const assessment = {
  days: [
    { date: 'd1', indicators: [{ indicator: 'spo2_percent', status: 'warning', value: 93 }] },
    {
      date: 'd2',
      indicators: [
        { indicator: 'spo2_percent', status: 'nominal', value: 97, deviation_sigma: -0.4 },
        { indicator: 'resting_heart_rate_bpm', status: 'critical', value: 130 },
      ],
    },
  ],
};

test('latestIndicator reads the most recent day only', () => {
  assert.equal(latestIndicator(assessment, 'spo2_percent').value, 97);
  assert.equal(latestIndicator(assessment, 'sleep_hours'), null);
  assert.equal(latestIndicator(null, 'spo2_percent'), null);
});

const thresholds = {
  profile: 'personal',
  baseline_days: 23,
  indicators: {
    spo2_percent: {
      source: 'personal',
      baseline_median: 98.3,
      sigma: 0.5,
      environment_shift: -2,
      thresholds: { warning_low: 96.5, critical_low: 95.1 },
      generic: { warning_low: 94, critical_low: 90 },
      baseline_note: 'Baseline is above the normal range.',
    },
    resting_heart_rate_bpm: {
      source: 'generic',
      environment_tolerance_high: 30,
      thresholds: { warning_low: 50, warning_high: 100, critical_low: 40, critical_high: 130 },
      generic: { warning_low: 50, warning_high: 100 },
    },
  },
};

test('thresholdRows combines limits in force with the latest judgement', () => {
  const [spo2, hr] = thresholdRows(thresholds, assessment);
  assert.equal(spo2.field, 'spo2_percent');
  assert.equal(spo2.unit, '%');
  assert.equal(spo2.personal, true);
  assert.equal(spo2.baseline, '98.3 ± 0.5');
  assert.equal(spo2.warning, '< 96.5');
  assert.equal(spo2.critical, '< 95.1');
  assert.equal(spo2.genericWarning, '< 94');
  assert.equal(spo2.shift, -2);
  assert.equal(spo2.value, 97);
  assert.equal(spo2.status, 'nominal');
  assert.equal(spo2.deviation, -0.4);
  assert.equal(spo2.note, 'Baseline is above the normal range.');
  assert.equal(hr.tolerance, 30);
  assert.equal(hr.status, 'critical');
  assert.equal(hr.deviation, null);
  assert.equal(hr.baseline, '—');
  assert.equal(thresholdRows(thresholds, assessment, 'أو')[1].warning, '< 50 أو > 100');
});

test('thresholdRows still works before the assessment has loaded', () => {
  const rows = thresholdRows(thresholds, undefined);
  assert.equal(rows.length, 2);
  assert.equal(rows[0].value, null);
  assert.equal(rows[0].status, null);
  assert.deepEqual(thresholdRows(undefined, undefined), []);
});

test('summaryKind says which sentence describes the limits in force', () => {
  assert.deepEqual(summaryKind(thresholds), { key: 'th_sumPersonal', n: 23 });
  assert.equal(summaryKind({ profile: 'personal', baseline_days: 0 }).key, 'th_sumFewDays');
  assert.equal(summaryKind({ profile: 'generic' }).key, 'th_sumGeneric');
  assert.equal(summaryKind(undefined), null);
});

test('chartLimits draws the limits in force and the differing generic ones', () => {
  const lines = chartLimits(thresholds.indicators.spo2_percent);
  assert.deepEqual(lines, [
    { y: 95.1, tone: 'critical', side: 'low' },
    { y: 96.5, tone: 'warning', side: 'low' },
    { y: 94, tone: 'generic', side: 'low' },
  ]);
});

test('chartLimits omits generic lines that equal the limits in force', () => {
  const lines = chartLimits(thresholds.indicators.resting_heart_rate_bpm);
  assert.equal(
    lines.some((l) => l.tone === 'generic'),
    false,
  );
  assert.equal(lines.length, 4);
  assert.deepEqual(chartLimits(null), []);
});

test('every detect preset has a key and numeric telemetry', () => {
  assert.ok(DETECT_PRESETS.length >= 5);
  for (const p of DETECT_PRESETS) {
    assert.match(p.key, /^[a-zA-Z]+$/);
    assert.ok(['earth', 'mars'].includes(p.body));
    assert.equal(typeof p.altitudeKm, 'number');
    assert.equal(typeof p.accelG, 'number');
  }
});

test('environmentFacts describes shifts, ramps, allowances and hard limits as data', () => {
  const facts = environmentFacts({
    shifts: { body_temperature_c: { value: 1, ramp_days: 75 }, spo2_percent: -2 },
    tolerances: { resting_heart_rate_bpm: { high: 30 } },
    absolute_overrides: { resting_heart_rate_bpm: { high: 160 }, spo2_percent: { low: 88 } },
  });
  assert.deepEqual(facts.shifts, [
    { field: 'body_temperature_c', value: 1, rampDays: 75 },
    { field: 'spo2_percent', value: -2, rampDays: null },
  ]);
  assert.deepEqual(facts.tolerances, [{ field: 'resting_heart_rate_bpm', high: 30 }]);
  assert.deepEqual(facts.limits, [
    { field: 'resting_heart_rate_bpm', side: 'high', value: 160 },
    { field: 'spo2_percent', side: 'low', value: 88 },
  ]);
  assert.deepEqual(environmentFacts(null), { shifts: [], tolerances: [], limits: [] });
});

test('fill puts values into {placeholders} and leaves unknown ones as written', () => {
  assert.equal(
    fill('{name}: {value} over {days} days', { name: 'HR', value: '+3', days: 75 }),
    'HR: +3 over 75 days',
  );
  assert.equal(fill('keep {unknown}', {}), 'keep {unknown}');
  assert.equal(fill('a {n} b {n}', { n: 0 }), 'a 0 b 0');
  assert.equal(fill(undefined), '');
});
