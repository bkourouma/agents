import React, { createContext, useContext, useEffect, useState } from 'react';
import { api } from '../lib/simple-api';
import toast from 'react-hot-toast';

interface User {
  id: number;
  tenant_id: string;
  email: string;
  username: string;
  full_name?: string;
  bio?: string;
  is_active: boolean;
  is_superuser: boolean;
  is_tenant_admin: boolean;
  created_at: string;
  updated_at?: string;
  last_login?: string;
  avatar_url?: string;
}

interface Tenant {
  id: string;
  name: string;
  slug: string;
  domain?: string;
  status: string;
  plan: string;
  settings: Record<string, any>;
  features: string[];
  tenant_metadata: Record<string, any>;
  max_users: number;
  max_agents: number;
  max_storage_mb: number;
  created_at: string;
  is_active: boolean;
}

interface LoginRequest {
  username: string;
  password: string;
}

interface RegisterRequest {
  email: string;
  username: string;
  password: string;
  full_name?: string;
  bio?: string;
}

interface AuthContextType {
  user: User | null;
  tenant: Tenant | null;
  isLoading: boolean;
  isAuthenticated: boolean;
  isTenantAdmin: boolean;
  login: (credentials: LoginRequest) => Promise<void>;
  register: (userData: RegisterRequest) => Promise<void>;
  logout: () => void;
  refreshTenant: () => Promise<void>;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (context === undefined) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
};

interface AuthProviderProps {
  children: React.ReactNode;
}

export const AuthProvider: React.FC<AuthProviderProps> = ({ children }) => {
  const [user, setUser] = useState<User | null>(null);
  const [tenant, setTenant] = useState<Tenant | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  const isAuthenticated = !!user;
  const isTenantAdmin = user?.is_tenant_admin || false;

  useEffect(() => {
    const initAuth = async () => {
      const token = localStorage.getItem('auth_token');
      const savedUser = localStorage.getItem('user');
      const savedTenant = localStorage.getItem('tenant');

      if (token && savedUser) {
        try {
          // Verify token is still valid by fetching current user
          const currentUser = await api.getCurrentUser();
          setUser(currentUser);

          // Fetch tenant information if user has tenant_id
          if (currentUser.tenant_id) {
            try {
              const tenantData = await api.getTenant(currentUser.tenant_id);
              setTenant(tenantData);
              localStorage.setItem('tenant', JSON.stringify(tenantData));
            } catch (tenantError) {
              console.warn('Failed to fetch tenant data:', tenantError);
              // Use saved tenant data if available
              if (savedTenant) {
                setTenant(JSON.parse(savedTenant));
              }
            }
          }
        } catch (error) {
          // Token is invalid, clear storage
          localStorage.removeItem('auth_token');
          localStorage.removeItem('user');
          localStorage.removeItem('tenant');
        }
      }
      setIsLoading(false);
    };

    initAuth();
  }, []);

  const login = async (credentials: LoginRequest) => {
    try {
      setIsLoading(true);
      const authResponse = await api.login(credentials);

      // Store token
      localStorage.setItem('auth_token', authResponse.access_token);

      // Fetch user data
      const userData = await api.getCurrentUser();
      setUser(userData);
      localStorage.setItem('user', JSON.stringify(userData));

      // Fetch tenant data if user has tenant_id
      if (userData.tenant_id) {
        try {
          // Small delay to ensure token is properly set in axios interceptor
          await new Promise(resolve => setTimeout(resolve, 100));
          const tenantData = await api.getTenant(userData.tenant_id);
          setTenant(tenantData);
          localStorage.setItem('tenant', JSON.stringify(tenantData));
        } catch (tenantError) {
          console.error('Failed to fetch tenant data during login:', tenantError);
          // Don't fail login if tenant fetch fails
        }
      }

      toast.success('Connexion réussie !');
    } catch (error: any) {
      const message = error.response?.data?.detail || 'Échec de la connexion';
      toast.error(message);
      throw error;
    } finally {
      setIsLoading(false);
    }
  };

  const register = async (userData: RegisterRequest) => {
    try {
      setIsLoading(true);
      await api.register(userData);

      // Auto-login after registration
      await login({
        username: userData.username,
        password: userData.password,
      });

      toast.success('Compte créé avec succès !');
    } catch (error: any) {
      const message = error.response?.data?.detail || 'Échec de l\'inscription';
      toast.error(message);
      throw error;
    } finally {
      setIsLoading(false);
    }
  };

  const logout = () => {
    localStorage.removeItem('auth_token');
    localStorage.removeItem('user');
    localStorage.removeItem('tenant');
    setUser(null);
    setTenant(null);
    toast.success('Déconnexion réussie');
  };

  const refreshTenant = async () => {
    if (user?.tenant_id) {
      try {
        const tenantData = await api.getTenant(user.tenant_id);
        setTenant(tenantData);
        localStorage.setItem('tenant', JSON.stringify(tenantData));
      } catch (error) {
        console.error('Failed to refresh tenant data:', error);
        toast.error('Échec de la mise à jour des informations du tenant');
      }
    }
  };

  const value: AuthContextType = {
    user,
    tenant,
    isLoading,
    isAuthenticated,
    isTenantAdmin,
    login,
    register,
    logout,
    refreshTenant,
  };

  return (
    <AuthContext.Provider value={value}>
      {children}
    </AuthContext.Provider>
  );
};
