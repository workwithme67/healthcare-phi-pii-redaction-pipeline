import React, { useState, useRef } from 'react';
import { FileUp, Clipboard, Trash2, Send, Loader2, CheckCircle2, AlertTriangle, FileText } from 'lucide-react';
import { uploadService } from '../services/uploadService';

const MAX_TEXT_CHARS = 100000;
const MAX_FILE_SIZE = 10 * 1024 * 1024; // 10MB

const UploadForm = ({ onUploadSuccess }) => {
  const [text, setText] = useState('');
  const [file, setFile] = useState(null);
  const [dragActive, setDragActive] = useState(false);
  const [uploading, setUploading] = useState(false);
  const [progress, setProgress] = useState(0);
  const [successMsg, setSuccessMsg] = useState(null);
  const [errorMsg, setErrorMsg] = useState(null);
  const fileInputRef = useRef(null);

  const handleDrag = (e) => {
    e.preventDefault();
    e.stopPropagation();
    if (e.type === "dragenter" || e.type === "dragover") {
      setDragActive(true);
    } else if (e.type === "dragleave") {
      setDragActive(false);
    }
  };

  const validateAndSetFile = (selectedFile) => {
    setErrorMsg(null);
    setSuccessMsg(null);
    
    if (!selectedFile) return;

    // Validate type
    const ext = selectedFile.name.substring(selectedFile.name.lastIndexOf('.')).toLowerCase();
    if (ext !== '.txt' && ext !== '.pdf') {
      setErrorMsg("Unsupported file type. Only TXT and PDF files are permitted.");
      return;
    }

    // Validate size
    if (selectedFile.size > MAX_FILE_SIZE) {
      setErrorMsg("File size exceeds the 10MB limit.");
      return;
    }

    setFile(selectedFile);
    setText(''); // Clear text when a file is selected
  };

  const handleDrop = (e) => {
    e.preventDefault();
    e.stopPropagation();
    setDragActive(false);
    
    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      validateAndSetFile(e.dataTransfer.files[0]);
    }
  };

  const handleFileInput = (e) => {
    if (e.target.files && e.target.files[0]) {
      validateAndSetFile(e.target.files[0]);
    }
  };

  const handleTextChange = (e) => {
    const val = e.target.value;
    if (val.length <= MAX_TEXT_CHARS) {
      setText(val);
      if (file) setFile(null); // Clear file if user types
      setErrorMsg(null);
      setSuccessMsg(null);
    }
  };

  const handleClear = () => {
    setText('');
    setFile(null);
    setErrorMsg(null);
    setSuccessMsg(null);
    setProgress(0);
    if (fileInputRef.current) fileInputRef.current.value = '';
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setErrorMsg(null);
    setSuccessMsg(null);

    // 1. Validation
    if (!file && !text.trim()) {
      setErrorMsg("Please enter a clinical note or select a TXT/PDF file to upload.");
      return;
    }

    setUploading(true);
    setProgress(0);

    try {
      if (file) {
        // Handle file upload
        const response = await uploadService.uploadFile(file, (progressEvent) => {
          const percentCompleted = Math.round((progressEvent.loaded * 100) / progressEvent.total);
          setProgress(percentCompleted);
        });
        setSuccessMsg(`File "${response.filename}" uploaded successfully!`);
        handleClear();
      } else {
        // Handle raw text upload
        const response = await uploadService.uploadText(text);
        setSuccessMsg(response.message || "Clinical note uploaded successfully!");
        handleClear();
      }

      // Notify parent component to refresh history/stats
      if (onUploadSuccess) {
        onUploadSuccess();
      }
    } catch (err) {
      console.error("Upload failed:", err);
      setErrorMsg(err.response?.data?.detail || "An unexpected error occurred during upload. Please try again.");
    } finally {
      setUploading(false);
    }
  };

  const charCount = text.length;
  const isNearLimit = charCount > MAX_TEXT_CHARS * 0.9;

  return (
    <div className="bg-white rounded-3xl border border-slate-200 p-6 md:p-8 shadow-sm space-y-6">
      <div className="space-y-1">
        <h2 className="text-xl font-bold text-slate-900 tracking-tight">Upload Center</h2>
        <p className="text-slate-500 text-sm">
          Submit clinical documents as raw text or upload TXT/PDF files. Protected health information will be stored securely.
        </p>
      </div>

      {/* Success Banner */}
      {successMsg && (
        <div className="flex items-start gap-3 p-4 bg-emerald-50 border border-emerald-200/80 text-emerald-800 rounded-2xl text-sm animate-fade-in">
          <CheckCircle2 className="w-5 h-5 text-emerald-600 flex-shrink-0 mt-0.5" />
          <div>
            <span className="font-semibold">Success:</span> {successMsg}
          </div>
        </div>
      )}

      {/* Error Banner */}
      {errorMsg && (
        <div className="flex items-start gap-3 p-4 bg-rose-50 border border-rose-200/80 text-rose-800 rounded-2xl text-sm animate-fade-in">
          <AlertTriangle className="w-5 h-5 text-rose-600 flex-shrink-0 mt-0.5" />
          <div>
            <span className="font-semibold">Error:</span> {errorMsg}
          </div>
        </div>
      )}

      <form onSubmit={handleSubmit} className="space-y-6">
        {/* Drag & Drop File Upload Area */}
        <div
          onDragEnter={handleDrag}
          onDragOver={handleDrag}
          onDragLeave={handleDrag}
          onDrop={handleDrop}
          className={`border-2 border-dashed rounded-2xl p-6 text-center transition-all duration-300 relative ${
            dragActive
              ? 'border-teal-500 bg-teal-50/30 shadow-inner scale-[0.99]'
              : 'border-slate-200 hover:border-slate-300 bg-slate-50/40 hover:bg-slate-50/80'
          }`}
        >
          <input
            type="file"
            id="file-upload"
            ref={fileInputRef}
            className="hidden"
            accept=".txt,.pdf"
            onChange={handleFileInput}
            disabled={uploading}
          />
          
          <label htmlFor="file-upload" className="cursor-pointer space-y-3 block">
            <div className="inline-flex p-3.5 bg-white text-slate-500 rounded-2xl border border-slate-150 shadow-sm mx-auto transition-transform duration-200 hover:scale-105">
              <FileUp className="w-6 h-6 text-teal-600" />
            </div>
            <div className="space-y-1">
              <p className="text-sm font-bold text-slate-700">
                {file ? `File selected: ${file.name}` : 'Drag & drop clinical file here'}
              </p>
              <p className="text-xs text-slate-400 font-semibold">
                {file ? `Size: ${(file.size / 1024).toFixed(1)} KB` : 'Or browse from computer (.txt, .pdf up to 10MB)'}
              </p>
            </div>
          </label>
        </div>

        {/* OR Divider */}
        <div className="relative flex py-2 items-center">
          <div className="flex-grow border-t border-slate-200"></div>
          <span className="flex-shrink mx-4 text-xs font-bold text-slate-400 uppercase tracking-widest bg-white px-2">OR</span>
          <div className="flex-grow border-t border-slate-200"></div>
        </div>

        {/* Text Area for raw clinical note */}
        <div className="bg-white rounded-2xl border border-slate-200 shadow-sm overflow-hidden focus-within:border-teal-500 focus-within:ring-1 focus-within:ring-teal-500 transition-all duration-200">
          <div className="px-5 py-3.5 border-b border-slate-100 flex items-center justify-between bg-slate-50/80">
            <div className="flex items-center gap-2 text-slate-600">
              <Clipboard className="w-4 h-4 text-teal-600" />
              <span className="text-xs font-bold uppercase tracking-wider text-slate-600">Raw Clinical Text Editor</span>
            </div>
            {(text || file) && (
              <button
                type="button"
                onClick={handleClear}
                disabled={uploading}
                className="text-xs font-bold text-rose-600 hover:text-rose-700 flex items-center gap-1 transition-colors px-2 py-1 rounded-lg hover:bg-rose-50"
              >
                <Trash2 className="w-3.5 h-3.5" />
                <span>Clear</span>
              </button>
            )}
          </div>
          <textarea
            value={text}
            onChange={handleTextChange}
            disabled={uploading}
            placeholder="Paste raw clinical transcription, physician notes, or patient history here..."
            className="w-full h-64 px-5 py-4 focus:outline-none resize-none text-slate-800 text-sm font-mono leading-relaxed"
          />
          {/* Character Counter footer */}
          <div className="px-5 py-2.5 bg-slate-50/50 border-t border-slate-100 flex justify-end">
            <span className={`text-[11px] font-bold tracking-wider ${isNearLimit ? 'text-rose-600' : 'text-slate-400'}`}>
              {charCount.toLocaleString()} / {MAX_TEXT_CHARS.toLocaleString()} characters
            </span>
          </div>
        </div>

        {/* Active Uploading Progress Bar */}
        {uploading && file && (
          <div className="space-y-2 animate-pulse">
            <div className="flex justify-between text-xs font-bold text-slate-600">
              <span>Uploading "{file.name}"...</span>
              <span>{progress}%</span>
            </div>
            <div className="w-full bg-slate-100 h-2.5 rounded-full overflow-hidden border border-slate-150">
              <div
                className="bg-teal-500 h-full rounded-full transition-all duration-300 ease-out"
                style={{ width: `${progress}%` }}
              ></div>
            </div>
          </div>
        )}

        {/* Form Actions */}
        <div className="flex items-center justify-between gap-4 pt-2">
          <div className="text-[11px] font-semibold text-slate-400 max-w-[200px] leading-snug">
            All uploads are encrypted and isolated in compliance with security guidelines.
          </div>

          <div className="flex items-center gap-3">
            {(text || file) && (
              <button
                type="button"
                onClick={handleClear}
                disabled={uploading}
                className="px-5 py-3 text-slate-600 hover:text-slate-800 hover:bg-slate-100 font-bold rounded-2xl transition-all text-sm"
              >
                Cancel
              </button>
            )}

            <button
              type="submit"
              disabled={uploading || (!file && !text.trim())}
              className="flex items-center gap-2 px-6 py-3.5 bg-teal-600 hover:bg-teal-500 disabled:bg-slate-100 text-white disabled:text-slate-400 font-bold rounded-2xl transition-all shadow-lg shadow-teal-600/10 hover:shadow-teal-500/20 disabled:shadow-none text-sm"
            >
              {uploading ? (
                <>
                  <Loader2 className="w-4 h-4 animate-spin" />
                  <span>Uploading...</span>
                </>
              ) : (
                <>
                  <Send className="w-4 h-4" />
                  <span>Upload Clinical Note</span>
                </>
              )}
            </button>
          </div>
        </div>
      </form>
    </div>
  );
};

export default UploadForm;
