import React, { useState } from 'react';
import { useQuery, useMutation } from '@tanstack/react-query';
import { toast } from 'react-hot-toast';
import {
  ArrowUpTrayIcon,
  ArrowDownTrayIcon,
  PlusIcon,
  TableCellsIcon,
  DocumentArrowUpIcon
} from '@heroicons/react/24/outline';
import { apiClient } from '../../lib/api';

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
  is_nullable: boolean;
  is_primary_key: boolean;
  description?: string;
}

interface DataManagerProps {
  tables: DatabaseTable[];
  selectedTable: DatabaseTable | null;
  onTableSelect: (table: DatabaseTable | null) => void;
}

const DataManager: React.FC<DataManagerProps> = ({
  tables,
  selectedTable,
  onTableSelect
}) => {
  const [showImportModal, setShowImportModal] = useState(false);
  const [importFile, setImportFile] = useState<File | null>(null);
  const [currentPage, setCurrentPage] = useState(1);
  const pageSize = 50;

  // Fetch table data
  const { data: tableData, isLoading: dataLoading, refetch: refetchData } = useQuery({
    queryKey: ['table-data', selectedTable?.id, currentPage],
    queryFn: async () => {
      if (!selectedTable) return null;
      return await apiClient.getTableData(selectedTable.id, currentPage, pageSize);
    },
    enabled: !!selectedTable,
  });

  // Import data mutation
  const importDataMutation = useMutation({
    mutationFn: async ({ file, tableId }: { file: File; tableId: number }) => {
      return await apiClient.importTableData(tableId, file, {});
    },
    onSuccess: () => {
      toast.success('Data import started successfully');
      setShowImportModal(false);
      setImportFile(null);
      refetchData();
    },
    onError: (error: any) => {
      toast.error(error.response?.data?.detail || 'Failed to import data');
    },
  });

  // Download template
  const downloadTemplate = async (table: DatabaseTable) => {
    try {
      await apiClient.getTableTemplate(table.id);
      toast.success(`Excel template for ${table.display_name} downloaded successfully!`);
    } catch (error: any) {
      console.error('Error downloading template:', error);
      toast.error(error.response?.data?.detail || 'Failed to download template');
    }
  };

  const handleImport = () => {
    if (!selectedTable || !importFile) return;
    
    importDataMutation.mutate({
      file: importFile,
      tableId: selectedTable.id
    });
  };

  return (
    <div className="h-full flex">
      {/* Tables List */}
      <div className="w-1/3 border-r border-gray-200 bg-gray-50">
        <div className="p-4 border-b border-gray-200 bg-white">
          <h2 className="text-lg font-medium text-gray-900">Data Management</h2>
          <p className="text-sm text-gray-500">Import, export, and manage table data</p>
        </div>

        <div className="overflow-y-auto h-full">
          {tables.length === 0 ? (
            <div className="p-6 text-center">
              <TableCellsIcon className="mx-auto h-12 w-12 text-gray-400" />
              <h3 className="mt-2 text-sm font-medium text-gray-900">No tables</h3>
              <p className="mt-1 text-sm text-gray-500">
                Create tables first to manage data.
              </p>
            </div>
          ) : (
            <div className="p-2">
              {tables.map((table) => (
                <div
                  key={table.id}
                  className={`
                    p-3 mb-2 rounded-lg cursor-pointer border
                    ${selectedTable?.id === table.id
                      ? 'bg-blue-50 border-blue-200'
                      : 'bg-white border-gray-200 hover:bg-gray-50'
                    }
                  `}
                  onClick={() => onTableSelect(table)}
                >
                  <div className="flex items-center justify-between">
                    <div className="flex-1 min-w-0">
                      <h3 className="text-sm font-medium text-gray-900 truncate">
                        {table.display_name}
                      </h3>
                      <p className="text-xs text-gray-500 truncate">
                        {table.name} • {table.columns.length} columns
                      </p>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>

      {/* Data View */}
      <div className="flex-1 flex flex-col">
        {selectedTable ? (
          <>
            <div className="p-4 border-b border-gray-200 bg-white">
              <div className="flex items-center justify-between">
                <div>
                  <h2 className="text-lg font-medium text-gray-900">
                    {selectedTable.display_name} Data
                  </h2>
                  <p className="text-sm text-gray-500">
                    {tableData ? `${tableData.total_rows} rows` : 'Loading...'}
                  </p>
                </div>
                <div className="flex space-x-2">
                  <button
                    onClick={() => downloadTemplate(selectedTable)}
                    className="inline-flex items-center px-3 py-2 border border-gray-300 shadow-sm text-sm font-medium rounded-md text-gray-700 bg-white hover:bg-gray-50"
                  >
                    <ArrowDownTrayIcon className="h-4 w-4 mr-2" />
                    Template
                  </button>
                  <button
                    onClick={() => setShowImportModal(true)}
                    className="inline-flex items-center px-3 py-2 border border-transparent shadow-sm text-sm font-medium rounded-md text-white bg-blue-600 hover:bg-blue-700"
                  >
                    <ArrowUpTrayIcon className="h-4 w-4 mr-2" />
                    Import Data
                  </button>
                  <button
                    className="inline-flex items-center px-3 py-2 border border-transparent shadow-sm text-sm font-medium rounded-md text-white bg-green-600 hover:bg-green-700"
                  >
                    <PlusIcon className="h-4 w-4 mr-2" />
                    Add Row
                  </button>
                </div>
              </div>
            </div>

            <div className="flex-1 overflow-auto p-4">
              {dataLoading ? (
                <div className="flex items-center justify-center h-full">
                  <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
                </div>
              ) : tableData && tableData.data && tableData.data.length > 0 ? (
                <div className="bg-white shadow overflow-hidden sm:rounded-lg">
                  <table className="min-w-full divide-y divide-gray-200">
                    <thead className="bg-gray-50">
                      <tr>
                        {selectedTable.columns
                          .sort((a, b) => a.order_index - b.order_index)
                          .map((column) => (
                            <th
                              key={column.id}
                              className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider"
                            >
                              {column.display_name}
                            </th>
                          ))}
                        <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">
                          Actions
                        </th>
                      </tr>
                    </thead>
                    <tbody className="bg-white divide-y divide-gray-200">
                      {tableData.data.map((row: any, index: number) => (
                        <tr key={index} className="hover:bg-gray-50">
                          {selectedTable.columns
                            .sort((a, b) => a.order_index - b.order_index)
                            .map((column) => (
                              <td
                                key={column.id}
                                className="px-6 py-4 whitespace-nowrap text-sm text-gray-900"
                              >
                                {row[column.name] || '-'}
                              </td>
                            ))}
                          <td className="px-6 py-4 whitespace-nowrap text-right text-sm font-medium">
                            <button className="text-blue-600 hover:text-blue-900 mr-2">
                              Edit
                            </button>
                            <button className="text-red-600 hover:text-red-900">
                              Delete
                            </button>
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              ) : (
                <div className="text-center py-12">
                  <TableCellsIcon className="mx-auto h-12 w-12 text-gray-400" />
                  <h3 className="mt-2 text-sm font-medium text-gray-900">No data</h3>
                  <p className="mt-1 text-sm text-gray-500">
                    This table doesn't have any data yet. Import data or add rows manually.
                  </p>
                  <div className="mt-6 flex justify-center space-x-3">
                    <button
                      onClick={() => setShowImportModal(true)}
                      className="inline-flex items-center px-4 py-2 border border-transparent shadow-sm text-sm font-medium rounded-md text-white bg-blue-600 hover:bg-blue-700"
                    >
                      <ArrowUpTrayIcon className="h-5 w-5 mr-2" />
                      Import Data
                    </button>
                    <button className="inline-flex items-center px-4 py-2 border border-gray-300 shadow-sm text-sm font-medium rounded-md text-gray-700 bg-white hover:bg-gray-50">
                      <PlusIcon className="h-5 w-5 mr-2" />
                      Add Row
                    </button>
                  </div>
                </div>
              )}
            </div>
          </>
        ) : (
          <div className="flex-1 flex items-center justify-center">
            <div className="text-center">
              <TableCellsIcon className="mx-auto h-12 w-12 text-gray-400" />
              <h3 className="mt-2 text-sm font-medium text-gray-900">No table selected</h3>
              <p className="mt-1 text-sm text-gray-500">
                Select a table to view and manage its data.
              </p>
            </div>
          </div>
        )}
      </div>

      {/* Import Modal */}
      {showImportModal && (
        <div className="fixed inset-0 z-50 overflow-y-auto">
          <div className="flex items-end justify-center min-h-screen pt-4 px-4 pb-20 text-center sm:block sm:p-0">
            <div className="fixed inset-0 bg-gray-500 bg-opacity-75 transition-opacity" onClick={() => setShowImportModal(false)} />

            <span className="hidden sm:inline-block sm:align-middle sm:h-screen">&#8203;</span>

            <div className="inline-block align-bottom bg-white rounded-lg text-left overflow-hidden shadow-xl transform transition-all sm:my-8 sm:align-middle sm:max-w-lg sm:w-full">
              <div className="bg-white px-4 pt-5 pb-4 sm:p-6 sm:pb-4">
                <div className="flex items-center justify-between mb-4">
                  <h3 className="text-lg leading-6 font-medium text-gray-900">
                    Import Data to {selectedTable?.display_name}
                  </h3>
                </div>

                <div className="space-y-4">
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">
                      Select Excel File
                    </label>
                    <div className="mt-1 flex justify-center px-6 pt-5 pb-6 border-2 border-gray-300 border-dashed rounded-md">
                      <div className="space-y-1 text-center">
                        <DocumentArrowUpIcon className="mx-auto h-12 w-12 text-gray-400" />
                        <div className="flex text-sm text-gray-600">
                          <label
                            htmlFor="file-upload"
                            className="relative cursor-pointer bg-white rounded-md font-medium text-blue-600 hover:text-blue-500 focus-within:outline-none focus-within:ring-2 focus-within:ring-offset-2 focus-within:ring-blue-500"
                          >
                            <span>Upload a file</span>
                            <input
                              id="file-upload"
                              name="file-upload"
                              type="file"
                              accept=".xlsx,.xls,.csv"
                              className="sr-only"
                              onChange={(e) => setImportFile(e.target.files?.[0] || null)}
                            />
                          </label>
                          <p className="pl-1">or drag and drop</p>
                        </div>
                        <p className="text-xs text-gray-500">
                          Excel (.xlsx, .xls) or CSV files up to 10MB
                        </p>
                      </div>
                    </div>
                    {importFile && (
                      <p className="mt-2 text-sm text-gray-600">
                        Selected: {importFile.name}
                      </p>
                    )}
                  </div>
                </div>
              </div>

              <div className="bg-gray-50 px-4 py-3 sm:px-6 sm:flex sm:flex-row-reverse">
                <button
                  onClick={handleImport}
                  disabled={!importFile || importDataMutation.isPending}
                  className="w-full inline-flex justify-center rounded-md border border-transparent shadow-sm px-4 py-2 bg-blue-600 text-base font-medium text-white hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 sm:ml-3 sm:w-auto sm:text-sm disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  {importDataMutation.isPending ? 'Importing...' : 'Import Data'}
                </button>
                <button
                  onClick={() => {
                    setShowImportModal(false);
                    setImportFile(null);
                  }}
                  className="mt-3 w-full inline-flex justify-center rounded-md border border-gray-300 shadow-sm px-4 py-2 bg-white text-base font-medium text-gray-700 hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 sm:mt-0 sm:ml-3 sm:w-auto sm:text-sm"
                >
                  Cancel
                </button>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default DataManager;
