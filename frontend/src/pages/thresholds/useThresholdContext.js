// State behind the Thresholds page. The profile (generic / personal) and the
// environment are chosen in the page header and owned by App; this hook adds
// what only this page needs (where the baseline was recorded, days in the
// environment, "detect from telemetry") and loads the thresholds and the
// assessment for the combination.
import { useEffect, useState } from 'react';
import { get } from '../../lib/api';
import { contextQuery, detectQuery } from '../../lib/context';

const ASSESSMENT_DAYS = 7;

const initialDetect = () => ({
  body: 'earth',
  altitudeKm: '0',
  accelG: '1',
  result: null,
  failed: false,
});

/** Data and actions for `crew` under the chosen `profile` and `environment`. */
export function useThresholdContext(crew, profile, environment, onEnvironmentChange) {
  const [baselineMode, setBaselineMode] = useState('preflight');
  const [daysInEnvironment, setDaysInEnvironment] = useState('');
  const [loaded, setLoaded] = useState({});
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [envList, setEnvList] = useState(null);
  const [detect, setDetect] = useState(initialDetect);

  // The list of environments does not depend on the crew member.
  useEffect(() => {
    get('/environments')
      .then(setEnvList)
      .catch(() => {});
  }, []);

  // Reload whenever anything in the context changes. The `live` flag drops
  // answers that arrive after a newer request was started.
  useEffect(() => {
    let live = true;
    const ctx = { profile, environment, baselineMode, daysInEnvironment };
    setLoading(true);
    setError('');
    Promise.all([
      get(`/crew/${crew}/thresholds${contextQuery(ctx)}`),
      get(`/crew/${crew}/assessment${contextQuery(ctx, { days: ASSESSMENT_DAYS })}`),
    ])
      .then(([thresholds, assessment]) => {
        if (live) setLoaded({ crew, thresholds, assessment });
      })
      .catch((e) => {
        if (live) setError(e.message);
      })
      .finally(() => {
        if (live) setLoading(false);
      });
    return () => {
      live = false;
    };
  }, [crew, profile, environment, baselineMode, daysInEnvironment]);

  /** Ask the API which environment the telemetry describes, and switch to it. */
  async function runDetect(telemetry) {
    const next = { ...detect, ...telemetry };
    setDetect({ ...next, result: null, failed: false });
    try {
      const result = await get('/environments/detect' + detectQuery(next));
      setDetect({ ...next, result, failed: false });
      onEnvironmentChange(result.environment);
    } catch {
      setDetect({ ...next, result: null, failed: true });
    }
  }

  return {
    baselineMode,
    setBaselineMode,
    daysInEnvironment,
    setDaysInEnvironment,
    // Data of another crew member is not shown while the new one loads.
    data: loaded.crew === crew ? loaded : {},
    loading,
    error,
    envList,
    detect,
    setDetect,
    runDetect,
  };
}
