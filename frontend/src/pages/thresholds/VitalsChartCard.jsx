import { useState } from 'react';
import {
  CartesianGrid,
  Line,
  LineChart,
  ReferenceLine,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from 'recharts';
import { Card } from '../../components/ui';
import { chartLimits } from '../../lib/context';
import { indName } from '../../lib/format';

const LINE_COLOR = { critical: '#ff8f8f', warning: '#e9b65b', generic: '#8494a8' };

// One vital over the last 30 days with the limits in force drawn across it.
export default function VitalsChartCard({ t, vitals, thresholds, grid, tick, tipBg, tipBorder }) {
  const [field, setField] = useState('resting_heart_rate_bpm');
  const lines = chartLimits(thresholds?.indicators?.[field]);

  return (
    <Card
      title={t.th_chartTitle}
      sub={t.th_chartSub}
      action={
        <select
          className="filter-select"
          aria-label={t.th_colIndicator}
          value={field}
          onChange={(e) => setField(e.target.value)}
        >
          {Object.keys(thresholds?.indicators || {}).map((f) => (
            <option key={f} value={f}>
              {indName(t, f)}
            </option>
          ))}
        </select>
      }
    >
      <div className="chart tall-chart">
        <ResponsiveContainer width="100%" height="100%">
          <LineChart data={vitals}>
            <CartesianGrid strokeDasharray="3 5" stroke={grid} />
            <XAxis
              dataKey="date"
              tick={{ fill: tick, fontSize: 10 }}
              tickFormatter={(x) => x.slice(5)}
              axisLine={false}
              tickLine={false}
            />
            <YAxis
              tick={{ fill: tick, fontSize: 10 }}
              axisLine={false}
              tickLine={false}
              domain={['auto', 'auto']}
            />
            <Tooltip
              contentStyle={{
                background: tipBg,
                border: `1px solid ${tipBorder}`,
                borderRadius: 10,
              }}
            />
            {lines.map((l) => {
              const label = `${t['th_line_' + l.tone + '_' + l.side]} ${l.y}`;
              return (
                <ReferenceLine
                  key={label}
                  y={l.y}
                  ifOverflow="extendDomain"
                  stroke={LINE_COLOR[l.tone]}
                  strokeDasharray={l.tone === 'generic' ? '2 4' : '5 4'}
                  label={{
                    value: label,
                    fill: LINE_COLOR[l.tone],
                    fontSize: 10,
                    position: l.tone === 'generic' ? 'insideBottomRight' : 'insideTopRight',
                  }}
                />
              );
            })}
            <Line
              dataKey={field}
              name={indName(t, field)}
              stroke="#55d8d0"
              dot={false}
              strokeWidth={2}
            />
          </LineChart>
        </ResponsiveContainer>
      </div>
      <div className="tiny-note">{t.th_chartNote}</div>
    </Card>
  );
}
