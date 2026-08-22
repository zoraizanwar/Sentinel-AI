import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { Search, Cpu } from 'lucide-react';
import { useAnalysis } from '../context/AnalysisContext';
import { EmptyState } from '../components/common/EmptyState';

export const Investigation: React.FC = () => {
  const { analysisId, openInvestigation } = useAnalysis();
  const navigate = useNavigate();
  const [txIdInput, setTxIdInput] = useState('');

  const handleLookup = (e: React.FormEvent) => {
    e.preventDefault();
    if (txIdInput.trim()) {
      openInvestigation(txIdInput.trim());
    }
  };

  if (!analysisId) {
    return (
      <EmptyState
        title="No Active Dataset Session"
        description="Upload a transaction dataset or select an analysis from history to execute machine learning inference and transaction-level SHAP explainability."
        actionLabel="Upload Dataset"
        onAction={() => navigate('/upload')}
      />
    );
  }

  return (
    <div className="space-y-8 max-w-4xl mx-auto">
      {/* Search Header */}
      <div className="bg-surface rounded-xl border border-surface-border p-8 text-center space-y-4">
        <div className="w-12 h-12 rounded-xl bg-rose-500/15 border border-rose-500/30 text-rose-400 mx-auto flex items-center justify-center">
          <Cpu className="w-6 h-6" />
        </div>
        <h2 className="text-xl font-bold text-white tracking-tight">
          Explainable AI Transaction Investigator
        </h2>
        <p className="text-xs text-slate-400 max-w-md mx-auto leading-relaxed">
          Input any transaction identifier to execute on-demand local SHAP feature attribution,
          uncovering the exact mathematical factors driving risk scores higher or lower.
        </p>

        <form onSubmit={handleLookup} className="max-w-md mx-auto flex gap-2 pt-2">
          <div className="relative flex-1">
            <Search className="w-4 h-4 text-slate-400 absolute left-3.5 top-1/2 -translate-y-1/2" />
            <input
              type="text"
              placeholder="e.g. 16bf2e46c54369a8eab2214649506425"
              value={txIdInput}
              onChange={(e) => setTxIdInput(e.target.value)}
              className="w-full pl-10 pr-4 py-2.5 bg-surface-elevated border border-surface-border rounded-lg text-sm text-white placeholder-slate-400 focus:outline-hidden focus:border-rose-500 font-mono transition-colors"
            />
          </div>
          <button
            type="submit"
            className="px-5 py-2.5 text-xs font-semibold text-white bg-rose-600 hover:bg-rose-500 rounded-lg shadow-md shadow-rose-950/40 transition-colors cursor-pointer"
          >
            Investigate
          </button>
        </form>
      </div>

      {/* Investigation Methodology Guide */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <div className="bg-surface rounded-xl border border-surface-border p-5 space-y-2">
          <div className="w-7 h-7 rounded-lg bg-surface-elevated flex items-center justify-center text-rose-400 font-mono text-xs font-bold">
            01
          </div>
          <h3 className="text-sm font-bold text-white">Local Feature Attribution</h3>
          <p className="text-xs text-slate-400 leading-relaxed">
            Measures the marginal contribution of transaction amount, time-of-day, geospatial distance,
            and merchant risk tier against expected population baseline.
          </p>
        </div>

        <div className="bg-surface rounded-xl border border-surface-border p-5 space-y-2">
          <div className="w-7 h-7 rounded-lg bg-surface-elevated flex items-center justify-center text-amber-400 font-mono text-xs font-bold">
            02
          </div>
          <h3 className="text-sm font-bold text-white">On-Demand Computation</h3>
          <p className="text-xs text-slate-400 leading-relaxed">
            Rather than calculating explanations for millions of transactions upfront, SHAP values are
            derived dynamically and cached in memory per session.
          </p>
        </div>

        <div className="bg-surface rounded-xl border border-surface-border p-5 space-y-2">
          <div className="w-7 h-7 rounded-lg bg-surface-elevated flex items-center justify-center text-emerald-400 font-mono text-xs font-bold">
            03
          </div>
          <h3 className="text-sm font-bold text-white">Auditable & Explainable</h3>
          <p className="text-xs text-slate-400 leading-relaxed">
            Produces human-interpretable reasons supporting regulatory compliance, adverse action notices,
            and fraud analyst review workflows.
          </p>
        </div>
      </div>
    </div>
  );
};
