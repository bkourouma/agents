import React from 'react';
import TenantDashboard from '../components/TenantDashboard';
import { useAuth } from '../contexts/AuthContext';

const DashboardPage: React.FC = () => {
  const { tenant } = useAuth();

  return (
    <div className="space-y-8">
      {/* Header Section */}
      <div className="bg-gradient-to-r from-primary-600 to-primary-700 rounded-xl p-8 text-white">
        <h1 className="text-3xl font-bold mb-2">Tableau de bord</h1>
        <p className="text-primary-100 text-lg">
          Bienvenue sur votre tableau de bord de la Plateforme d'Agents IA
          {tenant && <span className="block text-sm mt-1">Tenant: {tenant.name}</span>}
        </p>
      </div>

      {/* Tenant Dashboard */}
      <TenantDashboard />
    </div>
  );
};

export default DashboardPage;
