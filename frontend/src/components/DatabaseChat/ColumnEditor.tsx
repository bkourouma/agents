import React, { useState } from 'react';
import { useMutation } from '@tanstack/react-query';
import { toast } from 'react-hot-toast';
import { XMarkIcon } from '@heroicons/react/24/outline';
import { apiClient } from '../../lib/api';

interface DatabaseTable {
  id: number;
  name: string;
  display_name: string;
  description?: string;
  columns: any[];
}

interface ColumnEditorProps {
  table: DatabaseTable;
  onClose: () => void;
}

interface ColumnFormData {
  name: string;
  display_name: string;
  data_type: string;
  max_length?: number;
  precision?: number;
  scale?: number;
  is_nullable: boolean;
  is_primary_key: boolean;
  is_unique: boolean;
  default_value: string;
  description: string;
  order_index: number;
}

const DATA_TYPES = [
  { value: 'INTEGER', label: 'Integer' },
  { value: 'VARCHAR', label: 'Text (VARCHAR)' },
  { value: 'TEXT', label: 'Long Text' },
  { value: 'BOOLEAN', label: 'Boolean' },
  { value: 'DATETIME', label: 'Date & Time' },
  { value: 'DATE', label: 'Date' },
  { value: 'TIME', label: 'Time' },
  { value: 'DECIMAL', label: 'Decimal' },
  { value: 'FLOAT', label: 'Float' },
  { value: 'JSON', label: 'JSON' }
];

const ColumnEditor: React.FC<ColumnEditorProps> = ({ table, onClose }) => {
  const [formData, setFormData] = useState<ColumnFormData>({
    name: '',
    display_name: '',
    data_type: 'VARCHAR',
    max_length: 255,
    precision: undefined,
    scale: undefined,
    is_nullable: true,
    is_primary_key: false,
    is_unique: false,
    default_value: '',
    description: '',
    order_index: table.columns.length
  });

  const [errors, setErrors] = useState<Record<string, string>>({});

  // Create column mutation
  const createColumnMutation = useMutation({
    mutationFn: async (data: ColumnFormData) => {
      return await apiClient.createTableColumn(table.id, data);
    },
    onSuccess: () => {
      toast.success('Column added successfully');
      onClose();
    },
    onError: (error: any) => {
      const errorMessage = error.response?.data?.detail || 'Failed to add column';
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
    
    if (!formData.name.trim()) {
      newErrors.name = 'Column name is required';
    }
    
    if (formData.name && !/^[a-zA-Z][a-zA-Z0-9_]*$/.test(formData.name)) {
      newErrors.name = 'Column name must start with a letter and contain only letters, numbers, and underscores';
    }

    if (formData.data_type === 'VARCHAR' && (!formData.max_length || formData.max_length < 1)) {
      newErrors.max_length = 'Max length is required for VARCHAR columns';
    }

    if (formData.data_type === 'DECIMAL' && (!formData.precision || formData.precision < 1)) {
      newErrors.precision = 'Precision is required for DECIMAL columns';
    }

    if (Object.keys(newErrors).length > 0) {
      setErrors(newErrors);
      return;
    }

    // Clean up data based on type
    const cleanData = { ...formData };
    if (formData.data_type !== 'VARCHAR') {
      cleanData.max_length = undefined;
    }
    if (formData.data_type !== 'DECIMAL') {
      cleanData.precision = undefined;
      cleanData.scale = undefined;
    }
    if (!cleanData.default_value.trim()) {
      cleanData.default_value = '';
    }

    createColumnMutation.mutate(cleanData);
  };

  const handleInputChange = (field: keyof ColumnFormData, value: any) => {
    setFormData(prev => ({ ...prev, [field]: value }));
    
    // Auto-generate column name from display name
    if (field === 'display_name') {
      const columnName = value
        .toLowerCase()
        .replace(/[^a-z0-9\s]/g, '')
        .replace(/\s+/g, '_')
        .replace(/^[0-9]/, 'col_$&');
      
      setFormData(prev => ({ ...prev, name: columnName }));
    }
    
    // Clear error when user starts typing
    if (errors[field]) {
      setErrors(prev => ({ ...prev, [field]: '' }));
    }
  };

  const requiresLength = formData.data_type === 'VARCHAR';
  const requiresPrecision = formData.data_type === 'DECIMAL';

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
                  Add Column to {table.display_name}
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
                    placeholder="e.g., Customer Name"
                  />
                  {errors.display_name && (
                    <p className="mt-1 text-sm text-red-600">{errors.display_name}</p>
                  )}
                </div>

                {/* Column Name */}
                <div>
                  <label htmlFor="name" className="block text-sm font-medium text-gray-700">
                    Column Name *
                  </label>
                  <input
                    type="text"
                    id="name"
                    value={formData.name}
                    onChange={(e) => handleInputChange('name', e.target.value)}
                    className={`mt-1 block w-full border rounded-md px-3 py-2 shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500 sm:text-sm ${
                      errors.name ? 'border-red-300' : 'border-gray-300'
                    }`}
                    placeholder="e.g., customer_name"
                  />
                  {errors.name && (
                    <p className="mt-1 text-sm text-red-600">{errors.name}</p>
                  )}
                </div>

                {/* Data Type */}
                <div>
                  <label htmlFor="data_type" className="block text-sm font-medium text-gray-700">
                    Data Type *
                  </label>
                  <select
                    id="data_type"
                    value={formData.data_type}
                    onChange={(e) => handleInputChange('data_type', e.target.value)}
                    className="mt-1 block w-full border border-gray-300 rounded-md px-3 py-2 shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500 sm:text-sm"
                  >
                    {DATA_TYPES.map((type) => (
                      <option key={type.value} value={type.value}>
                        {type.label}
                      </option>
                    ))}
                  </select>
                </div>

                {/* Length/Precision */}
                {requiresLength && (
                  <div>
                    <label htmlFor="max_length" className="block text-sm font-medium text-gray-700">
                      Max Length *
                    </label>
                    <input
                      type="number"
                      id="max_length"
                      value={formData.max_length || ''}
                      onChange={(e) => handleInputChange('max_length', parseInt(e.target.value) || undefined)}
                      className={`mt-1 block w-full border rounded-md px-3 py-2 shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500 sm:text-sm ${
                        errors.max_length ? 'border-red-300' : 'border-gray-300'
                      }`}
                      placeholder="255"
                      min="1"
                      max="65535"
                    />
                    {errors.max_length && (
                      <p className="mt-1 text-sm text-red-600">{errors.max_length}</p>
                    )}
                  </div>
                )}

                {requiresPrecision && (
                  <div className="grid grid-cols-2 gap-4">
                    <div>
                      <label htmlFor="precision" className="block text-sm font-medium text-gray-700">
                        Precision *
                      </label>
                      <input
                        type="number"
                        id="precision"
                        value={formData.precision || ''}
                        onChange={(e) => handleInputChange('precision', parseInt(e.target.value) || undefined)}
                        className={`mt-1 block w-full border rounded-md px-3 py-2 shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500 sm:text-sm ${
                          errors.precision ? 'border-red-300' : 'border-gray-300'
                        }`}
                        placeholder="10"
                        min="1"
                        max="65"
                      />
                      {errors.precision && (
                        <p className="mt-1 text-sm text-red-600">{errors.precision}</p>
                      )}
                    </div>
                    <div>
                      <label htmlFor="scale" className="block text-sm font-medium text-gray-700">
                        Scale
                      </label>
                      <input
                        type="number"
                        id="scale"
                        value={formData.scale || ''}
                        onChange={(e) => handleInputChange('scale', parseInt(e.target.value) || undefined)}
                        className="mt-1 block w-full border border-gray-300 rounded-md px-3 py-2 shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500 sm:text-sm"
                        placeholder="2"
                        min="0"
                        max="30"
                      />
                    </div>
                  </div>
                )}

                {/* Constraints */}
                <div className="space-y-2">
                  <label className="block text-sm font-medium text-gray-700">Constraints</label>
                  <div className="space-y-2">
                    <label className="flex items-center">
                      <input
                        type="checkbox"
                        checked={formData.is_primary_key}
                        onChange={(e) => handleInputChange('is_primary_key', e.target.checked)}
                        className="rounded border-gray-300 text-blue-600 shadow-sm focus:border-blue-300 focus:ring focus:ring-blue-200 focus:ring-opacity-50"
                      />
                      <span className="ml-2 text-sm text-gray-700">Primary Key</span>
                    </label>
                    <label className="flex items-center">
                      <input
                        type="checkbox"
                        checked={formData.is_unique}
                        onChange={(e) => handleInputChange('is_unique', e.target.checked)}
                        className="rounded border-gray-300 text-blue-600 shadow-sm focus:border-blue-300 focus:ring focus:ring-blue-200 focus:ring-opacity-50"
                      />
                      <span className="ml-2 text-sm text-gray-700">Unique</span>
                    </label>
                    <label className="flex items-center">
                      <input
                        type="checkbox"
                        checked={!formData.is_nullable}
                        onChange={(e) => handleInputChange('is_nullable', !e.target.checked)}
                        className="rounded border-gray-300 text-blue-600 shadow-sm focus:border-blue-300 focus:ring focus:ring-blue-200 focus:ring-opacity-50"
                      />
                      <span className="ml-2 text-sm text-gray-700">Required (NOT NULL)</span>
                    </label>
                  </div>
                </div>

                {/* Default Value */}
                <div>
                  <label htmlFor="default_value" className="block text-sm font-medium text-gray-700">
                    Default Value
                  </label>
                  <input
                    type="text"
                    id="default_value"
                    value={formData.default_value}
                    onChange={(e) => handleInputChange('default_value', e.target.value)}
                    className="mt-1 block w-full border border-gray-300 rounded-md px-3 py-2 shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500 sm:text-sm"
                    placeholder="Optional default value"
                  />
                </div>

                {/* Description */}
                <div>
                  <label htmlFor="description" className="block text-sm font-medium text-gray-700">
                    Description
                  </label>
                  <textarea
                    id="description"
                    rows={2}
                    value={formData.description}
                    onChange={(e) => handleInputChange('description', e.target.value)}
                    className="mt-1 block w-full border border-gray-300 rounded-md px-3 py-2 shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500 sm:text-sm"
                    placeholder="Optional description of this column"
                  />
                </div>
              </div>
            </div>

            <div className="bg-gray-50 px-4 py-3 sm:px-6 sm:flex sm:flex-row-reverse">
              <button
                type="submit"
                disabled={createColumnMutation.isPending}
                className="w-full inline-flex justify-center rounded-md border border-transparent shadow-sm px-4 py-2 bg-blue-600 text-base font-medium text-white hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 sm:ml-3 sm:w-auto sm:text-sm disabled:opacity-50 disabled:cursor-not-allowed"
              >
                {createColumnMutation.isPending ? (
                  <>
                    <svg className="animate-spin -ml-1 mr-3 h-5 w-5 text-white" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                      <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                      <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                    </svg>
                    Adding...
                  </>
                ) : (
                  'Add Column'
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

export default ColumnEditor;
