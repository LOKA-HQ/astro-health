import { Shield, Sparkles } from 'lucide-react';
import {
  Area,
  AreaChart,
  CartesianGrid,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
  ReferenceLine,
} from 'recharts';
import { Card, Pill } from '../components/ui';
import { radStatus, sScaleLabel, fmt, pretty } from '../lib/format';

export default function EnvironmentPage({ t, data, dailyFlux, grid, tick, tipBg, tipBorder }) {
  return (
    <>
      <div className="env-status">
        <div className="env-status-icon">
          <Shield size={22} />
        </div>
        <div>
          <b>
            {t.radEnvTitle.toUpperCase()} · {radStatus(t, data.rad?.latest_status)}
          </b>
          <small>{t.goesChannel}</small>
        </div>
        <div className="env-reading">
          {fmt(data.rad?.latest_flux_pfu, 3)} <small>pfu</small>
        </div>
      </div>
      <div className="overview-grid">
        <Card title={t.protonFlux} sub={t.protonFluxSub} action={<Pill>NOAA SWPC</Pill>}>
          <div className="chart tall-chart">
            <ResponsiveContainer width="100%" height="100%">
              <AreaChart data={dailyFlux}>
                <defs>
                  <linearGradient id="fluxFill" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="0%" stopColor="#58d7cf" stopOpacity={0.3} />
                    <stop offset="100%" stopColor="#58d7cf" stopOpacity={0} />
                  </linearGradient>
                </defs>
                <CartesianGrid strokeDasharray="3 5" stroke={grid} />
                <XAxis
                  dataKey="day"
                  tick={{ fill: tick, fontSize: 11 }}
                  axisLine={false}
                  tickLine={false}
                />
                <YAxis tick={{ fill: tick, fontSize: 11 }} axisLine={false} tickLine={false} />
                <Tooltip
                  contentStyle={{
                    background: tipBg,
                    border: '1px solid ' + tipBorder,
                    borderRadius: 10,
                  }}
                />
                <ReferenceLine
                  y={10}
                  stroke="#e9b65b"
                  strokeDasharray="4 4"
                  label={{ value: t.s1Threshold, fill: '#e9b65b', fontSize: 10 }}
                />
                <Area
                  dataKey="flux"
                  name={t.meanFlux}
                  stroke="#58d7cf"
                  fill="url(#fluxFill)"
                  strokeWidth={2}
                />
              </AreaChart>
            </ResponsiveContainer>
          </div>
          <div className="tiny-note">{t.s1Note}</div>
        </Card>
        <Card title={t.stormScaleTitle} sub={t.stormScaleSub}>
          <div className="scale-list">
            {Object.entries(data.rad?.noaa_s_scale_thresholds_pfu || {}).map(([k, v], i) => (
              <div key={k}>
                <span className={'scale-dot s' + i} />
                <span>{sScaleLabel(t, k)}</span>
                <b>{v.toLocaleString()} pfu</b>
              </div>
            ))}
          </div>
          <div className="scale-current">
            <span>{t.currentLevel}</span>
            <b>{radStatus(t, data.rad?.latest_status)}</b>
          </div>
        </Card>
      </div>
      <Card
        title={t.donkiTitle}
        sub={`NASA DONKI · ${data.weather?.recent_30d?.window || t.recent30d}`}
        action={<Pill tone="blue">NASA DONKI</Pill>}
      >
        <div className="event-counts">
          <div>
            <b>{data.weather?.recent_30d?.sep_events ?? '—'}</b>
            <small>{t.sepEvents}</small>
          </div>
          <div>
            <b>{data.weather?.recent_30d?.cme_events ?? '—'}</b>
            <small>{t.cmeEvents}</small>
          </div>
          <div>
            <b>{data.weather?.recent_30d?.gst_events ?? '—'}</b>
            <small>{t.gstEvents}</small>
          </div>
          <div>
            <b>{data.weather?.recent_30d?.strongest_gst?.maxKp ?? '—'}</b>
            <small>{t.strongestKp}</small>
          </div>
        </div>
        <div className="event-list">
          {(data.weather?.recent_30d?.cmes || [])
            .slice(-5)
            .reverse()
            .map((e, i) => (
              <div key={i}>
                <span className="event-icon">
                  <Sparkles size={15} />
                </span>
                <div>
                  <b>{t.cme}</b>
                  <small>
                    {e.startTime} · {e.sourceLocation || t.srcUnavailable}
                  </small>
                </div>
                <strong>{e.speed_kms ? `${e.speed_kms} km/s` : t.speedNa}</strong>
              </div>
            ))}
        </div>
      </Card>
      <Card title={t.doseRates} sub={t.doseRatesSub}>
        <div className="dose-grid">
          {Object.entries(data.rad?.reference_dose_rates_published || {})
            .filter(([k]) => k !== 'note')
            .map(([k, v]) => (
              <div key={k}>
                <small>{pretty(k)}</small>
                <b>{v}</b>
              </div>
            ))}
        </div>
        <div className="tiny-note">{data.rad?.reference_dose_rates_published?.note}</div>
      </Card>
    </>
  );
}
