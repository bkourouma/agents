import React, { useState, useEffect } from 'react';
import { X, Save, AlertCircle, User, Package, CreditCard, Calendar, FileText } from 'lucide-react';
import { insuranceApi } from '../../lib/insurance-api';

// Interface pour une commande (compatible avec OrderManagement)
interface Order {
  id: string;
  orderNumber: string;
  customerId: string;
  productId: string;
  orderStatus: string;
  customerName: string;
  productName: string;
  coverageAmount: number;
  premiumAmount: number;
  premiumFrequency: string;
  paymentMethod: string;
  applicationDate: string;
  effectiveDate?: string;
  expiryDate?: string;
  medicalExamRequired?: boolean;
  medicalExamCompleted?: boolean;
  documentsReceived?: boolean;
  notes?: string;
}

interface EditOrderModalProps {
  isOpen: boolean;
  onClose: () => void;
  order: Order | null;
  onOrderUpdated?: (updatedOrder: Order) => void;
}

export default function EditOrderModal({ isOpen, onClose, order, onOrderUpdated }: EditOrderModalProps) {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [formData, setFormData] = useState({
    orderStatus: '',
    paymentMethod: '',
    effectiveDate: '',
    expiryDate: '',
    medicalExamRequired: false,
    medicalExamCompleted: false,
    documentsReceived: false,
    notes: ''
  });

  // Initialiser le formulaire avec les données de la commande
  useEffect(() => {
    if (order) {
      setFormData({
        orderStatus: order.orderStatus || '',
        paymentMethod: order.paymentMethod || '',
        effectiveDate: order.effectiveDate || '',
        expiryDate: order.expiryDate || '',
        medicalExamRequired: order.medicalExamRequired || false,
        medicalExamCompleted: order.medicalExamCompleted || false,
        documentsReceived: order.documentsReceived || false,
        notes: order.notes || ''
      });
      setError(null); // Reset error when order changes
    }
  }, [order]);

  const handleInputChange = (e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement | HTMLTextAreaElement>) => {
    const { name, value, type } = e.target;
    
    if (type === 'checkbox') {
      const checked = (e.target as HTMLInputElement).checked;
      setFormData(prev => ({
        ...prev,
        [name]: checked
      }));
    } else {
      setFormData(prev => ({
        ...prev,
        [name]: value
      }));
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    
    if (!order) return;

    setLoading(true);
    setError(null);

    try {
      // Préparer les données pour l'API
      const updateData = {
        order_status: formData.orderStatus,
        payment_method: formData.paymentMethod,
        effective_date: formData.effectiveDate || null,
        expiry_date: formData.expiryDate || null,
        medical_exam_required: formData.medicalExamRequired,
        medical_exam_completed: formData.medicalExamCompleted,
        documents_received: formData.documentsReceived,
        notes: formData.notes || null
      };

      console.log('Mise à jour de la commande:', order.orderNumber, updateData);

      // Appel API réel
      const response = await insuranceApi.updateOrder(order.id, updateData);

      if (response.success && response.data) {
        // Créer l'objet commande mis à jour avec les données de l'API
        const updatedOrder: Order = {
          ...order,
          orderStatus: response.data.order_status || formData.orderStatus,
          paymentMethod: response.data.payment_method || formData.paymentMethod,
          effectiveDate: response.data.effective_date || formData.effectiveDate,
          expiryDate: response.data.expiry_date || formData.expiryDate,
          medicalExamRequired: response.data.medical_exam_required ?? formData.medicalExamRequired,
          medicalExamCompleted: response.data.medical_exam_completed ?? formData.medicalExamCompleted,
          documentsReceived: response.data.documents_received ?? formData.documentsReceived,
          notes: response.data.notes || formData.notes
        };

        // Notifier le parent
        if (onOrderUpdated) {
          onOrderUpdated(updatedOrder);
        }

        // Fermer la modal
        onClose();

        // Message de succès
        alert(`Commande ${order.orderNumber} mise à jour avec succès !`);
      } else {
        throw new Error(response.error || 'Erreur lors de la mise à jour');
      }

    } catch (error) {
      console.error('Erreur lors de la mise à jour:', error);
      const errorMessage = error instanceof Error ? error.message : 'Erreur lors de la mise à jour de la commande';
      setError(errorMessage);
    } finally {
      setLoading(false);
    }
  };

  if (!isOpen || !order) return null;

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
      <div className="bg-white rounded-lg shadow-xl max-w-2xl w-full max-h-[90vh] overflow-y-auto">
        {/* Header */}
        <div className="flex items-center justify-between p-6 border-b border-gray-200">
          <div className="flex items-center space-x-3">
            <div className="w-10 h-10 bg-blue-100 rounded-full flex items-center justify-center">
              <FileText className="w-5 h-5 text-blue-600" />
            </div>
            <div>
              <h2 className="text-xl font-semibold text-gray-900">Modifier la Commande</h2>
              <p className="text-sm text-gray-500">{order.orderNumber}</p>
            </div>
          </div>
          <button
            onClick={onClose}
            className="text-gray-400 hover:text-gray-600 transition-colors"
          >
            <X className="w-6 h-6" />
          </button>
        </div>

        {/* Form */}
        <form onSubmit={handleSubmit} className="p-6 space-y-6">
          {/* Informations non modifiables */}
          <div className="bg-gray-50 p-4 rounded-lg">
            <h3 className="font-medium text-gray-900 mb-3">Informations de Base (Non modifiables)</h3>
            <div className="grid grid-cols-2 gap-4 text-sm">
              <div className="flex items-center">
                <User className="w-4 h-4 text-gray-500 mr-2" />
                <span className="text-gray-600">Client:</span>
                <span className="ml-2 font-medium">{order.customerName}</span>
              </div>
              <div className="flex items-center">
                <Package className="w-4 h-4 text-gray-500 mr-2" />
                <span className="text-gray-600">Produit:</span>
                <span className="ml-2 font-medium">{order.productName}</span>
              </div>
              <div>
                <span className="text-gray-600">Couverture:</span>
                <span className="ml-2 font-medium">{order.coverageAmount.toLocaleString()} XOF</span>
              </div>
              <div>
                <span className="text-gray-600">Prime:</span>
                <span className="ml-2 font-medium">{order.premiumAmount.toLocaleString()} XOF/{order.premiumFrequency === 'monthly' ? 'mois' : 'an'}</span>
              </div>
            </div>
          </div>

          {/* Message d'erreur */}
          {error && (
            <div className="bg-red-50 border border-red-200 rounded-lg p-4">
              <div className="flex items-center">
                <AlertCircle className="w-5 h-5 text-red-500 mr-2" />
                <span className="text-red-800 font-medium">Erreur</span>
              </div>
              <p className="text-red-700 text-sm mt-1">{error}</p>
            </div>
          )}

          {/* Champs modifiables */}
          <div className="space-y-4">
            <h3 className="font-medium text-gray-900">Informations Modifiables</h3>
            
            {/* Statut de la commande */}
            <div>
              <label htmlFor="orderStatus" className="block text-sm font-medium text-gray-700 mb-1">
                Statut de la Commande
              </label>
              <select
                id="orderStatus"
                name="orderStatus"
                value={formData.orderStatus}
                onChange={handleInputChange}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
              >
                <option value="draft">Brouillon</option>
                <option value="submitted">Soumise</option>
                <option value="under_review">En révision</option>
                <option value="approved">Approuvée</option>
                <option value="rejected">Rejetée</option>
                <option value="cancelled">Annulée</option>
              </select>
            </div>

            {/* Méthode de paiement */}
            <div>
              <label htmlFor="paymentMethod" className="block text-sm font-medium text-gray-700 mb-1">
                Méthode de Paiement
              </label>
              <select
                id="paymentMethod"
                name="paymentMethod"
                value={formData.paymentMethod}
                onChange={handleInputChange}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
              >
                <option value="bank_transfer">Virement bancaire</option>
                <option value="credit_card">Carte de crédit</option>
                <option value="cash">Espèces</option>
                <option value="check">Chèque</option>
                <option value="mobile_money">Mobile Money</option>
              </select>
            </div>

            {/* Dates */}
            <div className="grid grid-cols-2 gap-4">
              <div>
                <label htmlFor="effectiveDate" className="block text-sm font-medium text-gray-700 mb-1">
                  Date d'Effet
                </label>
                <input
                  type="date"
                  id="effectiveDate"
                  name="effectiveDate"
                  value={formData.effectiveDate}
                  onChange={handleInputChange}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                />
              </div>
              <div>
                <label htmlFor="expiryDate" className="block text-sm font-medium text-gray-700 mb-1">
                  Date d'Expiration
                </label>
                <input
                  type="date"
                  id="expiryDate"
                  name="expiryDate"
                  value={formData.expiryDate}
                  onChange={handleInputChange}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                />
              </div>
            </div>

            {/* Cases à cocher */}
            <div className="space-y-3">
              <div className="flex items-center">
                <input
                  type="checkbox"
                  id="medicalExamRequired"
                  name="medicalExamRequired"
                  checked={formData.medicalExamRequired}
                  onChange={handleInputChange}
                  className="h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded"
                />
                <label htmlFor="medicalExamRequired" className="ml-2 text-sm text-gray-700">
                  Examen médical requis
                </label>
              </div>
              
              <div className="flex items-center">
                <input
                  type="checkbox"
                  id="medicalExamCompleted"
                  name="medicalExamCompleted"
                  checked={formData.medicalExamCompleted}
                  onChange={handleInputChange}
                  className="h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded"
                />
                <label htmlFor="medicalExamCompleted" className="ml-2 text-sm text-gray-700">
                  Examen médical complété
                </label>
              </div>
              
              <div className="flex items-center">
                <input
                  type="checkbox"
                  id="documentsReceived"
                  name="documentsReceived"
                  checked={formData.documentsReceived}
                  onChange={handleInputChange}
                  className="h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded"
                />
                <label htmlFor="documentsReceived" className="ml-2 text-sm text-gray-700">
                  Documents reçus
                </label>
              </div>
            </div>

            {/* Notes */}
            <div>
              <label htmlFor="notes" className="block text-sm font-medium text-gray-700 mb-1">
                Notes
              </label>
              <textarea
                id="notes"
                name="notes"
                value={formData.notes}
                onChange={handleInputChange}
                rows={3}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                placeholder="Ajoutez des notes sur cette commande..."
              />
            </div>
          </div>

          {/* Actions */}
          <div className="flex space-x-3 pt-4 border-t border-gray-200">
            <button
              type="button"
              onClick={onClose}
              className="flex-1 px-4 py-2 text-gray-700 bg-gray-100 rounded-lg hover:bg-gray-200 transition-colors"
            >
              Annuler
            </button>
            <button
              type="submit"
              disabled={loading}
              className="flex-1 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors disabled:opacity-50 flex items-center justify-center space-x-2"
            >
              <Save className="w-4 h-4" />
              <span>{loading ? 'Sauvegarde...' : 'Sauvegarder'}</span>
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
