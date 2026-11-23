import { Activity, AlertTriangle, Download, Microscope } from 'lucide-react';
import { Card, Pill, Metric } from '../components/ui';
import { labStatus, statLabel, fmt, pretty } from '../lib/format';

// One page of the labs table.
const LAB_PAGE_SIZE = 50;

export default function LabsPage({
  t,
  data,
  crew,
  labFilter,
  labPage,
  onLabFilterChange,
  onLabPageChange,
  onExportReport,
}) {
  const filteredLabs = (data.labs || []).filter((x) =>
    labFilter === 'all'
      ? x.status !== 'normal'
      : labFilter === 'baseline'
        ? x.status.includes('baseline')
        : x.status === labFilter,
  );
  const labPageCount = Math.max(1, Math.ceil(filteredLabs.length / LAB_PAGE_SIZE));
  const visibleLabs = filteredLabs.slice(labPage * LAB_PAGE_SIZE, (labPage + 1) * LAB_PAGE_SIZE);
  return (
    <>
      <div className="lab-summary">
        <Metric
          t={t}
          label={t.totalLabs}
          value={(data.summary?.lab_records || 0).toLocaleString()}
          icon={Microscope}
        />
        <Metric
          t={t}
          label={t.flaggedResults}
          value={data.summary?.flagged_total || 0}
          icon={AlertTriangle}
          tone="amber"
        />
        <Metric
          t={t}
          label={t.clinicalOOR}
          value={data.summary?.clinical_out_of_range || 0}
          icon={Activity}
          tone="red"
        />
        <div className="report-tile">
          <div>
            <b>{t.weeklyReport}</b>
            <small>{data.report?.period || t.latest7d}</small>
          </div>
          <button onClick={onExportReport}>
            <Download size={15} /> {t.export}
          </button>
        </div>
      </div>
      <Card
        title={t.labsTitle}
        sub={t.labsSub}
        action={
          <select
            className="filter-select"
            value={labFilter}
            onChange={(e) => {
              onLabFilterChange(e.target.value);
            }}
          >
            <option value="all">{t.allFlagged}</option>
            <option value="high">{t.high}</option>
            <option value="low">{t.low}</option>
            <option value="baseline">{t.baselineDeviation}</option>
          </select>
        }
      >
        <div className="table-wrap">
          <table>
            <thead>
              <tr>
                <th>{t.thBiomarker}</th>
                <th>{t.thPanel}</th>
                <th>{t.thTimepoint}</th>
                <th>{t.thResult}</th>
                <th>{t.thRefRange}</th>
                <th>{t.thStatus}</th>
              </tr>
            </thead>
            <tbody>
              {visibleLabs.map((x, i) => (
                <tr key={`${x.study}-${x.crew}-${x.indicator}-${x.timepoint}-${i}`}>
                  <td>
                    <b>{pretty(x.indicator)}</b>
                    <small>
                      {x.study} · {x.phase}
                    </small>
                  </td>
                  <td>{pretty(x.panel)}</td>
                  <td>{x.timepoint}</td>
                  <td className="result">
                    {x.value} <small>{x.unit.replaceAll('_', ' ')}</small>
                  </td>
                  <td>
                    {x.ref_min ?? '—'} – {x.ref_max ?? '—'}
                  </td>
                  <td>
                    <Pill
                      tone={x.status === 'high' ? 'red' : x.status === 'low' ? 'amber' : 'blue'}
                    >
                      {labStatus(t, x.status)}
                    </Pill>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
          {filteredLabs.length === 0 && <div className="empty">{t.noMatching}</div>}
        </div>
        <div className="lab-pagination">
          <button
            disabled={labPage === 0}
            onClick={() => onLabPageChange((p) => Math.max(0, p - 1))}
          >
            {t.prev}
          </button>
          <span>
            {t.page} {labPage + 1} {t.of} {labPageCount}
          </span>
          <button
            disabled={labPage + 1 >= labPageCount}
            onClick={() => onLabPageChange((p) => Math.min(labPageCount - 1, p + 1))}
          >
            {t.next}
          </button>
        </div>
        <div className="table-note">
          {t.showing} {filteredLabs.length === 0 ? 0 : labPage * LAB_PAGE_SIZE + 1}–
          {Math.min((labPage + 1) * LAB_PAGE_SIZE, filteredLabs.length)} {t.of}{' '}
          {filteredLabs.length.toLocaleString()} {t.matchingRecords}. {t.refNote}
        </div>
      </Card>
      <div className="report-grid">
        <Card title={t.summary7d} sub={`${t.crew} ${crew} · ${data.report?.period}`}>
          <div className="report-stats">
            {Object.entries(data.report?.vitals_7d || {}).map(([k, v]) => (
              <div key={k}>
                <small>{statLabel(t, k)}</small>
                <b>
                  {typeof v === 'number' ? fmt(v) : v}
                  {k.includes('hr')
                    ? ' bpm'
                    : k.includes('sleep')
                      ? ' h'
                      : k.includes('spo2')
                        ? '%'
                        : ''}
                </b>
              </div>
            ))}
          </div>
        </Card>
        <Card title={t.mostFlagged} sub={t.acrossCrew}>
          <div className="flag-bars">
            {(data.summary?.top_flagged_indicators || []).slice(0, 6).map((x) => (
              <div key={x.indicator}>
                <span>{pretty(x.indicator)}</span>
                <div>
                  <i style={{ width: `${Math.min(100, x.count * 12)}%` }} />
                </div>
                <b>{x.count}</b>
              </div>
            ))}
          </div>
        </Card>
      </div>
    </>
  );
}
