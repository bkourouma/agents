import React, { useState, useEffect } from 'react';
import { useQuery } from '@tanstack/react-query';
import {
  EyeIcon,
  EyeSlashIcon,
  CheckCircleIcon,
  ExclamationCircleIcon,
  ClockIcon,
  InformationCircleIcon
} from '@heroicons/react/24/outline';
import { apiClient } from '../../lib/api';

interface ConnectionConfig {
  host: string;
  port: number;
  database: string;
  username: string;
  password: string;
  ssl_mode?: string;
  connection_timeout?: number;
}

interface ConnectionStringBuilderProps {
  databaseType: string;
  config: ConnectionConfig;
  onConfigChange: (config: ConnectionConfig) => void;
  onConnectionStringChange: (connectionString: string) => void;
  manualConnectionString?: string;
  onManualModeChange: (isManual: boolean) => void;
  isManualMode: boolean;
  onTestConnection?: () => Promise<{ success: boolean; message: string; response_time_ms?: number }>;
}

const ConnectionStringBuilder: React.FC<ConnectionStringBuilderProps> = ({
  databaseType,
  config,
  onConfigChange,
  onConnectionStringChange,
  manualConnectionString = '',
  onManualModeChange,
  isManualMode,
  onTestConnection
}) => {
  const [showPassword, setShowPassword] = useState(false);
  const [testResult, setTestResult] = useState<{ success: boolean; message: string; response_time_ms?: number } | null>(null);
  const [isTesting, setIsTesting] = useState(false);

  // Fetch connection string template for the current provider
  const { data: templateData, isLoading: templateLoading } = useQuery({
    queryKey: ['connection-template', databaseType],
    queryFn: () => apiClient.getConnectionStringTemplate(databaseType),
    enabled: !!databaseType
  });

  // Default ports for different database types
  const defaultPorts = {
    postgresql: 5432,
    mysql: 3306,
    sqlserver: 1433,
    oracle: 1521,
    sqlite: 0
  };

  // SSL modes for PostgreSQL
  const sslModes = ['disable', 'allow', 'prefer', 'require', 'verify-ca', 'verify-full'];

  useEffect(() => {
    if (!isManualMode) {
      const connectionString = buildConnectionString();
      onConnectionStringChange(connectionString);
    }
  }, [config, databaseType, isManualMode]);

  const buildConnectionString = (): string => {
    const { host, port, database, username, password } = config;
    
    switch (databaseType) {
      case 'postgresql':
        let pgString = `postgresql://${username}:${password}@${host}:${port}/${database}`;
        if (config.ssl_mode && config.ssl_mode !== 'disable') {
          pgString += `?sslmode=${config.ssl_mode}`;
        }
        return pgString;
      
      case 'mysql':
        return `mysql://${username}:${password}@${host}:${port}/${database}`;
      
      case 'sqlserver':
        return `mssql+pyodbc://${username}:${password}@${host}:${port}/${database}?driver=ODBC+Driver+17+for+SQL+Server`;
      
      case 'oracle':
        return `oracle+cx_oracle://${username}:${password}@${host}:${port}/${database}`;
      
      case 'sqlite':
        return `sqlite:///${database}`;
      
      default:
        return '';
    }
  };

  const handleConfigChange = (field: keyof ConnectionConfig, value: string | number) => {
    const newConfig = { ...config, [field]: value };
    onConfigChange(newConfig);
  };

  const handleTestConnection = async () => {
    setIsTesting(true);
    setTestResult(null);

    try {
      let connectionString = '';
      if (isManualMode) {
        connectionString = manualConnectionString;
      } else {
        connectionString = buildConnectionString();
      }

      if (!connectionString) {
        setTestResult({
          success: false,
          message: 'Please provide a connection string or fill in the connection parameters'
        });
        return;
      }

      // Use the enhanced API to test connection
      const result = await apiClient.testConnectionString(databaseType, connectionString);
      setTestResult(result);

      // If there's an onTestConnection callback, call it too
      if (onTestConnection) {
        await onTestConnection();
      }
    } catch (error: any) {
      setTestResult({
        success: false,
        message: 'Test failed: ' + (error?.response?.data?.detail || error.message || 'Unknown error')
      });
    } finally {
      setIsTesting(false);
    }
  };

  const renderFormFields = () => {
    if (databaseType === 'sqlite') {
      return (
        <div className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Chemin de la base de données
            </label>
            <input
              type="text"
              value={config.database}
              onChange={(e) => handleConfigChange('database', e.target.value)}
              placeholder="/path/to/database.db"
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
          </div>
        </div>
      );
    }

    return (
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">
            Hôte
          </label>
          <input
            type="text"
            value={config.host}
            onChange={(e) => handleConfigChange('host', e.target.value)}
            placeholder="localhost"
            className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
          />
        </div>

        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">
            Port
          </label>
          <input
            type="number"
            value={config.port}
            onChange={(e) => handleConfigChange('port', parseInt(e.target.value) || defaultPorts[databaseType as keyof typeof defaultPorts])}
            placeholder={defaultPorts[databaseType as keyof typeof defaultPorts]?.toString()}
            className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
          />
        </div>

        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">
            Base de données
          </label>
          <input
            type="text"
            value={config.database}
            onChange={(e) => handleConfigChange('database', e.target.value)}
            placeholder="database_name"
            className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
          />
        </div>

        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">
            Nom d'utilisateur
          </label>
          <input
            type="text"
            value={config.username}
            onChange={(e) => handleConfigChange('username', e.target.value)}
            placeholder="username"
            className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
          />
        </div>

        <div className="md:col-span-2">
          <label className="block text-sm font-medium text-gray-700 mb-1">
            Mot de passe
          </label>
          <div className="relative">
            <input
              type={showPassword ? 'text' : 'password'}
              value={config.password}
              onChange={(e) => handleConfigChange('password', e.target.value)}
              placeholder="password"
              className="w-full px-3 py-2 pr-10 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
            <button
              type="button"
              onClick={() => setShowPassword(!showPassword)}
              className="absolute inset-y-0 right-0 pr-3 flex items-center"
            >
              {showPassword ? (
                <EyeSlashIcon className="h-5 w-5 text-gray-400" />
              ) : (
                <EyeIcon className="h-5 w-5 text-gray-400" />
              )}
            </button>
          </div>
        </div>

        {databaseType === 'postgresql' && (
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Mode SSL
            </label>
            <select
              value={config.ssl_mode || 'prefer'}
              onChange={(e) => handleConfigChange('ssl_mode', e.target.value)}
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
            >
              {sslModes.map(mode => (
                <option key={mode} value={mode}>{mode}</option>
              ))}
            </select>
          </div>
        )}

        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">
            Timeout de connexion (secondes)
          </label>
          <input
            type="number"
            value={config.connection_timeout || 30}
            onChange={(e) => handleConfigChange('connection_timeout', parseInt(e.target.value) || 30)}
            placeholder="30"
            min="1"
            max="300"
            className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
          />
        </div>
      </div>
    );
  };

  return (
    <div className="space-y-6">
      {/* Connection String Examples */}
      {templateData && templateData.examples && templateData.examples.length > 0 && (
        <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
          <div className="flex items-start space-x-2">
            <InformationCircleIcon className="h-5 w-5 text-blue-500 mt-0.5 flex-shrink-0" />
            <div className="flex-1">
              <h4 className="text-sm font-medium text-blue-900 mb-2">
                Exemples de chaînes de connexion pour {databaseType.toUpperCase()}
              </h4>
              <div className="space-y-2">
                {templateData.examples.map((example: string, index: number) => (
                  <div key={index} className="bg-white border border-blue-200 rounded p-2">
                    <code className="text-xs text-gray-800 break-all">{example}</code>
                  </div>
                ))}
              </div>
              {templateData.template && (
                <div className="mt-3">
                  <p className="text-xs text-blue-700 mb-1">Modèle recommandé :</p>
                  <div className="bg-white border border-blue-200 rounded p-2">
                    <code className="text-xs text-blue-800 break-all">{templateData.template}</code>
                  </div>
                </div>
              )}
            </div>
          </div>
        </div>
      )}

      {/* Mode Toggle */}
      <div className="flex items-center space-x-4">
        <label className="flex items-center">
          <input
            type="radio"
            checked={!isManualMode}
            onChange={() => onManualModeChange(false)}
            className="mr-2"
          />
          <span className="text-sm font-medium text-gray-700">Configuration assistée</span>
        </label>
        <label className="flex items-center">
          <input
            type="radio"
            checked={isManualMode}
            onChange={() => onManualModeChange(true)}
            className="mr-2"
          />
          <span className="text-sm font-medium text-gray-700">Chaîne de connexion manuelle</span>
        </label>
      </div>

      {isManualMode ? (
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">
            Chaîne de connexion
          </label>
          <textarea
            value={manualConnectionString}
            onChange={(e) => onConnectionStringChange(e.target.value)}
            placeholder={`Exemple pour ${databaseType}: ${buildConnectionString()}`}
            rows={3}
            className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 font-mono text-sm"
          />
        </div>
      ) : (
        <>
          {renderFormFields()}
          
          {/* Generated Connection String Preview */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Chaîne de connexion générée
            </label>
            <div className="bg-gray-50 p-3 rounded-md border">
              <code className="text-sm text-gray-800 break-all">
                {buildConnectionString()}
              </code>
            </div>
          </div>
        </>
      )}

      {/* Test Connection */}
      {onTestConnection && (
        <div className="space-y-3">
          <button
            onClick={handleTestConnection}
            disabled={isTesting}
            className="flex items-center space-x-2 px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {isTesting ? (
              <ClockIcon className="h-4 w-4 animate-spin" />
            ) : (
              <CheckCircleIcon className="h-4 w-4" />
            )}
            <span>{isTesting ? 'Test en cours...' : 'Tester la connexion'}</span>
          </button>

          {testResult && (
            <div className={`flex items-start space-x-2 p-3 rounded-md ${
              testResult.success ? 'bg-green-50 border border-green-200' : 'bg-red-50 border border-red-200'
            }`}>
              {testResult.success ? (
                <CheckCircleIcon className="h-5 w-5 text-green-500 mt-0.5" />
              ) : (
                <ExclamationCircleIcon className="h-5 w-5 text-red-500 mt-0.5" />
              )}
              <div className="flex-1">
                <p className={`text-sm font-medium ${
                  testResult.success ? 'text-green-800' : 'text-red-800'
                }`}>
                  {testResult.message}
                </p>
                {testResult.response_time_ms && (
                  <p className="text-xs text-gray-600 mt-1">
                    Temps de réponse: {testResult.response_time_ms}ms
                  </p>
                )}
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
};

export default ConnectionStringBuilder;
