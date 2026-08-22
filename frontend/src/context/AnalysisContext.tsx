import React, { createContext, useContext, useState, useEffect, ReactNode } from 'react';
import { AnalysisResult, DatasetInspectionResult } from '../types/api';
import { inspectDataset, runAnalysis, getAnalysisResult, getAnalysisDetail } from '../api/endpoints';
import { extractApiError } from '../api/client';

interface AnalysisContextType {
  analysisId: string | null;
  analysisResult: AnalysisResult | null;
  inspectionResult: DatasetInspectionResult | null;
  isInspecting: boolean;
  isAnalyzing: boolean;
  analysisStage: string;
  error: string | null;
  selectedTxId: string | null;
  isDrawerOpen: boolean;
  inspectFile: (file: File) => Promise<DatasetInspectionResult | null>;
  executeAnalysis: (file: File) => Promise<AnalysisResult | null>;
  loadAnalysis: (id: string) => Promise<void>;
  setAnalysisResultDirectly: (result: AnalysisResult | null) => void;
  openInvestigation: (txId: string) => void;
  closeInvestigation: () => void;
  clearAnalysis: () => void;
}

const AnalysisContext = createContext<AnalysisContextType | undefined>(undefined);

const STORAGE_KEY = 'sentinel_active_analysis_id';

export const AnalysisProvider: React.FC<{ children: ReactNode }> = ({ children }) => {
  const [analysisId, setAnalysisId] = useState<string | null>(() => {
    return sessionStorage.getItem(STORAGE_KEY) || null;
  });
  const [analysisResult, setAnalysisResult] = useState<AnalysisResult | null>(null);
  const [inspectionResult, setInspectionResult] = useState<DatasetInspectionResult | null>(null);
  const [isInspecting, setIsInspecting] = useState(false);
  const [isAnalyzing, setIsAnalyzing] = useState(false);
  const [analysisStage, setAnalysisStage] = useState<string>('');
  const [error, setError] = useState<string | null>(null);
  const [selectedTxId, setSelectedTxId] = useState<string | null>(null);
  const [isDrawerOpen, setIsDrawerOpen] = useState(false);

  // Restore analysis from session storage if present
  useEffect(() => {
    if (analysisId && !analysisResult) {
      loadAnalysis(analysisId);
    }
  }, [analysisId]);

  const inspectFile = async (file: File): Promise<DatasetInspectionResult | null> => {
    setIsInspecting(true);
    setError(null);
    try {
      const result = await inspectDataset(file);
      setInspectionResult(result);
      return result;
    } catch (err) {
      const apiErr = extractApiError(err);
      setError(apiErr.message);
      return null;
    } finally {
      setIsInspecting(false);
    }
  };

  const executeAnalysis = async (file: File): Promise<AnalysisResult | null> => {
    setIsAnalyzing(true);
    setError(null);
    setAnalysisStage('Uploading dataset to Sentinel ML Engine...');

    // Progress simulation states for UX
    const stageTimer1 = setTimeout(() => setAnalysisStage('Validating schema and data quality...'), 1500);
    const stageTimer2 = setTimeout(() => setAnalysisStage('Engineering domain temporal & geospatial features...'), 4000);
    const stageTimer3 = setTimeout(() => setAnalysisStage('Fitting leak-free preprocessors on training split...'), 8000);
    const stageTimer4 = setTimeout(() => setAnalysisStage('Training candidate models (Logistic Regression, Random Forest)...'), 12000);
    const stageTimer5 = setTimeout(() => setAnalysisStage('Optimizing operational decision threshold on PR curve...'), 18000);
    const stageTimer6 = setTimeout(() => setAnalysisStage('Calculating calibrated risk scores and analytics...'), 24000);

    try {
      const result = await runAnalysis(file);
      setAnalysisResult(result);
      setAnalysisId(result.analysis_id);
      sessionStorage.setItem(STORAGE_KEY, result.analysis_id);
      setAnalysisStage('Analysis complete.');
      return result;
    } catch (err) {
      const apiErr = extractApiError(err);
      setError(apiErr.message);
      return null;
    } finally {
      clearTimeout(stageTimer1);
      clearTimeout(stageTimer2);
      clearTimeout(stageTimer3);
      clearTimeout(stageTimer4);
      clearTimeout(stageTimer5);
      clearTimeout(stageTimer6);
      setIsAnalyzing(false);
    }
  };

  const setAnalysisResultDirectly = (result: AnalysisResult | null) => {
    setAnalysisResult(result);
    if (result) {
      const id = result.analysis_id || (result as any).id;
      setAnalysisId(id);
      sessionStorage.setItem(STORAGE_KEY, id);
    } else {
      clearAnalysis();
    }
  };

  const loadAnalysis = async (id: string) => {
    setError(null);
    const activeOrgId = localStorage.getItem('sentinel_active_org_id');
    try {
      let result: AnalysisResult | null = null;
      if (activeOrgId) {
        try {
          result = await getAnalysisDetail(activeOrgId, id);
        } catch {
          // fallback to session
        }
      }
      if (!result) {
        result = await getAnalysisResult(id);
      }
      setAnalysisResult(result);
      const resId = result.analysis_id || (result as any).id || id;
      setAnalysisId(resId);
      sessionStorage.setItem(STORAGE_KEY, resId);
    } catch (err) {
      const apiErr = extractApiError(err);
      setError(apiErr.message);
      if (apiErr.statusCode === 404) {
        clearAnalysis();
      }
    }
  };

  const openInvestigation = (txId: string) => {
    setSelectedTxId(txId);
    setIsDrawerOpen(true);
  };

  const closeInvestigation = () => {
    setIsDrawerOpen(false);
    setSelectedTxId(null);
  };

  const clearAnalysis = () => {
    setAnalysisId(null);
    setAnalysisResult(null);
    setInspectionResult(null);
    setError(null);
    setSelectedTxId(null);
    setIsDrawerOpen(false);
    sessionStorage.removeItem(STORAGE_KEY);
  };

  return (
    <AnalysisContext.Provider
      value={{
        analysisId,
        analysisResult,
        inspectionResult,
        isInspecting,
        isAnalyzing,
        analysisStage,
        error,
        selectedTxId,
        isDrawerOpen,
        inspectFile,
        executeAnalysis,
        loadAnalysis,
        setAnalysisResultDirectly,
        openInvestigation,
        closeInvestigation,
        clearAnalysis,
      }}
    >
      {children}
    </AnalysisContext.Provider>
  );
};

export const useAnalysis = () => {
  const context = useContext(AnalysisContext);
  if (!context) {
    throw new Error('useAnalysis must be used within an AnalysisProvider');
  }
  return context;
};
