import React, { useState, useEffect, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  Search,
  ChevronLeft,
  ChevronRight,
  ArrowUpDown,
  RefreshCw,
  ExternalLink,
} from 'lucide-react';
import { useAnalysis } from '../context/AnalysisContext';
import { useAuth } from '../context/AuthContext';
import { getTransactions, getOrgTransactions, TransactionQueryParams } from '../api/endpoints';
import { PaginatedTransactionsResponse } from '../types/api';
import { RiskBadge } from '../components/common/RiskBadge';
import { TableSkeleton } from '../components/common/Skeleton';
import { EmptyState } from '../components/common/EmptyState';
import { ErrorMessage } from '../components/common/ErrorMessage';
import { extractApiError } from '../api/client';

export const Transactions: React.FC = () => {
  const { analysisId, openInvestigation } = useAnalysis();
  const { activeOrgId } = useAuth();
  const navigate = useNavigate();
  const [data, setData] = useState<PaginatedTransactionsResponse | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Filter & Pagination State
  const [page, setPage] = useState(1);
  const [pageSize, setPageSize] = useState(25);
  const [sortBy, setSortBy] = useState('risk_score');
  const [sortOrder, setSortOrder] = useState<'asc' | 'desc'>('desc');
  const [riskBand, setRiskBand] = useState<string>('');
  const [isFraud, setIsFraud] = useState<string>('');
  const [search, setSearch] = useState('');
  const [searchInput, setSearchInput] = useState('');
  const [minAmount, setMinAmount] = useState<string>('');
  const [maxAmount, setMaxAmount] = useState<string>('');

  const fetchTransactions = useCallback(async () => {
    if (!analysisId) return;
    setIsLoading(true);
    setError(null);

    const params: TransactionQueryParams = {
      page,
      page_size: pageSize,
      sort_by: sortBy,
      sort_order: sortOrder,
    };

    if (riskBand) params.risk_band = riskBand;
    if (isFraud !== '') params.is_fraud = Number(isFraud);
    if (search.trim()) params.search = search.trim();
    if (minAmount) params.min_amount = parseFloat(minAmount);
    if (maxAmount) params.max_amount = parseFloat(maxAmount);

    try {
      let resp: PaginatedTransactionsResponse | null = null;
      if (activeOrgId) {
        try {
          resp = await getOrgTransactions(activeOrgId, analysisId, params);
        } catch {
          // fallback
        }
      }
      if (!resp) {
        resp = await getTransactions(analysisId, params);
      }
      setData(resp);
    } catch (err) {
      const apiErr = extractApiError(err);
      setError(apiErr.message);
    } finally {
      setIsLoading(false);
    }
  }, [analysisId, activeOrgId, page, pageSize, sortBy, sortOrder, riskBand, isFraud, search, minAmount, maxAmount]);

  useEffect(() => {
    fetchTransactions();
  }, [fetchTransactions]);

  const handleSearchSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    setPage(1);
    setSearch(searchInput);
  };

  const handleSortToggle = (column: string) => {
    if (sortBy === column) {
      setSortOrder(sortOrder === 'asc' ? 'desc' : 'asc');
    } else {
      setSortBy(column);
      setSortOrder('desc');
    }
    setPage(1);
  };

  if (!analysisId) {
    return (
      <EmptyState
        title="No Active Dataset Session"
        description="Upload a transaction dataset or select an analysis from history to explore and filter individual transaction predictions."
        actionLabel="Upload Dataset"
        onAction={() => navigate('/upload')}
      />
    );
  }

  return (
    <div className="space-y-6">
      {/* Control Bar & Filter Drawer */}
      <div className="bg-surface rounded-xl border border-surface-border p-5 space-y-4">
        <div className="flex flex-col lg:flex-row items-stretch lg:items-center justify-between gap-4">
          {/* Search Form */}
          <form onSubmit={handleSearchSubmit} className="flex-1 flex gap-2">
            <div className="relative flex-1">
              <Search className="w-4 h-4 text-slate-400 absolute left-3.5 top-1/2 -translate-y-1/2" />
              <input
                type="text"
                placeholder="Search transaction ID, merchant, category, city, state..."
                value={searchInput}
                onChange={(e) => setSearchInput(e.target.value)}
                className="w-full pl-10 pr-4 py-2 bg-surface-elevated border border-surface-border rounded-lg text-sm text-white placeholder-slate-400 focus:outline-hidden focus:border-rose-500 transition-colors"
              />
            </div>
            <button
              type="submit"
              className="px-4 py-2 text-xs font-semibold text-white bg-rose-600 hover:bg-rose-500 rounded-lg transition-colors cursor-pointer"
            >
              Search
            </button>
          </form>

          {/* Quick Refresh */}
          <button
            onClick={fetchTransactions}
            disabled={isLoading}
            className="inline-flex items-center gap-1.5 px-3 py-2 text-xs font-medium text-slate-300 hover:text-white bg-surface-elevated hover:bg-surface-hover border border-surface-border rounded-lg transition-colors cursor-pointer disabled:opacity-50"
          >
            <RefreshCw className={`w-3.5 h-3.5 ${isLoading ? 'animate-spin' : ''}`} />
            Refresh
          </button>
        </div>

        {/* Filter Row */}
        <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-5 gap-3 pt-2 border-t border-surface-border text-xs">
          {/* Risk Band */}
          <div>
            <label className="block text-slate-400 font-medium mb-1">Risk Band</label>
            <select
              value={riskBand}
              onChange={(e) => {
                setRiskBand(e.target.value);
                setPage(1);
              }}
              className="w-full px-2.5 py-1.5 bg-surface-elevated border border-surface-border rounded-md text-slate-200 focus:outline-hidden focus:border-rose-500"
            >
              <option value="">All Risk Bands</option>
              <option value="CRITICAL">Critical (80-100)</option>
              <option value="HIGH">High (50-80)</option>
              <option value="MEDIUM">Medium (20-50)</option>
              <option value="LOW">Low (0-20)</option>
            </select>
          </div>

          {/* Actual Fraud Flag */}
          <div>
            <label className="block text-slate-400 font-medium mb-1">Actual Status</label>
            <select
              value={isFraud}
              onChange={(e) => {
                setIsFraud(e.target.value);
                setPage(1);
              }}
              className="w-full px-2.5 py-1.5 bg-surface-elevated border border-surface-border rounded-md text-slate-200 focus:outline-hidden focus:border-rose-500"
            >
              <option value="">All Transactions</option>
              <option value="1">Confirmed Fraud</option>
              <option value="0">Legitimate Only</option>
            </select>
          </div>

          {/* Min Amount */}
          <div>
            <label className="block text-slate-400 font-medium mb-1">Min Amount ($)</label>
            <input
              type="number"
              placeholder="0.00"
              value={minAmount}
              onChange={(e) => {
                setMinAmount(e.target.value);
                setPage(1);
              }}
              className="w-full px-2.5 py-1.5 bg-surface-elevated border border-surface-border rounded-md text-slate-200 focus:outline-hidden focus:border-rose-500 font-mono"
            />
          </div>

          {/* Max Amount */}
          <div>
            <label className="block text-slate-400 font-medium mb-1">Max Amount ($)</label>
            <input
              type="number"
              placeholder="10000.00"
              value={maxAmount}
              onChange={(e) => {
                setMaxAmount(e.target.value);
                setPage(1);
              }}
              className="w-full px-2.5 py-1.5 bg-surface-elevated border border-surface-border rounded-md text-slate-200 focus:outline-hidden focus:border-rose-500 font-mono"
            />
          </div>

          {/* Page Size */}
          <div>
            <label className="block text-slate-400 font-medium mb-1">Page Size</label>
            <select
              value={pageSize}
              onChange={(e) => {
                setPageSize(Number(e.target.value));
                setPage(1);
              }}
              className="w-full px-2.5 py-1.5 bg-surface-elevated border border-surface-border rounded-md text-slate-200 focus:outline-hidden focus:border-rose-500"
            >
              <option value="25">25 per page</option>
              <option value="50">50 per page</option>
              <option value="100">100 per page</option>
            </select>
          </div>
        </div>
      </div>

      {/* Transactions Data Table */}
      {error ? (
        <ErrorMessage title="Transaction Query Error" message={error} onRetry={fetchTransactions} />
      ) : isLoading && !data ? (
        <TableSkeleton rows={pageSize} />
      ) : data ? (
        <div className="bg-surface rounded-xl border border-surface-border overflow-hidden shadow-sm">
          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs">
              <thead className="bg-surface-elevated border-b border-surface-border text-slate-400 font-semibold uppercase tracking-wider">
                <tr>
                  <th className="py-3 px-4">Transaction ID</th>
                  <th
                    className="py-3 px-4 cursor-pointer hover:text-white"
                    onClick={() => handleSortToggle('trans_date_trans_time')}
                  >
                    <div className="flex items-center gap-1">
                      <span>Timestamp</span>
                      <ArrowUpDown className="w-3 h-3" />
                    </div>
                  </th>
                  <th
                    className="py-3 px-4 cursor-pointer hover:text-white font-mono"
                    onClick={() => handleSortToggle('amt')}
                  >
                    <div className="flex items-center gap-1">
                      <span>Amount</span>
                      <ArrowUpDown className="w-3 h-3" />
                    </div>
                  </th>
                  <th className="py-3 px-4">Merchant</th>
                  <th className="py-3 px-4">Category</th>
                  <th className="py-3 px-4">Location</th>
                  <th
                    className="py-3 px-4 cursor-pointer hover:text-white"
                    onClick={() => handleSortToggle('risk_score')}
                  >
                    <div className="flex items-center gap-1">
                      <span>Risk Score</span>
                      <ArrowUpDown className="w-3 h-3" />
                    </div>
                  </th>
                  <th className="py-3 px-4">Risk Band</th>
                  <th className="py-3 px-4">Status</th>
                  <th className="py-3 px-4 text-right">Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-surface-border font-mono">
                {data.transactions.length === 0 ? (
                  <tr>
                    <td colSpan={10} className="py-8 text-center text-slate-400">
                      No transactions matched the specified filter criteria.
                    </td>
                  </tr>
                ) : (
                  data.transactions.map((tx) => (
                    <tr
                      key={tx.transaction_id}
                      onClick={() => openInvestigation(tx.transaction_id)}
                      className="hover:bg-surface-hover/80 transition-colors cursor-pointer group"
                    >
                      <td className="py-3 px-4 text-slate-300 font-medium font-mono text-[11px] truncate max-w-[120px]">
                        {tx.transaction_id}
                      </td>
                      <td className="py-3 px-4 text-slate-400 text-[11px] whitespace-nowrap">
                        {tx.timestamp || 'N/A'}
                      </td>
                      <td className="py-3 px-4 text-white font-semibold">
                        ${tx.amount.toFixed(2)}
                      </td>
                      <td className="py-3 px-4 text-slate-300 font-sans truncate max-w-[140px]">
                        {tx.merchant || 'N/A'}
                      </td>
                      <td className="py-3 px-4 text-slate-400 font-sans capitalize">
                        {tx.category ? tx.category.replace('_', ' ') : 'N/A'}
                      </td>
                      <td className="py-3 px-4 text-slate-400 font-sans text-[11px]">
                        {tx.city && tx.state ? `${tx.city}, ${tx.state}` : 'N/A'}
                      </td>
                      <td className="py-3 px-4 font-bold text-white">
                        {tx.risk_score.toFixed(1)}
                      </td>
                      <td className="py-3 px-4 font-sans">
                        <RiskBadge band={tx.risk_band} size="sm" />
                      </td>
                      <td className="py-3 px-4 font-sans">
                        {tx.is_actual_fraud === 1 ? (
                          <span className="text-[10px] font-semibold text-rose-400 bg-rose-500/15 border border-rose-500/30 px-2 py-0.5 rounded">
                            FRAUD
                          </span>
                        ) : tx.is_actual_fraud === 0 ? (
                          <span className="text-[10px] font-medium text-slate-400 bg-surface-elevated px-2 py-0.5 rounded">
                            LEGIT
                          </span>
                        ) : (
                          <span className="text-[10px] text-slate-500">—</span>
                        )}
                      </td>
                      <td className="py-3 px-4 text-right">
                        <button
                          onClick={(e) => {
                            e.stopPropagation();
                            openInvestigation(tx.transaction_id);
                          }}
                          className="inline-flex items-center gap-1 px-2.5 py-1 text-[11px] font-semibold text-rose-300 hover:text-white bg-rose-500/10 hover:bg-rose-500/20 border border-rose-500/20 rounded transition-colors cursor-pointer"
                        >
                          <span>Explain</span>
                          <ExternalLink className="w-3 h-3" />
                        </button>
                      </td>
                    </tr>
                  ))
                )}
              </tbody>
            </table>
          </div>

          {/* Pagination Footer */}
          <div className="px-6 py-4 border-t border-surface-border flex items-center justify-between bg-surface-elevated/40">
            <span className="text-xs text-slate-400 font-mono">
              Showing {(data.page - 1) * data.page_size + 1} to{' '}
              {Math.min(data.page * data.page_size, data.total_matching)} of{' '}
              {data.total_matching.toLocaleString()} matching records
            </span>

            <div className="flex items-center gap-2">
              <button
                onClick={() => setPage(page - 1)}
                disabled={page <= 1 || isLoading}
                className="inline-flex items-center gap-1 px-3 py-1.5 text-xs font-medium text-slate-300 hover:text-white bg-surface-elevated hover:bg-surface-hover border border-surface-border rounded-lg transition-colors disabled:opacity-40 cursor-pointer"
              >
                <ChevronLeft className="w-3.5 h-3.5" />
                Previous
              </button>
              <span className="text-xs font-mono text-slate-300 px-2">
                Page {data.page} of {data.total_pages}
              </span>
              <button
                onClick={() => setPage(page + 1)}
                disabled={page >= data.total_pages || isLoading}
                className="inline-flex items-center gap-1 px-3 py-1.5 text-xs font-medium text-slate-300 hover:text-white bg-surface-elevated hover:bg-surface-hover border border-surface-border rounded-lg transition-colors disabled:opacity-40 cursor-pointer"
              >
                Next
                <ChevronRight className="w-3.5 h-3.5" />
              </button>
            </div>
          </div>
        </div>
      ) : null}
    </div>
  );
};
