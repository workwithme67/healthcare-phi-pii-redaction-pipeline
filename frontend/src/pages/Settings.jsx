import React, { useState } from 'react';
import { ToggleLeft, ToggleRight, Save, Settings as SettingsIcon, ShieldCheck } from 'lucide-react';

const Settings = () => {
  const [openaiEnabled, setOpenaiEnabled] = useState(false);
  const [presidioEnabled, setPresidioEnabled] = useState(true);
  const [maskType, setMaskType] = useState('REDACTED');
  const [saveSuccess, setSaveSuccess] = useState(false);

  const handleSave = (e) => {
    e.preventDefault();
    setSaveSuccess(true);
    setTimeout(() => setSaveSuccess(false), 3000);
  };

  return (
    <div className="space-y-8 max-w-3xl mx-auto">
      <div className="space-y-2">
        <h1 className="text-2xl font-bold tracking-tight text-slate-900">Pipeline Configurations</h1>
        <p className="text-slate-500 text-sm">
          Customize PHI matching thresholds, enable LLM sanitizers, and integrate future processors.
        </p>
      </div>

      {saveSuccess && (
        <div className="p-4 bg-emerald-50 border border-emerald-200 text-emerald-800 rounded-2xl text-sm font-semibold">
          Configuration parameters successfully saved to SQLite database.
        </div>
      )}

      <form onSubmit={handleSave} className="space-y-6">
        <div className="bg-white rounded-2xl border border-slate-200 shadow-sm divide-y divide-slate-100 overflow-hidden">
          {/* Presidio toggle */}
          <div className="p-6 flex items-start justify-between gap-4">
            <div className="space-y-1">
              <label className="text-sm font-bold text-slate-900 block">Microsoft Presidio Engine (Day 2)</label>
              <span className="text-xs text-slate-400 font-medium">Use local SpaCy &amp; Presidio microservices for high-efficiency clinical entity matching.</span>
            </div>
            <button
              type="button"
              onClick={() => setPresidioEnabled(!presidioEnabled)}
              className="text-slate-500 focus:outline-none"
            >
              {presidioEnabled ? (
                <ToggleRight className="w-12 h-7 text-teal-600" />
              ) : (
                <ToggleLeft className="w-12 h-7" />
              )}
            </button>
          </div>

          {/* OpenAI toggle */}
          <div className="p-6 flex items-start justify-between gap-4">
            <div className="space-y-1">
              <label className="text-sm font-bold text-slate-900 block">OpenAI / Ollama LLM Sanitization (Day 3)</label>
              <span className="text-xs text-slate-400 font-medium">Pass scrubbed data through custom system prompts to verify complete contextual redaction.</span>
            </div>
            <button
              type="button"
              onClick={() => setOpenaiEnabled(!openaiEnabled)}
              className="text-slate-500 focus:outline-none"
            >
              {openaiEnabled ? (
                <ToggleRight className="w-12 h-7 text-teal-600" />
              ) : (
                <ToggleLeft className="w-12 h-7" />
              )}
            </button>
          </div>

          {/* Mask Options */}
          <div className="p-6 space-y-3">
            <label className="text-sm font-bold text-slate-900 block">Redaction Mask Format</label>
            <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
              {[
                { value: 'REDACTED', label: '[REDACTED]' },
                { value: 'ENTITY', label: '[PATIENT_NAME]' },
                { value: 'HASH', label: '[Hashed-ID]' },
              ].map((opt) => (
                <button
                  type="button"
                  key={opt.value}
                  onClick={() => setMaskType(opt.value)}
                  className={`p-3.5 border rounded-xl text-xs font-bold text-center transition-all ${
                    maskType === opt.value
                      ? 'border-teal-500 bg-teal-50/30 text-teal-700 shadow-sm'
                      : 'border-slate-200 text-slate-600 hover:bg-slate-50'
                  }`}
                >
                  {opt.label}
                </button>
              ))}
            </div>
          </div>
        </div>

        {/* Action button */}
        <div className="flex items-center justify-between gap-4">
          <div className="flex items-center gap-2 text-xs font-semibold text-slate-500">
            <ShieldCheck className="w-4 h-4 text-emerald-500" />
            <span>Updates apply in real-time</span>
          </div>

          <button
            type="submit"
            className="flex items-center gap-2 px-6 py-3.5 bg-slate-900 hover:bg-slate-800 text-white font-semibold rounded-2xl transition-all shadow-lg text-sm"
          >
            <Save className="w-4 h-4" />
            <span>Save Settings</span>
          </button>
        </div>
      </form>
    </div>
  );
};

export default Settings;
