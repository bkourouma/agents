import React, { useState, useEffect } from 'react';
import {
  Search,
  Plus,
  Eye,
  Edit,
  Phone,
  Mail,
  MapPin,
  User,
  Shield,
  AlertCircle,
  CheckCircle,
  Clock,
  Trash2,
  X,
  Save
} from 'lucide-react';
import { insuranceApi } from '../../lib/insurance-api';
import type { Customer, CustomerSummary } from '../../lib/insurance-api';

// Les interfaces sont maintenant importées de insurance-api.ts

const CustomerManagement: React.FC = () => {
  const [customers, setCustomers] = useState<Customer[]>([]);
  const [searchQuery, setSearchQuery] = useState('');
  const [selectedCustomer, setSelectedCustomer] = useState<Customer | null>(null);
  const [customerSummary, setCustomerSummary] = useState<CustomerSummary | null>(null);
  const [loading, setLoading] = useState(false);
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [showEditModal, setShowEditModal] = useState(false);
  const [createLoading, setCreateLoading] = useState(false);
  const [editLoading, setEditLoading] = useState(false);
  const [deleteLoading, setDeleteLoading] = useState<string | null>(null);

  // Form state for creating new customer
  const [newCustomer, setNewCustomer] = useState({
    customerNumber: '',
    firstName: '',
    lastName: '',
    email: '',
    phone: '',
    dateOfBirth: '',
    city: '',
    customerType: 'individual' as 'individual' | 'business',
    riskProfile: 'medium' as 'low' | 'medium' | 'high',
    kycStatus: 'pending' as 'pending' | 'verified' | 'rejected'
  });

  // Form state for editing existing customer
  const [editCustomer, setEditCustomer] = useState({
    id: '',
    customerNumber: '',
    firstName: '',
    lastName: '',
    email: '',
    phone: '',
    dateOfBirth: '',
    city: '',
    customerType: 'individual' as 'individual' | 'business',
    riskProfile: 'medium' as 'low' | 'medium' | 'high',
    kycStatus: 'pending' as 'pending' | 'verified' | 'rejected'
  });

  // Charger les données depuis l'API
  useEffect(() => {
    const loadInitialData = async () => {
      try {
        // Charger les clients depuis l'API
        const response = await insuranceApi.searchCustomers('', 50);

        if (response.success && response.data) {
          setCustomers(response.data);
        } else {
          console.error('Erreur lors du chargement des clients:', response.error);
          setCustomers([]);
        }
      } catch (error) {
        console.error('Erreur lors du chargement des données:', error);
        setCustomers([]);
      }
    };

    loadInitialData();
  }, []);

  const handleSearch = async () => {
    if (!searchQuery.trim()) return;

    setLoading(true);
    try {
      const response = await insuranceApi.searchCustomers(searchQuery);

      if (response.success && response.data) {
        setCustomers(response.data);
      } else {
        console.error('Erreur lors de la recherche:', response.error);
        setCustomers([]);
      }
    } catch (error) {
      console.error('Erreur lors de la recherche:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleCreateCustomer = async () => {
    if (!newCustomer.firstName || !newCustomer.lastName || !newCustomer.email) {
      alert('Veuillez remplir tous les champs obligatoires');
      return;
    }

    setCreateLoading(true);
    try {
      // Convert camelCase to snake_case for backend
      const customerData = {
        customer_number: newCustomer.customerNumber || `CLI${Date.now()}`,
        first_name: newCustomer.firstName,
        last_name: newCustomer.lastName,
        email: newCustomer.email,
        phone: newCustomer.phone || null,
        date_of_birth: newCustomer.dateOfBirth || null,
        city: newCustomer.city || null,
        customer_type: newCustomer.customerType,
        risk_profile: newCustomer.riskProfile,
        kyc_status: newCustomer.kycStatus
      };

      console.log('Creating customer with data:', customerData);
      const response = await insuranceApi.createCustomer(customerData);
      console.log('Create customer response:', response);

      if (response.success && response.data) {
        // Add new customer to the list
        setCustomers(prev => [response.data!, ...prev]);

        // Reset form and close modal
        setNewCustomer({
          customerNumber: '',
          firstName: '',
          lastName: '',
          email: '',
          phone: '',
          dateOfBirth: '',
          city: '',
          customerType: 'individual',
          riskProfile: 'medium',
          kycStatus: 'pending'
        });
        setShowCreateModal(false);

        alert('Client créé avec succès!');
      } else {
        console.error('Erreur lors de la création:', response.error);
        alert('Erreur lors de la création du client');
      }
    } catch (error) {
      console.error('Erreur lors de la création:', error);
      alert('Erreur lors de la création du client');
    } finally {
      setCreateLoading(false);
    }
  };

  const handleEditCustomer = (customer: Customer) => {
    setEditCustomer({
      id: customer.id,
      customerNumber: customer.customer_number,
      firstName: customer.first_name,
      lastName: customer.last_name,
      email: customer.email,
      phone: customer.phone || '',
      dateOfBirth: customer.date_of_birth || '',
      city: customer.city || '',
      customerType: customer.customer_type,
      riskProfile: customer.risk_profile,
      kycStatus: customer.kyc_status
    });
    setShowEditModal(true);
  };

  const handleUpdateCustomer = async () => {
    if (!editCustomer.firstName || !editCustomer.lastName || !editCustomer.email) {
      alert('Veuillez remplir tous les champs obligatoires');
      return;
    }

    setEditLoading(true);
    try {
      // Convert camelCase to snake_case for backend
      const customerData = {
        customer_number: editCustomer.customerNumber,
        first_name: editCustomer.firstName,
        last_name: editCustomer.lastName,
        email: editCustomer.email,
        phone: editCustomer.phone || null,
        date_of_birth: editCustomer.dateOfBirth || null,
        city: editCustomer.city || null,
        customer_type: editCustomer.customerType,
        risk_profile: editCustomer.riskProfile,
        kyc_status: editCustomer.kycStatus
      };

      const response = await insuranceApi.updateCustomer(editCustomer.id, customerData);

      if (response.success && response.data) {
        // Update customer in the list
        setCustomers(prev => prev.map(c =>
          c.id === editCustomer.id ? response.data! : c
        ));

        // Update selected customer if it's the one being edited
        if (selectedCustomer?.id === editCustomer.id) {
          setSelectedCustomer(response.data);
        }

        setShowEditModal(false);
        alert('Client modifié avec succès!');
      } else {
        console.error('Erreur lors de la modification:', response.error);
        alert('Erreur lors de la modification du client');
      }
    } catch (error) {
      console.error('Erreur lors de la modification:', error);
      alert('Erreur lors de la modification du client');
    } finally {
      setEditLoading(false);
    }
  };

  const handleDeleteCustomer = async (customerId: string) => {
    if (!confirm('Êtes-vous sûr de vouloir supprimer ce client ?')) {
      return;
    }

    setDeleteLoading(customerId);
    try {
      const response = await insuranceApi.deleteCustomer(customerId);

      if (response.success) {
        // Remove customer from the list
        setCustomers(prev => prev.filter(c => c.id !== customerId));

        // Clear selected customer if it was deleted
        if (selectedCustomer?.id === customerId) {
          setSelectedCustomer(null);
          setCustomerSummary(null);
        }

        alert('Client supprimé avec succès!');
      } else {
        console.error('Erreur lors de la suppression:', response.error);
        alert('Erreur lors de la suppression du client');
      }
    } catch (error) {
      console.error('Erreur lors de la suppression:', error);
      alert('Erreur lors de la suppression du client');
    } finally {
      setDeleteLoading(null);
    }
  };

  const handleViewCustomer = async (customer: Customer) => {
    setSelectedCustomer(customer);
    setLoading(true);

    try {
      const response = await insuranceApi.getCustomerSummary(customer.id);

      if (response.success && response.data) {
        setCustomerSummary(response.data);
      } else {
        console.error('Erreur lors du chargement du résumé:', response.error);
        setCustomerSummary(null);
      }
    } catch (error) {
      console.error('Erreur lors du chargement du résumé:', error);
    } finally {
      setLoading(false);
    }
  };

  const getRiskProfileColor = (profile: string) => {
    switch (profile) {
      case 'low': return 'text-green-600 bg-green-100';
      case 'medium': return 'text-yellow-600 bg-yellow-100';
      case 'high': return 'text-red-600 bg-red-100';
      default: return 'text-gray-600 bg-gray-100';
    }
  };

  const getKycStatusIcon = (status: string) => {
    switch (status) {
      case 'verified': return <CheckCircle className="w-4 h-4 text-green-600" />;
      case 'pending': return <Clock className="w-4 h-4 text-yellow-600" />;
      case 'rejected': return <AlertCircle className="w-4 h-4 text-red-600" />;
      default: return <Clock className="w-4 h-4 text-gray-600" />;
    }
  };

  return (
    <div className="space-y-6">
      {/* En-tête et recherche */}
      <div className="bg-white rounded-lg shadow-md p-6">
        <div className="flex justify-between items-center mb-4">
          <h2 className="text-xl font-semibold text-gray-900">Gestion des Clients</h2>
          <button
            onClick={() => setShowCreateModal(true)}
            className="bg-blue-600 text-white px-4 py-2 rounded-lg hover:bg-blue-700 transition-colors flex items-center space-x-2"
          >
            <Plus className="w-4 h-4" />
            <span>Nouveau Client</span>
          </button>
        </div>
        
        <div className="flex space-x-4">
          <div className="flex-1 relative">
            <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400 w-4 h-4" />
            <input
              type="text"
              placeholder="Rechercher par nom, email, téléphone ou numéro client..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              onKeyPress={(e) => e.key === 'Enter' && handleSearch()}
              className="w-full pl-10 pr-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
            />
          </div>
          <button
            onClick={handleSearch}
            disabled={loading}
            className="bg-gray-600 text-white px-6 py-2 rounded-lg hover:bg-gray-700 transition-colors disabled:opacity-50"
          >
            {loading ? 'Recherche...' : 'Rechercher'}
          </button>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Liste des clients */}
        <div className="bg-white rounded-lg shadow-md">
          <div className="p-6 border-b border-gray-200">
            <h3 className="text-lg font-semibold text-gray-900">
              Clients ({customers.length})
            </h3>
          </div>
          <div className="max-h-96 overflow-y-auto">
            {customers.map((customer) => (
              <div
                key={customer.id}
                className="p-4 border-b border-gray-100 hover:bg-gray-50"
              >
                <div className="flex items-center justify-between">
                  <div
                    className="flex items-center space-x-3 flex-1 cursor-pointer"
                    onClick={() => handleViewCustomer(customer)}
                  >
                    <div className="w-10 h-10 bg-blue-100 rounded-full flex items-center justify-center">
                      <User className="w-5 h-5 text-blue-600" />
                    </div>
                    <div>
                      <p className="font-medium text-gray-900">
                        {customer.first_name} {customer.last_name}
                      </p>
                      <p className="text-sm text-gray-500">{customer.customer_number}</p>
                    </div>
                  </div>
                  <div className="flex items-center space-x-2">
                    {getKycStatusIcon(customer.kyc_status)}
                    <span className={`px-2 py-1 rounded-full text-xs font-medium ${getRiskProfileColor(customer.risk_profile)}`}>
                      {customer.risk_profile === 'low' ? 'Faible' :
                       customer.risk_profile === 'medium' ? 'Moyen' : 'Élevé'}
                    </span>
                    <button
                      onClick={(e) => {
                        e.stopPropagation();
                        handleEditCustomer(customer);
                      }}
                      className="p-1 text-blue-600 hover:text-blue-800 hover:bg-blue-50 rounded transition-colors"
                      title="Modifier le client"
                    >
                      <Edit className="w-4 h-4" />
                    </button>
                    <button
                      onClick={(e) => {
                        e.stopPropagation();
                        handleDeleteCustomer(customer.id);
                      }}
                      disabled={deleteLoading === customer.id}
                      className="p-1 text-red-600 hover:text-red-800 hover:bg-red-50 rounded transition-colors disabled:opacity-50"
                      title="Supprimer le client"
                    >
                      {deleteLoading === customer.id ? (
                        <div className="w-4 h-4 border-2 border-red-600 border-t-transparent rounded-full animate-spin"></div>
                      ) : (
                        <Trash2 className="w-4 h-4" />
                      )}
                    </button>
                  </div>
                </div>
                <div className="mt-2 flex items-center space-x-4 text-sm text-gray-600">
                  <div className="flex items-center space-x-1">
                    <Mail className="w-4 h-4" />
                    <span>{customer.email}</span>
                  </div>
                  <div className="flex items-center space-x-1">
                    <Shield className="w-4 h-4" />
                    <span>{customer.activeContracts || 0} contrat(s)</span>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Détails du client sélectionné */}
        <div className="bg-white rounded-lg shadow-md">
          <div className="p-6 border-b border-gray-200">
            <h3 className="text-lg font-semibold text-gray-900">
              {selectedCustomer ? 'Détails du Client' : 'Sélectionnez un client'}
            </h3>
          </div>
          <div className="p-6">
            {selectedCustomer ? (
              <div className="space-y-6">
                {/* Informations personnelles */}
                <div>
                  <h4 className="font-medium text-gray-900 mb-3">Informations Personnelles</h4>
                  <div className="grid grid-cols-2 gap-4 text-sm">
                    <div>
                      <span className="text-gray-500">Nom complet:</span>
                      <p className="font-medium">{selectedCustomer.first_name} {selectedCustomer.last_name}</p>
                    </div>
                    <div>
                      <span className="text-gray-500">Date de naissance:</span>
                      <p className="font-medium">{selectedCustomer.date_of_birth ? new Date(selectedCustomer.date_of_birth).toLocaleDateString('fr-FR') : 'Non renseigné'}</p>
                    </div>
                    <div>
                      <span className="text-gray-500">Email:</span>
                      <p className="font-medium">{selectedCustomer.email}</p>
                    </div>
                    <div>
                      <span className="text-gray-500">Téléphone:</span>
                      <p className="font-medium">{selectedCustomer.phone || 'Non renseigné'}</p>
                    </div>
                    <div>
                      <span className="text-gray-500">Ville:</span>
                      <p className="font-medium">{selectedCustomer.city || 'Non renseigné'}</p>
                    </div>
                    <div>
                      <span className="text-gray-500">Statut KYC:</span>
                      <div className="flex items-center space-x-1">
                        {getKycStatusIcon(selectedCustomer.kyc_status)}
                        <span className="font-medium">
                          {selectedCustomer.kyc_status === 'verified' ? 'Vérifié' :
                           selectedCustomer.kyc_status === 'pending' ? 'En attente' : 'Rejeté'}
                        </span>
                      </div>
                    </div>
                  </div>
                </div>

                {/* Résumé financier */}
                {customerSummary && (
                  <div>
                    <h4 className="font-medium text-gray-900 mb-3">Résumé Financier</h4>
                    <div className="grid grid-cols-2 gap-4">
                      <div className="bg-blue-50 p-3 rounded-lg">
                        <p className="text-sm text-blue-600">Couverture Totale</p>
                        <p className="text-lg font-bold text-blue-900">
                          {customerSummary.totalCoverageAmount.toLocaleString()} €
                        </p>
                      </div>
                      <div className="bg-green-50 p-3 rounded-lg">
                        <p className="text-sm text-green-600">Prime Annuelle</p>
                        <p className="text-lg font-bold text-green-900">
                          {customerSummary.totalPremiumAmount.toLocaleString()} €
                        </p>
                      </div>
                      <div className="bg-purple-50 p-3 rounded-lg">
                        <p className="text-sm text-purple-600">Contrats Actifs</p>
                        <p className="text-lg font-bold text-purple-900">
                          {customerSummary.activeContracts}
                        </p>
                      </div>
                      <div className={`p-3 rounded-lg ${
                        customerSummary.paymentStatus === 'À jour' ? 'bg-green-50' : 'bg-red-50'
                      }`}>
                        <p className={`text-sm ${
                          customerSummary.paymentStatus === 'À jour' ? 'text-green-600' : 'text-red-600'
                        }`}>
                          Statut Paiement
                        </p>
                        <p className={`text-lg font-bold ${
                          customerSummary.paymentStatus === 'À jour' ? 'text-green-900' : 'text-red-900'
                        }`}>
                          {customerSummary.paymentStatus}
                        </p>
                      </div>
                    </div>
                  </div>
                )}

                {/* Actions */}
                <div className="flex space-x-3">
                  <button className="flex-1 bg-blue-600 text-white py-2 px-4 rounded-lg hover:bg-blue-700 transition-colors flex items-center justify-center space-x-2">
                    <Eye className="w-4 h-4" />
                    <span>Voir Détails</span>
                  </button>
                  <button
                    onClick={() => handleEditCustomer(selectedCustomer)}
                    className="flex-1 bg-gray-600 text-white py-2 px-4 rounded-lg hover:bg-gray-700 transition-colors flex items-center justify-center space-x-2"
                  >
                    <Edit className="w-4 h-4" />
                    <span>Modifier</span>
                  </button>
                </div>
              </div>
            ) : (
              <div className="text-center text-gray-500 py-8">
                <User className="w-12 h-12 mx-auto mb-4 text-gray-300" />
                <p>Cliquez sur un client pour voir ses détails</p>
              </div>
            )}
          </div>
        </div>
      </div>

      {/* Modal de création de client */}
      {showCreateModal && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg shadow-xl max-w-2xl w-full mx-4 max-h-[90vh] overflow-y-auto">
            <div className="p-6 border-b border-gray-200">
              <div className="flex justify-between items-center">
                <h3 className="text-lg font-semibold text-gray-900">Nouveau Client</h3>
                <button
                  onClick={() => setShowCreateModal(false)}
                  className="text-gray-400 hover:text-gray-600"
                >
                  <X className="w-6 h-6" />
                </button>
              </div>
            </div>

            <div className="p-6 space-y-4">
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Prénom *
                  </label>
                  <input
                    type="text"
                    value={newCustomer.firstName}
                    onChange={(e) => setNewCustomer(prev => ({ ...prev, firstName: e.target.value }))}
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                    placeholder="Prénom du client"
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Nom *
                  </label>
                  <input
                    type="text"
                    value={newCustomer.lastName}
                    onChange={(e) => setNewCustomer(prev => ({ ...prev, lastName: e.target.value }))}
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                    placeholder="Nom du client"
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Email *
                  </label>
                  <input
                    type="email"
                    value={newCustomer.email}
                    onChange={(e) => setNewCustomer(prev => ({ ...prev, email: e.target.value }))}
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                    placeholder="email@exemple.com"
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Téléphone
                  </label>
                  <input
                    type="tel"
                    value={newCustomer.phone}
                    onChange={(e) => setNewCustomer(prev => ({ ...prev, phone: e.target.value }))}
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                    placeholder="+33 1 23 45 67 89"
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Date de naissance
                  </label>
                  <input
                    type="date"
                    value={newCustomer.dateOfBirth}
                    onChange={(e) => setNewCustomer(prev => ({ ...prev, dateOfBirth: e.target.value }))}
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Ville
                  </label>
                  <input
                    type="text"
                    value={newCustomer.city}
                    onChange={(e) => setNewCustomer(prev => ({ ...prev, city: e.target.value }))}
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                    placeholder="Paris"
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Type de client
                  </label>
                  <select
                    value={newCustomer.customerType}
                    onChange={(e) => setNewCustomer(prev => ({ ...prev, customerType: e.target.value as 'individual' | 'business' }))}
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                  >
                    <option value="individual">Particulier</option>
                    <option value="business">Entreprise</option>
                  </select>
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Profil de risque
                  </label>
                  <select
                    value={newCustomer.riskProfile}
                    onChange={(e) => setNewCustomer(prev => ({ ...prev, riskProfile: e.target.value as 'low' | 'medium' | 'high' }))}
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                  >
                    <option value="low">Faible</option>
                    <option value="medium">Moyen</option>
                    <option value="high">Élevé</option>
                  </select>
                </div>
              </div>
            </div>

            <div className="p-6 border-t border-gray-200 flex justify-end space-x-3">
              <button
                onClick={() => setShowCreateModal(false)}
                className="px-4 py-2 text-gray-700 bg-gray-100 rounded-lg hover:bg-gray-200 transition-colors"
              >
                Annuler
              </button>
              <button
                onClick={handleCreateCustomer}
                disabled={createLoading}
                className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors flex items-center space-x-2 disabled:opacity-50"
              >
                {createLoading ? (
                  <div className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin"></div>
                ) : (
                  <Save className="w-4 h-4" />
                )}
                <span>{createLoading ? 'Création...' : 'Créer le client'}</span>
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Modal de modification de client */}
      {showEditModal && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg shadow-xl max-w-2xl w-full mx-4 max-h-[90vh] overflow-y-auto">
            <div className="p-6 border-b border-gray-200">
              <div className="flex justify-between items-center">
                <h3 className="text-lg font-semibold text-gray-900">Modifier le Client</h3>
                <button
                  onClick={() => setShowEditModal(false)}
                  className="text-gray-400 hover:text-gray-600"
                >
                  <X className="w-6 h-6" />
                </button>
              </div>
            </div>

            <div className="p-6 space-y-4">
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Numéro Client
                  </label>
                  <input
                    type="text"
                    value={editCustomer.customerNumber}
                    onChange={(e) => setEditCustomer(prev => ({ ...prev, customerNumber: e.target.value }))}
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 bg-gray-50"
                    placeholder="Numéro du client"
                    disabled
                  />
                </div>

                <div></div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Prénom *
                  </label>
                  <input
                    type="text"
                    value={editCustomer.firstName}
                    onChange={(e) => setEditCustomer(prev => ({ ...prev, firstName: e.target.value }))}
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                    placeholder="Prénom du client"
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Nom *
                  </label>
                  <input
                    type="text"
                    value={editCustomer.lastName}
                    onChange={(e) => setEditCustomer(prev => ({ ...prev, lastName: e.target.value }))}
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                    placeholder="Nom du client"
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Email *
                  </label>
                  <input
                    type="email"
                    value={editCustomer.email}
                    onChange={(e) => setEditCustomer(prev => ({ ...prev, email: e.target.value }))}
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                    placeholder="email@exemple.com"
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Téléphone
                  </label>
                  <input
                    type="tel"
                    value={editCustomer.phone}
                    onChange={(e) => setEditCustomer(prev => ({ ...prev, phone: e.target.value }))}
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                    placeholder="+33 1 23 45 67 89"
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Date de naissance
                  </label>
                  <input
                    type="date"
                    value={editCustomer.dateOfBirth}
                    onChange={(e) => setEditCustomer(prev => ({ ...prev, dateOfBirth: e.target.value }))}
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Ville
                  </label>
                  <input
                    type="text"
                    value={editCustomer.city}
                    onChange={(e) => setEditCustomer(prev => ({ ...prev, city: e.target.value }))}
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                    placeholder="Paris"
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Type de client
                  </label>
                  <select
                    value={editCustomer.customerType}
                    onChange={(e) => setEditCustomer(prev => ({ ...prev, customerType: e.target.value as 'individual' | 'business' }))}
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                  >
                    <option value="individual">Particulier</option>
                    <option value="business">Entreprise</option>
                  </select>
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Profil de risque
                  </label>
                  <select
                    value={editCustomer.riskProfile}
                    onChange={(e) => setEditCustomer(prev => ({ ...prev, riskProfile: e.target.value as 'low' | 'medium' | 'high' }))}
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                  >
                    <option value="low">Faible</option>
                    <option value="medium">Moyen</option>
                    <option value="high">Élevé</option>
                  </select>
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Statut KYC
                  </label>
                  <select
                    value={editCustomer.kycStatus}
                    onChange={(e) => setEditCustomer(prev => ({ ...prev, kycStatus: e.target.value as 'pending' | 'verified' | 'rejected' }))}
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                  >
                    <option value="pending">En attente</option>
                    <option value="verified">Vérifié</option>
                    <option value="rejected">Rejeté</option>
                  </select>
                </div>
              </div>
            </div>

            <div className="p-6 border-t border-gray-200 flex justify-end space-x-3">
              <button
                onClick={() => setShowEditModal(false)}
                className="px-4 py-2 text-gray-700 bg-gray-100 rounded-lg hover:bg-gray-200 transition-colors"
              >
                Annuler
              </button>
              <button
                onClick={handleUpdateCustomer}
                disabled={editLoading}
                className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors flex items-center space-x-2 disabled:opacity-50"
              >
                {editLoading ? (
                  <div className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin"></div>
                ) : (
                  <Save className="w-4 h-4" />
                )}
                <span>{editLoading ? 'Modification...' : 'Modifier le client'}</span>
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default CustomerManagement;
