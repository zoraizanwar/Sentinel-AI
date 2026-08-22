import React, { useState, useRef, useEffect } from 'react';
import { useNavigate, useSearchParams } from 'react-router-dom';
import {
  UploadCloud,
  FileCheck,
  AlertTriangle,
  Cpu,
  ArrowRight,
  Building2,
  CheckCircle2,
} from 'lucide-react';
import { useAnalysis } from '../context/AnalysisContext';
import { useWorkspace } from '../context/WorkspaceContext';
import { useAuth } from '../context/AuthContext';
import { DatasetInspectionResult } from '../types/api';
import { ErrorMessage } from '../components/common/ErrorMessage';
import { uploadClientDataset, runPersistentAnalysis } from '../api/endpoints';
import { extractApiError } from '../api/client';

export const UploadView: React.FC = () => {
  const {
    inspectFile,
    executeAnalysis,
    setAnalysisResultDirectly,
    isInspecting,
    isAnalyzing,
    analysisStage,
    error: sessionError,
  } = useAnalysis();
  const { clients, refreshWorkspace, refreshAnalyses, loadAnalysisDetail } = useWorkspace();
  const { activeOrgId } = useAuth();
  const [searchParams] = useSearchParams();
  const navigate = useNavigate();

  const [selectedClient, setSelectedClient] = useState<string>('');
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [inspection, setInspection] = useState<DatasetInspectionResult | null>(null);
  const [dragActive, setDragActive] = useState(false);
  const [persistentProcessing, setPersistentProcessing] = useState(false);
  const [processingStage, setProcessingStage] = useState<string>('');
  const [customError, setCustomError] = useState<string | null>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);

  useEffect(() => {
    const urlClientId = searchParams.get('clientId');
    if (urlClientId) {
      setSelectedClient(urlClientId);
    } else if (clients.length > 0 && !selectedClient) {
      setSelectedClient(clients[0].id);
    }
  }, [clients, searchParams]);

  const handleFileChange = async (file: File) => {
    if (!file.name.toLowerCase().endsWith('.csv')) {
      alert('Only .csv files are supported.');
      return;
    }
    setSelectedFile(file);
    const result = await inspectFile(file);
    if (result) {
      setInspection(result);
    }
  };

  const handleDrag = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    if (e.type === 'dragenter' || e.type === 'dragover') {
      setDragActive(true);
    } else if (e.type === 'dragleave') {
      setDragActive(false);
    }
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setDragActive(false);
    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      handleFileChange(e.dataTransfer.files[0]);
    }
  };

  const handleStartAnalysis = async () => {
    if (!selectedFile) return;

    if (activeOrgId && selectedClient) {
      // Execute multi-tenant persistent ingestion & analysis pipeline
      setPersistentProcessing(true);
      setCustomError(null);
      try {
        setProcessingStage('1/3 Uploading & Validating Dataset into Client Repository...');
        const dataset = await uploadClientDataset(activeOrgId, selectedClient, selectedFile);

        setProcessingStage('2/3 Training Baseline, Random Forest & XGBoost Models on Localhost...');
        const analysis = await runPersistentAnalysis(activeOrgId, selectedClient, dataset.id);

        setProcessingStage('3/3 Deriving SHAP Explanations & Risk Intelligence Telemetry...');
        await Promise.all([refreshWorkspace(), refreshAnalyses()]);
        const detail = await loadAnalysisDetail(analysis.id);
        if (detail) {
          setAnalysisResultDirectly(detail);
        }

        navigate('/');
      } catch (err) {
        const apiErr = extractApiError(err);
        setCustomError(apiErr.message);
      } finally {
        setPersistentProcessing(false);
      }
    } else {
      // Fallback to in-memory analysis pipeline
      const result = await executeAnalysis(selectedFile);
      if (result) {
        navigate('/');
      }
    }
  };

  const isBusy = isAnalyzing || persistentProcessing;

  return (
    <div className="max-w-4xl mx-auto space-y-8">
      {/* Page Header */}
      <div className="text-center space-y-2">
        <h2 className="text-2xl font-bold text-white tracking-tight">
          Dataset Ingestion & Machine Learning Execution
        </h2>
        <p className="text-xs text-slate-400 max-w-lg mx-auto leading-relaxed">
          Select target client institution, upload transaction CSV records, and trigger pre-flight schema audit,
          leak-free preprocessing, candidate model benchmarking, and persistent risk calibration.
        </p>
      </div>

      {(sessionError || customError) && (
        <ErrorMessage message={customError || sessionError || 'An error occurred'} />
      )}

      {/* Step 1: Client Selection */}
      {!isBusy && clients.length > 0 && (
        <div className="bg-surface rounded-2xl border border-surface-border p-6 shadow-sm">
          <label className="block text-xs font-semibold uppercase tracking-wider text-slate-300 mb-2 flex items-center gap-2">
            <Building2 className="w-4 h-4 text-rose-500" /> Target Client Institution
          </label>
          <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 gap-3">
            {clients.map((c) => (
              <div
                key={c.id}
                onClick={() => setSelectedClient(c.id)}
                className={`p-3.5 rounded-xl border transition-all cursor-pointer flex items-center justify-between ${
                  selectedClient === c.id
                    ? 'border-rose-500 bg-rose-500/10 text-white'
                    : 'border-surface-border bg-surface-elevated text-slate-400 hover:border-slate-500'
                }`}
              >
                <div>
                  <div className="text-xs font-bold font-sans text-white">{c.name}</div>
                  <div className="text-[10px] font-mono text-slate-400">{c.client_code}</div>
                </div>
                {selectedClient === c.id && <CheckCircle2 className="w-4 h-4 text-rose-500 shrink-0" />}
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Step 2: Upload Dropzone */}
      {!isBusy && (
        <div
          onDragEnter={handleDrag}
          onDragLeave={handleDrag}
          onDragOver={handleDrag}
          onDrop={handleDrop}
          onClick={() => fileInputRef.current?.click()}
          className={`bg-surface border-2 border-dashed rounded-2xl p-10 text-center cursor-pointer transition-all duration-200 ${
            dragActive
              ? 'border-rose-500 bg-rose-500/5'
              : 'border-surface-subtle hover:border-surface-hover hover:bg-surface-elevated/40'
          }`}
        >
          <input
            ref={fileInputRef}
            type="file"
            accept=".csv"
            onChange={(e) => e.target.files?.[0] && handleFileChange(e.target.files[0])}
            className="hidden"
          />
          <div className="w-14 h-14 rounded-2xl bg-surface-elevated border border-surface-border text-rose-400 mx-auto flex items-center justify-center mb-4 shadow-inner">
            <UploadCloud className="w-7 h-7" />
          </div>
          <h3 className="text-sm font-bold text-white">
            {selectedFile ? selectedFile.name : 'Drop transaction CSV file here or browse'}
          </h3>
          <p className="text-xs text-slate-400 mt-1">
            Accepts CSV format up to 500 MB (e.g. Kaggle Credit Card Fraud dataset)
          </p>
          {isInspecting && (
            <p className="text-xs font-mono text-amber-400 mt-3 animate-pulse">
              Running pre-flight structural inspection & data quality audit...
            </p>
          )}
        </div>
      )}

      {/* Analyzing Progress State */}
      {isBusy && (
        <div className="bg-surface rounded-2xl border border-rose-500/30 p-10 text-center space-y-6 shadow-xl shadow-rose-950/20">
          <div className="w-16 h-16 rounded-2xl bg-rose-500/15 border border-rose-500/30 text-rose-400 mx-auto flex items-center justify-center animate-pulse">
            <Cpu className="w-8 h-8" />
          </div>
          <div className="space-y-2">
            <h3 className="text-lg font-bold text-white tracking-tight">
              Executing Multi-Tenant Machine Learning Pipeline
            </h3>
            <p className="text-xs text-rose-300 font-mono animate-pulse">
              {processingStage || analysisStage || 'Training models & calibrating risk thresholds...'}
            </p>
          </div>

          <div className="w-full bg-surface-elevated rounded-full h-2 overflow-hidden max-w-md mx-auto">
            <div className="bg-gradient-to-r from-rose-600 to-amber-500 h-2 rounded-full animate-indeterminate" />
          </div>

          <p className="text-[11px] text-slate-400 max-w-sm mx-auto">
            Fitting leak-free transformers on train partition, computing PR-AUC curves, scoring transactions, and storing persistent audit records in local database.
          </p>
        </div>
      )}

      {/* Pre-flight Inspection Results & Confirmation */}
      {inspection && !isBusy && (
        <div className="bg-surface rounded-xl border border-surface-border p-6 space-y-6">
          <div className="flex items-center justify-between border-b border-surface-border pb-4">
            <div className="flex items-center gap-2">
              <FileCheck className="w-5 h-5 text-emerald-400" />
              <h3 className="text-sm font-bold text-white uppercase tracking-wider">
                Pre-Flight Data Quality Audit
              </h3>
            </div>
            <span
              className={`text-xs font-mono font-semibold px-2.5 py-1 rounded-full ${
                inspection.validation_status === 'VALID'
                  ? 'bg-emerald-500/15 text-emerald-400 border border-emerald-500/30'
                  : 'bg-amber-500/15 text-amber-400 border border-amber-500/30'
              }`}
            >
              STATUS: {inspection.validation_status}
            </span>
          </div>

          {/* Quick Metrics Grid */}
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 text-xs font-mono">
            <div className="p-3 bg-surface-elevated/60 rounded-lg border border-surface-border">
              <span className="text-slate-400 block text-[10px]">TOTAL ROWS</span>
              <span className="text-sm font-bold text-white mt-1 block">
                {inspection.row_count.toLocaleString()}
              </span>
            </div>
            <div className="p-3 bg-surface-elevated/60 rounded-lg border border-surface-border">
              <span className="text-slate-400 block text-[10px]">COLUMNS</span>
              <span className="text-sm font-bold text-white mt-1 block">
                {inspection.column_count}
              </span>
            </div>
            <div className="p-3 bg-surface-elevated/60 rounded-lg border border-surface-border">
              <span className="text-slate-400 block text-[10px]">TARGET DETECTED</span>
              <span className="text-sm font-bold text-emerald-400 mt-1 block truncate">
                {inspection.target_column || 'None'}
              </span>
            </div>
            <div className="p-3 bg-surface-elevated/60 rounded-lg border border-surface-border">
              <span className="text-slate-400 block text-[10px]">IMBALANCE RATIO</span>
              <span className="text-sm font-bold text-amber-400 mt-1 block">
                {inspection.class_distribution ? `${inspection.class_distribution.imbalance_ratio.toFixed(1)}:1` : 'N/A'}
              </span>
            </div>
          </div>

          {/* Warnings List if any */}
          {inspection.warnings.length > 0 && (
            <div className="space-y-2">
              <span className="text-xs font-semibold text-amber-400 flex items-center gap-1">
                <AlertTriangle className="w-3.5 h-3.5" />
                Data Quality Warnings ({inspection.warnings.length})
              </span>
              <div className="space-y-1.5">
                {inspection.warnings.map((w, idx) => (
                  <div
                    key={idx}
                    className="p-2.5 bg-amber-500/10 border border-amber-500/20 rounded text-xs text-amber-200/90 leading-snug"
                  >
                    {w.message}
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Action CTA */}
          <div className="pt-4 border-t border-surface-border flex justify-end">
            <button
              onClick={handleStartAnalysis}
              className="inline-flex items-center gap-2 px-6 py-2.5 text-xs font-bold text-white bg-rose-600 hover:bg-rose-500 rounded-lg shadow-lg shadow-rose-950/40 transition-colors cursor-pointer"
            >
              <span>Run Machine Learning Analysis</span>
              <ArrowRight className="w-4 h-4" />
            </button>
          </div>
        </div>
      )}
    </div>
  );
};
