import React, { useState, useEffect } from 'react';
import { 
  X, 
  User, 
  Package, 
  DollarSign, 
  Calendar, 
  Shield, 
  CheckCircle,
  AlertTriangle,
  CreditCard,
  Mail,
  ShoppingCart
} from 'lucide-react';
import { insuranceApi } from '../../lib/insurance-api';
// Interface compatible avec QuotesManagement
interface Quote {
  id?: string;
  quote_number: string;
  customer: {
    id: string;
    name: string;
    email: string;
    phone: string;
    age?: number;
    risk_profile: string;
  };
  product: {
    id: string;
    name: string;
    product_type: string;
    description: string;
  };
  coverage_amount: number;
  premium_frequency: string;
  base_premium: number;
  adjusted_premium: number;
  additional_premium: number;
  final_premium: number;
  annual_premium: number;
  pricing_factors: Array<{
    factor_name: string;
    factor_type: string;
    factor_value: string;
    multiplier: number;
  }>;
  selected_features: Array<{
    id: string;
    name: string;
    description: string;
    additional_premium: number;
  }>;
  quote_date: string;
  expiry_date: string;
  eligible: boolean;
  conditions: string[];
  medical_exam_required: boolean;
  quote_status: string;
}

interface QuoteToOrderModalProps {
  isOpen: boolean;
  onClose: () => void;
  quote: Quote | null;
  onOrderCreated?: (orderNumber: string) => void;
}

const QuoteToOrderModal: React.FC<QuoteToOrderModalProps> = ({
  isOpen,
  onClose,
  quote,
  onOrderCreated
}) => {
  const [isCreatingOrder, setIsCreatingOrder] = useState(false);
  const [paymentMethod, setPaymentMethod] = useState('bank_transfer');
  const [sendEmail, setSendEmail] = useState(true);
  const [notes, setNotes] = useState('');

  // Reset form when modal opens/closes
  useEffect(() => {
    if (isOpen) {
      setPaymentMethod('bank_transfer');
      setSendEmail(true);
      setNotes('');
    }
  }, [isOpen]);

  if (!isOpen || !quote) return null;

  const handleCreateOrder = async () => {
    if (!quote.id) return;

    try {
      setIsCreatingOrder(true);
      
      const response = await insuranceApi.createOrderFromQuote(
        quote.id,
        paymentMethod,
        sendEmail
      );

      if (response.success) {
        const orderNumber = response.data?.order?.order_number || 'N/A';
        
        // Notification de succès
        alert(`✅ Commande ${orderNumber} créée avec succès !${sendEmail ? ' Email envoyé au client.' : ''}`);
        
        // Callback pour notifier le parent
        if (onOrderCreated) {
          onOrderCreated(orderNumber);
        }
        
        // Émettre des événements pour rafraîchir les listes
        window.dispatchEvent(new CustomEvent('newOrderCreated', { 
          detail: { orderNumber } 
        }));
        
        // Fermer la modal
        onClose();
        
        // Proposer de voir la commande
        if (confirm('Voulez-vous voir la commande dans l\'onglet Commandes ?')) {
          window.dispatchEvent(new CustomEvent('switchToOrdersTab', { 
            detail: { orderNumber } 
          }));
        }
        
      } else {
        alert('❌ Erreur lors de la création de la commande');
      }
    } catch (error) {
      console.error('Erreur lors de la création de la commande:', error);
      alert('❌ Erreur lors de la création de la commande');
    } finally {
      setIsCreatingOrder(false);
    }
  };

  const formatCurrency = (amount: number) => {
    return `${amount.toLocaleString()} XOF`;
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'active': return 'text-green-600 bg-green-100';
      case 'expired': return 'text-red-600 bg-red-100';
      case 'converted': return 'text-blue-600 bg-blue-100';
      case 'cancelled': return 'text-gray-600 bg-gray-100';
      default: return 'text-gray-600 bg-gray-100';
    }
  };

  const getStatusLabel = (status: string) => {
    switch (status) {
      case 'active': return 'Actif';
      case 'expired': return 'Expiré';
      case 'converted': return 'Converti';
      case 'cancelled': return 'Annulé';
      default: return status;
    }
  };

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
      <div className="bg-white rounded-lg shadow-xl max-w-4xl w-full max-h-[90vh] overflow-y-auto">
        {/* Header */}
        <div className="flex items-center justify-between p-6 border-b border-gray-200">
          <div className="flex items-center space-x-3">
            <ShoppingCart className="w-6 h-6 text-blue-600" />
            <div>
              <h2 className="text-xl font-semibold text-gray-900">
                Créer une Commande
              </h2>
              <p className="text-sm text-gray-600">
                Devis: {quote.quote_number}
              </p>
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
        <div className="p-6 space-y-6">
          {/* Quote Summary */}
          <div className="bg-gray-50 rounded-lg p-4">
            <h3 className="text-lg font-medium text-gray-900 mb-4 flex items-center">
              <Shield className="w-5 h-5 text-blue-600 mr-2" />
              Résumé du Devis
            </h3>
            
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              {/* Client Info */}
              <div className="space-y-2">
                <div className="flex items-center text-sm">
                  <User className="w-4 h-4 text-gray-500 mr-2" />
                  <span className="font-medium">Client:</span>
                  <span className="ml-2">{quote.customer?.name}</span>
                </div>
                <div className="flex items-center text-sm">
                  <Mail className="w-4 h-4 text-gray-500 mr-2" />
                  <span className="font-medium">Email:</span>
                  <span className="ml-2">{quote.customer?.email}</span>
                </div>
              </div>

              {/* Product Info */}
              <div className="space-y-2">
                <div className="flex items-center text-sm">
                  <Package className="w-4 h-4 text-gray-500 mr-2" />
                  <span className="font-medium">Produit:</span>
                  <span className="ml-2">{quote.product?.name}</span>
                </div>
                <div className="flex items-center text-sm">
                  <Calendar className="w-4 h-4 text-gray-500 mr-2" />
                  <span className="font-medium">Statut:</span>
                  <span className={`ml-2 px-2 py-1 rounded-full text-xs ${getStatusColor(quote.quote_status)}`}>
                    {getStatusLabel(quote.quote_status)}
                  </span>
                </div>
              </div>
            </div>

            {/* Financial Details */}
            <div className="mt-4 pt-4 border-t border-gray-200">
              <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                <div className="text-center">
                  <div className="text-2xl font-bold text-blue-600">
                    {formatCurrency(quote.coverage_amount)}
                  </div>
                  <div className="text-sm text-gray-600">Couverture</div>
                </div>
                <div className="text-center">
                  <div className="text-2xl font-bold text-green-600">
                    {formatCurrency(quote.final_premium)}
                  </div>
                  <div className="text-sm text-gray-600">Prime Mensuelle</div>
                </div>
                <div className="text-center">
                  <div className="text-2xl font-bold text-purple-600">
                    {formatCurrency(quote.annual_premium)}
                  </div>
                  <div className="text-sm text-gray-600">Prime Annuelle</div>
                </div>
              </div>
            </div>

            {/* Eligibility */}
            <div className="mt-4 pt-4 border-t border-gray-200">
              <div className="flex items-center justify-center">
                {quote.eligible ? (
                  <div className="flex items-center text-green-600">
                    <CheckCircle className="w-5 h-5 mr-2" />
                    <span className="font-medium">Client Éligible</span>
                  </div>
                ) : (
                  <div className="flex items-center text-red-600">
                    <AlertTriangle className="w-5 h-5 mr-2" />
                    <span className="font-medium">Client Non Éligible</span>
                  </div>
                )}
              </div>
            </div>
          </div>

          {/* Order Configuration */}
          <div className="space-y-4">
            <h3 className="text-lg font-medium text-gray-900 flex items-center">
              <CreditCard className="w-5 h-5 text-blue-600 mr-2" />
              Configuration de la Commande
            </h3>

            {/* Payment Method */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Méthode de Paiement
              </label>
              <select
                value={paymentMethod}
                onChange={(e) => setPaymentMethod(e.target.value)}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
              >
                <option value="bank_transfer">Virement Bancaire</option>
                <option value="credit_card">Carte de Crédit</option>
                <option value="cash">Espèces</option>
                <option value="check">Chèque</option>
                <option value="mobile_money">Mobile Money</option>
              </select>
            </div>

            {/* Email Option */}
            <div className="flex items-center">
              <input
                type="checkbox"
                id="sendEmail"
                checked={sendEmail}
                onChange={(e) => setSendEmail(e.target.checked)}
                className="h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded"
              />
              <label htmlFor="sendEmail" className="ml-2 text-sm text-gray-700">
                Envoyer un email de confirmation au client
              </label>
            </div>

            {/* Notes */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Notes (optionnel)
              </label>
              <textarea
                value={notes}
                onChange={(e) => setNotes(e.target.value)}
                rows={3}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                placeholder="Ajoutez des notes sur cette commande..."
              />
            </div>
          </div>
        </div>

        {/* Footer */}
        <div className="flex items-center justify-end space-x-3 p-6 border-t border-gray-200 bg-gray-50">
          <button
            onClick={onClose}
            className="px-4 py-2 text-gray-700 bg-white border border-gray-300 rounded-lg hover:bg-gray-50 transition-colors"
          >
            Annuler
          </button>
          <button
            onClick={handleCreateOrder}
            disabled={isCreatingOrder || !quote.eligible}
            className="px-6 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors disabled:opacity-50 disabled:cursor-not-allowed flex items-center space-x-2"
          >
            {isCreatingOrder ? (
              <>
                <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white"></div>
                <span>Création...</span>
              </>
            ) : (
              <>
                <ShoppingCart className="w-4 h-4" />
                <span>Créer la Commande</span>
              </>
            )}
          </button>
        </div>
      </div>
    </div>
  );
};

export default QuoteToOrderModal;
