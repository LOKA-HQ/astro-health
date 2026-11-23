import { Area, AreaChart, ResponsiveContainer } from 'recharts';

// Shared presentational components: cards, pills, metric tiles and the
// sparkline used by the radiation card. No data fetching happens here.

// Card with a title, an optional subtitle and an optional header action.
export function Card({ title, sub, action, children, className = '' }) {
  return (
    <section className={'card ' + className}>
      <div className="card-head">
        <div>
          <h3>{title}</h3>
          {sub && <p>{sub}</p>}
        </div>
        {action}
      </div>
      {children}
    </section>
  );
}

// Small colored label. Tones: blue (default), green, amber, red.
export function Pill({ children, tone = 'blue' }) {
  return <span className={'pill ' + tone}>{children}</span>;
}

// Metric tile: label, big value with a unit, and a footer line. The footer
// shows `foot` when given, otherwise a delta line (or a dataset note).
export function Metric({ t, label, value, unit, delta, icon: Icon, tone = 'cyan', foot }) {
  return (
    <div className="metric">
      <div className="metric-top">
        <span>{label}</span>
        <span className={'metric-icon ' + tone}>
          <Icon size={16} />
        </span>
      </div>
      <div className="metric-value">
        {value}
        <small>{unit}</small>
      </div>
      {foot ? (
        <div className="metric-foot">{foot}</div>
      ) : (
        <div className={'metric-delta ' + (delta?.startsWith('-') ? 'good' : '')}>
          {delta || t.preparedDataset}
        </div>
      )}
    </div>
  );
}

// Static sparkline (no animation) over an array of {v} points.
export function Spark({ data, color = '#5bd9d0' }) {
  return (
    <div className="spark">
      <ResponsiveContainer width="100%" height="100%">
        <AreaChart data={data}>
          <defs>
            <linearGradient id="sparkFill" x1="0" y1="0" x2="0" y2="1">
              <stop offset="0%" stopColor={color} stopOpacity={0.28} />
              <stop offset="100%" stopColor={color} stopOpacity={0} />
            </linearGradient>
          </defs>
          <Area
            dataKey="v"
            stroke={color}
            strokeWidth={2}
            fill="url(#sparkFill)"
            isAnimationActive={false}
          />
        </AreaChart>
      </ResponsiveContainer>
    </div>
  );
}
