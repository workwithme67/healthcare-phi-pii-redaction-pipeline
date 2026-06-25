import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { 
  FileText, 
  CheckCircle2, 
  AlertCircle, 
  Clock, 
  Plus, 
  ShieldCheck 
} from 'lucide-react';
import { redactionService } from '../services/api';

const Home = () => {
  const [stats, setStats] = useState({ total_jobs: 0, by_status: {} });
  const [recentJobs, setRecentJobs] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchData = async () => {
      try {
        const statsData = await redactionService.getStatistics();
        const listData = await redactionService.listJobs(1, 5);
        setStats(statsData);
        setRecentJobs(listData.items);
      } catch (err) {
        console.error("Error fetching dashboard data:", err);
      } finally {
        setLoading(false);
      }
    };
    fetchData();
  }, []);

  const cardItems = [
    { 
      title: 'Total Note Submissions', 
      value: stats.total_jobs, 
      icon: FileText, 
      color: 'text-blue-600', 
      bgColor: 'bg-blue-50 border-blue-100' 
    },
    { 
      title: 'Pending Redaction', 
      value: stats.by_status?.pending || 0, 
      icon: Clock, 
      color: 'text-amber-600', 
      bgColor: 'bg-amber-50 border-amber-100' 
    },
    { 
      title: 'Fully Completed', 
      value: (stats.by_status?.completed || 0) + (stats.by_status?.reviewed || 0), 
      icon: CheckCircle2, 
      color: 'text-emerald-600', 
      bgColor: 'bg-emerald-50 border-emerald-100' 
    },
    { 
      title: 'Failed/Error Jobs', 
      value: stats.by_status?.failed || 0, 
      icon: AlertCircle, 
      color: 'text-rose-600', 
      bgColor: 'bg-rose-50 border-rose-100' 
    },
  ];

  return (
    <div className="space-y-8">
      {/* Welcome Header Banner */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 p-6 bg-gradient-to-r from-slate-900 to-slate-800 rounded-3xl text-white shadow-xl">
        <div className="space-y-1">
          <h1 className="text-2xl font-bold tracking-tight">PHI/PII Redaction Dashboard</h1>
          <p className="text-slate-400 text-sm">Secure clinical note pipeline for LLM processing.</p>
        </div>
        <Link 
          to="/upload" 
          className="flex items-center gap-2 px-5 py-3 bg-teal-500 text-slate-950 font-semibold rounded-2xl shadow-lg shadow-teal-500/10 hover:bg-teal-400 transition-all self-start md:self-auto text-sm"
        >
          <Plus className="w-4 h-4" />
          <span>New Redaction Job</span>
        </Link>
      </div>

      {/* Grid Stats Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-6">
        {cardItems.map((card, idx) => {
          const Icon = card.icon;
          return (
            <div key={idx} className={`p-5 rounded-2xl border ${card.bgColor} shadow-sm flex items-center justify-between`}>
              <div className="space-y-2">
                <span className="text-xs font-semibold text-slate-500 uppercase tracking-wider">{card.title}</span>
                {loading ? (
                  <div className="h-8 w-12 bg-slate-200 animate-pulse rounded-lg" />
                ) : (
                  <p className="text-3xl font-bold text-slate-900 leading-none">{card.value}</p>
                )}
              </div>
              <div className={`p-3 bg-white rounded-xl shadow-sm border ${card.color}`}>
                <Icon className="w-6 h-6" />
              </div>
            </div>
          );
        })}
      </div>

      {/* Content Columns: Recent Jobs & HIPAA Notice */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
        {/* Recent Jobs Table */}
        <div className="lg:col-span-2 bg-white rounded-2xl border border-slate-200 shadow-sm overflow-hidden flex flex-col">
          <div className="px-6 py-5 border-b border-slate-200 flex items-center justify-between">
            <h2 className="font-bold text-slate-900">Recent Redaction Jobs</h2>
            <Link to="/audit-logs" className="text-xs font-semibold text-teal-600 hover:text-teal-700">View All</Link>
          </div>
          
          <div className="flex-1 overflow-x-auto">
            {loading ? (
              <div className="p-8 space-y-4">
                {[1, 2, 3].map(i => (
                  <div key={i} className="h-12 bg-slate-100 animate-pulse rounded-xl" />
                ))}
              </div>
            ) : recentJobs.length === 0 ? (
              <div className="p-12 text-center">
                <p className="text-slate-400 text-sm font-medium">No redaction jobs submitted yet.</p>
              </div>
            ) : (
              <table className="w-full text-left border-collapse">
                <thead>
                  <tr className="bg-slate-50 border-b border-slate-150 text-[10px] font-bold text-slate-500 uppercase tracking-wider">
                    <th className="px-6 py-3.5">Filename / ID</th>
                    <th className="px-6 py-3.5">Status</th>
                    <th className="px-6 py-3.5">Entities</th>
                    <th className="px-6 py-3.5">Created At</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-100 text-sm">
                  {recentJobs.map((job) => (
                    <tr key={job.job_id} className="hover:bg-slate-50/50 transition-colors">
                      <td className="px-6 py-4">
                        <span className="font-semibold text-slate-900 block truncate max-w-[200px]">
                          {job.filename || 'Direct Text Input'}
                        </span>
                        <span className="text-[10px] font-mono text-slate-400">{job.job_id.substring(0, 8)}...</span>
                      </td>
                      <td className="px-6 py-4">
                        <span className={`inline-flex items-center gap-1 px-2.5 py-1 rounded-full text-xs font-semibold ${
                          job.status === 'completed' || job.status === 'reviewed'
                            ? 'bg-emerald-50 text-emerald-700 border border-emerald-200'
                            : job.status === 'failed'
                            ? 'bg-rose-50 text-rose-700 border border-rose-200'
                            : 'bg-amber-50 text-amber-700 border border-amber-200'
                        }`}>
                          {job.status}
                        </span>
                      </td>
                      <td className="px-6 py-4 font-semibold text-slate-700">
                        {job.entity_count}
                      </td>
                      <td className="px-6 py-4 text-xs text-slate-400 font-medium">
                        {new Date(job.created_at).toLocaleString()}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            )}
          </div>
        </div>

        {/* HIPAA Compliance Info Card */}
        <div className="bg-white rounded-2xl border border-slate-200 p-6 shadow-sm space-y-6 flex flex-col justify-between">
          <div className="space-y-4">
            <div className="inline-flex p-3 bg-teal-50 text-teal-600 rounded-xl border border-teal-100 shadow-sm">
              <ShieldCheck className="w-6 h-6" />
            </div>
            <h2 className="text-lg font-bold text-slate-900">HIPAA Safeguards</h2>
            <p className="text-slate-600 text-sm leading-relaxed">
              This pipeline is designed to enforce HIPAA Security Rules regarding the protection of Protected Health Information (PHI) and Personally Identifiable Information (PII) before LLM submission.
            </p>
            <ul className="text-xs text-slate-500 space-y-2.5">
              <li className="flex items-start gap-2">
                <span className="w-1.5 h-1.5 rounded-full bg-teal-500 mt-1.5 flex-shrink-0" />
                <span>18 Safe Harbor PHI identifiers targeted.</span>
              </li>
              <li className="flex items-start gap-2">
                <span className="w-1.5 h-1.5 rounded-full bg-teal-500 mt-1.5 flex-shrink-0" />
                <span>Fully auditable ledger logging all access.</span>
              </li>
              <li className="flex items-start gap-2">
                <span className="w-1.5 h-1.5 rounded-full bg-teal-500 mt-1.5 flex-shrink-0" />
                <span>Local deployments to prevent data leaks.</span>
              </li>
            </ul>
          </div>
          <div className="pt-6 border-t border-slate-100">
            <Link 
              to="/settings" 
              className="text-xs font-bold text-teal-600 hover:text-teal-700"
            >
              Configure compliance policies &rarr;
            </Link>
          </div>
        </div>
      </div>
    </div>
  );
};

export default Home;
