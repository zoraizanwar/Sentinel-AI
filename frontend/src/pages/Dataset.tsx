import React from 'react';
import { useNavigate } from 'react-router-dom';
import { Database, Cpu, CheckCircle2 } from 'lucide-react';
import { useAnalysis } from '../context/AnalysisContext';
import { EmptyState } from '../components/common/EmptyState';

export const Dataset: React.FC = () => {
  const { analysisResult } = useAnalysis();
  const navigate = useNavigate();

  if (!analysisResult) {
    return (
      <EmptyState
        title="No Dataset Loaded"
        description="Upload a transaction dataset to inspect its structure, data quality report, and model evaluation metrics."
        actionLabel="Upload Dataset"
        onAction={() => navigate('/upload')}
      />
    );
  }

  const { dataset_summary: summary, data_quality: quality, model_results: modelResults } = analysisResult;
  const { selected_model: selected, candidate_models: candidates, test_metrics: testMetrics } = modelResults;

  return (
    <div className="space-y-8">
      {/* Dataset Health & Schema Details */}
      <div className="bg-surface rounded-xl border border-surface-border p-6 space-y-6">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="w-9 h-9 rounded-lg bg-indigo-500/15 border border-indigo-500/30 flex items-center justify-center text-indigo-400">
              <Database className="w-5 h-5" />
            </div>
            <div>
              <h2 className="text-base font-bold text-white tracking-tight">
                Dataset Integrity & Pre-flight Quality Report
              </h2>
              <p className="text-xs text-slate-400 font-mono">
                {summary.dataset_name} ({(summary.file_size_bytes / (1024 * 1024)).toFixed(2)} MB)
              </p>
            </div>
          </div>
          <span
            className={`text-xs font-semibold px-3 py-1 rounded-full font-mono ${
              quality.is_valid_for_analysis
                ? 'bg-emerald-500/15 text-emerald-400 border border-emerald-500/30'
                : 'bg-rose-500/15 text-rose-400 border border-rose-500/30'
            }`}
          >
            {quality.is_valid_for_analysis ? 'VALIDATED FOR ML' : 'DATASET INVALID'}
          </span>
        </div>

        {/* Quality Metrics Grid */}
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-4 pt-2">
          <div className="bg-surface-elevated/60 border border-surface-border rounded-lg p-3">
            <span className="text-[11px] text-slate-400 uppercase tracking-wider block">Total Row Count</span>
            <span className="text-lg font-bold font-mono text-white mt-1 block">
              {summary.row_count.toLocaleString()}
            </span>
          </div>
          <div className="bg-surface-elevated/60 border border-surface-border rounded-lg p-3">
            <span className="text-[11px] text-slate-400 uppercase tracking-wider block">Columns Identified</span>
            <span className="text-lg font-bold font-mono text-white mt-1 block">
              {summary.column_count}
            </span>
          </div>
          <div className="bg-surface-elevated/60 border border-surface-border rounded-lg p-3">
            <span className="text-[11px] text-slate-400 uppercase tracking-wider block">Missing Cells %</span>
            <span className="text-lg font-bold font-mono text-emerald-400 mt-1 block">
              {quality.missing_cells_percentage.toFixed(2)}%
            </span>
          </div>
          <div className="bg-surface-elevated/60 border border-surface-border rounded-lg p-3">
            <span className="text-[11px] text-slate-400 uppercase tracking-wider block">Class Imbalance</span>
            <span className="text-lg font-bold font-mono text-amber-400 mt-1 block">
              {summary.class_distribution ? `${summary.class_distribution.imbalance_ratio.toFixed(1)}:1` : 'N/A'}
            </span>
          </div>
        </div>
      </div>

      {/* Model Training & Candidates Comparison Table */}
      <div className="bg-surface rounded-xl border border-surface-border p-6 space-y-6">
        <div className="flex items-center gap-3">
          <div className="w-9 h-9 rounded-lg bg-rose-500/15 border border-rose-500/30 flex items-center justify-center text-rose-400">
            <Cpu className="w-5 h-5" />
          </div>
          <div>
            <h2 className="text-base font-bold text-white tracking-tight">
              Machine Learning Model Evaluation & Benchmark Matrix
            </h2>
            <p className="text-xs text-slate-400">
              Evaluated strictly on validation and test partitions with zero data leakage
            </p>
          </div>
        </div>

        {/* Selected Model Highlight */}
        <div className="bg-surface-elevated/80 border border-rose-500/30 rounded-xl p-4 flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
          <div>
            <div className="flex items-center gap-2">
              <span className="text-xs font-mono font-semibold text-rose-400 uppercase tracking-wider">
                Active Winning Architecture:
              </span>
              <span className="text-sm font-bold text-white">{selected.model_name}</span>
            </div>
            <p className="text-xs text-slate-300 mt-1">{selected.justification}</p>
          </div>
          <div className="shrink-0 text-right font-mono text-xs">
            <span className="text-slate-400 block">Optimized Decision Threshold</span>
            <span className="text-base font-bold text-rose-400">
              τ* = {selected.optimal_threshold.toFixed(4)}
            </span>
          </div>
        </div>

        {/* Candidates Table */}
        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs font-mono">
            <thead className="bg-surface-elevated text-slate-400 font-semibold uppercase tracking-wider border-b border-surface-border">
              <tr>
                <th className="py-3 px-4">Candidate Model</th>
                <th className="py-3 px-4">PR-AUC (Primary)</th>
                <th className="py-3 px-4">ROC-AUC</th>
                <th className="py-3 px-4">Precision</th>
                <th className="py-3 px-4">Recall</th>
                <th className="py-3 px-4">F1 Score</th>
                <th className="py-3 px-4">Status</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-surface-border">
              {candidates.map((model) => {
                const isWinner = model.model_name === selected.model_name;
                return (
                  <tr
                    key={model.model_name}
                    className={isWinner ? 'bg-rose-500/5 font-semibold text-white' : 'text-slate-300'}
                  >
                    <td className="py-3 px-4 font-sans flex items-center gap-2">
                      <span>{model.model_name}</span>
                      {isWinner && (
                        <span className="text-[10px] bg-rose-500/20 text-rose-400 px-1.5 py-0.5 rounded font-mono">
                          WINNER
                        </span>
                      )}
                    </td>
                    <td className="py-3 px-4 text-rose-400 font-bold">{model.pr_auc.toFixed(4)}</td>
                    <td className="py-3 px-4">{model.roc_auc.toFixed(4)}</td>
                    <td className="py-3 px-4">{(model.precision * 100).toFixed(2)}%</td>
                    <td className="py-3 px-4">{(model.recall * 100).toFixed(2)}%</td>
                    <td className="py-3 px-4">{model.f1.toFixed(4)}</td>
                    <td className="py-3 px-4 font-sans">
                      {isWinner ? (
                        <span className="text-emerald-400 flex items-center gap-1 text-[11px]">
                          <CheckCircle2 className="w-3.5 h-3.5" /> Deployed
                        </span>
                      ) : (
                        <span className="text-slate-500 text-[11px]">Evaluated</span>
                      )}
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>

        {/* Unseen Test Evaluation Summary (if present) */}
        {testMetrics && (
          <div className="pt-4 border-t border-surface-border space-y-2">
            <h3 className="text-xs font-bold text-white uppercase tracking-wider">
              Holdout Unseen Test Set Metrics (fraudTest.csv)
            </h3>
            <div className="grid grid-cols-2 sm:grid-cols-5 gap-3 font-mono text-xs">
              <div className="p-3 bg-surface-elevated/40 rounded-lg border border-surface-border">
                <span className="text-[10px] text-slate-400 block">Test PR-AUC</span>
                <span className="text-sm font-bold text-white mt-1 block">{testMetrics.pr_auc.toFixed(4)}</span>
              </div>
              <div className="p-3 bg-surface-elevated/40 rounded-lg border border-surface-border">
                <span className="text-[10px] text-slate-400 block">Test ROC-AUC</span>
                <span className="text-sm font-bold text-white mt-1 block">{testMetrics.roc_auc.toFixed(4)}</span>
              </div>
              <div className="p-3 bg-surface-elevated/40 rounded-lg border border-surface-border">
                <span className="text-[10px] text-slate-400 block">Test Precision</span>
                <span className="text-sm font-bold text-emerald-400 mt-1 block">
                  {(testMetrics.precision * 100).toFixed(2)}%
                </span>
              </div>
              <div className="p-3 bg-surface-elevated/40 rounded-lg border border-surface-border">
                <span className="text-[10px] text-slate-400 block">Test Recall</span>
                <span className="text-sm font-bold text-emerald-400 mt-1 block">
                  {(testMetrics.recall * 100).toFixed(2)}%
                </span>
              </div>
              <div className="p-3 bg-surface-elevated/40 rounded-lg border border-surface-border">
                <span className="text-[10px] text-slate-400 block">Test F1 Score</span>
                <span className="text-sm font-bold text-white mt-1 block">{testMetrics.f1.toFixed(4)}</span>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};
