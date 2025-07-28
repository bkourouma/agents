import React, { useState } from 'react';
import { useMutation, useQuery } from '@tanstack/react-query';
import { toast } from 'react-hot-toast';
import {
  ChatBubbleLeftRightIcon,
  PaperAirplaneIcon,
  ClockIcon,
  HeartIcon,
  TableCellsIcon,
  CodeBracketIcon,
  DocumentTextIcon
} from '@heroicons/react/24/outline';
import { HeartIcon as HeartIconSolid } from '@heroicons/react/24/solid';
import { apiClient } from '../../lib/api';

interface DatabaseTable {
  id: number;
  name: string;
  display_name: string;
  description?: string;
  columns: any[];
}

interface DatabaseSchema {
  tables: DatabaseTable[];
  total_tables: number;
  total_columns: number;
}

interface QueryResult {
  success: boolean;
  data?: any[];
  columns?: string[];
  row_count: number;
  execution_time_ms: number;
  sql?: string;
  error?: string;
  format: string;
}

interface QueryHistoryItem {
  id: number;
  natural_language_query: string;
  generated_sql?: string;
  execution_status: string;
  error_message?: string;
  result_count?: number;
  execution_time_ms?: number;
  created_at: string;
  is_favorite: boolean;
  result_preview?: any;
}

interface NaturalLanguageQueryProps {
  tables: DatabaseTable[];
  schema?: DatabaseSchema;
}

const NaturalLanguageQuery: React.FC<NaturalLanguageQueryProps> = ({ tables, schema }) => {
  const [query, setQuery] = useState('');
  const [outputFormat, setOutputFormat] = useState<'json' | 'text' | 'table'>('table');
  const [currentResult, setCurrentResult] = useState<QueryResult | null>(null);
  const [showSQL, setShowSQL] = useState(false);

  // Fetch query history
  const { data: queryHistory = [], refetch: refetchHistory } = useQuery({
    queryKey: ['query-history'],
    queryFn: async () => {
      return await apiClient.getQueryHistory(1, 10);
    },
  });

  // Execute query mutation
  const executeQueryMutation = useMutation({
    mutationFn: async (queryData: { query: string; output_format: string }) => {
      return await apiClient.processNaturalLanguageQuery(queryData);
    },
    onSuccess: (data: QueryResult) => {
      setCurrentResult(data);
      refetchHistory();
      if (data.success) {
        toast.success(`Query executed successfully! Found ${data.row_count} rows.`);
      } else {
        toast.error(data.error || 'Query failed');
      }
    },
    onError: (error: any) => {
      toast.error(error.response?.data?.detail || 'Failed to execute query');
    },
  });

  // Toggle favorite mutation
  const toggleFavoriteMutation = useMutation({
    mutationFn: async (queryId: number) => {
      return await apiClient.toggleQueryFavorite(queryId);
    },
    onSuccess: () => {
      refetchHistory();
    },
    onError: (error: any) => {
      toast.error(error.response?.data?.detail || 'Failed to update favorite');
    },
  });

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!query.trim()) {
      toast.error('Please enter a query');
      return;
    }

    executeQueryMutation.mutate({
      query: query.trim(),
      output_format: outputFormat
    });
  };

  const handleHistoryItemClick = (item: QueryHistoryItem) => {
    setQuery(item.natural_language_query);
    if (item.result_preview) {
      setCurrentResult({
        success: item.execution_status === 'success',
        data: item.result_preview.data || [],
        columns: item.result_preview.data?.[0] ? Object.keys(item.result_preview.data[0]) : [],
        row_count: item.result_count || 0,
        execution_time_ms: item.execution_time_ms || 0,
        sql: item.generated_sql,
        error: item.error_message,
        format: 'table'
      });
    }
  };

  const renderResult = () => {
    if (!currentResult) return null;

    if (!currentResult.success) {
      return (
        <div className="bg-red-50 border border-red-200 rounded-lg p-4">
          <div className="flex items-center">
            <div className="flex-shrink-0">
              <svg className="h-5 w-5 text-red-400" viewBox="0 0 20 20" fill="currentColor">
                <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z" clipRule="evenodd" />
              </svg>
            </div>
            <div className="ml-3">
              <h3 className="text-sm font-medium text-red-800">Query Error</h3>
              <div className="mt-2 text-sm text-red-700">
                {currentResult.error}
              </div>
            </div>
          </div>
        </div>
      );
    }

    return (
      <div className="bg-white border border-gray-200 rounded-lg overflow-hidden">
        {/* Result Header */}
        <div className="bg-gray-50 px-4 py-3 border-b border-gray-200">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-4">
              <span className="text-sm font-medium text-gray-900">
                {currentResult.row_count} rows
              </span>
              <span className="text-sm text-gray-500">
                {currentResult.execution_time_ms}ms
              </span>
              {currentResult.sql && (
                <button
                  onClick={() => setShowSQL(!showSQL)}
                  className="inline-flex items-center text-sm text-blue-600 hover:text-blue-800"
                >
                  <CodeBracketIcon className="h-4 w-4 mr-1" />
                  {showSQL ? 'Hide SQL' : 'Show SQL'}
                </button>
              )}
            </div>
            <div className="flex items-center space-x-2">
              <select
                value={outputFormat}
                onChange={(e) => setOutputFormat(e.target.value as any)}
                className="text-sm border border-gray-300 rounded px-2 py-1"
              >
                <option value="table">Table</option>
                <option value="json">JSON</option>
                <option value="text">Text</option>
              </select>
            </div>
          </div>
        </div>

        {/* SQL Display */}
        {showSQL && currentResult.sql && (
          <div className="bg-gray-900 text-gray-100 p-4 text-sm font-mono">
            <pre className="whitespace-pre-wrap">{currentResult.sql}</pre>
          </div>
        )}

        {/* Result Content */}
        <div className="p-4">
          {currentResult.data && currentResult.data.length > 0 ? (
            outputFormat === 'table' ? (
              <div className="overflow-x-auto">
                <table className="min-w-full divide-y divide-gray-200">
                  <thead className="bg-gray-50">
                    <tr>
                      {currentResult.columns?.map((column) => (
                        <th
                          key={column}
                          className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider"
                        >
                          {column}
                        </th>
                      ))}
                    </tr>
                  </thead>
                  <tbody className="bg-white divide-y divide-gray-200">
                    {currentResult.data.slice(0, 100).map((row, index) => (
                      <tr key={index} className="hover:bg-gray-50">
                        {currentResult.columns?.map((column) => (
                          <td
                            key={column}
                            className="px-6 py-4 whitespace-nowrap text-sm text-gray-900"
                          >
                            {row[column] !== null && row[column] !== undefined
                              ? String(row[column])
                              : '-'}
                          </td>
                        ))}
                      </tr>
                    ))}
                  </tbody>
                </table>
                {currentResult.data.length > 100 && (
                  <div className="text-center py-2 text-sm text-gray-500">
                    Showing first 100 rows of {currentResult.row_count} total
                  </div>
                )}
              </div>
            ) : outputFormat === 'json' ? (
              <pre className="bg-gray-100 p-4 rounded text-sm overflow-x-auto">
                {JSON.stringify(currentResult.data, null, 2)}
              </pre>
            ) : (
              <div className="space-y-2">
                {currentResult.data.slice(0, 20).map((row, index) => (
                  <div key={index} className="text-sm">
                    {Object.entries(row).map(([key, value]) => (
                      <span key={key} className="mr-4">
                        <strong>{key}:</strong> {String(value)}
                      </span>
                    ))}
                  </div>
                ))}
              </div>
            )
          ) : (
            <div className="text-center py-8 text-gray-500">
              No data returned
            </div>
          )}
        </div>
      </div>
    );
  };

  return (
    <div className="h-full flex">
      {/* Query Interface */}
      <div className="flex-1 flex flex-col">
        {/* Header */}
        <div className="p-6 border-b border-gray-200 bg-white">
          <div className="flex items-center">
            <ChatBubbleLeftRightIcon className="h-8 w-8 text-blue-600 mr-3" />
            <div>
              <h2 className="text-xl font-bold text-gray-900">Natural Language Query</h2>
              <p className="text-gray-600">
                Ask questions about your data in plain English
              </p>
            </div>
          </div>
        </div>

        {/* Query Input */}
        <div className="p-6 border-b border-gray-200 bg-white">
          <form onSubmit={handleSubmit} className="space-y-4">
            <div>
              <label htmlFor="query" className="block text-sm font-medium text-gray-700 mb-2">
                Your Question
              </label>
              <div className="relative">
                <textarea
                  id="query"
                  rows={3}
                  value={query}
                  onChange={(e) => setQuery(e.target.value)}
                  className="w-full border border-gray-300 rounded-lg px-4 py-3 pr-12 shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500 resize-none"
                  placeholder="e.g., Show me all customers from New York, or What's the total revenue this month?"
                />
                <button
                  type="submit"
                  disabled={executeQueryMutation.isPending || !query.trim()}
                  className="absolute bottom-3 right-3 inline-flex items-center p-2 border border-transparent rounded-md shadow-sm text-white bg-blue-600 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  {executeQueryMutation.isPending ? (
                    <ClockIcon className="h-5 w-5 animate-spin" />
                  ) : (
                    <PaperAirplaneIcon className="h-5 w-5" />
                  )}
                </button>
              </div>
            </div>

            <div className="flex items-center justify-between">
              <div className="flex items-center space-x-4">
                <label className="text-sm font-medium text-gray-700">Output Format:</label>
                <select
                  value={outputFormat}
                  onChange={(e) => setOutputFormat(e.target.value as any)}
                  className="border border-gray-300 rounded px-3 py-1 text-sm"
                >
                  <option value="table">Table</option>
                  <option value="json">JSON</option>
                  <option value="text">Text</option>
                </select>
              </div>
              {schema && (
                <div className="text-sm text-gray-500">
                  {schema.total_tables} tables • {schema.total_columns} columns available
                </div>
              )}
            </div>
          </form>
        </div>

        {/* Results */}
        <div className="flex-1 overflow-auto p-6">
          {executeQueryMutation.isPending ? (
            <div className="flex items-center justify-center h-full">
              <div className="text-center">
                <ClockIcon className="mx-auto h-8 w-8 text-blue-600 animate-spin" />
                <p className="mt-2 text-sm text-gray-600">Processing your query...</p>
              </div>
            </div>
          ) : currentResult ? (
            renderResult()
          ) : (
            <div className="flex items-center justify-center h-full">
              <div className="text-center">
                <ChatBubbleLeftRightIcon className="mx-auto h-12 w-12 text-gray-400" />
                <h3 className="mt-2 text-sm font-medium text-gray-900">Ready for your question</h3>
                <p className="mt-1 text-sm text-gray-500">
                  Type a natural language question about your data above.
                </p>
                {tables.length === 0 && (
                  <p className="mt-2 text-xs text-red-500">
                    Note: Create and train on database tables first for best results.
                  </p>
                )}
              </div>
            </div>
          )}
        </div>
      </div>

      {/* Query History Sidebar */}
      <div className="w-80 border-l border-gray-200 bg-gray-50">
        <div className="p-4 border-b border-gray-200 bg-white">
          <h3 className="text-lg font-medium text-gray-900">Query History</h3>
          <p className="text-sm text-gray-500">Recent queries and results</p>
        </div>

        <div className="overflow-y-auto h-full">
          {queryHistory.length === 0 ? (
            <div className="p-6 text-center">
              <ClockIcon className="mx-auto h-8 w-8 text-gray-400" />
              <p className="mt-2 text-sm text-gray-500">No queries yet</p>
              <p className="text-xs text-gray-400">
                Your query history will appear here
              </p>
            </div>
          ) : (
            <div className="p-2">
              {queryHistory.map((item: QueryHistoryItem) => (
                <div
                  key={item.id}
                  className="mb-2 p-3 bg-white rounded-lg border border-gray-200 cursor-pointer hover:bg-gray-50"
                  onClick={() => handleHistoryItemClick(item)}
                >
                  <div className="flex items-start justify-between">
                    <div className="flex-1 min-w-0">
                      <p className="text-sm text-gray-900 line-clamp-2">
                        {item.natural_language_query}
                      </p>
                      <div className="mt-1 flex items-center text-xs text-gray-500">
                        <span
                          className={`inline-flex items-center px-2 py-0.5 rounded text-xs font-medium ${
                            item.execution_status === 'success'
                              ? 'bg-green-100 text-green-800'
                              : 'bg-red-100 text-red-800'
                          }`}
                        >
                          {item.execution_status}
                        </span>
                        {item.result_count !== undefined && (
                          <span className="ml-2">{item.result_count} rows</span>
                        )}
                        <span className="ml-2">
                          {new Date(item.created_at).toLocaleDateString()}
                        </span>
                      </div>
                    </div>
                    <button
                      onClick={(e) => {
                        e.stopPropagation();
                        toggleFavoriteMutation.mutate(item.id);
                      }}
                      className="ml-2 text-gray-400 hover:text-red-500"
                    >
                      {item.is_favorite ? (
                        <HeartIconSolid className="h-4 w-4 text-red-500" />
                      ) : (
                        <HeartIcon className="h-4 w-4" />
                      )}
                    </button>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default NaturalLanguageQuery;
