import React, { useState, useEffect } from 'react';
import { ShieldAlert, Clock, Terminal } from 'lucide-react';
import { auditService } from '../services/api';

const AuditLogs = () => {
  const [logs, setLogs] = useState([]);
  const [total, setTotal] = useState(0);
  const [page, setPage] = useState(1);
  const [pageSize] = useState(25);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchLogs = async () => {
      setLoading(true);
      try {
        const data = await auditService.listLogs(page, pageSize);
        setLogs(data.items);
        setTotal(data.total);
      } catch (err) {
        console.error("Error fetching audit logs:", err);
      } finally {
        setLoading(false);
      }
    };
    fetchLogs();
  }, [page, pageSize]);

  return (
    <div className="space-y-8">
      <div className="space-y-2">
        <h1 className="text-2xl font-bold tracking-tight text-slate-900">HIPAA Audit Trail</h1>
        <p className="text-slate-500 text-sm">
          Immutable logging of every PHI pipeline request for rigorous HIPAA-compliance verification.
        </p>
      </div>

      {/* Logs Table */}
      <div className="bg-white rounded-2xl border border-slate-200 shadow-sm overflow-hidden">
        <div className="px-5 py-4 border-b border-slate-200 flex items-center justify-between bg-slate-50">
          <div className="flex items-center gap-2 text-slate-700">
            <Terminal className="w-4 h-4" />
            <span className="text-xs font-semibold uppercase tracking-wider">Access Ledger</span>
          </div>
          <span className="text-xs font-semibold text-slate-500">
            {total} Total Operations Recorded
          </span>
        </div>

        <div className="overflow-x-auto">
          {loading ? (
            <div className="p-8 space-y-4">
              {[1, 2, 3, 4].map(i => (
                <div key={i} className="h-12 bg-slate-100 animate-pulse rounded-xl" />
              ))}
            </div>
          ) : logs.length === 0 ? (
            <div className="p-16 text-center space-y-3">
              <div className="inline-flex p-3 bg-slate-50 text-slate-400 rounded-2xl border border-slate-150 shadow-inner mx-auto">
                <ShieldAlert className="w-6 h-6" />
              </div>
              <p className="text-slate-400 text-sm font-medium">No actions recorded in the audit trail yet.</p>
            </div>
          ) : (
            <table className="w-full text-left border-collapse">
              <thead>
                <tr className="bg-slate-50 border-b border-slate-150 text-[10px] font-bold text-slate-500 uppercase tracking-wider">
                  <th className="px-6 py-4">Action</th>
                  <th className="px-6 py-4">Actor / System</th>
                  <th className="px-6 py-4">Request correlation ID</th>
                  <th className="px-6 py-4">Client IP</th>
                  <th className="px-6 py-4">Timestamp (UTC)</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100 text-sm">
                {logs.map((log) => (
                  <tr key={log.id} className="hover:bg-slate-50/30 transition-colors">
                    <td className="px-6 py-4 font-semibold text-slate-900">
                      <span className={`inline-flex px-2.5 py-1 rounded-full text-xs font-semibold ${
                        log.action === 'REDACT'
                          ? 'bg-purple-50 text-purple-700 border border-purple-200'
                          : log.action === 'UPLOAD'
                          ? 'bg-blue-50 text-blue-700 border border-blue-200'
                          : 'bg-slate-50 text-slate-700 border border-slate-200'
                      }`}>
                        {log.action}
                      </span>
                    </td>
                    <td className="px-6 py-4 text-slate-600 font-medium">
                      {log.actor}
                    </td>
                    <td className="px-6 py-4 font-mono text-xs text-slate-400">
                      {log.request_id}
                    </td>
                    <td className="px-6 py-4 text-slate-500 font-medium">
                      {log.ip_address || 'Internal'}
                    </td>
                    <td className="px-6 py-4 text-xs text-slate-400 font-medium flex items-center gap-1.5">
                      <Clock className="w-3.5 h-3.5" />
                      <span>{new Date(log.created_at).toLocaleString()}</span>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
        </div>

        {/* Pagination controls */}
        {total > pageSize && (
          <div className="px-6 py-4 border-t border-slate-100 flex items-center justify-between bg-slate-50">
            <button
              disabled={page === 1}
              onClick={() => setPage(page - 1)}
              className="px-4 py-2 border border-slate-200 bg-white rounded-xl text-xs font-bold text-slate-600 hover:bg-slate-50 disabled:opacity-50 transition-colors"
            >
              Previous
            </button>
            <span className="text-xs font-semibold text-slate-500">
              Page {page} of {Math.ceil(total / pageSize)}
            </span>
            <button
              disabled={page >= Math.ceil(total / pageSize)}
              onClick={() => setPage(page + 1)}
              className="px-4 py-2 border border-slate-200 bg-white rounded-xl text-xs font-bold text-slate-600 hover:bg-slate-50 disabled:opacity-50 transition-colors"
            >
              Next
            </button>
          </div>
        )}
      </div>
    </div>
  );
};

export default AuditLogs;
