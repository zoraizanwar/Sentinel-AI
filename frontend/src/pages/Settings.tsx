import React, { useState, useEffect } from 'react';
import { Settings as SettingsIcon, UserPlus, Building } from 'lucide-react';
import { useAuth } from '../context/AuthContext';
import { useWorkspace } from '../context/WorkspaceContext';
import { getOrgMembers, addOrgMember } from '../api/endpoints';
import { OrganizationMemberItem, OrganizationRole } from '../types/api';
import { extractApiError } from '../api/client';

export const Settings: React.FC = () => {
  const { activeOrgId, activeRole } = useAuth();
  const { activeOrg } = useWorkspace();

  const [members, setMembers] = useState<OrganizationMemberItem[]>([]);
  const [email, setEmail] = useState('');
  const [role, setRole] = useState<OrganizationRole>('ANALYST');
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);

  const isAdmin = activeRole === 'ORGANIZATION_ADMIN';

  const loadMembers = async () => {
    if (!activeOrgId) return;
    try {
      const list = await getOrgMembers(activeOrgId);
      setMembers(Array.isArray(list) ? list : []);
    } catch (err) {
      console.error(err);
      setMembers([]);
    }
  };

  useEffect(() => {
    loadMembers();
  }, [activeOrgId]);

  const handleInvite = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!activeOrgId || !email) return;
    setIsSubmitting(true);
    setError(null);
    setSuccess(null);
    try {
      await addOrgMember(activeOrgId, { email, role });
      setSuccess(`Invited ${email} with role ${role}`);
      setEmail('');
      await loadMembers();
    } catch (err) {
      const apiErr = extractApiError(err);
      setError(apiErr.message);
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div className="space-y-8 max-w-7xl mx-auto">
      {/* Header */}
      <div className="bg-surface p-6 rounded-2xl border border-surface-border">
        <div className="flex items-center gap-2">
          <SettingsIcon className="w-5 h-5 text-rose-500" />
          <h2 className="text-xl font-bold text-white tracking-tight">Organization Settings & RBAC</h2>
        </div>
        <p className="text-xs text-slate-400 mt-1">
          Manage workspace members, assign fine-grained RBAC roles, and control access permissions.
        </p>
      </div>

      {/* Org Profile Summary */}
      <div className="bg-surface p-6 rounded-2xl border border-surface-border flex items-center justify-between">
        <div className="flex items-center gap-4">
          <div className="w-12 h-12 rounded-xl bg-surface-elevated border border-surface-border flex items-center justify-center text-rose-400">
            <Building className="w-6 h-6" />
          </div>
          <div>
            <h3 className="text-base font-bold text-white">{activeOrg?.name || 'Current Organization'}</h3>
            <p className="text-xs text-slate-400 font-mono">Org ID: {activeOrgId}</p>
          </div>
        </div>
        <span className="px-3 py-1 rounded-full text-xs font-semibold bg-rose-500/10 text-rose-400 border border-rose-500/20">
          Your Role: {activeRole || 'VIEWER'}
        </span>
      </div>

      {/* Invite Member Card (Admin Only) */}
      {isAdmin && (
        <div className="bg-surface p-6 rounded-2xl border border-surface-border">
          <h3 className="text-sm font-bold text-white mb-4 flex items-center gap-2">
            <UserPlus className="w-4 h-4 text-rose-400" /> Add Team Member
          </h3>

          {error && (
            <div className="mb-4 p-3 rounded-xl bg-rose-500/10 border border-rose-500/30 text-xs text-rose-200">
              {error}
            </div>
          )}

          {success && (
            <div className="mb-4 p-3 rounded-xl bg-emerald-500/10 border border-emerald-500/30 text-xs text-emerald-200">
              {success}
            </div>
          )}

          <form onSubmit={handleInvite} className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <input
              type="email"
              required
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              placeholder="colleague@riskcorp.com"
              className="px-3 py-2.5 bg-surface-elevated border border-surface-border rounded-xl text-xs text-white placeholder-slate-500 focus:outline-none focus:border-rose-500"
            />

            <select
              value={role}
              onChange={(e) => setRole(e.target.value as OrganizationRole)}
              className="px-3 py-2.5 bg-surface-elevated border border-surface-border rounded-xl text-xs text-white focus:outline-none focus:border-rose-500"
            >
              <option value="ANALYST">ANALYST (Upload, Train Models, Query)</option>
              <option value="VIEWER">VIEWER (Read-Only Dashboards & Reports)</option>
              <option value="ORGANIZATION_ADMIN">ORGANIZATION_ADMIN (Full Workspace Control)</option>
            </select>

            <button
              type="submit"
              disabled={isSubmitting}
              className="py-2.5 px-4 bg-rose-600 hover:bg-rose-500 text-white rounded-xl text-xs font-semibold shadow-md shadow-rose-950/40 cursor-pointer disabled:opacity-50"
            >
              {isSubmitting ? 'Adding...' : 'Add Member'}
            </button>
          </form>
        </div>
      )}

      {/* Member List Table */}
      <div className="bg-surface rounded-2xl border border-surface-border overflow-hidden shadow-sm">
        <div className="p-6 border-b border-surface-border">
          <h3 className="text-base font-semibold text-white">Active Team Members</h3>
          <p className="text-xs text-slate-400 mt-0.5">Assigned roles and privileges for this tenant</p>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs">
            <thead className="bg-surface-elevated/60 text-slate-400 uppercase tracking-wider font-semibold border-b border-surface-border">
              <tr>
                <th className="py-3 px-6">Member</th>
                <th className="py-3 px-6">Assigned Role</th>
                <th className="py-3 px-6 text-right">Joined Date</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-surface-border/50 text-slate-300 font-mono">
              {members.map((m) => (
                <tr key={m.id} className="hover:bg-surface-hover transition-colors">
                  <td className="py-3.5 px-6 font-sans">
                    <div className="text-white font-medium">{m.user_full_name || 'Member'}</div>
                    <div className="text-slate-400 text-[11px] font-mono">{m.user_email || m.user_id}</div>
                  </td>
                  <td className="py-3.5 px-6 font-sans">
                    <span
                      className={`px-2.5 py-0.5 rounded-full text-[10px] font-semibold ${
                        m.role === 'ORGANIZATION_ADMIN'
                          ? 'bg-rose-500/20 text-rose-300 border border-rose-500/40'
                          : m.role === 'ANALYST'
                          ? 'bg-blue-500/20 text-blue-300 border border-blue-500/40'
                          : 'bg-slate-500/20 text-slate-300 border border-slate-500/40'
                      }`}
                    >
                      {m.role}
                    </span>
                  </td>
                  <td className="py-3.5 px-6 text-right text-slate-400">
                    {new Date(m.joined_at).toLocaleDateString()}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
};
