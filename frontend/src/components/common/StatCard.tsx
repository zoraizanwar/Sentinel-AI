import React, { ReactNode } from 'react';

interface StatCardProps {
  title: string;
  value: string | number;
  subtitle?: string;
  icon?: ReactNode;
  trend?: {
    value: string;
    isNegative?: boolean;
  };
  highlight?: 'normal' | 'danger' | 'warning' | 'success';
}

export const StatCard: React.FC<StatCardProps> = ({
  title,
  value,
  subtitle,
  icon,
  trend,
  highlight = 'normal',
}) => {
  const getHighlightBorder = () => {
    switch (highlight) {
      case 'danger':
        return 'border-rose-500/30 hover:border-rose-500/50';
      case 'warning':
        return 'border-amber-500/30 hover:border-amber-500/50';
      case 'success':
        return 'border-emerald-500/30 hover:border-emerald-500/50';
      case 'normal':
      default:
        return 'border-surface-border hover:border-surface-subtle';
    }
  };

  return (
    <div
      className={`bg-surface rounded-xl border p-5 transition-all duration-200 shadow-sm ${getHighlightBorder()}`}
    >
      <div className="flex items-center justify-between">
        <span className="text-xs font-semibold uppercase tracking-wider text-slate-400">
          {title}
        </span>
        {icon && <div className="text-slate-400">{icon}</div>}
      </div>

      <div className="mt-3 flex items-baseline gap-2">
        <span className="text-2xl font-bold tracking-tight text-white font-mono">
          {value}
        </span>
        {trend && (
          <span
            className={`text-xs font-medium ${
              trend.isNegative ? 'text-rose-400' : 'text-emerald-400'
            }`}
          >
            {trend.value}
          </span>
        )}
      </div>

      {subtitle && (
        <p className="mt-1 text-xs text-slate-400 truncate">{subtitle}</p>
      )}
    </div>
  );
};
