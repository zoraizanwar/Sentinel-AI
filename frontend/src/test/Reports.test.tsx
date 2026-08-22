import { describe, it, expect } from 'vitest';
import { render, screen } from '@testing-library/react';
import { BrowserRouter } from 'react-router-dom';
import { Reports } from '../pages/Reports';
import { AnalysisProvider } from '../context/AnalysisContext';

describe('Reports Page Component', () => {
  it('renders empty state when no dataset is active', () => {
    render(
      <AnalysisProvider>
        <BrowserRouter>
          <Reports />
        </BrowserRouter>
      </AnalysisProvider>
    );

    expect(screen.getByText('No Active Dataset Loaded')).toBeInTheDocument();
  });
});
