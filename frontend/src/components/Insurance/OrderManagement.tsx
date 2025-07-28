import React, { useState, useEffect } from 'react';
import {
  ShoppingCart,
  Plus,
  Eye,
  Edit,
  CheckCircle,
  XCircle,
  Clock,
  AlertTriangle,
  User,
  Package,
  Calendar,
  FileText,
  ArrowRight,
  RefreshCw
} from 'lucide-react';
import { insuranceApi } from '../../lib/insurance-api';
import EditOrderModal from './EditOrderModal';

interface Order {
  id: string;
  orderNumber: string;
  customerId: string;
  productId: string;
  orderStatus: string;
  coverageAmount: number;
  premiumAmount: number;
  premiumFrequency: string;
  applicationDate: string;
  effectiveDate: string;
  customerName?: string;
  productName?: string;
}

interface OrderDetails {
  order: Order;
  statusHistory: Array<{
    previousStatus: string;
    newStatus: string;
    changedAt: string;
    changedBy: string;
    reason: string;
  }>;
}

const OrderManagement: React.FC = () => {
  const [orders, setOrders] = useState<Order[]>([]);
  const [selectedOrder, setSelectedOrder] = useState<Order | null>(null);
  const [orderDetails, setOrderDetails] = useState<OrderDetails | null>(null);
  const [loading, setLoading] = useState(false);
  const [statusFilter, setStatusFilter] = useState<string>('all');
  const [showEditModal, setShowEditModal] = useState(false);

  useEffect(() => {
    loadOrders();
  }, [statusFilter]);

  // Rafraîchir automatiquement quand le composant devient visible
  useEffect(() => {
    const handleVisibilityChange = () => {
      if (!document.hidden) {
        loadOrders();
      }
    };

    const handleFocus = () => {
      loadOrders();
    };

    document.addEventListener('visibilitychange', handleVisibilityChange);
    window.addEventListener('focus', handleFocus);

    return () => {
      document.removeEventListener('visibilitychange', handleVisibilityChange);
      window.removeEventListener('focus', handleFocus);
    };
  }, []);

  // Écouter l'événement de nouvelle commande
  useEffect(() => {
    const handleNewOrder = () => {
      loadOrders();
    };

    window.addEventListener('newOrderCreated', handleNewOrder);

    return () => {
      window.removeEventListener('newOrderCreated', handleNewOrder);
    };
  }, []);

  const loadOrders = async () => {
    setLoading(true);
    try {
      const response = await insuranceApi.getAllOrders(
        statusFilter !== 'all' ? statusFilter : undefined,
        0,
        50
      );

      if (response.success && response.data) {
        // Transformer les données pour correspondre à l'interface Order
        const transformedOrders = response.data.map((order: any) => ({
          id: order.id,
          orderNumber: order.order_number,
          customerId: order.customer_id,
          productId: order.product_id,
          orderStatus: order.order_status,
          coverageAmount: order.coverage_amount,
          premiumAmount: order.premium_amount,
          premiumFrequency: order.premium_frequency,
          applicationDate: order.application_date,
          effectiveDate: order.effective_date,
          customerName: order.customer?.first_name && order.customer?.last_name
            ? `${order.customer.first_name} ${order.customer.last_name}`
            : 'Client inconnu',
          productName: order.product?.name || 'Produit inconnu'
        }));

        setOrders(transformedOrders);
      } else {
        console.error('Erreur API:', response.error);
        setOrders([]);
      }
    } catch (error) {
      console.error('Erreur lors du chargement des commandes:', error);
      setOrders([]);
    } finally {
      setLoading(false);
    }
  };

  const handleViewOrder = async (order: Order) => {
    setSelectedOrder(order);
    setLoading(true);
    
    try {
      const response = await insuranceApi.getOrderStatus(order.orderNumber);
      
      if (response.success && response.data) {
        setOrderDetails(response.data);
      } else {
        console.error('Erreur lors du chargement des détails:', response.error);
        setOrderDetails(null);
      }
    } catch (error) {
      console.error('Erreur lors du chargement des détails:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleLoadMoreDetails = async () => {
    if (!selectedOrder) return;

    setLoading(true);
    try {
      const response = await insuranceApi.getOrderStatus(selectedOrder.orderNumber);

      if (response.success && response.data) {
        setOrderDetails(response.data);

        // Message de succès discret
        const historyCount = response.data.status_history?.length || 0;
        console.log(`✅ Détails chargés pour ${selectedOrder.orderNumber} - ${historyCount} entrées d'historique`);
      } else {
        console.error('Erreur lors du chargement des détails:', response.error);
        alert('Impossible de charger les détails de la commande');
      }
    } catch (error) {
      console.error('Erreur lors du chargement des détails:', error);
      alert('Erreur lors du chargement des détails');
    } finally {
      setLoading(false);
    }
  };

  const handleEditOrder = () => {
    if (!selectedOrder) return;
    setShowEditModal(true);
  };

  const handleOrderUpdated = (updatedOrder: Order) => {
    // Mettre à jour la liste des commandes
    setOrders(prevOrders =>
      prevOrders.map(order =>
        order.id === updatedOrder.id ? updatedOrder : order
      )
    );

    // Mettre à jour la commande sélectionnée
    setSelectedOrder(updatedOrder);

    // Recharger les détails si nécessaire
    if (orderDetails) {
      handleLoadMoreDetails();
    }
  };

  const getStatusBadge = (status: string) => {
    switch (status) {
      case 'draft':
        return <span className="px-2 py-1 rounded-full text-xs font-medium bg-gray-100 text-gray-800">Brouillon</span>;
      case 'submitted':
        return <span className="px-2 py-1 rounded-full text-xs font-medium bg-blue-100 text-blue-800">Soumise</span>;
      case 'under_review':
        return <span className="px-2 py-1 rounded-full text-xs font-medium bg-yellow-100 text-yellow-800">En révision</span>;
      case 'approved':
        return <span className="px-2 py-1 rounded-full text-xs font-medium bg-green-100 text-green-800">Approuvée</span>;
      case 'rejected':
        return <span className="px-2 py-1 rounded-full text-xs font-medium bg-red-100 text-red-800">Rejetée</span>;
      case 'cancelled':
        return <span className="px-2 py-1 rounded-full text-xs font-medium bg-gray-100 text-gray-800">Annulée</span>;
      default:
        return <span className="px-2 py-1 rounded-full text-xs font-medium bg-gray-100 text-gray-800">{status}</span>;
    }
  };

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'draft':
        return <FileText className="w-4 h-4 text-gray-600" />;
      case 'submitted':
        return <Clock className="w-4 h-4 text-blue-600" />;
      case 'under_review':
        return <AlertTriangle className="w-4 h-4 text-yellow-600" />;
      case 'approved':
        return <CheckCircle className="w-4 h-4 text-green-600" />;
      case 'rejected':
        return <XCircle className="w-4 h-4 text-red-600" />;
      case 'cancelled':
        return <XCircle className="w-4 h-4 text-gray-600" />;
      default:
        return <FileText className="w-4 h-4 text-gray-600" />;
    }
  };

  const getStatusLabel = (status: string) => {
    switch (status) {
      case 'draft': return 'Brouillon';
      case 'submitted': return 'Soumise';
      case 'under_review': return 'En révision';
      case 'approved': return 'Approuvée';
      case 'rejected': return 'Rejetée';
      case 'cancelled': return 'Annulée';
      default: return status;
    }
  };

  const statusOptions = [
    { value: 'all', label: 'Toutes les commandes' },
    { value: 'draft', label: 'Brouillons' },
    { value: 'submitted', label: 'Soumises' },
    { value: 'under_review', label: 'En révision' },
    { value: 'approved', label: 'Approuvées' },
    { value: 'rejected', label: 'Rejetées' },
    { value: 'cancelled', label: 'Annulées' }
  ];

  const filteredOrders = statusFilter === 'all' 
    ? orders 
    : orders.filter(order => order.orderStatus === statusFilter);

  return (
    <div className="space-y-6">
      {/* En-tête et filtres */}
      <div className="bg-white rounded-lg shadow-md p-6">
        <div className="flex justify-between items-center mb-4">
          <h2 className="text-xl font-semibold text-gray-900">Gestion des Commandes</h2>
          <div className="flex space-x-2">
            <button
              onClick={loadOrders}
              disabled={loading}
              className="bg-gray-600 text-white px-4 py-2 rounded-lg hover:bg-gray-700 transition-colors flex items-center space-x-2 disabled:opacity-50"
            >
              <RefreshCw className={`w-4 h-4 ${loading ? 'animate-spin' : ''}`} />
              <span>Rafraîchir</span>
            </button>
            <button className="bg-blue-600 text-white px-4 py-2 rounded-lg hover:bg-blue-700 transition-colors flex items-center space-x-2">
              <Plus className="w-4 h-4" />
              <span>Nouvelle Commande</span>
            </button>
          </div>
        </div>
        
        <div className="flex space-x-4">
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
        {/* Liste des commandes */}
        <div className="bg-white rounded-lg shadow-md">
          <div className="p-6 border-b border-gray-200">
            <h3 className="text-lg font-semibold text-gray-900">
              Commandes ({filteredOrders.length})
            </h3>
          </div>
          <div className="max-h-96 overflow-y-auto">
            {loading ? (
              <div className="p-6 text-center text-gray-500">
                Chargement des commandes...
              </div>
            ) : filteredOrders.length === 0 ? (
              <div className="p-6 text-center text-gray-500">
                Aucune commande trouvée
              </div>
            ) : (
              filteredOrders.map((order) => (
                <div
                  key={order.id}
                  className="p-4 border-b border-gray-100 hover:bg-gray-50 cursor-pointer"
                  onClick={() => handleViewOrder(order)}
                >
                  <div className="flex items-center justify-between">
                    <div className="flex items-center space-x-3">
                      <div className="w-10 h-10 bg-blue-100 rounded-full flex items-center justify-center">
                        <ShoppingCart className="w-5 h-5 text-blue-600" />
                      </div>
                      <div>
                        <p className="font-medium text-gray-900">{order.orderNumber}</p>
                        <p className="text-sm text-gray-500">
                          {new Date(order.applicationDate).toLocaleDateString('fr-FR')}
                        </p>
                      </div>
                    </div>
                    <div className="flex items-center space-x-2">
                      {getStatusBadge(order.orderStatus)}
                    </div>
                  </div>
                  <div className="mt-2 grid grid-cols-2 gap-2 text-sm text-gray-600">
                    <div className="flex items-center space-x-1">
                      <User className="w-4 h-4" />
                      <span>{order.customerName}</span>
                    </div>
                    <div className="flex items-center space-x-1">
                      <Package className="w-4 h-4" />
                      <span>{order.productName}</span>
                    </div>
                    <div className="flex items-center space-x-1">
                      <Calendar className="w-4 h-4" />
                      <span>Effet: {new Date(order.effectiveDate).toLocaleDateString('fr-FR')}</span>
                    </div>
                    <div className="flex items-center space-x-1">
                      <ShoppingCart className="w-4 h-4" />
                      <span>{order.premiumAmount.toLocaleString()} €/{order.premiumFrequency === 'monthly' ? 'mois' : 'an'}</span>
                    </div>
                  </div>
                </div>
              ))
            )}
          </div>
        </div>

        {/* Détails de la commande sélectionnée */}
        <div className="bg-white rounded-lg shadow-md">
          <div className="p-6 border-b border-gray-200">
            <h3 className="text-lg font-semibold text-gray-900">
              {selectedOrder ? 'Détails de la Commande' : 'Sélectionnez une commande'}
            </h3>
          </div>
          <div className="p-6">
            {selectedOrder ? (
              <div className="space-y-6">
                {/* Informations générales */}
                <div>
                  <h4 className="font-medium text-gray-900 mb-3">Informations Générales</h4>
                  <div className="grid grid-cols-2 gap-4 text-sm">
                    <div>
                      <span className="text-gray-500">Numéro de commande:</span>
                      <p className="font-medium">{selectedOrder.orderNumber}</p>
                    </div>
                    <div>
                      <span className="text-gray-500">Statut:</span>
                      <div className="flex items-center space-x-1">
                        {getStatusIcon(selectedOrder.orderStatus)}
                        <span className="font-medium">{getStatusLabel(selectedOrder.orderStatus)}</span>
                      </div>
                    </div>
                    <div>
                      <span className="text-gray-500">Client:</span>
                      <p className="font-medium">{selectedOrder.customerName}</p>
                    </div>
                    <div>
                      <span className="text-gray-500">Produit:</span>
                      <p className="font-medium">{selectedOrder.productName}</p>
                    </div>
                    <div>
                      <span className="text-gray-500">Date de demande:</span>
                      <p className="font-medium">{new Date(selectedOrder.applicationDate).toLocaleDateString('fr-FR')}</p>
                    </div>
                    <div>
                      <span className="text-gray-500">Date d'effet:</span>
                      <p className="font-medium">{new Date(selectedOrder.effectiveDate).toLocaleDateString('fr-FR')}</p>
                    </div>
                    <div>
                      <span className="text-gray-500">Montant de couverture:</span>
                      <p className="font-medium">{selectedOrder.coverageAmount.toLocaleString()} €</p>
                    </div>
                    <div>
                      <span className="text-gray-500">Prime:</span>
                      <p className="font-medium">
                        {selectedOrder.premiumAmount.toLocaleString()} €/{selectedOrder.premiumFrequency === 'monthly' ? 'mois' : 'an'}
                      </p>
                    </div>
                  </div>
                </div>

                {/* Historique des statuts - seulement si orderDetails est disponible */}
                {orderDetails && orderDetails.statusHistory && (
                  <div>
                    <h4 className="font-medium text-gray-900 mb-3">Historique des Statuts</h4>
                    <div className="space-y-4">
                      {orderDetails.statusHistory.map((status, index) => (
                      <div key={index} className="relative pl-6 pb-4">
                        {index < orderDetails.statusHistory.length - 1 && (
                          <div className="absolute top-0 left-2 h-full w-0.5 bg-gray-200"></div>
                        )}
                        <div className="absolute top-0 left-0 w-4 h-4 rounded-full bg-blue-500"></div>
                        <div className="ml-2">
                          <div className="flex items-center space-x-2">
                            <span className="font-medium">
                              {status.previousStatus ? (
                                <>
                                  {getStatusLabel(status.previousStatus)}
                                  <ArrowRight className="inline w-3 h-3 mx-1" />
                                  {getStatusLabel(status.newStatus)}
                                </>
                              ) : (
                                <>Création - {getStatusLabel(status.newStatus)}</>
                              )}
                            </span>
                          </div>
                          <p className="text-sm text-gray-500">
                            {new Date(status.changedAt).toLocaleString('fr-FR')}
                            {status.changedBy && ` par ${status.changedBy}`}
                          </p>
                          {status.reason && (
                            <p className="text-sm text-gray-600 mt-1">{status.reason}</p>
                          )}
                        </div>
                      </div>
                    ))}

                    {/* Message si l'historique est vide */}
                    {orderDetails.statusHistory.length === 0 && (
                      <div className="text-center py-4">
                        <p className="text-gray-500 text-sm">
                          📋 Aucun changement de statut enregistré pour cette commande.
                        </p>
                        <p className="text-gray-400 text-xs mt-1">
                          L'historique apparaîtra ici lors des mises à jour de statut.
                        </p>
                      </div>
                    )}
                    </div>
                  </div>
                )}

                {/* Message si pas de détails supplémentaires */}
                {!orderDetails && (
                  <div className="bg-blue-50 p-4 rounded-lg">
                    <p className="text-blue-800 text-sm">
                      💡 Cliquez sur "Voir Plus" pour charger l'historique détaillé de cette commande.
                    </p>
                  </div>
                )}

                {/* Actions */}
                <div className="flex space-x-3">
                  <button
                    onClick={handleLoadMoreDetails}
                    disabled={loading}
                    className="flex-1 bg-blue-600 text-white py-2 px-4 rounded-lg hover:bg-blue-700 transition-colors flex items-center justify-center space-x-2 disabled:opacity-50"
                  >
                    <Eye className="w-4 h-4" />
                    <span>
                      {loading ? 'Chargement...' : orderDetails ? 'Actualiser' : 'Voir Plus'}
                    </span>
                  </button>
                  <button
                    onClick={handleEditOrder}
                    className="flex-1 bg-gray-600 text-white py-2 px-4 rounded-lg hover:bg-gray-700 transition-colors flex items-center justify-center space-x-2"
                  >
                    <Edit className="w-4 h-4" />
                    <span>Modifier</span>
                  </button>
                </div>
              </div>
            ) : (
              <div className="text-center text-gray-500 py-8">
                <ShoppingCart className="w-12 h-12 mx-auto mb-4 text-gray-300" />
                <p>Cliquez sur une commande pour voir ses détails</p>
              </div>
            )}
          </div>
        </div>
      </div>

      {/* Modal d'édition de commande */}
      <EditOrderModal
        isOpen={showEditModal}
        onClose={() => setShowEditModal(false)}
        order={selectedOrder}
        onOrderUpdated={handleOrderUpdated}
      />
    </div>
  );
};

export default OrderManagement;
