import React, { useState } from 'react';
import { Eye, Trash2, Calendar, FileText, ShieldAlert, X, Loader2 } from 'lucide-react';
import { uploadService } from '../services/uploadService';

const UploadHistory = ({ uploads, loading, onDeleteSuccess }) => {
  const [previewItem, setPreviewItem] = useState(null);
  const [previewContent, setPreviewContent] = useState('');
  const [loadingPreview, setLoadingPreview] = useState(false);
  const [deleteConfirmId, setDeleteConfirmId] = useState(null);
  const [deletingId, setDeletingId] = useState(null);

  const handlePreview = async (item) => {
    setPreviewItem(item);
    setLoadingPreview(true);
    setPreviewContent('');
    try {
      const details = await uploadService.getUploadDetails(item.id);
      setPreviewContent(details.note_text || '');
    } catch (err) {
      console.error("Failed to fetch upload details:", err);
      setPreviewContent("Error: Could not load clinical note content.");
    } finally {
      setLoadingPreview(false);
    }
  };

  const handleDelete = async (id) => {
    setDeletingId(id);
    try {
      await uploadService.deleteUpload(id);
      setDeleteConfirmId(null);
      if (onDeleteSuccess) {
        onDeleteSuccess();
      }
    } catch (err) {
      console.error("Failed to delete upload:", err);
      alert("Failed to delete the clinical note. Please try again.");
    } finally {
      setDeletingId(null);
    }
  };

  const getFileIconColor = (type) => {
    switch (type) {
      case 'PDF': return 'text-rose-600 bg-rose-50 border-rose-100';
      case 'TXT': return 'text-blue-600 bg-blue-50 border-blue-100';
      default: return 'text-teal-600 bg-teal-50 border-teal-100';
    }
  };

  return (
    <div className="bg-white rounded-3xl border border-slate-200 shadow-sm overflow-hidden flex flex-col">
      <div className="px-6 py-5 border-b border-slate-100 flex items-center justify-between">
        <div className="space-y-1">
          <h3 className="font-bold text-slate-900">Recent Uploads</h3>
          <p className="text-xs text-slate-400 font-medium">History of uploaded notes and documents</p>
        </div>
      </div>

      <div className="overflow-x-auto">
        {loading ? (
          <div className="p-12 space-y-4">
            {[1, 2, 3].map((i) => (
              <div key={i} className="h-14 bg-slate-50 animate-pulse rounded-2xl border border-slate-100" />
            ))}
          </div>
        ) : uploads.length === 0 ? (
          <div className="p-16 text-center space-y-3">
            <div className="p-4 bg-slate-50 border border-slate-100 text-slate-400 rounded-full w-fit mx-auto">
              <FileText className="w-8 h-8 text-slate-300" />
            </div>
            <p className="text-slate-400 text-sm font-semibold">No recent uploads found.</p>
            <p className="text-xs text-slate-400 max-w-[280px] mx-auto leading-relaxed">
              Use the upload form above to submit clinical text transcriptions or documents.
            </p>
          </div>
        ) : (
          <table className="w-full text-left border-collapse">
            <thead>
              <tr className="bg-slate-50/70 border-b border-slate-100 text-[10px] font-bold text-slate-500 uppercase tracking-widest">
                <th className="px-6 py-4">Document / File Name</th>
                <th className="px-6 py-4">Type</th>
                <th className="px-6 py-4">Upload Time</th>
                <th className="px-6 py-4">Status</th>
                <th className="px-6 py-4 text-right">Actions</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100 text-sm">
              {uploads.map((item) => (
                <tr key={item.id} className="hover:bg-slate-50/40 transition-colors group">
                  <td className="px-6 py-4.5">
                    <div className="flex items-center gap-3">
                      <div className={`p-2 rounded-xl border ${getFileIconColor(item.file_type)} flex-shrink-0`}>
                        <FileText className="w-4 h-4" />
                      </div>
                      <div className="min-w-0">
                        <span className="font-bold text-slate-900 block truncate max-w-[240px]">
                          {item.filename || 'Direct Note Upload'}
                        </span>
                        <span className="text-[10px] font-mono text-slate-400 block mt-0.5">
                          {item.id}
                        </span>
                      </div>
                    </div>
                  </td>
                  <td className="px-6 py-4.5">
                    <span className={`inline-flex items-center px-2 py-0.5 rounded-md text-[10px] font-extrabold tracking-wider border uppercase ${
                      item.file_type === 'PDF' 
                        ? 'bg-rose-50 text-rose-700 border-rose-200' 
                        : item.file_type === 'TXT' 
                        ? 'bg-blue-50 text-blue-700 border-blue-200' 
                        : 'bg-teal-50 text-teal-700 border-teal-200'
                    }`}>
                      {item.file_type}
                    </span>
                  </td>
                  <td className="px-6 py-4.5">
                    <div className="flex items-center gap-1.5 text-slate-500 text-xs font-semibold">
                      <Calendar className="w-3.5 h-3.5 text-slate-400" />
                      <span>{new Date(item.uploaded_at).toLocaleString()}</span>
                    </div>
                  </td>
                  <td className="px-6 py-4.5">
                    <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-bold bg-amber-50 text-amber-700 border border-amber-200/60">
                      <span className="w-1.5 h-1.5 rounded-full bg-amber-500 animate-pulse" />
                      {item.status}
                    </span>
                  </td>
                  <td className="px-6 py-4.5 text-right">
                    {deleteConfirmId === item.id ? (
                      <div className="flex items-center justify-end gap-2 animate-fade-in">
                        <span className="text-[10px] font-bold text-rose-600 uppercase tracking-wider">Confirm Delete?</span>
                        <button
                          onClick={() => handleDelete(item.id)}
                          disabled={deletingId === item.id}
                          className="p-1 bg-rose-600 hover:bg-rose-500 text-white rounded-lg text-xs font-bold transition-all px-2.5 py-1 flex items-center gap-1 shadow-sm"
                        >
                          {deletingId === item.id ? (
                            <Loader2 className="w-3 h-3 animate-spin" />
                          ) : (
                            <span>Yes</span>
                          )}
                        </button>
                        <button
                          onClick={() => setDeleteConfirmId(null)}
                          disabled={deletingId === item.id}
                          className="p-1 bg-slate-200 hover:bg-slate-300 text-slate-700 rounded-lg text-xs font-bold transition-all px-2.5 py-1"
                        >
                          No
                        </button>
                      </div>
                    ) : (
                      <div className="flex items-center justify-end gap-2">
                        <button
                          onClick={() => handlePreview(item)}
                          className="p-2 text-slate-400 hover:text-teal-600 hover:bg-teal-50 rounded-xl transition-all border border-transparent hover:border-teal-150"
                          title="Preview document"
                        >
                          <Eye className="w-4 h-4" />
                        </button>
                        <button
                          onClick={() => setDeleteConfirmId(item.id)}
                          className="p-2 text-slate-400 hover:text-rose-600 hover:bg-rose-50 rounded-xl transition-all border border-transparent hover:border-rose-150"
                          title="Delete record"
                        >
                          <Trash2 className="w-4 h-4" />
                        </button>
                      </div>
                    )}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>

      {/* Preview Modal */}
      {previewItem && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-900/60 backdrop-blur-sm animate-fade-in">
          <div className="bg-white rounded-3xl border border-slate-200 w-full max-w-3xl max-h-[85vh] flex flex-col shadow-2xl overflow-hidden animate-scale-in">
            {/* Modal Header */}
            <div className="px-6 py-5 border-b border-slate-100 flex items-center justify-between bg-slate-50/50">
              <div className="flex items-center gap-3">
                <div className={`p-2 rounded-xl border ${getFileIconColor(previewItem.file_type)}`}>
                  <FileText className="w-5 h-5" />
                </div>
                <div>
                  <h4 className="font-bold text-slate-900 truncate max-w-[400px]">
                    {previewItem.filename || 'Direct Note Upload'}
                  </h4>
                  <span className="text-[10px] font-mono text-slate-400 block mt-0.5">
                    UUID: {previewItem.id}
                  </span>
                </div>
              </div>
              <button
                onClick={() => setPreviewItem(null)}
                className="p-2 text-slate-400 hover:text-slate-600 hover:bg-slate-100 rounded-xl transition-all"
              >
                <X className="w-5 h-5" />
              </button>
            </div>

            {/* Modal Content */}
            <div className="p-6 overflow-y-auto flex-1 bg-white">
              {loadingPreview ? (
                <div className="flex flex-col items-center justify-center py-20 space-y-3">
                  <Loader2 className="w-8 h-8 text-teal-500 animate-spin" />
                  <span className="text-xs font-bold text-slate-400 uppercase tracking-wider">Loading Content...</span>
                </div>
              ) : previewItem.file_type === 'PDF' ? (
                <div className="p-8 text-center border-2 border-dashed border-slate-150 rounded-2xl space-y-4 max-w-md mx-auto my-6 bg-slate-50/50">
                  <div className="p-3 bg-rose-50 text-rose-500 rounded-2xl w-fit mx-auto border border-rose-100 shadow-sm">
                    <ShieldAlert className="w-8 h-8" />
                  </div>
                  <h5 className="font-bold text-slate-800">PDF Store Only Mode</h5>
                  <p className="text-xs text-slate-500 leading-relaxed">
                    This PDF file has been securely written to the server's disk storage in 
                    <code className="bg-slate-100 px-1 py-0.5 rounded mx-1 font-mono">uploads/</code>. 
                    Extraction and redaction of text inside PDF layouts will be implemented in subsequent phases.
                  </p>
                </div>
              ) : (
                <div className="space-y-4">
                  <div className="flex items-center gap-2 text-[10px] font-bold text-slate-400 uppercase tracking-widest bg-slate-50/50 p-2.5 border border-slate-100 rounded-xl w-fit">
                    <Clipboard className="w-3.5 h-3.5 text-teal-600" />
                    <span>Plain Text Content</span>
                  </div>
                  <div className="bg-slate-50 p-5 rounded-2xl border border-slate-150 text-slate-800 text-sm font-mono whitespace-pre-wrap leading-relaxed max-h-[50vh] overflow-y-auto shadow-inner">
                    {previewContent || <span className="text-slate-400 italic">No text content found in this note.</span>}
                  </div>
                </div>
              )}
            </div>

            {/* Modal Footer */}
            <div className="px-6 py-4.5 border-t border-slate-100 flex justify-end bg-slate-50/50 gap-3">
              <div className="flex items-center gap-1.5 text-xs font-semibold text-slate-400 mr-auto">
                <Calendar className="w-4 h-4 text-slate-400" />
                <span>Uploaded: {new Date(previewItem.uploaded_at).toLocaleString()}</span>
              </div>
              <button
                onClick={() => setPreviewItem(null)}
                className="px-5 py-2.5 bg-slate-800 hover:bg-slate-700 text-white font-bold rounded-xl transition-all text-sm shadow-sm"
              >
                Close Preview
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default UploadHistory;
