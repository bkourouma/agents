import React, { useState } from 'react';
import { useMutation, useQuery } from '@tanstack/react-query';
import { toast } from 'react-hot-toast';
import {
  ChevronLeftIcon,
  ChevronRightIcon,
  CheckIcon,
  CircleStackIcon,
  ServerIcon,
  TableCellsIcon,
  CpuChipIcon,
  XMarkIcon,
  InformationCircleIcon
} from '@heroicons/react/24/outline';
import ConnectionStringBuilder from './ConnectionStringBuilder';
import { apiClient } from '../../lib/api';

interface DatabaseSetupWizardProps {
  isOpen: boolean;
  onClose: () => void;
  onComplete: (connectionId: number) => void;
}

interface WizardStep {
  id: number;
  title: string;
  description: string;
  icon: React.ComponentType<any>;
}

interface ConnectionConfig {
  host: string;
  port: number;
  database: string;
  username: string;
  password: string;
  ssl_mode?: string;
  connection_timeout?: number;
}

const DatabaseSetupWizard: React.FC<DatabaseSetupWizardProps> = ({
  isOpen,
  onClose,
  onComplete
}) => {
  const [currentStep, setCurrentStep] = useState(1);
  const [connectionName, setConnectionName] = useState('');
  const [databaseType, setDatabaseType] = useState('postgresql');
  const [connectionConfig, setConnectionConfig] = useState<ConnectionConfig>({
    host: 'localhost',
    port: 5432,
    database: '',
    username: '',
    password: '',
    ssl_mode: 'prefer',
    connection_timeout: 30
  });

  // Fetch available database providers
  const { data: providers, isLoading: providersLoading } = useQuery({
    queryKey: ['database-providers'],
    queryFn: () => apiClient.getDatabaseProviders()
  });
  const [isManualMode, setIsManualMode] = useState(false);
  const [manualConnectionString, setManualConnectionString] = useState('');
  const [selectedTables, setSelectedTables] = useState<string[]>([]);
  const [connectionId, setConnectionId] = useState<number | null>(null);

  const steps: WizardStep[] = [
    {
      id: 1,
      title: 'Type de base de données',
      description: 'Choisissez le type de base de données',
      icon: CircleStackIcon
    },
    {
      id: 2,
      title: 'Configuration de connexion',
      description: 'Configurez les paramètres de connexion',
      icon: ServerIcon
    },
    {
      id: 3,
      title: 'Sélection des tables',
      description: 'Choisissez les tables à importer',
      icon: TableCellsIcon
    },
    {
      id: 4,
      title: 'Configuration de l\'entraînement',
      description: 'Configurez l\'entraînement Vanna AI',
      icon: CpuChipIcon
    }
  ];

  // Use dynamic provider list or fallback to static list
  const databaseTypes = providers || [
    { value: 'postgresql', name: 'PostgreSQL', description: 'Base de données relationnelle avancée' },
    { value: 'mysql', name: 'MySQL', description: 'Base de données relationnelle populaire' },
    { value: 'sqlserver', name: 'SQL Server', description: 'Base de données Microsoft' },
    { value: 'oracle', name: 'Oracle', description: 'Base de données d\'entreprise' },
    { value: 'sqlite', name: 'SQLite', description: 'Base de données légère' }
  ];

  // Default ports for different database types
  const defaultPorts = {
    postgresql: 5432,
    mysql: 3306,
    sqlserver: 1433,
    oracle: 1521,
    sqlite: 0
  };

  // Update port when database type changes
  React.useEffect(() => {
    setConnectionConfig(prev => ({
      ...prev,
      port: defaultPorts[databaseType as keyof typeof defaultPorts]
    }));
  }, [databaseType]);

  // Create connection mutation
  const createConnectionMutation = useMutation({
    mutationFn: async (connectionData: any) => {
      return await apiClient.createDatabaseConnection(connectionData);
    },
    onSuccess: (data) => {
      setConnectionId(data.id);
      toast.success('Connexion créée avec succès');
    },
    onError: (error: any) => {
      toast.error('Erreur lors de la création de la connexion: ' + error.message);
    }
  });

  // Test connection mutation
  const testConnectionMutation = useMutation({
    mutationFn: async () => {
      if (!connectionId) throw new Error('No connection ID');
      return await apiClient.testDatabaseConnection(connectionId);
    }
  });

  // Get external schema query
  const { data: externalSchema, refetch: refetchSchema } = useQuery({
    queryKey: ['external-schema', connectionId],
    queryFn: async () => {
      if (!connectionId) throw new Error('No connection ID');
      return await apiClient.getExternalDatabaseSchema(connectionId);
    },
    enabled: false
  });

  const handleNext = async () => {
    if (currentStep === 2) {
      // Create connection before moving to step 3
      const connectionData = {
        name: connectionName,
        database_type: databaseType,
        connection_string: isManualMode ? manualConnectionString : undefined,
        ...(!isManualMode && connectionConfig),
        is_default: false,
        test_on_create: true,
        description: `Connexion ${databaseType.toUpperCase()} créée via l'assistant`
      };

      try {
        await createConnectionMutation.mutateAsync(connectionData);
        setCurrentStep(currentStep + 1);
        // Fetch schema for step 3
        setTimeout(() => refetchSchema(), 500);
      } catch (error) {
        // Error is handled by mutation
        return;
      }
    } else if (currentStep < steps.length) {
      setCurrentStep(currentStep + 1);
    }
  };

  const handlePrevious = () => {
    if (currentStep > 1) {
      setCurrentStep(currentStep - 1);
    }
  };

  const handleComplete = () => {
    if (connectionId) {
      onComplete(connectionId);
      onClose();
    }
  };

  const handleTestConnection = async () => {
    if (!connectionId) {
      toast.error('Veuillez d\'abord créer la connexion');
      return { success: false, message: 'No connection created' };
    }

    try {
      const result = await testConnectionMutation.mutateAsync();
      return result;
    } catch (error: any) {
      return { success: false, message: error.message };
    }
  };

  const renderStepContent = () => {
    switch (currentStep) {
      case 1:
        return (
          <div className="space-y-6">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Nom de la connexion
              </label>
              <input
                type="text"
                value={connectionName}
                onChange={(e) => setConnectionName(e.target.value)}
                placeholder="Ma base de données"
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-3">
                Type de base de données
              </label>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                {databaseTypes.map((type) => (
                  <div
                    key={type.value}
                    onClick={() => setDatabaseType(type.value)}
                    className={`p-4 border rounded-lg cursor-pointer transition-colors ${
                      databaseType === type.value
                        ? 'border-blue-500 bg-blue-50'
                        : 'border-gray-300 hover:border-gray-400'
                    }`}
                  >
                    <div className="flex items-center justify-between">
                      <div>
                        <h3 className="font-medium text-gray-900">{type.name}</h3>
                        <p className="text-sm text-gray-500">{type.description}</p>
                        {type.default_port && (
                          <p className="text-xs text-gray-400">Port par défaut: {type.default_port}</p>
                        )}
                      </div>
                      {databaseType === type.value && (
                        <CheckIcon className="h-5 w-5 text-blue-500" />
                      )}
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </div>
        );

      case 2:
        return (
          <div className="space-y-6">
            <ConnectionStringBuilder
              databaseType={databaseType}
              config={connectionConfig}
              onConfigChange={setConnectionConfig}
              onConnectionStringChange={setManualConnectionString}
              manualConnectionString={manualConnectionString}
              onManualModeChange={setIsManualMode}
              isManualMode={isManualMode}
              onTestConnection={connectionId ? handleTestConnection : undefined}
            />
          </div>
        );

      case 3:
        return (
          <div className="space-y-6">
            <div className="text-center">
              <h3 className="text-lg font-medium text-gray-900 mb-2">
                Sélection des tables
              </h3>
              <p className="text-sm text-gray-500">
                Choisissez les tables que vous souhaitez importer pour l'entraînement Vanna AI
              </p>
            </div>

            {externalSchema ? (
              <div className="space-y-4">
                <div className="bg-blue-50 p-4 rounded-lg">
                  <div className="flex items-center space-x-2">
                    <CircleStackIcon className="h-5 w-5 text-blue-500" />
                    <span className="font-medium text-blue-900">
                      {externalSchema.total_tables} tables trouvées
                    </span>
                  </div>
                </div>

                <div className="max-h-96 overflow-y-auto space-y-2">
                  {externalSchema.tables.map((table) => (
                    <div
                      key={table.name}
                      className="flex items-center justify-between p-3 border border-gray-200 rounded-lg"
                    >
                      <div className="flex items-center space-x-3">
                        <input
                          type="checkbox"
                          checked={selectedTables.includes(table.name)}
                          onChange={(e) => {
                            if (e.target.checked) {
                              setSelectedTables([...selectedTables, table.name]);
                            } else {
                              setSelectedTables(selectedTables.filter(t => t !== table.name));
                            }
                          }}
                          className="h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded"
                        />
                        <div>
                          <h4 className="font-medium text-gray-900">{table.name}</h4>
                          {table.schema && (
                            <p className="text-sm text-gray-500">Schéma: {table.schema}</p>
                          )}
                        </div>
                      </div>
                      <div className="text-right text-sm text-gray-500">
                        <div>{table.columns.length} colonnes</div>
                        {table.row_count && (
                          <div>{table.row_count.toLocaleString()} lignes</div>
                        )}
                      </div>
                    </div>
                  ))}
                </div>

                <div className="bg-gray-50 p-3 rounded-lg">
                  <p className="text-sm text-gray-600">
                    {selectedTables.length} table(s) sélectionnée(s)
                  </p>
                </div>
              </div>
            ) : (
              <div className="text-center py-8">
                <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-500 mx-auto"></div>
                <p className="text-sm text-gray-500 mt-2">Chargement des tables...</p>
              </div>
            )}
          </div>
        );

      case 4:
        return (
          <div className="space-y-6">
            <div className="text-center">
              <CheckIcon className="h-12 w-12 text-green-500 mx-auto mb-4" />
              <h3 className="text-lg font-medium text-gray-900 mb-2">
                Configuration terminée !
              </h3>
              <p className="text-sm text-gray-500">
                Votre connexion à la base de données est prête. Vous pouvez maintenant commencer l'entraînement Vanna AI.
              </p>
            </div>

            <div className="bg-green-50 p-4 rounded-lg">
              <div className="space-y-2 text-sm">
                <div><strong>Connexion:</strong> {connectionName}</div>
                <div><strong>Type:</strong> {databaseTypes.find(t => t.value === databaseType)?.name}</div>
                <div><strong>Tables sélectionnées:</strong> {selectedTables.length}</div>
              </div>
            </div>
          </div>
        );

      default:
        return null;
    }
  };

  const canProceed = () => {
    switch (currentStep) {
      case 1:
        return connectionName.trim() !== '' && databaseType !== '';
      case 2:
        return isManualMode ? manualConnectionString.trim() !== '' : 
               connectionConfig.host && connectionConfig.database && connectionConfig.username;
      case 3:
        return selectedTables.length > 0;
      case 4:
        return true;
      default:
        return false;
    }
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <div className="bg-white rounded-lg shadow-xl w-full max-w-4xl max-h-[90vh] overflow-hidden">
        {/* Header */}
        <div className="flex items-center justify-between p-6 border-b border-gray-200">
          <h2 className="text-xl font-semibold text-gray-900">
            Assistant de configuration de base de données
          </h2>
          <button
            onClick={onClose}
            className="text-gray-400 hover:text-gray-600"
          >
            <XMarkIcon className="h-6 w-6" />
          </button>
        </div>

        {/* Progress Steps */}
        <div className="px-6 py-4 border-b border-gray-200">
          <div className="flex items-center justify-between">
            {steps.map((step, index) => {
              const StepIcon = step.icon;
              const isActive = currentStep === step.id;
              const isCompleted = currentStep > step.id;
              
              return (
                <div key={step.id} className="flex items-center">
                  <div className={`flex items-center justify-center w-10 h-10 rounded-full border-2 ${
                    isCompleted ? 'bg-green-500 border-green-500 text-white' :
                    isActive ? 'bg-blue-500 border-blue-500 text-white' :
                    'bg-gray-100 border-gray-300 text-gray-400'
                  }`}>
                    {isCompleted ? (
                      <CheckIcon className="h-5 w-5" />
                    ) : (
                      <StepIcon className="h-5 w-5" />
                    )}
                  </div>
                  <div className="ml-3">
                    <p className={`text-sm font-medium ${
                      isActive ? 'text-blue-600' : isCompleted ? 'text-green-600' : 'text-gray-500'
                    }`}>
                      {step.title}
                    </p>
                    <p className="text-xs text-gray-500">{step.description}</p>
                  </div>
                  {index < steps.length - 1 && (
                    <div className={`flex-1 h-0.5 mx-4 ${
                      isCompleted ? 'bg-green-500' : 'bg-gray-300'
                    }`} />
                  )}
                </div>
              );
            })}
          </div>
        </div>

        {/* Content */}
        <div className="p-6 overflow-y-auto max-h-96">
          {renderStepContent()}
        </div>

        {/* Footer */}
        <div className="flex items-center justify-between p-6 border-t border-gray-200">
          <button
            onClick={handlePrevious}
            disabled={currentStep === 1}
            className="flex items-center space-x-2 px-4 py-2 text-gray-600 hover:text-gray-800 disabled:opacity-50 disabled:cursor-not-allowed"
          >
            <ChevronLeftIcon className="h-4 w-4" />
            <span>Précédent</span>
          </button>

          <div className="flex space-x-3">
            <button
              onClick={onClose}
              className="px-4 py-2 text-gray-600 hover:text-gray-800"
            >
              Annuler
            </button>
            
            {currentStep === steps.length ? (
              <button
                onClick={handleComplete}
                className="flex items-center space-x-2 px-6 py-2 bg-green-600 text-white rounded-md hover:bg-green-700"
              >
                <CheckIcon className="h-4 w-4" />
                <span>Terminer</span>
              </button>
            ) : (
              <button
                onClick={handleNext}
                disabled={!canProceed() || createConnectionMutation.isPending}
                className="flex items-center space-x-2 px-6 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed"
              >
                <span>
                  {createConnectionMutation.isPending ? 'Création...' : 'Suivant'}
                </span>
                <ChevronRightIcon className="h-4 w-4" />
              </button>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};

export default DatabaseSetupWizard;
