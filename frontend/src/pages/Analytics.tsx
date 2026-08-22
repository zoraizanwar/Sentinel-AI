import React from 'react';
import { useNavigate } from 'react-router-dom';
import {
  ResponsiveContainer,
  BarChart,
  Bar,
  XAxis,
  YAxis,
  Tooltip,
  LineChart,
  Line,
  CartesianGrid,
} from 'recharts';
import { Zap } from 'lucide-react';
import { useAnalysis } from '../context/AnalysisContext';
import { EmptyState } from '../components/common/EmptyState';
import { ChartSkeleton } from '../components/common/Skeleton';

export const Analytics: React.FC = () => {
  const { analysisResult, isAnalyzing } = useAnalysis();
  const navigate = useNavigate();

  if (isAnalyzing) {
    return (
      <div className="space-y-6">
        <ChartSkeleton />
        <ChartSkeleton />
      </div>
    );
  }

  if (!analysisResult) {
    return (
      <EmptyState
        title="No Active Dataset Session"
        description="Upload a transaction dataset to run behavioral pattern analysis, category loss metrics, and risk concentrations."
        actionLabel="Upload Dataset"
        onAction={() => navigate('/upload')}
      />
    );
  }

  const {
    categorical_breakdowns: catBreakdowns,
    high_risk_patterns: patterns,
    risk_distribution: riskDist,
  } = analysisResult;

  // Category Loss vs Volume
  const categoryData = Object.values(catBreakdowns)
    .sort((a, b) => b.fraud_volume_usd - a.fraud_volume_usd)
    .map((c) => ({
      category: c.category_name.replace('_', ' '),
      fraudVolume: c.fraud_volume_usd,
      totalVolume: c.total_volume_usd,
      fraudRate: c.fraud_rate_percentage,
      fraudCount: c.fraud_count,
    }));

  // Score Decile Trends
  const decileData = riskDist.score_bins.map((bin, i) => ({
    bin,
    fraudRatio:
      riskDist.counts[i] > 0
        ? Number(((riskDist.fraud_counts_per_bin[i] / riskDist.counts[i]) * 100).toFixed(2))
        : 0,
    fraudCount: riskDist.fraud_counts_per_bin[i] || 0,
    totalCount: riskDist.counts[i] || 0,
  }));

  return (
    <div className="space-y-8">
      {/* High Risk Patterns Section */}
      <div className="space-y-4">
        <div>
          <h2 className="text-sm font-bold text-white uppercase tracking-wider">
            Behavioral Risk Patterns & Anomaly Vectors
          </h2>
          <p className="text-xs text-slate-400">
            Empirical risk concentrations identified across temporal and monetary features
          </p>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {patterns.map((pat, idx) => (
            <div
              key={idx}
              className="bg-surface rounded-xl border border-surface-border p-5 space-y-3"
            >
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <Zap className="w-4 h-4 text-amber-400" />
                  <span className="text-sm font-bold text-white">{pat.pattern_name}</span>
                </div>
                <span
                  className={`text-[10px] font-semibold font-mono uppercase px-2 py-0.5 rounded ${
                    pat.severity === 'CRITICAL'
                      ? 'bg-rose-500/20 text-rose-400 border border-rose-500/30'
                      : 'bg-amber-500/20 text-amber-400 border border-amber-500/30'
                  }`}
                >
                  {pat.severity}
                </span>
              </div>
              <p className="text-xs text-slate-300 leading-relaxed">{pat.description}</p>
              <div className="pt-2 border-t border-surface-border flex items-center justify-between text-xs font-mono">
                <span className="text-slate-400">
                  Affected: <strong className="text-white">{pat.affected_count.toLocaleString()}</strong> events
                </span>
                <span className="text-rose-400 font-bold">
                  Fraud Rate: {pat.fraud_rate_percentage.toFixed(2)}%
                </span>
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Category Loss Volume Chart */}
      <div className="bg-surface rounded-xl border border-surface-border p-5 space-y-4">
        <div>
          <h3 className="text-sm font-bold text-white uppercase tracking-wider">
            Financial Fraud Exposure by Merchant Category ($ USD)
          </h3>
          <p className="text-xs text-slate-400">
            Absolute direct loss exposure in dollars mapped across merchant classifications
          </p>
        </div>

        <div className="h-72">
          <ResponsiveContainer width="100%" height="100%">
            <BarChart data={categoryData} margin={{ top: 10, right: 20, left: 10, bottom: 25 }}>
              <CartesianGrid strokeDasharray="3 3" stroke="#1F2937" />
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
                tickFormatter={(v) => `$${(v / 1000).toFixed(0)}k`}
              />
              <Tooltip
                contentStyle={{
                  backgroundColor: '#1F2937',
                  borderColor: '#374151',
                  borderRadius: '0.5rem',
                  color: '#FFF',
                  fontSize: '12px',
                }}
                formatter={(val: number) => [`$${val.toLocaleString()}`, 'Fraud Loss']}
              />
              <Bar dataKey="fraudVolume" fill="#EF4444" radius={[4, 4, 0, 0]} />
            </BarChart>
          </ResponsiveContainer>
        </div>
      </div>

      {/* Risk Decile Fraud Ratio Trend */}
      <div className="bg-surface rounded-xl border border-surface-border p-5 space-y-4">
        <div>
          <h3 className="text-sm font-bold text-white uppercase tracking-wider">
            Empirical Risk Calibration Curve
          </h3>
          <p className="text-xs text-slate-400">
            Actual fraud rate percentage observed across model risk score deciles
          </p>
        </div>

        <div className="h-72">
          <ResponsiveContainer width="100%" height="100%">
            <LineChart data={decileData} margin={{ top: 10, right: 20, left: 0, bottom: 10 }}>
              <CartesianGrid strokeDasharray="3 3" stroke="#1F2937" />
              <XAxis dataKey="bin" stroke="#9CA3AF" fontSize={10} tickLine={false} />
              <YAxis stroke="#9CA3AF" fontSize={10} tickLine={false} unit="%" />
              <Tooltip
                contentStyle={{
                  backgroundColor: '#1F2937',
                  borderColor: '#374151',
                  borderRadius: '0.5rem',
                  color: '#FFF',
                  fontSize: '12px',
                }}
                formatter={(val: number) => [`${val}%`, 'Observed Fraud Rate']}
              />
              <Line
                type="monotone"
                dataKey="fraudRatio"
                stroke="#F59E0B"
                strokeWidth={3}
                dot={{ r: 4, fill: '#F59E0B' }}
              />
            </LineChart>
          </ResponsiveContainer>
        </div>
      </div>
    </div>
  );
};
