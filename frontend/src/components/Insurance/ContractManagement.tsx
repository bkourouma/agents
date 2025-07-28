import React, { useState, useEffect } from 'react';
import {
  FileText,
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
  CreditCard,
  RefreshCw,
  Search,
  Filter
} from 'lucide-react';
import { insuranceApi } from '../../lib/insurance-api';
import ContractDetailsModal from './ContractDetailsModal';
import CreateContractModal from './CreateContractModal';

interface Contract {
  id: string;
  policyNumber: string;
  orderId: string;
  customerId: string;
  productId: string;
  contractStatus: string;
  coverageAmount: number;
  premiumAmount: number;
  premiumFrequency: string;
  issueDate: string;
  effectiveDate: string;
  expiryDate?: string;
  nextRenewalDate?: string;
  nextPremiumDueDate?: string;
  customer?: {
    id: string;
    firstName: string;
    lastName: string;
    email: string;
  };
  product?: {
    id: string;
    name: string;
    productType: string;
  };
}

interface ContractDetails {
  contract: Contract;
  customer: any;
  product: any;
  beneficiaries: any[];
  paymentHistory: any[];
}

export default function ContractManagement() {
  const [contracts, setContracts] = useState<Contract[]>([]);
  const [selectedContract, setSelectedContract] = useState<Contract | null>(null);
  const [contractDetails, setContractDetails] = useState<ContractDetails | null>(null);
  const [loading, setLoading] = useState(false);
  const [statusFilter, setStatusFilter] = useState<string>('all');
  const [searchTerm, setSearchTerm] = useState('');
  const [showDetailsModal, setShowDetailsModal] = useState(false);
  const [showCreateModal, setShowCreateModal] = useState(false);

  useEffect(() => {
    loadContracts();
  }, [statusFilter]);

  // Rafraîchir automatiquement quand le composant devient visible
  useEffect(() => {
    const handleVisibilityChange = () => {
      if (!document.hidden) {
        loadContracts();
      }
    };

    const handleFocus = () => {
      loadContracts();
    };

    document.addEventListener('visibilitychange', handleVisibilityChange);
    window.addEventListener('focus', handleFocus);

    // Écouter les événements de création de contrat
    const handleNewContract = () => {
      loadContracts();
    };

    window.addEventListener('newContractCreated', handleNewContract);

    return () => {
      document.removeEventListener('visibilitychange', handleVisibilityChange);
      window.removeEventListener('focus', handleFocus);
      window.removeEventListener('newContractCreated', handleNewContract);
    };
  }, []);

  const loadContracts = async () => {
    setLoading(true);
    try {
      const response = await insuranceApi.getAllContracts(statusFilter);

      if (response.success && response.data) {
        // Transformer les données de snake_case vers camelCase
        const transformedContracts = response.data.map((contract: any) => ({
          id: contract.id,
          policyNumber: contract.policy_number,
          orderId: contract.order_id,
          customerId: contract.customer_id,
          productId: contract.product_id,
          contractStatus: contract.contract_status,
          coverageAmount: contract.coverage_amount || 0,
          premiumAmount: contract.premium_amount || 0,
          premiumFrequency: contract.premium_frequency,
          issueDate: contract.issue_date,
          effectiveDate: contract.effective_date,
          expiryDate: contract.expiry_date,
          nextRenewalDate: contract.next_renewal_date,
          nextPremiumDueDate: contract.next_premium_due_date,
          customer: contract.customer,
          product: contract.product
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

  const handleViewContract = async (contract: Contract) => {
    setSelectedContract(contract);
    setLoading(true);

    try {
      const response = await insuranceApi.getContractDetails(contract.policyNumber);

      if (response.success && response.data) {
        setContractDetails(response.data);
      } else {
        console.error('Erreur lors du chargement des détails:', response.error);
        setContractDetails(null);
      }
    } catch (error) {
      console.error('Erreur lors du chargement des détails:', error);
      setContractDetails(null);
    } finally {
      setLoading(false);
    }
  };

  const getStatusBadge = (status: string) => {
    switch (status) {
      case 'active':
        return <span className="px-2 py-1 rounded-full text-xs font-medium bg-green-100 text-green-800">Actif</span>;
      case 'suspended':
        return <span className="px-2 py-1 rounded-full text-xs font-medium bg-yellow-100 text-yellow-800">Suspendu</span>;
      case 'lapsed':
        return <span className="px-2 py-1 rounded-full text-xs font-medium bg-orange-100 text-orange-800">Échu</span>;
      case 'cancelled':
        return <span className="px-2 py-1 rounded-full text-xs font-medium bg-red-100 text-red-800">Annulé</span>;
      case 'expired':
        return <span className="px-2 py-1 rounded-full text-xs font-medium bg-gray-100 text-gray-800">Expiré</span>;
      case 'claimed':
        return <span className="px-2 py-1 rounded-full text-xs font-medium bg-blue-100 text-blue-800">Réclamé</span>;
      default:
        return <span className="px-2 py-1 rounded-full text-xs font-medium bg-gray-100 text-gray-800">{status}</span>;
    }
  };

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'active':
        return <CheckCircle className="w-4 h-4 text-green-500" />;
      case 'suspended':
        return <Clock className="w-4 h-4 text-yellow-500" />;
      case 'lapsed':
        return <AlertTriangle className="w-4 h-4 text-orange-500" />;
      case 'cancelled':
      case 'expired':
        return <XCircle className="w-4 h-4 text-red-500" />;
      case 'claimed':
        return <CheckCircle className="w-4 h-4 text-blue-500" />;
      default:
        return <Clock className="w-4 h-4 text-gray-500" />;
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

  // Filtrer les contrats par terme de recherche
  const filteredContracts = contracts.filter(contract => {
    if (!searchTerm) return true;
    
    const searchLower = searchTerm.toLowerCase();
    return (
      contract.policyNumber.toLowerCase().includes(searchLower) ||
      contract.customer?.firstName?.toLowerCase().includes(searchLower) ||
      contract.customer?.lastName?.toLowerCase().includes(searchLower) ||
      contract.product?.name?.toLowerCase().includes(searchLower)
    );
  });

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="bg-white rounded-lg shadow-md p-6">
        <div className="flex justify-between items-center mb-4">
          <h2 className="text-xl font-semibold text-gray-900">Gestion des Contrats</h2>
          <div className="flex space-x-2">
            <button
              onClick={loadContracts}
              disabled={loading}
              className="bg-gray-600 text-white px-4 py-2 rounded-lg hover:bg-gray-700 transition-colors flex items-center space-x-2 disabled:opacity-50"
            >
              <RefreshCw className={`w-4 h-4 ${loading ? 'animate-spin' : ''}`} />
              <span>Rafraîchir</span>
            </button>
            <button
              onClick={() => setShowCreateModal(true)}
              className="bg-blue-600 text-white px-4 py-2 rounded-lg hover:bg-blue-700 transition-colors flex items-center space-x-2"
            >
              <Plus className="w-4 h-4" />
              <span>Nouveau Contrat</span>
            </button>
          </div>
        </div>

        {/* Filtres et recherche */}
        <div className="flex flex-col sm:flex-row gap-4 mb-4">
          <div className="flex-1">
            <div className="relative">
              <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400 w-4 h-4" />
              <input
                type="text"
                placeholder="Rechercher par numéro de police, client ou produit..."
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                className="w-full pl-10 pr-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
              />
            </div>
          </div>
          <div className="flex items-center space-x-2">
            <Filter className="w-4 h-4 text-gray-500" />
            <select
              value={statusFilter}
              onChange={(e) => setStatusFilter(e.target.value)}
              className="border border-gray-300 rounded-lg px-3 py-2 focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
            >
              <option value="all">Tous les statuts</option>
              <option value="active">Actifs</option>
              <option value="suspended">Suspendus</option>
              <option value="lapsed">Échus</option>
              <option value="cancelled">Annulés</option>
              <option value="expired">Expirés</option>
              <option value="claimed">Réclamés</option>
            </select>
          </div>
        </div>

        {/* Statistiques rapides */}
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          <div className="bg-green-50 p-3 rounded-lg">
            <div className="text-green-600 text-sm font-medium">Contrats Actifs</div>
            <div className="text-green-900 text-lg font-bold">
              {contracts.filter(c => c.contractStatus === 'active').length}
            </div>
          </div>
          <div className="bg-yellow-50 p-3 rounded-lg">
            <div className="text-yellow-600 text-sm font-medium">Suspendus</div>
            <div className="text-yellow-900 text-lg font-bold">
              {contracts.filter(c => c.contractStatus === 'suspended').length}
            </div>
          </div>
          <div className="bg-orange-50 p-3 rounded-lg">
            <div className="text-orange-600 text-sm font-medium">Échus</div>
            <div className="text-orange-900 text-lg font-bold">
              {contracts.filter(c => c.contractStatus === 'lapsed').length}
            </div>
          </div>
          <div className="bg-blue-50 p-3 rounded-lg">
            <div className="text-blue-600 text-sm font-medium">Total</div>
            <div className="text-blue-900 text-lg font-bold">{contracts.length}</div>
          </div>
        </div>
      </div>

      {/* Contenu principal */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Liste des contrats */}
        <div className="bg-white rounded-lg shadow-md">
          <div className="p-4 border-b border-gray-200">
            <h3 className="text-lg font-semibold text-gray-900">
              Contrats ({filteredContracts.length})
            </h3>
          </div>
          <div className="max-h-96 overflow-y-auto">
            {loading ? (
              <div className="p-8 text-center">
                <RefreshCw className="w-8 h-8 animate-spin mx-auto mb-4 text-gray-400" />
                <p className="text-gray-500">Chargement des contrats...</p>
              </div>
            ) : filteredContracts.length === 0 ? (
              <div className="p-8 text-center">
                <FileText className="w-12 h-12 mx-auto mb-4 text-gray-300" />
                <p className="text-gray-500">Aucun contrat trouvé</p>
              </div>
            ) : (
              filteredContracts.map((contract) => (
                <div
                  key={contract.id}
                  className="p-4 border-b border-gray-100 hover:bg-gray-50 cursor-pointer"
                  onClick={() => handleViewContract(contract)}
                >
                  <div className="flex items-center justify-between">
                    <div className="flex items-center space-x-3">
                      <div className="w-10 h-10 bg-blue-100 rounded-full flex items-center justify-center">
                        <FileText className="w-5 h-5 text-blue-600" />
                      </div>
                      <div>
                        <div className="font-medium text-gray-900">{contract.policyNumber}</div>
                        <div className="text-sm text-gray-500">
                          {contract.customer?.firstName} {contract.customer?.lastName}
                        </div>
                      </div>
                    </div>
                    <div className="text-right">
                      {getStatusBadge(contract.contractStatus)}
                      <div className="text-sm text-gray-500 mt-1">
                        {(contract.coverageAmount || 0).toLocaleString()} XOF
                      </div>
                    </div>
                  </div>
                  <div className="mt-2 flex items-center justify-between text-sm text-gray-500">
                    <div className="flex items-center">
                      <Package className="w-4 h-4 mr-1" />
                      {contract.product?.name}
                    </div>
                    <div className="flex items-center">
                      <Calendar className="w-4 h-4 mr-1" />
                      {new Date(contract.effectiveDate).toLocaleDateString('fr-FR')}
                    </div>
                  </div>
                </div>
              ))
            )}
          </div>
        </div>

        {/* Détails du contrat */}
        <div className="bg-white rounded-lg shadow-md">
          <div className="p-4 border-b border-gray-200">
            <h3 className="text-lg font-semibold text-gray-900">
              {selectedContract ? 'Détails du Contrat' : 'Sélectionnez un contrat'}
            </h3>
          </div>
          <div className="p-6">
            {selectedContract ? (
              <div className="space-y-6">
                {/* Informations générales */}
                <div>
                  <h4 className="font-medium text-gray-900 mb-3">Informations Générales</h4>
                  <div className="grid grid-cols-2 gap-4 text-sm">
                    <div>
                      <span className="text-gray-500">Numéro de police:</span>
                      <p className="font-medium">{selectedContract.policyNumber}</p>
                    </div>
                    <div>
                      <span className="text-gray-500">Statut:</span>
                      <div className="flex items-center space-x-1">
                        {getStatusIcon(selectedContract.contractStatus)}
                        <span className="font-medium">{getStatusLabel(selectedContract.contractStatus)}</span>
                      </div>
                    </div>
                    <div>
                      <span className="text-gray-500">Client:</span>
                      <p className="font-medium">
                        {selectedContract.customer?.firstName} {selectedContract.customer?.lastName}
                      </p>
                    </div>
                    <div>
                      <span className="text-gray-500">Produit:</span>
                      <p className="font-medium">{selectedContract.product?.name}</p>
                    </div>
                    <div>
                      <span className="text-gray-500">Couverture:</span>
                      <p className="font-medium">{(selectedContract.coverageAmount || 0).toLocaleString()} XOF</p>
                    </div>
                    <div>
                      <span className="text-gray-500">Prime:</span>
                      <p className="font-medium">
                        {(selectedContract.premiumAmount || 0).toLocaleString()} XOF/
                        {selectedContract.premiumFrequency === 'monthly' ? 'mois' :
                         selectedContract.premiumFrequency === 'quarterly' ? 'trimestre' :
                         selectedContract.premiumFrequency === 'semi-annual' ? 'semestre' : 'an'}
                      </p>
                    </div>
                  </div>
                </div>

                {/* Dates importantes */}
                <div>
                  <h4 className="font-medium text-gray-900 mb-3">Dates Importantes</h4>
                  <div className="grid grid-cols-2 gap-4 text-sm">
                    <div>
                      <span className="text-gray-500">Date d'émission:</span>
                      <p className="font-medium">
                        {new Date(selectedContract.issueDate).toLocaleDateString('fr-FR')}
                      </p>
                    </div>
                    <div>
                      <span className="text-gray-500">Date d'effet:</span>
                      <p className="font-medium">
                        {new Date(selectedContract.effectiveDate).toLocaleDateString('fr-FR')}
                      </p>
                    </div>
                    {selectedContract.expiryDate && (
                      <div>
                        <span className="text-gray-500">Date d'expiration:</span>
                        <p className="font-medium">
                          {new Date(selectedContract.expiryDate).toLocaleDateString('fr-FR')}
                        </p>
                      </div>
                    )}
                    {selectedContract.nextRenewalDate && (
                      <div>
                        <span className="text-gray-500">Prochain renouvellement:</span>
                        <p className="font-medium">
                          {new Date(selectedContract.nextRenewalDate).toLocaleDateString('fr-FR')}
                        </p>
                      </div>
                    )}
                  </div>
                </div>

                {/* Actions */}
                <div className="flex space-x-3">
                  <button
                    onClick={() => setShowDetailsModal(true)}
                    className="flex-1 bg-blue-600 text-white py-2 px-4 rounded-lg hover:bg-blue-700 transition-colors flex items-center justify-center space-x-2"
                  >
                    <Eye className="w-4 h-4" />
                    <span>Voir Plus</span>
                  </button>
                  <button className="flex-1 bg-gray-600 text-white py-2 px-4 rounded-lg hover:bg-gray-700 transition-colors flex items-center justify-center space-x-2">
                    <Edit className="w-4 h-4" />
                    <span>Modifier</span>
                  </button>
                </div>
              </div>
            ) : (
              <div className="text-center text-gray-500 py-8">
                <FileText className="w-12 h-12 mx-auto mb-4 text-gray-300" />
                <p>Cliquez sur un contrat pour voir ses détails</p>
              </div>
            )}
          </div>
        </div>
      </div>

      {/* Modal de détails du contrat */}
      <ContractDetailsModal
        isOpen={showDetailsModal}
        onClose={() => setShowDetailsModal(false)}
        contract={selectedContract}
      />

      {/* Modal de création de contrat */}
      <CreateContractModal
        isOpen={showCreateModal}
        onClose={() => setShowCreateModal(false)}
        onContractCreated={() => {
          loadContracts(); // Recharger la liste des contrats
        }}
      />
    </div>
  );
};
