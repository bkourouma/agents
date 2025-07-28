import React, { useState, useEffect } from 'react';
import {
  Package,
  Plus,
  Eye,
  Edit,
  Shield,
  Heart,
  Car,
  Home,
  Building,
  Euro,
  Calendar,
  Users,
  CheckCircle,
  XCircle,
  Trash2,
  X,
  Save
} from 'lucide-react';
import { insuranceApi } from '../../lib/insurance-api';
import type { InsuranceProduct } from '../../lib/insurance-api';

const ProductManagement: React.FC = () => {
  const [products, setProducts] = useState<InsuranceProduct[]>([]);
  const [selectedProduct, setSelectedProduct] = useState<InsuranceProduct | null>(null);
  const [productDetails, setProductDetails] = useState<any>(null);
  const [loading, setLoading] = useState(false);
  const [filter, setFilter] = useState<string>('all');
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [showEditModal, setShowEditModal] = useState(false);
  const [createLoading, setCreateLoading] = useState(false);
  const [editLoading, setEditLoading] = useState(false);
  const [deleteLoading, setDeleteLoading] = useState<string | null>(null);

  // Form state for creating new product
  const [newProduct, setNewProduct] = useState({
    product_code: '',
    name: '',
    category_id: '',
    description: '',
    product_type: 'life' as 'life' | 'health' | 'auto' | 'home' | 'business',
    coverage_type: '',
    min_coverage_amount: 0,
    max_coverage_amount: 0,
    min_age: 18,
    max_age: 65,
    waiting_period_days: 0,
    policy_term_years: 1,
    renewable: true,
    requires_medical_exam: false
  });

  // Form state for editing existing product
  const [editProduct, setEditProduct] = useState({
    id: '',
    product_code: '',
    name: '',
    category_id: '',
    description: '',
    product_type: 'life' as 'life' | 'health' | 'auto' | 'home' | 'business',
    coverage_type: '',
    min_coverage_amount: 0,
    max_coverage_amount: 0,
    min_age: 18,
    max_age: 65,
    waiting_period_days: 0,
    policy_term_years: 1,
    renewable: true,
    requires_medical_exam: false
  });

  useEffect(() => {
    loadProducts();
  }, [filter]);

  const loadProducts = async () => {
    setLoading(true);
    try {
      const filters = filter !== 'all' ? { type_produit: filter } : {};
      const response = await insuranceApi.getProducts(filters);
      
      if (response.success && response.data) {
        setProducts(response.data);
      } else {
        console.error('Erreur lors du chargement des produits:', response.error);
        setProducts([]);
      }
    } catch (error) {
      console.error('Erreur lors du chargement des produits:', error);
    } finally {
      setLoading(false);
    }
  };



  const handleCreateProduct = async () => {
    if (!newProduct.name || !newProduct.product_code) {
      alert('Veuillez remplir tous les champs obligatoires');
      return;
    }

    setCreateLoading(true);
    try {
      const response = await insuranceApi.createProduct(newProduct);

      if (response.success && response.data) {
        // Add new product to the list
        setProducts(prev => [response.data!, ...prev]);

        // Reset form and close modal
        setNewProduct({
          product_code: '',
          name: '',
          category_id: '',
          description: '',
          product_type: 'life',
          coverage_type: '',
          min_coverage_amount: 0,
          max_coverage_amount: 0,
          min_age: 18,
          max_age: 65,
          waiting_period_days: 0,
          policy_term_years: 1,
          renewable: true,
          requires_medical_exam: false
        });
        setShowCreateModal(false);

        alert('Produit créé avec succès!');
      } else {
        console.error('Erreur lors de la création:', response.error);
        alert('Erreur lors de la création du produit');
      }
    } catch (error) {
      console.error('Erreur lors de la création:', error);
      alert('Erreur lors de la création du produit');
    } finally {
      setCreateLoading(false);
    }
  };

  const handleEditProduct = (product: InsuranceProduct) => {
    setEditProduct({
      id: product.id,
      product_code: product.product_code,
      name: product.name,
      category_id: product.category_id,
      description: product.description || '',
      product_type: product.product_type,
      coverage_type: product.coverage_type || '',
      min_coverage_amount: product.min_coverage_amount || 0,
      max_coverage_amount: product.max_coverage_amount || 0,
      min_age: product.min_age || 18,
      max_age: product.max_age || 65,
      waiting_period_days: product.waiting_period_days || 0,
      policy_term_years: product.policy_term_years || 1,
      renewable: product.renewable,
      requires_medical_exam: product.requires_medical_exam
    });
    setShowEditModal(true);
  };

  const handleUpdateProduct = async () => {
    if (!editProduct.name || !editProduct.product_code) {
      alert('Veuillez remplir tous les champs obligatoires');
      return;
    }

    setEditLoading(true);
    try {
      const { id, ...productData } = editProduct;
      const response = await insuranceApi.updateProduct(id, productData);

      if (response.success && response.data) {
        // Update product in the list
        setProducts(prev => prev.map(p =>
          p.id === id ? response.data! : p
        ));

        // Update selected product if it's the one being edited
        if (selectedProduct?.id === id) {
          setSelectedProduct(response.data);
        }

        setShowEditModal(false);
        alert('Produit modifié avec succès!');
      } else {
        console.error('Erreur lors de la modification:', response.error);
        alert('Erreur lors de la modification du produit');
      }
    } catch (error) {
      console.error('Erreur lors de la modification:', error);
      alert('Erreur lors de la modification du produit');
    } finally {
      setEditLoading(false);
    }
  };

  const handleDeleteProduct = async (productId: string) => {
    if (!confirm('Êtes-vous sûr de vouloir supprimer ce produit ?')) {
      return;
    }

    setDeleteLoading(productId);
    try {
      const response = await insuranceApi.deleteProduct(productId);

      if (response.success) {
        // Remove product from the list
        setProducts(prev => prev.filter(p => p.id !== productId));

        // Clear selected product if it was deleted
        if (selectedProduct?.id === productId) {
          setSelectedProduct(null);
          setProductDetails(null);
        }

        alert('Produit supprimé avec succès!');
      } else {
        console.error('Erreur lors de la suppression:', response.error);
        alert('Erreur lors de la suppression du produit');
      }
    } catch (error) {
      console.error('Erreur lors de la suppression:', error);
      alert('Erreur lors de la suppression du produit');
    } finally {
      setDeleteLoading(null);
    }
  };

  const getProductTypeIcon = (type: string) => {
    switch (type) {
      case 'life': return <Shield className="w-5 h-5 text-blue-600" />;
      case 'health': return <Heart className="w-5 h-5 text-red-600" />;
      case 'auto': return <Car className="w-5 h-5 text-green-600" />;
      case 'home': return <Home className="w-5 h-5 text-purple-600" />;
      case 'business': return <Building className="w-5 h-5 text-orange-600" />;
      default: return <Package className="w-5 h-5 text-gray-600" />;
    }
  };

  const getProductTypeLabel = (type: string) => {
    switch (type) {
      case 'life': return 'Vie';
      case 'health': return 'Santé';
      case 'auto': return 'Auto';
      case 'home': return 'Habitation';
      case 'business': return 'Entreprise';
      default: return 'Autre';
    }
  };

  const resetCreateForm = () => {
    setNewProduct({
      product_code: '',
      name: '',
      category_id: '',
      description: '',
      product_type: 'life',
      coverage_type: '',
      min_coverage_amount: 0,
      max_coverage_amount: 0,
      min_age: 18,
      max_age: 65,
      waiting_period_days: 0,
      policy_term_years: 1,
      renewable: true,
      requires_medical_exam: false
    });
  };

  const productTypes = [
    { value: 'all', label: 'Tous les produits' },
    { value: 'life', label: 'Assurance Vie' },
    { value: 'health', label: 'Assurance Santé' },
    { value: 'auto', label: 'Assurance Auto' },
    { value: 'home', label: 'Assurance Habitation' },
    { value: 'business', label: 'Assurance Entreprise' }
  ];

  return (
    <div className="space-y-6">
      {/* En-tête et filtres */}
      <div className="bg-white rounded-lg shadow-md p-6">
        <div className="flex justify-between items-center mb-4">
          <h2 className="text-xl font-semibold text-gray-900">Catalogue de Produits</h2>
          <button
            onClick={() => setShowCreateModal(true)}
            className="bg-blue-600 text-white px-4 py-2 rounded-lg hover:bg-blue-700 transition-colors flex items-center space-x-2"
          >
            <Plus className="w-4 h-4" />
            <span>Nouveau Produit</span>
          </button>
        </div>
        
        <div className="flex space-x-4">
          <select
            value={filter}
            onChange={(e) => setFilter(e.target.value)}
            className="px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
          >
            {productTypes.map((type) => (
              <option key={type.value} value={type.value}>
                {type.label}
              </option>
            ))}
          </select>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Liste des produits */}
        <div className="bg-white rounded-lg shadow-md">
          <div className="p-6 border-b border-gray-200">
            <h3 className="text-lg font-semibold text-gray-900">
              Produits ({products.length})
            </h3>
          </div>
          <div className="max-h-96 overflow-y-auto">
            {loading ? (
              <div className="p-6 text-center text-gray-500">
                Chargement des produits...
              </div>
            ) : products.length === 0 ? (
              <div className="p-6 text-center text-gray-500">
                Aucun produit trouvé
              </div>
            ) : (
              products.map((product) => (
                <div
                  key={product.id}
                  className="p-4 border-b border-gray-100 hover:bg-gray-50 cursor-pointer"
                  onClick={() => loadProductDetails(product)}
                >
                  <div className="flex items-center justify-between">
                    <div className="flex items-center space-x-3">
                      <div className="w-10 h-10 bg-gray-100 rounded-full flex items-center justify-center">
                        {getProductTypeIcon(product.product_type)}
                      </div>
                      <div>
                        <p className="font-medium text-gray-900">{product.name}</p>
                        <p className="text-sm text-gray-500">{product.product_code}</p>
                      </div>
                    </div>
                    <div className="flex items-center space-x-2">
                      <span className="px-2 py-1 rounded-full text-xs font-medium bg-blue-100 text-blue-800">
                        {getProductTypeLabel(product.product_type)}
                      </span>
                      <button
                        onClick={(e) => {
                          e.stopPropagation();
                          handleEditProduct(product);
                        }}
                        className="p-1 text-blue-600 hover:text-blue-800 hover:bg-blue-50 rounded transition-colors"
                        title="Modifier le produit"
                      >
                        <Edit className="w-4 h-4" />
                      </button>
                      <button
                        onClick={(e) => {
                          e.stopPropagation();
                          handleDeleteProduct(product.id);
                        }}
                        disabled={deleteLoading === product.id}
                        className="p-1 text-red-600 hover:text-red-800 hover:bg-red-50 rounded transition-colors disabled:opacity-50"
                        title="Supprimer le produit"
                      >
                        {deleteLoading === product.id ? (
                          <div className="w-4 h-4 border-2 border-red-600 border-t-transparent rounded-full animate-spin"></div>
                        ) : (
                          <Trash2 className="w-4 h-4" />
                        )}
                      </button>
                      {product.is_active ? (
                        <CheckCircle className="w-4 h-4 text-green-600" />
                      ) : (
                        <XCircle className="w-4 h-4 text-red-600" />
                      )}
                    </div>
                  </div>
                  <div className="mt-2 text-sm text-gray-600">
                    <p>{product.description}</p>
                    <div className="flex items-center space-x-4 mt-1">
                      <span>Âge: {product.min_age}-{product.max_age} ans</span>
                      {product.min_coverage_amount > 0 && (
                        <span>Couverture: {product.min_coverage_amount.toLocaleString()} - {product.max_coverage_amount.toLocaleString()} €</span>
                      )}
                    </div>
                  </div>
                </div>
              ))
            )}
          </div>
        </div>

        {/* Détails du produit sélectionné */}
        <div className="bg-white rounded-lg shadow-md">
          <div className="p-6 border-b border-gray-200">
            <h3 className="text-lg font-semibold text-gray-900">
              {selectedProduct ? 'Détails du Produit' : 'Sélectionnez un produit'}
            </h3>
          </div>
          <div className="p-6">
            {selectedProduct && productDetails ? (
              <div className="space-y-6">
                {/* Informations générales */}
                <div>
                  <h4 className="font-medium text-gray-900 mb-3">Informations Générales</h4>
                  <div className="grid grid-cols-2 gap-4 text-sm">
                    <div>
                      <span className="text-gray-500">Code produit:</span>
                      <p className="font-medium">{selectedProduct.product_code}</p>
                    </div>
                    <div>
                      <span className="text-gray-500">Type:</span>
                      <p className="font-medium">{getProductTypeLabel(selectedProduct.product_type)}</p>
                    </div>
                    <div>
                      <span className="text-gray-500">Couverture:</span>
                      <p className="font-medium">{selectedProduct.coverageType}</p>
                    </div>
                    <div>
                      <span className="text-gray-500">Renouvelable:</span>
                      <p className="font-medium">{selectedProduct.renewable ? 'Oui' : 'Non'}</p>
                    </div>
                    <div>
                      <span className="text-gray-500">Examen médical:</span>
                      <p className="font-medium">{selectedProduct.requiresMedicalExam ? 'Requis' : 'Non requis'}</p>
                    </div>
                    <div>
                      <span className="text-gray-500">Statut:</span>
                      <p className={`font-medium ${selectedProduct.isActive ? 'text-green-600' : 'text-red-600'}`}>
                        {selectedProduct.isActive ? 'Actif' : 'Inactif'}
                      </p>
                    </div>
                  </div>
                </div>

                {/* Fonctionnalités */}
                {productDetails.features && productDetails.features.length > 0 && (
                  <div>
                    <h4 className="font-medium text-gray-900 mb-3">Fonctionnalités</h4>
                    <div className="space-y-2">
                      {productDetails.features.map((feature: any, index: number) => (
                        <div key={index} className="flex items-center justify-between p-2 bg-gray-50 rounded">
                          <div>
                            <p className="font-medium text-sm">{feature.featureName}</p>
                            <p className="text-xs text-gray-600">{feature.description}</p>
                          </div>
                          <span className={`px-2 py-1 rounded text-xs ${
                            feature.isStandard ? 'bg-green-100 text-green-800' : 'bg-blue-100 text-blue-800'
                          }`}>
                            {feature.isStandard ? 'Standard' : 'Option'}
                          </span>
                        </div>
                      ))}
                    </div>
                  </div>
                )}

                {/* Niveaux de prix */}
                {productDetails.pricing_tiers && productDetails.pricing_tiers.length > 0 && (
                  <div>
                    <h4 className="font-medium text-gray-900 mb-3">Niveaux de Prix</h4>
                    <div className="space-y-2">
                      {productDetails.pricing_tiers.map((tier: any, index: number) => (
                        <div key={index} className="flex items-center justify-between p-3 border border-gray-200 rounded">
                          <div>
                            <p className="font-medium">{tier.tierName}</p>
                            {tier.coverageAmount > 0 && (
                              <p className="text-sm text-gray-600">
                                Couverture: {tier.coverageAmount.toLocaleString()} €
                              </p>
                            )}
                          </div>
                          <div className="text-right">
                            <p className="font-bold text-blue-600">
                              {tier.basePremium.toLocaleString()} €
                            </p>
                            <p className="text-xs text-gray-500">
                              {tier.premiumFrequency === 'monthly' ? '/mois' : 
                               tier.premiumFrequency === 'annual' ? '/an' : '/' + tier.premiumFrequency}
                            </p>
                          </div>
                        </div>
                      ))}
                    </div>
                  </div>
                )}

                {/* Actions */}
                <div className="flex space-x-3">
                  <button className="flex-1 bg-blue-600 text-white py-2 px-4 rounded-lg hover:bg-blue-700 transition-colors flex items-center justify-center space-x-2">
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
                <Package className="w-12 h-12 mx-auto mb-4 text-gray-300" />
                <p>Cliquez sur un produit pour voir ses détails</p>
              </div>
            )}
          </div>
        </div>
      </div>

      {/* Modal de création de produit */}
      {showCreateModal && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg shadow-xl max-w-2xl w-full mx-4 max-h-[90vh] overflow-y-auto">
            <div className="p-6 border-b border-gray-200">
              <div className="flex justify-between items-center">
                <h3 className="text-lg font-semibold text-gray-900">Nouveau Produit</h3>
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
                    Code Produit *
                  </label>
                  <input
                    type="text"
                    value={newProduct.product_code}
                    onChange={(e) => setNewProduct(prev => ({ ...prev, product_code: e.target.value }))}
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                    placeholder="PROD001"
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Nom du Produit *
                  </label>
                  <input
                    type="text"
                    value={newProduct.name}
                    onChange={(e) => setNewProduct(prev => ({ ...prev, name: e.target.value }))}
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                    placeholder="Assurance Vie Premium"
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Type de Produit *
                  </label>
                  <select
                    value={newProduct.product_type}
                    onChange={(e) => setNewProduct(prev => ({ ...prev, product_type: e.target.value as any }))}
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                  >
                    <option value="life">Assurance Vie</option>
                    <option value="health">Assurance Santé</option>
                    <option value="auto">Assurance Auto</option>
                    <option value="home">Assurance Habitation</option>
                    <option value="business">Assurance Entreprise</option>
                  </select>
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    ID Catégorie
                  </label>
                  <input
                    type="text"
                    value={newProduct.category_id}
                    onChange={(e) => setNewProduct(prev => ({ ...prev, category_id: e.target.value }))}
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                    placeholder="CAT001"
                  />
                </div>

                <div className="md:col-span-2">
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Description
                  </label>
                  <textarea
                    value={newProduct.description}
                    onChange={(e) => setNewProduct(prev => ({ ...prev, description: e.target.value }))}
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                    rows={3}
                    placeholder="Description du produit..."
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Type de Couverture
                  </label>
                  <input
                    type="text"
                    value={newProduct.coverage_type}
                    onChange={(e) => setNewProduct(prev => ({ ...prev, coverage_type: e.target.value }))}
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                    placeholder="Couverture complète"
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Durée de Police (années)
                  </label>
                  <input
                    type="number"
                    value={newProduct.policy_term_years}
                    onChange={(e) => setNewProduct(prev => ({ ...prev, policy_term_years: parseInt(e.target.value) || 1 }))}
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                    min="1"
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Couverture Min (€)
                  </label>
                  <input
                    type="number"
                    value={newProduct.min_coverage_amount}
                    onChange={(e) => setNewProduct(prev => ({ ...prev, min_coverage_amount: parseFloat(e.target.value) || 0 }))}
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                    min="0"
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Couverture Max (€)
                  </label>
                  <input
                    type="number"
                    value={newProduct.max_coverage_amount}
                    onChange={(e) => setNewProduct(prev => ({ ...prev, max_coverage_amount: parseFloat(e.target.value) || 0 }))}
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                    min="0"
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Âge Minimum
                  </label>
                  <input
                    type="number"
                    value={newProduct.min_age}
                    onChange={(e) => setNewProduct(prev => ({ ...prev, min_age: parseInt(e.target.value) || 18 }))}
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                    min="0"
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Âge Maximum
                  </label>
                  <input
                    type="number"
                    value={newProduct.max_age}
                    onChange={(e) => setNewProduct(prev => ({ ...prev, max_age: parseInt(e.target.value) || 65 }))}
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                    min="0"
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Période d'Attente (jours)
                  </label>
                  <input
                    type="number"
                    value={newProduct.waiting_period_days}
                    onChange={(e) => setNewProduct(prev => ({ ...prev, waiting_period_days: parseInt(e.target.value) || 0 }))}
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                    min="0"
                  />
                </div>

                <div className="md:col-span-2">
                  <div className="flex items-center space-x-6">
                    <label className="flex items-center">
                      <input
                        type="checkbox"
                        checked={newProduct.renewable}
                        onChange={(e) => setNewProduct(prev => ({ ...prev, renewable: e.target.checked }))}
                        className="rounded border-gray-300 text-blue-600 focus:ring-blue-500"
                      />
                      <span className="ml-2 text-sm text-gray-700">Renouvelable</span>
                    </label>

                    <label className="flex items-center">
                      <input
                        type="checkbox"
                        checked={newProduct.requires_medical_exam}
                        onChange={(e) => setNewProduct(prev => ({ ...prev, requires_medical_exam: e.target.checked }))}
                        className="rounded border-gray-300 text-blue-600 focus:ring-blue-500"
                      />
                      <span className="ml-2 text-sm text-gray-700">Examen médical requis</span>
                    </label>
                  </div>
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
                onClick={handleCreateProduct}
                disabled={createLoading}
                className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors flex items-center space-x-2 disabled:opacity-50"
              >
                {createLoading ? (
                  <div className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin"></div>
                ) : (
                  <Save className="w-4 h-4" />
                )}
                <span>{createLoading ? 'Création...' : 'Créer le produit'}</span>
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Modal de modification de produit */}
      {showEditModal && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg shadow-xl max-w-2xl w-full mx-4 max-h-[90vh] overflow-y-auto">
            <div className="p-6 border-b border-gray-200">
              <div className="flex justify-between items-center">
                <h3 className="text-lg font-semibold text-gray-900">Modifier le Produit</h3>
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
                    Code Produit *
                  </label>
                  <input
                    type="text"
                    value={editProduct.product_code}
                    onChange={(e) => setEditProduct(prev => ({ ...prev, product_code: e.target.value }))}
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                    placeholder="PROD001"
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Nom du Produit *
                  </label>
                  <input
                    type="text"
                    value={editProduct.name}
                    onChange={(e) => setEditProduct(prev => ({ ...prev, name: e.target.value }))}
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                    placeholder="Assurance Vie Premium"
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Type de Produit *
                  </label>
                  <select
                    value={editProduct.product_type}
                    onChange={(e) => setEditProduct(prev => ({ ...prev, product_type: e.target.value as any }))}
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                  >
                    <option value="life">Assurance Vie</option>
                    <option value="health">Assurance Santé</option>
                    <option value="auto">Assurance Auto</option>
                    <option value="home">Assurance Habitation</option>
                    <option value="business">Assurance Entreprise</option>
                  </select>
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    ID Catégorie
                  </label>
                  <input
                    type="text"
                    value={editProduct.category_id}
                    onChange={(e) => setEditProduct(prev => ({ ...prev, category_id: e.target.value }))}
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                    placeholder="CAT001"
                  />
                </div>

                <div className="md:col-span-2">
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Description
                  </label>
                  <textarea
                    value={editProduct.description}
                    onChange={(e) => setEditProduct(prev => ({ ...prev, description: e.target.value }))}
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                    rows={3}
                    placeholder="Description du produit..."
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Type de Couverture
                  </label>
                  <input
                    type="text"
                    value={editProduct.coverage_type}
                    onChange={(e) => setEditProduct(prev => ({ ...prev, coverage_type: e.target.value }))}
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                    placeholder="Couverture complète"
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Durée de Police (années)
                  </label>
                  <input
                    type="number"
                    value={editProduct.policy_term_years}
                    onChange={(e) => setEditProduct(prev => ({ ...prev, policy_term_years: parseInt(e.target.value) || 1 }))}
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                    min="1"
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Couverture Min (€)
                  </label>
                  <input
                    type="number"
                    value={editProduct.min_coverage_amount}
                    onChange={(e) => setEditProduct(prev => ({ ...prev, min_coverage_amount: parseFloat(e.target.value) || 0 }))}
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                    min="0"
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Couverture Max (€)
                  </label>
                  <input
                    type="number"
                    value={editProduct.max_coverage_amount}
                    onChange={(e) => setEditProduct(prev => ({ ...prev, max_coverage_amount: parseFloat(e.target.value) || 0 }))}
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                    min="0"
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Âge Minimum
                  </label>
                  <input
                    type="number"
                    value={editProduct.min_age}
                    onChange={(e) => setEditProduct(prev => ({ ...prev, min_age: parseInt(e.target.value) || 18 }))}
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                    min="0"
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Âge Maximum
                  </label>
                  <input
                    type="number"
                    value={editProduct.max_age}
                    onChange={(e) => setEditProduct(prev => ({ ...prev, max_age: parseInt(e.target.value) || 65 }))}
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                    min="0"
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Période d'Attente (jours)
                  </label>
                  <input
                    type="number"
                    value={editProduct.waiting_period_days}
                    onChange={(e) => setEditProduct(prev => ({ ...prev, waiting_period_days: parseInt(e.target.value) || 0 }))}
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                    min="0"
                  />
                </div>

                <div className="md:col-span-2">
                  <div className="flex items-center space-x-6">
                    <label className="flex items-center">
                      <input
                        type="checkbox"
                        checked={editProduct.renewable}
                        onChange={(e) => setEditProduct(prev => ({ ...prev, renewable: e.target.checked }))}
                        className="rounded border-gray-300 text-blue-600 focus:ring-blue-500"
                      />
                      <span className="ml-2 text-sm text-gray-700">Renouvelable</span>
                    </label>

                    <label className="flex items-center">
                      <input
                        type="checkbox"
                        checked={editProduct.requires_medical_exam}
                        onChange={(e) => setEditProduct(prev => ({ ...prev, requires_medical_exam: e.target.checked }))}
                        className="rounded border-gray-300 text-blue-600 focus:ring-blue-500"
                      />
                      <span className="ml-2 text-sm text-gray-700">Examen médical requis</span>
                    </label>
                  </div>
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
                onClick={handleUpdateProduct}
                disabled={editLoading}
                className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors flex items-center space-x-2 disabled:opacity-50"
              >
                {editLoading ? (
                  <div className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin"></div>
                ) : (
                  <Save className="w-4 h-4" />
                )}
                <span>{editLoading ? 'Modification...' : 'Modifier le produit'}</span>
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default ProductManagement;
