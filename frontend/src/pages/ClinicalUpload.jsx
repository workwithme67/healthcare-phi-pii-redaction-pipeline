import React, { useState, useEffect, useCallback } from 'react';
import { ShieldCheck, Plus, FileText, ArrowRight } from 'lucide-react';
import UploadCard from '../components/UploadCard';
import UploadForm from '../components/UploadForm';
import UploadHistory from '../components/UploadHistory';
import { uploadService } from '../services/uploadService';

const ClinicalUpload = () => {
  const [uploads, setUploads] = useState([]);
  const [loading, setLoading] = useState(true);
  const [stats, setStats] = useState({
    totalUploads: 0,
    uploadedToday: 0,
    pendingProcessing: 0,
    avgSize: 0,
  });

  const fetchUploads = useCallback(async () => {
    setLoading(true);
    try {
      const data = await uploadService.listUploads();
      setUploads(data);

      // Compute stats in real-time from the uploads list
      const total = data.length;
      const todayStr = new Date().toDateString();
      const today = data.filter(
        (u) => new Date(u.uploaded_at).toDateString() === todayStr
      ).length;
      
      // All notes in Day 2 are stored in 'Uploaded' status
      const pending = data.filter(
        (u) => u.status === 'Uploaded' || u.status === 'Pending Processing'
      ).length;

      const totalSize = data.reduce((sum, item) => sum + (item.size_bytes || 0), 0);
      const avg = total > 0 ? Math.round(totalSize / total) : 0;

      setStats({
        totalUploads: total,
        uploadedToday: today,
        pendingProcessing: pending,
        avgSize: avg,
      });
    } catch (err) {
      console.error('Error fetching uploads for dashboard:', err);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchUploads();
  }, [fetchUploads]);

  return (
    <div className="space-y-8 animate-fade-in pb-12">
      {/* Welcome Header Banner */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-6 p-8 bg-gradient-to-br from-slate-900 via-slate-800 to-teal-950 rounded-3xl text-white shadow-xl relative overflow-hidden">
        <div className="space-y-2 relative z-10">
          <span className="px-3 py-1 bg-teal-500/10 text-teal-350 border border-teal-500/20 rounded-full text-xs font-bold uppercase tracking-wider">
            Day 2 Pipeline Active
          </span>
          <h1 className="text-3xl font-extrabold tracking-tight bg-gradient-to-r from-white to-slate-200 bg-clip-text text-transparent">
            Clinical Note Upload & Ingestion
          </h1>
          <p className="text-slate-400 text-sm max-w-xl">
            Securely upload clinical records. Files are validated, registered in the SQLite database, and stored locally for downstream redaction processing.
          </p>
        </div>
        <div className="flex items-center gap-3 relative z-10 self-start md:self-auto">
          <div className="p-3 bg-white/5 border border-white/10 rounded-2xl backdrop-blur-md flex items-center gap-2 text-xs font-bold text-slate-300">
            <ShieldCheck className="w-5 h-5 text-emerald-400" />
            <span>HIPAA Sanitized Storage</span>
          </div>
        </div>
        
        {/* Decorative ambient background blur */}
        <div className="absolute right-0 top-0 w-64 h-64 bg-teal-500/10 rounded-full blur-3xl -z-0 pointer-events-none" />
      </div>

      {/* KPI Stats Cards */}
      <UploadCard
        totalUploads={stats.totalUploads}
        uploadedToday={stats.uploadedToday}
        pendingProcessing={stats.pendingProcessing}
        avgSize={stats.avgSize}
      />

      {/* Upload Form and History Sections */}
      <div className="grid grid-cols-1 gap-8">
        {/* Upload Form Section */}
        <UploadForm onUploadSuccess={fetchUploads} />

        {/* Upload History Section */}
        <UploadHistory
          uploads={uploads}
          loading={loading}
          onDeleteSuccess={fetchUploads}
        />
      </div>
    </div>
  );
};

export default ClinicalUpload;
