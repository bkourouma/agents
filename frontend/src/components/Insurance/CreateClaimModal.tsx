import React, { useState, useEffect } from 'react';
import { X, Search, User, Shield, AlertTriangle, Calendar, Euro, FileText } from 'lucide-react';
import { insuranceApi } from '../../lib/insurance-api';

interface Contract {
  id: string;
  contractNumber: string;
  policyNumber: string;
  customerId: string;
  customerName: string;
  productName: string;
  coverageAmount: number;
  contractStatus: string;
}

interface CreateClaimModalProps {
  isOpen: boolean;
  onClose: () => void;
  onClaimCreated: () => void;
}

const CreateClaimModal: React.FC<CreateClaimModalProps> = ({
  isOpen,
  onClose,
  onClaimCreated
}) => {
  const [contracts, setContracts] = useState<Contract[]>([]);
  const [selectedContract, setSelectedContract] = useState<Contract | null>(null);
  const [searchQuery, setSearchQuery] = useState('');
  const [loading, setLoading] = useState(false);
  const [creating, setCreating] = useState(false);
  
  const [claimData, setClaimData] = useState({
    claim_type: 'accident',
    claim_amount: '',
    incident_date: '',
    description: ''
  });

  useEffect(() => {
    if (isOpen) {
      loadActiveContracts();
    }
  }, [isOpen]);

  const loadActiveContracts = async () => {
    setLoading(true);
    try {
      const response = await insuranceApi.getAllContracts('active');
      
      if (response.success && response.data) {
        // Transformer les données de snake_case vers camelCase
        const transformedContracts = response.data.map((contract: any) => ({
          id: contract.id,
          contractNumber: contract.contract_number,
          policyNumber: contract.policy_number,
          customerId: contract.customer_id,
          customerName: contract.customer ? `${contract.customer.first_name} ${contract.customer.last_name}` : contract.customer_name || 'N/A',
          productName: contract.product ? contract.product.name : contract.product_name || 'N/A',
          coverageAmount: contract.coverage_amount || 0,
          contractStatus: contract.contract_status
        }));
        
        setContracts(transformedContracts);
      } else {
        console.error('Erreur lors du chargement des contrats:', response.error);
      }
    } catch (error) {
      console.error('Erreur lors du chargement des contrats:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleCreateClaim = async () => {
    if (!selectedContract || !claimData.claim_amount || !claimData.incident_date || !claimData.description) {
      alert('Veuillez remplir tous les champs obligatoires');
      return;
    }

    setCreating(true);
    try {
      const response = await insuranceApi.createClaim({
        contract_id: selectedContract.id,
        customer_id: selectedContract.customerId,
        claim_type: claimData.claim_type,
        claim_amount: parseFloat(claimData.claim_amount),
        incident_date: claimData.incident_date,
        description: claimData.description
      });

      if (response.success) {
        onClaimCreated();
        onClose();
        // Reset form
        setSelectedContract(null);
        setClaimData({
          claim_type: 'accident',
          claim_amount: '',
          incident_date: '',
          description: ''
        });
        alert('Réclamation créée avec succès!');
      } else {
        console.error('Erreur lors de la création:', response.error);
        alert('Erreur lors de la création de la réclamation');
      }
    } catch (error) {
      console.error('Erreur lors de la création:', error);
      alert('Erreur lors de la création de la réclamation');
    } finally {
      setCreating(false);
    }
  };

  const filteredContracts = contracts.filter(contract =>
    contract.policyNumber.toLowerCase().includes(searchQuery.toLowerCase()) ||
    contract.customerName.toLowerCase().includes(searchQuery.toLowerCase()) ||
    contract.productName.toLowerCase().includes(searchQuery.toLowerCase())
  );

  const claimTypes = [
    { value: 'accident', label: 'Accident' },
    { value: 'death', label: 'Décès' },
    { value: 'disability', label: 'Invalidité' },
    { value: 'health', label: 'Santé' },
    { value: 'theft', label: 'Vol' },
    { value: 'damage', label: 'Dommages' }
  ];

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <div className="bg-white rounded-lg shadow-xl w-full max-w-4xl max-h-[90vh] overflow-hidden">
        {/* Header */}
        <div className="flex items-center justify-between p-6 border-b border-gray-200">
          <div className="flex items-center space-x-3">
            <div className="w-10 h-10 bg-red-100 rounded-full flex items-center justify-center">
              <AlertTriangle className="w-5 h-5 text-red-600" />
            </div>
            <div>
              <h2 className="text-xl font-semibold text-gray-900">Créer une Nouvelle Réclamation</h2>
              <p className="text-sm text-gray-500">Sélectionnez un contrat actif et remplissez les détails</p>
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
        <div className="p-6 overflow-y-auto max-h-[calc(90vh-140px)]">
          {/* Recherche de contrat */}
          <div className="mb-6">
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Sélectionner un Contrat Actif
            </label>
            <div className="relative mb-4">
              <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400 w-4 h-4" />
              <input
                type="text"
                placeholder="Rechercher par police, client ou produit..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                className="w-full pl-10 pr-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              />
            </div>

            {loading ? (
              <div className="p-4 text-center text-gray-500">
                Chargement des contrats...
              </div>
            ) : (
              <div className="max-h-48 overflow-y-auto border border-gray-200 rounded-lg">
                {filteredContracts.map((contract) => (
                  <div
                    key={contract.id}
                    className={`p-4 border-b border-gray-100 cursor-pointer transition-colors ${
                      selectedContract?.id === contract.id
                        ? 'bg-blue-50 border-blue-200'
                        : 'hover:bg-gray-50'
                    }`}
                    onClick={() => setSelectedContract(contract)}
                  >
                    <div className="flex items-center justify-between">
                      <div className="flex items-center space-x-3">
                        <div className="w-8 h-8 bg-green-100 rounded-full flex items-center justify-center">
                          <Shield className="w-4 h-4 text-green-600" />
                        </div>
                        <div>
                          <div className="font-medium text-gray-900">{contract.policyNumber}</div>
                          <div className="text-sm text-gray-500">{contract.customerName}</div>
                        </div>
                      </div>
                      <div className="text-right">
                        <div className="font-medium text-gray-900">
                          {contract.coverageAmount.toLocaleString()} XOF
                        </div>
                        <div className="text-sm text-gray-500">{contract.productName}</div>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>

          {/* Formulaire de réclamation */}
          {selectedContract && (
            <div className="space-y-4">
              <h3 className="text-lg font-medium text-gray-900">Détails de la Réclamation</h3>
              
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Type de Réclamation *
                  </label>
                  <select
                    value={claimData.claim_type}
                    onChange={(e) => setClaimData(prev => ({ ...prev, claim_type: e.target.value }))}
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                  >
                    {claimTypes.map((type) => (
                      <option key={type.value} value={type.value}>
                        {type.label}
                      </option>
                    ))}
                  </select>
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Montant Réclamé (XOF) *
                  </label>
                  <input
                    type="number"
                    value={claimData.claim_amount}
                    onChange={(e) => setClaimData(prev => ({ ...prev, claim_amount: e.target.value }))}
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                    placeholder="0"
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Date de l'Incident *
                  </label>
                  <input
                    type="date"
                    value={claimData.incident_date}
                    onChange={(e) => setClaimData(prev => ({ ...prev, incident_date: e.target.value }))}
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                  />
                </div>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Description de l'Incident *
                </label>
                <textarea
                  value={claimData.description}
                  onChange={(e) => setClaimData(prev => ({ ...prev, description: e.target.value }))}
                  rows={4}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                  placeholder="Décrivez en détail les circonstances de l'incident..."
                />
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
            onClick={handleCreateClaim}
            disabled={!selectedContract || creating}
            className="px-4 py-2 bg-red-600 text-white rounded-lg hover:bg-red-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors flex items-center space-x-2"
          >
            {creating ? (
              <>
                <div className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin" />
                <span>Création...</span>
              </>
            ) : (
              <>
                <AlertTriangle className="w-4 h-4" />
                <span>Créer la Réclamation</span>
              </>
            )}
          </button>
        </div>
      </div>
    </div>
  );
};

export default CreateClaimModal;
