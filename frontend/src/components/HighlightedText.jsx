/**
 * HighlightedText.jsx
 * Renders text with PHI/PII entity spans colour-coded by type.
 *
 * Props:
 *   text     — original text string
 *   entities — array of { type, value, start, end, confidence }
 */

import React from 'react';

// ── Colour Map ─────────────────────────────────────────────────────────────────
// Each entry: { bg (highlight bg), text (badge fg), border }
export const TYPE_COLORS = {
  EMAIL:            { bg: 'rgba(59,130,246,0.25)',  text: '#60a5fa', border: 'rgba(59,130,246,0.4)'  },
  PHONE:            { bg: 'rgba(34,197,94,0.20)',   text: '#4ade80', border: 'rgba(34,197,94,0.4)'   },
  DATE:             { bg: 'rgba(249,115,22,0.22)',  text: '#fb923c', border: 'rgba(249,115,22,0.4)'  },
  PAN:              { bg: 'rgba(168,85,247,0.22)',  text: '#c084fc', border: 'rgba(168,85,247,0.4)'  },
  AADHAAR:          { bg: 'rgba(239,68,68,0.22)',   text: '#f87171', border: 'rgba(239,68,68,0.4)'   },
  PASSPORT:         { bg: 'rgba(120,53,15,0.35)',   text: '#d97706', border: 'rgba(120,53,15,0.5)'   },
  CREDIT_CARD:      { bg: 'rgba(30,58,138,0.35)',   text: '#93c5fd', border: 'rgba(30,58,138,0.5)'   },
  IP_ADDRESS:       { bg: 'rgba(6,182,212,0.22)',   text: '#22d3ee', border: 'rgba(6,182,212,0.4)'   },
  PIN_CODE:         { bg: 'rgba(234,179,8,0.22)',   text: '#facc15', border: 'rgba(234,179,8,0.4)'   },
  URL:              { bg: 'rgba(16,185,129,0.20)',  text: '#34d399', border: 'rgba(16,185,129,0.4)'  },
  MRN:              { bg: 'rgba(244,114,182,0.22)', text: '#f472b6', border: 'rgba(244,114,182,0.4)' },
  PATIENT_ID:       { bg: 'rgba(251,146,60,0.22)',  text: '#fb923c', border: 'rgba(251,146,60,0.4)'  },
  HEALTH_INSURANCE: { bg: 'rgba(99,102,241,0.22)',  text: '#a5b4fc', border: 'rgba(99,102,241,0.4)'  },
  DEFAULT:          { bg: 'rgba(148,163,184,0.20)', text: '#94a3b8', border: 'rgba(148,163,184,0.4)' },
};

// ── Component ─────────────────────────────────────────────────────────────────

const HighlightedText = ({ text = '', entities = [] }) => {
  if (!text) {
    return (
      <p className="text-slate-500 text-sm italic">No text to display.</p>
    );
  }

  if (!entities.length) {
    return (
      <pre className="whitespace-pre-wrap text-slate-300 text-sm font-mono leading-relaxed">
        {text}
      </pre>
    );
  }

  // Build an array of segments: plain strings OR entity objects
  const segments = [];
  let cursor = 0;

  // Sort entities by start to ensure left-to-right traversal
  const sorted = [...entities].sort((a, b) => a.start - b.start);

  for (const entity of sorted) {
    // Skip overlapping entities (shouldn't occur after backend dedup)
    if (entity.start < cursor) continue;

    // Plain text before this entity
    if (entity.start > cursor) {
      segments.push({ kind: 'text', value: text.slice(cursor, entity.start) });
    }

    // Entity span
    segments.push({ kind: 'entity', entity, value: text.slice(entity.start, entity.end) });
    cursor = entity.end;
  }

  // Trailing plain text
  if (cursor < text.length) {
    segments.push({ kind: 'text', value: text.slice(cursor) });
  }

  return (
    <pre className="whitespace-pre-wrap text-sm font-mono leading-relaxed text-slate-300 select-text">
      {segments.map((seg, i) => {
        if (seg.kind === 'text') {
          return <span key={i}>{seg.value}</span>;
        }

        const colorConfig = TYPE_COLORS[seg.entity.type] || TYPE_COLORS.DEFAULT;
        return (
          <mark
            key={i}
            title={`${seg.entity.type} — confidence: ${Math.round(seg.entity.confidence * 100)}%`}
            style={{
              backgroundColor: colorConfig.bg,
              color: colorConfig.text,
              borderBottom: `2px solid ${colorConfig.border}`,
              borderRadius: '3px',
              padding: '1px 2px',
              cursor: 'help',
              fontWeight: 600,
            }}
          >
            {seg.value}
          </mark>
        );
      })}
    </pre>
  );
};

// ── Legend Component ──────────────────────────────────────────────────────────

export const ColorLegend = ({ activeTypes = [] }) => {
  const types = activeTypes.length
    ? activeTypes
    : Object.keys(TYPE_COLORS).filter(t => t !== 'DEFAULT');

  return (
    <div className="flex flex-wrap gap-2">
      {types.map(type => {
        const c = TYPE_COLORS[type] || TYPE_COLORS.DEFAULT;
        return (
          <span
            key={type}
            className="inline-flex items-center gap-1.5 px-2 py-1 rounded-md text-xs font-semibold"
            style={{ backgroundColor: c.bg, color: c.text }}
          >
            <span
              className="inline-block w-2 h-2 rounded-full"
              style={{ backgroundColor: c.text }}
            />
            {type}
          </span>
        );
      })}
    </div>
  );
};

export default HighlightedText;
