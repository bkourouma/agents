import React, { useState } from 'react';
import { ArrowLeft, FileText, Calculator, List, Eye } from 'lucide-react';
import QuotesList from '../components/Insurance/QuotesList';
import QuotesManagement from '../components/Insurance/QuotesManagement';
import type { InsuranceQuote } from '../types/insurance';

type ViewMode = 'list' | 'create' | 'view' | 'edit';

const QuotesPage: React.FC = () => {
  const [viewMode, setViewMode] = useState<ViewMode>('list');
  const [selectedQuote, setSelectedQuote] = useState<InsuranceQuote | null>(null);

  const handleViewQuote = (quote: InsuranceQuote) => {
    setSelectedQuote(quote);
    setViewMode('view');
  };

  const handleEditQuote = (quote: InsuranceQuote) => {
    setSelectedQuote(quote);
    setViewMode('edit');
  };

  const handleCreateQuote = () => {
    setSelectedQuote(null);
    setViewMode('create');
  };

  const handleBackToList = () => {
    setSelectedQuote(null);
    setViewMode('list');
  };

  const getPageTitle = () => {
    switch (viewMode) {
      case 'create':
        return 'Nouveau Devis';
      case 'view':
        return `Devis ${selectedQuote?.quote_number || ''}`;
      case 'edit':
        return `Modifier Devis ${selectedQuote?.quote_number || ''}`;
      default:
        return 'Gestion des Devis';
    }
  };

  const getPageIcon = () => {
    switch (viewMode) {
      case 'create':
        return <Calculator className="w-6 h-6" />;
      case 'view':
        return <Eye className="w-6 h-6" />;
      case 'edit':
        return <FileText className="w-6 h-6" />;
      default:
        return <List className="w-6 h-6" />;
    }
  };

  return (
    <div className="min-h-screen bg-gray-50">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Header */}
        <div className="mb-8">
          <div className="flex items-center space-x-4 mb-4">
            {viewMode !== 'list' && (
              <button
                onClick={handleBackToList}
                className="flex items-center text-gray-600 hover:text-gray-900 transition-colors"
              >
                <ArrowLeft className="w-5 h-5 mr-2" />
                Retour à la liste
              </button>
            )}
          </div>
          
          <div className="flex items-center space-x-3">
            <div className="p-2 bg-blue-100 rounded-lg text-blue-600">
              {getPageIcon()}
            </div>
            <div>
              <h1 className="text-3xl font-bold text-gray-900">{getPageTitle()}</h1>
              <p className="text-gray-600 mt-1">
                {viewMode === 'list' && 'Gérez tous vos devis d\'assurance'}
                {viewMode === 'create' && 'Créez un nouveau devis personnalisé'}
                {viewMode === 'view' && 'Consultez les détails du devis'}
                {viewMode === 'edit' && 'Modifiez les paramètres du devis'}
              </p>
            </div>
          </div>
        </div>

        {/* Content */}
        <div className="bg-white rounded-lg shadow-sm">
          {viewMode === 'list' && (
            <div className="p-6">
              <QuotesList
                onViewQuote={handleViewQuote}
                onEditQuote={handleEditQuote}
                onCreateQuote={handleCreateQuote}
              />
            </div>
          )}

          {(viewMode === 'create' || viewMode === 'view' || viewMode === 'edit') && (
            <div className="p-6">
              <QuotesManagement />
            </div>
          )}
        </div>

        {/* Quick Stats */}
        {viewMode === 'list' && (
          <div className="mt-8 grid grid-cols-1 md:grid-cols-4 gap-6">
            <div className="bg-white p-6 rounded-lg shadow-sm border">
              <div className="flex items-center">
                <div className="p-2 bg-green-100 rounded-lg">
                  <FileText className="w-6 h-6 text-green-600" />
                </div>
                <div className="ml-4">
                  <p className="text-sm font-medium text-gray-600">Devis Actifs</p>
                  <p className="text-2xl font-bold text-gray-900">-</p>
                </div>
              </div>
            </div>

            <div className="bg-white p-6 rounded-lg shadow-sm border">
              <div className="flex items-center">
                <div className="p-2 bg-blue-100 rounded-lg">
                  <Calculator className="w-6 h-6 text-blue-600" />
                </div>
                <div className="ml-4">
                  <p className="text-sm font-medium text-gray-600">Devis ce mois</p>
                  <p className="text-2xl font-bold text-gray-900">-</p>
                </div>
              </div>
            </div>

            <div className="bg-white p-6 rounded-lg shadow-sm border">
              <div className="flex items-center">
                <div className="p-2 bg-yellow-100 rounded-lg">
                  <FileText className="w-6 h-6 text-yellow-600" />
                </div>
                <div className="ml-4">
                  <p className="text-sm font-medium text-gray-600">Taux de conversion</p>
                  <p className="text-2xl font-bold text-gray-900">-</p>
                </div>
              </div>
            </div>

            <div className="bg-white p-6 rounded-lg shadow-sm border">
              <div className="flex items-center">
                <div className="p-2 bg-purple-100 rounded-lg">
                  <FileText className="w-6 h-6 text-purple-600" />
                </div>
                <div className="ml-4">
                  <p className="text-sm font-medium text-gray-600">Prime moyenne</p>
                  <p className="text-2xl font-bold text-gray-900">-</p>
                </div>
              </div>
            </div>
          </div>
        )}

        {/* Quick Actions */}
        {viewMode === 'list' && (
          <div className="mt-8 bg-white rounded-lg shadow-sm border p-6">
            <h3 className="text-lg font-semibold text-gray-900 mb-4">Actions Rapides</h3>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              <button
                onClick={handleCreateQuote}
                className="flex items-center justify-center p-4 border-2 border-dashed border-gray-300 rounded-lg hover:border-blue-500 hover:bg-blue-50 transition-colors group"
              >
                <div className="text-center">
                  <Calculator className="w-8 h-8 text-gray-400 group-hover:text-blue-500 mx-auto mb-2" />
                  <p className="text-sm font-medium text-gray-600 group-hover:text-blue-600">
                    Créer un nouveau devis
                  </p>
                </div>
              </button>

              <button className="flex items-center justify-center p-4 border-2 border-dashed border-gray-300 rounded-lg hover:border-green-500 hover:bg-green-50 transition-colors group">
                <div className="text-center">
                  <FileText className="w-8 h-8 text-gray-400 group-hover:text-green-500 mx-auto mb-2" />
                  <p className="text-sm font-medium text-gray-600 group-hover:text-green-600">
                    Importer des devis
                  </p>
                </div>
              </button>

              <button className="flex items-center justify-center p-4 border-2 border-dashed border-gray-300 rounded-lg hover:border-purple-500 hover:bg-purple-50 transition-colors group">
                <div className="text-center">
                  <FileText className="w-8 h-8 text-gray-400 group-hover:text-purple-500 mx-auto mb-2" />
                  <p className="text-sm font-medium text-gray-600 group-hover:text-purple-600">
                    Exporter les rapports
                  </p>
                </div>
              </button>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default QuotesPage;
