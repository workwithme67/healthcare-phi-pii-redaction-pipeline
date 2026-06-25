import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { FileUp, Clipboard, ShieldCheck, Loader2 } from 'lucide-react';
import { redactionService } from '../services/api';

const Upload = () => {
  const [text, setText] = useState('');
  const [filename, setFilename] = useState('');
  const [dragActive, setDragActive] = useState(false);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState(null);
  const navigate = useNavigate();

  const handleDrag = (e) => {
    e.preventDefault();
    e.stopPropagation();
    if (e.type === "dragenter" || e.type === "dragover") {
      setDragActive(true);
    } else if (e.type === "dragleave") {
      setDragActive(false);
    }
  };

  const handleDrop = (e) => {
    e.preventDefault();
    e.stopPropagation();
    setDragActive(false);
    
    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      const file = e.dataTransfer.files[0];
      const reader = new FileReader();
      reader.onload = (event) => {
        setText(event.target.result);
        setFilename(file.name);
      };
      reader.readAsText(file);
    }
  };

  const handleFileInput = (e) => {
    if (e.target.files && e.target.files[0]) {
      const file = e.target.files[0];
      const reader = new FileReader();
      reader.onload = (event) => {
        setText(event.target.result);
        setFilename(file.name);
      };
      reader.readAsText(file);
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!text.trim()) return;

    setSubmitting(true);
    setError(null);

    try {
      await redactionService.submitJob(text, filename || 'web_upload.txt');
      navigate('/');
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to submit redaction job.');
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className="space-y-8 max-w-4xl mx-auto">
      <div className="space-y-2">
        <h1 className="text-2xl font-bold tracking-tight text-slate-900">Upload Clinical Note</h1>
        <p className="text-slate-500 text-sm">
          Submit clinical text raw or upload a text file. The pipeline will securely queue it.
        </p>
      </div>

      {error && (
        <div className="p-4 bg-rose-50 border border-rose-200 text-rose-800 rounded-2xl text-sm">
          {error}
        </div>
      )}

      <form onSubmit={handleSubmit} className="space-y-6">
        {/* Upload Drag & Drop Zone */}
        <div 
          onDragEnter={handleDrag}
          onDragOver={handleDrag}
          onDragLeave={handleDrag}
          onDrop={handleDrop}
          className={`border-2 border-dashed rounded-2xl p-8 text-center transition-all duration-200 ${
            dragActive ? 'border-teal-500 bg-teal-50/20' : 'border-slate-300 hover:border-slate-400 bg-white'
          }`}
        >
          <input 
            type="file" 
            id="file-upload" 
            className="hidden" 
            accept=".txt,.md"
            onChange={handleFileInput}
          />
          <label htmlFor="file-upload" className="cursor-pointer space-y-4 block">
            <div className="inline-flex p-3.5 bg-slate-50 text-slate-500 rounded-xl border border-slate-100 shadow-sm mx-auto">
              <FileUp className="w-6 h-6" />
            </div>
            <div className="space-y-1">
              <p className="text-sm font-semibold text-slate-700">
                {filename ? `Selected: ${filename}` : 'Drag and drop your clinical note here'}
              </p>
              <p className="text-xs text-slate-400 font-medium">
                Or click to browse from your computer (.txt, .md only)
              </p>
            </div>
          </label>
        </div>

        {/* Text Area */}
        <div className="bg-white rounded-2xl border border-slate-200 shadow-sm overflow-hidden">
          <div className="px-5 py-4 border-b border-slate-200 flex items-center justify-between bg-slate-50">
            <div className="flex items-center gap-2 text-slate-600">
              <Clipboard className="w-4 h-4" />
              <span className="text-xs font-semibold uppercase tracking-wider">Clinical Text Editor</span>
            </div>
            {filename && (
              <button 
                type="button"
                onClick={() => { setText(''); setFilename(''); }}
                className="text-xs font-semibold text-rose-600 hover:text-rose-700"
              >
                Clear
              </button>
            )}
          </div>
          <textarea
            value={text}
            onChange={(e) => setText(e.target.value)}
            placeholder="Paste raw clinical transcription, physician notes, or patient history here..."
            className="w-full h-80 px-6 py-5 focus:outline-none resize-none text-slate-800 text-sm font-mono leading-relaxed"
            required
          />
        </div>

        {/* Action button */}
        <div className="flex items-center justify-between gap-4">
          <div className="flex items-center gap-2 text-xs font-semibold text-slate-500">
            <ShieldCheck className="w-4 h-4 text-emerald-500" />
            <span>Encrypted in transit & at rest</span>
          </div>

          <button
            type="submit"
            disabled={submitting || !text.trim()}
            className="flex items-center gap-2 px-6 py-3.5 bg-teal-600 hover:bg-teal-500 disabled:bg-slate-200 text-white disabled:text-slate-400 font-semibold rounded-2xl transition-all shadow-lg shadow-teal-600/10 text-sm"
          >
            {submitting ? (
              <>
                <Loader2 className="w-4 h-4 animate-spin" />
                <span>Queuing...</span>
              </>
            ) : (
              <span>Submit Redaction Job</span>
            )}
          </button>
        </div>
      </form>
    </div>
  );
};

export default Upload;
