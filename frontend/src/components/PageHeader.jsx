import { ChevronDown, RefreshCw, Users } from 'lucide-react';

// Page title plus the context selectors: crew member, threshold profile
// (generic/personal) and environment. These drive every data load.
export default function PageHeader({
  t,
  page,
  data,
  crew,
  profile,
  environment,
  refreshing,
  onCrewChange,
  onProfileChange,
  onEnvironmentChange,
  onRefresh,
}) {
  return (
    <div className="page-title">
      <div>
        <div className="eyebrow">{t.eyebrow}</div>
        <h1>{t['title_' + page]}</h1>
        <p>{t['sub_' + page]}</p>
      </div>
      <div className="title-actions">
        <div className="crew-select">
          <Users size={15} />
          <select value={crew} onChange={(e) => onCrewChange(e.target.value)}>
            {(data.roster || ['C001', 'C002', 'C003', 'C004'].map((crew_id) => ({ crew_id }))).map(
              (c) => (
                <option key={c.crew_id} value={c.crew_id}>
                  {c.crew_id} · {t.crewMember}
                </option>
              ),
            )}
          </select>
          <ChevronDown size={14} />
        </div>
        <div className="crew-select">
          <select value={profile} onChange={(e) => onProfileChange(e.target.value)}>
            <option value="generic">{t.profileGeneric}</option>
            <option value="personal">{t.profilePersonal}</option>
          </select>
          <ChevronDown size={14} />
        </div>
        <div className="crew-select">
          <select value={environment} onChange={(e) => onEnvironmentChange(e.target.value)}>
            {['earth_ground', 'atmosphere', 'launch', 'iss', 'mars_transit', 'mars_surface'].map(
              (k) => (
                <option key={k} value={k}>
                  {t['env_' + k]}
                </option>
              ),
            )}
          </select>
          <ChevronDown size={14} />
        </div>
        <button className="refresh-btn" onClick={onRefresh} disabled={refreshing}>
          <RefreshCw size={14} /> {refreshing ? t.refreshing : t.refreshSources}
        </button>
      </div>
    </div>
  );
}
