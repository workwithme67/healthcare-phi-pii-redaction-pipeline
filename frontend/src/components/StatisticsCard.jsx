/**
 * StatisticsCard.jsx
 * Compact metric card for the Detection page statistics strip.
 *
 * Props:
 *   title    — string label
 *   value    — number | string to display prominently
 *   subtitle — optional secondary line
 *   icon     — optional Lucide icon component
 *   color    — tailwind color token prefix (default: 'teal')
 *   trend    — optional { value: number, label: string }
 */

import React from 'react';

const COLOR_MAP = {
  teal:   { ring: 'ring-teal-500/20',   bg: 'bg-teal-500/10',   text: 'text-teal-400'   },
  blue:   { ring: 'ring-blue-500/20',   bg: 'bg-blue-500/10',   text: 'text-blue-400'   },
  purple: { ring: 'ring-purple-500/20', bg: 'bg-purple-500/10', text: 'text-purple-400' },
  amber:  { ring: 'ring-amber-500/20',  bg: 'bg-amber-500/10',  text: 'text-amber-400'  },
  rose:   { ring: 'ring-rose-500/20',   bg: 'bg-rose-500/10',   text: 'text-rose-400'   },
  cyan:   { ring: 'ring-cyan-500/20',   bg: 'bg-cyan-500/10',   text: 'text-cyan-400'   },
};

const StatisticsCard = ({
  title,
  value,
  subtitle,
  icon: Icon,
  color = 'teal',
  trend,
}) => {
  const c = COLOR_MAP[color] || COLOR_MAP.teal;

  return (
    <div className={`relative overflow-hidden bg-slate-800/50 rounded-2xl p-5 ring-1 ${c.ring} hover:bg-slate-800/70 transition-colors duration-200`}>
      {/* Decorative glow */}
      <div className={`absolute -top-6 -right-6 w-24 h-24 ${c.bg} rounded-full blur-2xl opacity-60 pointer-events-none`} />

      <div className="relative flex items-start justify-between">
        <div className="flex-1 min-w-0">
          <p className="text-xs font-semibold text-slate-400 uppercase tracking-wider mb-1">
            {title}
          </p>
          <p className={`text-3xl font-bold ${c.text} tabular-nums leading-none`}>
            {value ?? '—'}
          </p>
          {subtitle && (
            <p className="text-xs text-slate-500 mt-1.5 truncate">{subtitle}</p>
          )}
          {trend && (
            <p className={`text-xs mt-2 font-medium ${trend.value >= 0 ? 'text-emerald-400' : 'text-rose-400'}`}>
              {trend.value >= 0 ? '↑' : '↓'} {Math.abs(trend.value)} {trend.label}
            </p>
          )}
        </div>

        {Icon && (
          <div className={`flex-shrink-0 p-2.5 ${c.bg} rounded-xl ml-3`}>
            <Icon className={`w-5 h-5 ${c.text}`} />
          </div>
        )}
      </div>
    </div>
  );
};

export default StatisticsCard;
