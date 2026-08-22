import { describe, it, expect } from 'vitest';
import { render, screen } from '@testing-library/react';
import { RiskBadge } from '../components/common/RiskBadge';

describe('RiskBadge Component', () => {
  it('renders LOW risk badge correctly', () => {
    render(<RiskBadge band="LOW" score={15.4} showScore={true} />);
    expect(screen.getByText('LOW')).toBeInTheDocument();
    expect(screen.getByText('(15.4)')).toBeInTheDocument();
  });

  it('renders CRITICAL risk badge correctly', () => {
    render(<RiskBadge band="CRITICAL" score={94.2} showScore={true} />);
    expect(screen.getByText('CRITICAL')).toBeInTheDocument();
    expect(screen.getByText('(94.2)')).toBeInTheDocument();
  });

  it('renders MEDIUM risk badge correctly', () => {
    render(<RiskBadge band="MEDIUM" />);
    expect(screen.getByText('MEDIUM')).toBeInTheDocument();
  });

  it('renders HIGH risk badge correctly', () => {
    render(<RiskBadge band="HIGH" />);
    expect(screen.getByText('HIGH')).toBeInTheDocument();
  });
});
