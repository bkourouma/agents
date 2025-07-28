import React, { useState, useEffect } from 'react';
import { X, FileText, User, Package, Calendar, CreditCard, Clock, CheckCircle, XCircle, AlertTriangle } from 'lucide-react';
import { insuranceApi } from '../../lib/insurance-api';

interface Contract {
  id: string;
  policyNumber: string;
  contractStatus: string;
  coverageAmount: number;
  premiumAmount: number;
  premiumFrequency: string;
  issueDate: string;
  effectiveDate: string;
  expiryDate?: string;
  nextRenewalDate?: string;
  nextPremiumDueDate?: string;
}

interface ContractDetailsModalProps {
  isOpen: boolean;
  onClose: () => void;
  contract: Contract | null;
}

export default function ContractDetailsModal({ isOpen, onClose, contract }: ContractDetailsModalProps) {
  const [loading, setLoading] = useState(false);
  const [contractDetails, setContractDetails] = useState<any>(null);
  const [paymentHistory, setPaymentHistory] = useState<any[]>([]);

  useEffect(() => {
    if (isOpen && contract) {
      loadContractDetails();
    }
  }, [isOpen, contract]);

  const loadContractDetails = async () => {
    if (!contract) return;
    
    setLoading(true);
    try {
      // Load contract details
      const detailsResponse = await insuranceApi.getContractDetails(contract.policyNumber);
      if (detailsResponse.success) {
        setContractDetails(detailsResponse.data);
      }

      // Load payment history
      const paymentsResponse = await insuranceApi.getContractPaymentHistory(contract.policyNumber);
      if (paymentsResponse.success) {
        setPaymentHistory(paymentsResponse.data);
      }
    } catch (error) {
      console.error('Erreur lors du chargement des détails:', error);
    } finally {
      setLoading(false);
    }
  };

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'active':
        return <CheckCircle className="w-5 h-5 text-green-500" />;
      case 'suspended':
        return <Clock className="w-5 h-5 text-yellow-500" />;
      case 'lapsed':
        return <AlertTriangle className="w-5 h-5 text-orange-500" />;
      case 'cancelled':
      case 'expired':
        return <XCircle className="w-5 h-5 text-red-500" />;
      case 'claimed':
        return <CheckCircle className="w-5 h-5 text-blue-500" />;
      default:
        return <Clock className="w-5 h-5 text-gray-500" />;
    }
  };

  const getStatusLabel = (status: string) => {
    switch (status) {
      case 'active': return 'Actif';
      case 'suspended': return 'Suspendu';
      case 'lapsed': return 'Échu';
      case 'cancelled': return 'Annulé';
      case 'expired': return 'Expiré';
      case 'claimed': return 'Réclamé';
      default: return status;
    }
  };

  const formatFrequency = (frequency: string) => {
    switch (frequency) {
      case 'monthly': return 'Mensuelle';
      case 'quarterly': return 'Trimestrielle';
      case 'semi-annual': return 'Semestrielle';
      case 'annual': return 'Annuelle';
      default: return frequency;
    }
  };

  if (!isOpen || !contract) return null;

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
      <div className="bg-white rounded-lg shadow-xl max-w-4xl w-full max-h-[90vh] overflow-y-auto">
        {/* Header */}
        <div className="flex items-center justify-between p-6 border-b border-gray-200">
          <div className="flex items-center space-x-3">
            <div className="w-10 h-10 bg-blue-100 rounded-full flex items-center justify-center">
              <FileText className="w-5 h-5 text-blue-600" />
            </div>
            <div>
              <h2 className="text-xl font-semibold text-gray-900">Détails du Contrat</h2>
              <p className="text-sm text-gray-500">{contract.policyNumber}</p>
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
          {loading ? (
            <div className="text-center py-8">
              <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600 mx-auto"></div>
              <p className="text-gray-500 mt-2">Chargement des détails...</p>
            </div>
          ) : (
            <div className="space-y-6">
              {/* Informations principales */}
              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                {/* Informations du contrat */}
                <div className="bg-gray-50 p-4 rounded-lg">
                  <h3 className="font-medium text-gray-900 mb-3 flex items-center">
                    <FileText className="w-4 h-4 mr-2" />
                    Informations du Contrat
                  </h3>
                  <div className="space-y-2 text-sm">
                    <div className="flex justify-between">
                      <span className="text-gray-600">Numéro de police:</span>
                      <span className="font-medium">{contract.policyNumber}</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-gray-600">Statut:</span>
                      <div className="flex items-center space-x-1">
                        {getStatusIcon(contract.contractStatus)}
                        <span className="font-medium">{getStatusLabel(contract.contractStatus)}</span>
                      </div>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-gray-600">Couverture:</span>
                      <span className="font-medium">{(contract.coverageAmount || 0).toLocaleString()} XOF</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-gray-600">Prime:</span>
                      <span className="font-medium">
                        {(contract.premiumAmount || 0).toLocaleString()} XOF
                      </span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-gray-600">Fréquence:</span>
                      <span className="font-medium">{formatFrequency(contract.premiumFrequency)}</span>
                    </div>
                  </div>
                </div>

                {/* Informations client */}
                {contractDetails?.customer && (
                  <div className="bg-gray-50 p-4 rounded-lg">
                    <h3 className="font-medium text-gray-900 mb-3 flex items-center">
                      <User className="w-4 h-4 mr-2" />
                      Informations Client
                    </h3>
                    <div className="space-y-2 text-sm">
                      <div className="flex justify-between">
                        <span className="text-gray-600">Nom:</span>
                        <span className="font-medium">
                          {contractDetails.customer.first_name} {contractDetails.customer.last_name}
                        </span>
                      </div>
                      <div className="flex justify-between">
                        <span className="text-gray-600">Email:</span>
                        <span className="font-medium">{contractDetails.customer.email}</span>
                      </div>
                      <div className="flex justify-between">
                        <span className="text-gray-600">Téléphone:</span>
                        <span className="font-medium">{contractDetails.customer.phone}</span>
                      </div>
                      <div className="flex justify-between">
                        <span className="text-gray-600">Date de naissance:</span>
                        <span className="font-medium">
                          {new Date(contractDetails.customer.date_of_birth).toLocaleDateString('fr-FR')}
                        </span>
                      </div>
                    </div>
                  </div>
                )}
              </div>

              {/* Dates importantes */}
              <div className="bg-gray-50 p-4 rounded-lg">
                <h3 className="font-medium text-gray-900 mb-3 flex items-center">
                  <Calendar className="w-4 h-4 mr-2" />
                  Dates Importantes
                </h3>
                <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm">
                  <div>
                    <span className="text-gray-600 block">Date d'émission:</span>
                    <span className="font-medium">
                      {new Date(contract.issueDate).toLocaleDateString('fr-FR')}
                    </span>
                  </div>
                  <div>
                    <span className="text-gray-600 block">Date d'effet:</span>
                    <span className="font-medium">
                      {new Date(contract.effectiveDate).toLocaleDateString('fr-FR')}
                    </span>
                  </div>
                  {contract.expiryDate && (
                    <div>
                      <span className="text-gray-600 block">Date d'expiration:</span>
                      <span className="font-medium">
                        {new Date(contract.expiryDate).toLocaleDateString('fr-FR')}
                      </span>
                    </div>
                  )}
                  {contract.nextRenewalDate && (
                    <div>
                      <span className="text-gray-600 block">Prochain renouvellement:</span>
                      <span className="font-medium">
                        {new Date(contract.nextRenewalDate).toLocaleDateString('fr-FR')}
                      </span>
                    </div>
                  )}
                </div>
              </div>

              {/* Produit d'assurance */}
              {contractDetails?.product && (
                <div className="bg-gray-50 p-4 rounded-lg">
                  <h3 className="font-medium text-gray-900 mb-3 flex items-center">
                    <Package className="w-4 h-4 mr-2" />
                    Produit d'Assurance
                  </h3>
                  <div className="grid grid-cols-2 gap-4 text-sm">
                    <div>
                      <span className="text-gray-600 block">Nom du produit:</span>
                      <span className="font-medium">{contractDetails.product.name}</span>
                    </div>
                    <div>
                      <span className="text-gray-600 block">Type:</span>
                      <span className="font-medium">{contractDetails.product.product_type}</span>
                    </div>
                    <div className="col-span-2">
                      <span className="text-gray-600 block">Description:</span>
                      <span className="font-medium">{contractDetails.product.description}</span>
                    </div>
                  </div>
                </div>
              )}

              {/* Historique des paiements */}
              <div className="bg-gray-50 p-4 rounded-lg">
                <h3 className="font-medium text-gray-900 mb-3 flex items-center">
                  <CreditCard className="w-4 h-4 mr-2" />
                  Historique des Paiements ({paymentHistory.length})
                </h3>
                {paymentHistory.length > 0 ? (
                  <div className="space-y-2">
                    {paymentHistory.slice(0, 5).map((payment, index) => (
                      <div key={index} className="flex justify-between items-center py-2 border-b border-gray-200 last:border-b-0">
                        <div>
                          <span className="font-medium">{(payment.amount || 0).toLocaleString()} XOF</span>
                          <span className="text-gray-500 text-sm ml-2">
                            {payment.payment_date ? new Date(payment.payment_date).toLocaleDateString('fr-FR') : 'Date inconnue'}
                          </span>
                        </div>
                        <span className={`px-2 py-1 rounded-full text-xs font-medium ${
                          payment.status === 'completed' ? 'bg-green-100 text-green-800' :
                          payment.status === 'pending' ? 'bg-yellow-100 text-yellow-800' :
                          'bg-red-100 text-red-800'
                        }`}>
                          {payment.status === 'completed' ? 'Payé' :
                           payment.status === 'pending' ? 'En attente' : 'Échoué'}
                        </span>
                      </div>
                    ))}
                    {paymentHistory.length > 5 && (
                      <p className="text-sm text-gray-500 text-center pt-2">
                        ... et {paymentHistory.length - 5} autres paiements
                      </p>
                    )}
                  </div>
                ) : (
                  <p className="text-gray-500 text-sm">Aucun paiement enregistré</p>
                )}
              </div>

              {/* Bénéficiaires */}
              {contractDetails?.beneficiaries && contractDetails.beneficiaries.length > 0 && (
                <div className="bg-gray-50 p-4 rounded-lg">
                  <h3 className="font-medium text-gray-900 mb-3 flex items-center">
                    <User className="w-4 h-4 mr-2" />
                    Bénéficiaires ({contractDetails.beneficiaries.length})
                  </h3>
                  <div className="space-y-2">
                    {contractDetails.beneficiaries.map((beneficiary: any, index: number) => (
                      <div key={index} className="flex justify-between items-center py-2 border-b border-gray-200 last:border-b-0">
                        <div>
                          <span className="font-medium">{beneficiary.first_name} {beneficiary.last_name}</span>
                          <span className="text-gray-500 text-sm ml-2">({beneficiary.relationship})</span>
                        </div>
                        <span className="text-sm font-medium">{beneficiary.percentage}%</span>
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </div>
          )}
        </div>

        {/* Footer */}
        <div className="flex justify-end space-x-3 p-6 border-t border-gray-200">
          <button
            onClick={onClose}
            className="px-4 py-2 text-gray-700 bg-gray-100 rounded-lg hover:bg-gray-200 transition-colors"
          >
            Fermer
          </button>
          <button className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors">
            Modifier le Contrat
          </button>
        </div>
      </div>
    </div>
  );
}
