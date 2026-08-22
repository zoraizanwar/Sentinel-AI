import React, { useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { FileSpreadsheet, Plus, ArrowRight, Zap } from 'lucide-react';
import { useWorkspace } from '../context/WorkspaceContext';
import { useAuth } from '../context/AuthContext';
import { useAnalysis } from '../context/AnalysisContext';

export const Analyses: React.FC = () => {
  const { analyses, refreshAnalyses, loadAnalysisDetail } = useWorkspace();
  const { setAnalysisResultDirectly } = useAnalysis();
  const { activeRole } = useAuth();
  const navigate = useNavigate();

  useEffect(() => {
    refreshAnalyses();
  }, [refreshAnalyses]);

  const handleSelectAnalysis = async (analysisId: string) => {
    const detail = await loadAnalysisDetail(analysisId);
    if (detail) {
      setAnalysisResultDirectly(detail);
    }
    navigate('/');
  };

  const canAnalyze = activeRole === 'ORGANIZATION_ADMIN' || activeRole === 'ANALYST';

  return (
    <div className="space-y-8 max-w-7xl mx-auto">
      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 bg-surface p-6 rounded-2xl border border-surface-border">
        <div>
          <div className="flex items-center gap-2">
            <FileSpreadsheet className="w-5 h-5 text-rose-500" />
            <h2 className="text-xl font-bold text-white tracking-tight">Machine Learning Analyses</h2>
          </div>
          <p className="text-xs text-slate-400 mt-1">
            Historical audit records of trained models, threshold optimizations, and risk intelligence runs.
          </p>
        </div>

        {canAnalyze && (
          <button
            onClick={() => navigate('/upload')}
            className="inline-flex items-center gap-2 px-4 py-2 bg-rose-600 hover:bg-rose-500 text-white rounded-xl text-xs font-semibold shadow-md shadow-rose-950/40 transition-all cursor-pointer"
          >
            <Plus className="w-4 h-4" />
            Run New Analysis
          </button>
        )}
      </div>

      {/* Analyses List */}
      {analyses.length === 0 ? (
        <div className="bg-surface rounded-2xl border border-surface-border p-12 text-center">
          <FileSpreadsheet className="w-12 h-12 text-slate-600 mx-auto mb-3" />
          <h3 className="text-sm font-medium text-slate-300">No completed analyses yet</h3>
          <p className="text-xs text-slate-500 mt-1">
            Upload a CSV dataset and run the ML pipeline to generate persistent fraud models.
          </p>
          {canAnalyze && (
            <button
              onClick={() => navigate('/upload')}
              className="mt-4 inline-flex items-center gap-2 px-4 py-2 bg-rose-600 hover:bg-rose-500 text-white rounded-xl text-xs font-semibold cursor-pointer"
            >
              <Plus className="w-4 h-4" /> Start Ingestion
            </button>
          )}
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {analyses.map((a: any) => {
            const aId = a.id || a.analysis_id || '';
            const modelName = a.model_name || 'XGBoost';
            const clientName = a.client_name || '';
            const status = a.status || 'COMPLETED';
            const thresholdStr = a.optimal_threshold != null ? Number(a.optimal_threshold).toFixed(4) : null;
            const execTimeStr = a.execution_time_seconds != null ? `${Number(a.execution_time_seconds).toFixed(2)}s` : null;
            const totalTx = a.total_transactions != null ? Number(a.total_transactions).toLocaleString() : null;
            const fraudTx = a.fraud_transactions ?? a.fraud_count;
            const fraudRate = a.fraud_rate_percentage != null ? `${Number(a.fraud_rate_percentage).toFixed(2)}%` : null;
            const createdDate = a.created_at ? new Date(a.created_at).toLocaleDateString() : 'Recent';

            return (
              <div
                key={aId}
                onClick={() => handleSelectAnalysis(aId)}
                className="bg-surface rounded-2xl border border-surface-border p-6 hover:border-rose-500/50 hover:bg-surface-elevated/40 transition-all shadow-sm cursor-pointer group flex flex-col justify-between"
              >
                <div>
                  <div className="flex items-start justify-between gap-2 mb-4">
                    <div className="w-10 h-10 rounded-xl bg-surface-elevated border border-surface-border flex items-center justify-center text-rose-400">
                      <Zap className="w-5 h-5" />
                    </div>
                    <span className="px-2.5 py-0.5 rounded-full text-[10px] font-semibold bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">
                      {status}
                    </span>
                  </div>

                  <h3 className="text-base font-bold text-white group-hover:text-rose-400 transition-colors">
                    {clientName ? `${clientName} • ${modelName}` : modelName}
                  </h3>
                  <p className="text-xs font-mono text-slate-400 mt-0.5">
                    {aId ? `ID: ${aId.slice(0, 8)}...` : 'Analysis Run'}
                  </p>

                  <div className="mt-4 pt-4 border-t border-surface-border space-y-2 text-xs text-slate-400">
                    {thresholdStr && (
                      <div className="flex items-center justify-between font-mono">
                        <span className="text-slate-500">Optimal Threshold</span>
                        <span className="text-white font-semibold">{thresholdStr}</span>
                      </div>
                    )}
                    {totalTx && (
                      <div className="flex items-center justify-between font-mono">
                        <span className="text-slate-500">Volume</span>
                        <span className="text-slate-200">
                          {totalTx} txs {fraudTx != null ? `(${Number(fraudTx).toLocaleString()} fraud)` : ''}
                        </span>
                      </div>
                    )}
                    {fraudRate && (
                      <div className="flex items-center justify-between font-mono">
                        <span className="text-slate-500">Fraud Rate</span>
                        <span className="text-rose-400 font-semibold">{fraudRate}</span>
                      </div>
                    )}
                    {execTimeStr && (
                      <div className="flex items-center justify-between font-mono">
                        <span className="text-slate-500">Execution Time</span>
                        <span className="text-slate-300">{execTimeStr}</span>
                      </div>
                    )}
                    <div className="flex items-center justify-between font-mono">
                      <span className="text-slate-500">Executed At</span>
                      <span className="text-slate-400">{createdDate}</span>
                    </div>
                  </div>
                </div>

                <div className="mt-6 pt-4 border-t border-surface-border flex items-center justify-between text-xs font-medium text-slate-400 group-hover:text-rose-400">
                  <span>Explore Full Results</span>
                  <ArrowRight className="w-4 h-4" />
                </div>
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
};
