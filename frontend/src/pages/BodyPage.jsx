import { Activity, Clock3, HeartPulse, Sparkles, Thermometer, Wind } from 'lucide-react';
import {
  CartesianGrid,
  Line,
  LineChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from 'recharts';
import { Card, Pill, Metric } from '../components/ui';
import { indName, fmt, limitStr } from '../lib/format';
import BodyModel from '../BodyModel';

export default function BodyPage({
  t,
  data,
  latest,
  vitals,
  grid,
  tick,
  tipBg,
  tipBorder,
  theme,
  environment,
  profile,
}) {
  return (
    <>
      <div className="body-layout">
        <Card title={t.telemetryModel} sub={t.telemetrySub}>
          <BodyModel hr={latest.resting_heart_rate_bpm || 72} t={t} theme={theme} />
          <div className="system-points">
            {t.systems.map((x, i) => (
              <span key={x}>
                <i className={i === 0 ? 'active' : ''} />
                {x}
              </span>
            ))}
          </div>
        </Card>
        <div className="body-side">
          <div className="body-status">
            <span className="pulse-dot" /> {t.demoVitals} <small>{latest.date}</small>
          </div>
          <Metric
            t={t}
            label={t.restingHr}
            value={latest.resting_heart_rate_bpm || '—'}
            unit=" bpm"
            icon={HeartPulse}
          />
          <Metric
            t={t}
            label={t.bloodOxygen}
            value={fmt(latest.spo2_percent)}
            unit="%"
            icon={Activity}
          />
          <Metric
            t={t}
            label={t.bodyTemp}
            value={fmt(latest.body_temperature_c, 1)}
            unit="°C"
            icon={Thermometer}
          />
          <Metric
            t={t}
            label={t.sleepDuration}
            value={fmt(latest.sleep_hours, 1)}
            unit={t.hrsUnit}
            icon={Clock3}
          />
        </div>
      </div>
      <div className="metric-grid four">
        <Metric
          t={t}
          label={t.bloodPressure}
          value={`${latest.blood_pressure_systolic_mmhg || '—'}/${latest.blood_pressure_diastolic_mmhg || '—'}`}
          unit=" mmHg"
          icon={Activity}
        />
        <Metric
          t={t}
          label={t.stressIndex}
          value={latest.stress_score ?? '—'}
          unit="/ 100"
          icon={Wind}
        />
        <Metric
          t={t}
          label={t.dailySteps}
          value={latest.steps?.toLocaleString() || '—'}
          unit={t.stepsUnit}
          icon={Activity}
        />
        <Metric
          t={t}
          label={t.moodScore}
          value={latest.mood_score ?? '—'}
          unit="/ 10"
          icon={Sparkles}
        />
      </div>
      <Card title={t.trends30d} sub={t.trends30dSub}>
        <div className="chart tall-chart">
          <ResponsiveContainer width="100%" height="100%">
            <LineChart data={vitals}>
              <CartesianGrid strokeDasharray="3 5" stroke={grid} />
              <XAxis
                dataKey="date"
                tick={{ fill: tick, fontSize: 10 }}
                tickFormatter={(x) => x.slice(5)}
                axisLine={false}
                tickLine={false}
              />
              <YAxis tick={{ fill: tick, fontSize: 10 }} axisLine={false} tickLine={false} />
              <Tooltip
                contentStyle={{
                  background: tipBg,
                  border: '1px solid ' + tipBorder,
                  borderRadius: 10,
                }}
              />
              <Line
                dataKey="resting_heart_rate_bpm"
                name={t.heartRate}
                stroke="#55d8d0"
                dot={false}
                strokeWidth={2}
              />
              <Line
                dataKey="sleep_hours"
                name={t.sleepHours}
                stroke="#9d8bff"
                dot={false}
                strokeWidth={2}
              />
            </LineChart>
          </ResponsiveContainer>
        </div>
        <div className="tiny-note">{t.vitalsNote}</div>
      </Card>
      <Card
        title={t.thresholdsTitle}
        sub={`${t['env_' + environment]} · ${data.thresholds?.baseline_days || 0} ${t.baselineDays} · ${profile === 'personal' ? t.profilePersonal : t.profileGeneric}`}
      >
        <div className="table-wrap">
          <table>
            <thead>
              <tr>
                <th>{t.thBiomarker}</th>
                <th>{t.thBaseline}</th>
                <th>{t.thLimits}</th>
                <th>{t.thGeneric}</th>
                <th>{t.thSource}</th>
              </tr>
            </thead>
            <tbody>
              {Object.entries(data.thresholds?.indicators || {}).map(([key, x]) => (
                <tr key={key}>
                  <td>
                    <b>{indName(t, key)}</b>
                  </td>
                  <td>{x.baseline_median ?? '—'}</td>
                  <td>{limitStr(x.thresholds)}</td>
                  <td>{limitStr(x.generic)}</td>
                  <td>
                    <Pill tone={x.source === 'personal' ? 'green' : 'blue'}>
                      {t['source_' + x.source] || x.source}
                    </Pill>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </Card>
    </>
  );
}
