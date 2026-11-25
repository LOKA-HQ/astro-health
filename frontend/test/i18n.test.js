// The two languages must carry the same strings, and every string the
// Thresholds page asks for must exist (a missing key would show as blank).
import { test } from 'node:test';
import assert from 'node:assert/strict';
import { readFileSync, readdirSync } from 'node:fs';
import { dirname, join, resolve } from 'node:path';
import { fileURLToPath } from 'node:url';

import { STRINGS } from '../src/i18n.js';
import { DETECT_PRESETS } from '../src/lib/context.js';
import { fill } from '../src/lib/context.js';

const src = resolve(dirname(fileURLToPath(import.meta.url)), '../src');

test('English and Arabic have exactly the same keys', () => {
  const en = Object.keys(STRINGS.en).sort();
  const ar = Object.keys(STRINGS.ar).sort();
  assert.deepEqual(
    en.filter((k) => !ar.includes(k)),
    [],
    'missing in Arabic',
  );
  assert.deepEqual(
    ar.filter((k) => !en.includes(k)),
    [],
    'missing in English',
  );
});

test('no string is empty', () => {
  for (const lang of ['en', 'ar']) {
    for (const [key, value] of Object.entries(STRINGS[lang])) {
      if (typeof value === 'string') assert.notEqual(value.trim(), '', `${lang}.${key} is empty`);
    }
  }
});

test('placeholders match between the languages', () => {
  const names = (s) => [...String(s).matchAll(/\{(\w+)\}/g)].map((m) => m[1]).sort();
  for (const key of Object.keys(STRINGS.en)) {
    if (typeof STRINGS.en[key] !== 'string') continue;
    assert.deepEqual(names(STRINGS.ar[key]), names(STRINGS.en[key]), `placeholders of ${key}`);
  }
});

function pageSources() {
  const dir = join(src, 'pages', 'thresholds');
  return [
    join(src, 'pages', 'ThresholdsPage.jsx'),
    ...readdirSync(dir)
      .filter((f) => f.endsWith('.jsx'))
      .map((f) => join(dir, f)),
  ].map((f) => readFileSync(f, 'utf8'));
}

test('every literal string key the Thresholds page uses exists in both languages', () => {
  const keys = new Set();
  for (const text of pageSources()) {
    for (const [, key] of text.matchAll(
      /\bt\.(th_\w+|navThresholds|title_Thresholds|sub_Thresholds)/g,
    ))
      keys.add(key);
    for (const [, key] of text.matchAll(/\bt\[\s*'(th_\w+)'\s*\]/g)) keys.add(key);
  }
  assert.ok(keys.size > 30, 'expected the page to use many strings');
  for (const key of keys) {
    for (const lang of ['en', 'ar']) assert.ok(STRINGS[lang][key], `${lang} lacks ${key}`);
  }
});

test('computed keys resolve: detect presets, hints, chart lines, summaries', () => {
  const keys = [
    ...DETECT_PRESETS.map((p) => 'th_p_' + p.key),
    'th_hint_generic',
    'th_hint_personal',
    'th_sumPersonal',
    'th_sumFewDays',
    'th_sumGeneric',
    ...['critical', 'warning', 'generic'].flatMap((tone) =>
      ['high', 'low'].map((side) => `th_line_${tone}_${side}`),
    ),
  ];
  for (const key of keys) {
    for (const lang of ['en', 'ar']) assert.ok(STRINGS[lang][key], `${lang} lacks ${key}`);
  }
});

test('sentences fill in without leftover placeholders', () => {
  for (const lang of ['en', 'ar']) {
    const t = STRINGS[lang];
    const out = fill(t.th_factRamp, { name: 'X', value: '+1 °C', days: 75 });
    assert.ok(!out.includes('{'), `${lang}: ${out}`);
    assert.match(fill(t.th_sumPersonal, { n: 23 }), /23/);
  }
});

test('the Thresholds page is in the navigation and the breadcrumb', async () => {
  const { pageLabel } = await import('../src/lib/format.js');
  assert.equal(pageLabel(STRINGS.en, 'Thresholds'), STRINGS.en.navThresholds);
  assert.equal(pageLabel(STRINGS.ar, 'Thresholds'), STRINGS.ar.navThresholds);
  assert.match(readFileSync(join(src, 'components', 'Sidebar.jsx'), 'utf8'), /'Thresholds'/);
  assert.match(readFileSync(join(src, 'App.jsx'), 'utf8'), /page === 'Thresholds'/);
});
