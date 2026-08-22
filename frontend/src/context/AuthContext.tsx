import React, { createContext, useContext, useState, useEffect, ReactNode } from 'react';
import { User, OrganizationRole, AuthResponse } from '../types/api';
import { loginUser, registerUser, getCurrentUserProfile } from '../api/endpoints';
import { extractApiError } from '../api/client';

interface AuthContextType {
  user: User | null;
  token: string | null;
  activeOrgId: string | null;
  activeRole: OrganizationRole | null;
  isAuthenticated: boolean;
  isLoading: boolean;
  error: string | null;
  login: (email: string, password: string) => Promise<boolean>;
  register: (email: string, password: string, fullName: string, orgName?: string) => Promise<boolean>;
  logout: () => void;
  switchOrganization: (orgId: string) => void;
  clearError: () => void;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export const AuthProvider: React.FC<{ children: ReactNode }> = ({ children }) => {
  const [user, setUser] = useState<User | null>(null);
  const [token, setToken] = useState<string | null>(() => localStorage.getItem('sentinel_token'));
  const [activeOrgId, setActiveOrgId] = useState<string | null>(() => localStorage.getItem('sentinel_active_org_id'));
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const activeMembership = user?.memberships?.find((m) => m.organization_id === activeOrgId);
  const activeRole: OrganizationRole | null = activeMembership?.role || (user?.memberships?.[0]?.role ?? null);

  useEffect(() => {
    async function loadUser() {
      if (!token) {
        setIsLoading(false);
        return;
      }
      try {
        const profile = await getCurrentUserProfile();
        setUser(profile);
        if (!activeOrgId && profile.memberships?.length > 0) {
          const defaultOrg = profile.memberships[0].organization_id;
          setActiveOrgId(defaultOrg);
          localStorage.setItem('sentinel_active_org_id', defaultOrg);
        }
      } catch (err) {
        logout();
      } finally {
        setIsLoading(false);
      }
    }
    loadUser();
  }, [token]);

  const handleAuthSuccess = async (data: AuthResponse) => {
    localStorage.setItem('sentinel_token', data.access_token);
    setToken(data.access_token);
    if (data.default_organization_id) {
      localStorage.setItem('sentinel_active_org_id', data.default_organization_id);
      setActiveOrgId(data.default_organization_id);
    }
    try {
      const profile = await getCurrentUserProfile();
      setUser(profile);
      const orgId = data.default_organization_id || profile.memberships?.[0]?.organization_id;
      if (orgId) {
        localStorage.setItem('sentinel_active_org_id', orgId);
        setActiveOrgId(orgId);
      }
    } catch {
      setUser({
        id: data.user_id || 'user',
        email: data.email || '',
        full_name: data.full_name || 'User',
        is_active: true,
        created_at: new Date().toISOString(),
        memberships: []
      });
    }
    setError(null);
  };

  const login = async (email: string, password: string): Promise<boolean> => {
    setIsLoading(true);
    setError(null);
    try {
      const data = await loginUser({ email, password });
      await handleAuthSuccess(data);
      return true;
    } catch (err) {
      const apiErr = extractApiError(err);
      setError(apiErr.message);
      return false;
    } finally {
      setIsLoading(false);
    }
  };

  const register = async (email: string, password: string, fullName: string, orgName?: string): Promise<boolean> => {
    setIsLoading(true);
    setError(null);
    try {
      const data = await registerUser({ email, password, full_name: fullName, organization_name: orgName });
      await handleAuthSuccess(data);
      return true;
    } catch (err) {
      const apiErr = extractApiError(err);
      setError(apiErr.message);
      return false;
    } finally {
      setIsLoading(false);
    }
  };

  const logout = () => {
    localStorage.removeItem('sentinel_token');
    localStorage.removeItem('sentinel_active_org_id');
    setToken(null);
    setUser(null);
    setActiveOrgId(null);
  };

  const switchOrganization = (orgId: string) => {
    localStorage.setItem('sentinel_active_org_id', orgId);
    setActiveOrgId(orgId);
  };

  return (
    <AuthContext.Provider
      value={{
        user,
        token,
        activeOrgId,
        activeRole,
        isAuthenticated: !!token && !!user,
        isLoading,
        error,
        login,
        register,
        logout,
        switchOrganization,
        clearError: () => setError(null),
      }}
    >
      {children}
    </AuthContext.Provider>
  );
};

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (!context) {
    return {
      user: null,
      token: null,
      activeOrgId: typeof window !== 'undefined' ? localStorage.getItem('sentinel_active_org_id') : null,
      activeRole: null,
      isAuthenticated: false,
      isLoading: false,
      error: null,
      login: async () => false,
      register: async () => false,
      logout: () => {},
      switchOrganization: () => {},
      clearError: () => {},
    };
  }
  return context;
};
