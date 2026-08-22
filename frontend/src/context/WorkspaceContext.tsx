import React, { createContext, useContext, useState, useEffect, ReactNode, useCallback } from 'react';
import {
  Organization,
  Client,
  OrganizationDashboardData,
  ClientDashboardData,
  PersistentAnalysisSummary,
  AnalysisResult,
} from '../types/api';
import {
  getUserOrganizations,
  getOrgDashboard,
  getClients,
  getClientDashboard,
  getOrgAnalyses,
  getAnalysisDetail,
} from '../api/endpoints';
import { useAuth } from './AuthContext';
import { extractApiError } from '../api/client';

interface WorkspaceContextType {
  organizations: Organization[];
  activeOrg: Organization | null;
  clients: Client[];
  activeClient: Client | null;
  orgDashboard: OrganizationDashboardData | null;
  clientDashboard: ClientDashboardData | null;
  analyses: PersistentAnalysisSummary[];
  activeAnalysis: AnalysisResult | null;
  selectedAnalysisId: string | null;
  isLoading: boolean;
  error: string | null;
  setActiveClient: (client: Client | null) => void;
  setSelectedAnalysisId: (id: string | null) => void;
  refreshWorkspace: () => Promise<void>;
  refreshClients: () => Promise<void>;
  refreshOrgDashboard: () => Promise<void>;
  refreshAnalyses: () => Promise<void>;
  loadClientDashboard: (clientId: string) => Promise<void>;
  loadAnalysisDetail: (analysisId: string) => Promise<AnalysisResult | null>;
}

const WorkspaceContext = createContext<WorkspaceContextType | undefined>(undefined);

export const WorkspaceProvider: React.FC<{ children: ReactNode }> = ({ children }) => {
  const { token, activeOrgId } = useAuth();
  const [organizations, setOrganizations] = useState<Organization[]>([]);
  const [clients, setClients] = useState<Client[]>([]);
  const [activeClient, setActiveClient] = useState<Client | null>(null);
  const [orgDashboard, setOrgDashboard] = useState<OrganizationDashboardData | null>(null);
  const [clientDashboard, setClientDashboard] = useState<ClientDashboardData | null>(null);
  const [analyses, setAnalyses] = useState<PersistentAnalysisSummary[]>([]);
  const [activeAnalysis, setActiveAnalysis] = useState<AnalysisResult | null>(null);
  const [selectedAnalysisId, setSelectedAnalysisId] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const activeOrg = organizations.find((o) => o.id === activeOrgId) || (organizations.length > 0 ? organizations[0] : null);

  const refreshClients = useCallback(async () => {
    if (!activeOrgId || !token) return;
    try {
      const data = await getClients(activeOrgId);
      setClients(data);
    } catch (err) {
      console.error('Failed to load clients:', err);
    }
  }, [activeOrgId, token]);

  const refreshOrgDashboard = useCallback(async () => {
    if (!activeOrgId || !token) return;
    try {
      const data = await getOrgDashboard(activeOrgId);
      setOrgDashboard(data);
    } catch (err) {
      console.error('Failed to load org dashboard:', err);
    }
  }, [activeOrgId, token]);

  const refreshAnalyses = useCallback(async () => {
    if (!activeOrgId || !token) return;
    try {
      const data = await getOrgAnalyses(activeOrgId);
      setAnalyses(data);
    } catch (err) {
      console.error('Failed to load analyses:', err);
    }
  }, [activeOrgId, token]);

  const refreshWorkspace = useCallback(async () => {
    if (!token) return;
    setIsLoading(true);
    setError(null);
    try {
      const orgs = await getUserOrganizations();
      setOrganizations(orgs);
      if (activeOrgId) {
        await Promise.all([refreshClients(), refreshOrgDashboard(), refreshAnalyses()]);
      }
    } catch (err) {
      const apiErr = extractApiError(err);
      setError(apiErr.message);
    } finally {
      setIsLoading(false);
    }
  }, [token, activeOrgId, refreshClients, refreshOrgDashboard, refreshAnalyses]);

  useEffect(() => {
    if (token) {
      refreshWorkspace();
    } else {
      setOrganizations([]);
      setClients([]);
      setOrgDashboard(null);
      setClientDashboard(null);
      setAnalyses([]);
      setActiveAnalysis(null);
      setSelectedAnalysisId(null);
    }
  }, [token, activeOrgId, refreshWorkspace]);

  const loadClientDashboard = async (clientId: string) => {
    if (!activeOrgId) return;
    setIsLoading(true);
    try {
      const data = await getClientDashboard(activeOrgId, clientId);
      setClientDashboard(data);
    } catch (err) {
      const apiErr = extractApiError(err);
      setError(apiErr.message);
    } finally {
      setIsLoading(false);
    }
  };

  const loadAnalysisDetail = async (analysisId: string): Promise<AnalysisResult | null> => {
    if (!activeOrgId) return null;
    setIsLoading(true);
    try {
      const res = await getAnalysisDetail(activeOrgId, analysisId);
      setActiveAnalysis(res);
      setSelectedAnalysisId(analysisId);
      return res;
    } catch (err) {
      const apiErr = extractApiError(err);
      setError(apiErr.message);
      return null;
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <WorkspaceContext.Provider
      value={{
        organizations,
        activeOrg,
        clients,
        activeClient,
        orgDashboard,
        clientDashboard,
        analyses,
        activeAnalysis,
        selectedAnalysisId,
        isLoading,
        error,
        setActiveClient,
        setSelectedAnalysisId,
        refreshWorkspace,
        refreshClients,
        refreshOrgDashboard,
        refreshAnalyses,
        loadClientDashboard,
        loadAnalysisDetail,
      }}
    >
      {children}
    </WorkspaceContext.Provider>
  );
};

export const useWorkspace = () => {
  const context = useContext(WorkspaceContext);
  if (!context) {
    return {
      organizations: [],
      activeOrg: null,
      clients: [],
      activeClient: null,
      orgDashboard: null,
      clientDashboard: null,
      analyses: [],
      activeAnalysis: null,
      selectedAnalysisId: null,
      isLoading: false,
      error: null,
      setActiveClient: () => {},
      setSelectedAnalysisId: () => {},
      refreshWorkspace: async () => {},
      refreshClients: async () => {},
      refreshOrgDashboard: async () => {},
      refreshAnalyses: async () => {},
      loadClientDashboard: async () => {},
      loadAnalysisDetail: async () => null,
    };
  }
  return context;
};
