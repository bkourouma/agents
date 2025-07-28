import React, { useState } from 'react';
import { useAuth } from '../contexts/AuthContext';
import { ChevronDownIcon, BuildingOfficeIcon, UserGroupIcon, CogIcon } from '@heroicons/react/24/outline';

const TenantHeader: React.FC = () => {
  const { user, tenant, isTenantAdmin } = useAuth();
  const [showTenantMenu, setShowTenantMenu] = useState(false);

  if (!user || !tenant) {
    return null;
  }

  const getPlanBadgeColor = (plan: string) => {
    switch (plan.toLowerCase()) {
      case 'enterprise':
        return 'bg-purple-100 text-purple-800 border-purple-200';
      case 'professional':
        return 'bg-blue-100 text-blue-800 border-blue-200';
      case 'starter':
        return 'bg-green-100 text-green-800 border-green-200';
      case 'free':
      default:
        return 'bg-gray-100 text-gray-800 border-gray-200';
    }
  };

  const getStatusBadgeColor = (status: string) => {
    switch (status.toLowerCase()) {
      case 'active':
        return 'bg-green-100 text-green-800 border-green-200';
      case 'trial':
        return 'bg-yellow-100 text-yellow-800 border-yellow-200';
      case 'suspended':
        return 'bg-red-100 text-red-800 border-red-200';
      default:
        return 'bg-gray-100 text-gray-800 border-gray-200';
    }
  };

  return (
    <div className="bg-white border-b border-gray-200 px-6 py-3">
      <div className="flex items-center justify-between">
        {/* Tenant Info */}
        <div className="flex items-center space-x-4">
          <div className="flex items-center space-x-2">
            <BuildingOfficeIcon className="h-5 w-5 text-gray-500" />
            <div>
              <h2 className="text-sm font-semibold text-gray-900">{tenant.name}</h2>
              <p className="text-xs text-gray-500">Tenant: {tenant.slug}</p>
            </div>
          </div>

          {/* Plan Badge */}
          <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium border ${getPlanBadgeColor(tenant.plan)}`}>
            {tenant.plan.charAt(0).toUpperCase() + tenant.plan.slice(1)}
          </span>

          {/* Status Badge */}
          <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium border ${getStatusBadgeColor(tenant.status)}`}>
            {tenant.status.charAt(0).toUpperCase() + tenant.status.slice(1)}
          </span>
        </div>

        {/* Tenant Stats & Actions */}
        <div className="flex items-center space-x-4">
          {/* Usage Stats */}
          <div className="hidden md:flex items-center space-x-4 text-xs text-gray-500">
            <div className="flex items-center space-x-1">
              <UserGroupIcon className="h-4 w-4" />
              <span>Utilisateurs: {tenant.max_users}</span>
            </div>
            <div className="flex items-center space-x-1">
              <span>🤖</span>
              <span>Agents: {tenant.max_agents}</span>
            </div>
            <div className="flex items-center space-x-1">
              <span>💾</span>
              <span>Stockage: {Math.round(tenant.max_storage_mb / 1024)}GB</span>
            </div>
          </div>

          {/* Tenant Admin Actions */}
          {isTenantAdmin && (
            <div className="relative">
              <button
                onClick={() => setShowTenantMenu(!showTenantMenu)}
                className="flex items-center space-x-1 px-3 py-1.5 text-xs font-medium text-gray-700 bg-gray-100 rounded-md hover:bg-gray-200 transition-colors"
              >
                <CogIcon className="h-4 w-4" />
                <span>Gestion</span>
                <ChevronDownIcon className="h-3 w-3" />
              </button>

              {showTenantMenu && (
                <div className="absolute right-0 mt-2 w-48 bg-white rounded-md shadow-lg border border-gray-200 z-50">
                  <div className="py-1">
                    <a
                      href="/tenant/settings"
                      className="block px-4 py-2 text-sm text-gray-700 hover:bg-gray-100"
                    >
                      Paramètres du tenant
                    </a>
                    <a
                      href="/tenant/users"
                      className="block px-4 py-2 text-sm text-gray-700 hover:bg-gray-100"
                    >
                      Gestion des utilisateurs
                    </a>
                    <a
                      href="/tenant/billing"
                      className="block px-4 py-2 text-sm text-gray-700 hover:bg-gray-100"
                    >
                      Facturation
                    </a>
                    <a
                      href="/tenant/analytics"
                      className="block px-4 py-2 text-sm text-gray-700 hover:bg-gray-100"
                    >
                      Analytiques
                    </a>
                  </div>
                </div>
              )}
            </div>
          )}

          {/* User Role Badge */}
          {isTenantAdmin && (
            <span className="inline-flex items-center px-2 py-1 rounded-full text-xs font-medium bg-indigo-100 text-indigo-800 border border-indigo-200">
              Admin
            </span>
          )}
        </div>
      </div>

      {/* Mobile Stats */}
      <div className="md:hidden mt-2 flex items-center space-x-4 text-xs text-gray-500">
        <div className="flex items-center space-x-1">
          <UserGroupIcon className="h-4 w-4" />
          <span>{tenant.max_users} utilisateurs</span>
        </div>
        <div className="flex items-center space-x-1">
          <span>🤖</span>
          <span>{tenant.max_agents} agents</span>
        </div>
        <div className="flex items-center space-x-1">
          <span>💾</span>
          <span>{Math.round(tenant.max_storage_mb / 1024)}GB</span>
        </div>
      </div>

      {/* Click outside to close menu */}
      {showTenantMenu && (
        <div
          className="fixed inset-0 z-40"
          onClick={() => setShowTenantMenu(false)}
        />
      )}
    </div>
  );
};

export default TenantHeader;
