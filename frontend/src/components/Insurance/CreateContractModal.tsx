import React, { useState, useEffect } from 'react';
import { X, Plus, Search, CheckCircle, User, Package, CreditCard } from 'lucide-react';
import { insuranceApi } from '../../lib/insurance-api';

interface Order {
  id: string;
  orderNumber: string;
  orderStatus: string;
  customerName: string;
  productName: string;
  coverageAmount: number;
  premiumAmount: number;
  premiumFrequency: string;
  applicationDate: string;
}

interface CreateContractModalProps {
  isOpen: boolean;
  onClose: () => void;
  onContractCreated?: (contract: any) => void;
}

export default function CreateContractModal({ isOpen, onClose, onContractCreated }: CreateContractModalProps) {
  const [loading, setLoading] = useState(false);
  const [creating, setCreating] = useState(false);
  const [approvedOrders, setApprovedOrders] = useState<Order[]>([]);
  const [selectedOrder, setSelectedOrder] = useState<Order | null>(null);
  const [searchTerm, setSearchTerm] = useState('');

  useEffect(() => {
    if (isOpen) {
      loadApprovedOrders();
    }
  }, [isOpen]);

  const loadApprovedOrders = async () => {
    setLoading(true);
    try {
      const response = await insuranceApi.getAllOrders('approved');

      if (response.success && response.data) {
        // Transformer les données de snake_case vers camelCase
        const transformedOrders = response.data.map((order: any) => ({
          id: order.id,
          orderNumber: order.order_number,
          orderStatus: order.order_status,
          customerName: order.customer ? `${order.customer.first_name} ${order.customer.last_name}` : order.customer_name || 'N/A',
          productName: order.product ? order.product.name : order.product_name || 'N/A',
          coverageAmount: order.coverage_amount || 0,
          premiumAmount: order.premium_amount || 0,
          premiumFrequency: order.premium_frequency,
          applicationDate: order.application_date
        }));

        setApprovedOrders(transformedOrders);
      } else {
        console.error('Erreur lors du chargement des commandes:', response.error);
      }
    } catch (error) {
      console.error('Erreur lors du chargement des commandes:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleCreateContract = async () => {
    if (!selectedOrder) return;
    
    setCreating(true);
    try {
      const response = await insuranceApi.createContractFromOrder(selectedOrder.id);
      
      if (response.success && response.data) {
        // Notifier le parent
        if (onContractCreated) {
          onContractCreated(response.data);
        }
        
        // Fermer la modal
        onClose();
        
        // Message de succès
        alert(`Contrat ${response.data.policy_number} créé avec succès !`);
        
        // Déclencher un événement pour rafraîchir la liste des contrats
        window.dispatchEvent(new CustomEvent('newContractCreated'));
      } else {
        throw new Error(response.error || 'Erreur lors de la création du contrat');
      }
    } catch (error) {
      console.error('Erreur lors de la création du contrat:', error);
      const errorMessage = error instanceof Error ? error.message : 'Erreur lors de la création du contrat';
      alert(`Erreur: ${errorMessage}`);
    } finally {
      setCreating(false);
    }
  };

  // Filtrer les commandes par terme de recherche
  const filteredOrders = approvedOrders.filter(order => {
    if (!searchTerm) return true;
    
    const searchLower = searchTerm.toLowerCase();
    return (
      order.orderNumber.toLowerCase().includes(searchLower) ||
      order.customerName.toLowerCase().includes(searchLower) ||
      order.productName.toLowerCase().includes(searchLower)
    );
  });

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
      <div className="bg-white rounded-lg shadow-xl max-w-4xl w-full max-h-[90vh] overflow-y-auto">
        {/* Header */}
        <div className="flex items-center justify-between p-6 border-b border-gray-200">
          <div className="flex items-center space-x-3">
            <div className="w-10 h-10 bg-green-100 rounded-full flex items-center justify-center">
              <Plus className="w-5 h-5 text-green-600" />
            </div>
            <div>
              <h2 className="text-xl font-semibold text-gray-900">Créer un Nouveau Contrat</h2>
              <p className="text-sm text-gray-500">Sélectionnez une commande approuvée</p>
            </div>
          </div>
          <button
            onClick={onClose}
            className="text-gray-400 hover:text-gray-600 transition-colors"
          >
            <X className="w-6 h-6" />
          </button>
        </div>

        {/* Content */}
        <div className="p-6">
          {/* Recherche */}
          <div className="mb-6">
            <div className="relative">
              <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400 w-4 h-4" />
              <input
                type="text"
                placeholder="Rechercher par numéro de commande, client ou produit..."
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                className="w-full pl-10 pr-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
              />
            </div>
          </div>

          {/* Liste des commandes approuvées */}
          <div className="space-y-4">
            <h3 className="font-medium text-gray-900">
              Commandes Approuvées ({filteredOrders.length})
            </h3>
            
            {loading ? (
              <div className="text-center py-8">
                <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600 mx-auto"></div>
                <p className="text-gray-500 mt-2">Chargement des commandes...</p>
              </div>
            ) : filteredOrders.length === 0 ? (
              <div className="text-center py-8">
                <CheckCircle className="w-12 h-12 mx-auto mb-4 text-gray-300" />
                <p className="text-gray-500">
                  {searchTerm ? 'Aucune commande trouvée' : 'Aucune commande approuvée disponible'}
                </p>
                <p className="text-gray-400 text-sm mt-1">
                  Les contrats ne peuvent être créés qu'à partir de commandes approuvées
                </p>
              </div>
            ) : (
              <div className="max-h-96 overflow-y-auto space-y-2">
                {filteredOrders.map((order) => (
                  <div
                    key={order.id}
                    className={`p-4 border rounded-lg cursor-pointer transition-colors ${
                      selectedOrder?.id === order.id
                        ? 'border-blue-500 bg-blue-50'
                        : 'border-gray-200 hover:border-gray-300 hover:bg-gray-50'
                    }`}
                    onClick={() => setSelectedOrder(order)}
                  >
                    <div className="flex items-center justify-between">
                      <div className="flex items-center space-x-3">
                        <div className="w-10 h-10 bg-green-100 rounded-full flex items-center justify-center">
                          <CheckCircle className="w-5 h-5 text-green-600" />
                        </div>
                        <div>
                          <div className="font-medium text-gray-900">{order.orderNumber}</div>
                          <div className="text-sm text-gray-500">{order.customerName}</div>
                        </div>
                      </div>
                      <div className="text-right">
                        <div className="font-medium text-gray-900">
                          {(order.coverageAmount || 0).toLocaleString()} XOF
                        </div>
                        <div className="text-sm text-gray-500">
                          Prime: {(order.premiumAmount || 0).toLocaleString()} XOF
                        </div>
                      </div>
                    </div>
                    <div className="mt-2 flex items-center justify-between text-sm text-gray-500">
                      <div className="flex items-center">
                        <Package className="w-4 h-4 mr-1" />
                        {order.productName}
                      </div>
                      <div className="flex items-center">
                        <CreditCard className="w-4 h-4 mr-1" />
                        {order.premiumFrequency === 'monthly' ? 'Mensuel' : 
                         order.premiumFrequency === 'quarterly' ? 'Trimestriel' :
                         order.premiumFrequency === 'semi-annual' ? 'Semestriel' : 'Annuel'}
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>

          {/* Détails de la commande sélectionnée */}
          {selectedOrder && (
            <div className="mt-6 p-4 bg-blue-50 border border-blue-200 rounded-lg">
              <h4 className="font-medium text-blue-900 mb-3">Détails de la Commande Sélectionnée</h4>
              <div className="grid grid-cols-2 gap-4 text-sm">
                <div>
                  <span className="text-blue-700">Numéro de commande:</span>
                  <p className="font-medium text-blue-900">{selectedOrder.orderNumber}</p>
                </div>
                <div>
                  <span className="text-blue-700">Client:</span>
                  <p className="font-medium text-blue-900">{selectedOrder.customerName}</p>
                </div>
                <div>
                  <span className="text-blue-700">Produit:</span>
                  <p className="font-medium text-blue-900">{selectedOrder.productName}</p>
                </div>
                <div>
                  <span className="text-blue-700">Date de demande:</span>
                  <p className="font-medium text-blue-900">
                    {new Date(selectedOrder.applicationDate).toLocaleDateString('fr-FR')}
                  </p>
                </div>
                <div>
                  <span className="text-blue-700">Couverture:</span>
                  <p className="font-medium text-blue-900">{(selectedOrder.coverageAmount || 0).toLocaleString()} XOF</p>
                </div>
                <div>
                  <span className="text-blue-700">Prime:</span>
                  <p className="font-medium text-blue-900">
                    {(selectedOrder.premiumAmount || 0).toLocaleString()} XOF/
                    {selectedOrder.premiumFrequency === 'monthly' ? 'mois' :
                     selectedOrder.premiumFrequency === 'quarterly' ? 'trimestre' :
                     selectedOrder.premiumFrequency === 'semi-annual' ? 'semestre' : 'an'}
                  </p>
                </div>
              </div>
            </div>
          )}
        </div>

        {/* Footer */}
        <div className="flex justify-end space-x-3 p-6 border-t border-gray-200">
          <button
            onClick={onClose}
            className="px-4 py-2 text-gray-700 bg-gray-100 rounded-lg hover:bg-gray-200 transition-colors"
          >
            Annuler
          </button>
          <button
            onClick={handleCreateContract}
            disabled={!selectedOrder || creating}
            className="px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 transition-colors disabled:opacity-50 disabled:cursor-not-allowed flex items-center space-x-2"
          >
            <Plus className="w-4 h-4" />
            <span>{creating ? 'Création...' : 'Créer le Contrat'}</span>
          </button>
        </div>
      </div>
    </div>
  );
}
