/**
 * AIDetection.jsx
 * Day 4 — AI-Powered PHI/PII Detection Page
 *
 * Features:
 *  - Large text input with "Load Sample" & "Clear"
 *  - "Detect Using AI" button → POST /api/detect-ai
 *  - "Compare Detection" button → POST /api/compare
 *  - 5 Dashboard cards: Total, Regex, Presidio, spaCy, Merged, Time
 *  - Color-coded highlighted text view
 *  - Entity table: Entity | Type | Source | Confidence | Start | End
 *  - Engine comparison bar chart
 *  - Entity type statistics
 */

import React, { useState, useCallback, useRef } from 'react';
import {
  Brain,
  ScanSearch,
  BarChart3,
  Eraser,
  Copy,
  CheckCheck,
  FileText,
  Clock,
  AlertCircle,
  Zap,
  Shield,
  Activity,
  Cpu,
  TrendingUp,
  ChevronRight,
  Info,
  Layers,
} from 'lucide-react';
import aiDetectionService from '../services/aiDetectionService';

// ── Highlight colour map ───────────────────────────────────────────────────────
const ENTITY_COLORS = {
  PERSON:              { bg: 'rgba(34,197,94,0.25)',  border: '#22c55e', text: '#4ade80',  label: 'Person'       },
  DOCTOR:              { bg: 'rgba(59,130,246,0.25)', border: '#3b82f6', text: '#60a5fa',  label: 'Doctor'       },
  HOSPITAL:            { bg: 'rgba(168,85,247,0.25)', border: '#a855f7', text: '#c084fc',  label: 'Hospital'     },
  ORGANIZATION:        { bg: 'rgba(249,115,22,0.25)', border: '#f97316', text: '#fb923c',  label: 'Organization' },
  LOCATION:            { bg: 'rgba(161,110,82,0.25)', border: '#a16e4e', text: '#c49a7a',  label: 'Location'     },
  PHONE_NUMBER:        { bg: 'rgba(6,182,212,0.25)',  border: '#06b6d4', text: '#22d3ee',  label: 'Phone'        },
  EMAIL_ADDRESS:       { bg: 'rgba(236,72,153,0.25)', border: '#ec4899', text: '#f472b6',  label: 'Email'        },
  DATE_TIME:           { bg: 'rgba(234,179,8,0.25)',  border: '#eab308', text: '#facc15',  label: 'Date/Time'    },
  CREDIT_CARD:         { bg: 'rgba(239,68,68,0.25)',  border: '#ef4444', text: '#f87171',  label: 'Credit Card'  },
  IP_ADDRESS:          { bg: 'rgba(99,102,241,0.25)', border: '#6366f1', text: '#818cf8',  label: 'IP Address'   },
  URL:                 { bg: 'rgba(20,184,166,0.25)', border: '#14b8a6', text: '#2dd4bf',  label: 'URL'          },
  AADHAAR_NUMBER:      { bg: 'rgba(245,158,11,0.25)', border: '#f59e0b', text: '#fbbf24',  label: 'Aadhaar'      },
  IN_PAN:              { bg: 'rgba(16,185,129,0.25)', border: '#10b981', text: '#34d399',  label: 'PAN'          },
  IN_PASSPORT:         { bg: 'rgba(139,92,246,0.25)', border: '#8b5cf6', text: '#a78bfa',  label: 'Passport'     },
  PATIENT:             { bg: 'rgba(52,211,153,0.25)', border: '#34d399', text: '#6ee7b7',  label: 'Patient ID'   },
  MEDICAL_LICENSE:     { bg: 'rgba(248,113,113,0.25)',border: '#f87171', text: '#fca5a5',  label: 'Insurance'    },
  MEDICAL_RECORD_NUMBER:{ bg: 'rgba(251,146,60,0.25)',border: '#fb923c', text: '#fdba74',  label: 'MRN'          },
  DEFAULT:             { bg: 'rgba(148,163,184,0.25)',border: '#94a3b8', text: '#cbd5e1',  label: 'Other'        },
};

const getEntityColor = (type) => ENTITY_COLORS[type] || ENTITY_COLORS.DEFAULT;

const SOURCE_COLORS = {
  Presidio: { bg: 'bg-violet-500/15', text: 'text-violet-400', border: 'border-violet-500/30' },
  spaCy:    { bg: 'bg-sky-500/15',    text: 'text-sky-400',    border: 'border-sky-500/30'    },
  Regex:    { bg: 'bg-amber-500/15',  text: 'text-amber-400',  border: 'border-amber-500/30'  },
  Merged:   { bg: 'bg-teal-500/15',   text: 'text-teal-400',   border: 'border-teal-500/30'   },
};

const getSourceStyle = (source) => SOURCE_COLORS[source] || SOURCE_COLORS.Merged;

// ── Sample clinical note ───────────────────────────────────────────────────────
const SAMPLE_TEXT = `Clinical Note — Discharge Summary

Patient: John Smith
Date of Admission: 12/04/2026
Date of Discharge: 18/04/2026
Patient ID: PID-A987654
Medical Record No: MRN-REF-20240115

Attending Physician: Dr. Michael Adams, MD
Consulting: Dr. Priya Sharma (Neurology)

Facility: Apollo Hospital, New Delhi, India

Contact:
  Phone: +91 98765 43210
  Email: john.smith@healthmail.in

Identity:
  Aadhaar: 2345 6789 0123
  PAN: ABCDE1234F
  Passport: B1234567

Insurance:
  Health Insurance No: HIN-POL-234567

Financial:
  Credit Card: 4111 1111 1111 1111

System:
  IP: 192.168.1.105
  Portal: https://portal.apollo.in/patient/12345

Diagnosis:
  Patient presents with symptoms consistent with Parkinson's disease.
  Rule out Alzheimer's disease and Crohn's disease.
  MRI findings reviewed by Dr. Adams at Apollo Hospital, New Delhi.

Note: Hodgkin lymphoma and Wilson disease were excluded by lab workup.

Follow-up: Scheduled at Apollo Hospital for 25/05/2026.`;

// ── Helpers ───────────────────────────────────────────────────────────────────
const formatMs = (ms) => {
  if (ms == null) return '—';
  if (ms < 1) return '<1 ms';
  if (ms < 1000) return `${ms.toFixed(1)} ms`;
  return `${(ms / 1000).toFixed(2)} s`;
};

// ── Highlighted Text Component ────────────────────────────────────────────────
const HighlightedTextAI = ({ text, entities }) => {
  if (!text) return null;
  if (!entities || entities.length === 0) {
    return (
      <pre className="whitespace-pre-wrap text-sm font-mono text-slate-300 leading-relaxed">
        {text}
      </pre>
    );
  }

  const sortedEntities = [...entities].sort((a, b) => a.start - b.start);
  const segments = [];
  let cursor = 0;

  sortedEntities.forEach((ent, i) => {
    if (ent.start > cursor) {
      segments.push(
        <span key={`plain-${i}`} className="text-slate-300">
          {text.slice(cursor, ent.start)}
        </span>
      );
    }
    if (ent.end > cursor) {
      const color = getEntityColor(ent.type);
      segments.push(
        <span
          key={`ent-${i}`}
          className="relative group cursor-help rounded px-0.5"
          style={{
            backgroundColor: color.bg,
            borderBottom: `2px solid ${color.border}`,
            color: color.text,
            fontWeight: 600,
          }}
          title={`${ent.type} (${ent.source}) — ${(ent.confidence * 100).toFixed(0)}%`}
        >
          {text.slice(Math.max(cursor, ent.start), ent.end)}
          {/* Tooltip */}
          <span className="absolute bottom-full left-1/2 -translate-x-1/2 mb-1 px-2 py-1 bg-slate-900 border border-slate-700 rounded text-xs text-slate-200 whitespace-nowrap opacity-0 group-hover:opacity-100 transition-opacity z-10 pointer-events-none shadow-lg">
            {ent.type} · {ent.source} · {(ent.confidence * 100).toFixed(0)}%
          </span>
        </span>
      );
      cursor = ent.end;
    }
  });

  if (cursor < text.length) {
    segments.push(
      <span key="plain-tail" className="text-slate-300">
        {text.slice(cursor)}
      </span>
    );
  }

  return (
    <pre className="whitespace-pre-wrap text-sm font-mono leading-relaxed">
      {segments}
    </pre>
  );
};

// ── Dashboard Card ─────────────────────────────────────────────────────────────
const DashCard = ({ title, value, subtitle, icon: Icon, colorClass, glowColor }) => (
  <div
    className="relative bg-slate-900/70 rounded-2xl border border-slate-800/60 p-5 overflow-hidden group hover:border-slate-700/60 transition-all duration-300"
    style={{ boxShadow: `0 0 0 0 ${glowColor}`, transition: 'box-shadow 0.3s' }}
    onMouseEnter={(e) => { e.currentTarget.style.boxShadow = `0 0 20px 2px ${glowColor}`; }}
    onMouseLeave={(e) => { e.currentTarget.style.boxShadow = '0 0 0 0 transparent'; }}
  >
    <div className="absolute inset-0 bg-gradient-to-br from-transparent to-slate-800/20 pointer-events-none" />
    <div className="relative">
      <div className="flex items-center justify-between mb-3">
        <p className="text-xs font-semibold text-slate-400 uppercase tracking-wider">{title}</p>
        <div className={`p-1.5 rounded-lg ${colorClass} bg-opacity-10`}>
          <Icon className="w-4 h-4" style={{ color: glowColor }} />
        </div>
      </div>
      <p className="text-3xl font-black text-white tabular-nums">{value ?? '—'}</p>
      {subtitle && <p className="text-xs text-slate-500 mt-1">{subtitle}</p>}
    </div>
  </div>
);

// ── Engine Comparison Bar ──────────────────────────────────────────────────────
const EngineBar = ({ label, count, maxCount, color, timeMs }) => {
  const pct = maxCount > 0 ? Math.round((count / maxCount) * 100) : 0;
  return (
    <div className="space-y-1">
      <div className="flex items-center justify-between text-xs">
        <span className="font-semibold text-slate-300">{label}</span>
        <span className="text-slate-400 tabular-nums">
          {count} entities · {formatMs(timeMs)}
        </span>
      </div>
      <div className="h-2.5 bg-slate-800 rounded-full overflow-hidden">
        <div
          className="h-full rounded-full transition-all duration-700"
          style={{ width: `${pct}%`, backgroundColor: color }}
        />
      </div>
    </div>
  );
};

// ── Entity Table ───────────────────────────────────────────────────────────────
const EntityTable = ({ entities, loading }) => {
  if (loading) {
    return (
      <div className="flex items-center justify-center py-12 gap-3 text-slate-400">
        <div className="w-5 h-5 border-2 border-violet-500 border-t-transparent rounded-full animate-spin" />
        <span className="text-sm">Analyzing…</span>
      </div>
    );
  }

  if (!entities || entities.length === 0) {
    return (
      <div className="text-center py-10">
        <Brain className="w-10 h-10 text-slate-700 mx-auto mb-3" />
        <p className="text-sm text-slate-500">No entities detected yet</p>
      </div>
    );
  }

  return (
    <div className="overflow-x-auto">
      <table className="w-full text-sm">
        <thead>
          <tr className="border-b border-slate-800">
            <th className="text-left py-2.5 px-3 text-xs font-semibold text-slate-400 uppercase tracking-wider">Entity</th>
            <th className="text-left py-2.5 px-3 text-xs font-semibold text-slate-400 uppercase tracking-wider">Type</th>
            <th className="text-left py-2.5 px-3 text-xs font-semibold text-slate-400 uppercase tracking-wider">Source</th>
            <th className="text-left py-2.5 px-3 text-xs font-semibold text-slate-400 uppercase tracking-wider">Confidence</th>
            <th className="text-left py-2.5 px-3 text-xs font-semibold text-slate-400 uppercase tracking-wider">Start</th>
            <th className="text-left py-2.5 px-3 text-xs font-semibold text-slate-400 uppercase tracking-wider">End</th>
          </tr>
        </thead>
        <tbody>
          {entities.map((ent, i) => {
            const color = getEntityColor(ent.type);
            const srcStyle = getSourceStyle(ent.source);
            const confPct = Math.round(ent.confidence * 100);
            return (
              <tr key={i} className="border-b border-slate-800/40 hover:bg-slate-800/30 transition-colors">
                <td className="py-2.5 px-3">
                  <span
                    className="font-mono text-sm font-semibold px-2 py-0.5 rounded"
                    style={{ backgroundColor: color.bg, color: color.text }}
                  >
                    {ent.value}
                  </span>
                </td>
                <td className="py-2.5 px-3">
                  <span
                    className="text-xs font-bold px-2 py-0.5 rounded-full border"
                    style={{
                      backgroundColor: color.bg,
                      borderColor: color.border,
                      color: color.text,
                    }}
                  >
                    {ent.type}
                  </span>
                </td>
                <td className="py-2.5 px-3">
                  <span className={`text-xs font-semibold px-2 py-0.5 rounded-full border ${srcStyle.bg} ${srcStyle.text} ${srcStyle.border}`}>
                    {ent.source}
                  </span>
                </td>
                <td className="py-2.5 px-3">
                  <div className="flex items-center gap-2">
                    <div className="w-16 h-1.5 bg-slate-800 rounded-full overflow-hidden">
                      <div
                        className="h-full rounded-full"
                        style={{
                          width: `${confPct}%`,
                          backgroundColor: confPct >= 90 ? '#22c55e' : confPct >= 70 ? '#eab308' : '#ef4444',
                        }}
                      />
                    </div>
                    <span className="text-xs text-slate-400 tabular-nums">{confPct}%</span>
                  </div>
                </td>
                <td className="py-2.5 px-3 text-xs text-slate-400 tabular-nums font-mono">{ent.start}</td>
                <td className="py-2.5 px-3 text-xs text-slate-400 tabular-nums font-mono">{ent.end}</td>
              </tr>
            );
          })}
        </tbody>
      </table>
    </div>
  );
};

// ── Color Legend ───────────────────────────────────────────────────────────────
const ColorLegend = ({ activeTypes }) => (
  <div className="flex flex-wrap gap-2">
    {activeTypes.map((type) => {
      const c = getEntityColor(type);
      return (
        <span
          key={type}
          className="text-xs font-semibold px-2.5 py-1 rounded-full border"
          style={{ backgroundColor: c.bg, borderColor: c.border, color: c.text }}
        >
          {c.label || type}
        </span>
      );
    })}
  </div>
);

// ── Main Page ─────────────────────────────────────────────────────────────────
const AIDetection = () => {
  const [inputText, setInputText] = useState('');
  const [entities, setEntities] = useState([]);
  const [compareData, setCompareData] = useState(null);
  const [processingTime, setProcessingTime] = useState(null);
  const [presidioCount, setPresidioCount] = useState(null);
  const [spacyCount, setSpacyCount] = useState(null);

  const [loading, setLoading] = useState(false);
  const [comparing, setComparing] = useState(false);
  const [error, setError] = useState('');
  const [mode, setMode] = useState('idle'); // 'idle' | 'detected' | 'compared'
  const [copied, setCopied] = useState(false);

  const resultsRef = useRef(null);

  // ── Detect Using AI ──────────────────────────────────────────────────────────
  const handleDetectAI = async () => {
    if (!inputText.trim()) { setError('Please enter some text to analyze.'); return; }
    setError('');
    setLoading(true);
    setMode('idle');
    setEntities([]);
    setCompareData(null);

    try {
      const data = await aiDetectionService.detectAI(inputText);
      setEntities(data.entities || []);
      setProcessingTime(data.processing_time_ms);
      setPresidioCount(data.presidio_count);
      setSpacyCount(data.spacy_count);
      setMode('detected');
      setTimeout(() => resultsRef.current?.scrollIntoView({ behavior: 'smooth', block: 'start' }), 100);
    } catch (err) {
      const detail = err.response?.data?.detail || err.message || 'AI detection failed.';
      setError(detail.includes('503') || detail.includes('unavailable')
        ? '🔧 AI models not ready. Install presidio-analyzer, presidio-anonymizer, spacy, then run: python -m spacy download en_core_web_lg'
        : detail);
    } finally {
      setLoading(false);
    }
  };

  // ── Compare Detection ────────────────────────────────────────────────────────
  const handleCompare = async () => {
    if (!inputText.trim()) { setError('Please enter some text to compare.'); return; }
    setError('');
    setComparing(true);
    setMode('idle');

    try {
      const data = await aiDetectionService.compareDetection(inputText);
      setCompareData(data);
      setEntities(data.merged_entities || []);
      setProcessingTime(data.processing_time_ms);
      setPresidioCount(data.presidio);
      setSpacyCount(data.spacy);
      setMode('compared');
      setTimeout(() => resultsRef.current?.scrollIntoView({ behavior: 'smooth', block: 'start' }), 100);
    } catch (err) {
      const detail = err.response?.data?.detail || err.message || 'Comparison failed.';
      setError(detail.includes('503') || detail.includes('unavailable')
        ? '🔧 AI models not ready. Install presidio-analyzer, presidio-anonymizer, spacy, then run: python -m spacy download en_core_web_lg'
        : detail);
    } finally {
      setComparing(false);
    }
  };

  const handleClear = () => {
    setInputText('');
    setEntities([]);
    setCompareData(null);
    setProcessingTime(null);
    setPresidioCount(null);
    setSpacyCount(null);
    setMode('idle');
    setError('');
  };

  const handleCopy = async () => {
    const text = entities.map(e => `${e.type}: "${e.value}" (${e.source})`).join('\n') || inputText;
    try {
      await navigator.clipboard.writeText(text);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    } catch { setError('Failed to copy to clipboard.'); }
  };

  const activeTypes = [...new Set(entities.map(e => e.type))];

  const maxEngineCount = compareData
    ? Math.max(compareData.regex, compareData.presidio, compareData.spacy, 1)
    : 1;

  // ── Render ───────────────────────────────────────────────────────────────────
  return (
    <div className="min-h-screen bg-slate-950 text-white">
      {/* ── Page Header ─────────────────────────────────────────────────────── */}
      <div className="bg-gradient-to-br from-violet-950/40 via-slate-900 to-slate-950 border-b border-slate-800/60 px-6 py-8">
        <div className="max-w-7xl mx-auto">
          <div className="flex items-center gap-3 mb-2">
            <div className="p-2.5 bg-violet-500/10 rounded-xl ring-1 ring-violet-500/20">
              <Brain className="w-6 h-6 text-violet-400" />
            </div>
            <div>
              <h1 className="text-2xl font-bold text-white tracking-tight">
                AI Detection Engine
              </h1>
              <p className="text-sm text-slate-400 mt-0.5">
                Microsoft Presidio + spaCy NER · Entity Merging · Medical Context Awareness
              </p>
            </div>
            <div className="ml-auto flex items-center gap-2">
              <span className="px-2.5 py-1 text-xs font-bold bg-violet-500/15 text-violet-400 border border-violet-500/30 rounded-full">
                Presidio
              </span>
              <span className="px-2.5 py-1 text-xs font-bold bg-sky-500/15 text-sky-400 border border-sky-500/30 rounded-full">
                spaCy NER
              </span>
              <span className="px-2.5 py-1 text-xs font-bold bg-teal-500/15 text-teal-400 border border-teal-500/30 rounded-full">
                Day 4
              </span>
            </div>
          </div>

          {activeTypes.length > 0 && (
            <div className="mt-4 p-3 bg-slate-800/40 rounded-xl border border-slate-700/40">
              <p className="text-xs text-slate-400 mb-2 font-semibold uppercase tracking-wider">
                Detected entity types in this run
              </p>
              <ColorLegend activeTypes={activeTypes} />
            </div>
          )}
        </div>
      </div>

      <div className="max-w-7xl mx-auto px-6 py-6 space-y-6">

        {/* ── Dashboard Cards ────────────────────────────────────────────── */}
        <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-3">
          <DashCard
            title="Total Entities"
            value={entities.length || '—'}
            subtitle="Merged & deduplicated"
            icon={Layers}
            colorClass="bg-violet-500"
            glowColor="rgba(139,92,246,0.4)"
          />
          <DashCard
            title="Presidio"
            value={presidioCount ?? '—'}
            subtitle="Presidio detections"
            icon={Shield}
            colorClass="bg-violet-400"
            glowColor="rgba(167,139,250,0.35)"
          />
          <DashCard
            title="spaCy NER"
            value={spacyCount ?? '—'}
            subtitle="spaCy detections"
            icon={Brain}
            colorClass="bg-sky-500"
            glowColor="rgba(56,189,248,0.35)"
          />
          <DashCard
            title="Regex"
            value={compareData?.regex ?? '—'}
            subtitle="Regex detections"
            icon={Activity}
            colorClass="bg-amber-500"
            glowColor="rgba(251,191,36,0.35)"
          />
          <DashCard
            title="Merged"
            value={compareData?.merged ?? entities.length || '—'}
            subtitle="After deduplication"
            icon={TrendingUp}
            colorClass="bg-teal-500"
            glowColor="rgba(20,184,166,0.35)"
          />
          <DashCard
            title="Detection Time"
            value={processingTime != null ? formatMs(processingTime) : '—'}
            subtitle="Full pipeline"
            icon={Clock}
            colorClass="bg-emerald-500"
            glowColor="rgba(52,211,153,0.35)"
          />
        </div>

        {/* ── Input Panel ────────────────────────────────────────────────── */}
        <div className="bg-slate-900/50 rounded-2xl border border-slate-800/60 overflow-hidden">
          <div className="flex items-center justify-between px-5 py-4 border-b border-slate-800/40">
            <div className="flex items-center gap-2">
              <FileText className="w-4 h-4 text-slate-400" />
              <span className="text-sm font-semibold text-slate-200">Clinical Notes Input</span>
            </div>
            <button
              onClick={() => { setInputText(SAMPLE_TEXT); setMode('idle'); setEntities([]); setCompareData(null); setError(''); }}
              className="text-xs text-violet-400 hover:text-violet-300 font-medium px-2 py-1 rounded-lg hover:bg-violet-500/10 transition-colors"
            >
              Load sample →
            </button>
          </div>

          <div className="p-5">
            <textarea
              id="ai-clinical-text-input"
              value={inputText}
              onChange={(e) => { setInputText(e.target.value); setMode('idle'); }}
              placeholder={"Paste clinical notes here…\n\nExample: Patient John Smith visited Apollo Hospital on 12/04/2026.\nAttending: Dr. Michael Adams. Phone: +91 98765 43210"}
              rows={10}
              className="w-full bg-slate-800/50 border border-slate-700/60 rounded-xl px-4 py-3 text-sm font-mono text-slate-200 placeholder-slate-600 resize-y focus:outline-none focus:ring-2 focus:ring-violet-500/50 focus:border-violet-500/50 transition-all duration-200 min-h-[160px]"
            />
            <div className="flex items-center justify-between mt-2">
              <span className="text-xs text-slate-500">
                {inputText.length.toLocaleString()} characters
                {entities.length > 0 && (
                  <span className="ml-2 text-violet-400">
                    · {entities.length} {entities.length === 1 ? 'entity' : 'entities'} detected
                  </span>
                )}
              </span>
              {processingTime != null && (
                <span className="text-xs text-slate-500 flex items-center gap-1">
                  <Zap className="w-3 h-3 text-amber-400" />
                  {formatMs(processingTime)}
                </span>
              )}
            </div>
          </div>

          {/* Action Buttons */}
          <div className="px-5 pb-5 flex flex-wrap gap-3">
            <button
              id="detect-ai-btn"
              onClick={handleDetectAI}
              disabled={loading || comparing}
              className="flex items-center gap-2 px-5 py-2.5 bg-violet-600 hover:bg-violet-500 disabled:bg-violet-800/50 disabled:cursor-not-allowed text-white text-sm font-semibold rounded-xl transition-all duration-200 shadow-lg shadow-violet-600/25"
            >
              {loading ? (
                <div className="w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin" />
              ) : (
                <Brain className="w-4 h-4" />
              )}
              {loading ? 'Detecting…' : 'Detect Using AI'}
            </button>

            <button
              id="compare-detection-btn"
              onClick={handleCompare}
              disabled={loading || comparing}
              className="flex items-center gap-2 px-5 py-2.5 bg-sky-600 hover:bg-sky-500 disabled:bg-sky-800/50 disabled:cursor-not-allowed text-white text-sm font-semibold rounded-xl transition-all duration-200 shadow-lg shadow-sky-600/20"
            >
              {comparing ? (
                <div className="w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin" />
              ) : (
                <BarChart3 className="w-4 h-4" />
              )}
              {comparing ? 'Comparing…' : 'Compare Detection'}
            </button>

            <button
              id="copy-output-btn"
              onClick={handleCopy}
              disabled={entities.length === 0}
              className="flex items-center gap-2 px-5 py-2.5 bg-slate-700 hover:bg-slate-600 disabled:bg-slate-800/40 disabled:cursor-not-allowed text-white text-sm font-semibold rounded-xl transition-all duration-200"
            >
              {copied ? <CheckCheck className="w-4 h-4 text-emerald-400" /> : <Copy className="w-4 h-4" />}
              {copied ? 'Copied!' : 'Copy Output'}
            </button>

            <button
              id="clear-ai-btn"
              onClick={handleClear}
              className="flex items-center gap-2 px-5 py-2.5 bg-slate-800 hover:bg-slate-700 text-slate-300 hover:text-white text-sm font-semibold rounded-xl transition-all duration-200 border border-slate-700/60"
            >
              <Eraser className="w-4 h-4" />
              Clear
            </button>
          </div>
        </div>

        {/* ── Error Banner ──────────────────────────────────────────────── */}
        {error && (
          <div className="flex items-start gap-3 p-4 bg-rose-500/10 border border-rose-500/30 rounded-xl">
            <AlertCircle className="w-5 h-5 text-rose-400 flex-shrink-0 mt-0.5" />
            <div>
              <p className="text-sm font-semibold text-rose-300">Error</p>
              <p className="text-sm text-rose-400/80 mt-0.5 font-mono">{error}</p>
            </div>
          </div>
        )}

        {/* ── Results ───────────────────────────────────────────────────── */}
        {mode !== 'idle' && (
          <div ref={resultsRef} className="space-y-6">

            {/* ── Engine Comparison Panel (Compare mode only) ──────────── */}
            {mode === 'compared' && compareData && (
              <div className="bg-slate-900/50 rounded-2xl border border-slate-800/60 overflow-hidden">
                <div className="flex items-center gap-2 px-5 py-4 border-b border-slate-800/40">
                  <BarChart3 className="w-4 h-4 text-sky-400" />
                  <span className="text-sm font-semibold text-slate-200">Engine Comparison</span>
                  <span className="ml-auto text-xs text-slate-500">
                    {compareData.duplicates_removed} duplicates removed · Total time: {compareData.processing_time}
                  </span>
                </div>
                <div className="p-5 space-y-4">
                  {/* Summary row */}
                  <div className="grid grid-cols-4 gap-3">
                    {[
                      { label: 'Regex',    count: compareData.regex,    color: '#f59e0b' },
                      { label: 'Presidio', count: compareData.presidio, color: '#8b5cf6' },
                      { label: 'spaCy',    count: compareData.spacy,    color: '#38bdf8' },
                      { label: 'Merged',   count: compareData.merged,   color: '#2dd4bf' },
                    ].map(({ label, count, color }) => (
                      <div key={label} className="bg-slate-800/40 rounded-xl p-3 text-center border border-slate-700/40">
                        <p className="text-2xl font-black" style={{ color }}>{count}</p>
                        <p className="text-xs text-slate-400 font-semibold mt-0.5">{label}</p>
                      </div>
                    ))}
                  </div>

                  {/* Per-engine bars */}
                  <div className="space-y-3 mt-2">
                    {compareData.engine_stats?.map((es) => (
                      <EngineBar
                        key={es.engine}
                        label={es.engine}
                        count={es.entity_count}
                        maxCount={maxEngineCount}
                        color={es.engine === 'Regex' ? '#f59e0b' : es.engine === 'Presidio' ? '#8b5cf6' : '#38bdf8'}
                        timeMs={es.processing_time_ms}
                      />
                    ))}
                    <EngineBar
                      label="Merged (deduplicated)"
                      count={compareData.merged}
                      maxCount={maxEngineCount}
                      color="#2dd4bf"
                      timeMs={compareData.processing_time_ms}
                    />
                  </div>
                </div>
              </div>
            )}

            {/* ── Entity Table ─────────────────────────────────────────── */}
            <div className="bg-slate-900/50 rounded-2xl border border-slate-800/60 overflow-hidden">
              <div className="flex items-center justify-between px-5 py-4 border-b border-slate-800/40">
                <div className="flex items-center gap-2">
                  <ScanSearch className="w-4 h-4 text-violet-400" />
                  <span className="text-sm font-semibold text-slate-200">Detected Entities</span>
                  {entities.length > 0 && (
                    <span className="px-2 py-0.5 bg-violet-500/15 text-violet-400 text-xs font-bold rounded-full border border-violet-500/20">
                      {entities.length}
                    </span>
                  )}
                </div>
                <div className="flex items-center gap-3 text-xs text-slate-500">
                  <span className="flex items-center gap-1">
                    <span className="w-2 h-2 rounded-full bg-violet-500 inline-block" /> Presidio
                  </span>
                  <span className="flex items-center gap-1">
                    <span className="w-2 h-2 rounded-full bg-sky-500 inline-block" /> spaCy
                  </span>
                  <span className="flex items-center gap-1">
                    <span className="w-2 h-2 rounded-full bg-amber-500 inline-block" /> Regex
                  </span>
                </div>
              </div>
              <div className="p-5">
                <EntityTable entities={entities} loading={loading || comparing} />
              </div>
            </div>

            {/* ── Highlighted Original Text ─────────────────────────── */}
            <div className="bg-slate-900/50 rounded-2xl border border-slate-800/60 overflow-hidden">
              <div className="flex items-center gap-2 px-5 py-4 border-b border-slate-800/40">
                <Info className="w-4 h-4 text-blue-400" />
                <span className="text-sm font-semibold text-slate-200">Highlighted PHI Text</span>
                <span className="text-xs text-slate-500 ml-auto">Hover highlights to see type, source & confidence</span>
              </div>
              <div className="p-5 bg-slate-800/20 max-h-80 overflow-y-auto">
                <HighlightedTextAI text={inputText} entities={entities} />
              </div>
            </div>

            {/* ── Entity Statistics ─────────────────────────────────── */}
            {entities.length > 0 && (
              <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                {/* Type breakdown */}
                <div className="bg-slate-900/50 rounded-2xl border border-slate-800/60 p-5">
                  <h3 className="text-sm font-semibold text-slate-200 mb-4 flex items-center gap-2">
                    <Cpu className="w-4 h-4 text-violet-400" />
                    Entity Type Breakdown
                  </h3>
                  <div className="space-y-2.5">
                    {(() => {
                      const counts = entities.reduce((acc, e) => {
                        acc[e.type] = (acc[e.type] || 0) + 1;
                        return acc;
                      }, {});
                      const max = Math.max(...Object.values(counts));
                      return Object.entries(counts)
                        .sort((a, b) => b[1] - a[1])
                        .map(([type, count]) => {
                          const c = getEntityColor(type);
                          const pct = Math.round((count / max) * 100);
                          return (
                            <div key={type} className="flex items-center gap-3">
                              <span className="text-xs font-semibold text-slate-400 w-36 flex-shrink-0 truncate"
                                style={{ color: c.text }}>{type}</span>
                              <div className="flex-1 bg-slate-800 rounded-full h-2">
                                <div
                                  className="h-2 rounded-full transition-all duration-700"
                                  style={{ width: `${pct}%`, backgroundColor: c.border }}
                                />
                              </div>
                              <span className="text-xs text-slate-400 w-5 text-right tabular-nums">{count}</span>
                            </div>
                          );
                        });
                    })()}
                  </div>
                </div>

                {/* Source breakdown */}
                <div className="bg-slate-900/50 rounded-2xl border border-slate-800/60 p-5">
                  <h3 className="text-sm font-semibold text-slate-200 mb-4 flex items-center gap-2">
                    <ChevronRight className="w-4 h-4 text-sky-400" />
                    Detection Source Breakdown
                  </h3>
                  <div className="space-y-3">
                    {(() => {
                      const sourceCounts = entities.reduce((acc, e) => {
                        acc[e.source] = (acc[e.source] || 0) + 1;
                        return acc;
                      }, {});
                      const total = entities.length;
                      return Object.entries(sourceCounts).map(([source, count]) => {
                        const pct = Math.round((count / total) * 100);
                        const style = getSourceStyle(source);
                        return (
                          <div key={source} className="space-y-1">
                            <div className="flex items-center justify-between text-xs">
                              <span className={`font-semibold px-2 py-0.5 rounded-full border ${style.bg} ${style.text} ${style.border}`}>
                                {source}
                              </span>
                              <span className="text-slate-400">{count} ({pct}%)</span>
                            </div>
                            <div className="h-2 bg-slate-800 rounded-full overflow-hidden">
                              <div
                                className="h-full rounded-full"
                                style={{
                                  width: `${pct}%`,
                                  backgroundColor:
                                    source === 'Presidio' ? '#8b5cf6' :
                                    source === 'spaCy' ? '#38bdf8' :
                                    source === 'Regex' ? '#f59e0b' : '#2dd4bf',
                                }}
                              />
                            </div>
                          </div>
                        );
                      });
                    })()}
                  </div>
                </div>
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
};

export default AIDetection;
