import React, { useState, useEffect } from 'react';
import { useMutation } from '@tanstack/react-query';
import { toast } from 'react-hot-toast';
import { XMarkIcon } from '@heroicons/react/24/outline';
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
  columns: any[];
}

interface TableCreatorProps {
  table?: DatabaseTable | null;
  onClose: () => void;
  onSuccess: () => void;
}

interface TableFormData {
  name: string;
  display_name: string;
  description: string;
  metadata_config: Record<string, any>;
}

const TableCreator: React.FC<TableCreatorProps> = ({ table, onClose, onSuccess }) => {
  const [formData, setFormData] = useState<TableFormData>({
    name: '',
    display_name: '',
    description: '',
    metadata_config: {}
  });

  const [errors, setErrors] = useState<Record<string, string>>({});

  // Initialize form data when editing
  useEffect(() => {
    if (table) {
      setFormData({
        name: table.name,
        display_name: table.display_name,
        description: table.description || '',
        metadata_config: table.metadata_config || {}
      });
    }
  }, [table]);

  // Create table mutation
  const createTableMutation = useMutation({
    mutationFn: async (data: TableFormData) => {
      if (table) {
        // Update existing table
        return await apiClient.updateDatabaseTable(table.id, {
          display_name: data.display_name,
          description: data.description || undefined,
          metadata_config: data.metadata_config
        });
      } else {
        // Create new table
        return await apiClient.createDatabaseTable(data);
      }
    },
    onSuccess: () => {
      toast.success(table ? 'Table updated successfully' : 'Table created successfully');
      onSuccess();
    },
    onError: (error: any) => {
      const errorMessage = error.response?.data?.detail || 'Failed to save table';
      toast.error(errorMessage);
      
      // Handle validation errors
      if (error.response?.status === 422) {
        const validationErrors: Record<string, string> = {};
        error.response.data.detail?.forEach((err: any) => {
          if (err.loc && err.loc.length > 1) {
            validationErrors[err.loc[1]] = err.msg;
          }
        });
        setErrors(validationErrors);
      }
    },
  });

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    setErrors({});

    // Basic validation
    const newErrors: Record<string, string> = {};
    
    if (!formData.display_name.trim()) {
      newErrors.display_name = 'Display name is required';
    }
    
    if (!table && !formData.name.trim()) {
      newErrors.name = 'Table name is required';
    }
    
    if (!table && formData.name && !/^[a-zA-Z][a-zA-Z0-9_]*$/.test(formData.name)) {
      newErrors.name = 'Table name must start with a letter and contain only letters, numbers, and underscores';
    }

    if (Object.keys(newErrors).length > 0) {
      setErrors(newErrors);
      return;
    }

    createTableMutation.mutate(formData);
  };

  const handleInputChange = (field: keyof TableFormData, value: string) => {
    setFormData(prev => ({ ...prev, [field]: value }));
    
    // Auto-generate table name from display name (only for new tables)
    if (!table && field === 'display_name') {
      const tableName = value
        .toLowerCase()
        .replace(/[^a-z0-9\s]/g, '')
        .replace(/\s+/g, '_')
        .replace(/^[0-9]/, 'table_$&');
      
      setFormData(prev => ({ ...prev, name: tableName }));
    }
    
    // Clear error when user starts typing
    if (errors[field]) {
      setErrors(prev => ({ ...prev, [field]: '' }));
    }
  };

  return (
    <div className="fixed inset-0 z-50 overflow-y-auto">
      <div className="flex items-end justify-center min-h-screen pt-4 px-4 pb-20 text-center sm:block sm:p-0">
        <div className="fixed inset-0 bg-gray-500 bg-opacity-75 transition-opacity" onClick={onClose} />

        <span className="hidden sm:inline-block sm:align-middle sm:h-screen">&#8203;</span>

        <div className="inline-block align-bottom bg-white rounded-lg text-left overflow-hidden shadow-xl transform transition-all sm:my-8 sm:align-middle sm:max-w-lg sm:w-full">
          <form onSubmit={handleSubmit}>
            <div className="bg-white px-4 pt-5 pb-4 sm:p-6 sm:pb-4">
              <div className="flex items-center justify-between mb-4">
                <h3 className="text-lg leading-6 font-medium text-gray-900">
                  {table ? 'Edit Table' : 'Create New Table'}
                </h3>
                <button
                  type="button"
                  onClick={onClose}
                  className="text-gray-400 hover:text-gray-600"
                >
                  <XMarkIcon className="h-6 w-6" />
                </button>
              </div>

              <div className="space-y-4">
                {/* Display Name */}
                <div>
                  <label htmlFor="display_name" className="block text-sm font-medium text-gray-700">
                    Display Name *
                  </label>
                  <input
                    type="text"
                    id="display_name"
                    value={formData.display_name}
                    onChange={(e) => handleInputChange('display_name', e.target.value)}
                    className={`mt-1 block w-full border rounded-md px-3 py-2 shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500 sm:text-sm ${
                      errors.display_name ? 'border-red-300' : 'border-gray-300'
                    }`}
                    placeholder="e.g., Customer Orders"
                  />
                  {errors.display_name && (
                    <p className="mt-1 text-sm text-red-600">{errors.display_name}</p>
                  )}
                </div>

                {/* Table Name (only for new tables) */}
                {!table && (
                  <div>
                    <label htmlFor="name" className="block text-sm font-medium text-gray-700">
                      Table Name *
                    </label>
                    <input
                      type="text"
                      id="name"
                      value={formData.name}
                      onChange={(e) => handleInputChange('name', e.target.value)}
                      className={`mt-1 block w-full border rounded-md px-3 py-2 shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500 sm:text-sm ${
                        errors.name ? 'border-red-300' : 'border-gray-300'
                      }`}
                      placeholder="e.g., customer_orders"
                    />
                    {errors.name && (
                      <p className="mt-1 text-sm text-red-600">{errors.name}</p>
                    )}
                    <p className="mt-1 text-xs text-gray-500">
                      Database identifier (auto-generated from display name)
                    </p>
                  </div>
                )}

                {/* Description */}
                <div>
                  <label htmlFor="description" className="block text-sm font-medium text-gray-700">
                    Description
                  </label>
                  <textarea
                    id="description"
                    rows={3}
                    value={formData.description}
                    onChange={(e) => handleInputChange('description', e.target.value)}
                    className="mt-1 block w-full border border-gray-300 rounded-md px-3 py-2 shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500 sm:text-sm"
                    placeholder="Optional description of what this table stores..."
                  />
                </div>

                {/* Metadata Config (Advanced) */}
                <div>
                  <label className="block text-sm font-medium text-gray-700">
                    Advanced Configuration
                  </label>
                  <div className="mt-1 text-xs text-gray-500">
                    Additional table metadata and configuration options will be available here.
                  </div>
                </div>
              </div>
            </div>

            <div className="bg-gray-50 px-4 py-3 sm:px-6 sm:flex sm:flex-row-reverse">
              <button
                type="submit"
                disabled={createTableMutation.isPending}
                className="w-full inline-flex justify-center rounded-md border border-transparent shadow-sm px-4 py-2 bg-blue-600 text-base font-medium text-white hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 sm:ml-3 sm:w-auto sm:text-sm disabled:opacity-50 disabled:cursor-not-allowed"
              >
                {createTableMutation.isPending ? (
                  <>
                    <svg className="animate-spin -ml-1 mr-3 h-5 w-5 text-white" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                      <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                      <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                    </svg>
                    {table ? 'Updating...' : 'Creating...'}
                  </>
                ) : (
                  table ? 'Update Table' : 'Create Table'
                )}
              </button>
              <button
                type="button"
                onClick={onClose}
                className="mt-3 w-full inline-flex justify-center rounded-md border border-gray-300 shadow-sm px-4 py-2 bg-white text-base font-medium text-gray-700 hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 sm:mt-0 sm:ml-3 sm:w-auto sm:text-sm"
              >
                Cancel
              </button>
            </div>
          </form>
        </div>
      </div>
    </div>
  );
};

export default TableCreator;
