import React, { useEffect, useMemo, useState } from 'react';
import { AlertTriangle } from 'lucide-react';
import { STRINGS } from './i18n';
import { API, get } from './lib/api';
import Sidebar from './components/Sidebar';
import Topbar from './components/Topbar';
import PageHeader from './components/PageHeader';
import AlertModal from './components/AlertModal';
import OverviewPage from './pages/OverviewPage';
import BodyPage from './pages/BodyPage';
import ThresholdsPage from './pages/ThresholdsPage';
import LabsPage from './pages/LabsPage';
import EnvironmentPage from './pages/EnvironmentPage';

// App shell: owns the dashboard state, loads all data from the backend and
// hands it to the page components. Shared UI lives in components/, one
// component per page lives in pages/, and pure helpers live in lib/.
function App() {
  const [page, setPage] = useState('Overview');
  const [crew, setCrew] = useState('C001');
  const [data, setData] = useState({});
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [error, setError] = useState('');
  const [mobile, setMobile] = useState(false);
  const [labFilter, setLabFilter] = useState('all');
  const [labPage, setLabPage] = useState(0);
  const [selectedAlert, setSelectedAlert] = useState(null);
  const [lang, setLang] = useState(() => localStorage.getItem('astro-lang') || 'en');
  const [theme, setTheme] = useState(() => localStorage.getItem('astro-theme') || 'dark');
  const [profile, setProfile] = useState(() => localStorage.getItem('astro-profile') || 'generic');
  const [environment, setEnvironment] = useState(
    () => localStorage.getItem('astro-env') || 'earth_ground',
  );
  const t = STRINGS[lang];

  // Language: html lang/dir attributes + persistence.
  useEffect(() => {
    document.documentElement.lang = lang;
    document.documentElement.dir = lang === 'ar' ? 'rtl' : 'ltr';
    localStorage.setItem('astro-lang', lang);
  }, [lang]);

  // Theme: data-theme attribute, persistence, and the matching favicon.
  useEffect(() => {
    document.documentElement.dataset.theme = theme;
    localStorage.setItem('astro-theme', theme);
    const icon = document.querySelector("link[rel='icon']");
    if (icon) icon.href = theme === 'light' ? '/logo-light.svg' : '/logo.svg';
  }, [theme]);

  useEffect(() => {
    localStorage.setItem('astro-profile', profile);
  }, [profile]);

  useEffect(() => {
    localStorage.setItem('astro-env', environment);
  }, [environment]);

  // Chart colors follow the theme (recharts reads plain values, not CSS).
  const grid = theme === 'light' ? '#d7e4e9' : '#1d2b3b';
  const tick = theme === 'light' ? '#6b8290' : '#77889a';
  const tipBg = theme === 'light' ? '#ffffff' : '#111d2c';
  const tipBorder = theme === 'light' ? '#c9dbe1' : '#26384c';
  const tipColor = theme === 'light' ? '#12272f' : '#e8f2fa';

  // Load every resource the dashboard needs. Alerts, thresholds, assessment
  // and forecast are judged by the selected profile and environment.
  const load = async () => {
    setLoading(true);
    setError('');
    try {
      const ctx = `profile=${profile}&environment=${environment}`;
      const [
        health,
        roster,
        alerts,
        summary,
        vitals,
        firstLabs,
        report,
        rad,
        weather,
        thresholds,
        assessment,
        forecast,
      ] = await Promise.all([
        fetch(API.replace('/api/v1', '') + '/health').then((r) => {
          if (!r.ok) throw Error(t.errHealth);
          return r.json();
        }),
        get('/crew'),
        get(`/alerts?${ctx}`),
        get(`/crew/${crew}/summary`),
        get(`/crew/${crew}/vitals?days=30`),
        get(`/crew/${crew}/labs?limit=1000&offset=0`),
        get(`/crew/${crew}/report`),
        get('/radiation'),
        get('/space-weather'),
        get(`/crew/${crew}/thresholds?${ctx}`),
        get(`/crew/${crew}/assessment?${ctx}&days=7`),
        get(`/crew/${crew}/forecast?${ctx}&horizon=7`),
      ]);
      // Labs are paginated (max 1000 per page); fetch the rest for the table.
      const labRecords = [...firstLabs.records];
      for (let offset = firstLabs.records.length; offset < firstLabs.total; offset += 1000) {
        const next = await get(`/crew/${crew}/labs?limit=1000&offset=${offset}`);
        labRecords.push(...next.records);
      }
      setData({
        health,
        roster: roster.crew,
        alerts: alerts.alerts,
        summary,
        vitals: vitals.days,
        labs: labRecords,
        report,
        rad,
        weather,
        thresholds,
        assessment,
        forecast,
      });
      setLabPage(0);
    } catch (e) {
      setError(e.message + ' · ' + t.errServer);
    } finally {
      setLoading(false);
    }
  };

  // Refresh the cached space-weather snapshots, then reload everything.
  const refreshAll = async () => {
    setRefreshing(true);
    setError('');
    try {
      const r = await fetch(API + '/environment/refresh', { method: 'POST' });
      if (!r.ok) throw Error(t.errRefresh + ' ' + r.status);
      const result = await r.json();
      await load();
      const failed = Object.entries(result)
        .filter(([, v]) => v?.status === 'error')
        .map(([k]) => k.replace('_', ' '));
      if (failed.length) setError(t.errPartial + ' ' + failed.join(', ') + '. ' + t.errSnapshots);
    } catch (e) {
      setError(e.message + ' · ' + t.errCached);
    } finally {
      setRefreshing(false);
    }
  };

  useEffect(() => {
    load();
  }, [crew, profile, environment]);

  // Derived values shared by the pages.
  const vitals = data.vitals || [];
  const latest = vitals.at(-1) || {};
  const alerts = data.alerts || [];
  const critical = alerts.filter((a) => a.level === 'critical').length;
  const assessLatest = (data.assessment?.days || []).at(-1);
  const assessOff = assessLatest?.indicators.filter((i) => i.status !== 'nominal') || [];
  const trend = vitals.slice(-14).map((d) => ({
    day: d.date?.slice(5),
    hr: d.resting_heart_rate_bpm,
    spo2: d.spo2_percent,
    sleep: d.sleep_hours,
    stress: d.stress_score,
  }));
  const flux = data.rad?.hourly_flux_pfu || [];
  const dailyFlux = useMemo(() => {
    const m = {};
    flux.forEach((x) => {
      const k = x.time?.slice(5, 10);
      (m[k] ??= []).push(x.flux_pfu);
    });
    return Object.entries(m)
      .slice(-7)
      .map(([day, a]) => ({ day, flux: +(a.reduce((s, v) => s + v, 0) / a.length).toFixed(3) }));
  }, [flux]);

  // Download the weekly report as a plain-text file.
  const exportReport = () => {
    const r = data.report;
    if (!r) return;
    const lines = [
      t.reportTitle,
      `${t.crew} ${crew}`,
      `${t.reportPeriod} ${r.period}`,
      `${t.reportStatus} ${r.overall_status}`,
      '',
      `${t.reportAvgHr} ${r.vitals_7d.avg_resting_hr} bpm`,
      `${t.reportAvgSleep} ${r.vitals_7d.avg_sleep_hours} h`,
      `${t.reportAvgStress} ${r.vitals_7d.avg_stress}`,
      `${t.reportMinSpo2} ${r.vitals_7d.min_spo2}%`,
      `${t.reportFlaggedLabs} ${r.labs.flagged_total}`,
    ];
    const a = document.createElement('a');
    a.href = URL.createObjectURL(new Blob([lines.join('\n')], { type: 'text/plain' }));
    a.download = `astro-health-${crew}-weekly-report.txt`;
    a.click();
    URL.revokeObjectURL(a.href);
  };

  // Changing the lab filter resets the table to the first page.
  const handleLabFilterChange = (value) => {
    setLabFilter(value);
    setLabPage(0);
  };

  return (
    <div className="app-shell">
      <Sidebar
        t={t}
        page={page}
        mobile={mobile}
        onNavigate={setPage}
        onClose={() => setMobile(false)}
      />
      <main className="main">
        <Topbar
          t={t}
          page={page}
          theme={theme}
          lang={lang}
          refreshing={refreshing}
          onRefresh={refreshAll}
          onToggleTheme={() => setTheme(theme === 'dark' ? 'light' : 'dark')}
          onToggleLang={() => setLang(lang === 'en' ? 'ar' : 'en')}
          onOpenMenu={() => setMobile(true)}
          onGoOverview={() => setPage('Overview')}
        />
        <div className="content">
          <PageHeader
            t={t}
            page={page}
            data={data}
            crew={crew}
            profile={profile}
            environment={environment}
            refreshing={refreshing}
            onCrewChange={setCrew}
            onProfileChange={setProfile}
            onEnvironmentChange={setEnvironment}
            onRefresh={refreshAll}
          />
          {error && (
            <div className="error">
              <AlertTriangle size={16} />
              <span>
                {t.apiUnavailable} {error}
              </span>
              <button onClick={load}>{t.retry}</button>
            </div>
          )}
          {loading && !data.summary ? (
            <div className="loading">
              <div className="loader" />
              <span>{t.syncing}</span>
            </div>
          ) : (
            <>
              {page === 'Overview' && (
                <OverviewPage
                  t={t}
                  data={data}
                  latest={latest}
                  trend={trend}
                  alerts={alerts}
                  critical={critical}
                  dailyFlux={dailyFlux}
                  assessLatest={assessLatest}
                  assessOff={assessOff}
                  grid={grid}
                  tick={tick}
                  tipBg={tipBg}
                  tipBorder={tipBorder}
                  tipColor={tipColor}
                  onSelectAlert={setSelectedAlert}
                  onGoLabs={() => setPage('Labs')}
                />
              )}
              {page === 'Body' && (
                <BodyPage
                  t={t}
                  data={data}
                  latest={latest}
                  vitals={vitals}
                  theme={theme}
                  environment={environment}
                  profile={profile}
                  grid={grid}
                  tick={tick}
                  tipBg={tipBg}
                  tipBorder={tipBorder}
                />
              )}
              {page === 'Thresholds' && (
                <ThresholdsPage
                  t={t}
                  crew={crew}
                  vitals={vitals}
                  profile={profile}
                  environment={environment}
                  onProfileChange={setProfile}
                  onEnvironmentChange={setEnvironment}
                  grid={grid}
                  tick={tick}
                  tipBg={tipBg}
                  tipBorder={tipBorder}
                />
              )}
              {page === 'Labs' && (
                <LabsPage
                  t={t}
                  data={data}
                  crew={crew}
                  labFilter={labFilter}
                  labPage={labPage}
                  onLabFilterChange={handleLabFilterChange}
                  onLabPageChange={setLabPage}
                  onExportReport={exportReport}
                />
              )}
              {page === 'Environment' && (
                <EnvironmentPage
                  t={t}
                  data={data}
                  dailyFlux={dailyFlux}
                  grid={grid}
                  tick={tick}
                  tipBg={tipBg}
                  tipBorder={tipBorder}
                />
              )}
            </>
          )}
          <footer>
            <span>{t.footerLeft}</span>
            <span>
              {t.footerRight} <i>·</i> {data.health?.lab_records?.toLocaleString() || '—'}{' '}
              {t.labRecordsUpper}
            </span>
          </footer>
        </div>
      </main>
      {selectedAlert && (
        <AlertModal t={t} alert={selectedAlert} onClose={() => setSelectedAlert(null)} />
      )}
    </div>
  );
}

export default App;
