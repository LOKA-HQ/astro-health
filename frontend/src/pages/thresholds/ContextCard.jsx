import { Signal } from 'lucide-react';
import { Card } from '../../components/ui';
import {
  DEFAULT_ENVIRONMENT,
  DETECT_PRESETS,
  MAX_DAYS_IN_ENVIRONMENT,
  fill,
  hasRamp,
} from '../../lib/context';

const PROFILES = ['generic', 'personal'];

// Fine-tune how the limits are set: the profile and environment (the same
// values as in the page header), how long the person has been there and where
// the personal baseline was recorded. Below, pick the environment from telemetry.
export default function ContextCard({
  t,
  profile,
  environment,
  env,
  state,
  onProfileChange,
  onEnvironmentChange,
}) {
  const { envList, baselineMode, setBaselineMode, daysInEnvironment, setDaysInEnvironment } = state;
  const environments = envList?.environments?.map((e) => e.key) || [environment];
  const showBaseline = profile === 'personal' && environment !== DEFAULT_ENVIRONMENT;

  return (
    <Card title={t.th_ctxTitle} sub={t.th_ctxSub}>
      <div className="ctx-controls">
        <div className="ctx-field">
          <span>{t.th_thresholds}</span>
          <div className="seg" role="group" aria-label={t.th_thresholds}>
            {PROFILES.map((p) => (
              <button
                key={p}
                className={profile === p ? 'active' : ''}
                title={t['th_hint_' + p]}
                onClick={() => onProfileChange(p)}
              >
                {t['th_short_' + p]}
              </button>
            ))}
          </div>
          <small>{t['th_hint_' + profile]}</small>
        </div>

        <div className="ctx-field">
          <span>{t.th_location}</span>
          <select
            className="filter-select"
            aria-label={t.th_location}
            value={environment}
            onChange={(e) => onEnvironmentChange(e.target.value)}
          >
            {environments.map((key) => (
              <option key={key} value={key}>
                {t['env_' + key] || key}
              </option>
            ))}
          </select>
        </div>

        {hasRamp(env) && (
          <div className="ctx-field">
            <span>{t.th_daysIn}</span>
            <input
              className="filter-select"
              type="number"
              min="0"
              max={MAX_DAYS_IN_ENVIRONMENT}
              aria-label={t.th_daysIn}
              placeholder={t.th_unknown}
              value={daysInEnvironment}
              onChange={(e) => setDaysInEnvironment(e.target.value)}
            />
            <small>{t.th_daysHint}</small>
          </div>
        )}

        {showBaseline && (
          <div className="ctx-field">
            <span>{t.th_baselineRecorded}</span>
            <select
              className="filter-select"
              aria-label={t.th_baselineRecorded}
              value={baselineMode}
              onChange={(e) => setBaselineMode(e.target.value)}
            >
              <option value="preflight">{t.th_baseEarth}</option>
              <option value="inplace">{t.th_baseHere}</option>
            </select>
            <small>{baselineMode === 'inplace' ? t.th_baseInplaceNote : t.th_basePreNote}</small>
          </div>
        )}
      </div>

      <DetectPanel t={t} state={state} />
    </Card>
  );
}

// Pick the environment from telemetry (body, altitude, acceleration).
function DetectPanel({ t, state }) {
  const { detect, setDetect, runDetect } = state;
  const change = (field) => (e) => setDetect({ ...detect, [field]: e.target.value });

  return (
    <div className="detect">
      <div className="detect-head">
        <Signal size={14} /> <b>{t.th_detectTitle}</b>
      </div>
      <div className="detect-presets">
        {DETECT_PRESETS.map((p) => (
          <button
            key={p.key}
            onClick={() => runDetect({ body: p.body, altitudeKm: p.altitudeKm, accelG: p.accelG })}
          >
            {t['th_p_' + p.key]}
          </button>
        ))}
      </div>
      <div className="detect-form">
        <label>
          {t.th_body}
          <select className="filter-select" value={detect.body} onChange={change('body')}>
            <option value="earth">{t.th_earth}</option>
            <option value="mars">{t.th_mars}</option>
          </select>
        </label>
        <label>
          {t.th_altitude}
          <input
            className="filter-select"
            type="number"
            min="0"
            value={detect.altitudeKm}
            onChange={change('altitudeKm')}
          />
        </label>
        <label>
          {t.th_accel}
          <input
            className="filter-select"
            type="number"
            min="0"
            step="0.01"
            value={detect.accelG}
            onChange={change('accelG')}
          />
        </label>
        <button className="detect-go" onClick={() => runDetect(detect)}>
          {t.th_detect}
        </button>
      </div>
      {detect.result && (
        <div className="detect-result">
          {fill(t.th_detected, {
            env: t['env_' + detect.result.environment] || detect.result.environment,
          })}
          {detect.result.reason ? ` · ${detect.result.reason}` : ''}
        </div>
      )}
      {detect.failed && <div className="detect-result bad">{t.th_detectFailed}</div>}
    </div>
  );
}
