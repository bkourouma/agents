import React, { useState } from 'react';
import { useMutation, useQueryClient } from '@tanstack/react-query';
import { toast } from 'react-hot-toast';
import {
  PlusIcon,
  PencilIcon,
  TrashIcon,
  TableCellsIcon,
  EyeIcon
} from '@heroicons/react/24/outline';

import TableCreator from './TableCreator';
import ColumnEditor from './ColumnEditor';
import SchemaVisualizer from './SchemaVisualizer';
import { apiClient } from '../../lib/api';

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

interface SchemaDesignerProps {
  tables: DatabaseTable[];
  selectedTable: DatabaseTable | null;
  onTableSelect: (table: DatabaseTable | null) => void;
  onTableUpdate: () => void;
}

const SchemaDesigner: React.FC<SchemaDesignerProps> = ({
  tables,
  selectedTable,
  onTableSelect,
  onTableUpdate
}) => {
  const [showTableCreator, setShowTableCreator] = useState(false);
  const [showColumnEditor, setShowColumnEditor] = useState(false);
  const [showSchemaVisualizer, setShowSchemaVisualizer] = useState(false);
  const [editingTable, setEditingTable] = useState<DatabaseTable | null>(null);
  const queryClient = useQueryClient();

  // Delete table mutation
  const deleteTableMutation = useMutation({
    mutationFn: async (tableId: number) => {
      await apiClient.deleteDatabaseTable(tableId);
    },
    onSuccess: () => {
      toast.success('Table supprimée avec succès');
      onTableUpdate();
      if (selectedTable && selectedTable.id === deleteTableMutation.variables) {
        onTableSelect(null);
      }
    },
    onError: (error: any) => {
      toast.error(error.response?.data?.detail || 'Échec de la suppression de la table');
    },
  });

  const handleDeleteTable = (table: DatabaseTable) => {
    if (window.confirm(`Êtes-vous sûr de vouloir supprimer la table "${table.display_name}" ?`)) {
      deleteTableMutation.mutate(table.id);
    }
  };

  const handleEditTable = (table: DatabaseTable) => {
    setEditingTable(table);
    setShowTableCreator(true);
  };

  const handleTableCreated = () => {
    setShowTableCreator(false);
    setEditingTable(null);
    onTableUpdate();
  };

  const handleColumnEditorClose = () => {
    setShowColumnEditor(false);
    onTableUpdate();
  };

  return (
    <div className="h-full flex bg-gradient-to-br from-slate-50 via-blue-50 to-indigo-50">
      {/* Tables List */}
      <div className="w-1/3 border-r border-gray-200/50 bg-white/80 backdrop-blur-sm shadow-lg">
        <div className="p-6 border-b border-gray-200/50 bg-gradient-to-r from-blue-50 to-indigo-50">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-3">
              <div className="w-8 h-8 bg-gradient-to-br from-blue-500 to-indigo-600 rounded-lg flex items-center justify-center shadow-lg">
                <TableCellsIcon className="h-5 w-5 text-white" />
              </div>
              <h2 className="text-xl font-bold bg-gradient-to-r from-gray-900 via-blue-800 to-indigo-800 bg-clip-text text-transparent">Tables</h2>
            </div>
            <div className="flex space-x-2">
              <button
                onClick={() => setShowSchemaVisualizer(true)}
                className="inline-flex items-center px-4 py-2 border border-gray-300/50 shadow-sm text-sm font-medium rounded-lg text-gray-700 bg-white/80 backdrop-blur-sm hover:bg-white hover:shadow-md transition-all duration-300 transform hover:scale-105"
                title="Voir le schéma"
              >
                <EyeIcon className="h-4 w-4" />
              </button>
              <button
                onClick={() => setShowTableCreator(true)}
                className="inline-flex items-center px-4 py-2 border border-transparent shadow-lg text-sm font-medium rounded-lg text-white bg-gradient-to-r from-blue-500 to-indigo-600 hover:from-blue-600 hover:to-indigo-700 transition-all duration-300 transform hover:scale-105"
              >
                <PlusIcon className="h-4 w-4 mr-2" />
                Nouvelle table
              </button>
            </div>
          </div>
        </div>

        <div className="overflow-y-auto h-full p-4">
          {tables.length === 0 ? (
            <div className="p-8 text-center animate-fadeIn">
              <div className="relative mb-6">
                <div className="w-20 h-20 bg-gradient-to-br from-blue-100 to-indigo-100 rounded-full flex items-center justify-center mx-auto shadow-lg">
                  <TableCellsIcon className="h-10 w-10 text-blue-500" />
                </div>
                <div className="absolute -top-1 -right-1 w-6 h-6 bg-gradient-to-br from-yellow-400 to-orange-500 rounded-full flex items-center justify-center shadow-lg">
                  <span className="text-white text-xs font-bold">!</span>
                </div>
              </div>
              <h3 className="text-lg font-semibold text-gray-900 mb-2">Aucune table</h3>
              <p className="text-gray-600 mb-8 max-w-sm mx-auto">
                Commencez par créer votre première table pour structurer votre base de données.
              </p>
              <button
                onClick={() => setShowTableCreator(true)}
                className="inline-flex items-center px-6 py-3 border border-transparent shadow-lg text-sm font-medium rounded-xl text-white bg-gradient-to-r from-blue-500 to-indigo-600 hover:from-blue-600 hover:to-indigo-700 transition-all duration-300 transform hover:scale-105"
              >
                <PlusIcon className="h-5 w-5 mr-2" />
                Créer une table
              </button>
            </div>
          ) : (
            <div className="space-y-3">
              {tables.map((table, index) => (
                <div
                  key={table.id}
                  className={`
                    group p-4 rounded-xl cursor-pointer border transition-all duration-300 transform hover:scale-[1.02] animate-slideUp
                    ${selectedTable?.id === table.id
                      ? 'bg-gradient-to-r from-blue-50 to-indigo-50 border-blue-300 shadow-lg shadow-blue-500/20'
                      : 'bg-white/80 backdrop-blur-sm border-gray-200/50 hover:bg-white hover:shadow-lg hover:border-blue-200'
                    }
                  `}
                  style={{ animationDelay: `${index * 100}ms` }}
                  onClick={() => onTableSelect(table)}
                >
                  <div className="flex items-center justify-between">
                    <div className="flex items-center space-x-3 flex-1 min-w-0">
                      <div className={`w-10 h-10 rounded-lg flex items-center justify-center shadow-sm ${
                        selectedTable?.id === table.id
                          ? 'bg-gradient-to-br from-blue-500 to-indigo-600'
                          : 'bg-gradient-to-br from-gray-100 to-gray-200 group-hover:from-blue-100 group-hover:to-indigo-100'
                      } transition-all duration-300`}>
                        <TableCellsIcon className={`h-5 w-5 ${
                          selectedTable?.id === table.id ? 'text-white' : 'text-gray-600 group-hover:text-blue-600'
                        }`} />
                      </div>
                      <div className="flex-1 min-w-0">
                        <h3 className="text-sm font-semibold text-gray-900 truncate">
                          {table.display_name}
                        </h3>
                        <p className="text-xs text-gray-500 truncate flex items-center">
                          <span className="font-mono">{table.name}</span>
                          <span className="mx-1">•</span>
                          <span className="flex items-center">
                            <span className="w-1.5 h-1.5 bg-blue-500 rounded-full mr-1"></span>
                            {table.columns.length} colonnes
                          </span>
                        </p>
                        {table.description && (
                          <p className="text-xs text-gray-400 mt-1 line-clamp-2">
                            {table.description}
                          </p>
                        )}
                      </div>
                    </div>
                    <div className="flex items-center space-x-1 ml-2 opacity-0 group-hover:opacity-100 transition-opacity duration-300">
                      <button
                        onClick={(e) => {
                          e.stopPropagation();
                          handleEditTable(table);
                        }}
                        className="p-2 text-gray-400 hover:text-blue-600 hover:bg-blue-50 rounded-lg transition-all duration-200"
                        title="Modifier la table"
                      >
                        <PencilIcon className="h-4 w-4" />
                      </button>
                      <button
                        onClick={(e) => {
                          e.stopPropagation();
                          handleDeleteTable(table);
                        }}
                        className="p-2 text-gray-400 hover:text-red-600 hover:bg-red-50 rounded-lg transition-all duration-200"
                        title="Supprimer la table"
                      >
                        <TrashIcon className="h-4 w-4" />
                      </button>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>

      {/* Table Details */}
      <div className="flex-1 flex flex-col bg-white/50 backdrop-blur-sm rounded-tl-2xl shadow-xl border-l border-gray-200/50">
        {selectedTable ? (
          <>
            <div className="p-6 border-b border-gray-200/50 bg-gradient-to-r from-white/80 to-blue-50/50 backdrop-blur-sm">
              <div className="flex items-center justify-between">
                <div className="flex items-center space-x-4">
                  <div className="w-12 h-12 bg-gradient-to-br from-blue-500 to-indigo-600 rounded-xl flex items-center justify-center shadow-lg">
                    <TableCellsIcon className="h-6 w-6 text-white" />
                  </div>
                  <div>
                    <h2 className="text-xl font-bold bg-gradient-to-r from-gray-900 via-blue-800 to-indigo-800 bg-clip-text text-transparent">
                      {selectedTable.display_name}
                    </h2>
                    <p className="text-sm text-gray-600 flex items-center">
                      <span className="font-mono bg-gray-100 px-2 py-1 rounded text-xs mr-2">{selectedTable.name}</span>
                      <span className="flex items-center">
                        <span className="w-1.5 h-1.5 bg-blue-500 rounded-full mr-1"></span>
                        {selectedTable.columns.length} colonnes
                      </span>
                    </p>
                  </div>
                </div>
                <button
                  onClick={() => setShowColumnEditor(true)}
                  className="inline-flex items-center px-6 py-3 border border-transparent shadow-lg text-sm font-medium rounded-xl text-white bg-gradient-to-r from-blue-500 to-indigo-600 hover:from-blue-600 hover:to-indigo-700 transition-all duration-300 transform hover:scale-105"
                >
                  <PlusIcon className="h-5 w-5 mr-2" />
                  Ajouter une colonne
                </button>
              </div>
              {selectedTable.description && (
                <div className="mt-4 p-3 bg-blue-50/50 rounded-lg border border-blue-200/50">
                  <p className="text-sm text-gray-700">
                    {selectedTable.description}
                  </p>
                </div>
              )}
            </div>

            <div className="flex-1 overflow-y-auto p-6">
              {selectedTable.columns.length === 0 ? (
                <div className="text-center py-16 animate-fadeIn">
                  <div className="relative mb-6">
                    <div className="w-20 h-20 bg-gradient-to-br from-blue-100 to-indigo-100 rounded-full flex items-center justify-center mx-auto shadow-lg">
                      <TableCellsIcon className="h-10 w-10 text-blue-500" />
                    </div>
                    <div className="absolute -top-1 -right-1 w-6 h-6 bg-gradient-to-br from-yellow-400 to-orange-500 rounded-full flex items-center justify-center shadow-lg">
                      <span className="text-white text-xs font-bold">+</span>
                    </div>
                  </div>
                  <h3 className="text-lg font-semibold text-gray-900 mb-2">Aucune colonne</h3>
                  <p className="text-gray-600 mb-8 max-w-md mx-auto">
                    Ajoutez des colonnes pour définir la structure et les propriétés de votre table.
                  </p>
                  <button
                    onClick={() => setShowColumnEditor(true)}
                    className="inline-flex items-center px-6 py-3 border border-transparent shadow-lg text-sm font-medium rounded-xl text-white bg-gradient-to-r from-blue-500 to-indigo-600 hover:from-blue-600 hover:to-indigo-700 transition-all duration-300 transform hover:scale-105"
                  >
                    <PlusIcon className="h-5 w-5 mr-2" />
                    Ajouter une colonne
                  </button>
                </div>
              ) : (
                <div className="space-y-3">
                  {selectedTable.columns
                    .sort((a, b) => a.order_index - b.order_index)
                    .map((column, index) => (
                      <div
                        key={column.id}
                        className="bg-white/80 backdrop-blur-sm border border-gray-200/50 rounded-xl p-6 shadow-sm hover:shadow-lg transition-all duration-300 transform hover:scale-[1.01] animate-slideUp"
                        style={{ animationDelay: `${index * 100}ms` }}
                      >
                        <div className="flex items-center justify-between">
                          <div className="flex-1">
                            <div className="flex items-center space-x-3 mb-3">
                              <div className="w-8 h-8 bg-gradient-to-br from-blue-100 to-indigo-100 rounded-lg flex items-center justify-center">
                                <span className="text-blue-600 font-bold text-sm">
                                  {column.display_name.charAt(0).toUpperCase()}
                                </span>
                              </div>
                              <div className="flex-1">
                                <h4 className="text-base font-semibold text-gray-900">
                                  {column.display_name}
                                </h4>
                                <span className="text-xs text-gray-500 font-mono bg-gray-100 px-2 py-1 rounded">
                                  {column.name}
                                </span>
                              </div>
                              <div className="flex flex-wrap gap-1">
                                {column.is_primary_key && (
                                  <span className="inline-flex items-center px-2 py-1 rounded-full text-xs font-medium bg-gradient-to-r from-yellow-100 to-orange-100 text-yellow-800 border border-yellow-200">
                                    🔑 CP
                                  </span>
                                )}
                                {column.is_unique && (
                                  <span className="inline-flex items-center px-2 py-1 rounded-full text-xs font-medium bg-gradient-to-r from-blue-100 to-indigo-100 text-blue-800 border border-blue-200">
                                    ✨ UNIQUE
                                  </span>
                                )}
                                {!column.is_nullable && (
                                  <span className="inline-flex items-center px-2 py-1 rounded-full text-xs font-medium bg-gradient-to-r from-red-100 to-rose-100 text-red-800 border border-red-200">
                                    ⚠️ NON NULL
                                  </span>
                                )}
                              </div>
                            </div>
                            <div className="bg-gray-50/50 rounded-lg p-3 border border-gray-200/50">
                              <div className="flex items-center text-sm text-gray-700 space-x-4">
                                <span className="font-semibold text-blue-600">{column.data_type}</span>
                                {column.max_length && (
                                  <span className="bg-blue-100 text-blue-800 px-2 py-1 rounded text-xs">
                                    Longueur: {column.max_length}
                                  </span>
                                )}
                                {column.precision && (
                                  <span className="bg-green-100 text-green-800 px-2 py-1 rounded text-xs">
                                    Précision: {column.precision}
                                    {column.scale ? `,${column.scale}` : ''}
                                  </span>
                                )}
                                {column.default_value && (
                                  <span className="bg-purple-100 text-purple-800 px-2 py-1 rounded text-xs">
                                    Défaut : {column.default_value}
                                  </span>
                                )}
                              </div>
                              {column.description && (
                                <p className="mt-2 text-sm text-gray-600 italic">
                                  {column.description}
                                </p>
                              )}
                            </div>
                          </div>
                        </div>
                      </div>
                    ))}
                </div>
              )}
            </div>
          </>
        ) : (
          <div className="flex-1 flex items-center justify-center animate-fadeIn">
            <div className="text-center max-w-md">
              <div className="relative mb-8">
                <div className="w-24 h-24 bg-gradient-to-br from-gray-100 to-gray-200 rounded-full flex items-center justify-center mx-auto shadow-lg">
                  <TableCellsIcon className="h-12 w-12 text-gray-400" />
                </div>
                <div className="absolute -top-2 -right-2 w-8 h-8 bg-gradient-to-br from-blue-500 to-indigo-600 rounded-full flex items-center justify-center shadow-lg">
                  <span className="text-white text-sm">👆</span>
                </div>
              </div>
              <h3 className="text-xl font-semibold text-gray-900 mb-3">Aucune table sélectionnée</h3>
              <p className="text-gray-600 leading-relaxed">
                Sélectionnez une table dans la liste de gauche pour explorer sa structure et gérer ses colonnes.
              </p>
              <div className="mt-8 p-4 bg-blue-50/50 rounded-lg border border-blue-200/50">
                <p className="text-sm text-blue-700">
                  💡 <strong>Astuce :</strong> Cliquez sur une table pour voir ses détails et colonnes
                </p>
              </div>
            </div>
          </div>
        )}
      </div>

      {/* Modals */}
      {showTableCreator && (
        <TableCreator
          table={editingTable}
          onClose={() => {
            setShowTableCreator(false);
            setEditingTable(null);
          }}
          onSuccess={handleTableCreated}
        />
      )}

      {showColumnEditor && selectedTable && (
        <ColumnEditor
          table={selectedTable}
          onClose={handleColumnEditorClose}
        />
      )}

      {showSchemaVisualizer && (
        <SchemaVisualizer
          tables={tables}
          onClose={() => setShowSchemaVisualizer(false)}
        />
      )}
    </div>
  );
};

export default SchemaDesigner;
