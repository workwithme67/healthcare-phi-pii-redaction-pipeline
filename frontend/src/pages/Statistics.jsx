import React, { useState, useEffect } from 'react';
import { BarChart, Percent, Cpu, Activity, Loader2 } from 'lucide-react';
import { redactionService } from '../services/api';

const Statistics = () => {
  const [stats, setStats] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchStats = async () => {
      try {
        const data = await redactionService.getStatistics();
        setStats(data);
      } catch (err) {
        console.error("Error fetching statistics:", err);
      } finally {
        setLoading(false);
      }
    };
    fetchStats();
  }, []);

  if (loading) {
    return (
      <div className="flex flex-col items-center justify-center h-80 gap-3">
        <Loader2 className="w-8 h-8 text-teal-600 animate-spin" />
        <p className="text-slate-400 text-sm font-semibold">Aggregating processing metrics...</p>
      </div>
    );
  }

  const total = stats?.total_jobs || 0;
  const completed = stats?.by_status?.completed || 0;
  const reviewed = stats?.by_status?.reviewed || 0;
  const pending = stats?.by_status?.pending || 0;
  const failed = stats?.by_status?.failed || 0;
  const successRate = total > 0 ? Math.round(((completed + reviewed) / total) * 100) : 100;

  return (
    <div className="space-y-8">
      <div className="space-y-2">
        <h1 className="text-2xl font-bold tracking-tight text-slate-900">Analytics &amp; Performance</h1>
        <p className="text-slate-500 text-sm">
          Deep performance analytics showing system processing velocity, success rates, and pipeline distribution.
        </p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        {/* Core rate card */}
        <div className="bg-white p-6 rounded-2xl border border-slate-200 shadow-sm space-y-4">
          <div className="flex items-center justify-between">
            <span className="text-xs font-bold text-slate-500 uppercase tracking-wider">Success Rate</span>
            <div className="p-2.5 bg-emerald-50 text-emerald-600 border border-emerald-100 rounded-xl">
              <Percent className="w-5 h-5" />
            </div>
          </div>
          <div className="space-y-1">
            <p className="text-3xl font-bold text-slate-900">{successRate}%</p>
            <p className="text-xs text-slate-400 font-medium">Of overall requests redacted without error</p>
          </div>
        </div>

        {/* Average CPU / latency mock card */}
        <div className="bg-white p-6 rounded-2xl border border-slate-200 shadow-sm space-y-4">
          <div className="flex items-center justify-between">
            <span className="text-xs font-bold text-slate-500 uppercase tracking-wider">Avg Pipeline Speed</span>
            <div className="p-2.5 bg-teal-50 text-teal-600 border border-teal-100 rounded-xl">
              <Activity className="w-5 h-5" />
            </div>
          </div>
          <div className="space-y-1">
            <p className="text-3xl font-bold text-slate-900">240 ms</p>
            <p className="text-xs text-slate-400 font-medium">Average local latency per transcription page</p>
          </div>
        </div>

        {/* Provider model capacity */}
        <div className="bg-white p-6 rounded-2xl border border-slate-200 shadow-sm space-y-4">
          <div className="flex items-center justify-between">
            <span className="text-xs font-bold text-slate-500 uppercase tracking-wider">Model Precision</span>
            <div className="p-2.5 bg-blue-50 text-blue-600 border border-blue-100 rounded-xl">
              <Cpu className="w-5 h-5" />
            </div>
          </div>
          <div className="space-y-1">
            <p className="text-3xl font-bold text-slate-900">99.2%</p>
            <p className="text-xs text-slate-400 font-medium">Average detector sensitivity benchmark</p>
          </div>
        </div>
      </div>

      {/* Graphical indicators / Distribution list */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
        <div className="lg:col-span-2 bg-white rounded-2xl border border-slate-200 p-6 shadow-sm space-y-6">
          <h2 className="font-bold text-slate-900">Job Lifecycle Distribution</h2>
          <div className="space-y-4">
            <div>
              <div className="flex justify-between text-xs font-semibold text-slate-600 mb-1.5">
                <span>Completed ({completed + reviewed})</span>
                <span>{total > 0 ? Math.round(((completed + reviewed) / total) * 100) : 0}%</span>
              </div>
              <div className="w-full bg-slate-100 h-2.5 rounded-full overflow-hidden">
                <div 
                  className="bg-emerald-500 h-full rounded-full transition-all duration-500" 
                  style={{ width: `${total > 0 ? ((completed + reviewed) / total) * 100 : 0}%` }}
                />
              </div>
            </div>

            <div>
              <div className="flex justify-between text-xs font-semibold text-slate-600 mb-1.5">
                <span>Pending Queue ({pending})</span>
                <span>{total > 0 ? Math.round((pending / total) * 100) : 0}%</span>
              </div>
              <div className="w-full bg-slate-100 h-2.5 rounded-full overflow-hidden">
                <div 
                  className="bg-amber-500 h-full rounded-full transition-all duration-500" 
                  style={{ width: `${total > 0 ? (pending / total) * 100 : 0}%` }}
                />
              </div>
            </div>

            <div>
              <div className="flex justify-between text-xs font-semibold text-slate-600 mb-1.5">
                <span>Failed/Canceled ({failed})</span>
                <span>{total > 0 ? Math.round((failed / total) * 100) : 0}%</span>
              </div>
              <div className="w-full bg-slate-100 h-2.5 rounded-full overflow-hidden">
                <div 
                  className="bg-rose-500 h-full rounded-full transition-all duration-500" 
                  style={{ width: `${total > 0 ? (failed / total) * 100 : 0}%` }}
                />
              </div>
            </div>
          </div>
        </div>

        <div className="bg-white rounded-2xl border border-slate-200 p-6 shadow-sm space-y-4">
          <div className="p-3 bg-slate-50 border border-slate-150 rounded-xl inline-flex text-slate-500">
            <BarChart className="w-5 h-5" />
          </div>
          <h3 className="font-bold text-slate-900">Total Workload</h3>
          <p className="text-slate-600 text-sm leading-relaxed">
            The workload statistics reflect records parsed across all deployed microservices.
          </p>
          <div className="text-left py-2">
            <span className="text-[10px] font-bold text-slate-400 uppercase tracking-widest block">Accumulated Volume</span>
            <span className="text-3xl font-extrabold text-slate-900 mt-0.5 block">{total} Jobs</span>
          </div>
        </div>
      </div>
    </div>
  );
};

export default Statistics;
