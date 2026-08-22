import React, { useEffect, useState } from 'react';
import { X, ShieldAlert, Cpu } from 'lucide-react';
import { useAnalysis } from '../../context/AnalysisContext';
import { explainTransaction, explainOrgTransaction } from '../../api/endpoints';
import { useAuth } from '../../context/AuthContext';
import { LocalExplanation } from '../../types/api';
import { RiskBadge } from '../common/RiskBadge';
import { SHAPWaterfall } from './SHAPWaterfall';
import { Skeleton } from '../common/Skeleton';
import { ErrorMessage } from '../common/ErrorMessage';
import { extractApiError } from '../../api/client';

export const TransactionDrawer: React.FC = () => {
  const { isDrawerOpen, closeInvestigation, selectedTxId, analysisId } = useAnalysis();
  const { activeOrgId } = useAuth();
  const [explanation, setExplanation] = useState<LocalExplanation | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (isDrawerOpen && selectedTxId && analysisId) {
      fetchExplanation(selectedTxId);
    } else {
      setExplanation(null);
      setError(null);
    }
  }, [isDrawerOpen, selectedTxId, analysisId, activeOrgId]);

  const fetchExplanation = async (txId: string) => {
    if (!analysisId) return;
    setIsLoading(true);
    setError(null);
    try {
      let data: LocalExplanation | null = null;
      if (activeOrgId) {
        try {
          data = await explainOrgTransaction(activeOrgId, analysisId, txId);
        } catch {
          // fallback
        }
      }
      if (!data) {
        data = await explainTransaction(analysisId, txId);
      }
      setExplanation(data);
    } catch (err) {
      const apiErr = extractApiError(err);
      setError(apiErr.message);
    } finally {
      setIsLoading(false);
    }
  };

  if (!isDrawerOpen) return null;

  return (
    <div className="fixed inset-0 z-50 overflow-hidden">
      {/* Backdrop */}
      <div
        className="absolute inset-0 bg-black/60 backdrop-blur-xs transition-opacity"
        onClick={closeInvestigation}
      />

      <div className="fixed inset-y-0 right-0 max-w-full flex pl-10">
        <div className="w-screen max-w-xl bg-surface border-l border-surface-border shadow-2xl flex flex-col">
          {/* Drawer Header */}
          <div className="px-6 py-5 border-b border-surface-border flex items-center justify-between bg-surface-elevated/40">
            <div className="flex items-center gap-3">
              <div className="w-8 h-8 rounded-lg bg-rose-500/15 border border-rose-500/30 flex items-center justify-center text-rose-400">
                <ShieldAlert className="w-4 h-4" />
              </div>
              <div>
                <h2 className="text-sm font-bold text-white tracking-tight flex items-center gap-2">
                  Transaction Investigation
                </h2>
                <p className="text-xs text-slate-400 font-mono">
                  ID: {selectedTxId}
                </p>
              </div>
            </div>

            <button
              onClick={closeInvestigation}
              className="p-1.5 rounded-lg text-slate-400 hover:text-white hover:bg-surface-hover transition-colors cursor-pointer"
            >
              <X className="w-5 h-5" />
            </button>
          </div>

          {/* Drawer Body */}
          <div className="flex-1 overflow-y-auto p-6 space-y-6">
            {isLoading ? (
              <div className="space-y-4">
                <div className="p-4 bg-surface-elevated rounded-xl space-y-3">
                  <Skeleton className="h-6 w-32" />
                  <Skeleton className="h-4 w-48" />
                  <Skeleton className="h-10 w-full" />
                </div>
                <div className="space-y-3 pt-4">
                  <Skeleton className="h-5 w-40" />
                  <Skeleton className="h-16 w-full" />
                  <Skeleton className="h-16 w-full" />
                  <Skeleton className="h-16 w-full" />
                </div>
              </div>
            ) : error ? (
              <ErrorMessage
                title="SHAP Attribution Failed"
                message={error}
                onRetry={() => selectedTxId && fetchExplanation(selectedTxId)}
              />
            ) : explanation ? (
              <>
                {/* Risk Summary Banner */}
                <div className="p-5 bg-surface-elevated/80 border border-surface-border rounded-xl space-y-4">
                  <div className="flex items-center justify-between">
                    <div>
                      <span className="text-xs uppercase tracking-wider text-slate-400 font-semibold block">
                        Assessed Risk Classification
                      </span>
                      <div className="mt-1 flex items-center gap-2">
                        <span className="text-2xl font-bold font-mono text-white">
                          {explanation.risk_score.toFixed(2)}
                        </span>
                        <span className="text-xs text-slate-400 font-mono">/ 100</span>
                      </div>
                    </div>
                    <RiskBadge band={explanation.risk_band} size="lg" />
                  </div>

                  <div className="grid grid-cols-2 gap-3 pt-3 border-t border-surface-border text-xs">
                    <div>
                      <span className="text-slate-400 block">Model Fraud Probability</span>
                      <span className="font-mono font-semibold text-white text-sm">
                        {(explanation.fraud_probability * 100).toFixed(2)}%
                      </span>
                    </div>
                    <div>
                      <span className="text-slate-400 block">Explainability Engine</span>
                      <span className="font-mono font-medium text-slate-200">
                        {explanation.method} {explanation.is_cached && '(Cached)'}
                      </span>
                    </div>
                  </div>
                </div>

                {/* Explainability Section */}
                <div className="space-y-3">
                  <div className="flex items-center gap-2">
                    <Cpu className="w-4 h-4 text-rose-400" />
                    <h3 className="text-sm font-bold text-white uppercase tracking-wider">
                      Why Was This Transaction Flagged?
                    </h3>
                  </div>
                  <p className="text-xs text-slate-400 leading-relaxed">
                    Local SHAP (SHapley Additive exPlanations) isolates each attribute's exact contribution
                    pushing the risk score higher or lower relative to the baseline population expectation.
                  </p>

                  <SHAPWaterfall
                    positiveFactors={explanation.positive_contributions}
                    negativeFactors={explanation.negative_contributions}
                    baseValue={explanation.base_value}
                  />
                </div>
              </>
            ) : null}
          </div>

          {/* Drawer Footer */}
          <div className="p-4 border-t border-surface-border bg-surface-elevated/30 flex justify-end">
            <button
              onClick={closeInvestigation}
              className="px-4 py-2 text-xs font-semibold text-slate-300 hover:text-white bg-surface-elevated hover:bg-surface-hover border border-surface-border rounded-lg transition-colors cursor-pointer"
            >
              Close Investigation
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};
