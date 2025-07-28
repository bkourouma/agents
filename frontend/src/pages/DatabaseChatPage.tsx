import React, { useState, useEffect } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { toast } from 'react-hot-toast';
import {
  PlusIcon,
  TableCellsIcon,
  ChatBubbleLeftRightIcon,
  ChartBarIcon,
  Cog6ToothIcon,
  SparklesIcon,
  CircleStackIcon,
  ServerIcon
} from '@heroicons/react/24/outline';

import SchemaDesigner from '../components/DatabaseChat/SchemaDesigner';
import DataManager from '../components/DatabaseChat/DataManager';
import VannaTraining from '../components/DatabaseChat/VannaTraining';
import NaturalLanguageQuery from '../components/DatabaseChat/NaturalLanguageQuery';
import DatabaseSetupWizard from '../components/DatabaseChat/DatabaseSetupWizard';
import { apiClient } from '../lib/api';

interface DatabaseTable {
  id: number;
  name: string;
  display_name: string;
  description?: string;
  user_id: number;
  created_at: string;
  updated_at?: string;
  is_active: boolean;
  metadata_config: Record<string, any>;
  columns: DatabaseColumn[];
}

interface DatabaseColumn {
  id: number;
  table_id: number;
  name: string;
  display_name: string;
  data_type: string;
  max_length?: number;
  precision?: number;
  scale?: number;
  is_nullable: boolean;
  is_primary_key: boolean;
  is_unique: boolean;
  default_value?: string;
  description?: string;
  order_index: number;
  created_at: string;
  updated_at?: string;
}

type ActiveTab = 'connections' | 'schema' | 'data' | 'training' | 'query' | 'analytics';

const DatabaseChatPage: React.FC = () => {
  const [activeTab, setActiveTab] = useState<ActiveTab>('connections');
  const [selectedTable, setSelectedTable] = useState<DatabaseTable | null>(null);
  const [showSetupWizard, setShowSetupWizard] = useState(false);
  const queryClient = useQueryClient();

  // Fetch tables
  const { data: tables = [], isLoading: tablesLoading, error: tablesError } = useQuery({
    queryKey: ['database-tables'],
    queryFn: async () => {
      return await apiClient.getDatabaseTables();
    },
  });

  // Fetch database schema
  const { data: schema, isLoading: schemaLoading } = useQuery({
    queryKey: ['database-schema'],
    queryFn: async () => {
      return await apiClient.getDatabaseSchema();
    },
  });

  // Fetch database connections
  const { data: connections = [], isLoading: connectionsLoading } = useQuery({
    queryKey: ['database-connections'],
    queryFn: async () => {
      return await apiClient.getDatabaseConnections();
    },
  });

  const tabs = [
    {
      id: 'connections' as const,
      name: 'Connexions',
      shortName: 'Connexions',
      icon: ServerIcon,
      description: 'Gérer les connexions aux bases de données externes',
      color: 'gray',
      gradient: 'from-gray-500 to-gray-600'
    },
    {
      id: 'schema' as const,
      name: 'Schéma',
      shortName: 'Schéma',
      icon: TableCellsIcon,
      description: 'Créer et gérer les tables et colonnes de la base de données',
      color: 'blue',
      gradient: 'from-blue-500 to-blue-600'
    },
    {
      id: 'data' as const,
      name: 'Données',
      shortName: 'Données',
      icon: CircleStackIcon,
      description: 'Importer, exporter et gérer les données des tables',
      color: 'emerald',
      gradient: 'from-emerald-500 to-emerald-600'
    },
    {
      id: 'training' as const,
      name: 'Formation IA',
      shortName: 'Formation',
      icon: SparklesIcon,
      description: 'Former Vanna AI sur votre schéma de base de données',
      color: 'purple',
      gradient: 'from-purple-500 to-purple-600'
    },
    {
      id: 'query' as const,
      name: 'Requêtes',
      shortName: 'Requêtes',
      icon: ChatBubbleLeftRightIcon,
      description: 'Interroger votre base de données en langage naturel',
      color: 'indigo',
      gradient: 'from-indigo-500 to-indigo-600'
    },
    {
      id: 'analytics' as const,
      name: 'Analytiques',
      shortName: 'Analytics',
      icon: ChartBarIcon,
      description: 'Voir les analyses d\'utilisation et les métriques de performance',
      color: 'orange',
      gradient: 'from-orange-500 to-orange-600'
    }
  ];

  const renderTabContent = () => {
    switch (activeTab) {
      case 'connections':
        return (
          <div className="space-y-6">
            {/* Header */}
            <div className="flex items-center justify-between">
              <div>
                <h2 className="text-xl font-semibold text-gray-900">Connexions aux bases de données</h2>
                <p className="text-sm text-gray-600 mt-1">
                  Gérez vos connexions aux bases de données externes pour l'entraînement Vanna AI
                </p>
              </div>
              <button
                onClick={() => setShowSetupWizard(true)}
                className="flex items-center space-x-2 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700"
              >
                <PlusIcon className="h-4 w-4" />
                <span>Nouvelle connexion</span>
              </button>
            </div>

            {/* Connections list */}
            {connectionsLoading ? (
              <div className="text-center py-8">
                <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-500 mx-auto"></div>
                <p className="text-sm text-gray-500 mt-2">Chargement des connexions...</p>
              </div>
            ) : connections.length === 0 ? (
              <div className="text-center py-16">
                <div className="w-20 h-20 bg-gray-100 rounded-2xl flex items-center justify-center mx-auto mb-6">
                  <ServerIcon className="w-10 h-10 text-gray-400" />
                </div>
                <h3 className="text-lg font-medium text-gray-900 mb-2">Aucune connexion configurée</h3>
                <p className="text-gray-500 mb-6 max-w-md mx-auto">
                  Commencez par configurer une connexion à votre base de données externe pour pouvoir importer des tables et entraîner Vanna AI.
                </p>
                <button
                  onClick={() => setShowSetupWizard(true)}
                  className="flex items-center space-x-2 px-6 py-3 bg-blue-600 text-white rounded-lg hover:bg-blue-700 mx-auto"
                >
                  <PlusIcon className="h-5 w-5" />
                  <span>Configurer une connexion</span>
                </button>
              </div>
            ) : (
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                {connections.map((connection: any) => (
                  <div key={connection.id} className="bg-white border border-gray-200 rounded-lg p-4">
                    <div className="flex items-center justify-between mb-3">
                      <h3 className="font-medium text-gray-900">{connection.name}</h3>
                      <span className={`px-2 py-1 text-xs rounded-full ${
                        connection.connection_status === 'connected'
                          ? 'bg-green-100 text-green-800'
                          : connection.connection_status === 'failed'
                          ? 'bg-red-100 text-red-800'
                          : 'bg-gray-100 text-gray-800'
                      }`}>
                        {connection.connection_status === 'connected' ? 'Connecté' :
                         connection.connection_status === 'failed' ? 'Échec' : 'Non testé'}
                      </span>
                    </div>
                    <div className="space-y-1 text-sm text-gray-600">
                      <div>Type: {connection.database_type}</div>
                      {connection.host && <div>Hôte: {connection.host}:{connection.port}</div>}
                      {connection.database && <div>Base: {connection.database}</div>}
                    </div>
                    <div className="mt-4 flex space-x-2">
                      <button className="text-xs text-blue-600 hover:text-blue-800">
                        Tester
                      </button>
                      <button className="text-xs text-gray-600 hover:text-gray-800">
                        Modifier
                      </button>
                      <button className="text-xs text-red-600 hover:text-red-800">
                        Supprimer
                      </button>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        );
      case 'schema':
        return (
          <SchemaDesigner
            tables={tables}
            selectedTable={selectedTable}
            onTableSelect={setSelectedTable}
            onTableUpdate={() => queryClient.invalidateQueries({ queryKey: ['database-tables'] })}
          />
        );
      case 'data':
        return (
          <DataManager
            tables={tables}
            selectedTable={selectedTable}
            onTableSelect={setSelectedTable}
          />
        );
      case 'training':
        return (
          <VannaTraining
            tables={tables}
            schema={schema}
          />
        );
      case 'query':
        return (
          <NaturalLanguageQuery
            tables={tables}
            schema={schema}
          />
        );
      case 'analytics':
        return (
          <div className="text-center py-16">
            <div className="w-20 h-20 bg-orange-500/20 rounded-2xl flex items-center justify-center mx-auto mb-6">
              <ChartBarIcon className="w-10 h-10 text-orange-400" />
            </div>
            <h3 className="text-2xl font-bold text-white mb-3">Tableau de Bord Analytique</h3>
            <p className="text-slate-400 text-lg max-w-md mx-auto">
              Bientôt disponible : Visualisez les analyses d'utilisation, les performances des requêtes et les métriques système.
            </p>
            <div className="mt-8 inline-flex items-center px-4 py-2 bg-orange-500/20 text-orange-300 rounded-xl text-sm font-medium">
              <svg className="w-4 h-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
              </svg>
              En développement
            </div>
          </div>
        );
      default:
        return null;
    }
  };

  if (tablesError) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-slate-900 via-gray-900 to-slate-800 flex items-center justify-center p-6">
        <div className="max-w-md w-full">
          <div className="bg-slate-800/50 backdrop-blur-sm rounded-2xl shadow-2xl border border-red-500/20 p-8 text-center">
            <div className="w-16 h-16 bg-gradient-to-br from-red-500 to-red-600 rounded-2xl flex items-center justify-center mx-auto mb-6 shadow-lg shadow-red-500/25">
              <svg className="w-8 h-8 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-2.5L13.732 4c-.77-.833-1.964-.833-2.732 0L3.732 16.5c-.77.833.192 2.5 1.732 2.5z" />
              </svg>
            </div>
            <h3 className="text-xl font-bold text-white mb-3">Erreur de Connexion</h3>
            <p className="text-slate-400 mb-6">
              Impossible de charger les tables de la base de données. Vérifiez votre connexion et réessayez.
            </p>
            <button
              onClick={() => window.location.reload()}
              className="bg-gradient-to-r from-red-500 to-red-600 text-white px-6 py-3 rounded-xl font-medium hover:from-red-600 hover:to-red-700 transition-all duration-300 transform hover:scale-105 shadow-lg shadow-red-500/25"
            >
              Réessayer la Connexion
            </button>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-900 via-gray-900 to-slate-800">
      {/* Header Section */}
      <div className="bg-slate-800/50 backdrop-blur-sm border-b border-slate-700/50">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
          <div className="flex flex-col lg:flex-row lg:items-center lg:justify-between gap-6">
            {/* Title Section */}
            <div className="flex items-center space-x-4">
              <div className="w-14 h-14 bg-gradient-to-br from-blue-500 to-blue-600 rounded-2xl flex items-center justify-center shadow-lg shadow-blue-500/25">
                <CircleStackIcon className="w-7 h-7 text-white" />
              </div>
              <div>
                <h1 className="text-3xl font-bold text-white mb-1">
                  Base de Données
                </h1>
                <p className="text-slate-400 text-lg">
                  Concevez des schémas, gérez les données et interrogez avec l'IA
                </p>
              </div>
            </div>

            {/* Stats Cards */}
            {schema && (
              <div className="flex items-center space-x-4">
                <div className="bg-slate-700/50 backdrop-blur-sm rounded-xl px-4 py-3 border border-slate-600/50">
                  <div className="flex items-center space-x-3">
                    <div className="w-3 h-3 bg-blue-500 rounded-full animate-pulse"></div>
                    <div>
                      <span className="text-white text-lg font-semibold">{schema.total_tables}</span>
                      <span className="text-slate-400 text-sm ml-1">tables</span>
                    </div>
                  </div>
                </div>
                <div className="bg-slate-700/50 backdrop-blur-sm rounded-xl px-4 py-3 border border-slate-600/50">
                  <div className="flex items-center space-x-3">
                    <div className="w-3 h-3 bg-emerald-500 rounded-full animate-pulse"></div>
                    <div>
                      <span className="text-white text-lg font-semibold">{schema.total_columns}</span>
                      <span className="text-slate-400 text-sm ml-1">colonnes</span>
                    </div>
                  </div>
                </div>
              </div>
            )}
          </div>
        </div>

        {/* Tab Navigation */}
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex items-center bg-slate-700/50 rounded-full p-1 backdrop-blur-sm border border-slate-600/50 overflow-x-auto">
            {tabs.map((tab, index) => {
              const Icon = tab.icon;
              const isActive = activeTab === tab.id;
              return (
                <button
                  key={tab.id}
                  onClick={() => setActiveTab(tab.id)}
                  className={`
                    relative px-4 py-2.5 rounded-full text-xs font-medium transition-all duration-300 flex items-center space-x-2 whitespace-nowrap
                    ${isActive
                      ? `bg-gradient-to-r ${tab.gradient} text-white shadow-lg shadow-${tab.color}-500/25`
                      : 'text-slate-300 hover:text-white hover:bg-slate-600/50'
                    }
                  `}
                  title={tab.description}
                >
                  <Icon className="w-4 h-4" />
                  <span className="hidden sm:inline">{tab.name}</span>
                  <span className="sm:hidden">{tab.shortName}</span>

                  {/* Active glow effect */}
                  {isActive && (
                    <div className="absolute inset-0 rounded-full bg-blue-400/20 blur-sm"></div>
                  )}
                </button>
              );
            })}
          </div>
        </div>
      </div>

      {/* Content Area */}
      <div className="flex-1 p-6">
        <div className="max-w-7xl mx-auto">
          {tablesLoading || schemaLoading ? (
            <div className="flex flex-col items-center justify-center h-96 space-y-6">
              <div className="relative">
                <div className="w-16 h-16 border-4 border-slate-600 border-t-blue-500 rounded-full animate-spin"></div>
                <div className="absolute inset-0 w-16 h-16 border-4 border-transparent border-r-blue-400 rounded-full animate-spin" style={{ animationDirection: 'reverse', animationDuration: '1.5s' }}></div>
              </div>
              <div className="text-center">
                <h3 className="text-xl font-semibold text-white mb-2">Chargement de la base de données</h3>
                <p className="text-slate-400">Récupération de votre schéma et de vos tables...</p>
              </div>
            </div>
          ) : (
            <div className="animate-fadeIn">
              <div className="bg-slate-800/50 backdrop-blur-sm border border-slate-700/50 rounded-2xl shadow-2xl overflow-hidden">
                <div className="p-6">
                  {renderTabContent()}
                </div>
              </div>
            </div>
          )}
        </div>
      </div>

      {/* Database Setup Wizard */}
      <DatabaseSetupWizard
        isOpen={showSetupWizard}
        onClose={() => setShowSetupWizard(false)}
        onComplete={(connectionId) => {
          queryClient.invalidateQueries({ queryKey: ['database-connections'] });
          toast.success('Connexion configurée avec succès !');
        }}
      />
    </div>
  );
};

export default DatabaseChatPage;
