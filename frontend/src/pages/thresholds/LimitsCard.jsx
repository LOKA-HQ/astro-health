import { Card, Pill } from '../../components/ui';
import { fill, deviationText, summaryKind, thresholdRows } from '../../lib/context';
import { indName, statusLabel, statusTone } from '../../lib/format';

const COLUMNS = [
  'th_colIndicator',
  'th_colBaseline',
  'th_colWarn',
  'th_colCrit',
  'th_colGeneric',
  'th_colLatest',
  'th_colStatus',
];

// How the environment moved an indicator's limits, as text after its unit.
function limitAdjustment(t, row) {
  if (row.shift) {
    const sign = row.shift > 0 ? '+' : '−';
    return ` · ${fill(t.th_shifted, { value: sign + Math.abs(row.shift) })}`;
  }
  if (row.tolerance) return ` · ${fill(t.th_upperPlus, { value: row.tolerance })}`;
  return '';
}

// The limits in force for every indicator next to the latest value and its status.
export default function LimitsCard({ t, crew, thresholds, assessment, loading, error }) {
  const rows = thresholdRows(thresholds, assessment, t.th_or);
  const notes = rows.filter((r) => r.note);
  const summary = summaryKind(thresholds);

  return (
    <Card
      title={t.th_limitsTitle}
      sub={`${t.crew} ${crew}${summary ? ' · ' + fill(t[summary.key], { n: summary.n }) : ''}`}
      action={
        assessment && (
          <Pill tone={statusTone(assessment.latest_status)}>
            {loading
              ? t.th_updating
              : fill(t.th_latestDay, { status: statusLabel(t, assessment.latest_status) })}
          </Pill>
        )
      }
    >
      <div className="table-wrap">
        <table className="limits-table">
          <thead>
            <tr>
              {COLUMNS.map((key) => (
                <th key={key}>{t[key]}</th>
              ))}
            </tr>
          </thead>
          <tbody>
            {rows.map((r) => (
              <tr key={r.field}>
                <td>
                  <b>{indName(t, r.field)}</b>
                  <small>
                    {r.unit}
                    {limitAdjustment(t, r)}
                  </small>
                </td>
                <td dir="ltr">{r.baseline}</td>
                <td dir="ltr">{r.warning}</td>
                <td dir="ltr">{r.critical}</td>
                <td dir="ltr" className="muted-cell">
                  {r.genericWarning}
                </td>
                <td dir="ltr" className="result">
                  {r.value ?? '—'}
                  {r.deviation != null && <small>{deviationText(r.deviation)}</small>}
                </td>
                <td>
                  {r.status ? (
                    <Pill tone={statusTone(r.status)}>{statusLabel(t, r.status)}</Pill>
                  ) : (
                    '—'
                  )}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
        {rows.length === 0 && !loading && !error && <div className="empty">{t.th_noLimits}</div>}
      </div>
      {notes.length > 0 && (
        <div className="baseline-notes">
          {notes.map((r) => (
            <div key={r.field}>
              <b>{indName(t, r.field)}</b> {r.note}
            </div>
          ))}
        </div>
      )}
      <div className="table-note">{t.th_limitsNote}</div>
    </Card>
  );
}
