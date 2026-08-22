import React from 'react';
import { RiskBand } from '../../types/api';

interface RiskBadgeProps {
  band: RiskBand | string;
  score?: number;
  size?: 'sm' | 'md' | 'lg';
  showScore?: boolean;
}

export const RiskBadge: React.FC<RiskBadgeProps> = ({
  band,
  score,
  size = 'md',
  showScore = false,
}) => {
  const normalizedBand = (band || 'LOW').toUpperCase();

  const getStyles = () => {
    switch (normalizedBand) {
      case 'CRITICAL':
        return 'bg-rose-500/15 text-rose-400 border-rose-500/30';
      case 'HIGH':
        return 'bg-orange-500/15 text-orange-400 border-orange-500/30';
      case 'MEDIUM':
        return 'bg-amber-500/15 text-amber-400 border-amber-500/30';
      case 'LOW':
      default:
        return 'bg-emerald-500/15 text-emerald-400 border-emerald-500/30';
    }
  };

  const getSizeStyles = () => {
    switch (size) {
      case 'sm':
        return 'px-2 py-0.5 text-xs';
      case 'lg':
        return 'px-3 py-1.5 text-sm font-semibold';
      case 'md':
      default:
        return 'px-2.5 py-1 text-xs font-medium';
    }
  };

  return (
    <span
      className={`inline-flex items-center gap-1.5 rounded-full border font-mono ${getStyles()} ${getSizeStyles()}`}
    >
      <span className="w-1.5 h-1.5 rounded-full bg-current"></span>
      <span>{normalizedBand}</span>
      {showScore && score !== undefined && (
        <span className="font-semibold opacity-90">({score.toFixed(1)})</span>
      )}
    </span>
  );
};
