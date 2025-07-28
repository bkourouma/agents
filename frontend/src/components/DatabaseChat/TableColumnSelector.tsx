import React, { useState } from 'react';
import { 
  TableCellsIcon, 
  ChevronDownIcon, 
  ChevronRightIcon,
  CheckIcon,
  XMarkIcon,
  EyeIcon,
  KeyIcon,
  LockClosedIcon
} from '@heroicons/react/24/outline';

interface Column {
  name: string;
  data_type: string;
  is_nullable: boolean;
  is_primary_key: boolean;
  is_unique: boolean;
  max_length?: number;
  precision?: number;
  scale?: number;
  default_value?: string;
  description?: string;
}

interface Table {
  name: string;
  schema?: string;
  table_type: string;
  row_count?: number;
  columns: Column[];
  description?: string;
}

interface TableColumnSelectorProps {
  tables: Table[];
  selectedTables: string[];
  onTableSelectionChange: (selectedTables: string[]) => void;
  onColumnMappingChange?: (tableName: string, columnMappings: Record<string, any>) => void;
  showColumnDetails?: boolean;
}

const TableColumnSelector: React.FC<TableColumnSelectorProps> = ({
  tables,
  selectedTables,
  onTableSelectionChange,
  onColumnMappingChange,
  showColumnDetails = false
}) => {
  const [expandedTables, setExpandedTables] = useState<Set<string>>(new Set());
  const [sampleDataVisible, setSampleDataVisible] = useState<Set<string>>(new Set());

  const toggleTableExpansion = (tableName: string) => {
    const newExpanded = new Set(expandedTables);
    if (newExpanded.has(tableName)) {
      newExpanded.delete(tableName);
    } else {
      newExpanded.add(tableName);
    }
    setExpandedTables(newExpanded);
  };

  const toggleTableSelection = (tableName: string) => {
    const newSelected = selectedTables.includes(tableName)
      ? selectedTables.filter(t => t !== tableName)
      : [...selectedTables, tableName];
    onTableSelectionChange(newSelected);
  };

  const selectAllTables = () => {
    onTableSelectionChange(tables.map(t => t.name));
  };

  const deselectAllTables = () => {
    onTableSelectionChange([]);
  };

  const getDataTypeIcon = (dataType: string) => {
    const type = dataType.toLowerCase();
    if (type.includes('int') || type.includes('number')) {
      return '🔢';
    } else if (type.includes('varchar') || type.includes('text') || type.includes('char')) {
      return '📝';
    } else if (type.includes('date') || type.includes('time')) {
      return '📅';
    } else if (type.includes('bool')) {
      return '✅';
    } else if (type.includes('decimal') || type.includes('float') || type.includes('double')) {
      return '💰';
    } else if (type.includes('json')) {
      return '📋';
    }
    return '❓';
  };

  const formatDataType = (column: Column) => {
    let type = column.data_type;
    if (column.max_length) {
      type += `(${column.max_length})`;
    } else if (column.precision && column.scale) {
      type += `(${column.precision},${column.scale})`;
    } else if (column.precision) {
      type += `(${column.precision})`;
    }
    return type;
  };

  return (
    <div className="space-y-4">
      {/* Header with bulk actions */}
      <div className="flex items-center justify-between">
        <div className="flex items-center space-x-2">
          <TableCellsIcon className="h-5 w-5 text-gray-500" />
          <span className="font-medium text-gray-900">
            Tables disponibles ({tables.length})
          </span>
        </div>
        <div className="flex space-x-2">
          <button
            onClick={selectAllTables}
            className="text-sm text-blue-600 hover:text-blue-800"
          >
            Tout sélectionner
          </button>
          <span className="text-gray-300">|</span>
          <button
            onClick={deselectAllTables}
            className="text-sm text-gray-600 hover:text-gray-800"
          >
            Tout désélectionner
          </button>
        </div>
      </div>

      {/* Selection summary */}
      {selectedTables.length > 0 && (
        <div className="bg-blue-50 border border-blue-200 rounded-lg p-3">
          <div className="flex items-center space-x-2">
            <CheckIcon className="h-4 w-4 text-blue-500" />
            <span className="text-sm font-medium text-blue-900">
              {selectedTables.length} table(s) sélectionnée(s)
            </span>
          </div>
          <div className="mt-1 text-xs text-blue-700">
            {selectedTables.join(', ')}
          </div>
        </div>
      )}

      {/* Tables list */}
      <div className="space-y-2 max-h-96 overflow-y-auto">
        {tables.map((table) => {
          const isSelected = selectedTables.includes(table.name);
          const isExpanded = expandedTables.has(table.name);
          
          return (
            <div
              key={table.name}
              className={`border rounded-lg transition-colors ${
                isSelected ? 'border-blue-300 bg-blue-50' : 'border-gray-200 bg-white'
              }`}
            >
              {/* Table header */}
              <div className="p-4">
                <div className="flex items-center justify-between">
                  <div className="flex items-center space-x-3">
                    <input
                      type="checkbox"
                      checked={isSelected}
                      onChange={() => toggleTableSelection(table.name)}
                      className="h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded"
                    />
                    
                    <div className="flex-1">
                      <div className="flex items-center space-x-2">
                        <h3 className="font-medium text-gray-900">{table.name}</h3>
                        {table.schema && (
                          <span className="text-xs bg-gray-100 text-gray-600 px-2 py-1 rounded">
                            {table.schema}
                          </span>
                        )}
                        <span className="text-xs bg-blue-100 text-blue-600 px-2 py-1 rounded">
                          {table.table_type}
                        </span>
                      </div>
                      
                      <div className="flex items-center space-x-4 mt-1 text-sm text-gray-500">
                        <span>{table.columns.length} colonnes</span>
                        {table.row_count !== undefined && (
                          <span>{table.row_count.toLocaleString()} lignes</span>
                        )}
                      </div>
                      
                      {table.description && (
                        <p className="text-sm text-gray-600 mt-1">{table.description}</p>
                      )}
                    </div>
                  </div>

                  <div className="flex items-center space-x-2">
                    {showColumnDetails && (
                      <button
                        onClick={() => toggleTableExpansion(table.name)}
                        className="p-1 text-gray-400 hover:text-gray-600"
                      >
                        {isExpanded ? (
                          <ChevronDownIcon className="h-4 w-4" />
                        ) : (
                          <ChevronRightIcon className="h-4 w-4" />
                        )}
                      </button>
                    )}
                  </div>
                </div>
              </div>

              {/* Expanded column details */}
              {isExpanded && showColumnDetails && (
                <div className="border-t border-gray-200 bg-gray-50">
                  <div className="p-4">
                    <h4 className="text-sm font-medium text-gray-900 mb-3">
                      Colonnes ({table.columns.length})
                    </h4>
                    
                    <div className="space-y-2">
                      {table.columns.map((column, index) => (
                        <div
                          key={column.name}
                          className="flex items-center justify-between p-2 bg-white rounded border border-gray-200"
                        >
                          <div className="flex items-center space-x-3">
                            <span className="text-lg">{getDataTypeIcon(column.data_type)}</span>
                            
                            <div>
                              <div className="flex items-center space-x-2">
                                <span className="font-medium text-gray-900">{column.name}</span>
                                
                                {column.is_primary_key && (
                                  <KeyIcon className="h-3 w-3 text-yellow-500" title="Clé primaire" />
                                )}
                                
                                {column.is_unique && (
                                  <LockClosedIcon className="h-3 w-3 text-blue-500" title="Unique" />
                                )}
                                
                                {!column.is_nullable && (
                                  <span className="text-xs bg-red-100 text-red-600 px-1 py-0.5 rounded">
                                    NOT NULL
                                  </span>
                                )}
                              </div>
                              
                              <div className="text-sm text-gray-500">
                                {formatDataType(column)}
                              </div>
                              
                              {column.description && (
                                <div className="text-xs text-gray-400 mt-1">
                                  {column.description}
                                </div>
                              )}
                            </div>
                          </div>

                          <div className="text-right text-xs text-gray-500">
                            {column.default_value && (
                              <div>Défaut: {column.default_value}</div>
                            )}
                          </div>
                        </div>
                      ))}
                    </div>
                  </div>
                </div>
              )}
            </div>
          );
        })}
      </div>

      {tables.length === 0 && (
        <div className="text-center py-8 text-gray-500">
          <TableCellsIcon className="h-12 w-12 mx-auto mb-2 text-gray-300" />
          <p>Aucune table trouvée</p>
        </div>
      )}
    </div>
  );
};

export default TableColumnSelector;
