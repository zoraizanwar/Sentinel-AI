import React from 'react';
import { NavLink } from 'react-router-dom';
import {
  ShieldAlert,
  LayoutDashboard,
  Building,
  Users,
  FileSpreadsheet,
  Receipt,
  LineChart,
  SearchCheck,
  Database,
  FileText,
  UploadCloud,
  ShieldCheck,
  Settings,
  ChevronDown,
} from 'lucide-react';
import { useWorkspace } from '../../context/WorkspaceContext';
import { useAuth } from '../../context/AuthContext';
import { useAnalysis } from '../../context/AnalysisContext';

export const Sidebar: React.FC = () => {
  const { organizations, activeOrg } = useWorkspace();
  const { switchOrganization, activeRole } = useAuth();
  const { analysisId } = useAnalysis();

  const workspaceNav = [
    { to: '/org-dashboard', label: 'Org Portfolio', icon: Building },
    { to: '/clients', label: 'Clients', icon: Users },
    { to: '/analyses', label: 'Analyses History', icon: FileSpreadsheet },
    { to: '/audit-logs', label: 'Audit Logs', icon: ShieldCheck },
    { to: '/settings', label: 'Settings & RBAC', icon: Settings },
  ];

  const analysisNav = [
    { to: '/', label: 'Analysis Overview', icon: LayoutDashboard },
    { to: '/transactions', label: 'Transactions', icon: Receipt },
    { to: '/analytics', label: 'Risk Analytics', icon: LineChart },
    { to: '/investigation', label: 'Investigation', icon: SearchCheck },
    { to: '/dataset', label: 'Dataset & Model', icon: Database },
    { to: '/reports', label: 'Reports', icon: FileText },
  ];

  return (
    <aside className="w-64 bg-surface border-r border-surface-border flex flex-col shrink-0 h-screen sticky top-0">
      {/* Brand Header */}
      <div className="h-16 flex items-center gap-3 px-6 border-b border-surface-border">
        <div className="w-9 h-9 rounded-xl bg-gradient-to-br from-rose-500 to-rose-700 flex items-center justify-center text-white shadow-md shadow-rose-950/40">
          <ShieldAlert className="w-5 h-5" />
        </div>
        <div>
          <span className="font-bold text-base tracking-tight text-white flex items-center gap-1.5 font-mono">
            SENTINEL<span className="text-rose-500">.AI</span>
          </span>
          <span className="block text-[10px] tracking-wider uppercase text-slate-400 font-medium">
            Fraud Intelligence
          </span>
        </div>
      </div>

      {/* Organization Switcher Dropdown */}
      {organizations.length > 0 && (
        <div className="p-3 border-b border-surface-border bg-surface-elevated/40">
          <label className="block text-[10px] uppercase font-semibold text-slate-400 mb-1 px-1">
            Active Tenant
          </label>
          <div className="relative">
            <select
              value={activeOrg?.id || ''}
              onChange={(e) => switchOrganization(e.target.value)}
              className="w-full appearance-none bg-surface border border-surface-border rounded-xl px-3 py-2 text-xs font-semibold text-white focus:outline-none focus:border-rose-500 pr-8 cursor-pointer"
            >
              {organizations.map((org) => (
                <option key={org.id} value={org.id}>
                  {org.name}
                </option>
              ))}
            </select>
            <ChevronDown className="w-3.5 h-3.5 text-slate-400 absolute right-2.5 top-1/2 -translate-y-1/2 pointer-events-none" />
          </div>
        </div>
      )}

      {/* Navigation */}
      <nav className="flex-1 px-3 py-4 space-y-1 overflow-y-auto">
        <div className="px-3 pb-2 text-[10px] font-semibold uppercase tracking-wider text-slate-400">
          Tenant Workspace
        </div>
        {workspaceNav.map((item) => {
          const Icon = item.icon;
          return (
            <NavLink
              key={item.to}
              to={item.to}
              className={({ isActive }) =>
                `flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-medium transition-all ${
                  isActive
                    ? 'bg-rose-500/15 text-white font-semibold border border-rose-500/30'
                    : 'text-slate-400 hover:text-slate-200 hover:bg-surface-hover'
                }`
              }
            >
              <Icon className="w-4 h-4 shrink-0" />
              <span>{item.label}</span>
            </NavLink>
          );
        })}

        <div className="pt-4 px-3 pb-2 text-[10px] font-semibold uppercase tracking-wider text-slate-400">
          Active ML Analysis
        </div>
        {analysisNav.map((item) => {
          const Icon = item.icon;
          return (
            <NavLink
              key={item.to}
              to={item.to}
              end={item.to === '/'}
              className={({ isActive }) =>
                `flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-medium transition-all ${
                  isActive
                    ? 'bg-rose-500/15 text-white font-semibold border border-rose-500/30'
                    : 'text-slate-400 hover:text-slate-200 hover:bg-surface-hover'
                }`
              }
            >
              <Icon className="w-4 h-4 shrink-0" />
              <span>{item.label}</span>
            </NavLink>
          );
        })}

        <div className="pt-4 px-3 pb-2 text-[10px] font-semibold uppercase tracking-wider text-slate-400">
          Actions
        </div>
        <NavLink
          to="/upload"
          className={({ isActive }) =>
            `flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-medium transition-all ${
              isActive
                ? 'bg-rose-500/15 text-white font-semibold border border-rose-500/30'
                : 'text-slate-400 hover:text-slate-200 hover:bg-surface-hover'
            }`
          }
        >
          <UploadCloud className="w-4 h-4 text-rose-400" />
          <span>Upload Dataset</span>
        </NavLink>
      </nav>

      {/* Active Session Status Footer */}
      <div className="p-4 border-t border-surface-border bg-surface-elevated/40">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <span
              className={`w-2 h-2 rounded-full ${
                analysisId ? 'bg-emerald-400 animate-pulse' : 'bg-slate-500'
              }`}
            />
            <span className="text-xs font-medium text-slate-300">
              {analysisId ? 'Active Session' : 'Ready'}
            </span>
          </div>
          <span className="text-[10px] font-mono text-rose-400 font-semibold px-2 py-0.5 rounded bg-rose-500/10 border border-rose-500/20">
            {activeRole || 'VIEWER'}
          </span>
        </div>
      </div>
    </aside>
  );
};
