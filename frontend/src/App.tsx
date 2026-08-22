import React from 'react';
import { BrowserRouter, Routes, Route, Navigate, useLocation } from 'react-router-dom';
import { AuthProvider, useAuth } from './context/AuthContext';
import { WorkspaceProvider } from './context/WorkspaceContext';
import { AnalysisProvider } from './context/AnalysisContext';
import { ErrorBoundary } from './components/common/ErrorBoundary';
import { AppLayout } from './components/layout/AppLayout';

import { Login } from './pages/Login';
import { Register } from './pages/Register';
import { OrganizationDashboard } from './pages/OrganizationDashboard';
import { Clients } from './pages/Clients';
import { ClientDetail } from './pages/ClientDetail';
import { Analyses } from './pages/Analyses';
import { AuditLogs } from './pages/AuditLogs';
import { Settings } from './pages/Settings';

import { Overview } from './pages/Overview';
import { Transactions } from './pages/Transactions';
import { Analytics } from './pages/Analytics';
import { Investigation } from './pages/Investigation';
import { Dataset } from './pages/Dataset';
import { Reports } from './pages/Reports';
import { UploadView } from './pages/UploadView';

const ProtectedRoute: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const { isAuthenticated, isLoading } = useAuth();
  const location = useLocation();

  if (isLoading) {
    return (
      <div className="min-h-screen bg-surface-dark flex items-center justify-center text-xs text-slate-400 font-mono">
        Authenticating Sentinel AI workspace...
      </div>
    );
  }

  if (!isAuthenticated) {
    return <Navigate to="/login" state={{ from: location }} replace />;
  }

  return <>{children}</>;
};

export const App: React.FC = () => {
  return (
    <ErrorBoundary>
      <AuthProvider>
        <WorkspaceProvider>
          <AnalysisProvider>
            <BrowserRouter>
              <Routes>
                {/* Public Authentication Routes */}
                <Route path="/login" element={<Login />} />
                <Route path="/register" element={<Register />} />

                {/* Protected Workspace Routes */}
                <Route
                  element={
                    <ProtectedRoute>
                      <AppLayout />
                    </ProtectedRoute>
                  }
                >
                  {/* Multi-Tenant Platform Workspace */}
                  <Route path="/org-dashboard" element={<OrganizationDashboard />} />
                  <Route path="/clients" element={<Clients />} />
                  <Route path="/clients/:clientId" element={<ClientDetail />} />
                  <Route path="/analyses" element={<Analyses />} />
                  <Route path="/audit-logs" element={<AuditLogs />} />
                  <Route path="/settings" element={<Settings />} />

                  {/* ML Analysis & Deep Investigation Routes */}
                  <Route path="/" element={<Overview />} />
                  <Route path="/transactions" element={<Transactions />} />
                  <Route path="/analytics" element={<Analytics />} />
                  <Route path="/investigation" element={<Investigation />} />
                  <Route path="/dataset" element={<Dataset />} />
                  <Route path="/reports" element={<Reports />} />
                  <Route path="/upload" element={<UploadView />} />

                  {/* Fallback */}
                  <Route path="*" element={<Navigate to="/org-dashboard" replace />} />
                </Route>
              </Routes>
            </BrowserRouter>
          </AnalysisProvider>
        </WorkspaceProvider>
      </AuthProvider>
    </ErrorBoundary>
  );
};

export default App;
