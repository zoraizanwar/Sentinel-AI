import React from 'react';
import { useNavigate } from 'react-router-dom';
import {
  ShieldAlert,
  DollarSign,
  AlertOctagon,
  TrendingUp,
  Percent,
  Layers,
  ShieldCheck,
  CheckCircle2,
} from 'lucide-react';
import {
  ResponsiveContainer,
  PieChart,
  Pie,
  Cell,
  BarChart,
  Bar,
  XAxis,
  YAxis,
  Tooltip,
  Legend,
} from 'recharts';
import { useAnalysis } from '../context/AnalysisContext';
import { StatCard } from '../components/common/StatCard';
import { CardSkeleton, ChartSkeleton } from '../components/common/Skeleton';
import { EmptyState } from '../components/common/EmptyState';
import { ErrorMessage } from '../components/common/ErrorMessage';

export const Overview: React.FC = () => {
  const { analysisResult, isAnalyzing, error } = useAnalysis();
  const navigate = useNavigate();

  if (isAnalyzing) {
    return (
      <div className="space-y-6">
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
          <CardSkeleton />
          <CardSkeleton />
          <CardSkeleton />
          <CardSkeleton />
        </div>
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          <ChartSkeleton />
          <ChartSkeleton />
        </div>
      </div>
    );
  }

  if (error && !analysisResult) {
    return (
      <ErrorMessage
        title="Failed to Load Analysis"
        message={error}
        onRetry={() => navigate('/upload')}
      />
    );
  }

  if (!analysisResult) {
    return (
      <EmptyState
        title="No Active Analysis Session"
        description="Upload a transaction dataset to execute machine learning fraud detection, threshold optimization, and risk intelligence."
        actionLabel="Upload Transaction Dataset"
        onAction={() => navigate('/upload')}
      />
    );
  }

  const {
    fraud_statistics: fraudStats,
    risk_statistics: riskStats,
    model_results: modelResults,
    risk_distribution: riskDist,
    categorical_breakdowns: catBreakdowns,
    findings,
    recommendations,
  } = analysisResult;

  // 1. Risk Tier Distribution Data for Pie Chart
  const riskPieData = [
    { name: 'Low (0-20)', value: riskStats.low_risk_count, color: '#10B981' },
    { name: 'Medium (20-50)', value: riskStats.medium_risk_count, color: '#F59E0B' },
    { name: 'High (50-80)', value: riskStats.high_risk_count, color: '#F97316' },
    { name: 'Critical (80-100)', value: riskStats.critical_risk_count, color: '#EF4444' },
  ];

  // 2. Risk Score 10-Bin Histogram Data
  const scoreHistData = riskDist.score_bins.map((binLabel, idx) => ({
    bin: binLabel,
    total: riskDist.counts[idx] || 0,
    fraud: riskDist.fraud_counts_per_bin[idx] || 0,
  }));

  // 3. Category Fraud Rates Top 6
  const categoryChartData = Object.values(catBreakdowns)
    .sort((a, b) => b.fraud_rate_percentage - a.fraud_rate_percentage)
    .slice(0, 7)
    .map((c) => ({
      category: c.category_name.replace('_', ' '),
      fraudRate: c.fraud_rate_percentage,
      totalCount: c.total_count,
    }));

  return (
    <div className="space-y-8">
      {/* Top Executive KPI Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-6 gap-4">
        <StatCard
          title="Total Transactions"
          value={fraudStats.total_transactions.toLocaleString()}
          subtitle="Processed Volume"
          icon={<Layers className="w-4 h-4" />}
        />
        <StatCard
          title="Fraud Detected"
          value={fraudStats.fraud_count.toLocaleString()}
          subtitle={`${fraudStats.fraud_rate_percentage.toFixed(3)}% Prevalence`}
          highlight="danger"
          icon={<AlertOctagon className="w-4 h-4 text-rose-400" />}
        />
        <StatCard
          title="Fraud Exposure"
          value={`$${(fraudStats.fraud_volume_usd / 1000).toFixed(1)}k`}
          subtitle={`${fraudStats.fraud_loss_percentage.toFixed(2)}% of Volume`}
          highlight="danger"
          icon={<DollarSign className="w-4 h-4 text-rose-400" />}
        />
        <StatCard
          title="Critical Risk"
          value={riskStats.critical_risk_count.toLocaleString()}
          subtitle={`${riskStats.critical_risk_pct.toFixed(2)}% of Total`}
          highlight="danger"
          icon={<ShieldAlert className="w-4 h-4 text-rose-400" />}
        />
        <StatCard
          title="Model Precision"
          value={`${((modelResults.test_metrics?.precision ?? modelResults.candidate_models[0]?.precision ?? 0) * 100).toFixed(1)}%`}
          subtitle={`Recall: ${((modelResults.test_metrics?.recall ?? modelResults.candidate_models[0]?.recall ?? 0) * 100).toFixed(1)}%`}
          highlight="success"
          icon={<ShieldCheck className="w-4 h-4 text-emerald-400" />}
        />
        <StatCard
          title="Mean Risk Score"
          value={riskStats.mean_risk_score.toFixed(1)}
          subtitle={`Median: ${riskStats.median_risk_score.toFixed(1)}`}
          icon={<Percent className="w-4 h-4 text-slate-400" />}
        />
      </div>

      {/* Primary Analytics Charts Row */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Risk Distribution Donut */}
        <div className="bg-surface rounded-xl border border-surface-border p-5 space-y-4">
          <div className="flex items-center justify-between">
            <div>
              <h3 className="text-sm font-bold text-white uppercase tracking-wider">
                Risk Tier Distribution
              </h3>
              <p className="text-xs text-slate-400">
                Classification breakdown across calibrated risk bands
              </p>
            </div>
            <span className="text-xs font-mono text-slate-400">
              {fraudStats.total_transactions.toLocaleString()} Events
            </span>
          </div>

          <div className="h-64 flex items-center justify-center">
            <ResponsiveContainer width="100%" height="100%">
              <PieChart>
                <Pie
                  data={riskPieData}
                  cx="50%"
                  cy="50%"
                  innerRadius={60}
                  outerRadius={85}
                  paddingAngle={4}
                  dataKey="value"
                >
                  {riskPieData.map((entry, index) => (
                    <Cell key={`cell-${index}`} fill={entry.color} stroke="#111827" strokeWidth={2} />
                  ))}
                </Pie>
                <Tooltip
                  contentStyle={{
                    backgroundColor: '#1F2937',
                    borderColor: '#374151',
                    borderRadius: '0.5rem',
                    color: '#FFF',
                    fontSize: '12px',
                  }}
                  formatter={(val: number) => [`${val.toLocaleString()} transactions`, 'Volume']}
                />
                <Legend
                  verticalAlign="bottom"
                  height={36}
                  iconType="circle"
                  formatter={(val) => <span className="text-xs text-slate-300 ml-1">{val}</span>}
                />
              </PieChart>
            </ResponsiveContainer>
          </div>
        </div>

        {/* Category Fraud Rate Bar Chart */}
        <div className="bg-surface rounded-xl border border-surface-border p-5 space-y-4">
          <div className="flex items-center justify-between">
            <div>
              <h3 className="text-sm font-bold text-white uppercase tracking-wider">
                Highest Risk Categories
              </h3>
              <p className="text-xs text-slate-400">
                Fraud rate percentage by merchant industry classification
              </p>
            </div>
          </div>

          <div className="h-64">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={categoryChartData} margin={{ top: 10, right: 10, left: -20, bottom: 20 }}>
                <XAxis
                  dataKey="category"
                  stroke="#9CA3AF"
                  fontSize={10}
                  tickLine={false}
                  interval={0}
                  angle={-25}
                  textAnchor="end"
                />
                <YAxis
                  stroke="#9CA3AF"
                  fontSize={10}
                  tickLine={false}
                  unit="%"
                />
                <Tooltip
                  contentStyle={{
                    backgroundColor: '#1F2937',
                    borderColor: '#374151',
                    borderRadius: '0.5rem',
                    color: '#FFF',
                    fontSize: '12px',
                  }}
                  formatter={(val: number) => [`${val.toFixed(2)}%`, 'Fraud Rate']}
                />
                <Bar dataKey="fraudRate" fill="#EF4444" radius={[4, 4, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>
      </div>

      {/* Secondary Analytics Row: Risk Histogram + Top Global Features */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* 10-Point Score Histogram */}
        <div className="bg-surface rounded-xl border border-surface-border p-5 space-y-4">
          <div>
            <h3 className="text-sm font-bold text-white uppercase tracking-wider">
              Risk Score Concentration (0 - 100)
            </h3>
            <p className="text-xs text-slate-400">
              Histogram frequency showing fraud concentration at high scores
            </p>
          </div>

          <div className="h-64">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={scoreHistData} margin={{ top: 10, right: 10, left: -10, bottom: 0 }}>
                <XAxis dataKey="bin" stroke="#9CA3AF" fontSize={10} tickLine={false} />
                <YAxis stroke="#9CA3AF" fontSize={10} tickLine={false} />
                <Tooltip
                  contentStyle={{
                    backgroundColor: '#1F2937',
                    borderColor: '#374151',
                    borderRadius: '0.5rem',
                    color: '#FFF',
                    fontSize: '12px',
                  }}
                />
                <Bar dataKey="total" name="Total Transactions" fill="#4F46E5" radius={[4, 4, 0, 0]} />
                <Bar dataKey="fraud" name="Confirmed Fraud" fill="#EF4444" radius={[4, 4, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>

        {/* Global Feature Importance */}
        <div className="bg-surface rounded-xl border border-surface-border p-5 space-y-4">
          <div className="flex items-center justify-between">
            <div>
              <h3 className="text-sm font-bold text-white uppercase tracking-wider">
                Top Global Predictive Factors
              </h3>
              <p className="text-xs text-slate-400">
                Model feature attribution calculated across full dataset
              </p>
            </div>
            <span className="text-xs font-mono text-slate-400">
              {modelResults.selected_model.model_name}
            </span>
          </div>

          <div className="space-y-3 pt-2">
            {modelResults.global_feature_importance.slice(0, 6).map((item) => {
              const maxImp = modelResults.global_feature_importance[0]?.importance || 1.0;
              const pct = Math.round((item.importance / maxImp) * 100);
              return (
                <div key={item.feature_name} className="space-y-1">
                  <div className="flex justify-between text-xs">
                    <span className="font-mono text-slate-200">{item.feature_name}</span>
                    <span className="font-mono text-rose-400 font-semibold">
                      {(item.importance * 100).toFixed(1)}%
                    </span>
                  </div>
                  <div className="w-full bg-surface-elevated rounded-full h-1.5 overflow-hidden">
                    <div
                      className="bg-gradient-to-r from-rose-500 to-amber-500 h-1.5 rounded-full"
                      style={{ width: `${pct}%` }}
                    />
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      </div>

      {/* Analytical Findings & Recommendations */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Verified Findings */}
        <div className="bg-surface rounded-xl border border-surface-border p-5 space-y-4">
          <div className="flex items-center gap-2">
            <TrendingUp className="w-4 h-4 text-amber-400" />
            <h3 className="text-sm font-bold text-white uppercase tracking-wider">
              Empirical Findings
            </h3>
          </div>
          <div className="space-y-3">
            {findings.slice(0, 3).map((f) => (
              <div
                key={f.finding_id}
                className="p-3 bg-surface-elevated/50 border border-surface-border rounded-lg"
              >
                <div className="flex items-center justify-between">
                  <span className="text-xs font-semibold text-white">{f.title}</span>
                  <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-surface-border text-slate-300">
                    {f.finding_id}
                  </span>
                </div>
                <p className="text-xs text-slate-400 mt-1 leading-relaxed">{f.description}</p>
              </div>
            ))}
          </div>
        </div>

        {/* Evidence-Based Recommendations */}
        <div className="bg-surface rounded-xl border border-surface-border p-5 space-y-4">
          <div className="flex items-center gap-2">
            <CheckCircle2 className="w-4 h-4 text-emerald-400" />
            <h3 className="text-sm font-bold text-white uppercase tracking-wider">
              Operational Actions
            </h3>
          </div>
          <div className="space-y-3">
            {recommendations.slice(0, 3).map((r) => (
              <div
                key={r.recommendation_id}
                className="p-3 bg-surface-elevated/50 border border-surface-border rounded-lg"
              >
                <div className="flex items-center justify-between">
                  <span className="text-xs font-semibold text-white">{r.title}</span>
                  <span
                    className={`text-[10px] font-semibold uppercase px-2 py-0.5 rounded font-mono ${
                      r.priority === 'CRITICAL'
                        ? 'bg-rose-500/20 text-rose-400'
                        : 'bg-amber-500/20 text-amber-400'
                    }`}
                  >
                    {r.priority}
                  </span>
                </div>
                <p className="text-xs text-slate-300 mt-1 font-medium">{r.action}</p>
                <p className="text-[11px] text-slate-400 mt-1">{r.rationale}</p>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
};
