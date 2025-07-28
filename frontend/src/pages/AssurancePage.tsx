import React, { useState, useEffect } from 'react';
import {
  Users,
  FileText,
  ShoppingCart,
  Shield,
  CreditCard,
  AlertTriangle,
  Search,
  Plus,
  TrendingUp,
  Calendar,
  Bell,
  Calculator
} from 'lucide-react';
import CustomerManagement from '../components/Insurance/CustomerManagement';
import ProductManagement from '../components/Insurance/ProductManagement';
import OrderManagement from '../components/Insurance/OrderManagement';
import ClaimsManagement from '../components/Insurance/ClaimsManagement';
import QuotesManagement from '../components/Insurance/QuotesManagement';
import ContractManagement from '../components/Insurance/ContractManagement';
import PaymentManagement from '../components/Insurance/PaymentManagement';

interface DashboardStats {
  totalClients: number;
  activeContracts: number;
  pendingOrders: number;
  openClaims: number;
  monthlyRevenue: number;
  expiringContracts: number;
}

interface RecentActivity {
  id: string;
  type: 'client' | 'order' | 'contract' | 'claim';
  description: string;
  timestamp: string;
  status: string;
}

const AssurancePage: React.FC = () => {
  const [activeTab, setActiveTab] = useState('dashboard');
  const [stats, setStats] = useState<DashboardStats>({
    totalClients: 0,
    activeContracts: 0,
    pendingOrders: 0,
    openClaims: 0,
    monthlyRevenue: 0,
    expiringContracts: 0
  });
  const [recentActivity, setRecentActivity] = useState<RecentActivity[]>([]);
  const [searchQuery, setSearchQuery] = useState('');

  useEffect(() => {
    // Simuler le chargement des données
    setStats({
      totalClients: 1247,
      activeContracts: 892,
      pendingOrders: 23,
      openClaims: 8,
      monthlyRevenue: 125000,
      expiringContracts: 15
    });

    setRecentActivity([
      {
        id: '1',
        type: 'client',
        description: 'Nouveau client créé: Marie Dubois',
        timestamp: '2024-01-15 14:30',
        status: 'success'
      },
      {
        id: '2',
        type: 'order',
        description: 'Commande approuvée: ORD-20240115-000123',
        timestamp: '2024-01-15 13:45',
        status: 'success'
      },
      {
        id: '3',
        type: 'claim',
        description: 'Nouvelle réclamation: REC-20240115-000045',
        timestamp: '2024-01-15 12:20',
        status: 'pending'
      }
    ]);
  }, []);

  // Écouter l'événement de changement d'onglet vers les commandes
  useEffect(() => {
    const handleSwitchToOrders = (event: CustomEvent) => {
      setActiveTab('commandes');

      // Optionnel : afficher une notification
      const orderNumber = event.detail?.orderNumber;
      if (orderNumber) {
        console.log(`Switching to orders tab for order: ${orderNumber}`);
      }
    };

    window.addEventListener('switchToOrdersTab', handleSwitchToOrders as EventListener);

    return () => {
      window.removeEventListener('switchToOrdersTab', handleSwitchToOrders as EventListener);
    };
  }, []);

  const tabs = [
    { id: 'dashboard', label: 'Tableau de bord', icon: TrendingUp },
    { id: 'clients', label: 'Clients', icon: Users },
    { id: 'produits', label: 'Produits', icon: FileText },
    { id: 'devis', label: 'Devis', icon: Calculator },
    { id: 'commandes', label: 'Commandes', icon: ShoppingCart },
    { id: 'contrats', label: 'Contrats', icon: Shield },
    { id: 'reclamations', label: 'Réclamations', icon: AlertTriangle },
    { id: 'paiements', label: 'Paiements', icon: CreditCard }
  ];

  const StatCard: React.FC<{
    title: string;
    value: string | number;
    icon: React.ReactNode;
    color: string;
    trend?: string;
  }> = ({ title, value, icon, color, trend }) => (
    <div className="bg-white rounded-lg shadow-md p-6 border-l-4" style={{ borderLeftColor: color }}>
      <div className="flex items-center justify-between">
        <div>
          <p className="text-sm font-medium text-gray-600">{title}</p>
          <p className="text-2xl font-bold text-gray-900">{value}</p>
          {trend && (
            <p className="text-sm text-green-600 mt-1">
              <TrendingUp className="inline w-4 h-4 mr-1" />
              {trend}
            </p>
          )}
        </div>
        <div className="p-3 rounded-full" style={{ backgroundColor: `${color}20` }}>
          {icon}
        </div>
      </div>
    </div>
  );

  const renderDashboard = () => (
    <div className="space-y-6">
      {/* Statistiques principales */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        <StatCard
          title="Total Clients"
          value={stats.totalClients.toLocaleString()}
          icon={<Users className="w-6 h-6 text-blue-600" />}
          color="#3B82F6"
          trend="+12% ce mois"
        />
        <StatCard
          title="Contrats Actifs"
          value={stats.activeContracts.toLocaleString()}
          icon={<Shield className="w-6 h-6 text-green-600" />}
          color="#10B981"
          trend="+8% ce mois"
        />
        <StatCard
          title="Commandes en Attente"
          value={stats.pendingOrders}
          icon={<ShoppingCart className="w-6 h-6 text-orange-600" />}
          color="#F59E0B"
        />
        <StatCard
          title="Réclamations Ouvertes"
          value={stats.openClaims}
          icon={<AlertTriangle className="w-6 h-6 text-red-600" />}
          color="#EF4444"
        />
      </div>

      {/* Revenus et alertes */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <StatCard
          title="Revenus Mensuels"
          value={`${stats.monthlyRevenue.toLocaleString()} €`}
          icon={<CreditCard className="w-6 h-6 text-purple-600" />}
          color="#8B5CF6"
          trend="+15% vs mois dernier"
        />
        <StatCard
          title="Contrats Expirant"
          value={`${stats.expiringContracts} (30 jours)`}
          icon={<Calendar className="w-6 h-6 text-yellow-600" />}
          color="#EAB308"
        />
      </div>

      {/* Activité récente */}
      <div className="bg-white rounded-lg shadow-md p-6">
        <div className="flex items-center justify-between mb-4">
          <h3 className="text-lg font-semibold text-gray-900">Activité Récente</h3>
          <Bell className="w-5 h-5 text-gray-400" />
        </div>
        <div className="space-y-3">
          {recentActivity.map((activity) => (
            <div key={activity.id} className="flex items-center space-x-3 p-3 bg-gray-50 rounded-lg">
              <div className={`w-2 h-2 rounded-full ${
                activity.status === 'success' ? 'bg-green-500' : 
                activity.status === 'pending' ? 'bg-yellow-500' : 'bg-red-500'
              }`} />
              <div className="flex-1">
                <p className="text-sm text-gray-900">{activity.description}</p>
                <p className="text-xs text-gray-500">{activity.timestamp}</p>
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Actions rapides */}
      <div className="bg-white rounded-lg shadow-md p-6">
        <h3 className="text-lg font-semibold text-gray-900 mb-4">Actions Rapides</h3>
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          <button className="flex flex-col items-center p-4 bg-blue-50 rounded-lg hover:bg-blue-100 transition-colors">
            <Plus className="w-6 h-6 text-blue-600 mb-2" />
            <span className="text-sm font-medium text-blue-900">Nouveau Client</span>
          </button>
          <button className="flex flex-col items-center p-4 bg-green-50 rounded-lg hover:bg-green-100 transition-colors">
            <ShoppingCart className="w-6 h-6 text-green-600 mb-2" />
            <span className="text-sm font-medium text-green-900">Nouvelle Commande</span>
          </button>
          <button className="flex flex-col items-center p-4 bg-purple-50 rounded-lg hover:bg-purple-100 transition-colors">
            <FileText className="w-6 h-6 text-purple-600 mb-2" />
            <span className="text-sm font-medium text-purple-900">Devis Rapide</span>
          </button>
          <button className="flex flex-col items-center p-4 bg-orange-50 rounded-lg hover:bg-orange-100 transition-colors">
            <AlertTriangle className="w-6 h-6 text-orange-600 mb-2" />
            <span className="text-sm font-medium text-orange-900">Nouvelle Réclamation</span>
          </button>
        </div>
      </div>
    </div>
  );

  const renderTabContent = () => {
    switch (activeTab) {
      case 'dashboard':
        return renderDashboard();
      case 'clients':
        return <CustomerManagement />;
      case 'produits':
        return <ProductManagement />;
      case 'commandes':
        return <OrderManagement />;
      case 'contrats':
        return <ContractManagement />;
      case 'devis':
        return <QuotesManagement />;
      case 'reclamations':
        return <ClaimsManagement />;
      case 'paiements':
        return <PaymentManagement />;
      default:
        return renderDashboard();
    }
  };

  return (
    <div className="min-h-screen bg-gray-50">
      {/* En-tête */}
      <div className="bg-white shadow-sm border-b">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between items-center py-4">
            <div>
              <h1 className="text-2xl font-bold text-gray-900">Système d'Assurance</h1>
              <p className="text-sm text-gray-600">Service Client & Gestion des Polices</p>
            </div>
            <div className="flex items-center space-x-4">
              <div className="relative">
                <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400 w-4 h-4" />
                <input
                  type="text"
                  placeholder="Rechercher client, police..."
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                  className="pl-10 pr-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                />
              </div>
              <button className="bg-blue-600 text-white px-4 py-2 rounded-lg hover:bg-blue-700 transition-colors flex items-center space-x-2">
                <Plus className="w-4 h-4" />
                <span>Nouveau</span>
              </button>
            </div>
          </div>
        </div>
      </div>

      {/* Navigation par onglets */}
      <div className="bg-white border-b">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <nav className="flex space-x-8">
            {tabs.map((tab) => {
              const Icon = tab.icon;
              return (
                <button
                  key={tab.id}
                  onClick={() => setActiveTab(tab.id)}
                  className={`flex items-center space-x-2 py-4 px-1 border-b-2 font-medium text-sm transition-colors ${
                    activeTab === tab.id
                      ? 'border-blue-500 text-blue-600'
                      : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
                  }`}
                >
                  <Icon className="w-4 h-4" />
                  <span>{tab.label}</span>
                </button>
              );
            })}
          </nav>
        </div>
      </div>

      {/* Contenu principal */}
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {renderTabContent()}
      </div>
    </div>
  );
};

export default AssurancePage;
