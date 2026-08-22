import React, { useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  Building,
  Users,
  AlertTriangle,
  DollarSign,
  Plus,
  ArrowRight,
  ShieldCheck,
  Activity,
  FileSpreadsheet,
} from 'lucide-react';
import { useWorkspace } from '../context/WorkspaceContext';
import { useAuth } from '../context/AuthContext';
import { useAnalysis } from '../context/AnalysisContext';

export const OrganizationDashboard: React.FC = () => {
  const { orgDashboard, refreshOrgDashboard, activeOrg, loadAnalysisDetail } = useWorkspace();
  const { setAnalysisResultDirectly } = useAnalysis();
  const { activeRole } = useAuth();
  const navigate = useNavigate();

  useEffect(() => {
    refreshOrgDashboard();
  }, [refreshOrgDashboard]);

  const canManage = activeRole === 'ORGANIZATION_ADMIN' || activeRole === 'ANALYST';

  // Defensive field normalization
  const totalClients = orgDashboard?.total_clients ?? 0;
  const totalTxAnalyzed = orgDashboard?.total_transactions_analyzed ?? 0;
  const totalDatasets = orgDashboard?.total_datasets ?? 0;
  const totalFraud = orgDashboard?.total_fraud_transactions ?? orgDashboard?.total_fraud_detected ?? 0;
  const overallFraudRate = orgDashboard?.overall_fraud_rate_percentage ?? orgDashboard?.overall_fraud_rate_pct ?? 0;
  const totalLoss = orgDashboard?.total_financial_exposure_usd ?? orgDashboard?.total_fraud_loss_usd ?? 0;

  const clientSummaries = orgDashboard?.highest_risk_clients || orgDashboard?.client_risk_summaries || [];
  const recentAnalyses = orgDashboard?.recent_analyses || [];

  return (
    <div className="space-y-8 max-w-7xl mx-auto">
      {/* Header Banner */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 bg-surface p-6 rounded-2xl border border-surface-border">
        <div>
          <div className="flex items-center gap-2">
            <Building className="w-5 h-5 text-rose-500" />
            <h2 className="text-xl font-bold text-white tracking-tight">
              {activeOrg?.name || 'Organization Portfolio'}
            </h2>
            <span className="px-2.5 py-0.5 rounded-full text-[10px] font-semibold bg-rose-500/10 text-rose-400 border border-rose-500/20">
              {activeRole || 'MEMBER'}
            </span>
          </div>
          <p className="text-xs text-slate-400 mt-1">
            Aggregated fraud detection metrics, client risk exposure, and multi-tenant intelligence.
          </p>
        </div>

        {canManage && (
          <div className="flex items-center gap-3">
            <button
              onClick={() => navigate('/clients')}
              className="inline-flex items-center gap-2 px-4 py-2 bg-surface-elevated hover:bg-surface-hover text-white rounded-xl text-xs font-semibold border border-surface-border transition-colors cursor-pointer"
            >
              <Users className="w-4 h-4 text-slate-400" />
              Manage Clients
            </button>
            <button
              onClick={() => navigate('/upload')}
              className="inline-flex items-center gap-2 px-4 py-2 bg-rose-600 hover:bg-rose-500 text-white rounded-xl text-xs font-semibold shadow-md shadow-rose-950/40 transition-all cursor-pointer"
            >
              <Plus className="w-4 h-4" />
              New Analysis
            </button>
          </div>
        )}
      </div>

      {/* KPI Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <div className="bg-surface p-5 rounded-xl border border-surface-border shadow-sm">
          <div className="flex items-center justify-between text-slate-400 mb-2">
            <span className="text-xs font-medium uppercase tracking-wider">Active Clients</span>
            <Users className="w-4 h-4 text-sky-400" />
          </div>
          <div className="text-2xl font-bold text-white font-mono">
            {totalClients}
          </div>
          <p className="text-[11px] text-slate-400 mt-1">Monitored client institutions</p>
        </div>

        <div className="bg-surface p-5 rounded-xl border border-surface-border shadow-sm">
          <div className="flex items-center justify-between text-slate-400 mb-2">
            <span className="text-xs font-medium uppercase tracking-wider">Transactions Analyzed</span>
            <Activity className="w-4 h-4 text-indigo-400" />
          </div>
          <div className="text-2xl font-bold text-white font-mono">
            {totalTxAnalyzed.toLocaleString()}
          </div>
          <p className="text-[11px] text-slate-400 mt-1">
            Across {totalDatasets} uploaded datasets
          </p>
        </div>

        <div className="bg-surface p-5 rounded-xl border border-surface-border shadow-sm">
          <div className="flex items-center justify-between text-slate-400 mb-2">
            <span className="text-xs font-medium uppercase tracking-wider">Fraud Detected</span>
            <AlertTriangle className="w-4 h-4 text-rose-400" />
          </div>
          <div className="text-2xl font-bold text-rose-400 font-mono">
            {totalFraud.toLocaleString()}
          </div>
          <p className="text-[11px] text-slate-400 mt-1">
            Overall Rate: {overallFraudRate.toFixed(2)}%
          </p>
        </div>

        <div className="bg-surface p-5 rounded-xl border border-surface-border shadow-sm">
          <div className="flex items-center justify-between text-slate-400 mb-2">
            <span className="text-xs font-medium uppercase tracking-wider">Fraud Volume ($)</span>
            <DollarSign className="w-4 h-4 text-emerald-400" />
          </div>
          <div className="text-2xl font-bold text-emerald-400 font-mono">
            ${totalLoss.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
          </div>
          <p className="text-[11px] text-slate-400 mt-1">Detected fraud volume</p>
        </div>
      </div>

      {/* Client Risk Overview Table */}
      <div className="bg-surface rounded-2xl border border-surface-border overflow-hidden shadow-sm">
        <div className="p-6 border-b border-surface-border flex items-center justify-between">
          <div>
            <h3 className="text-base font-semibold text-white">Client Portfolio Risk Overview</h3>
            <p className="text-xs text-slate-400 mt-0.5">Institutions ranked by operational fraud risk</p>
          </div>
          <button
            onClick={() => navigate('/clients')}
            className="text-xs font-medium text-rose-400 hover:text-rose-300 flex items-center gap-1 cursor-pointer"
          >
            View All Clients <ArrowRight className="w-3.5 h-3.5" />
          </button>
        </div>

        {clientSummaries.length === 0 ? (
          <div className="p-12 text-center">
            <ShieldCheck className="w-12 h-12 text-slate-600 mx-auto mb-3" />
            <h4 className="text-sm font-medium text-slate-300">No client risk data recorded</h4>
            <p className="text-xs text-slate-500 mt-1 max-w-sm mx-auto">
              Create clients and run fraud intelligence analyses to populate the multi-client risk matrix.
            </p>
            {canManage && (
              <button
                onClick={() => navigate('/clients')}
                className="mt-4 inline-flex items-center gap-2 px-4 py-2 bg-rose-600 hover:bg-rose-500 text-white rounded-xl text-xs font-semibold cursor-pointer"
              >
                <Plus className="w-4 h-4" /> Add First Client
              </button>
            )}
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs">
              <thead className="bg-surface-elevated/60 text-slate-400 uppercase tracking-wider font-semibold border-b border-surface-border">
                <tr>
                  <th className="py-3 px-6">Client Code</th>
                  <th className="py-3 px-6">Client Name</th>
                  <th className="py-3 px-6 text-right">Transactions</th>
                  <th className="py-3 px-6 text-right">Fraud Count</th>
                  <th className="py-3 px-6 text-right">Fraud Rate</th>
                  <th className="py-3 px-6 text-center">Risk Level</th>
                  <th className="py-3 px-6 text-right">Action</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-surface-border/50 text-slate-300 font-mono">
                {clientSummaries.map((c: any) => {
                  const cId = c.client_id;
                  const code = c.client_code || 'CLI';
                  const cName = c.name || c.client_name || 'Client';
                  const txCount = c.total_transactions ?? 0;
                  const fCount = c.fraud_count ?? c.total_fraud ?? 0;
                  const fRate = c.fraud_rate_percentage ?? c.fraud_rate_pct ?? (txCount > 0 ? (fCount / txCount) * 100 : 0);
                  const riskLevel = c.risk_level || (fRate > 2.0 ? 'CRITICAL' : fRate > 1.0 ? 'HIGH' : fRate > 0.5 ? 'MEDIUM' : 'LOW');

                  return (
                    <tr key={cId || code} className="hover:bg-surface-hover transition-colors">
                      <td className="py-3.5 px-6 text-white font-semibold">{code}</td>
                      <td className="py-3.5 px-6 font-sans text-white">{cName}</td>
                      <td className="py-3.5 px-6 text-right">{txCount.toLocaleString()}</td>
                      <td className="py-3.5 px-6 text-right text-rose-400 font-semibold">{fCount.toLocaleString()}</td>
                      <td className="py-3.5 px-6 text-right">{fRate.toFixed(2)}%</td>
                      <td className="py-3.5 px-6 text-center font-sans">
                        <span
                          className={`inline-block px-2 py-0.5 rounded-full text-[10px] font-semibold ${
                            riskLevel === 'CRITICAL'
                              ? 'bg-rose-500/20 text-rose-300 border border-rose-500/40'
                              : riskLevel === 'HIGH'
                              ? 'bg-amber-500/20 text-amber-300 border border-amber-500/40'
                              : riskLevel === 'MEDIUM'
                              ? 'bg-blue-500/20 text-blue-300 border border-blue-500/40'
                              : 'bg-emerald-500/20 text-emerald-300 border border-emerald-500/40'
                          }`}
                        >
                          {riskLevel}
                        </span>
                      </td>
                      <td className="py-3.5 px-6 text-right font-sans">
                        {cId && (
                          <button
                            onClick={() => navigate(`/clients/${cId}`)}
                            className="text-slate-400 hover:text-white text-xs font-medium cursor-pointer"
                          >
                            Details &rarr;
                          </button>
                        )}
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        )}
      </div>

      {/* Recent Analyses Card */}
      <div className="bg-surface rounded-2xl border border-surface-border overflow-hidden shadow-sm">
        <div className="p-6 border-b border-surface-border flex items-center justify-between">
          <div>
            <h3 className="text-base font-semibold text-white">Recent Fraud Analyses</h3>
            <p className="text-xs text-slate-400 mt-0.5">Latest machine learning models executed across datasets</p>
          </div>
          <button
            onClick={() => navigate('/analyses')}
            className="text-xs font-medium text-rose-400 hover:text-rose-300 flex items-center gap-1 cursor-pointer"
          >
            View All Analyses <ArrowRight className="w-3.5 h-3.5" />
          </button>
        </div>

        {recentAnalyses.length === 0 ? (
          <div className="p-8 text-center text-xs text-slate-500">
            No recent analyses found for this organization.
          </div>
        ) : (
          <div className="divide-y divide-surface-border/50">
            {recentAnalyses.map((a: any) => {
              const aId = a.analysis_id || a.id;
              const modelName = a.model_name || 'XGBoost';
              const totalTx = a.total_transactions ?? 0;
              const fCount = a.fraud_count ?? 0;
              const fRate = a.fraud_rate_percentage ?? 0;
              const clientName = a.client_name || 'Client';
              const createdDate = a.created_at ? new Date(a.created_at).toLocaleDateString() : 'Recent';
              const status = a.status || 'COMPLETED';

              return (
                <div
                  key={aId || modelName}
                  onClick={async () => {
                    if (aId) {
                      const detail = await loadAnalysisDetail(aId);
                      if (detail) {
                        setAnalysisResultDirectly(detail);
                      }
                      navigate('/');
                    }
                  }}
                  className="p-4 px-6 flex items-center justify-between hover:bg-surface-hover transition-colors cursor-pointer"
                >
                  <div className="flex items-center gap-4">
                    <div className="w-10 h-10 rounded-xl bg-surface-elevated border border-surface-border flex items-center justify-center text-rose-400">
                      <FileSpreadsheet className="w-5 h-5" />
                    </div>
                    <div>
                      <h4 className="text-sm font-semibold text-white">
                        {clientName} • {modelName}
                      </h4>
                      <p className="text-xs text-slate-400 font-mono">
                        {totalTx.toLocaleString()} txs • {fCount.toLocaleString()} fraud ({fRate.toFixed(2)}%) • {createdDate}
                      </p>
                    </div>
                  </div>

                  <div className="flex items-center gap-3">
                    <span className="px-2.5 py-0.5 rounded-full text-[10px] font-semibold bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">
                      {status}
                    </span>
                    <span className="text-slate-500 text-sm">&rarr;</span>
                  </div>
                </div>
              );
            })}
          </div>
        )}
      </div>
    </div>
  );
};
