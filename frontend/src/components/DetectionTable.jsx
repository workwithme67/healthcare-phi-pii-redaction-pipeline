/**
 * DetectionTable.jsx
 * Reusable table displaying detected PHI/PII entities.
 * Props:
 *   entities  — array of { type, value, start, end, confidence }
 *   loading   — boolean
 */

import React from 'react';
import { TYPE_COLORS } from './HighlightedText';

const CONFIDENCE_BAR_WIDTH = (conf) => `${Math.round(conf * 100)}%`;

const DetectionTable = ({ entities = [], loading = false }) => {
  if (loading) {
    return (
      <div className="flex items-center justify-center py-12">
        <div className="flex flex-col items-center gap-3">
          <div className="w-8 h-8 border-2 border-teal-500 border-t-transparent rounded-full animate-spin" />
          <span className="text-sm text-slate-400">Scanning for PHI/PII…</span>
        </div>
      </div>
    );
  }

  if (!entities.length) {
    return (
      <div className="flex flex-col items-center justify-center py-12 text-slate-500">
        <svg className="w-12 h-12 mb-3 opacity-40" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
        </svg>
        <p className="text-sm font-medium">No entities detected yet</p>
        <p className="text-xs mt-1">Paste clinical text and click Detect</p>
      </div>
    );
  }

  return (
    <div className="overflow-x-auto rounded-xl border border-slate-700/50">
      <table className="w-full text-sm">
        <thead>
          <tr className="bg-slate-800/60 text-slate-400 text-xs uppercase tracking-wider">
            <th className="px-4 py-3 text-left font-semibold">#</th>
            <th className="px-4 py-3 text-left font-semibold">Type</th>
            <th className="px-4 py-3 text-left font-semibold">Detected Value</th>
            <th className="px-4 py-3 text-left font-semibold">Position</th>
            <th className="px-4 py-3 text-left font-semibold">Confidence</th>
          </tr>
        </thead>
        <tbody className="divide-y divide-slate-700/40">
          {entities.map((entity, idx) => {
            const colorConfig = TYPE_COLORS[entity.type] || TYPE_COLORS.DEFAULT;
            return (
              <tr
                key={`${entity.type}-${entity.start}-${idx}`}
                className="hover:bg-slate-800/30 transition-colors duration-150 group"
              >
                {/* Row number */}
                <td className="px-4 py-3 text-slate-500 font-mono text-xs">
                  {String(idx + 1).padStart(2, '0')}
                </td>

                {/* Type badge */}
                <td className="px-4 py-3">
                  <span
                    className="inline-flex items-center px-2.5 py-1 rounded-lg text-xs font-bold tracking-wide"
                    style={{ backgroundColor: colorConfig.bg, color: colorConfig.text }}
                  >
                    {entity.type}
                  </span>
                </td>

                {/* Value */}
                <td className="px-4 py-3 font-mono text-slate-200 max-w-[200px] truncate" title={entity.value}>
                  {entity.value}
                </td>

                {/* Position */}
                <td className="px-4 py-3 font-mono text-xs text-slate-400">
                  <span className="bg-slate-800 px-2 py-0.5 rounded">
                    {entity.start}–{entity.end}
                  </span>
                </td>

                {/* Confidence bar */}
                <td className="px-4 py-3">
                  <div className="flex items-center gap-2">
                    <div className="flex-1 bg-slate-700 rounded-full h-1.5 min-w-[60px]">
                      <div
                        className="h-1.5 rounded-full transition-all duration-500"
                        style={{
                          width: CONFIDENCE_BAR_WIDTH(entity.confidence),
                          backgroundColor: colorConfig.text,
                        }}
                      />
                    </div>
                    <span className="text-xs text-slate-400 tabular-nums w-10 text-right">
                      {Math.round(entity.confidence * 100)}%
                    </span>
                  </div>
                </td>
              </tr>
            );
          })}
        </tbody>
      </table>

      {/* Footer summary */}
      <div className="px-4 py-2.5 bg-slate-800/30 border-t border-slate-700/40 flex items-center justify-between">
        <span className="text-xs text-slate-500">
          {entities.length} {entities.length === 1 ? 'entity' : 'entities'} found
        </span>
        <span className="text-xs text-slate-500">
          Types: {[...new Set(entities.map(e => e.type))].join(', ')}
        </span>
      </div>
    </div>
  );
};

export default DetectionTable;
