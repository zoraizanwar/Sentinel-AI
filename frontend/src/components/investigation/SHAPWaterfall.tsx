import React from 'react';
import { SHAPContribution } from '../../types/api';
import { TrendingUp, TrendingDown } from 'lucide-react';

interface SHAPWaterfallProps {
  positiveFactors: SHAPContribution[];
  negativeFactors: SHAPContribution[];
  baseValue?: number;
}

export const SHAPWaterfall: React.FC<SHAPWaterfallProps> = ({
  positiveFactors,
  negativeFactors,
}) => {
  const allFactors = [
    ...positiveFactors.map((f) => ({ ...f, isPositive: true })),
    ...negativeFactors.map((f) => ({ ...f, isPositive: false })),
  ];

  if (allFactors.length === 0) {
    return (
      <div className="p-4 bg-surface-elevated/40 rounded-xl border border-surface-border text-center text-xs text-slate-400">
        No significant individual SHAP feature deviations detected.
      </div>
    );
  }

  // Find max absolute SHAP value for scaling bars
  const maxVal = Math.max(...allFactors.map((f) => Math.abs(f.shap_value)), 0.001);

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between text-xs text-slate-400 border-b border-surface-border pb-2">
        <span className="font-semibold uppercase tracking-wider">Feature Factor</span>
        <span className="font-mono">SHAP Attribution</span>
      </div>

      <div className="space-y-3">
        {/* Risk Increasing Factors */}
        {positiveFactors.length > 0 && (
          <div className="space-y-2">
            <div className="flex items-center gap-1.5 text-xs font-semibold text-rose-400">
              <TrendingUp className="w-3.5 h-3.5" />
              <span>Risk Escalators (Increases Fraud Score)</span>
            </div>
            {positiveFactors.map((factor, idx) => {
              const pct = Math.min(100, Math.round((Math.abs(factor.shap_value) / maxVal) * 100));
              return (
                <div
                  key={idx}
                  className="bg-surface-elevated/60 border border-surface-border rounded-lg p-3 hover:border-rose-500/30 transition-colors"
                >
                  <div className="flex justify-between items-start">
                    <div>
                      <span className="text-xs font-mono font-semibold text-white">
                        {factor.feature_name}
                      </span>
                      {factor.feature_value !== undefined && (
                        <span className="ml-2 text-[11px] text-slate-400 font-mono">
                          = {String(factor.feature_value)}
                        </span>
                      )}
                    </div>
                    <span className="text-xs font-mono font-bold text-rose-400">
                      +{factor.shap_value.toFixed(4)}
                    </span>
                  </div>

                  {/* Horizontal Bar */}
                  <div className="w-full bg-surface-subtle/40 rounded-full h-1.5 mt-2 overflow-hidden">
                    <div
                      className="bg-rose-500 h-1.5 rounded-full transition-all duration-500"
                      style={{ width: `${pct}%` }}
                    />
                  </div>

                  <p className="text-[11px] text-slate-300 mt-1.5 leading-snug">
                    {factor.human_explanation}
                  </p>
                </div>
              );
            })}
          </div>
        )}

        {/* Risk Mitigating Factors */}
        {negativeFactors.length > 0 && (
          <div className="space-y-2 pt-2">
            <div className="flex items-center gap-1.5 text-xs font-semibold text-emerald-400">
              <TrendingDown className="w-3.5 h-3.5" />
              <span>Risk Mitigators (Decreases Fraud Score)</span>
            </div>
            {negativeFactors.map((factor, idx) => {
              const pct = Math.min(100, Math.round((Math.abs(factor.shap_value) / maxVal) * 100));
              return (
                <div
                  key={idx}
                  className="bg-surface-elevated/60 border border-surface-border rounded-lg p-3 hover:border-emerald-500/30 transition-colors"
                >
                  <div className="flex justify-between items-start">
                    <div>
                      <span className="text-xs font-mono font-semibold text-white">
                        {factor.feature_name}
                      </span>
                      {factor.feature_value !== undefined && (
                        <span className="ml-2 text-[11px] text-slate-400 font-mono">
                          = {String(factor.feature_value)}
                        </span>
                      )}
                    </div>
                    <span className="text-xs font-mono font-bold text-emerald-400">
                      {factor.shap_value.toFixed(4)}
                    </span>
                  </div>

                  {/* Horizontal Bar */}
                  <div className="w-full bg-surface-subtle/40 rounded-full h-1.5 mt-2 overflow-hidden">
                    <div
                      className="bg-emerald-500 h-1.5 rounded-full transition-all duration-500"
                      style={{ width: `${pct}%` }}
                    />
                  </div>

                  <p className="text-[11px] text-slate-300 mt-1.5 leading-snug">
                    {factor.human_explanation}
                  </p>
                </div>
              );
            })}
          </div>
        )}
      </div>
    </div>
  );
};
