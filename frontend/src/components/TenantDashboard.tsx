import React from 'react';
import { useAuth } from '../contexts/AuthContext';
import { useTenant, TenantUsageWarnings } from '../contexts/TenantContext';
import { 
  UserGroupIcon, 
  CpuChipIcon, 
  ChatBubbleLeftRightIcon, 
  CloudArrowUpIcon,
  ChartBarIcon,
  ExclamationTriangleIcon
} from '@heroicons/react/24/outline';

const TenantDashboard: React.FC = () => {
  const { user, tenant } = useAuth();
  // Use optional chaining and fallbacks for API endpoints that might not exist yet
  const { stats, usage, isLoading, refreshStats } = useTenant();

  if (!tenant || !user) {
    return (
      <div className="text-center py-12">
        <p className="text-gray-500">Aucune information de tenant disponible</p>
      </div>
    );
  }

  const getUsageColor = (percentage: number) => {
    if (percentage >= 95) return 'text-red-600 bg-red-100';
    if (percentage >= 80) return 'text-yellow-600 bg-yellow-100';
    return 'text-green-600 bg-green-100';
  };

  const getProgressBarColor = (percentage: number) => {
    if (percentage >= 95) return 'bg-red-500';
    if (percentage >= 80) return 'bg-yellow-500';
    return 'bg-green-500';
  };

  return (
    <div className="space-y-6">
      {/* Tenant Usage Warnings */}
      <TenantUsageWarnings />

      {/* Tenant Overview */}
      <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-lg font-semibold text-gray-900">
            Aperçu du Tenant: {tenant.name}
          </h2>
          <button
            onClick={refreshStats}
            disabled={isLoading}
            className="px-3 py-1.5 text-sm font-medium text-blue-600 bg-blue-50 rounded-md hover:bg-blue-100 disabled:opacity-50"
          >
            {isLoading ? 'Actualisation...' : 'Actualiser'}
          </button>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
          {/* Plan Info */}
          <div className="bg-gradient-to-r from-blue-50 to-indigo-50 rounded-lg p-4">
            <div className="flex items-center">
              <ChartBarIcon className="h-8 w-8 text-blue-600" />
              <div className="ml-3">
                <p className="text-sm font-medium text-gray-600">Plan</p>
                <p className="text-lg font-semibold text-gray-900 capitalize">
                  {tenant.plan}
                </p>
              </div>
            </div>
          </div>

          {/* Status */}
          <div className="bg-gradient-to-r from-green-50 to-emerald-50 rounded-lg p-4">
            <div className="flex items-center">
              <div className={`h-3 w-3 rounded-full mr-2 ${
                tenant.status === 'active' ? 'bg-green-500' : 
                tenant.status === 'trial' ? 'bg-yellow-500' : 'bg-red-500'
              }`} />
              <div>
                <p className="text-sm font-medium text-gray-600">Statut</p>
                <p className="text-lg font-semibold text-gray-900 capitalize">
                  {tenant.status}
                </p>
              </div>
            </div>
          </div>

          {/* Total Conversations */}
          <div className="bg-gradient-to-r from-purple-50 to-pink-50 rounded-lg p-4">
            <div className="flex items-center">
              <ChatBubbleLeftRightIcon className="h-8 w-8 text-purple-600" />
              <div className="ml-3">
                <p className="text-sm font-medium text-gray-600">Conversations</p>
                <p className="text-lg font-semibold text-gray-900">
                  {stats?.total_conversations || 0}
                </p>
              </div>
            </div>
          </div>

          {/* Total Messages */}
          <div className="bg-gradient-to-r from-orange-50 to-red-50 rounded-lg p-4">
            <div className="flex items-center">
              <ChatBubbleLeftRightIcon className="h-8 w-8 text-orange-600" />
              <div className="ml-3">
                <p className="text-sm font-medium text-gray-600">Messages</p>
                <p className="text-lg font-semibold text-gray-900">
                  {stats?.total_messages || 0}
                </p>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Usage Statistics */}
      {usage && (
        <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
          <h3 className="text-lg font-semibold text-gray-900 mb-4">
            Utilisation des Ressources
          </h3>

          <div className="space-y-6">
            {/* Users Usage */}
            <div>
              <div className="flex items-center justify-between mb-2">
                <div className="flex items-center">
                  <UserGroupIcon className="h-5 w-5 text-gray-500 mr-2" />
                  <span className="text-sm font-medium text-gray-700">Utilisateurs</span>
                </div>
                <span className={`px-2 py-1 rounded-full text-xs font-medium ${getUsageColor(usage.users.percentage)}`}>
                  {usage.users.current}/{usage.users.limit} ({usage.users.percentage}%)
                </span>
              </div>
              <div className="w-full bg-gray-200 rounded-full h-2">
                <div
                  className={`h-2 rounded-full transition-all duration-300 ${getProgressBarColor(usage.users.percentage)}`}
                  style={{ width: `${Math.min(usage.users.percentage, 100)}%` }}
                />
              </div>
            </div>

            {/* Agents Usage */}
            <div>
              <div className="flex items-center justify-between mb-2">
                <div className="flex items-center">
                  <CpuChipIcon className="h-5 w-5 text-gray-500 mr-2" />
                  <span className="text-sm font-medium text-gray-700">Agents IA</span>
                </div>
                <span className={`px-2 py-1 rounded-full text-xs font-medium ${getUsageColor(usage.agents.percentage)}`}>
                  {usage.agents.current}/{usage.agents.limit} ({usage.agents.percentage}%)
                </span>
              </div>
              <div className="w-full bg-gray-200 rounded-full h-2">
                <div
                  className={`h-2 rounded-full transition-all duration-300 ${getProgressBarColor(usage.agents.percentage)}`}
                  style={{ width: `${Math.min(usage.agents.percentage, 100)}%` }}
                />
              </div>
            </div>

            {/* Storage Usage */}
            <div>
              <div className="flex items-center justify-between mb-2">
                <div className="flex items-center">
                  <CloudArrowUpIcon className="h-5 w-5 text-gray-500 mr-2" />
                  <span className="text-sm font-medium text-gray-700">Stockage</span>
                </div>
                <span className={`px-2 py-1 rounded-full text-xs font-medium ${getUsageColor(usage.storage.percentage)}`}>
                  {Math.round(usage.storage.current_mb / 1024)}GB/{Math.round(usage.storage.limit_mb / 1024)}GB ({usage.storage.percentage}%)
                </span>
              </div>
              <div className="w-full bg-gray-200 rounded-full h-2">
                <div
                  className={`h-2 rounded-full transition-all duration-300 ${getProgressBarColor(usage.storage.percentage)}`}
                  style={{ width: `${Math.min(usage.storage.percentage, 100)}%` }}
                />
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Quick Actions */}
      <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
        <h3 className="text-lg font-semibold text-gray-900 mb-4">
          Actions Rapides
        </h3>

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          <a
            href="/agents"
            className="flex items-center p-4 bg-blue-50 rounded-lg hover:bg-blue-100 transition-colors"
          >
            <CpuChipIcon className="h-8 w-8 text-blue-600" />
            <div className="ml-3">
              <p className="text-sm font-medium text-blue-900">Gérer les Agents</p>
              <p className="text-xs text-blue-600">Créer et configurer des agents IA</p>
            </div>
          </a>

          <a
            href="/chat"
            className="flex items-center p-4 bg-green-50 rounded-lg hover:bg-green-100 transition-colors"
          >
            <ChatBubbleLeftRightIcon className="h-8 w-8 text-green-600" />
            <div className="ml-3">
              <p className="text-sm font-medium text-green-900">Démarrer un Chat</p>
              <p className="text-xs text-green-600">Interagir avec vos agents IA</p>
            </div>
          </a>

          <a
            href="/file-upload"
            className="flex items-center p-4 bg-purple-50 rounded-lg hover:bg-purple-100 transition-colors"
          >
            <CloudArrowUpIcon className="h-8 w-8 text-purple-600" />
            <div className="ml-3">
              <p className="text-sm font-medium text-purple-900">Télécharger des Fichiers</p>
              <p className="text-xs text-purple-600">Ajouter des documents à la base de connaissances</p>
            </div>
          </a>
        </div>
      </div>

      {/* Tenant Info */}
      <div className="bg-gray-50 rounded-lg p-4">
        <div className="flex items-center text-sm text-gray-600">
          <span className="font-medium">Tenant ID:</span>
          <span className="ml-2 font-mono text-xs bg-gray-200 px-2 py-1 rounded">
            {tenant.id}
          </span>
          <span className="ml-4 font-medium">Créé le:</span>
          <span className="ml-2">
            {new Date(tenant.created_at).toLocaleDateString('fr-FR')}
          </span>
        </div>
      </div>
    </div>
  );
};

export default TenantDashboard;
