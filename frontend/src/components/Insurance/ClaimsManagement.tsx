import React, { useState, useEffect } from 'react';
import {
  AlertTriangle,
  Plus,
  Eye,
  Edit,
  CheckCircle,
  XCircle,
  Clock,
  FileText,
  User,
  Shield,
  Calendar,
  Euro,
  Search,
  Filter
} from 'lucide-react';
import { insuranceApi } from '../../lib/insurance-api';
import CreateClaimModal from './CreateClaimModal';

interface Claim {
  id: string;
  claim_number: string;
  customer_id: string;
  customer_name: string;
  contract_id: string;
  policy_number: string;
  claim_type: string;
  claim_status: string;
  claim_amount: number;
  incident_date: string;
  report_date: string;
  description: string;
  approval_amount?: number;
  rejection_reason?: string;
  payment_date?: string;
  assigned_adjuster_id?: string;
  investigation_notes?: string;
}

interface ClaimDetails extends Claim {
  customer: {
    id: string;
    name: string;
    email: string;
    phone: string;
  };
  contract: {
    id: string;
    policy_number: string;
    coverage_amount: number;
  };
  product: {
    id: string;
    name: string;
    product_type: string;
  };
  documents: Array<{
    id: string;
    document_type: string;
    document_name: string;
    upload_date: string;
    is_verified: boolean;
  }>;
}

const ClaimsManagement: React.FC = () => {
  const [claims, setClaims] = useState<Claim[]>([]);
  const [selectedClaim, setSelectedClaim] = useState<Claim | null>(null);
  const [claimDetails, setClaimDetails] = useState<ClaimDetails | null>(null);
  const [loading, setLoading] = useState(false);
  const [statusFilter, setStatusFilter] = useState<string>('all');
  const [searchQuery, setSearchQuery] = useState('');
  const [showCreateModal, setShowCreateModal] = useState(false);

  useEffect(() => {
    loadClaims();
  }, [statusFilter]);

  const loadClaims = async () => {
    setLoading(true);
    try {
      const filters = statusFilter !== 'all' ? { statut: statusFilter } : {};
      const response = await insuranceApi.getClaims(filters);
      
      if (response.success && response.data) {
        setClaims(response.data);
      } else {
        console.error('Erreur lors du chargement des réclamations:', response.error);
        setClaims([]);
      }
    } catch (error) {
      console.error('Erreur lors du chargement des réclamations:', error);
      setClaims([]);
    } finally {
      setLoading(false);
    }
  };

  const handleViewClaim = async (claim: Claim) => {
    setSelectedClaim(claim);
    setLoading(true);
    
    try {
      const response = await insuranceApi.getClaimByNumber(claim.claim_number);
      
      if (response.success && response.data) {
        setClaimDetails(response.data);
      } else {
        console.error('Erreur lors du chargement des détails:', response.error);
        setClaimDetails(null);
      }
    } catch (error) {
      console.error('Erreur lors du chargement des détails:', error);
      setClaimDetails(null);
    } finally {
      setLoading(false);
    }
  };

  const handleUpdateStatus = async (newStatus: string, notes?: string, approvalAmount?: number, rejectionReason?: string) => {
    if (!selectedClaim) return;
    
    try {
      const response = await insuranceApi.updateClaimStatus(selectedClaim.id, {
        new_status: newStatus,
        notes,
        approval_amount: approvalAmount,
        rejection_reason: rejectionReason
      });
      
      if (response.success) {
        // Recharger les données
        await loadClaims();
        if (selectedClaim) {
          await handleViewClaim(selectedClaim);
        }
      } else {
        console.error('Erreur lors de la mise à jour:', response.error);
      }
    } catch (error) {
      console.error('Erreur lors de la mise à jour:', error);
    }
  };

  const getStatusBadge = (status: string) => {
    switch (status) {
      case 'submitted':
        return <span className="px-2 py-1 rounded-full text-xs font-medium bg-blue-100 text-blue-800">Soumise</span>;
      case 'investigating':
        return <span className="px-2 py-1 rounded-full text-xs font-medium bg-yellow-100 text-yellow-800">En enquête</span>;
      case 'approved':
        return <span className="px-2 py-1 rounded-full text-xs font-medium bg-green-100 text-green-800">Approuvée</span>;
      case 'rejected':
        return <span className="px-2 py-1 rounded-full text-xs font-medium bg-red-100 text-red-800">Rejetée</span>;
      case 'paid':
        return <span className="px-2 py-1 rounded-full text-xs font-medium bg-purple-100 text-purple-800">Payée</span>;
      case 'closed':
        return <span className="px-2 py-1 rounded-full text-xs font-medium bg-gray-100 text-gray-800">Fermée</span>;
      default:
        return <span className="px-2 py-1 rounded-full text-xs font-medium bg-gray-100 text-gray-800">{status}</span>;
    }
  };

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'submitted':
        return <FileText className="w-4 h-4 text-blue-600" />;
      case 'investigating':
        return <Clock className="w-4 h-4 text-yellow-600" />;
      case 'approved':
        return <CheckCircle className="w-4 h-4 text-green-600" />;
      case 'rejected':
        return <XCircle className="w-4 h-4 text-red-600" />;
      case 'paid':
        return <Euro className="w-4 h-4 text-purple-600" />;
      case 'closed':
        return <XCircle className="w-4 h-4 text-gray-600" />;
      default:
        return <FileText className="w-4 h-4 text-gray-600" />;
    }
  };

  const getClaimTypeLabel = (type: string) => {
    switch (type) {
      case 'death': return 'Décès';
      case 'disability': return 'Invalidité';
      case 'health': return 'Santé';
      case 'accident': return 'Accident';
      case 'theft': return 'Vol';
      case 'damage': return 'Dommages';
      default: return type;
    }
  };

  const statusOptions = [
    { value: 'all', label: 'Toutes les réclamations' },
    { value: 'submitted', label: 'Soumises' },
    { value: 'investigating', label: 'En enquête' },
    { value: 'approved', label: 'Approuvées' },
    { value: 'rejected', label: 'Rejetées' },
    { value: 'paid', label: 'Payées' },
    { value: 'closed', label: 'Fermées' }
  ];

  const filteredClaims = claims.filter(claim =>
    claim.claim_number.toLowerCase().includes(searchQuery.toLowerCase()) ||
    claim.customer_name.toLowerCase().includes(searchQuery.toLowerCase()) ||
    claim.policy_number.toLowerCase().includes(searchQuery.toLowerCase())
  );

  return (
    <div className="space-y-6">
      {/* En-tête et filtres */}
      <div className="bg-white rounded-lg shadow-md p-6">
        <div className="flex justify-between items-center mb-4">
          <h2 className="text-xl font-semibold text-gray-900">Gestion des Réclamations</h2>
          <button
            onClick={() => setShowCreateModal(true)}
            className="bg-blue-600 text-white px-4 py-2 rounded-lg hover:bg-blue-700 transition-colors flex items-center space-x-2"
          >
            <Plus className="w-4 h-4" />
            <span>Nouvelle Réclamation</span>
          </button>
        </div>
        
        <div className="flex space-x-4">
          <div className="flex-1 relative">
            <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400 w-4 h-4" />
            <input
              type="text"
              placeholder="Rechercher par numéro, client ou police..."
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
        {/* Liste des réclamations */}
        <div className="bg-white rounded-lg shadow-md">
          <div className="p-6 border-b border-gray-200">
            <h3 className="text-lg font-semibold text-gray-900">
              Réclamations ({filteredClaims.length})
            </h3>
          </div>
          <div className="max-h-96 overflow-y-auto">
            {loading ? (
              <div className="p-6 text-center text-gray-500">
                Chargement des réclamations...
              </div>
            ) : filteredClaims.length === 0 ? (
              <div className="p-6 text-center text-gray-500">
                Aucune réclamation trouvée
              </div>
            ) : (
              filteredClaims.map((claim) => (
                <div
                  key={claim.id}
                  className="p-4 border-b border-gray-100 hover:bg-gray-50 cursor-pointer"
                  onClick={() => handleViewClaim(claim)}
                >
                  <div className="flex items-center justify-between">
                    <div className="flex items-center space-x-3">
                      <div className="w-10 h-10 bg-red-100 rounded-full flex items-center justify-center">
                        <AlertTriangle className="w-5 h-5 text-red-600" />
                      </div>
                      <div>
                        <p className="font-medium text-gray-900">{claim.claim_number}</p>
                        <p className="text-sm text-gray-500">
                          {new Date(claim.report_date).toLocaleDateString('fr-FR')}
                        </p>
                      </div>
                    </div>
                    <div className="flex items-center space-x-2">
                      {getStatusBadge(claim.claim_status)}
                    </div>
                  </div>
                  <div className="mt-2 grid grid-cols-2 gap-2 text-sm text-gray-600">
                    <div className="flex items-center space-x-1">
                      <User className="w-4 h-4" />
                      <span>{claim.customer_name}</span>
                    </div>
                    <div className="flex items-center space-x-1">
                      <Shield className="w-4 h-4" />
                      <span>{claim.policy_number}</span>
                    </div>
                    <div className="flex items-center space-x-1">
                      <FileText className="w-4 h-4" />
                      <span>{getClaimTypeLabel(claim.claim_type)}</span>
                    </div>
                    <div className="flex items-center space-x-1">
                      <Euro className="w-4 h-4" />
                      <span>{claim.claim_amount.toLocaleString()} XOF</span>
                    </div>
                  </div>
                </div>
              ))
            )}
          </div>
        </div>

        {/* Détails de la réclamation sélectionnée */}
        <div className="bg-white rounded-lg shadow-md">
          <div className="p-6 border-b border-gray-200">
            <h3 className="text-lg font-semibold text-gray-900">
              {selectedClaim ? 'Détails de la Réclamation' : 'Sélectionnez une réclamation'}
            </h3>
          </div>
          <div className="p-6">
            {selectedClaim && claimDetails ? (
              <div className="space-y-6">
                {/* Informations générales */}
                <div>
                  <h4 className="font-medium text-gray-900 mb-3">Informations Générales</h4>
                  <div className="grid grid-cols-2 gap-4 text-sm">
                    <div>
                      <span className="text-gray-500">Numéro:</span>
                      <p className="font-medium">{claimDetails.claim_number}</p>
                    </div>
                    <div>
                      <span className="text-gray-500">Statut:</span>
                      <div className="flex items-center space-x-1">
                        {getStatusIcon(claimDetails.claim_status)}
                        <span className="font-medium">{getStatusBadge(claimDetails.claim_status)}</span>
                      </div>
                    </div>
                    <div>
                      <span className="text-gray-500">Type:</span>
                      <p className="font-medium">{getClaimTypeLabel(claimDetails.claim_type)}</p>
                    </div>
                    <div>
                      <span className="text-gray-500">Montant réclamé:</span>
                      <p className="font-medium">{claimDetails.claim_amount.toLocaleString()} XOF</p>
                    </div>
                    <div>
                      <span className="text-gray-500">Date incident:</span>
                      <p className="font-medium">{new Date(claimDetails.incident_date).toLocaleDateString('fr-FR')}</p>
                    </div>
                    <div>
                      <span className="text-gray-500">Date déclaration:</span>
                      <p className="font-medium">{new Date(claimDetails.report_date).toLocaleDateString('fr-FR')}</p>
                    </div>
                  </div>
                </div>

                {/* Description */}
                <div>
                  <h4 className="font-medium text-gray-900 mb-3">Description</h4>
                  <p className="text-sm text-gray-600 bg-gray-50 p-3 rounded-lg">
                    {claimDetails.description}
                  </p>
                </div>

                {/* Client et contrat */}
                <div>
                  <h4 className="font-medium text-gray-900 mb-3">Client et Contrat</h4>
                  <div className="grid grid-cols-2 gap-4 text-sm">
                    <div>
                      <span className="text-gray-500">Client:</span>
                      <p className="font-medium">{claimDetails.customer.name}</p>
                      <p className="text-xs text-gray-500">{claimDetails.customer.email}</p>
                    </div>
                    <div>
                      <span className="text-gray-500">Police:</span>
                      <p className="font-medium">{claimDetails.contract.policy_number}</p>
                      <p className="text-xs text-gray-500">
                        Couverture: {claimDetails.contract.coverage_amount.toLocaleString()} XOF
                      </p>
                    </div>
                  </div>
                </div>

                {/* Documents */}
                {claimDetails.documents && claimDetails.documents.length > 0 && (
                  <div>
                    <h4 className="font-medium text-gray-900 mb-3">Documents</h4>
                    <div className="space-y-2">
                      {claimDetails.documents.map((doc) => (
                        <div key={doc.id} className="flex items-center justify-between p-2 bg-gray-50 rounded">
                          <div>
                            <p className="font-medium text-sm">{doc.document_name}</p>
                            <p className="text-xs text-gray-500">
                              {doc.document_type} - {new Date(doc.upload_date).toLocaleDateString('fr-FR')}
                            </p>
                          </div>
                          {doc.is_verified ? (
                            <CheckCircle className="w-4 h-4 text-green-600" />
                          ) : (
                            <Clock className="w-4 h-4 text-yellow-600" />
                          )}
                        </div>
                      ))}
                    </div>
                  </div>
                )}

                {/* Actions */}
                <div className="flex space-x-3">
                  {claimDetails.claim_status === 'submitted' && (
                    <button
                      onClick={() => handleUpdateStatus('investigating', 'Enquête démarrée')}
                      className="flex-1 bg-yellow-600 text-white py-2 px-4 rounded-lg hover:bg-yellow-700 transition-colors"
                    >
                      Démarrer Enquête
                    </button>
                  )}
                  {claimDetails.claim_status === 'investigating' && (
                    <>
                      <button
                        onClick={() => handleUpdateStatus('approved', 'Réclamation approuvée', claimDetails.claim_amount)}
                        className="flex-1 bg-green-600 text-white py-2 px-4 rounded-lg hover:bg-green-700 transition-colors"
                      >
                        Approuver
                      </button>
                      <button
                        onClick={() => handleUpdateStatus('rejected', 'Réclamation rejetée', undefined, 'Preuves insuffisantes')}
                        className="flex-1 bg-red-600 text-white py-2 px-4 rounded-lg hover:bg-red-700 transition-colors"
                      >
                        Rejeter
                      </button>
                    </>
                  )}
                  {claimDetails.claim_status === 'approved' && (
                    <button
                      onClick={() => handleUpdateStatus('paid', 'Paiement effectué')}
                      className="flex-1 bg-purple-600 text-white py-2 px-4 rounded-lg hover:bg-purple-700 transition-colors"
                    >
                      Marquer Payée
                    </button>
                  )}
                </div>
              </div>
            ) : (
              <div className="text-center text-gray-500 py-8">
                <AlertTriangle className="w-12 h-12 mx-auto mb-4 text-gray-300" />
                <p>Cliquez sur une réclamation pour voir ses détails</p>
              </div>
            )}
          </div>
        </div>
      </div>

      {/* Modal de création de réclamation */}
      <CreateClaimModal
        isOpen={showCreateModal}
        onClose={() => setShowCreateModal(false)}
        onClaimCreated={loadClaims}
      />
    </div>
  );
};

export default ClaimsManagement;
