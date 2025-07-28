import React, { useState, useEffect } from 'react';
import {
  FileText,
  Plus,
  Calculator,
  User,
  Package,
  Euro,
  Calendar,
  CheckCircle,
  XCircle,
  AlertTriangle,
  Search,
  Download,
  ShoppingCart,
  Mail,
  Send
} from 'lucide-react';
import { insuranceApi } from '../../lib/insurance-api';
import type { Customer, InsuranceProduct } from '../../lib/insurance-api';
import QuoteToOrderModal from './QuoteToOrderModal';

interface Quote {
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
}

interface QuoteRequest {
  customer_id: string;
  product_id: string;
  coverage_amount: number;
  premium_frequency: string;
  additional_features?: string[];
}

const QuotesManagement: React.FC = () => {
  const [customers, setCustomers] = useState<Customer[]>([]);
  const [products, setProducts] = useState<InsuranceProduct[]>([]);
  const [currentQuote, setCurrentQuote] = useState<Quote | null>(null);
  const [loading, setLoading] = useState(false);
  const [showQuoteForm, setShowQuoteForm] = useState(false);
  const [isCreatingOrder, setIsCreatingOrder] = useState(false);
  const [isSendingEmail, setIsSendingEmail] = useState(false);
  const [showOrderModal, setShowOrderModal] = useState(false);
  const [selectedQuoteForOrder, setSelectedQuoteForOrder] = useState<Quote | null>(null);

  // Form state
  const [selectedCustomer, setSelectedCustomer] = useState<string>('');
  const [selectedProduct, setSelectedProduct] = useState<string>('');
  const [coverageAmount, setCoverageAmount] = useState<number>(50000);
  const [premiumFrequency, setPremiumFrequency] = useState<string>('monthly');
  const [additionalFeatures, setAdditionalFeatures] = useState<string[]>([]);

  useEffect(() => {
    loadInitialData();
  }, []);

  const loadInitialData = async () => {
    try {
      // Charger les clients
      const customersResponse = await insuranceApi.searchCustomers('', 50);
      if (customersResponse.success && customersResponse.data) {
        setCustomers(customersResponse.data);
      }

      // Charger les produits
      const productsResponse = await insuranceApi.getProducts();
      if (productsResponse.success && productsResponse.data) {
        setProducts(productsResponse.data);
      }
    } catch (error) {
      console.error('Erreur lors du chargement des données:', error);
    }
  };

  const handleGenerateQuote = async () => {
    if (!selectedCustomer || !selectedProduct || !coverageAmount) {
      alert('Veuillez remplir tous les champs obligatoires');
      return;
    }

    setLoading(true);
    try {
      const quoteRequest: QuoteRequest = {
        customer_id: selectedCustomer,
        product_id: selectedProduct,
        coverage_amount: coverageAmount,
        premium_frequency: premiumFrequency,
        additional_features: additionalFeatures
      };

      const response = await insuranceApi.generateQuote(quoteRequest);
      
      if (response.success && response.data) {
        setCurrentQuote(response.data);
        setShowQuoteForm(false);
      } else {
        console.error('Erreur lors de la génération du devis:', response.error);
        alert('Erreur lors de la génération du devis: ' + response.error);
      }
    } catch (error) {
      console.error('Erreur lors de la génération du devis:', error);
      alert('Erreur lors de la génération du devis');
    } finally {
      setLoading(false);
    }
  };

  const handleCreateOrder = () => {
    if (!currentQuote || !currentQuote.id) {
      alert('Aucun devis sélectionné');
      return;
    }

    // Ouvrir la modal avec le devis sélectionné
    setSelectedQuoteForOrder(currentQuote);
    setShowOrderModal(true);
  };

  const handleOrderCreated = (orderNumber: string) => {
    // Réinitialiser le devis actuel
    setCurrentQuote(null);
    setSelectedQuoteForOrder(null);
    setShowOrderModal(false);
  };

  const handleSendEmail = async () => {
    if (!currentQuote || !currentQuote.id) {
      alert('Aucun devis sélectionné');
      return;
    }

    try {
      setIsSendingEmail(true);
      const response = await insuranceApi.sendQuoteByEmail(currentQuote.id);

      if (response.success) {
        alert('Devis envoyé par email avec succès !');
      } else {
        alert('Erreur lors de l\'envoi de l\'email');
      }
    } catch (error) {
      console.error('Erreur lors de l\'envoi de l\'email:', error);
      alert('Erreur lors de l\'envoi de l\'email');
    } finally {
      setIsSendingEmail(false);
    }
  };

  const resetForm = () => {
    setSelectedCustomer('');
    setSelectedProduct('');
    setCoverageAmount(50000);
    setPremiumFrequency('monthly');
    setAdditionalFeatures([]);
    setCurrentQuote(null);
  };

  const getRiskProfileColor = (profile: string) => {
    switch (profile) {
      case 'low': return 'text-green-600 bg-green-100';
      case 'medium': return 'text-yellow-600 bg-yellow-100';
      case 'high': return 'text-red-600 bg-red-100';
      default: return 'text-gray-600 bg-gray-100';
    }
  };

  const getProductTypeIcon = (type: string) => {
    switch (type) {
      case 'life': return '🛡️';
      case 'health': return '❤️';
      case 'auto': return '🚗';
      case 'home': return '🏠';
      case 'business': return '🏢';
      default: return '📦';
    }
  };

  const getPremiumFrequencyLabel = (frequency: string) => {
    switch (frequency) {
      case 'monthly': return 'Mensuelle';
      case 'quarterly': return 'Trimestrielle';
      case 'semi-annual': return 'Semestrielle';
      case 'annual': return 'Annuelle';
      default: return frequency;
    }
  };

  return (
    <div className="space-y-6">
      {/* En-tête */}
      <div className="bg-white rounded-lg shadow-md p-6">
        <div className="flex justify-between items-center mb-4">
          <h2 className="text-xl font-semibold text-gray-900">Génération de Devis</h2>
          <div className="flex space-x-3">
            <button
              onClick={() => setShowQuoteForm(!showQuoteForm)}
              className="bg-blue-600 text-white px-4 py-2 rounded-lg hover:bg-blue-700 transition-colors flex items-center space-x-2"
            >
              <Calculator className="w-4 h-4" />
              <span>Nouveau Devis</span>
            </button>
            <button
              onClick={resetForm}
              className="bg-gray-600 text-white px-4 py-2 rounded-lg hover:bg-gray-700 transition-colors"
            >
              Réinitialiser
            </button>
          </div>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Formulaire de devis */}
        <div className="bg-white rounded-lg shadow-md">
          <div className="p-6 border-b border-gray-200">
            <h3 className="text-lg font-semibold text-gray-900">
              {showQuoteForm ? 'Paramètres du Devis' : 'Formulaire de Devis'}
            </h3>
          </div>
          <div className="p-6">
            {showQuoteForm || !currentQuote ? (
              <div className="space-y-4">
                {/* Sélection du client */}
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Client *
                  </label>
                  <select
                    value={selectedCustomer}
                    onChange={(e) => setSelectedCustomer(e.target.value)}
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                  >
                    <option value="">Sélectionnez un client</option>
                    {customers.map((customer) => (
                      <option key={customer.id} value={customer.id}>
                        {customer.firstName} {customer.lastName} - {customer.email}
                      </option>
                    ))}
                  </select>
                </div>

                {/* Sélection du produit */}
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Produit *
                  </label>
                  <select
                    value={selectedProduct}
                    onChange={(e) => setSelectedProduct(e.target.value)}
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                  >
                    <option value="">Sélectionnez un produit</option>
                    {products.map((product) => (
                      <option key={product.id} value={product.id}>
                        {getProductTypeIcon(product.productType)} {product.name}
                      </option>
                    ))}
                  </select>
                </div>

                {/* Montant de couverture */}
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Montant de couverture (€) *
                  </label>
                  <input
                    type="number"
                    value={coverageAmount}
                    onChange={(e) => setCoverageAmount(Number(e.target.value))}
                    min="1000"
                    step="1000"
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                  />
                </div>

                {/* Fréquence de prime */}
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Fréquence de paiement
                  </label>
                  <select
                    value={premiumFrequency}
                    onChange={(e) => setPremiumFrequency(e.target.value)}
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                  >
                    <option value="monthly">Mensuelle</option>
                    <option value="quarterly">Trimestrielle</option>
                    <option value="semi-annual">Semestrielle</option>
                    <option value="annual">Annuelle</option>
                  </select>
                </div>

                {/* Bouton de génération */}
                <button
                  onClick={handleGenerateQuote}
                  disabled={loading || !selectedCustomer || !selectedProduct}
                  className="w-full bg-blue-600 text-white py-3 px-4 rounded-lg hover:bg-blue-700 transition-colors disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center space-x-2"
                >
                  {loading ? (
                    <>
                      <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white"></div>
                      <span>Génération...</span>
                    </>
                  ) : (
                    <>
                      <Calculator className="w-4 h-4" />
                      <span>Générer le Devis</span>
                    </>
                  )}
                </button>
              </div>
            ) : (
              <div className="text-center text-gray-500 py-8">
                <FileText className="w-12 h-12 mx-auto mb-4 text-gray-300" />
                <p>Cliquez sur "Nouveau Devis" pour créer un devis</p>
              </div>
            )}
          </div>
        </div>

        {/* Résultat du devis */}
        <div className="bg-white rounded-lg shadow-md">
          <div className="p-6 border-b border-gray-200">
            <div className="flex justify-between items-center">
              <h3 className="text-lg font-semibold text-gray-900">
                {currentQuote ? `Devis ${currentQuote.quote_number}` : 'Résultat du Devis'}
              </h3>
              {currentQuote && (
                <button className="text-blue-600 hover:text-blue-800 flex items-center space-x-1">
                  <Download className="w-4 h-4" />
                  <span>Télécharger</span>
                </button>
              )}
            </div>
          </div>
          <div className="p-6">
            {currentQuote ? (
              currentQuote.eligible ? (
                <div className="space-y-6">
                  {/* Informations client et produit */}
                  <div className="grid grid-cols-2 gap-4">
                    <div>
                      <h4 className="font-medium text-gray-900 mb-2">Client</h4>
                      <div className="text-sm">
                        <p className="font-medium">{currentQuote.customer?.name || 'Client inconnu'}</p>
                        <p className="text-gray-600">{currentQuote.customer?.email || ''}</p>
                        {currentQuote.customer?.age && (
                          <p className="text-gray-600">{currentQuote.customer.age} ans</p>
                        )}
                        {currentQuote.customer?.risk_profile && (
                          <span className={`inline-block px-2 py-1 rounded-full text-xs font-medium mt-1 ${getRiskProfileColor(currentQuote.customer.risk_profile)}`}>
                            Risque {currentQuote.customer.risk_profile === 'low' ? 'faible' :
                                    currentQuote.customer.risk_profile === 'medium' ? 'moyen' : 'élevé'}
                          </span>
                        )}
                      </div>
                    </div>
                    <div>
                      <h4 className="font-medium text-gray-900 mb-2">Produit</h4>
                      <div className="text-sm">
                        <p className="font-medium">
                          {currentQuote.product?.product_type && getProductTypeIcon(currentQuote.product.product_type)} {currentQuote.product?.name || 'Produit inconnu'}
                        </p>
                        <p className="text-gray-600">{currentQuote.product?.description || ''}</p>
                      </div>
                    </div>
                  </div>

                  {/* Détails de couverture */}
                  <div>
                    <h4 className="font-medium text-gray-900 mb-2">Couverture</h4>
                    <div className="bg-blue-50 p-4 rounded-lg">
                      <div className="flex justify-between items-center">
                        <span className="text-blue-800">Montant de couverture:</span>
                        <span className="font-bold text-blue-900">
                          {(currentQuote.coverage_amount || 0).toLocaleString()} XOF
                        </span>
                      </div>
                      <div className="flex justify-between items-center mt-2">
                        <span className="text-blue-800">Fréquence:</span>
                        <span className="font-medium text-blue-900">
                          {getPremiumFrequencyLabel(currentQuote.premium_frequency || 'monthly')}
                        </span>
                      </div>
                    </div>
                  </div>

                  {/* Calcul de la prime */}
                  <div>
                    <h4 className="font-medium text-gray-900 mb-2">Calcul de la Prime</h4>
                    <div className="space-y-2 text-sm">
                      <div className="flex justify-between">
                        <span>Prime de base:</span>
                        <span>{(currentQuote.base_premium || 0).toLocaleString()} XOF</span>
                      </div>
                      <div className="flex justify-between">
                        <span>Prime ajustée (facteurs):</span>
                        <span>{(currentQuote.adjusted_premium || 0).toLocaleString()} XOF</span>
                      </div>
                      {(currentQuote.additional_premium || 0) > 0 && (
                        <div className="flex justify-between">
                          <span>Options supplémentaires:</span>
                          <span>+{(currentQuote.additional_premium || 0).toLocaleString()} XOF</span>
                        </div>
                      )}
                      <hr className="my-2" />
                      <div className="flex justify-between font-bold text-lg">
                        <span>Prime {getPremiumFrequencyLabel(currentQuote.premium_frequency || 'monthly').toLowerCase()}:</span>
                        <span className="text-green-600">{(currentQuote.final_premium || 0).toLocaleString()} XOF</span>
                      </div>
                      <div className="flex justify-between text-gray-600">
                        <span>Prime annuelle:</span>
                        <span>{(currentQuote.annual_premium || 0).toLocaleString()} XOF</span>
                      </div>
                    </div>
                  </div>

                  {/* Facteurs de tarification */}
                  {(currentQuote.pricing_factors || []).length > 0 && (
                    <div>
                      <h4 className="font-medium text-gray-900 mb-2">Facteurs de Tarification</h4>
                      <div className="space-y-1">
                        {(currentQuote.pricing_factors || []).map((factor, index) => (
                          <div key={index} className="flex justify-between text-sm">
                            <span>{factor.factor_name || 'Facteur inconnu'}:</span>
                            <span className={(factor.multiplier || 1) > 1 ? 'text-red-600' : (factor.multiplier || 1) < 1 ? 'text-green-600' : ''}>
                              ×{factor.multiplier || 1}
                            </span>
                          </div>
                        ))}
                      </div>
                    </div>
                  )}

                  {/* Conditions */}
                  {(currentQuote.conditions || []).length > 0 && (
                    <div>
                      <h4 className="font-medium text-gray-900 mb-2">Conditions Particulières</h4>
                      <ul className="text-sm text-amber-800 bg-amber-50 p-3 rounded-lg">
                        {(currentQuote.conditions || []).map((condition, index) => (
                          <li key={index} className="flex items-center space-x-2">
                            <AlertTriangle className="w-4 h-4" />
                            <span>{condition}</span>
                          </li>
                        ))}
                      </ul>
                    </div>
                  )}

                  {/* Validité */}
                  <div className="bg-gray-50 p-4 rounded-lg">
                    <div className="flex justify-between text-sm">
                      <span>Date du devis:</span>
                      <span>{currentQuote.quote_date ? new Date(currentQuote.quote_date).toLocaleDateString('fr-FR') : 'Non définie'}</span>
                    </div>
                    <div className="flex justify-between text-sm mt-1">
                      <span>Valable jusqu'au:</span>
                      <span className="font-medium text-red-600">
                        {currentQuote.expiry_date ? new Date(currentQuote.expiry_date).toLocaleDateString('fr-FR') : 'Non définie'}
                      </span>
                    </div>
                  </div>

                  {/* Actions */}
                  <div className="flex space-x-3">
                    <button
                      onClick={handleCreateOrder}
                      disabled={isCreatingOrder}
                      className="flex-1 bg-green-600 text-white py-2 px-4 rounded-lg hover:bg-green-700 transition-colors disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center space-x-2"
                    >
                      {isCreatingOrder ? (
                        <>
                          <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white"></div>
                          <span>Création...</span>
                        </>
                      ) : (
                        <>
                          <ShoppingCart className="w-4 h-4" />
                          <span>Créer Commande</span>
                        </>
                      )}
                    </button>
                    <button
                      onClick={handleSendEmail}
                      disabled={isSendingEmail}
                      className="flex-1 bg-blue-600 text-white py-2 px-4 rounded-lg hover:bg-blue-700 transition-colors disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center space-x-2"
                    >
                      {isSendingEmail ? (
                        <>
                          <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white"></div>
                          <span>Envoi...</span>
                        </>
                      ) : (
                        <>
                          <Send className="w-4 h-4" />
                          <span>Envoyer au Client</span>
                        </>
                      )}
                    </button>
                  </div>
                </div>
              ) : (
                <div className="text-center py-8">
                  <XCircle className="w-16 h-16 mx-auto mb-4 text-red-500" />
                  <h4 className="text-lg font-medium text-gray-900 mb-2">Client Non Éligible</h4>
                  <p className="text-gray-600">
                    {currentQuote.customer_name || (currentQuote.customer && currentQuote.customer.name) || 'Client inconnu'}
                  </p>
                  <p className="text-red-600 mt-2">
                    Raison: {currentQuote.reason || 'Information manquante ou critères non remplis'}
                  </p>
                  {currentQuote.product_name && (
                    <p className="text-gray-500 mt-1">
                      Produit: {currentQuote.product_name}
                    </p>
                  )}
                </div>
              )
            ) : (
              <div className="text-center text-gray-500 py-8">
                <Calculator className="w-12 h-12 mx-auto mb-4 text-gray-300" />
                <p>Générez un devis pour voir les résultats ici</p>
              </div>
            )}
          </div>
        </div>
      </div>

      {/* Modal de création de commande */}
      <QuoteToOrderModal
        isOpen={showOrderModal}
        onClose={() => setShowOrderModal(false)}
        quote={selectedQuoteForOrder}
        onOrderCreated={handleOrderCreated}
      />
    </div>
  );
};

export default QuotesManagement;
