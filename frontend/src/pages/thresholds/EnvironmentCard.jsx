import { Card, Pill } from '../../components/ui';
import { indName } from '../../lib/format';
import { environmentFacts, fill, signed, withUnit } from '../../lib/context';

// What the chosen environment changes, in words, and the sources behind it.
// The description, basis and citations are written by the API (in English).
export default function EnvironmentCard({ t, env, envList, environment }) {
  const sentences = factSentences(t, environmentFacts(env));

  return (
    <Card
      title={t['env_' + environment] || env?.label || ''}
      sub={t.th_envWhat}
      action={<Pill tone="blue">{environment.replaceAll('_', ' ')}</Pill>}
    >
      <p className="env-desc">{env?.description}</p>
      {env && <p className="env-basis">{env.basis}</p>}
      {sentences.shifts.length === 0 && sentences.limits.length === 0 && (
        <div className="tiny-note">{t.th_noAdjust}</div>
      )}
      <FactList items={sentences.shifts} />
      <FactList items={sentences.limits} className="limits" />
      {env?.sources?.length > 0 && (
        <Sources t={t} keys={env.sources} references={envList?.references} />
      )}
    </Card>
  );
}

// Facts as translated sentences: shifts (and one-sided allowances) and hard limits.
function factSentences(t, { shifts, tolerances, limits }) {
  return {
    shifts: [
      ...shifts.map(({ field, value, rampDays }) =>
        rampDays
          ? fill(t.th_factRamp, {
              name: indName(t, field),
              value: withUnit(field, signed(value)),
              days: rampDays,
            })
          : fill(t.th_factShift, {
              name: indName(t, field),
              value: withUnit(field, signed(value)),
            }),
      ),
      ...tolerances.map(({ field, high }) =>
        fill(t.th_factTolerance, { name: indName(t, field), value: withUnit(field, signed(high)) }),
      ),
    ],
    limits: limits.map(({ field, side, value }) =>
      fill(side === 'high' ? t.th_factAbsHigh : t.th_factAbsLow, {
        name: indName(t, field),
        value: withUnit(field, signed(value).replace(/^\+/, '')),
      }),
    ),
  };
}

function FactList({ items, className = '' }) {
  if (items.length === 0) return null;
  return (
    <ul className={('fact-list ' + className).trim()}>
      {items.map((text) => (
        <li key={text}>{text}</li>
      ))}
    </ul>
  );
}

function Sources({ t, keys, references }) {
  return (
    <div className="sources">
      <span>{t.th_sources}</span>
      {keys.map((key) => {
        const ref = references?.[key];
        return ref ? (
          <div key={key}>
            <a href={ref.url} target="_blank" rel="noreferrer">
              {ref.citation}
            </a>
            <small>{ref.finding}</small>
          </div>
        ) : null;
      })}
    </div>
  );
}
