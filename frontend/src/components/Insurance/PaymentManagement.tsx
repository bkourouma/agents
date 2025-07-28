import React, { useState, useEffect } from 'react';
import { 
  CreditCard, 
  Plus, 
  Eye, 
  CheckCircle, 
  XCircle, 
  Clock,
  AlertTriangle,
  Calendar,
  Euro,
  Search,
  Filter,
  TrendingUp,
  DollarSign,
  Users,
  FileText
} from 'lucide-react';
import { insuranceApi } from '../../lib/insurance-api';
import ProcessPaymentModal from './ProcessPaymentModal';

interface Payment {
  id: string;
  contract_id: string;
  policy_number: string;
  customer_name: string;
  customer_id: string;
  product_name: string;
  payment_date?: string;
  due_date: string;
  amount: number;
  payment_method?: string;
  payment_status: string;
  transaction_id?: string;
  late_fee: number;
  grace_period_used: boolean;
  processed_by?: string;
  created_at: string;
  days_overdue: number;
}

interface PaymentStatistics {
  total_payments: number;
  status_counts: Record<string, number>;
  total_collected: number;
  total_late_fees: number;
  overdue_payments: number;
  recent_payments: number;
  collection_rate: number;
}

const PaymentManagement: React.FC = () => {
  const [payments, setPayments] = useState<Payment[]>([]);
  const [selectedPayment, setSelectedPayment] = useState<Payment | null>(null);
  const [statistics, setStatistics] = useState<PaymentStatistics | null>(null);
  const [loading, setLoading] = useState(false);
  const [statusFilter, setStatusFilter] = useState<string>('all');
  const [searchQuery, setSearchQuery] = useState('');
  const [showProcessModal, setShowProcessModal] = useState(false);

  useEffect(() => {
    loadPayments();
    loadStatistics();
  }, [statusFilter]);

  const loadPayments = async () => {
    setLoading(true);
    try {
      const filters = statusFilter !== 'all' ? { statut: statusFilter } : {};
      const response = await insuranceApi.getPayments(filters);
      
      if (response.success && response.data) {
        setPayments(response.data);
      } else {
        console.error('Erreur lors du chargement des paiements:', response.error);
        setPayments([]);
      }
    } catch (error) {
      console.error('Erreur lors du chargement des paiements:', error);
      setPayments([]);
    } finally {
      setLoading(false);
    }
  };

  const loadStatistics = async () => {
    try {
      const response = await insuranceApi.getPaymentStatistics();
      
      if (response.success && response.data) {
        setStatistics(response.data);
      }
    } catch (error) {
      console.error('Erreur lors du chargement des statistiques:', error);
    }
  };

  const handleProcessPayment = async (paymentData: {
    payment_date: string;
    payment_method: string;
    transaction_id?: string;
  }) => {
    if (!selectedPayment) return;
    
    try {
      const response = await insuranceApi.processPayment(selectedPayment.id, {
        ...paymentData,
        processed_by: 'current_user' // À remplacer par l'utilisateur connecté
      });
      
      if (response.success) {
        await loadPayments();
        await loadStatistics();
        setShowProcessModal(false);
        setSelectedPayment(null);
        alert('Paiement traité avec succès!');
      } else {
        console.error('Erreur lors du traitement:', response.error);
        alert('Erreur lors du traitement du paiement');
      }
    } catch (error) {
      console.error('Erreur lors du traitement:', error);
      alert('Erreur lors du traitement du paiement');
    }
  };

  const getStatusBadge = (status: string) => {
    switch (status) {
      case 'pending':
        return <span className="px-2 py-1 rounded-full text-xs font-medium bg-yellow-100 text-yellow-800">En attente</span>;
      case 'completed':
        return <span className="px-2 py-1 rounded-full text-xs font-medium bg-green-100 text-green-800">Payé</span>;
      case 'failed':
        return <span className="px-2 py-1 rounded-full text-xs font-medium bg-red-100 text-red-800">Échec</span>;
      case 'refunded':
        return <span className="px-2 py-1 rounded-full text-xs font-medium bg-purple-100 text-purple-800">Remboursé</span>;
      default:
        return <span className="px-2 py-1 rounded-full text-xs font-medium bg-gray-100 text-gray-800">{status}</span>;
    }
  };

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'pending':
        return <Clock className="w-4 h-4 text-yellow-600" />;
      case 'completed':
        return <CheckCircle className="w-4 h-4 text-green-600" />;
      case 'failed':
        return <XCircle className="w-4 h-4 text-red-600" />;
      case 'refunded':
        return <CreditCard className="w-4 h-4 text-purple-600" />;
      default:
        return <Clock className="w-4 h-4 text-gray-600" />;
    }
  };

  const getPaymentMethodLabel = (method?: string) => {
    switch (method) {
      case 'bank_transfer': return 'Virement bancaire';
      case 'credit_card': return 'Carte de crédit';
      case 'mobile_money': return 'Mobile Money';
      case 'cash': return 'Espèces';
      case 'check': return 'Chèque';
      default: return method || 'Non spécifié';
    }
  };

  const statusOptions = [
    { value: 'all', label: 'Tous les paiements' },
    { value: 'pending', label: 'En attente' },
    { value: 'completed', label: 'Payés' },
    { value: 'failed', label: 'Échecs' },
    { value: 'refunded', label: 'Remboursés' }
  ];

  const filteredPayments = payments.filter(payment =>
    payment.policy_number.toLowerCase().includes(searchQuery.toLowerCase()) ||
    payment.customer_name.toLowerCase().includes(searchQuery.toLowerCase()) ||
    payment.product_name.toLowerCase().includes(searchQuery.toLowerCase())
  );

  // Statistiques cards
  const StatCard: React.FC<{
    title: string;
    value: string;
    icon: React.ReactNode;
    color: string;
    trend?: string;
  }> = ({ title, value, icon, color, trend }) => (
    <div className="bg-white rounded-lg shadow-md p-6">
      <div className="flex items-center justify-between">
        <div>
          <p className="text-sm font-medium text-gray-600">{title}</p>
          <p className="text-2xl font-bold text-gray-900">{value}</p>
          {trend && <p className="text-sm text-green-600">{trend}</p>}
        </div>
        <div className={`w-12 h-12 rounded-lg flex items-center justify-center`} style={{ backgroundColor: `${color}20` }}>
          {icon}
        </div>
      </div>
    </div>
  );

  return (
    <div className="space-y-6">
      {/* Statistiques */}
      {statistics && (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
          <StatCard
            title="Total Collecté"
            value={`${statistics.total_collected.toLocaleString()} XOF`}
            icon={<DollarSign className="w-6 h-6 text-green-600" />}
            color="#10B981"
          />
          <StatCard
            title="Paiements en Retard"
            value={statistics.overdue_payments.toString()}
            icon={<AlertTriangle className="w-6 h-6 text-red-600" />}
            color="#EF4444"
          />
          <StatCard
            title="Taux de Collecte"
            value={`${statistics.collection_rate.toFixed(1)}%`}
            icon={<TrendingUp className="w-6 h-6 text-blue-600" />}
            color="#3B82F6"
          />
          <StatCard
            title="Frais de Retard"
            value={`${statistics.total_late_fees.toLocaleString()} XOF`}
            icon={<Clock className="w-6 h-6 text-orange-600" />}
            color="#F59E0B"
          />
        </div>
      )}

      {/* En-tête et filtres */}
      <div className="bg-white rounded-lg shadow-md p-6">
        <div className="flex justify-between items-center mb-4">
          <h2 className="text-xl font-semibold text-gray-900">Gestion des Paiements</h2>
          <button
            onClick={() => {/* TODO: Implémenter création de paiement */}}
            className="bg-blue-600 text-white px-4 py-2 rounded-lg hover:bg-blue-700 transition-colors flex items-center space-x-2"
          >
            <Plus className="w-4 h-4" />
            <span>Nouveau Paiement</span>
          </button>
        </div>
        
        <div className="flex space-x-4">
          <div className="flex-1 relative">
            <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400 w-4 h-4" />
            <input
              type="text"
              placeholder="Rechercher par police, client ou produit..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="w-full pl-10 pr-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
            />
          </div>
          <select
            value={statusFilter}
            onChange={(e) => setStatusFilter(e.target.value)}
            className="px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
          >
            {statusOptions.map((option) => (
              <option key={option.value} value={option.value}>
                {option.label}
              </option>
            ))}
          </select>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Liste des paiements */}
        <div className="bg-white rounded-lg shadow-md">
          <div className="p-6 border-b border-gray-200">
            <h3 className="text-lg font-semibold text-gray-900">
              Paiements ({filteredPayments.length})
            </h3>
          </div>
          <div className="max-h-96 overflow-y-auto">
            {loading ? (
              <div className="p-6 text-center text-gray-500">
                Chargement des paiements...
              </div>
            ) : filteredPayments.length === 0 ? (
              <div className="p-6 text-center text-gray-500">
                Aucun paiement trouvé
              </div>
            ) : (
              filteredPayments.map((payment) => (
                <div
                  key={payment.id}
                  className={`p-4 border-b border-gray-100 hover:bg-gray-50 cursor-pointer ${
                    selectedPayment?.id === payment.id ? 'bg-blue-50' : ''
                  }`}
                  onClick={() => setSelectedPayment(payment)}
                >
                  <div className="flex items-center justify-between">
                    <div className="flex items-center space-x-3">
                      <div className={`w-10 h-10 rounded-full flex items-center justify-center ${
                        payment.days_overdue > 0 ? 'bg-red-100' : 'bg-blue-100'
                      }`}>
                        <CreditCard className={`w-5 h-5 ${
                          payment.days_overdue > 0 ? 'text-red-600' : 'text-blue-600'
                        }`} />
                      </div>
                      <div>
                        <p className="font-medium text-gray-900">{payment.policy_number}</p>
                        <p className="text-sm text-gray-500">{payment.customer_name}</p>
                      </div>
                    </div>
                    <div className="flex items-center space-x-2">
                      {getStatusBadge(payment.payment_status)}
                      {payment.days_overdue > 0 && (
                        <span className="px-2 py-1 rounded-full text-xs font-medium bg-red-100 text-red-800">
                          {payment.days_overdue}j retard
                        </span>
                      )}
                    </div>
                  </div>
                  <div className="mt-2 grid grid-cols-2 gap-2 text-sm text-gray-600">
                    <div className="flex items-center space-x-1">
                      <Calendar className="w-4 h-4" />
                      <span>Échéance: {new Date(payment.due_date).toLocaleDateString('fr-FR')}</span>
                    </div>
                    <div className="flex items-center space-x-1">
                      <Euro className="w-4 h-4" />
                      <span>{payment.amount.toLocaleString()} XOF</span>
                    </div>
                  </div>
                  {payment.late_fee > 0 && (
                    <div className="mt-1 text-xs text-red-600">
                      Frais de retard: {payment.late_fee.toLocaleString()} XOF
                    </div>
                  )}
                </div>
              ))
            )}
          </div>
        </div>

        {/* Détails du paiement sélectionné */}
        <div className="bg-white rounded-lg shadow-md">
          <div className="p-6 border-b border-gray-200">
            <h3 className="text-lg font-semibold text-gray-900">
              {selectedPayment ? 'Détails du Paiement' : 'Sélectionnez un paiement'}
            </h3>
          </div>
          <div className="p-6">
            {selectedPayment ? (
              <div className="space-y-6">
                {/* Informations générales */}
                <div>
                  <h4 className="font-medium text-gray-900 mb-3">Informations Générales</h4>
                  <div className="grid grid-cols-2 gap-4 text-sm">
                    <div>
                      <span className="text-gray-500">Police:</span>
                      <p className="font-medium">{selectedPayment.policy_number}</p>
                    </div>
                    <div>
                      <span className="text-gray-500">Statut:</span>
                      <div className="flex items-center space-x-1">
                        {getStatusIcon(selectedPayment.payment_status)}
                        <span className="font-medium">{getStatusBadge(selectedPayment.payment_status)}</span>
                      </div>
                    </div>
                    <div>
                      <span className="text-gray-500">Montant:</span>
                      <p className="font-medium">{selectedPayment.amount.toLocaleString()} XOF</p>
                    </div>
                    <div>
                      <span className="text-gray-500">Date d'échéance:</span>
                      <p className="font-medium">{new Date(selectedPayment.due_date).toLocaleDateString('fr-FR')}</p>
                    </div>
                    {selectedPayment.payment_date && (
                      <div>
                        <span className="text-gray-500">Date de paiement:</span>
                        <p className="font-medium">{new Date(selectedPayment.payment_date).toLocaleDateString('fr-FR')}</p>
                      </div>
                    )}
                    {selectedPayment.payment_method && (
                      <div>
                        <span className="text-gray-500">Méthode:</span>
                        <p className="font-medium">{getPaymentMethodLabel(selectedPayment.payment_method)}</p>
                      </div>
                    )}
                  </div>
                </div>

                {/* Client et produit */}
                <div>
                  <h4 className="font-medium text-gray-900 mb-3">Client et Produit</h4>
                  <div className="grid grid-cols-2 gap-4 text-sm">
                    <div>
                      <span className="text-gray-500">Client:</span>
                      <p className="font-medium">{selectedPayment.customer_name}</p>
                    </div>
                    <div>
                      <span className="text-gray-500">Produit:</span>
                      <p className="font-medium">{selectedPayment.product_name}</p>
                    </div>
                  </div>
                </div>

                {/* Frais et pénalités */}
                {(selectedPayment.late_fee > 0 || selectedPayment.days_overdue > 0) && (
                  <div>
                    <h4 className="font-medium text-gray-900 mb-3">Frais et Pénalités</h4>
                    <div className="grid grid-cols-2 gap-4 text-sm">
                      {selectedPayment.late_fee > 0 && (
                        <div>
                          <span className="text-gray-500">Frais de retard:</span>
                          <p className="font-medium text-red-600">{selectedPayment.late_fee.toLocaleString()} XOF</p>
                        </div>
                      )}
                      {selectedPayment.days_overdue > 0 && (
                        <div>
                          <span className="text-gray-500">Jours de retard:</span>
                          <p className="font-medium text-red-600">{selectedPayment.days_overdue} jours</p>
                        </div>
                      )}
                    </div>
                  </div>
                )}

                {/* Actions */}
                <div className="flex space-x-3">
                  {selectedPayment.payment_status === 'pending' && (
                    <button
                      onClick={() => setShowProcessModal(true)}
                      className="flex-1 bg-green-600 text-white py-2 px-4 rounded-lg hover:bg-green-700 transition-colors"
                    >
                      Traiter le Paiement
                    </button>
                  )}
                  {selectedPayment.payment_status === 'completed' && selectedPayment.transaction_id && (
                    <div className="flex-1 text-center text-sm text-gray-500">
                      Transaction: {selectedPayment.transaction_id}
                    </div>
                  )}
                </div>
              </div>
            ) : (
              <div className="text-center text-gray-500 py-8">
                <CreditCard className="w-12 h-12 mx-auto mb-4 text-gray-300" />
                <p>Cliquez sur un paiement pour voir ses détails</p>
              </div>
            )}
          </div>
        </div>
      </div>

      {/* Modal de traitement de paiement */}
      <ProcessPaymentModal
        isOpen={showProcessModal}
        onClose={() => setShowProcessModal(false)}
        payment={selectedPayment}
        onProcess={handleProcessPayment}
      />
    </div>
  );
};

export default PaymentManagement;
