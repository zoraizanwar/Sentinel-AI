import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { FileText, Download, AlertCircle, CheckCircle2 } from 'lucide-react';
import { useAnalysis } from '../context/AnalysisContext';
import { useAuth } from '../context/AuthContext';
import { generatePdfReport, generateOrgReport, downloadOrgReport } from '../api/endpoints';
import { EmptyState } from '../components/common/EmptyState';
import { extractApiError } from '../api/client';

export const Reports: React.FC = () => {
  const { analysisResult, analysisId } = useAnalysis();
  let activeOrgId: string | null = null;
  try {
    const auth = useAuth();
    activeOrgId = auth.activeOrgId;
  } catch {
    activeOrgId = localStorage.getItem('sentinel_active_org_id');
  }
  const navigate = useNavigate();
  const [isGenerating, setIsGenerating] = useState(false);
  const [pdfMessage, setPdfMessage] = useState<{ type: 'success' | 'error'; text: string } | null>(null);

  const handleGeneratePdf = async () => {
    if (!analysisId) return;
    setIsGenerating(true);
    setPdfMessage(null);
    try {
      let blob: Blob | null = null;
      if (activeOrgId) {
        try {
          const rep = await generateOrgReport(activeOrgId, {
            report_type: 'ANALYSIS',
            analysis_id: analysisId,
            title: `Executive Fraud Intelligence Audit — ${analysisId.slice(0, 8)}`
          });
          blob = await downloadOrgReport(activeOrgId, rep.id);
        } catch {
          // fallback
        }
      }
      if (!blob) {
        blob = await generatePdfReport(analysisId);
      }
      const url = window.URL.createObjectURL(blob);
      const link = document.createElement('a');
      link.href = url;
      link.setAttribute('download', `sentinel_ai_fraud_intelligence_report_${analysisId}.pdf`);
      document.body.appendChild(link);
      link.click();
      link.parentNode?.removeChild(link);
      window.URL.revokeObjectURL(url);

      setPdfMessage({
        type: 'success',
        text: 'Executive PDF report successfully compiled and downloaded.',
      });
    } catch (err) {
      const apiErr = extractApiError(err);
      if (apiErr.statusCode === 404) {
        setPdfMessage({
          type: 'error',
          text: 'Analysis session has expired or no longer exists. Please re-upload dataset.',
        });
      } else {
        setPdfMessage({
          type: 'error',
          text: apiErr.message || 'Failed to generate PDF report. Please try again.',
        });
      }
    } finally {
      setIsGenerating(false);
    }
  };

  if (!analysisResult) {
    return (
      <EmptyState
        title="No Active Dataset Loaded"
        description="Upload a transaction dataset to preview the executive risk report and export analytical summaries."
        actionLabel="Upload Dataset"
        onAction={() => navigate('/upload')}
      />
    );
  }

  const { fraud_statistics: fraud, risk_statistics: risk, findings, recommendations } = analysisResult;

  return (
    <div className="space-y-8 max-w-4xl mx-auto">
      {/* Report Header Card */}
      <div className="bg-surface rounded-xl border border-surface-border p-6 flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 rounded-xl bg-rose-500/15 border border-rose-500/30 flex items-center justify-center text-rose-400">
            <FileText className="w-5 h-5" />
          </div>
          <div>
            <h2 className="text-base font-bold text-white tracking-tight">
              Executive Fraud Risk Audit Report
            </h2>
            <p className="text-xs text-slate-400 font-mono">
              Session ID: {analysisId} • Generated: {new Date(analysisResult.created_at).toLocaleDateString()}
            </p>
          </div>
        </div>

        <button
          onClick={handleGeneratePdf}
          disabled={isGenerating}
          className="inline-flex items-center gap-2 px-5 py-2.5 text-xs font-bold text-white bg-rose-600 hover:bg-rose-500 rounded-lg shadow-md shadow-rose-950/40 transition-colors disabled:opacity-50 cursor-pointer"
        >
          <Download className="w-4 h-4" />
          {isGenerating ? 'Compiling PDF Report...' : 'Generate PDF Audit Report'}
        </button>
      </div>

      {/* Notification Message */}
      {pdfMessage && (
        <div
          className={`p-4 rounded-xl border flex items-start gap-3 text-xs leading-relaxed ${
            pdfMessage.type === 'success'
              ? 'bg-emerald-500/10 border-emerald-500/30 text-emerald-200'
              : 'bg-rose-500/10 border-rose-500/30 text-rose-200'
          }`}
        >
          {pdfMessage.type === 'success' ? (
            <CheckCircle2 className="w-4 h-4 text-emerald-400 shrink-0 mt-0.5" />
          ) : (
            <AlertCircle className="w-4 h-4 text-rose-400 shrink-0 mt-0.5" />
          )}
          <div>
            <span className="font-semibold block text-white mb-0.5">Report Engine</span>
            <span>{pdfMessage.text}</span>
          </div>
        </div>
      )}

      {/* Document Preview Container */}
      <div className="bg-surface rounded-xl border border-surface-border p-8 space-y-8 shadow-sm">
        {/* Section 1: Executive Summary */}
        <div className="space-y-3 pb-6 border-b border-surface-border">
          <h3 className="text-xs font-bold uppercase tracking-wider text-rose-400 font-mono">
            01. Executive Overview & Prevalence
          </h3>
          <p className="text-xs text-slate-300 leading-relaxed">
            The automated risk intelligence audit analyzed a total of{' '}
            <strong className="text-white font-mono">{fraud.total_transactions.toLocaleString()}</strong> financial
            transactions. The system identified <strong className="text-rose-400 font-mono">{fraud.fraud_count.toLocaleString()}</strong> confirmed
            fraud attacks ({fraud.fraud_rate_percentage.toFixed(3)}% prevalence), exposing a direct financial liability of{' '}
            <strong className="text-white font-mono">${fraud.fraud_volume_usd.toLocaleString()} USD</strong> (
            {fraud.fraud_loss_percentage.toFixed(2)}% of total processed gross volume).
          </p>
        </div>

        {/* Section 2: Calibrated Risk Distribution */}
        <div className="space-y-3 pb-6 border-b border-surface-border">
          <h3 className="text-xs font-bold uppercase tracking-wider text-amber-400 font-mono">
            02. Risk Band Segmentation
          </h3>
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 text-xs font-mono">
            <div className="p-3 bg-surface-elevated/40 rounded-lg border border-surface-border">
              <span className="text-slate-400 block text-[10px]">LOW (0-20)</span>
              <span className="text-white font-bold mt-1 block">{risk.low_risk_count.toLocaleString()} ({risk.low_risk_pct}%)</span>
            </div>
            <div className="p-3 bg-surface-elevated/40 rounded-lg border border-surface-border">
              <span className="text-slate-400 block text-[10px]">MEDIUM (20-50)</span>
              <span className="text-white font-bold mt-1 block">{risk.medium_risk_count.toLocaleString()} ({risk.medium_risk_pct}%)</span>
            </div>
            <div className="p-3 bg-surface-elevated/40 rounded-lg border border-surface-border">
              <span className="text-slate-400 block text-[10px]">HIGH (50-80)</span>
              <span className="text-orange-400 font-bold mt-1 block">{risk.high_risk_count.toLocaleString()} ({risk.high_risk_pct}%)</span>
            </div>
            <div className="p-3 bg-surface-elevated/40 rounded-lg border border-surface-border">
              <span className="text-slate-400 block text-[10px]">CRITICAL (80-100)</span>
              <span className="text-rose-400 font-bold mt-1 block">{risk.critical_risk_count.toLocaleString()} ({risk.critical_risk_pct}%)</span>
            </div>
          </div>
        </div>

        {/* Section 3: Empirical Findings */}
        <div className="space-y-3 pb-6 border-b border-surface-border">
          <h3 className="text-xs font-bold uppercase tracking-wider text-slate-300 font-mono">
            03. Verified Empirical Findings
          </h3>
          <div className="space-y-2">
            {findings.map((f) => (
              <div key={f.finding_id} className="p-3 bg-surface-elevated/40 rounded-lg border border-surface-border text-xs">
                <span className="font-semibold text-white block">{f.title}</span>
                <p className="text-slate-400 mt-1">{f.description}</p>
              </div>
            ))}
          </div>
        </div>

        {/* Section 4: Operational Recommendations */}
        <div className="space-y-3">
          <h3 className="text-xs font-bold uppercase tracking-wider text-emerald-400 font-mono">
            04. Actionable Security Actions
          </h3>
          <div className="space-y-2">
            {recommendations.map((r) => (
              <div key={r.recommendation_id} className="p-3 bg-surface-elevated/40 rounded-lg border border-surface-border text-xs">
                <div className="flex justify-between items-center">
                  <span className="font-semibold text-white">{r.title}</span>
                  <span className="text-[10px] font-mono font-bold text-rose-400 uppercase bg-rose-500/10 px-2 py-0.5 rounded">
                    {r.priority} PRIORITY
                  </span>
                </div>
                <p className="text-slate-300 mt-1">{r.action}</p>
                <p className="text-[11px] text-slate-400 mt-1">Rationale: {r.rationale}</p>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
};
