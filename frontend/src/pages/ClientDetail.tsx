import React, { useEffect, useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import {
  Database,
  Activity,
  AlertTriangle,
  DollarSign,
  ArrowLeft,
  UploadCloud,
  FileText,
} from 'lucide-react';
import { useWorkspace } from '../context/WorkspaceContext';
import { useAuth } from '../context/AuthContext';
import { getClientDatasets, generateOrgReport } from '../api/endpoints';
import { Dataset } from '../types/api';

export const ClientDetail: React.FC = () => {
  const { clientId } = useParams<{ clientId: string }>();
  const { clients, clientDashboard, loadClientDashboard } = useWorkspace();
  const { activeRole, activeOrgId } = useAuth();
  const navigate = useNavigate();

  const [datasets, setDatasets] = useState<Dataset[]>([]);
  const [isGeneratingReport, setIsGeneratingReport] = useState(false);

  const client = clients.find((c) => c.id === clientId);

  useEffect(() => {
    if (clientId) {
      loadClientDashboard(clientId);
      if (activeOrgId) {
        getClientDatasets(activeOrgId, clientId).then(setDatasets).catch(console.error);
      }
    }
  }, [clientId, activeOrgId]);

  const handleGenerateReport = async () => {
    if (!activeOrgId || !clientId) return;
    setIsGeneratingReport(true);
    try {
      await generateOrgReport(activeOrgId, {
        client_id: clientId,
        report_type: 'CLIENT',
        title: `${client?.name || 'Client'} Fraud Intelligence Audit Report`,
      });
      navigate('/reports');
    } catch (err) {
      console.error(err);
    } finally {
      setIsGeneratingReport(false);
    }
  };

  const canUpload = activeRole === 'ORGANIZATION_ADMIN' || activeRole === 'ANALYST';

  return (
    <div className="space-y-8 max-w-7xl mx-auto">
      {/* Back Button */}
      <button
        onClick={() => navigate('/clients')}
        className="inline-flex items-center gap-2 text-xs font-medium text-slate-400 hover:text-white cursor-pointer"
      >
        <ArrowLeft className="w-4 h-4" /> Back to Client Portfolio
      </button>

      {/* Header Banner */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 bg-surface p-6 rounded-2xl border border-surface-border">
        <div className="flex items-center gap-4">
          <div className="w-12 h-12 rounded-2xl bg-gradient-to-br from-rose-500 to-rose-700 text-white flex items-center justify-center font-mono font-bold text-lg shadow-lg shadow-rose-950/40">
            {client?.client_code.slice(0, 3) || 'CLI'}
          </div>
          <div>
            <div className="flex items-center gap-3">
              <h2 className="text-xl font-bold text-white tracking-tight">
                {client?.name || 'Client Details'}
              </h2>
              <span className="px-2.5 py-0.5 rounded-full text-[10px] font-semibold bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">
                {client?.status || 'ACTIVE'}
              </span>
            </div>
            <p className="text-xs font-mono text-slate-400 mt-1">
              Code: {client?.client_code} • Industry: {client?.industry || 'Financial Services'}
            </p>
          </div>
        </div>

        <div className="flex items-center gap-3">
          <button
            onClick={handleGenerateReport}
            disabled={isGeneratingReport}
            className="inline-flex items-center gap-2 px-4 py-2 bg-surface-elevated hover:bg-surface-hover text-white rounded-xl text-xs font-semibold border border-surface-border transition-colors cursor-pointer disabled:opacity-50"
          >
            <FileText className="w-4 h-4 text-slate-400" />
            {isGeneratingReport ? 'Generating PDF...' : 'Client Report PDF'}
          </button>
          {canUpload && (
            <button
              onClick={() => navigate(`/upload?clientId=${clientId}`)}
              className="inline-flex items-center gap-2 px-4 py-2 bg-rose-600 hover:bg-rose-500 text-white rounded-xl text-xs font-semibold shadow-md shadow-rose-950/40 transition-all cursor-pointer"
            >
              <UploadCloud className="w-4 h-4" />
              Upload Dataset
            </button>
          )}
        </div>
      </div>

      {/* KPI Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <div className="bg-surface p-5 rounded-xl border border-surface-border shadow-sm">
          <div className="flex items-center justify-between text-slate-400 mb-2">
            <span className="text-xs font-medium uppercase tracking-wider">Datasets</span>
            <Database className="w-4 h-4 text-sky-400" />
          </div>
          <div className="text-2xl font-bold text-white font-mono">
            {clientDashboard?.total_datasets ?? datasets.length}
          </div>
          <p className="text-[11px] text-slate-400 mt-1">Uploaded transactions datasets</p>
        </div>

        <div className="bg-surface p-5 rounded-xl border border-surface-border shadow-sm">
          <div className="flex items-center justify-between text-slate-400 mb-2">
            <span className="text-xs font-medium uppercase tracking-wider">Transactions</span>
            <Activity className="w-4 h-4 text-indigo-400" />
          </div>
          <div className="text-2xl font-bold text-white font-mono">
            {(clientDashboard?.total_transactions ?? 0).toLocaleString()}
          </div>
          <p className="text-[11px] text-slate-400 mt-1">Total analyzed records</p>
        </div>

        <div className="bg-surface p-5 rounded-xl border border-surface-border shadow-sm">
          <div className="flex items-center justify-between text-slate-400 mb-2">
            <span className="text-xs font-medium uppercase tracking-wider">Fraud Detected</span>
            <AlertTriangle className="w-4 h-4 text-rose-400" />
          </div>
          <div className="text-2xl font-bold text-rose-400 font-mono">
            {(clientDashboard?.total_fraud_detected ?? 0).toLocaleString()}
          </div>
          <p className="text-[11px] text-slate-400 mt-1">
            Rate: {clientDashboard?.fraud_rate_pct ? `${clientDashboard.fraud_rate_pct.toFixed(2)}%` : '0.00%'}
          </p>
        </div>

        <div className="bg-surface p-5 rounded-xl border border-surface-border shadow-sm">
          <div className="flex items-center justify-between text-slate-400 mb-2">
            <span className="text-xs font-medium uppercase tracking-wider">Loss Prevented ($)</span>
            <DollarSign className="w-4 h-4 text-emerald-400" />
          </div>
          <div className="text-2xl font-bold text-emerald-400 font-mono">
            ${(clientDashboard?.fraud_loss_prevented_usd ?? 0).toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
          </div>
          <p className="text-[11px] text-slate-400 mt-1">Prevented loss volume</p>
        </div>
      </div>

      {/* Datasets Table */}
      <div className="bg-surface rounded-2xl border border-surface-border overflow-hidden shadow-sm">
        <div className="p-6 border-b border-surface-border flex items-center justify-between">
          <div>
            <h3 className="text-base font-semibold text-white">Client Ingested Datasets</h3>
            <p className="text-xs text-slate-400 mt-0.5">Isolated dataset files available for ML model analysis</p>
          </div>
        </div>

        {datasets.length === 0 ? (
          <div className="p-12 text-center">
            <Database className="w-12 h-12 text-slate-600 mx-auto mb-3" />
            <h4 className="text-sm font-medium text-slate-300">No datasets uploaded yet</h4>
            <p className="text-xs text-slate-500 mt-1">Upload a CSV file for {client?.name} to execute the ML pipeline.</p>
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs">
              <thead className="bg-surface-elevated/60 text-slate-400 uppercase tracking-wider font-semibold border-b border-surface-border">
                <tr>
                  <th className="py-3 px-6">Filename</th>
                  <th className="py-3 px-6 text-right">Rows</th>
                  <th className="py-3 px-6 text-right">Columns</th>
                  <th className="py-3 px-6 text-right">Fraud Rate</th>
                  <th className="py-3 px-6 text-center">Validation</th>
                  <th className="py-3 px-6 text-center">Status</th>
                  <th className="py-3 px-6 text-right">Action</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-surface-border/50 text-slate-300 font-mono">
                {datasets.map((d) => (
                  <tr key={d.id} className="hover:bg-surface-hover transition-colors">
                    <td className="py-3.5 px-6 font-sans text-white font-medium">{d.filename}</td>
                    <td className="py-3.5 px-6 text-right">{d.row_count.toLocaleString()}</td>
                    <td className="py-3.5 px-6 text-right">{d.column_count}</td>
                    <td className="py-3.5 px-6 text-right">{d.fraud_rate_percentage ? `${d.fraud_rate_percentage.toFixed(2)}%` : 'N/A'}</td>
                    <td className="py-3.5 px-6 text-center font-sans">
                      <span className="px-2 py-0.5 rounded-full text-[10px] font-semibold bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">
                        {d.validation_status}
                      </span>
                    </td>
                    <td className="py-3.5 px-6 text-center font-sans">
                      <span className="px-2 py-0.5 rounded-full text-[10px] font-semibold bg-blue-500/10 text-blue-400 border border-blue-500/20">
                        {d.processing_status}
                      </span>
                    </td>
                    <td className="py-3.5 px-6 text-right font-sans">
                      {d.processing_status === 'ANALYZED' ? (
                        <button
                          onClick={() => navigate('/analyses')}
                          className="text-xs text-rose-400 hover:text-rose-300 font-medium cursor-pointer"
                        >
                          View Analysis &rarr;
                        </button>
                      ) : (
                        <button
                          onClick={() => navigate(`/upload?clientId=${clientId}&datasetId=${d.id}`)}
                          className="text-xs text-emerald-400 hover:text-emerald-300 font-medium cursor-pointer"
                        >
                          Analyze &rarr;
                        </button>
                      )}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  );
};
