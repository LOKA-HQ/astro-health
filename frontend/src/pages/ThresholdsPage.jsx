import { ShieldAlert } from 'lucide-react';
import { findEnvironment } from '../lib/context';
import ContextCard from './thresholds/ContextCard';
import EnvironmentCard from './thresholds/EnvironmentCard';
import LimitsCard from './thresholds/LimitsCard';
import VitalsChartCard from './thresholds/VitalsChartCard';
import { useThresholdContext } from './thresholds/useThresholdContext';
import './thresholds/thresholds.css';

// The "Thresholds" page: whose limits apply and where the crew member is.
// The profile and environment come from the page header (owned by App); the
// forecast and the 7-day assessment are on the Overview page.
export default function ThresholdsPage({
  t,
  crew,
  vitals,
  profile,
  environment,
  onProfileChange,
  onEnvironmentChange,
  grid,
  tick,
  tipBg,
  tipBorder,
}) {
  const state = useThresholdContext(crew, profile, environment, onEnvironmentChange);
  const { thresholds, assessment } = state.data;
  const env = findEnvironment(state.envList, environment);

  return (
    <>
      <div className="ctx-grid">
        <ContextCard
          t={t}
          profile={profile}
          environment={environment}
          env={env}
          state={state}
          onProfileChange={onProfileChange}
          onEnvironmentChange={onEnvironmentChange}
        />
        <EnvironmentCard t={t} env={env} envList={state.envList} environment={environment} />
      </div>

      {state.error && (
        <div className="error">
          <ShieldAlert size={16} />
          <span>
            {t.th_loadError} {state.error}
          </span>
        </div>
      )}

      <LimitsCard
        t={t}
        crew={crew}
        thresholds={thresholds}
        assessment={assessment}
        loading={state.loading}
        error={state.error}
      />

      <VitalsChartCard
        t={t}
        vitals={vitals}
        thresholds={thresholds}
        grid={grid}
        tick={tick}
        tipBg={tipBg}
        tipBorder={tipBorder}
      />
    </>
  );
}
