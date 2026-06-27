/**
 * Detection.jsx
 * Day 3 — Regex-Based PHI/PII Detection Page
 *
 * Features:
 *  - Paste clinical notes textarea
 *  - Detect / Redact / Clear / Copy buttons
 *  - Statistics strip (live from /api/statistics)
 *  - Detected entities table
 *  - Colour-coded highlighted text view
 *  - Redacted output panel
 */

import React, { useState, useEffect, useCallback, useRef } from 'react';
import {
  ScanSearch,
  ShieldOff,
  Eraser,
  Copy,
  CheckCheck,
  FileText,
  Zap,
  Database,
  Clock,
  AlertCircle,
  ChevronDown,
  ChevronUp,
  Info,
} from 'lucide-react';

import detectionService from '../services/detectionService';
import DetectionTable from '../components/DetectionTable';
import HighlightedText, { ColorLegend } from '../components/HighlightedText';
import StatisticsCard from '../components/StatisticsCard';

// ── Sample text for quick testing ─────────────────────────────────────────────
const SAMPLE_TEXT = `Patient: Ravi Kumar
MRN: MRN-REF-20240115
Patient ID: PID-A987654

Admission Date: 15/06/2024
Date of Birth: 03/04/1985

Contact Details:
  Phone: +91 98765 43210
  Email: ravi.kumar@healthmail.com
  Address: 45, MG Road, Bengaluru - 560001

Identity:
  Aadhaar: 2345 6789 0123
  PAN: ABCDE1234F
  Passport: B1234567

Insurance:
  Health Insurance No: HIN-POL-234567
  Policy No: POL987654

Payment:
  Credit Card: 4111 1111 1111 1111

System:
  Last accessed from IP: 192.168.1.105
  Patient portal: https://portal.healthtech.in/patient/12345

Diagnosis: Type 2 Diabetes Mellitus with hypertension.
Attending Physician: Dr. Priya Sharma
`;

// ── Helpers ───────────────────────────────────────────────────────────────────

const formatMs = (ms) => {
  if (ms == null) return '—';
  return ms < 1 ? '<1 ms' : `${ms.toFixed(1)} ms`;
};

// ── Main Page Component ───────────────────────────────────────────────────────

const Detection = () => {
  // Input
  const [inputText, setInputText] = useState('');

  // Results
  const [entities, setEntities] = useState([]);
  const [redactedText, setRedactedText] = useState('');
  const [processingTime, setProcessingTime] = useState(null);

  // UI state
  const [loading, setLoading] = useState(false);
  const [redactLoading, setRedactLoading] = useState(false);
  const [error, setError] = useState('');
  const [mode, setMode] = useState('idle'); // 'idle' | 'detected' | 'redacted'
  const [copied, setCopied] = useState(false);
  const [statsOpen, setStatsOpen] = useState(true);

  // Statistics
  const [stats, setStats] = useState(null);
  const [statsLoading, setStatsLoading] = useState(false);

  const resultsRef = useRef(null);

  // ── Load Statistics ─────────────────────────────────────────────────────────
  const loadStats = useCallback(async () => {
    setStatsLoading(true);
    try {
      const data = await detectionService.getStatistics();
      setStats(data);
    } catch {
      // Stats are non-critical; fail silently
    } finally {
      setStatsLoading(false);
    }
  }, []);

  useEffect(() => {
    loadStats();
  }, [loadStats]);

  // ── Detect ──────────────────────────────────────────────────────────────────
  const handleDetect = async () => {
    if (!inputText.trim()) {
      setError('Please enter some clinical text to analyze.');
      return;
    }
    setError('');
    setLoading(true);
    setMode('idle');
    setEntities([]);
    setRedactedText('');

    try {
      const data = await detectionService.detect(inputText);
      setEntities(data.entities || []);
      setProcessingTime(data.processing_time_ms);
      setMode('detected');
      await loadStats();
      // Scroll to results
      setTimeout(() => resultsRef.current?.scrollIntoView({ behavior: 'smooth', block: 'start' }), 100);
    } catch (err) {
      setError(err.response?.data?.detail || err.message || 'Detection failed. Is the backend running?');
    } finally {
      setLoading(false);
    }
  };

  // ── Redact ──────────────────────────────────────────────────────────────────
  const handleRedact = async () => {
    if (!inputText.trim()) {
      setError('Please enter some clinical text to redact.');
      return;
    }
    setError('');
    setRedactLoading(true);

    try {
      const data = await detectionService.redact(inputText);
      setEntities(data.entities || []);
      setRedactedText(data.redacted_text || '');
      setProcessingTime(data.processing_time_ms);
      setMode('redacted');
      await loadStats();
      setTimeout(() => resultsRef.current?.scrollIntoView({ behavior: 'smooth', block: 'start' }), 100);
    } catch (err) {
      setError(err.response?.data?.detail || err.message || 'Redaction failed. Is the backend running?');
    } finally {
      setRedactLoading(false);
    }
  };

  // ── Clear ───────────────────────────────────────────────────────────────────
  const handleClear = () => {
    setInputText('');
    setEntities([]);
    setRedactedText('');
    setProcessingTime(null);
    setMode('idle');
    setError('');
  };

  // ── Copy ────────────────────────────────────────────────────────────────────
  const handleCopy = async () => {
    const textToCopy = mode === 'redacted' ? redactedText : inputText;
    try {
      await navigator.clipboard.writeText(textToCopy);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    } catch {
      setError('Failed to copy to clipboard.');
    }
  };

  // ── Load Sample ─────────────────────────────────────────────────────────────
  const loadSample = () => {
    setInputText(SAMPLE_TEXT);
    setMode('idle');
    setEntities([]);
    setRedactedText('');
    setError('');
  };

  // ── Active entity types ─────────────────────────────────────────────────────
  const activeTypes = [...new Set(entities.map(e => e.type))];

  // ── Render ──────────────────────────────────────────────────────────────────
  return (
    <div className="min-h-screen bg-slate-950 text-white">
      {/* ── Page Header ──────────────────────────────────────────────────────── */}
      <div className="bg-gradient-to-br from-slate-900 via-slate-900 to-slate-950 border-b border-slate-800/60 px-6 py-8">
        <div className="max-w-7xl mx-auto">
          <div className="flex items-center gap-3 mb-2">
            <div className="p-2.5 bg-teal-500/10 rounded-xl ring-1 ring-teal-500/20">
              <ScanSearch className="w-6 h-6 text-teal-400" />
            </div>
            <div>
              <h1 className="text-2xl font-bold text-white tracking-tight">
                PHI/PII Detection Engine
              </h1>
              <p className="text-sm text-slate-400 mt-0.5">
                Regex-powered detection &amp; redaction of sensitive health information
              </p>
            </div>
          </div>

          {/* Entity type legend */}
          {activeTypes.length > 0 && (
            <div className="mt-4 p-3 bg-slate-800/40 rounded-xl border border-slate-700/40">
              <p className="text-xs text-slate-400 mb-2 font-semibold uppercase tracking-wider">
                Detected types in this run
              </p>
              <ColorLegend activeTypes={activeTypes} />
            </div>
          )}
        </div>
      </div>

      <div className="max-w-7xl mx-auto px-6 py-6 space-y-6">

        {/* ── Statistics Strip ──────────────────────────────────────────────── */}
        <div className="bg-slate-900/50 rounded-2xl border border-slate-800/60 overflow-hidden">
          <button
            className="w-full flex items-center justify-between px-5 py-3.5 hover:bg-slate-800/30 transition-colors"
            onClick={() => setStatsOpen(o => !o)}
          >
            <div className="flex items-center gap-2">
              <Database className="w-4 h-4 text-teal-400" />
              <span className="text-sm font-semibold text-slate-200">Detection Statistics</span>
              {statsLoading && (
                <div className="w-3 h-3 border border-teal-500 border-t-transparent rounded-full animate-spin" />
              )}
            </div>
            {statsOpen ? <ChevronUp className="w-4 h-4 text-slate-400" /> : <ChevronDown className="w-4 h-4 text-slate-400" />}
          </button>

          {statsOpen && (
            <div className="p-5 pt-0 grid grid-cols-2 lg:grid-cols-4 gap-4">
              <StatisticsCard
                title="Notes Processed"
                value={stats?.total_notes_processed ?? '—'}
                subtitle="Total detect + redact calls"
                icon={FileText}
                color="teal"
              />
              <StatisticsCard
                title="Entities Found"
                value={stats?.total_entities_found ?? '—'}
                subtitle="Across all processed notes"
                icon={ScanSearch}
                color="blue"
              />
              <StatisticsCard
                title="Avg. Detection Time"
                value={stats?.average_detection_time_ms != null ? formatMs(stats.average_detection_time_ms) : '—'}
                subtitle="Per request"
                icon={Clock}
                color="amber"
              />
              <StatisticsCard
                title="Most Common Type"
                value={stats?.entity_counts_by_type?.[0]?.type ?? '—'}
                subtitle={stats?.entity_counts_by_type?.[0] ? `${stats.entity_counts_by_type[0].count} occurrences` : 'No data yet'}
                icon={Zap}
                color="purple"
              />
            </div>
          )}
        </div>

        {/* ── Input Panel ───────────────────────────────────────────────────── */}
        <div className="bg-slate-900/50 rounded-2xl border border-slate-800/60 overflow-hidden">
          {/* Panel header */}
          <div className="flex items-center justify-between px-5 py-4 border-b border-slate-800/40">
            <div className="flex items-center gap-2">
              <FileText className="w-4 h-4 text-slate-400" />
              <span className="text-sm font-semibold text-slate-200">Clinical Notes Input</span>
            </div>
            <button
              onClick={loadSample}
              className="text-xs text-teal-400 hover:text-teal-300 font-medium px-2 py-1 rounded-lg hover:bg-teal-500/10 transition-colors"
            >
              Load sample →
            </button>
          </div>

          {/* Textarea */}
          <div className="p-5">
            <textarea
              id="clinical-text-input"
              value={inputText}
              onChange={e => { setInputText(e.target.value); setMode('idle'); }}
              placeholder="Paste clinical notes here…&#10;&#10;Example: Patient Ravi Kumar, Phone: 9876543210, Email: ravi@example.com, Aadhaar: 2345 6789 0123"
              rows={10}
              className="w-full bg-slate-800/50 border border-slate-700/60 rounded-xl px-4 py-3 text-sm font-mono text-slate-200 placeholder-slate-600 resize-y focus:outline-none focus:ring-2 focus:ring-teal-500/50 focus:border-teal-500/50 transition-all duration-200 min-h-[160px]"
            />

            {/* Character count */}
            <div className="flex items-center justify-between mt-2">
              <span className="text-xs text-slate-500">
                {inputText.length.toLocaleString()} characters
                {entities.length > 0 && (
                  <span className="ml-2 text-teal-400">
                    · {entities.length} {entities.length === 1 ? 'entity' : 'entities'} detected
                  </span>
                )}
              </span>
              {processingTime != null && (
                <span className="text-xs text-slate-500 flex items-center gap-1">
                  <Clock className="w-3 h-3" />
                  Processed in {formatMs(processingTime)}
                </span>
              )}
            </div>
          </div>

          {/* Action buttons */}
          <div className="px-5 pb-5 flex flex-wrap gap-3">
            <button
              id="detect-btn"
              onClick={handleDetect}
              disabled={loading || redactLoading}
              className="flex items-center gap-2 px-5 py-2.5 bg-teal-600 hover:bg-teal-500 disabled:bg-teal-800/50 disabled:cursor-not-allowed text-white text-sm font-semibold rounded-xl transition-all duration-200 shadow-lg shadow-teal-600/20"
            >
              {loading ? (
                <div className="w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin" />
              ) : (
                <ScanSearch className="w-4 h-4" />
              )}
              {loading ? 'Detecting…' : 'Detect'}
            </button>

            <button
              id="redact-btn"
              onClick={handleRedact}
              disabled={loading || redactLoading}
              className="flex items-center gap-2 px-5 py-2.5 bg-rose-600 hover:bg-rose-500 disabled:bg-rose-800/50 disabled:cursor-not-allowed text-white text-sm font-semibold rounded-xl transition-all duration-200 shadow-lg shadow-rose-600/20"
            >
              {redactLoading ? (
                <div className="w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin" />
              ) : (
                <ShieldOff className="w-4 h-4" />
              )}
              {redactLoading ? 'Redacting…' : 'Redact'}
            </button>

            <button
              id="copy-btn"
              onClick={handleCopy}
              disabled={!inputText && !redactedText}
              className="flex items-center gap-2 px-5 py-2.5 bg-slate-700 hover:bg-slate-600 disabled:bg-slate-800/40 disabled:cursor-not-allowed text-white text-sm font-semibold rounded-xl transition-all duration-200"
            >
              {copied ? <CheckCheck className="w-4 h-4 text-emerald-400" /> : <Copy className="w-4 h-4" />}
              {copied ? 'Copied!' : (mode === 'redacted' ? 'Copy Redacted' : 'Copy')}
            </button>

            <button
              id="clear-btn"
              onClick={handleClear}
              className="flex items-center gap-2 px-5 py-2.5 bg-slate-800 hover:bg-slate-700 text-slate-300 hover:text-white text-sm font-semibold rounded-xl transition-all duration-200 border border-slate-700/60"
            >
              <Eraser className="w-4 h-4" />
              Clear
            </button>
          </div>
        </div>

        {/* ── Error Banner ─────────────────────────────────────────────────── */}
        {error && (
          <div className="flex items-start gap-3 p-4 bg-rose-500/10 border border-rose-500/30 rounded-xl">
            <AlertCircle className="w-5 h-5 text-rose-400 flex-shrink-0 mt-0.5" />
            <div>
              <p className="text-sm font-semibold text-rose-300">Error</p>
              <p className="text-sm text-rose-400/80 mt-0.5">{error}</p>
            </div>
          </div>
        )}

        {/* ── Results Section ───────────────────────────────────────────────── */}
        {mode !== 'idle' && (
          <div ref={resultsRef} className="space-y-6">

            {/* Detected Entities Table */}
            <div className="bg-slate-900/50 rounded-2xl border border-slate-800/60 overflow-hidden">
              <div className="flex items-center justify-between px-5 py-4 border-b border-slate-800/40">
                <div className="flex items-center gap-2">
                  <ScanSearch className="w-4 h-4 text-teal-400" />
                  <span className="text-sm font-semibold text-slate-200">
                    Detected Entities
                  </span>
                  {entities.length > 0 && (
                    <span className="px-2 py-0.5 bg-teal-500/15 text-teal-400 text-xs font-bold rounded-full border border-teal-500/20">
                      {entities.length}
                    </span>
                  )}
                </div>
                {processingTime != null && (
                  <span className="text-xs text-slate-500 flex items-center gap-1">
                    <Zap className="w-3 h-3 text-amber-400" />
                    {formatMs(processingTime)}
                  </span>
                )}
              </div>
              <div className="p-5">
                <DetectionTable entities={entities} loading={loading || redactLoading} />
              </div>
            </div>

            {/* Highlighted Text */}
            <div className="bg-slate-900/50 rounded-2xl border border-slate-800/60 overflow-hidden">
              <div className="flex items-center gap-2 px-5 py-4 border-b border-slate-800/40">
                <Info className="w-4 h-4 text-blue-400" />
                <span className="text-sm font-semibold text-slate-200">
                  Highlighted Original Text
                </span>
                <span className="text-xs text-slate-500 ml-auto">
                  Hover over highlights to see entity type
                </span>
              </div>
              <div className="p-5 bg-slate-800/20 max-h-72 overflow-y-auto rounded-b-2xl">
                <HighlightedText text={inputText} entities={entities} />
              </div>
            </div>

            {/* Redacted Output */}
            {mode === 'redacted' && redactedText && (
              <div className="bg-slate-900/50 rounded-2xl border border-rose-500/20 overflow-hidden">
                <div className="flex items-center justify-between px-5 py-4 border-b border-rose-500/20 bg-rose-500/5">
                  <div className="flex items-center gap-2">
                    <ShieldOff className="w-4 h-4 text-rose-400" />
                    <span className="text-sm font-semibold text-slate-200">
                      Redacted Output
                    </span>
                    <span className="px-2 py-0.5 bg-rose-500/15 text-rose-400 text-xs font-bold rounded-full border border-rose-500/20">
                      PHI Removed
                    </span>
                  </div>
                  <button
                    onClick={handleCopy}
                    className="flex items-center gap-1.5 text-xs text-rose-300 hover:text-rose-200 px-2 py-1 rounded-lg hover:bg-rose-500/10 transition-colors font-medium"
                  >
                    {copied ? <CheckCheck className="w-3.5 h-3.5" /> : <Copy className="w-3.5 h-3.5" />}
                    {copied ? 'Copied!' : 'Copy'}
                  </button>
                </div>
                <div className="p-5 bg-slate-800/20 max-h-72 overflow-y-auto">
                  <pre className="whitespace-pre-wrap text-sm font-mono text-slate-300 leading-relaxed">
                    {redactedText}
                  </pre>
                </div>
              </div>
            )}

            {/* Entity Type Breakdown (mini chart) */}
            {entities.length > 0 && (
              <div className="bg-slate-900/50 rounded-2xl border border-slate-800/60 p-5">
                <h3 className="text-sm font-semibold text-slate-200 mb-4">Entity Type Breakdown</h3>
                <div className="space-y-2">
                  {(() => {
                    const counts = entities.reduce((acc, e) => {
                      acc[e.type] = (acc[e.type] || 0) + 1;
                      return acc;
                    }, {});
                    const max = Math.max(...Object.values(counts));
                    return Object.entries(counts)
                      .sort((a, b) => b[1] - a[1])
                      .map(([type, count]) => {
                        const pct = Math.round((count / max) * 100);
                        return (
                          <div key={type} className="flex items-center gap-3">
                            <span className="text-xs font-semibold text-slate-400 w-28 flex-shrink-0 truncate">
                              {type}
                            </span>
                            <div className="flex-1 bg-slate-800 rounded-full h-2">
                              <div
                                className="h-2 rounded-full bg-teal-500 transition-all duration-700"
                                style={{ width: `${pct}%` }}
                              />
                            </div>
                            <span className="text-xs text-slate-400 w-6 text-right tabular-nums">
                              {count}
                            </span>
                          </div>
                        );
                      });
                  })()}
                </div>
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
};

export default Detection;
