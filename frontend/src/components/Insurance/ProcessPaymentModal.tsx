import React, { useState } from 'react';
import { X, CreditCard, Calendar, DollarSign, FileText } from 'lucide-react';

interface Payment {
  id: string;
  policy_number: string;
  customer_name: string;
  amount: number;
  due_date: string;
  late_fee: number;
  days_overdue: number;
}

interface ProcessPaymentModalProps {
  isOpen: boolean;
  onClose: () => void;
  payment: Payment | null;
  onProcess: (paymentData: {
    payment_date: string;
    payment_method: string;
    transaction_id?: string;
  }) => void;
}

const ProcessPaymentModal: React.FC<ProcessPaymentModalProps> = ({
  isOpen,
  onClose,
  payment,
  onProcess
}) => {
  const [paymentData, setPaymentData] = useState({
    payment_date: new Date().toISOString().split('T')[0],
    payment_method: 'bank_transfer',
    transaction_id: '',
    notes: ''
  });

  const [processing, setProcessing] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    
    if (!payment) return;

    setProcessing(true);
    try {
      await onProcess({
        payment_date: paymentData.payment_date,
        payment_method: paymentData.payment_method,
        transaction_id: paymentData.transaction_id || undefined
      });
      
      // Reset form
      setPaymentData({
        payment_date: new Date().toISOString().split('T')[0],
        payment_method: 'bank_transfer',
        transaction_id: '',
        notes: ''
      });
    } finally {
      setProcessing(false);
    }
  };

  const paymentMethods = [
    { value: 'bank_transfer', label: 'Virement bancaire' },
    { value: 'credit_card', label: 'Carte de crédit' },
    { value: 'mobile_money', label: 'Mobile Money' },
    { value: 'cash', label: 'Espèces' },
    { value: 'check', label: 'Chèque' }
  ];

  if (!isOpen || !payment) return null;

  const totalAmount = payment.amount + payment.late_fee;

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <div className="bg-white rounded-lg shadow-xl w-full max-w-md max-h-[90vh] overflow-hidden">
        {/* Header */}
        <div className="flex items-center justify-between p-6 border-b border-gray-200">
          <div className="flex items-center space-x-3">
            <div className="w-10 h-10 bg-green-100 rounded-full flex items-center justify-center">
              <CreditCard className="w-5 h-5 text-green-600" />
            </div>
            <div>
              <h2 className="text-xl font-semibold text-gray-900">Traiter le Paiement</h2>
              <p className="text-sm text-gray-500">Police: {payment.policy_number}</p>
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
        <form onSubmit={handleSubmit} className="p-6 space-y-6">
          {/* Résumé du paiement */}
          <div className="bg-gray-50 rounded-lg p-4">
            <h3 className="font-medium text-gray-900 mb-3">Résumé du Paiement</h3>
            <div className="space-y-2 text-sm">
              <div className="flex justify-between">
                <span className="text-gray-600">Client:</span>
                <span className="font-medium">{payment.customer_name}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-gray-600">Montant de base:</span>
                <span className="font-medium">{payment.amount.toLocaleString()} XOF</span>
              </div>
              {payment.late_fee > 0 && (
                <div className="flex justify-between">
                  <span className="text-gray-600">Frais de retard:</span>
                  <span className="font-medium text-red-600">{payment.late_fee.toLocaleString()} XOF</span>
                </div>
              )}
              <div className="flex justify-between border-t pt-2">
                <span className="text-gray-900 font-medium">Total à payer:</span>
                <span className="font-bold text-lg">{totalAmount.toLocaleString()} XOF</span>
              </div>
              {payment.days_overdue > 0 && (
                <div className="text-xs text-red-600">
                  Paiement en retard de {payment.days_overdue} jour(s)
                </div>
              )}
            </div>
          </div>

          {/* Formulaire de paiement */}
          <div className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Date de Paiement *
              </label>
              <div className="relative">
                <Calendar className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400 w-4 h-4" />
                <input
                  type="date"
                  value={paymentData.payment_date}
                  onChange={(e) => setPaymentData(prev => ({ ...prev, payment_date: e.target.value }))}
                  className="w-full pl-10 pr-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-green-500 focus:border-transparent"
                  required
                />
              </div>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Méthode de Paiement *
              </label>
              <select
                value={paymentData.payment_method}
                onChange={(e) => setPaymentData(prev => ({ ...prev, payment_method: e.target.value }))}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-green-500 focus:border-transparent"
                required
              >
                {paymentMethods.map((method) => (
                  <option key={method.value} value={method.value}>
                    {method.label}
                  </option>
                ))}
              </select>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                ID de Transaction
              </label>
              <div className="relative">
                <FileText className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400 w-4 h-4" />
                <input
                  type="text"
                  value={paymentData.transaction_id}
                  onChange={(e) => setPaymentData(prev => ({ ...prev, transaction_id: e.target.value }))}
                  className="w-full pl-10 pr-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-green-500 focus:border-transparent"
                  placeholder="Numéro de référence (optionnel)"
                />
              </div>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Notes (optionnel)
              </label>
              <textarea
                value={paymentData.notes}
                onChange={(e) => setPaymentData(prev => ({ ...prev, notes: e.target.value }))}
                rows={3}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-green-500 focus:border-transparent"
                placeholder="Notes additionnelles sur le paiement..."
              />
            </div>
          </div>

          {/* Footer */}
          <div className="flex justify-end space-x-3 pt-4 border-t border-gray-200">
            <button
              type="button"
              onClick={onClose}
              className="px-4 py-2 text-gray-700 bg-gray-100 rounded-lg hover:bg-gray-200 transition-colors"
            >
              Annuler
            </button>
            <button
              type="submit"
              disabled={processing}
              className="px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors flex items-center space-x-2"
            >
              {processing ? (
                <>
                  <div className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin" />
                  <span>Traitement...</span>
                </>
              ) : (
                <>
                  <CreditCard className="w-4 h-4" />
                  <span>Confirmer le Paiement</span>
                </>
              )}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};

export default ProcessPaymentModal;
