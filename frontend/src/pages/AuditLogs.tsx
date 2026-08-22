import React, { useState, useEffect } from 'react';
import { ShieldCheck, Search } from 'lucide-react';
import { useAuth } from '../context/AuthContext';
import { getOrgAuditLogs } from '../api/endpoints';
import { AuditLogItem } from '../types/api';

export const AuditLogs: React.FC = () => {
  const { activeOrgId } = useAuth();
  const [logs, setLogs] = useState<AuditLogItem[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [search, setSearch] = useState('');

  useEffect(() => {
    if (activeOrgId) {
      setIsLoading(true);
      getOrgAuditLogs(activeOrgId)
        .then(setLogs)
        .catch(console.error)
        .finally(() => setIsLoading(false));
    }
  }, [activeOrgId]);

  const filteredLogs = (Array.isArray(logs) ? logs : []).filter(
    (l) =>
      (l.action || '').toLowerCase().includes(search.toLowerCase()) ||
      (l.resource_type || '').toLowerCase().includes(search.toLowerCase()) ||
      (l.resource_id && l.resource_id.toLowerCase().includes(search.toLowerCase()))
  );

  return (
    <div className="space-y-8 max-w-7xl mx-auto">
      {/* Header */}
      <div className="bg-surface p-6 rounded-2xl border border-surface-border">
        <div className="flex items-center gap-2">
          <ShieldCheck className="w-5 h-5 text-rose-500" />
          <h2 className="text-xl font-bold text-white tracking-tight">Security & Governance Audit Trail</h2>
        </div>
        <p className="text-xs text-slate-400 mt-1">
          Append-only chronological log of all organization activities, analyses, dataset uploads, and investigator actions.
        </p>
      </div>

      {/* Search */}
      <div className="flex items-center gap-4 bg-surface p-4 rounded-xl border border-surface-border">
        <div className="relative flex-1">
          <Search className="w-4 h-4 text-slate-400 absolute left-3.5 top-1/2 -translate-y-1/2" />
          <input
            type="text"
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            placeholder="Search by action, resource type, or ID..."
            className="w-full pl-10 pr-4 py-2 bg-surface-elevated border border-surface-border rounded-xl text-xs text-white placeholder-slate-500 focus:outline-none focus:border-rose-500 transition-colors"
          />
        </div>
      </div>

      {/* Audit Log Table */}
      <div className="bg-surface rounded-2xl border border-surface-border overflow-hidden shadow-sm">
        {filteredLogs.length === 0 ? (
          <div className="p-12 text-center text-xs text-slate-500">
            {isLoading ? 'Loading audit records...' : 'No audit log entries recorded yet.'}
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs">
              <thead className="bg-surface-elevated/60 text-slate-400 uppercase tracking-wider font-semibold border-b border-surface-border">
                <tr>
                  <th className="py-3 px-6">Timestamp</th>
                  <th className="py-3 px-6">Action</th>
                  <th className="py-3 px-6">Resource Type</th>
                  <th className="py-3 px-6">Resource ID</th>
                  <th className="py-3 px-6">Details</th>
                  <th className="py-3 px-6 text-right">IP Address</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-surface-border/50 text-slate-300 font-mono">
                {filteredLogs.map((log) => (
                  <tr key={log.id} className="hover:bg-surface-hover transition-colors">
                    <td className="py-3.5 px-6 text-slate-400">
                      {new Date(log.created_at).toLocaleString()}
                    </td>
                    <td className="py-3.5 px-6 font-sans">
                      <span className="px-2 py-0.5 rounded-full text-[10px] font-semibold bg-rose-500/10 text-rose-400 border border-rose-500/20">
                        {log.action}
                      </span>
                    </td>
                    <td className="py-3.5 px-6 text-white font-medium">{log.resource_type}</td>
                    <td className="py-3.5 px-6 text-slate-400">{log.resource_id ? `${log.resource_id.slice(0, 12)}...` : '-'}</td>
                    <td className="py-3.5 px-6 text-slate-400 font-sans truncate max-w-xs" title={JSON.stringify(log.details)}>
                      {log.details ? JSON.stringify(log.details) : '-'}
                    </td>
                    <td className="py-3.5 px-6 text-right text-slate-500">{log.ip_address || '127.0.0.1'}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  );
};
