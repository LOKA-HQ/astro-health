import { X } from 'lucide-react';
import { Pill } from './ui';
import { pretty, levelColor } from '../lib/format';

export default function AlertModal({ t, alert, onClose }) {
  return (
    <div className="modal-backdrop" onClick={() => onClose()}>
      <div className="alert-modal" onClick={(e) => e.stopPropagation()}>
        <button className="modal-close" onClick={() => onClose()}>
          <X size={18} />
        </button>
        <Pill tone={levelColor(alert.level)}>{t['level_' + alert.level] || alert.level}</Pill>
        <h2>
          {alert.indicator ? pretty(alert.indicator) : pretty(alert.type) + ' ' + t.alertWord}
        </h2>
        <p>{alert.message}</p>
        <div className="modal-meta">
          <span>{t.crewUpper}</span>
          <b>{alert.crew_id || 'GLOBAL'}</b>
          <span>{t.timepointUpper}</span>
          <b>{alert.timepoint || alert.date || t.snapshot}</b>
        </div>
      </div>
    </div>
  );
}
