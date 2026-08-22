/**
 * TypeScript API definitions mirroring backend Pydantic schemas.
 * Guarantees zero data fabrication across the entire user interface.
 */

export type Severity = 'ERROR' | 'WARNING' | 'INFO';
export type ValidationStatus = 'VALID' | 'WARNINGS' | 'INVALID';
export type RiskBand = 'LOW' | 'MEDIUM' | 'HIGH' | 'CRITICAL';

export interface ValidationFinding {
  severity: Severity;
  code: string;
  message: string;
  column?: string | null;
  details?: Record<string, any>;
}

export interface ColumnSummary {
  name: string;
  dtype: string;
  non_null_count: number;
  null_count: number;
  null_percentage: number;
  unique_count: number;
  is_numeric: boolean;
  is_categorical: boolean;
  is_datetime: boolean;
  is_constant: boolean;
  is_high_cardinality: boolean;
  is_identifier_candidate: boolean;
  is_leakage_candidate: boolean;
  min_value?: number | null;
  max_value?: number | null;
  mean_value?: number | null;
  sample_values: string[];
}

export interface ClassDistribution {
  target_column: string;
  total_count: number;
  legitimate_count: number;
  fraud_count: number;
  fraud_percentage: number;
  imbalance_ratio: number;
  is_single_class: boolean;
  is_severely_imbalanced: boolean;
}

export interface DatasetInspectionResult {
  dataset_name: string;
  file_size_bytes: number;
  row_count: number;
  column_count: number;
  target_column?: string | null;
  validation_status: ValidationStatus;
  errors: ValidationFinding[];
  warnings: ValidationFinding[];
  infos: ValidationFinding[];
  columns: Record<string, ColumnSummary>;
  class_distribution?: ClassDistribution | null;
  detected_numeric_columns: string[];
  detected_categorical_columns: string[];
  detected_temporal_columns: string[];
  detected_amount_columns: string[];
  detected_id_columns: string[];
  potential_leakage_columns: string[];
  duplicate_rows_count: number;
  total_missing_cells: number;
}

export interface DataQualityReport {
  is_valid_for_analysis: boolean;
  total_rows: number;
  total_columns: number;
  missing_cells_percentage: number;
  duplicate_rows_percentage: number;
  has_target: boolean;
  target_column_name?: string | null;
  fraud_rate_percentage?: number | null;
  validation_findings_count: Record<string, number>;
  findings: ValidationFinding[];
}

export interface ConfusionMatrix {
  true_positive: number;
  false_positive: number;
  true_negative: number;
  false_negative: number;
}

export interface CurvePoint {
  x: number;
  y: number;
  threshold?: number | null;
}

export interface CandidateModelMetrics {
  model_name: string;
  precision: number;
  recall: number;
  f1: number;
  pr_auc: number;
  roc_auc: number;
  false_positive_rate: number;
  false_negative_rate: number;
  accuracy: number;
  confusion_matrix: ConfusionMatrix;
  pr_curve: CurvePoint[];
  roc_curve: CurvePoint[];
}

export interface SelectedModelDetails {
  model_name: string;
  justification: string;
  selection_metric: string;
  selection_value: number;
  optimal_threshold: number;
  threshold_methodology: string;
}

export interface FeatureImportanceItem {
  feature_name: string;
  importance: number;
  rank: number;
}

export interface ModelEvaluationSummary {
  candidate_models: CandidateModelMetrics[];
  selected_model: SelectedModelDetails;
  global_feature_importance: FeatureImportanceItem[];
  is_xgboost_available: boolean;
  validation_fraud_count: number;
  validation_legit_count: number;
  test_fraud_count?: number | null;
  test_legit_count?: number | null;
  test_metrics?: CandidateModelMetrics | null;
}

export interface FraudStatistics {
  total_transactions: number;
  fraud_count: number;
  legitimate_count: number;
  fraud_rate_percentage: number;
  total_volume_usd: number;
  fraud_volume_usd: number;
  fraud_loss_percentage: number;
}

export interface RiskStatistics {
  low_risk_count: number;
  low_risk_pct: number;
  medium_risk_count: number;
  medium_risk_pct: number;
  high_risk_count: number;
  high_risk_pct: number;
  critical_risk_count: number;
  critical_risk_pct: number;
  mean_risk_score: number;
  median_risk_score: number;
}

export interface RiskDistributionSummary {
  score_bins: string[];
  counts: number[];
  fraud_counts_per_bin: number[];
}

export interface CategoricalBreakdown {
  category_name: string;
  total_count: number;
  fraud_count: number;
  fraud_rate_percentage: number;
  total_volume_usd: number;
  fraud_volume_usd: number;
}

export interface RiskPattern {
  pattern_name: string;
  description: string;
  affected_count: number;
  fraud_rate_percentage: number;
  severity: string;
}

export interface AnalyticalFinding {
  finding_id: string;
  title: string;
  description: string;
  category: string;
  evidence_metric: string;
  evidence_value: any;
}

export interface EvidenceBasedRecommendation {
  recommendation_id: string;
  title: string;
  action: string;
  rationale: string;
  priority: string;
  expected_impact: string;
}

export interface TransactionPaginationMeta {
  total_records: number;
  page: number;
  page_size: number;
  total_pages: number;
}

export interface AnalysisResult {
  analysis_id: string;
  created_at: string;
  execution_time_seconds: number;
  dataset_summary: DatasetInspectionResult;
  data_quality: DataQualityReport;
  fraud_statistics: FraudStatistics;
  risk_statistics: RiskStatistics;
  model_results: ModelEvaluationSummary;
  risk_distribution: RiskDistributionSummary;
  categorical_breakdowns: Record<string, CategoricalBreakdown>;
  high_risk_patterns: RiskPattern[];
  findings: AnalyticalFinding[];
  recommendations: EvidenceBasedRecommendation[];
  pagination_meta: TransactionPaginationMeta;
}

export interface TransactionItem {
  transaction_id: string;
  timestamp?: string | null;
  amount: number;
  category?: string | null;
  merchant?: string | null;
  city?: string | null;
  state?: string | null;
  fraud_probability: number;
  risk_score: number;
  risk_band: RiskBand;
  predicted_fraud: number;
  is_actual_fraud?: number | null;
}

export interface PaginatedTransactionsResponse {
  transactions: TransactionItem[];
  total_matching: number;
  page: number;
  page_size: number;
  total_pages: number;
  sort_by: string;
  sort_order: string;
  applied_filters: Record<string, any>;
}

export interface SHAPContribution {
  feature_name: string;
  feature_value: any;
  shap_value: number;
  contribution_type: 'RISK_INCREASING' | 'RISK_DECREASING';
  human_explanation: string;
}

export interface LocalExplanation {
  transaction_id: string;
  fraud_probability: number;
  risk_score: number;
  risk_band: RiskBand;
  base_value: number;
  positive_contributions: SHAPContribution[];
  negative_contributions: SHAPContribution[];
  method: string;
  is_cached: boolean;
}

export interface HealthResponse {
  status: string;
  service: string;
  version: string;
}

export interface ErrorResponse {
  error_code: string;
  message: string;
  details?: Record<string, any>;
}

// ==========================================
// PHASE 9: MULTI-ORGANIZATION & TENANCY TYPES
// ==========================================

export type OrganizationRole = 'ORGANIZATION_ADMIN' | 'ANALYST' | 'VIEWER';
export type ClientStatus = 'ACTIVE' | 'ARCHIVED';
export type ReportScope = 'ORGANIZATION' | 'CLIENT' | 'ANALYSIS';

export interface UserMembership {
  id: string;
  user_id: string;
  organization_id: string;
  role: OrganizationRole;
  joined_at: string;
  organization?: Organization;
}

export interface User {
  id: string;
  email: string;
  full_name: string;
  is_active: boolean;
  created_at: string;
  memberships: UserMembership[];
}

export interface AuthResponse {
  access_token: string;
  token_type: string;
  user_id: string;
  email: string;
  full_name: string;
  default_organization_id: string;
  user?: User;
}

export interface Organization {
  id: string;
  name: string;
  slug: string;
  created_at: string;
  members_count?: number;
  clients_count?: number;
}

export interface OrganizationMemberItem {
  id: string;
  user_id: string;
  organization_id: string;
  role: OrganizationRole;
  joined_at: string;
  user_email?: string;
  user_full_name?: string;
}

export interface Client {
  id: string;
  organization_id: string;
  client_code: string;
  name: string;
  industry?: string | null;
  contact_email?: string | null;
  status: ClientStatus;
  created_at: string;
  datasets_count?: number;
  analyses_count?: number;
  total_transactions?: number;
  total_fraud_detected?: number;
  risk_level?: string;
}

export interface Dataset {
  id: string;
  organization_id: string;
  client_id: string;
  filename: string;
  file_size_bytes: number;
  row_count: number;
  column_count: number;
  has_target: boolean;
  target_column_name?: string | null;
  fraud_rate_percentage?: number | null;
  validation_status: ValidationStatus;
  processing_status: 'PENDING' | 'VALIDATED' | 'ANALYZED' | 'FAILED';
  uploaded_by_user_id: string;
  created_at: string;
}

export interface PersistentAnalysisSummary {
  id: string;
  organization_id: string;
  client_id: string;
  dataset_id: string;
  user_id: string;
  model_name: string;
  optimal_threshold: number;
  execution_time_seconds: number;
  fraud_statistics?: FraudStatistics;
  risk_statistics?: RiskStatistics;
  status: string;
  created_at: string;
}

export interface ReportItem {
  id: string;
  organization_id: string;
  client_id?: string | null;
  analysis_id?: string | null;
  report_type: ReportScope;
  title: string;
  filename: string;
  file_size_bytes: number;
  created_by_user_id: string;
  created_at: string;
}

export interface AuditLogItem {
  id: string;
  organization_id: string;
  user_id: string;
  action: string;
  resource_type: string;
  resource_id?: string | null;
  details?: Record<string, any> | null;
  ip_address?: string | null;
  created_at: string;
}

export interface ClientRiskSummary {
  client_id: string;
  client_name?: string;
  name?: string;
  client_code: string;
  total_transactions?: number;
  total_fraud?: number;
  fraud_count?: number;
  fraud_rate_pct?: number;
  fraud_rate_percentage?: number;
  risk_level?: string;
  critical_risk_count?: number;
  high_risk_count?: number;
  financial_exposure_usd?: number;
}

export interface OrganizationDashboardData {
  organization_id: string;
  organization_name: string;
  total_clients: number;
  total_datasets: number;
  total_analyses: number;
  total_transactions_analyzed: number;
  total_fraud_detected?: number;
  total_fraud_transactions?: number;
  total_fraud_loss_usd?: number;
  total_financial_exposure_usd?: number;
  overall_fraud_rate_pct?: number;
  overall_fraud_rate_percentage?: number;
  critical_risk_count?: number;
  high_risk_count?: number;
  client_risk_summaries?: ClientRiskSummary[];
  highest_risk_clients?: ClientRiskSummary[];
  recent_analyses: any[];
}

export interface ClientDashboardData {
  client_id: string;
  client_name: string;
  client_code: string;
  total_datasets: number;
  total_analyses: number;
  total_transactions: number;
  total_fraud_detected: number;
  fraud_loss_prevented_usd: number;
  fraud_rate_pct: number;
  risk_band_distribution: Record<string, number>;
  recent_analyses: PersistentAnalysisSummary[];
}
