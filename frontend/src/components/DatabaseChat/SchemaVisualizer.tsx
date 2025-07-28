import React from 'react';
import { XMarkIcon, TableCellsIcon } from '@heroicons/react/24/outline';

interface DatabaseTable {
  id: number;
  name: string;
  display_name: string;
  description?: string;
  columns: DatabaseColumn[];
}

interface DatabaseColumn {
  id: number;
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
}

interface SchemaVisualizerProps {
  tables: DatabaseTable[];
  onClose: () => void;
}

const SchemaVisualizer: React.FC<SchemaVisualizerProps> = ({ tables, onClose }) => {
  const getDataTypeDisplay = (column: DatabaseColumn) => {
    let type = column.data_type;
    
    if (column.data_type === 'VARCHAR' && column.max_length) {
      type += `(${column.max_length})`;
    } else if (column.data_type === 'DECIMAL' && column.precision) {
      type += `(${column.precision}${column.scale ? `,${column.scale}` : ''})`;
    }
    
    return type;
  };

  const getColumnConstraints = (column: DatabaseColumn) => {
    const constraints = [];
    if (column.is_primary_key) constraints.push('PK');
    if (column.is_unique && !column.is_primary_key) constraints.push('UNIQUE');
    if (!column.is_nullable) constraints.push('NOT NULL');
    return constraints;
  };

  return (
    <div className="fixed inset-0 z-50 overflow-y-auto">
      <div className="flex items-center justify-center min-h-screen pt-4 px-4 pb-20 text-center sm:block sm:p-0">
        <div className="fixed inset-0 bg-gray-500 bg-opacity-75 transition-opacity" onClick={onClose} />

        <span className="hidden sm:inline-block sm:align-middle sm:h-screen">&#8203;</span>

        <div className="inline-block align-bottom bg-white rounded-lg text-left overflow-hidden shadow-xl transform transition-all sm:my-8 sm:align-middle sm:max-w-6xl sm:w-full">
          <div className="bg-white px-4 pt-5 pb-4 sm:p-6">
            <div className="flex items-center justify-between mb-6">
              <h3 className="text-lg leading-6 font-medium text-gray-900">
                Database Schema Overview
              </h3>
              <button
                type="button"
                onClick={onClose}
                className="text-gray-400 hover:text-gray-600"
              >
                <XMarkIcon className="h-6 w-6" />
              </button>
            </div>

            {tables.length === 0 ? (
              <div className="text-center py-12">
                <TableCellsIcon className="mx-auto h-12 w-12 text-gray-400" />
                <h3 className="mt-2 text-sm font-medium text-gray-900">No tables</h3>
                <p className="mt-1 text-sm text-gray-500">
                  Create your first table to see the schema visualization.
                </p>
              </div>
            ) : (
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6 max-h-96 overflow-y-auto">
                {tables.map((table) => (
                  <div
                    key={table.id}
                    className="bg-white border border-gray-200 rounded-lg shadow-sm hover:shadow-md transition-shadow"
                  >
                    {/* Table Header */}
                    <div className="bg-gray-50 px-4 py-3 border-b border-gray-200 rounded-t-lg">
                      <h4 className="text-sm font-medium text-gray-900 truncate">
                        {table.display_name}
                      </h4>
                      <p className="text-xs text-gray-500 truncate">
                        {table.name} • {table.columns.length} columns
                      </p>
                      {table.description && (
                        <p className="text-xs text-gray-400 mt-1 line-clamp-2">
                          {table.description}
                        </p>
                      )}
                    </div>

                    {/* Columns */}
                    <div className="px-4 py-3">
                      {table.columns.length === 0 ? (
                        <p className="text-xs text-gray-500 italic">No columns defined</p>
                      ) : (
                        <div className="space-y-2">
                          {table.columns
                            .sort((a, b) => a.order_index - b.order_index)
                            .map((column) => (
                              <div
                                key={column.id}
                                className="flex items-center justify-between text-xs"
                              >
                                <div className="flex-1 min-w-0">
                                  <div className="flex items-center">
                                    <span className="font-medium text-gray-900 truncate">
                                      {column.display_name}
                                    </span>
                                    {getColumnConstraints(column).map((constraint) => (
                                      <span
                                        key={constraint}
                                        className={`ml-1 inline-flex items-center px-1.5 py-0.5 rounded text-xs font-medium ${
                                          constraint === 'PK'
                                            ? 'bg-yellow-100 text-yellow-800'
                                            : constraint === 'UNIQUE'
                                            ? 'bg-blue-100 text-blue-800'
                                            : 'bg-red-100 text-red-800'
                                        }`}
                                      >
                                        {constraint}
                                      </span>
                                    ))}
                                  </div>
                                  <div className="text-gray-500 truncate">
                                    {column.name} • {getDataTypeDisplay(column)}
                                  </div>
                                  {column.default_value && (
                                    <div className="text-gray-400 truncate">
                                      Default: {column.default_value}
                                    </div>
                                  )}
                                </div>
                              </div>
                            ))}
                        </div>
                      )}
                    </div>
                  </div>
                ))}
              </div>
            )}

            {/* Schema Statistics */}
            {tables.length > 0 && (
              <div className="mt-6 pt-4 border-t border-gray-200">
                <div className="grid grid-cols-3 gap-4 text-center">
                  <div>
                    <div className="text-2xl font-bold text-blue-600">
                      {tables.length}
                    </div>
                    <div className="text-sm text-gray-500">Tables</div>
                  </div>
                  <div>
                    <div className="text-2xl font-bold text-green-600">
                      {tables.reduce((sum, table) => sum + table.columns.length, 0)}
                    </div>
                    <div className="text-sm text-gray-500">Columns</div>
                  </div>
                  <div>
                    <div className="text-2xl font-bold text-purple-600">
                      {tables.reduce(
                        (sum, table) =>
                          sum + table.columns.filter((col) => col.is_primary_key).length,
                        0
                      )}
                    </div>
                    <div className="text-sm text-gray-500">Primary Keys</div>
                  </div>
                </div>
              </div>
            )}
          </div>

          <div className="bg-gray-50 px-4 py-3 sm:px-6 sm:flex sm:flex-row-reverse">
            <button
              type="button"
              onClick={onClose}
              className="w-full inline-flex justify-center rounded-md border border-gray-300 shadow-sm px-4 py-2 bg-white text-base font-medium text-gray-700 hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 sm:w-auto sm:text-sm"
            >
              Close
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};

export default SchemaVisualizer;
