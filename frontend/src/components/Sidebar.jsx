import { Activity, Atom, ChevronDown, LayoutDashboard, Microscope, Orbit, X } from 'lucide-react';
import Logo from '../Logo';

// Sidebar navigation: [page name, icon, strings key].
const nav = [
  ['Overview', LayoutDashboard, 'navOverview'],
  ['Body', Activity, 'navBody'],
  ['Labs', Microscope, 'navLabs'],
  ['Environment', Orbit, 'navEnv'],
];

export default function Sidebar({ t, page, mobile, onNavigate, onClose }) {
  return (
    <aside className={'sidebar ' + (mobile ? 'open' : '')}>
      <div className="brand">
        <Logo />
        <div>
          <b>
            ASTRO<span>HEALTH</span>
          </b>
          <small>{t.brandSub}</small>
        </div>
        <button className="close-mobile" onClick={() => onClose()}>
          <X />
        </button>
      </div>
      <div className="mission-label">{t.missionDashboard}</div>
      <nav>
        {nav.map(([name, Icon, key]) => (
          <button
            key={name}
            className={page === name ? 'active' : ''}
            onClick={() => {
              onNavigate(name);
              onClose();
            }}
          >
            <Icon size={18} />
            {t[key]}
            {page === name && <i />}
          </button>
        ))}
      </nav>
      <div className="side-bottom">
        <div className="connection">
          <span className="pulse-dot" />
          <div>
            <b>{t.systemsOk}</b>
            <small>{t.apiConnected}</small>
          </div>
        </div>
        <div className="mission-card">
          <div className="mission-icon">
            <Atom size={17} />
          </div>
          <div>
            <b>{t.marsTransit}</b>
            <small>{t.deepSpace}</small>
          </div>
          <span>↗</span>
          <small>
            {t.missionProfile} <strong>{t.demo}</strong>
          </small>
        </div>
        <div className="profile">
          <div className="avatar">MC</div>
          <div>
            <b>{t.missionControlName}</b>
            <small>{t.flightSurgeon}</small>
          </div>
          <ChevronDown size={15} />
        </div>
      </div>
    </aside>
  );
}
