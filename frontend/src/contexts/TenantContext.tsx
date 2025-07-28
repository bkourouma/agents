import React, { createContext, useContext, useEffect, useState } from 'react';
import { useAuth } from './AuthContext';
import { api } from '../lib/simple-api';
import toast from 'react-hot-toast';

interface TenantStats {
  total_users: number;
  active_users: number;
  total_agents: number;
  active_agents: number;
  total_conversations: number;
  total_messages: number;
  storage_used_mb: number;
  storage_percentage: number;
}

interface TenantUsage {
  users: {
    current: number;
    limit: number;
    percentage: number;
  };
  agents: {
    current: number;
    limit: number;
    percentage: number;
  };
  storage: {
    current_mb: number;
    limit_mb: number;
    percentage: number;
  };
  conversations: {
    total: number;
    this_month: number;
  };
}

interface TenantContextType {
  stats: TenantStats | null;
  usage: TenantUsage | null;
  isLoading: boolean;
  refreshStats: () => Promise<void>;
  refreshUsage: () => Promise<void>;
  canCreateAgent: boolean;
  canAddUser: boolean;
  storageWarning: boolean;
}

const TenantContext = createContext<TenantContextType | undefined>(undefined);

export const useTenant = () => {
  const context = useContext(TenantContext);
  if (context === undefined) {
    throw new Error('useTenant must be used within a TenantProvider');
  }
  return context;
};

interface TenantProviderProps {
  children: React.ReactNode;
}

export const TenantProvider: React.FC<TenantProviderProps> = ({ children }) => {
  const { user, tenant, isAuthenticated } = useAuth();
  const [stats, setStats] = useState<TenantStats | null>(null);
  const [usage, setUsage] = useState<TenantUsage | null>(null);
  const [isLoading, setIsLoading] = useState(false);

  // Calculate derived values
  const canCreateAgent = usage ? usage.agents.current < usage.agents.limit : false;
  const canAddUser = usage ? usage.users.current < usage.users.limit : false;
  const storageWarning = usage ? usage.storage.percentage > 80 : false;

  const refreshStats = async () => {
    if (!tenant?.id || !isAuthenticated) return;

    try {
      setIsLoading(true);
      const statsData = await api.getTenantStats(tenant.id);
      setStats(statsData);
    } catch (error) {
      console.warn('Tenant stats endpoint not available yet:', error);
      // Set default stats for development
      setStats({
        total_users: 1,
        active_users: 1,
        total_agents: 0,
        active_agents: 0,
        total_conversations: 0,
        total_messages: 0,
        storage_used_mb: 0,
        storage_percentage: 0,
      });
    } finally {
      setIsLoading(false);
    }
  };

  const refreshUsage = async () => {
    if (!tenant?.id || !isAuthenticated) return;

    try {
      const usageData = await api.getTenantUsage(tenant.id);
      setUsage(usageData);
    } catch (error) {
      console.error('Failed to fetch tenant usage:', error);
      toast.error('Échec du chargement de l\'utilisation du tenant');
    }
  };

  // Load initial data when tenant changes
  useEffect(() => {
    if (tenant?.id && isAuthenticated) {
      refreshStats();
      refreshUsage();
    } else {
      setStats(null);
      setUsage(null);
    }
  }, [tenant?.id, isAuthenticated]);

  // Show storage warning when approaching limit
  useEffect(() => {
    if (storageWarning && usage) {
      toast.warning(
        `Attention: Vous utilisez ${usage.storage.percentage}% de votre espace de stockage`,
        { duration: 6000 }
      );
    }
  }, [storageWarning, usage]);

  const value: TenantContextType = {
    stats,
    usage,
    isLoading,
    refreshStats,
    refreshUsage,
    canCreateAgent,
    canAddUser,
    storageWarning,
  };

  return (
    <TenantContext.Provider value={value}>
      {children}
    </TenantContext.Provider>
  );
};

// Hook for checking tenant permissions
export const useTenantPermissions = () => {
  const { user, isTenantAdmin } = useAuth();
  const { canCreateAgent, canAddUser } = useTenant();

  return {
    canManageTenant: isTenantAdmin,
    canCreateAgent: canCreateAgent && (isTenantAdmin || user?.is_active),
    canAddUser: canAddUser && isTenantAdmin,
    canViewAnalytics: isTenantAdmin,
    canManageBilling: isTenantAdmin,
    canManageSettings: isTenantAdmin,
  };
};

// Hook for tenant-aware API calls
export const useTenantApi = () => {
  const { tenant } = useAuth();

  const withTenantContext = <T extends any[]>(
    apiCall: (...args: T) => Promise<any>
  ) => {
    return async (...args: T) => {
      if (!tenant?.id) {
        throw new Error('No tenant context available');
      }
      return apiCall(...args);
    };
  };

  return {
    withTenantContext,
    tenantId: tenant?.id,
  };
};

// Component for displaying tenant usage warnings
export const TenantUsageWarnings: React.FC = () => {
  const { usage, storageWarning } = useTenant();
  const { isTenantAdmin } = useAuth();

  if (!usage || !isTenantAdmin) return null;

  const warnings = [];

  // Agent limit warning
  if (usage.agents.percentage > 80) {
    warnings.push({
      type: 'agents',
      message: `Vous utilisez ${usage.agents.current}/${usage.agents.limit} agents (${usage.agents.percentage}%)`,
      severity: usage.agents.percentage > 95 ? 'error' : 'warning',
    });
  }

  // User limit warning
  if (usage.users.percentage > 80) {
    warnings.push({
      type: 'users',
      message: `Vous avez ${usage.users.current}/${usage.users.limit} utilisateurs (${usage.users.percentage}%)`,
      severity: usage.users.percentage > 95 ? 'error' : 'warning',
    });
  }

  // Storage warning
  if (storageWarning) {
    warnings.push({
      type: 'storage',
      message: `Stockage: ${Math.round(usage.storage.current_mb / 1024)}GB/${Math.round(usage.storage.limit_mb / 1024)}GB (${usage.storage.percentage}%)`,
      severity: usage.storage.percentage > 95 ? 'error' : 'warning',
    });
  }

  if (warnings.length === 0) return null;

  return (
    <div className="space-y-2 mb-4">
      {warnings.map((warning, index) => (
        <div
          key={index}
          className={`p-3 rounded-md text-sm ${
            warning.severity === 'error'
              ? 'bg-red-50 text-red-800 border border-red-200'
              : 'bg-yellow-50 text-yellow-800 border border-yellow-200'
          }`}
        >
          <div className="flex items-center">
            <span className="mr-2">
              {warning.severity === 'error' ? '🚨' : '⚠️'}
            </span>
            <span>{warning.message}</span>
          </div>
        </div>
      ))}
    </div>
  );
};

export default TenantProvider;
