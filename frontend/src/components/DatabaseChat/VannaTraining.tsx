import React, { useState } from 'react';
import { useMutation, useQuery } from '@tanstack/react-query';
import { toast } from 'react-hot-toast';
import {
  CpuChipIcon,
  PlayIcon,
  CheckCircleIcon,
  ExclamationCircleIcon,
  ClockIcon,
  SparklesIcon
} from '@heroicons/react/24/outline';
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

interface VannaTrainingProps {
  tables: DatabaseTable[];
  schema?: DatabaseSchema;
}

interface TrainingSession {
  id: number;
  user_id: number;
  table_id: number;
  model_name: string;
  training_status: string;
  training_started_at?: string;
  training_completed_at?: string;
  error_message?: string;
  training_config: Record<string, any>;
  training_metrics: Record<string, any>;
  created_at: string;
  updated_at?: string;
}



interface GeneratedTrainingData {
  question: string;
  sql: string;
  selected: boolean;
  confidence_score: number;
}

const VannaTraining: React.FC<VannaTrainingProps> = ({ tables, schema }) => {
  const [selectedTables, setSelectedTables] = useState<number[]>([]);
  const [modelName, setModelName] = useState('');
  const [isTraining, setIsTraining] = useState(false);

  // More Training modal state
  const [showMoreTrainingModal, setShowMoreTrainingModal] = useState(false);
  const [selectedLLMModel, setSelectedLLMModel] = useState('gpt-3.5-turbo');
  const [numQuestions, setNumQuestions] = useState(10);
  const [customPrompt, setCustomPrompt] = useState('');
  const [generatedQuestions, setGeneratedQuestions] = useState<GeneratedTrainingData[]>([]);
  const [isGenerating, setIsGenerating] = useState(false);
  const [isTrainingGenerated, setIsTrainingGenerated] = useState(false);

  // Fetch training sessions
  const { data: trainingSessions = [], refetch: refetchSessions } = useQuery({
    queryKey: ['vanna-training-sessions'],
    queryFn: async () => {
      console.log('🔄 Fetching training sessions...');
      try {
        const sessions = await apiClient.getVannaTrainingSessions();
        console.log('✅ Training sessions fetched:', sessions);
        return sessions;
      } catch (error) {
        console.error('❌ Failed to fetch training sessions:', error);
        return [];
      }
    },
  });

  // Start training mutation
  const startTrainingMutation = useMutation({
    mutationFn: async (data: { table_ids: number[]; model_name: string }) => {
      console.log('🔄 Mutation function called with:', data);
      try {
        const result = await apiClient.startVannaTraining(data);
        console.log('✅ Training API response:', result);
        return result;
      } catch (error) {
        console.error('❌ Training API error:', error);
        throw error;
      }
    },
    onSuccess: (data) => {
      console.log('🎉 Training started successfully:', data);
      toast.success('Vanna AI training started successfully');
      setIsTraining(true);
      refetchSessions();

      // Poll for training status
      pollTrainingStatus(data.id);
    },
    onError: (error: any) => {
      console.error('💥 Training mutation error:', error);
      toast.error(error.response?.data?.detail || 'Failed to start training');
    },
  });

  const pollTrainingStatus = async (trainingId: number) => {
    const maxAttempts = 30; // 5 minutes with 10-second intervals
    let attempts = 0;

    const poll = async () => {
      try {
        const session = await apiClient.getVannaTrainingStatus(trainingId);

        if (session.training_status === 'completed') {
          toast.success('Vanna AI training completed successfully');
          setIsTraining(false);
          refetchSessions();
          return;
        } else if (session.training_status === 'failed') {
          toast.error(`Training failed: ${session.error_message || 'Unknown error'}`);
          setIsTraining(false);
          refetchSessions();
          return;
        } else if (attempts < maxAttempts) {
          attempts++;
          setTimeout(poll, 10000); // Poll every 10 seconds
        } else {
          toast('Training is taking longer than expected. Check back later.', { icon: '⚠️' });
          setIsTraining(false);
        }
      } catch (error) {
        console.error('Error polling training status:', error);
        setIsTraining(false);
      }
    };

    setTimeout(poll, 5000); // Start polling after 5 seconds
  };

  const handleTableSelection = (tableId: number) => {
    setSelectedTables(prev => 
      prev.includes(tableId)
        ? prev.filter(id => id !== tableId)
        : [...prev, tableId]
    );
  };

  const handleStartTraining = () => {
    console.log('🚀 Training button clicked!');
    console.log('Selected tables:', selectedTables);
    console.log('Model name:', modelName);

    if (selectedTables.length === 0) {
      console.log('❌ No tables selected');
      toast.error('Please select at least one table for training');
      return;
    }

    if (!modelName.trim()) {
      console.log('❌ No model name provided');
      toast.error('Please enter a model name');
      return;
    }

    console.log('✅ Starting training mutation...');
    const trainingData = {
      table_ids: selectedTables,
      model_name: modelName.trim()
    };
    console.log('Training data:', trainingData);

    startTrainingMutation.mutate(trainingData);
  };

  const handleGenerateQuestions = async () => {
    if (selectedTables.length === 0 || !modelName.trim()) {
      toast.error('Please select tables and enter a model name');
      return;
    }

    setIsGenerating(true);
    try {
      const data = await apiClient.generateTrainingData({
        table_ids: selectedTables,
        model_name: modelName.trim(),
        llm_model: selectedLLMModel,
        num_questions: numQuestions,
        avoid_duplicates: true,
        prompt: customPrompt.trim() || undefined
      });

      const questionsWithSelection = data.training_data.map((item: any) => ({
        question: item.question,
        sql: item.sql,
        selected: true, // All selected by default
        confidence_score: item.confidence_score
      }));

      setGeneratedQuestions(questionsWithSelection);
      toast.success(`Generated ${data.generated_count} questions`);

      if (data.duplicates_avoided > 0) {
        toast(`Avoided ${data.duplicates_avoided} duplicate questions`, { icon: 'ℹ️' });
      }
    } catch (error) {
      console.error('Error generating questions:', error);
      toast.error('Failed to generate questions');
    } finally {
      setIsGenerating(false);
    }
  };

  const handleTrainGenerated = async () => {
    const selectedQuestions = generatedQuestions.filter(q => q.selected);

    if (selectedQuestions.length === 0) {
      toast.error('Please select at least one question to train');
      return;
    }

    setIsTrainingGenerated(true);
    try {
      // Prepare batch training data
      const trainingData = selectedQuestions.map(question => ({
        table_id: selectedTables[0], // Use first selected table for now
        model_name: modelName.trim(),
        question: question.question,
        sql: question.sql,
        is_generated: true,
        confidence_score: question.confidence_score,
        generation_model: selectedLLMModel
      }));

      // Use batch training endpoint
      const result = await apiClient.batchTrainQuestions(trainingData);

      toast.success(`Successfully trained on ${result.trained_count} questions`);
      setShowMoreTrainingModal(false);
      setGeneratedQuestions([]);
      refetchSessions(); // Refresh training sessions
    } catch (error) {
      console.error('Error training on generated questions:', error);
      toast.error('Failed to train on generated questions');
    } finally {
      setIsTrainingGenerated(false);
    }
  };

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'completed':
        return <CheckCircleIcon className="h-5 w-5 text-green-500" />;
      case 'failed':
        return <ExclamationCircleIcon className="h-5 w-5 text-red-500" />;
      case 'training':
        return <ClockIcon className="h-5 w-5 text-blue-500 animate-spin" />;
      default:
        return <ClockIcon className="h-5 w-5 text-gray-400" />;
    }
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'completed':
        return 'bg-green-100 text-green-800';
      case 'failed':
        return 'bg-red-100 text-red-800';
      case 'training':
        return 'bg-blue-100 text-blue-800';
      default:
        return 'bg-gray-100 text-gray-800';
    }
  };

  return (
    <div className="h-full p-6">
      <div className="max-w-4xl mx-auto">
        {/* Header */}
        <div className="mb-8">
          <div className="flex items-center">
            <CpuChipIcon className="h-8 w-8 text-blue-600 mr-3" />
            <div>
              <h2 className="text-2xl font-bold text-gray-900">Vanna AI Training</h2>
              <p className="text-gray-600">
                Train Vanna AI on your database schema to enable natural language querying
              </p>
            </div>
          </div>
        </div>

        {tables.length === 0 ? (
          <div className="text-center py-12">
            <CpuChipIcon className="mx-auto h-12 w-12 text-gray-400" />
            <h3 className="mt-2 text-sm font-medium text-gray-900">No tables available</h3>
            <p className="mt-1 text-sm text-gray-500">
              Create database tables first to train Vanna AI.
            </p>
          </div>
        ) : (
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
            {/* Training Configuration */}
            <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
              <h3 className="text-lg font-medium text-gray-900 mb-4">
                Configure Training
              </h3>

              {/* Model Name */}
              <div className="mb-6">
                <label htmlFor="model_name" className="block text-sm font-medium text-gray-700 mb-2">
                  Model Name
                </label>
                <input
                  type="text"
                  id="model_name"
                  value={modelName}
                  onChange={(e) => setModelName(e.target.value)}
                  className="w-full border border-gray-300 rounded-md px-3 py-2 shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500"
                  placeholder="e.g., my_database_model"
                />
                <p className="mt-1 text-xs text-gray-500">
                  Choose a unique name for your trained model
                </p>
              </div>

              {/* Table Selection */}
              <div className="mb-6">
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Select Tables for Training
                </label>
                <div className="space-y-2 max-h-64 overflow-y-auto border border-gray-200 rounded-md p-3">
                  {tables.map((table) => (
                    <label key={table.id} className="flex items-center">
                      <input
                        type="checkbox"
                        checked={selectedTables.includes(table.id)}
                        onChange={() => handleTableSelection(table.id)}
                        className="rounded border-gray-300 text-blue-600 shadow-sm focus:border-blue-300 focus:ring focus:ring-blue-200 focus:ring-opacity-50"
                      />
                      <div className="ml-3 flex-1">
                        <span className="text-sm font-medium text-gray-900">
                          {table.display_name}
                        </span>
                        <span className="text-xs text-gray-500 ml-2">
                          ({table.columns.length} columns)
                        </span>
                        {table.description && (
                          <p className="text-xs text-gray-400 mt-1">
                            {table.description}
                          </p>
                        )}
                      </div>
                    </label>
                  ))}
                </div>
                <p className="mt-1 text-xs text-gray-500">
                  Selected: {selectedTables.length} of {tables.length} tables
                </p>
              </div>

              {/* Training Buttons */}
              <div className="space-y-3">
                <button
                  onClick={handleStartTraining}
                  disabled={startTrainingMutation.isPending || isTraining || selectedTables.length === 0 || !modelName.trim()}
                  className="w-full inline-flex items-center justify-center px-4 py-2 border border-transparent shadow-sm text-sm font-medium rounded-md text-white bg-blue-600 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  {startTrainingMutation.isPending || isTraining ? (
                    <>
                      <ClockIcon className="animate-spin -ml-1 mr-3 h-5 w-5" />
                      Training in Progress...
                    </>
                  ) : (
                    <>
                      <PlayIcon className="-ml-1 mr-3 h-5 w-5" />
                      Start Training
                    </>
                  )}
                </button>

                <button
                  onClick={() => setShowMoreTrainingModal(true)}
                  disabled={selectedTables.length === 0 || !modelName.trim()}
                  className="w-full inline-flex items-center justify-center px-4 py-2 border border-gray-300 shadow-sm text-sm font-medium rounded-md text-gray-700 bg-white hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  <SparklesIcon className="-ml-1 mr-3 h-5 w-5" />
                  More Training
                </button>
              </div>

              {/* Training Info */}
              <div className="mt-4 p-3 bg-blue-50 rounded-md">
                <h4 className="text-sm font-medium text-blue-900 mb-2">
                  What happens during training?
                </h4>
                <ul className="text-xs text-blue-800 space-y-1">
                  <li>• Vanna AI analyzes your database schema</li>
                  <li>• Learns table relationships and column types</li>
                  <li>• Generates sample questions and SQL pairs</li>
                  <li>• Creates a model for natural language queries</li>
                </ul>
              </div>
            </div>

            {/* Training History */}
            <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
              <h3 className="text-lg font-medium text-gray-900 mb-4">
                Training History
              </h3>

              {trainingSessions.length === 0 ? (
                <div className="text-center py-8">
                  <CpuChipIcon className="mx-auto h-8 w-8 text-gray-400" />
                  <p className="mt-2 text-sm text-gray-500">
                    No training sessions yet
                  </p>
                  <p className="text-xs text-gray-400">
                    Start your first training to see history here
                  </p>
                </div>
              ) : (
                <div className="space-y-3">
                  {trainingSessions.map((session: TrainingSession) => (
                    <div
                      key={session.id}
                      className="border border-gray-200 rounded-lg p-4"
                    >
                      <div className="flex items-center justify-between">
                        <div className="flex items-center">
                          {getStatusIcon(session.training_status)}
                          <div className="ml-3">
                            <h4 className="text-sm font-medium text-gray-900">
                              {session.model_name}
                            </h4>
                            <p className="text-xs text-gray-500">
                              {new Date(session.created_at).toLocaleDateString()}
                            </p>
                          </div>
                        </div>
                        <span
                          className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${getStatusColor(
                            session.training_status
                          )}`}
                        >
                          {session.training_status}
                        </span>
                      </div>

                      {session.error_message && (
                        <div className="mt-2 text-xs text-red-600">
                          Error: {session.error_message}
                        </div>
                      )}

                      {session.training_metrics && Object.keys(session.training_metrics).length > 0 && (
                        <div className="mt-2 text-xs text-gray-500">
                          <div className="grid grid-cols-2 gap-2">
                            {session.training_metrics.tables_trained && (
                              <span>Tables: {session.training_metrics.tables_trained}</span>
                            )}
                            {session.training_metrics.training_duration_seconds && (
                              <span>
                                Duration: {Math.round(session.training_metrics.training_duration_seconds)}s
                              </span>
                            )}
                          </div>
                        </div>
                      )}
                    </div>
                  ))}
                </div>
              )}
            </div>
          </div>
        )}

        {/* Schema Overview */}
        {schema && (
          <div className="mt-8 bg-gray-50 rounded-lg p-6">
            <h3 className="text-lg font-medium text-gray-900 mb-4">
              Database Overview
            </h3>
            <div className="grid grid-cols-3 gap-4 text-center">
              <div>
                <div className="text-2xl font-bold text-blue-600">
                  {schema.total_tables}
                </div>
                <div className="text-sm text-gray-500">Tables</div>
              </div>
              <div>
                <div className="text-2xl font-bold text-green-600">
                  {schema.total_columns}
                </div>
                <div className="text-sm text-gray-500">Columns</div>
              </div>
              <div>
                <div className="text-2xl font-bold text-purple-600">
                  {selectedTables.length}
                </div>
                <div className="text-sm text-gray-500">Selected for Training</div>
              </div>
            </div>
          </div>
        )}

        {/* More Training Modal */}
        {showMoreTrainingModal && (
          <div className="fixed inset-0 bg-gray-600 bg-opacity-50 overflow-y-auto h-full w-full z-50">
            <div className="relative top-20 mx-auto p-5 border w-11/12 max-w-4xl shadow-lg rounded-md bg-white">
              <div className="mt-3">
                {/* Modal Header */}
                <div className="flex items-center justify-between mb-6">
                  <h3 className="text-lg font-medium text-gray-900">
                    Generate Training Data
                  </h3>
                  <button
                    onClick={() => setShowMoreTrainingModal(false)}
                    className="text-gray-400 hover:text-gray-600"
                  >
                    <span className="sr-only">Close</span>
                    <svg className="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                    </svg>
                  </button>
                </div>

                {/* Modal Content */}
                <div className="space-y-6">
                  {/* LLM Model Selection */}
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">
                      LLM Model
                    </label>
                    <select
                      value={selectedLLMModel}
                      onChange={(e) => setSelectedLLMModel(e.target.value)}
                      className="w-full border border-gray-300 rounded-md px-3 py-2 shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500"
                    >
                      <option value="gpt-3.5-turbo">GPT-3.5 Turbo</option>
                      <option value="gpt-4">GPT-4</option>
                      <option value="gpt-4-turbo">GPT-4 Turbo</option>
                    </select>
                  </div>

                  {/* Number of Questions */}
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">
                      Number of Questions
                    </label>
                    <input
                      type="number"
                      min="1"
                      max="100"
                      value={numQuestions}
                      onChange={(e) => setNumQuestions(parseInt(e.target.value) || 10)}
                      className="w-full border border-gray-300 rounded-md px-3 py-2 shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500"
                    />
                  </div>

                  {/* Custom Prompt */}
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">
                      Custom Prompt (Optional)
                    </label>
                    <textarea
                      value={customPrompt}
                      onChange={(e) => setCustomPrompt(e.target.value)}
                      placeholder="e.g., generate questions about aggregate functions, window functions, joins, etc."
                      rows={3}
                      className="w-full border border-gray-300 rounded-md px-3 py-2 shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500 resize-none"
                    />
                    <p className="mt-1 text-xs text-gray-500">
                      Guide the AI to generate specific types of questions (e.g., "focus on aggregate functions like COUNT, SUM, AVG")
                    </p>
                  </div>

                  {/* Generate Button */}
                  <button
                    onClick={handleGenerateQuestions}
                    disabled={isGenerating}
                    className="w-full inline-flex items-center justify-center px-4 py-2 border border-transparent shadow-sm text-sm font-medium rounded-md text-white bg-green-600 hover:bg-green-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-green-500 disabled:opacity-50 disabled:cursor-not-allowed"
                  >
                    {isGenerating ? (
                      <>
                        <ClockIcon className="animate-spin -ml-1 mr-3 h-5 w-5" />
                        Generating...
                      </>
                    ) : (
                      <>
                        <SparklesIcon className="-ml-1 mr-3 h-5 w-5" />
                        Generate
                      </>
                    )}
                  </button>

                  {/* Generated Questions List */}
                  {generatedQuestions.length > 0 && (
                    <div className="border border-gray-200 rounded-md p-4 max-h-96 overflow-y-auto">
                      <div className="flex items-center justify-between mb-4">
                        <h4 className="text-sm font-medium text-gray-900">
                          Generated Questions ({generatedQuestions.length})
                        </h4>
                        <div className="flex space-x-2">
                          <button
                            onClick={() => setGeneratedQuestions(prev =>
                              prev.map(q => ({ ...q, selected: true }))
                            )}
                            className="text-xs text-blue-600 hover:text-blue-800"
                          >
                            Select All
                          </button>
                          <button
                            onClick={() => setGeneratedQuestions(prev =>
                              prev.map(q => ({ ...q, selected: false }))
                            )}
                            className="text-xs text-gray-600 hover:text-gray-800"
                          >
                            Deselect All
                          </button>
                        </div>
                      </div>

                      <div className="space-y-3">
                        {generatedQuestions.map((item, index) => (
                          <div key={index} className="border border-gray-100 rounded p-3">
                            <label className="flex items-start">
                              <input
                                type="checkbox"
                                checked={item.selected}
                                onChange={(e) => {
                                  const newQuestions = [...generatedQuestions];
                                  newQuestions[index].selected = e.target.checked;
                                  setGeneratedQuestions(newQuestions);
                                }}
                                className="mt-1 rounded border-gray-300 text-blue-600 shadow-sm focus:border-blue-300 focus:ring focus:ring-blue-200 focus:ring-opacity-50"
                              />
                              <div className="ml-3 flex-1">
                                <div className="text-sm font-medium text-gray-900">
                                  {item.question}
                                </div>
                                <div className="text-xs text-gray-500 mt-1 font-mono bg-gray-50 p-2 rounded">
                                  {item.sql}
                                </div>
                                <div className="text-xs text-gray-400 mt-1">
                                  Confidence: {(item.confidence_score * 100).toFixed(0)}%
                                </div>
                              </div>
                            </label>
                          </div>
                        ))}
                      </div>
                    </div>
                  )}

                  {/* Train Button */}
                  {generatedQuestions.length > 0 && (
                    <button
                      onClick={handleTrainGenerated}
                      disabled={isTrainingGenerated || generatedQuestions.filter(q => q.selected).length === 0}
                      className="w-full inline-flex items-center justify-center px-4 py-2 border border-transparent shadow-sm text-sm font-medium rounded-md text-white bg-blue-600 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 disabled:opacity-50 disabled:cursor-not-allowed"
                    >
                      {isTrainingGenerated ? (
                        <>
                          <ClockIcon className="animate-spin -ml-1 mr-3 h-5 w-5" />
                          Training...
                        </>
                      ) : (
                        <>
                          <PlayIcon className="-ml-1 mr-3 h-5 w-5" />
                          Train ({generatedQuestions.filter(q => q.selected).length} selected)
                        </>
                      )}
                    </button>
                  )}
                </div>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default VannaTraining;
