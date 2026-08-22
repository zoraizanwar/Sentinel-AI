import React from 'react';
import { useNavigate, useLocation } from 'react-router-dom';
import { UploadCloud, RefreshCw, Trash2, LogOut } from 'lucide-react';
import { useAnalysis } from '../../context/AnalysisContext';
import { useAuth } from '../../context/AuthContext';

export const Header: React.FC = () => {
  const { analysisId, analysisResult, clearAnalysis, loadAnalysis, isAnalyzing } = useAnalysis();
  const { user, logout } = useAuth();
  const navigate = useNavigate();
  const location = useLocation();

  const getPageTitle = () => {
    switch (location.pathname) {
      case '/org-dashboard':
        return 'Organization Portfolio Dashboard';
      case '/clients':
        return 'Institutional Client Management';
      case '/analyses':
        return 'Historical ML Analyses';
      case '/audit-logs':
        return 'Compliance & Audit Trail';
      case '/settings':
        return 'Tenant Settings & Access Control';
      case '/':
        return 'Fraud Analysis Overview';
      case '/transactions':
        return 'Transaction Explorer & Query Engine';
      case '/analytics':
        return 'Fraud Risk Analytics & Patterns';
      case '/investigation':
        return 'Investigation Workspace & Explainable AI';
      case '/dataset':
        return 'Dataset Health & ML Model Architecture';
      case '/reports':
        return 'Executive Audit Reports';
      case '/upload':
        return 'Dataset Ingestion & Inspection';
      default:
        return 'Sentinel Risk Intelligence';
    }
  };

  const handleLogout = () => {
    logout();
    navigate('/login');
  };

  return (
    <header className="h-16 bg-surface/80 backdrop-blur border-b border-surface-border sticky top-0 z-30 px-8 flex items-center justify-between">
      <div>
        <h1 className="text-base font-semibold text-white tracking-tight flex items-center gap-2">
          {getPageTitle()}
        </h1>
        {analysisResult && (
          <p className="text-xs text-slate-400 font-mono">
            {analysisResult.dataset_summary.dataset_name} •{' '}
            {analysisResult.fraud_statistics.total_transactions.toLocaleString()} rows •{' '}
            Model: {analysisResult.model_results.selected_model.model_name}
          </p>
        )}
      </div>

      <div className="flex items-center gap-4">
        {analysisId && (
          <>
            <button
              onClick={() => loadAnalysis(analysisId)}
              className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-medium text-slate-300 hover:text-white bg-surface-elevated hover:bg-surface-hover border border-surface-border transition-colors cursor-pointer"
              title="Refresh Session Data"
            >
              <RefreshCw className="w-3.5 h-3.5" />
              Refresh
            </button>
            <button
              onClick={() => {
                clearAnalysis();
                navigate('/upload');
              }}
              className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-medium text-rose-300 hover:text-rose-200 bg-rose-500/10 hover:bg-rose-500/20 border border-rose-500/20 transition-colors cursor-pointer"
              title="Clear Current Analysis Session"
            >
              <Trash2 className="w-3.5 h-3.5" />
              Clear
            </button>
          </>
        )}

        <button
          onClick={() => navigate('/upload')}
          disabled={isAnalyzing}
          className="inline-flex items-center gap-1.5 px-3.5 py-1.5 rounded-lg text-xs font-semibold text-white bg-rose-600 hover:bg-rose-500 shadow-md shadow-rose-950/40 transition-all cursor-pointer disabled:opacity-50"
        >
          <UploadCloud className="w-3.5 h-3.5" />
          Ingest Dataset
        </button>

        {/* User Profile & Logout */}
        {user && (
          <div className="flex items-center gap-3 pl-4 border-l border-surface-border">
            <div className="text-right">
              <div className="text-xs font-bold text-white">{user.full_name}</div>
              <div className="text-[10px] font-mono text-slate-400">{user.email}</div>
            </div>
            <button
              onClick={handleLogout}
              className="p-1.5 rounded-lg text-slate-400 hover:text-rose-400 hover:bg-rose-500/10 border border-transparent hover:border-rose-500/20 transition-colors cursor-pointer"
              title="Sign Out"
            >
              <LogOut className="w-4 h-4" />
            </button>
          </div>
        )}
      </div>
    </header>
  );
};
