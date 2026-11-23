import {
  Activity,
  AlertTriangle,
  Atom,
  ChevronRight,
  HeartPulse,
  Shield,
  ShieldAlert,
  Users,
} from 'lucide-react';
import {
  CartesianGrid,
  Line,
  LineChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from 'recharts';
import { Card, Pill, Metric, Spark } from '../components/ui';
import {
  radStatus,
  indName,
  statusLabel,
  fmt,
  pretty,
  levelColor,
  riskTone,
  statusTone,
} from '../lib/format';

export default function OverviewPage({
  t,
  data,
  latest,
  trend,
  alerts,
  critical,
  dailyFlux,
  assessLatest,
  assessOff,
  grid,
  tick,
  tipBg,
  tipBorder,
  tipColor,
  onSelectAlert,
  onGoLabs,
}) {
  return (
    <>
      <div className="status-banner">
        <div className="status-symbol">
          <Shield size={20} />
        </div>
        <div>
          <b>
            {t.crewStatus} ·{' '}
            {data.report?.overall_status === 'attention' ? t.attentionRequired : t.nominal}
          </b>
          <small>
            {t.bioSync} · {t.lastDataPoint} {latest.date || '—'}
          </small>
        </div>
        <div className="banner-right">
          <span className="pulse-dot" /> {t.allSystems}{' '}
          {data.report?.overall_status === 'attention' ? t.monitoring : t.nominal}
        </div>
      </div>
      <div className="metric-grid">
        <Metric
          t={t}
          label={t.crewMembers}
          value="04"
          unit="/ 04"
          icon={Users}
          foot={t.allMonitored}
        />
        <Metric
          t={t}
          label={t.criticalAlerts}
          value={critical}
          unit={t.activeUnit}
          icon={ShieldAlert}
          tone="red"
          delta={`${alerts.length} ${t.totalAlerts}`}
        />
        <Metric
          t={t}
          label={t.restingHr}
          value={latest.resting_heart_rate_bpm || '—'}
          unit=" bpm"
          icon={HeartPulse}
          delta={t.latestSynthetic}
        />
        <Metric
          t={t}
          label={t.o2sat}
          value={fmt(latest.spo2_percent, 1)}
          unit="%"
          icon={Activity}
          delta={t.peripheralO2}
        />
      </div>
      <div className="overview-grid">
        <Card title={t.trendsTitle} sub={t.trendsSub} action={<Pill>{t.window7d}</Pill>}>
          <div className="trend-legend">
            <span>
              <i className="dot cyan" /> {t.heartRate}
            </span>
            <span>
              <i className="dot violet" /> SpO₂
            </span>
          </div>
          <div className="chart large-chart">
            <ResponsiveContainer width="100%" height="100%">
              <LineChart data={trend}>
                <CartesianGrid strokeDasharray="3 5" stroke={grid} />
                <XAxis
                  dataKey="day"
                  tick={{ fill: tick, fontSize: 11 }}
                  axisLine={false}
                  tickLine={false}
                />
                <YAxis
                  yAxisId="left"
                  tick={{ fill: tick, fontSize: 11 }}
                  axisLine={false}
                  tickLine={false}
                />
                <YAxis
                  yAxisId="right"
                  orientation="right"
                  domain={[90, 100]}
                  tick={{ fill: tick, fontSize: 11 }}
                  axisLine={false}
                  tickLine={false}
                />
                <Tooltip
                  contentStyle={{
                    background: tipBg,
                    border: '1px solid ' + tipBorder,
                    borderRadius: 10,
                    color: tipColor,
                  }}
                />
                <Line
                  yAxisId="left"
                  type="monotone"
                  dataKey="hr"
                  name={t.hrBpm}
                  stroke="#55d8d0"
                  strokeWidth={2.5}
                  dot={false}
                />
                <Line
                  yAxisId="right"
                  type="monotone"
                  dataKey="spo2"
                  name={t.spo2Pct}
                  stroke="#9d8bff"
                  strokeWidth={2.5}
                  dot={false}
                />
              </LineChart>
            </ResponsiveContainer>
          </div>
          <div className="chart-foot">
            <span>
              {t.prev7d} <b>—</b>
            </span>
            <span>
              {t.recent7d} <b>{trend.length ? trend.at(-1).day : '—'}</b>
            </span>
            <small>{t.illustrativeNote}</small>
          </div>
        </Card>
        <Card title={t.radEnvTitle} sub={t.radEnvSub}>
          <div className="radiation-read">
            <div>
              <div className="big-reading">
                {fmt(data.rad?.latest_flux_pfu, 3)} <small>pfu</small>
              </div>
              <Pill tone="green">{radStatus(t, data.rad?.latest_status)}</Pill>
            </div>
            <div className="radiation-icon">
              <Atom size={27} />
            </div>
          </div>
          <Spark data={dailyFlux.map((x) => ({ v: x.flux }))} />
          <div className="radiation-meta">
            <span>
              {t.peak7d} <b>{fmt(data.rad?.peak_7d_flux_pfu, 3)} pfu</b>
            </span>
            <span>
              {t.stormScale} <b>{t.belowS1}</b>
            </span>
          </div>
          <div className="tiny-note">{t.radNote}</div>
        </Card>
      </div>
      <div className="bottom-grid">
        <Card
          title={t.priorityAlerts}
          sub={`${alerts.length} ${t.activeSignals}`}
          action={
            <button className="text-btn" onClick={() => onGoLabs()}>
              {t.viewAnalysis} <ChevronRight size={14} />
            </button>
          }
        >
          <div className="alert-list">
            {alerts.slice(0, 4).map((a, i) => (
              <button className="alert-row" key={i} onClick={() => onSelectAlert(a)}>
                <span className={'alert-symbol ' + levelColor(a.level)}>
                  {a.level === 'critical' ? (
                    <AlertTriangle size={15} />
                  ) : a.type === 'radiation' ? (
                    <Atom size={15} />
                  ) : (
                    <Activity size={15} />
                  )}
                </span>
                <span className="alert-copy">
                  <b>{a.indicator ? pretty(a.indicator) : pretty(a.type) + ' ' + t.alertWord}</b>
                  <small>
                    {a.crew_id || 'GLOBAL'} · {a.timepoint || a.date || t.snapshot}
                  </small>
                </span>
                <Pill tone={levelColor(a.level)}>{t['level_' + a.level] || a.level}</Pill>
                <ChevronRight size={15} className="muted" />
              </button>
            ))}
          </div>
        </Card>
        <Card title={t.readiness} sub={t.readinessSub}>
          <div className="readiness-list">
            {(data.roster || []).map((c, i) => (
              <div className="readiness-row" key={c.crew_id}>
                <div className="mini-avatar">{String(i + 1).padStart(2, '0')}</div>
                <div className="readiness-name">
                  <b>{c.crew_id}</b>
                  <small>
                    {c.lab_records.toLocaleString()} {t.labRecords}
                  </small>
                </div>
                <div className="readiness-stat">
                  <b>{c.flagged}</b>
                  <small>{t.flagged}</small>
                </div>
                <Pill tone={c.clinical_out_of_range ? 'amber' : 'green'}>
                  {c.clinical_out_of_range ? t.review : t.nominalWord}
                </Pill>
              </div>
            ))}
          </div>
        </Card>
      </div>
      <div className="bottom-grid">
        <Card
          title={t.forecastTitle}
          sub={t.forecastSub}
          action={
            <Pill tone={riskTone(data.forecast?.overall_risk)}>
              {t['risk_' + (data.forecast?.overall_risk || 'low')] || data.forecast?.overall_risk}
            </Pill>
          }
        >
          <div className="readiness-list">
            {(data.forecast?.indicators || []).map((f) => (
              <div className="readiness-row" key={f.indicator}>
                <div className="readiness-name">
                  <b>{indName(t, f.indicator)}</b>
                  <small>
                    {t.current} {fmt(f.current_fit)} → {t.projected} {fmt(f.projected)} ·{' '}
                    {f.slope_per_day > 0 ? '+' : ''}
                    {fmt(f.slope_per_day, 2)}
                    {t.slopeDay}
                  </small>
                </div>
                <div className="readiness-stat">
                  <b>
                    {f.days_to_breach == null
                      ? t.noBreach
                      : f.days_to_breach + ' ' + t.daysToBreach}
                  </b>
                </div>
                <Pill tone={riskTone(f.risk)}>{t['risk_' + f.risk] || f.risk}</Pill>
              </div>
            ))}
          </div>
        </Card>
        <Card
          title={t.assessmentTitle}
          sub={t.assessmentSub}
          action={
            <Pill tone={statusTone(assessLatest?.status)}>
              {assessLatest ? statusLabel(t, assessLatest.status) : '—'}
            </Pill>
          }
        >
          <div className="day-dots">
            {(data.assessment?.days || []).map((d) => (
              <span key={d.date} className={'day-dot ' + d.status} title={d.date}>
                {d.date.slice(5)}
              </span>
            ))}
          </div>
          <div className="readiness-list">
            {assessOff.map((i) => (
              <div className="readiness-row" key={i.indicator}>
                <div className="readiness-name">
                  <b>{indName(t, i.indicator)}</b>
                  <small>
                    {i.value}
                    {i.limit != null
                      ? ` · ${i.side === 'high' ? '>' : i.side === 'low' ? '<' : ''}${fmt(i.limit)}`
                      : ''}
                    {i.deviation_sigma != null ? ` · σ ${fmt(i.deviation_sigma, 2)}` : ''}
                  </small>
                </div>
                <Pill tone={statusTone(i.status)}>{statusLabel(t, i.status)}</Pill>
              </div>
            ))}
          </div>
          {assessOff.length === 0 && <div className="empty">{t.allNominal}</div>}
        </Card>
      </div>
    </>
  );
}
