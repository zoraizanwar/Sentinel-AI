import { apiClient } from './client';
import {
  DatasetInspectionResult,
  AnalysisResult,
  PaginatedTransactionsResponse,
  LocalExplanation,
  HealthResponse,
} from '../types/api';

export interface TransactionQueryParams {
  page?: number;
  page_size?: number;
  sort_by?: string;
  sort_order?: 'asc' | 'desc';
  risk_band?: string;
  is_fraud?: number;
  predicted_fraud?: number;
  min_amount?: number;
  max_amount?: number;
  min_risk_score?: number;
  max_risk_score?: number;
  search?: string;
}

/** Check service health */
export async function checkHealth(): Promise<HealthResponse> {
  const resp = await apiClient.get<HealthResponse>('/health', { baseURL: '' });
  return resp.data;
}

/** Pre-flight dataset inspection */
export async function inspectDataset(file: File): Promise<DatasetInspectionResult> {
  const formData = new FormData();
  formData.append('file', file);
  const resp = await apiClient.post<DatasetInspectionResult>('/dataset/inspect', formData, {
    headers: { 'Content-Type': 'multipart/form-data' },
  });
  return resp.data;
}

/** Run complete fraud analysis */
export async function runAnalysis(file: File): Promise<AnalysisResult> {
  const formData = new FormData();
  formData.append('file', file);
  const resp = await apiClient.post<AnalysisResult>('/analysis/run', formData, {
    headers: { 'Content-Type': 'multipart/form-data' },
  });
  return resp.data;
}

/** Retrieve active AnalysisResult */
export async function getAnalysisResult(analysisId: string): Promise<AnalysisResult> {
  const resp = await apiClient.get<AnalysisResult>(`/analysis/${analysisId}`);
  return resp.data;
}

/** Query paginated transactions with server-side filters */
export async function getTransactions(
  analysisId: string,
  params?: TransactionQueryParams
): Promise<PaginatedTransactionsResponse> {
  const resp = await apiClient.get<PaginatedTransactionsResponse>(
    `/analysis/${analysisId}/transactions`,
    { params }
  );
  return resp.data;
}

/** Get on-demand SHAP explanation for a transaction */
export async function explainTransaction(
  analysisId: string,
  txId: string
): Promise<LocalExplanation> {
  const resp = await apiClient.get<LocalExplanation>(
    `/analysis/${analysisId}/transactions/${txId}/explain`
  );
  return resp.data;
}

/** Trigger PDF generation (Phase 6 contract) */
export async function generatePdfReport(analysisId: string): Promise<Blob> {
  const resp = await apiClient.post<Blob>(
    `/analysis/${analysisId}/report/pdf`,
    {},
    { responseType: 'blob' }
  );
  return resp.data;
}

// ==========================================
// PHASE 9: MULTI-ORGANIZATION & TENANCY APIS
// ==========================================

import {
  User,
  AuthResponse,
  Organization,
  OrganizationMemberItem,
  Client,
  Dataset,
  PersistentAnalysisSummary,
  ReportItem,
  AuditLogItem,
  OrganizationDashboardData,
  ClientDashboardData,
  ReportScope
} from '../types/api';

// Auth
export async function registerUser(data: { email: string; password: string; full_name: string; organization_name?: string }): Promise<AuthResponse> {
  const resp = await apiClient.post<AuthResponse>('/auth/register', data);
  return resp.data;
}

export async function loginUser(data: { email: string; password: string }): Promise<AuthResponse> {
  const resp = await apiClient.post<AuthResponse>('/auth/login', data);
  return resp.data;
}

export async function getCurrentUserProfile(): Promise<User> {
  const resp = await apiClient.get<User>('/auth/me');
  return resp.data;
}

// Organizations
export async function getUserOrganizations(): Promise<Organization[]> {
  const resp = await apiClient.get<Organization[]>('/organizations');
  return resp.data;
}

export async function getOrganization(orgId: string): Promise<Organization> {
  const resp = await apiClient.get<Organization>(`/organizations/${orgId}`);
  return resp.data;
}

export async function getOrgDashboard(orgId: string): Promise<OrganizationDashboardData> {
  const resp = await apiClient.get<OrganizationDashboardData>(`/organizations/${orgId}/dashboard`);
  return resp.data;
}

export async function getOrgMembers(orgId: string): Promise<OrganizationMemberItem[]> {
  const resp = await apiClient.get<OrganizationMemberItem[]>(`/organizations/${orgId}/members`);
  return resp.data;
}

export async function addOrgMember(orgId: string, data: { email: string; role: string }): Promise<OrganizationMemberItem> {
  const resp = await apiClient.post<OrganizationMemberItem>(`/organizations/${orgId}/members`, data);
  return resp.data;
}

// Clients
export async function getClients(orgId: string): Promise<Client[]> {
  const resp = await apiClient.get<Client[]>(`/organizations/${orgId}/clients`);
  return resp.data;
}

export async function createClient(orgId: string, data: { client_code: string; name: string; industry?: string; contact_email?: string }): Promise<Client> {
  const resp = await apiClient.post<Client>(`/organizations/${orgId}/clients`, data);
  return resp.data;
}

export async function getClientDashboard(orgId: string, clientId: string): Promise<ClientDashboardData> {
  const resp = await apiClient.get<ClientDashboardData>(`/organizations/${orgId}/clients/${clientId}/dashboard`);
  return resp.data;
}

// Datasets
export async function uploadClientDataset(orgId: string, clientId: string, file: File): Promise<Dataset> {
  const formData = new FormData();
  formData.append('file', file);
  const resp = await apiClient.post<Dataset>(
    `/organizations/${orgId}/clients/${clientId}/datasets/upload`,
    formData,
    { headers: { 'Content-Type': 'multipart/form-data' } }
  );
  return resp.data;
}

export async function getClientDatasets(orgId: string, clientId: string): Promise<Dataset[]> {
  const resp = await apiClient.get<Dataset[]>(`/organizations/${orgId}/clients/${clientId}/datasets`);
  return resp.data;
}

// Analyses
export async function runPersistentAnalysis(orgId: string, clientId: string, datasetId: string): Promise<PersistentAnalysisSummary> {
  const resp = await apiClient.post<PersistentAnalysisSummary>(
    `/organizations/${orgId}/clients/${clientId}/datasets/${datasetId}/analyze`
  );
  return resp.data;
}

export async function getOrgAnalyses(orgId: string): Promise<PersistentAnalysisSummary[]> {
  const resp = await apiClient.get<PersistentAnalysisSummary[]>(`/organizations/${orgId}/analyses`);
  return resp.data;
}

export async function getAnalysisDetail(orgId: string, analysisId: string): Promise<AnalysisResult> {
  const resp = await apiClient.get<AnalysisResult>(`/organizations/${orgId}/analyses/${analysisId}`);
  return resp.data;
}

// Transactions
export async function getOrgTransactions(
  orgId: string,
  analysisId: string,
  params?: TransactionQueryParams
): Promise<PaginatedTransactionsResponse> {
  const resp = await apiClient.get<PaginatedTransactionsResponse>(
    `/organizations/${orgId}/analyses/${analysisId}/transactions`,
    { params }
  );
  return resp.data;
}

// Explainability
export async function explainOrgTransaction(
  orgId: string,
  analysisId: string,
  txId: string
): Promise<LocalExplanation> {
  const resp = await apiClient.get<LocalExplanation>(
    `/organizations/${orgId}/analyses/${analysisId}/transactions/${txId}/explain`
  );
  return resp.data;
}

// Reports
export async function generateOrgReport(
  orgId: string,
  data: { client_id?: string; analysis_id?: string; report_type: ReportScope; title?: string }
): Promise<ReportItem> {
  const resp = await apiClient.post<ReportItem>(`/organizations/${orgId}/reports/generate`, data);
  return resp.data;
}

export async function getOrgReports(orgId: string): Promise<ReportItem[]> {
  const resp = await apiClient.get<ReportItem[]>(`/organizations/${orgId}/reports`);
  return resp.data;
}

export async function downloadOrgReport(orgId: string, reportId: string): Promise<Blob> {
  const resp = await apiClient.get<Blob>(`/organizations/${orgId}/reports/${reportId}/download`, {
    responseType: 'blob'
  });
  return resp.data;
}

// Audit Logs
export async function getOrgAuditLogs(
  orgId: string,
  page: number = 1,
  pageSize: number = 50
): Promise<AuditLogItem[]> {
  const resp = await apiClient.get<any>(`/organizations/${orgId}/audit-logs`, {
    params: { page, page_size: pageSize }
  });
  if (Array.isArray(resp.data)) {
    return resp.data;
  }
  if (resp.data && Array.isArray(resp.data.items)) {
    return resp.data.items;
  }
  return [];
}
