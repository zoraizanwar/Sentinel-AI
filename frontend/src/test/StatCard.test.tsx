import { describe, it, expect } from 'vitest';
import { render, screen } from '@testing-library/react';
import { StatCard } from '../components/common/StatCard';

describe('StatCard Component', () => {
  it('renders title, value, and subtitle', () => {
    render(
      <StatCard
        title="Total Volume"
        value="$1,296,675"
        subtitle="Processed Events"
      />
    );
    expect(screen.getByText('Total Volume')).toBeInTheDocument();
    expect(screen.getByText('$1,296,675')).toBeInTheDocument();
    expect(screen.getByText('Processed Events')).toBeInTheDocument();
  });
});
