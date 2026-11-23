import { Bell, ChevronRight, Menu, Moon, RefreshCw, Sun } from 'lucide-react';
import { pageLabel } from '../lib/format';

export default function Topbar({
  t,
  page,
  theme,
  lang,
  refreshing,
  onRefresh,
  onToggleTheme,
  onToggleLang,
  onOpenMenu,
  onGoOverview,
}) {
  return (
    <header className="topbar">
      <button className="mobile-menu" onClick={() => onOpenMenu()}>
        <Menu />
      </button>
      <div className="breadcrumb">
        {t.missionControl} <ChevronRight size={13} /> <b>{pageLabel(t, page).toUpperCase()}</b>
      </div>
      <div className="top-actions">
        <div className="utc">
          <span className="pulse-dot" /> {t.dataSnapshot} <b>· UTC</b>
        </div>
        <button
          className="icon-btn"
          title={t.refreshData}
          onClick={onRefresh}
          disabled={refreshing}
        >
          <RefreshCw size={17} />
        </button>
        <button
          className="icon-btn"
          title={theme === 'dark' ? t.lightMode : t.darkMode}
          onClick={() => onToggleTheme()}
        >
          {theme === 'dark' ? <Sun size={17} /> : <Moon size={17} />}
        </button>
        <button
          className="icon-btn lang-btn"
          title={lang === 'en' ? 'العربية' : 'English'}
          onClick={() => onToggleLang()}
        >
          {lang === 'en' ? 'عربي' : 'EN'}
        </button>
        <button className="icon-btn notification" onClick={() => onGoOverview()}>
          <Bell size={17} />
          <i />
        </button>
        <div className="top-avatar">MC</div>
      </div>
    </header>
  );
}
