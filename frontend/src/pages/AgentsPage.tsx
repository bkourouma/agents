import React, { useState, useEffect } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import toast from 'react-hot-toast';
import {
  PlusIcon,
  RocketLaunchIcon,
  PauseIcon,
  TrashIcon,
  EyeIcon,
  PencilIcon,
  ChatBubbleLeftRightIcon,
  DocumentDuplicateIcon,
  XMarkIcon,
  BookOpenIcon,
  CloudArrowUpIcon
} from '@heroicons/react/24/outline';
import { api } from '../lib/simple-api';
import KnowledgeBaseManager from '../components/KnowledgeBaseManager';

interface Agent {
  id: number;
  name: string;
  description: string;
  agent_type: string;
  status: 'draft' | 'active' | 'inactive';
  created_at: string;
  updated_at: string;
  usage_count: number;
  is_public: boolean;
  system_prompt: string;
  personality?: string;
  instructions?: string;
  llm_provider: string;
  llm_model: string;
  temperature: number;
  max_tokens: number;
}

interface AgentTemplate {
  name: string;
  display_name: string;
  description: string;
  agent_type: string;
  default_tools: string[];
  default_capabilities: string[];
}

const AgentsPage: React.FC = () => {
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [showTemplatesModal, setShowTemplatesModal] = useState(false);
  const [showEditModal, setShowEditModal] = useState(false);
  const [editingAgent, setEditingAgent] = useState<Agent | null>(null);
  const [selectedAgent, setSelectedAgent] = useState<Agent | null>(null);
  const [showAgentDetails, setShowAgentDetails] = useState(false);
  const [showKnowledgeBase, setShowKnowledgeBase] = useState(false);
  const [knowledgeBaseAgentId, setKnowledgeBaseAgentId] = useState<number | null>(null);

  const queryClient = useQueryClient();

  // Fetch agents
  const { data: agents = [], isLoading, error } = useQuery({
    queryKey: ['agents'],
    queryFn: () => api.getAgents(),
  });

  // Fetch templates
  const { data: templatesData } = useQuery({
    queryKey: ['agent-templates'],
    queryFn: () => api.getAgentTemplates(),
  });

  const templates: AgentTemplate[] = templatesData?.templates || [];

  // Update agent mutation
  const updateAgent = useMutation({
    mutationFn: ({ id, data }: { id: number; data: any }) => api.updateAgent(id, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['agents'] });
      toast.success('Agent mis à jour avec succès !');
      setShowEditModal(false);
      setEditingAgent(null);
    },
    onError: () => {
      toast.error('Échec de la mise à jour de l\'agent');
    },
  });

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-900 via-gray-900 to-slate-800">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Header Section */}
        <div className="text-center mb-8">
          <div className="inline-flex items-center justify-center w-16 h-16 bg-gradient-to-br from-blue-500 to-blue-600 rounded-2xl mb-4 shadow-lg shadow-blue-500/25">
            <RocketLaunchIcon className="w-8 h-8 text-white" />
          </div>
          <h1 className="text-3xl font-bold text-white mb-2">Agents IA</h1>
          <p className="text-slate-400 text-lg">Créez et gérez vos agents IA intelligents</p>
        </div>

        {/* Action Buttons */}
        <div className="flex flex-col sm:flex-row justify-center items-center gap-4 mb-8">
          <button
            onClick={() => setShowTemplatesModal(true)}
            className="px-6 py-3 bg-slate-700/50 text-slate-300 rounded-xl font-medium hover:bg-slate-600/50 hover:text-white transition-all duration-300 flex items-center space-x-2 border border-slate-600/50"
          >
            <DocumentDuplicateIcon className="w-5 h-5" />
            <span>Modèles</span>
          </button>
          <button
            onClick={() => setShowCreateModal(true)}
            className="px-6 py-3 bg-gradient-to-r from-blue-500 to-blue-600 text-white rounded-xl font-medium hover:from-blue-600 hover:to-blue-700 transition-all duration-300 flex items-center space-x-2 shadow-lg shadow-blue-500/25"
          >
            <PlusIcon className="w-5 h-5" />
            <span>Créer un Agent</span>
          </button>
        </div>

        {/* Stats Cards */}
        <div className="grid grid-cols-1 md:grid-cols-4 gap-6 mb-8">
          <div className="bg-white border border-gray-200 rounded-2xl p-6 shadow-sm">
            <div className="flex items-center">
              <div className="w-12 h-12 bg-blue-100 rounded-xl flex items-center justify-center mr-4">
                <RocketLaunchIcon className="w-6 h-6 text-blue-600" />
              </div>
              <div>
                <p className="text-gray-600 text-sm font-medium">Total Agents</p>
                <p className="text-gray-900 text-2xl font-bold">{agents.length}</p>
              </div>
            </div>
          </div>

          <div className="bg-white border border-gray-200 rounded-2xl p-6 shadow-sm">
            <div className="flex items-center">
              <div className="w-12 h-12 bg-green-100 rounded-xl flex items-center justify-center mr-4">
                <RocketLaunchIcon className="w-6 h-6 text-green-600" />
              </div>
              <div>
                <p className="text-gray-600 text-sm font-medium">Actifs</p>
                <p className="text-gray-900 text-2xl font-bold">
                  {agents.filter(a => a.status === 'active').length}
                </p>
              </div>
            </div>
          </div>

          <div className="bg-white border border-gray-200 rounded-2xl p-6 shadow-sm">
            <div className="flex items-center">
              <div className="w-12 h-12 bg-yellow-100 rounded-xl flex items-center justify-center mr-4">
                <PauseIcon className="w-6 h-6 text-yellow-600" />
              </div>
              <div>
                <p className="text-gray-600 text-sm font-medium">Brouillons</p>
                <p className="text-gray-900 text-2xl font-bold">
                  {agents.filter(a => a.status === 'draft').length}
                </p>
              </div>
            </div>
          </div>

          <div className="bg-white border border-gray-200 rounded-2xl p-6 shadow-sm">
            <div className="flex items-center">
              <div className="w-12 h-12 bg-purple-100 rounded-xl flex items-center justify-center mr-4">
                <ChatBubbleLeftRightIcon className="w-6 h-6 text-purple-600" />
              </div>
              <div>
                <p className="text-gray-600 text-sm font-medium">Total Discussions</p>
                <p className="text-gray-900 text-2xl font-bold">
                  {agents.reduce((sum, a) => sum + a.usage_count, 0)}
                </p>
              </div>
            </div>
          </div>
        </div>

        {/* Agents List */}
        <div className="bg-white border border-gray-200 rounded-2xl shadow-lg">
          <div className="p-6 border-b border-gray-200">
            <div className="flex items-center">
              <div className="w-8 h-8 bg-blue-100 rounded-lg flex items-center justify-center mr-3">
                <RocketLaunchIcon className="w-4 h-4 text-blue-600" />
              </div>
              <div>
                <h3 className="text-xl font-bold text-gray-900">Vos Agents</h3>
                <p className="text-gray-600 mt-1">Gérez et configurez vos agents IA</p>
              </div>
            </div>
          </div>

          <div className="p-6">
            {isLoading ? (
              <div className="text-center py-12">
                <div className="animate-spin rounded-full h-10 w-10 border-b-2 border-blue-500 mx-auto mb-4"></div>
                <p className="text-gray-600">Chargement des agents...</p>
              </div>
            ) : error ? (
              <div className="text-center py-12">
                <div className="w-16 h-16 bg-red-100 rounded-2xl flex items-center justify-center mx-auto mb-4">
                  <XMarkIcon className="w-8 h-8 text-red-600" />
                </div>
                <p className="text-red-600 text-lg">Erreur lors du chargement des agents.</p>
                <p className="text-gray-500 mt-1">Veuillez réessayer.</p>
              </div>
            ) : agents.length === 0 ? (
              <div className="text-center py-16">
                <div className="w-20 h-20 bg-gray-100 rounded-2xl flex items-center justify-center mx-auto mb-6">
                  <RocketLaunchIcon className="w-10 h-10 text-gray-400" />
                </div>
                <h3 className="text-2xl font-bold text-gray-900 mb-3">Aucun agent pour le moment</h3>
                <p className="text-gray-600 text-lg mb-8 max-w-md mx-auto">Créez votre premier agent IA pour commencer à automatiser vos tâches</p>
                <button
                  onClick={() => setShowCreateModal(true)}
                  className="px-8 py-4 bg-gradient-to-r from-blue-500 to-blue-600 text-white rounded-xl font-medium hover:from-blue-600 hover:to-blue-700 transition-all duration-300 shadow-lg shadow-blue-500/25"
                >
                  Créer votre Premier Agent
                </button>
              </div>
            ) : (
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                {agents.map((agent) => (
                  <AgentCard
                    key={agent.id}
                    agent={agent}
                    onView={() => {
                      setSelectedAgent(agent);
                      setShowAgentDetails(true);
                    }}
                    setKnowledgeBaseAgentId={setKnowledgeBaseAgentId}
                    setShowKnowledgeBase={setShowKnowledgeBase}
                    setEditingAgent={setEditingAgent}
                    setShowEditModal={setShowEditModal}
                  />
                ))}
              </div>
            )}
          </div>
        </div>

      {/* Create Agent Modal */}
      {showCreateModal && (
        <CreateAgentModal
          onClose={() => setShowCreateModal(false)}
          onSuccess={() => {
            setShowCreateModal(false);
            queryClient.invalidateQueries({ queryKey: ['agents'] });
          }}
        />
      )}

      {/* Templates Modal */}
      {showTemplatesModal && (
        <TemplatesModal
          templates={templates}
          onClose={() => setShowTemplatesModal(false)}
          onSelectTemplate={(template) => {
            setShowTemplatesModal(false);
            setShowCreateModal(true);
          }}
        />
      )}

      {/* Edit Agent Modal */}
      {showEditModal && editingAgent && (
        <EditAgentModal
          agent={editingAgent}
          onClose={() => {
            setShowEditModal(false);
            setEditingAgent(null);
          }}
          onSuccess={() => {
            setShowEditModal(false);
            setEditingAgent(null);
            queryClient.invalidateQueries({ queryKey: ['agents'] });
          }}
          updateAgent={updateAgent}
        />
      )}

      {/* Agent Details Modal */}
      {showAgentDetails && selectedAgent && (
        <AgentDetailsModal
          agent={selectedAgent}
          onClose={() => {
            setShowAgentDetails(false);
            setSelectedAgent(null);
          }}
        />
      )}

        {/* Knowledge Base Manager */}
        {showKnowledgeBase && knowledgeBaseAgentId && (
          <KnowledgeBaseManager
            agentId={knowledgeBaseAgentId}
            isOpen={showKnowledgeBase}
            onClose={() => {
              setShowKnowledgeBase(false);
              setKnowledgeBaseAgentId(null);
            }}
          />
        )}
      </div>
    </div>
  );
};

// Agent Card Component
interface AgentCardProps {
  agent: Agent;
  onView: () => void;
  setKnowledgeBaseAgentId: (id: number) => void;
  setShowKnowledgeBase: (show: boolean) => void;
  setEditingAgent: (agent: Agent) => void;
  setShowEditModal: (show: boolean) => void;
}

const AgentCard: React.FC<AgentCardProps> = ({
  agent,
  onView,
  setKnowledgeBaseAgentId,
  setShowKnowledgeBase,
  setEditingAgent,
  setShowEditModal
}) => {
  const queryClient = useQueryClient();

  // Activate agent mutation
  const activateAgent = useMutation({
    mutationFn: (agentId: number) => api.activateAgent(agentId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['agents'] });
      toast.success('Agent activated successfully!');
    },
    onError: () => {
      toast.error('Failed to activate agent');
    },
  });

  // Deactivate agent mutation
  const deactivateAgent = useMutation({
    mutationFn: (agentId: number) => api.deactivateAgent(agentId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['agents'] });
      toast.success('Agent deactivated successfully!');
    },
    onError: () => {
      toast.error('Failed to deactivate agent');
    },
  });

  // Delete agent mutation
  const deleteAgent = useMutation({
    mutationFn: (agentId: number) => api.deleteAgent(agentId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['agents'] });
      toast.success('Agent deleted successfully!');
    },
    onError: () => {
      toast.error('Failed to delete agent');
    },
  });

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'active':
        return 'bg-green-100 text-green-800';
      case 'draft':
        return 'bg-yellow-100 text-yellow-800';
      case 'inactive':
        return 'bg-gray-100 text-gray-800';
      default:
        return 'bg-gray-100 text-gray-800';
    }
  };

  const getTypeIcon = (type: string) => {
    switch (type) {
      case 'customer_service':
        return '🎧';
      case 'financial_analysis':
        return '📊';
      case 'research':
        return '🔬';
      case 'project_management':
        return '📋';
      case 'content_creation':
        return '✍️';
      case 'data_analysis':
        return '📈';
      default:
        return '🤖';
    }
  };

  return (
    <div className="bg-white border border-gray-200 rounded-2xl p-6 hover:bg-gray-50 transition-all duration-300 min-h-[320px] flex flex-col hover:shadow-lg">
      <div className="flex items-start justify-between mb-4">
        <div className="flex items-center space-x-3">
          <div className="w-12 h-12 bg-gray-100 rounded-xl flex items-center justify-center text-2xl">
            {getTypeIcon(agent.agent_type)}
          </div>
          <div>
            <h3 className="font-bold text-gray-900 text-lg">{agent.name}</h3>
            <span className={`inline-flex items-center px-3 py-1 rounded-full text-xs font-medium ${getStatusColor(agent.status)}`}>
              {agent.status}
            </span>
          </div>
        </div>
      </div>

      <p className="text-gray-600 text-sm mb-6 line-clamp-3 flex-1">
        {agent.description || 'Aucune description fournie'}
      </p>

      {/* Agent Info */}
      <div className="flex items-center justify-between text-sm text-gray-600 mb-4 bg-gray-50 rounded-lg p-3">
        <div className="flex items-center space-x-2">
          <span>Type: {agent.agent_type.replace('_', ' ')}</span>
        </div>
        <div className="flex items-center space-x-1">
          <ChatBubbleLeftRightIcon className="w-4 h-4" />
          <span>{agent.usage_count} chats</span>
        </div>
      </div>

      {/* Capabilities Preview */}
      <div className="mb-6">
        {agent.capabilities && agent.capabilities.length > 0 && (
          <div>
            <p className="text-xs font-medium text-gray-600 mb-2">Capacités:</p>
            <div className="flex flex-wrap gap-2">
              {agent.capabilities.slice(0, 3).map((capability: string, idx: number) => (
                <span key={idx} className="text-xs bg-blue-100 text-blue-700 px-2 py-1 rounded-lg">
                  {capability.replace('_', ' ')}
                </span>
              ))}
              {agent.capabilities.length > 3 && (
                <span className="text-xs text-gray-500 bg-gray-100 px-2 py-1 rounded-lg">
                  +{agent.capabilities.length - 3} autres
                </span>
              )}
            </div>
          </div>
        )}
      </div>

      {/* Action Buttons */}
      <div className="mt-auto space-y-3">
        <div className="grid grid-cols-2 gap-2">
          <button
            onClick={onView}
            className="flex items-center justify-center space-x-2 px-3 py-2 bg-blue-100 text-blue-700 rounded-lg hover:bg-blue-200 transition-all duration-300 text-sm font-medium"
          >
            <EyeIcon className="w-4 h-4" />
            <span>Voir</span>
          </button>

          <button
            onClick={() => {
              setKnowledgeBaseAgentId(agent.id);
              setShowKnowledgeBase(true);
            }}
            className="flex items-center justify-center space-x-2 px-3 py-2 bg-green-100 text-green-700 rounded-lg hover:bg-green-200 transition-all duration-300 text-sm font-medium"
          >
            <BookOpenIcon className="w-4 h-4" />
            <span>Base</span>
          </button>
        </div>

        <div className="grid grid-cols-3 gap-2">
          {agent.status === 'draft' || agent.status === 'inactive' ? (
            <button
              onClick={() => activateAgent.mutate(agent.id)}
              disabled={activateAgent.isPending}
              className="flex items-center justify-center space-x-1 px-3 py-2 bg-green-100 text-green-700 rounded-lg hover:bg-green-200 transition-all duration-300 text-sm font-medium disabled:opacity-50"
            >
              <RocketLaunchIcon className="w-4 h-4" />
              <span>Activer</span>
            </button>
          ) : (
            <button
              onClick={() => deactivateAgent.mutate(agent.id)}
              disabled={deactivateAgent.isPending}
              className="flex items-center justify-center space-x-1 px-3 py-2 bg-yellow-100 text-yellow-700 rounded-lg hover:bg-yellow-200 transition-all duration-300 text-sm font-medium disabled:opacity-50"
            >
              <PauseIcon className="w-4 h-4" />
              <span>Pause</span>
            </button>
          )}

          <button
            onClick={() => {
              setEditingAgent(agent);
              setShowEditModal(true);
            }}
            className="flex items-center justify-center space-x-1 px-3 py-2 bg-gray-100 text-gray-700 rounded-lg hover:bg-gray-200 transition-all duration-300 text-sm font-medium"
          >
            <PencilIcon className="w-4 h-4" />
            <span>Éditer</span>
          </button>

          <button
            onClick={() => {
              if (confirm('Êtes-vous sûr de vouloir supprimer cet agent ?')) {
                deleteAgent.mutate(agent.id);
              }
            }}
            disabled={deleteAgent.isPending}
            className="flex items-center justify-center space-x-1 px-3 py-2 bg-red-100 text-red-700 rounded-lg hover:bg-red-200 transition-all duration-300 text-sm font-medium disabled:opacity-50"
          >
            <TrashIcon className="w-4 h-4" />
            <span>Suppr</span>
          </button>
        </div>
      </div>
    </div>
  );
};

// Create Agent Modal Component
interface CreateAgentModalProps {
  onClose: () => void;
  onSuccess: () => void;
}

const CreateAgentModal: React.FC<CreateAgentModalProps> = ({ onClose, onSuccess }) => {
  const [formData, setFormData] = useState({
    name: '',
    description: '',
    agent_type: 'general' as const,
    system_prompt: '',
    personality: '',
    instructions: '',
    tools_config: { enabled_tools: [] as string[] },
    capabilities: [] as string[],
    llm_provider: 'openai',
    llm_model: 'gpt-3.5-turbo',
    temperature: 0.7,
    max_tokens: 1000,
  });

  // Available tools and capabilities
  const availableTools = [
    'knowledge_base', 'vanna_database', 'web_search', 'database', 'spreadsheet', 'calculator', 'document_analysis',
    'image_generator', 'writing_assistant', 'seo_tools', 'social_media',
    'project_tracker', 'calendar', 'communication', 'reporting',
    'analytics_tools', 'visualization', 'statistical_software',
    'financial_apis', 'citation', 'document_reader'
  ];

  const availableCapabilities = [
    'general_assistance', 'information_retrieval', 'problem_solving',
    'data_analysis', 'financial_modeling', 'report_generation',
    'information_gathering', 'source_verification', 'synthesis',
    'planning', 'scheduling', 'tracking', 'communication',
    'writing', 'editing', 'seo_optimization', 'content_strategy',
    'data_processing', 'statistical_analysis', 'visualization'
  ];

  const createAgent = useMutation({
    mutationFn: (data: any) => api.createAgent(data),
    onSuccess: () => {
      toast.success('Agent created successfully!');
      onSuccess();
    },
    onError: () => {
      toast.error('Failed to create agent');
    },
  });

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    createAgent.mutate(formData);
  };

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <div className="bg-white rounded-lg p-6 w-full max-w-2xl max-h-[90vh] overflow-y-auto">
        <div className="flex justify-between items-center mb-6">
          <h2 className="text-xl font-semibold text-gray-900">Create New Agent</h2>
          <button onClick={onClose} className="text-gray-400 hover:text-gray-600">
            <XMarkIcon className="w-6 h-6" />
          </button>
        </div>

        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Agent Name *
            </label>
            <input
              type="text"
              required
              value={formData.name}
              onChange={(e) => setFormData({ ...formData, name: e.target.value })}
              className="input-field"
              placeholder="Enter agent name"
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Description
            </label>
            <textarea
              value={formData.description}
              onChange={(e) => setFormData({ ...formData, description: e.target.value })}
              className="input-field"
              rows={3}
              placeholder="Describe what this agent does"
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Agent Type
            </label>
            <select
              value={formData.agent_type}
              onChange={(e) => setFormData({ ...formData, agent_type: e.target.value as any })}
              className="input-field"
            >
              <option value="general">General</option>
              <option value="customer_service">Customer Service</option>
              <option value="financial_analysis">Financial Analysis</option>
              <option value="research">Research</option>
              <option value="project_management">Project Management</option>
              <option value="content_creation">Content Creation</option>
              <option value="data_analysis">Data Analysis</option>
            </select>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              System Prompt *
            </label>
            <textarea
              required
              value={formData.system_prompt}
              onChange={(e) => setFormData({ ...formData, system_prompt: e.target.value })}
              className="input-field"
              rows={4}
              placeholder="Define the agent's role and behavior"
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Personality
            </label>
            <textarea
              value={formData.personality}
              onChange={(e) => setFormData({ ...formData, personality: e.target.value })}
              className="input-field"
              rows={2}
              placeholder="Describe the agent's personality traits"
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Instructions
            </label>
            <textarea
              value={formData.instructions}
              onChange={(e) => setFormData({ ...formData, instructions: e.target.value })}
              className="input-field"
              rows={3}
              placeholder="Additional instructions for the agent"
            />
          </div>

          {/* Tools Configuration */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Tools
            </label>
            <div className="bg-gray-50 p-3 rounded-lg max-h-32 overflow-y-auto">
              <div className="grid grid-cols-2 gap-2">
                {availableTools.map((tool) => (
                  <label key={tool} className="flex items-center space-x-2 text-sm">
                    <input
                      type="checkbox"
                      checked={formData.tools_config.enabled_tools.includes(tool)}
                      onChange={(e) => {
                        const enabled_tools = e.target.checked
                          ? [...formData.tools_config.enabled_tools, tool]
                          : formData.tools_config.enabled_tools.filter(t => t !== tool);
                        setFormData({
                          ...formData,
                          tools_config: { enabled_tools }
                        });
                      }}
                      className="rounded border-gray-300 text-primary-600 focus:ring-primary-500"
                    />
                    <span className="text-gray-700">{tool.replace('_', ' ')}</span>
                  </label>
                ))}
              </div>
            </div>
          </div>

          {/* Capabilities Configuration */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Capabilities
            </label>
            <div className="bg-gray-50 p-3 rounded-lg max-h-32 overflow-y-auto">
              <div className="grid grid-cols-2 gap-2">
                {availableCapabilities.map((capability) => (
                  <label key={capability} className="flex items-center space-x-2 text-sm">
                    <input
                      type="checkbox"
                      checked={formData.capabilities.includes(capability)}
                      onChange={(e) => {
                        const capabilities = e.target.checked
                          ? [...formData.capabilities, capability]
                          : formData.capabilities.filter(c => c !== capability);
                        setFormData({ ...formData, capabilities });
                      }}
                      className="rounded border-gray-300 text-primary-600 focus:ring-primary-500"
                    />
                    <span className="text-gray-700">{capability.replace('_', ' ')}</span>
                  </label>
                ))}
              </div>
            </div>
          </div>

          {/* LLM Configuration */}
          <div className="border-t pt-4">
            <h3 className="text-lg font-medium text-gray-900 mb-4">LLM Configuration</h3>

            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  LLM Provider *
                </label>
                <select
                  required
                  value={formData.llm_provider}
                  onChange={(e) => setFormData({ ...formData, llm_provider: e.target.value })}
                  className="input-field"
                >
                  <option value="openai">OpenAI</option>
                  <option value="anthropic">Anthropic</option>
                  <option value="azure">Azure OpenAI</option>
                  <option value="local">Local Model</option>
                </select>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Model *
                </label>
                <select
                  required
                  value={formData.llm_model}
                  onChange={(e) => setFormData({ ...formData, llm_model: e.target.value })}
                  className="input-field"
                >
                  {formData.llm_provider === 'openai' && (
                    <>
                      <option value="gpt-4">GPT-4</option>
                      <option value="gpt-4-turbo">GPT-4 Turbo</option>
                      <option value="gpt-3.5-turbo">GPT-3.5 Turbo</option>
                    </>
                  )}
                  {formData.llm_provider === 'anthropic' && (
                    <>
                      <option value="claude-3-opus">Claude 3 Opus</option>
                      <option value="claude-3-sonnet">Claude 3 Sonnet</option>
                      <option value="claude-3-haiku">Claude 3 Haiku</option>
                    </>
                  )}
                  {formData.llm_provider === 'azure' && (
                    <>
                      <option value="gpt-4">Azure GPT-4</option>
                      <option value="gpt-35-turbo">Azure GPT-3.5 Turbo</option>
                    </>
                  )}
                  {formData.llm_provider === 'local' && (
                    <>
                      <option value="llama-2">Llama 2</option>
                      <option value="mistral">Mistral</option>
                    </>
                  )}
                </select>
              </div>
            </div>

            <div className="grid grid-cols-2 gap-4 mt-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Temperature
                </label>
                <input
                  type="number"
                  min="0"
                  max="2"
                  step="0.1"
                  value={formData.temperature}
                  onChange={(e) => setFormData({ ...formData, temperature: parseFloat(e.target.value) })}
                  className="input-field"
                  placeholder="0.7"
                />
                <p className="text-xs text-gray-500 mt-1">Controls randomness (0.0 = deterministic, 2.0 = very random)</p>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Max Tokens
                </label>
                <input
                  type="number"
                  min="1"
                  max="4000"
                  value={formData.max_tokens}
                  onChange={(e) => setFormData({ ...formData, max_tokens: parseInt(e.target.value) })}
                  className="input-field"
                  placeholder="1000"
                />
                <p className="text-xs text-gray-500 mt-1">Maximum number of tokens in the response</p>
              </div>
            </div>
          </div>

          <div className="flex justify-end space-x-3 pt-4">
            <button
              type="button"
              onClick={onClose}
              className="btn-outline"
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={createAgent.isPending}
              className="btn-primary disabled:opacity-50"
            >
              {createAgent.isPending ? 'Creating...' : 'Create Agent'}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};

// Templates Modal Component
interface TemplatesModalProps {
  templates: AgentTemplate[];
  onClose: () => void;
  onSelectTemplate: (template: AgentTemplate) => void;
}

const TemplatesModal: React.FC<TemplatesModalProps> = ({ templates, onClose, onSelectTemplate }) => {
  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <div className="bg-white rounded-lg p-6 w-full max-w-4xl max-h-[90vh] overflow-y-auto">
        <div className="flex justify-between items-center mb-6">
          <h2 className="text-xl font-semibold text-gray-900">Agent Templates</h2>
          <button onClick={onClose} className="text-gray-400 hover:text-gray-600">
            <XMarkIcon className="w-6 h-6" />
          </button>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {templates.map((template) => (
            <div
              key={template.name}
              className="border border-gray-200 rounded-lg p-4 hover:border-primary-300 cursor-pointer"
              onClick={() => onSelectTemplate(template)}
            >
              <h3 className="font-semibold text-gray-900 mb-2">{template.display_name}</h3>
              <p className="text-gray-600 text-sm mb-3">{template.description}</p>

              {/* Tools */}
              {template.default_tools && template.default_tools.length > 0 && (
                <div className="mb-3">
                  <p className="text-xs font-medium text-gray-700 mb-1">Tools:</p>
                  <div className="flex flex-wrap gap-1">
                    {template.default_tools.slice(0, 3).map((tool, idx) => (
                      <span key={idx} className="text-xs bg-blue-100 text-blue-700 px-1.5 py-0.5 rounded">
                        {tool.replace('_', ' ')}
                      </span>
                    ))}
                    {template.default_tools.length > 3 && (
                      <span className="text-xs text-gray-500">+{template.default_tools.length - 3} more</span>
                    )}
                  </div>
                </div>
              )}

              {/* Capabilities */}
              {template.default_capabilities && template.default_capabilities.length > 0 && (
                <div className="mb-3">
                  <p className="text-xs font-medium text-gray-700 mb-1">Capabilities:</p>
                  <div className="flex flex-wrap gap-1">
                    {template.default_capabilities.slice(0, 3).map((capability, idx) => (
                      <span key={idx} className="text-xs bg-green-100 text-green-700 px-1.5 py-0.5 rounded">
                        {capability.replace('_', ' ')}
                      </span>
                    ))}
                    {template.default_capabilities.length > 3 && (
                      <span className="text-xs text-gray-500">+{template.default_capabilities.length - 3} more</span>
                    )}
                  </div>
                </div>
              )}

              <div className="flex items-center justify-between">
                <span className="text-xs bg-gray-100 text-gray-800 px-2 py-1 rounded">
                  {template.agent_type.replace('_', ' ')}
                </span>
                <button className="text-primary-600 hover:text-primary-700 text-sm">
                  Use Template
                </button>
              </div>
            </div>
          ))}
        </div>

        {templates.length === 0 && (
          <div className="text-center py-8">
            <p className="text-gray-500">No templates available</p>
          </div>
        )}
      </div>
    </div>
  );
};

// Agent Details Modal Component
interface AgentDetailsModalProps {
  agent: Agent;
  onClose: () => void;
}

const AgentDetailsModal: React.FC<AgentDetailsModalProps> = ({ agent, onClose }) => {
  // Function to open upload page in new tab
  const handleUploadFiles = () => {
    const uploadUrl = `/upload?agent=${agent.id}`;
    window.open(uploadUrl, '_blank');
  };
  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <div className="bg-white rounded-lg p-6 w-full max-w-3xl max-h-[90vh] overflow-y-auto">
        <div className="flex justify-between items-center mb-6">
          <h2 className="text-xl font-semibold text-gray-900">{agent.name}</h2>
          <button onClick={onClose} className="text-gray-400 hover:text-gray-600">
            <XMarkIcon className="w-6 h-6" />
          </button>
        </div>

        <div className="space-y-6">
          <div>
            <h3 className="text-sm font-medium text-gray-700 mb-2">Description</h3>
            <p className="text-gray-900">{agent.description || 'No description provided'}</p>
          </div>

          <div className="grid grid-cols-2 gap-4">
            <div>
              <h3 className="text-sm font-medium text-gray-700 mb-2">Type</h3>
              <p className="text-gray-900">{agent.agent_type.replace('_', ' ')}</p>
            </div>
            <div>
              <h3 className="text-sm font-medium text-gray-700 mb-2">Status</h3>
              <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${
                agent.status === 'active' ? 'bg-green-100 text-green-800' :
                agent.status === 'draft' ? 'bg-yellow-100 text-yellow-800' :
                'bg-gray-100 text-gray-800'
              }`}>
                {agent.status}
              </span>
            </div>
          </div>

          <div>
            <h3 className="text-sm font-medium text-gray-700 mb-2">System Prompt</h3>
            <div className="bg-gray-50 p-3 rounded-lg">
              <p className="text-gray-900 text-sm">{agent.system_prompt}</p>
            </div>
          </div>

          {agent.personality && (
            <div>
              <h3 className="text-sm font-medium text-gray-700 mb-2">Personality</h3>
              <div className="bg-gray-50 p-3 rounded-lg">
                <p className="text-gray-900 text-sm">{agent.personality}</p>
              </div>
            </div>
          )}

          {agent.instructions && (
            <div>
              <h3 className="text-sm font-medium text-gray-700 mb-2">Instructions</h3>
              <div className="bg-gray-50 p-3 rounded-lg">
                <p className="text-gray-900 text-sm">{agent.instructions}</p>
              </div>
            </div>
          )}

          <div className="grid grid-cols-2 gap-4">
            <div>
              <h3 className="text-sm font-medium text-gray-700 mb-2">LLM Provider</h3>
              <p className="text-gray-900">{agent.llm_provider}</p>
            </div>
            <div>
              <h3 className="text-sm font-medium text-gray-700 mb-2">Model</h3>
              <p className="text-gray-900">{agent.llm_model}</p>
            </div>
          </div>

          <div className="grid grid-cols-3 gap-4">
            <div>
              <h3 className="text-sm font-medium text-gray-700 mb-2">Temperature</h3>
              <p className="text-gray-900">{agent.temperature}</p>
            </div>
            <div>
              <h3 className="text-sm font-medium text-gray-700 mb-2">Max Tokens</h3>
              <p className="text-gray-900">{agent.max_tokens}</p>
            </div>
            <div>
              <h3 className="text-sm font-medium text-gray-700 mb-2">Usage Count</h3>
              <p className="text-gray-900">{agent.usage_count}</p>
            </div>
          </div>

          {/* Tools Configuration */}
          {agent.tools_config && (
            <div>
              <div className="flex justify-between items-center mb-2">
                <h3 className="text-sm font-medium text-gray-700">Tools</h3>
                {/* Upload Files Button - only show if agent has knowledge_base tool */}
                {agent.tools_config.enabled_tools?.includes('knowledge_base') && (
                  <button
                    onClick={handleUploadFiles}
                    className="flex items-center space-x-1 px-3 py-1 text-xs bg-blue-600 text-white rounded-md hover:bg-blue-700 transition-colors"
                  >
                    <CloudArrowUpIcon className="w-3 h-3" />
                    <span>Upload Files</span>
                  </button>
                )}
              </div>
              <div className="bg-gray-50 p-3 rounded-lg">
                {agent.tools_config.enabled_tools ? (
                  <div className="flex flex-wrap gap-2">
                    {agent.tools_config.enabled_tools.map((tool: string, index: number) => (
                      <span
                        key={index}
                        className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-blue-100 text-blue-800"
                      >
                        🔧 {tool.replace('_', ' ')}
                      </span>
                    ))}
                  </div>
                ) : (
                  <p className="text-gray-500 text-sm">No tools configured</p>
                )}
              </div>
            </div>
          )}

          {/* Capabilities */}
          {agent.capabilities && agent.capabilities.length > 0 && (
            <div>
              <h3 className="text-sm font-medium text-gray-700 mb-2">Capabilities</h3>
              <div className="bg-gray-50 p-3 rounded-lg">
                <div className="flex flex-wrap gap-2">
                  {agent.capabilities.map((capability: string, index: number) => (
                    <span
                      key={index}
                      className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-green-100 text-green-800"
                    >
                      ⚡ {capability.replace('_', ' ')}
                    </span>
                  ))}
                </div>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

// Edit Agent Modal Component
interface EditAgentModalProps {
  agent: Agent;
  onClose: () => void;
  onSuccess: () => void;
  updateAgent: any;
}

const EditAgentModal: React.FC<EditAgentModalProps> = ({ agent, onClose, onSuccess, updateAgent }) => {
  const [formData, setFormData] = useState({
    name: agent.name,
    description: agent.description,
    agent_type: agent.agent_type,
    system_prompt: agent.system_prompt,
    personality: agent.personality || '',
    instructions: agent.instructions || '',
    tools_config: agent.tools_config || { enabled_tools: [] },
    capabilities: agent.capabilities || [],
    llm_provider: agent.llm_provider,
    llm_model: agent.llm_model,
    temperature: agent.temperature,
    max_tokens: agent.max_tokens,
  });

  // Available tools and capabilities (same as CreateAgentModal)
  const availableTools = [
    'knowledge_base', 'vanna_database', 'web_search', 'database', 'spreadsheet', 'calculator', 'document_analysis',
    'image_generator', 'writing_assistant', 'seo_tools', 'social_media',
    'project_tracker', 'calendar', 'communication', 'reporting',
    'analytics_tools', 'visualization', 'statistical_software',
    'financial_apis', 'citation', 'document_reader'
  ];

  const availableCapabilities = [
    'general_assistance', 'information_retrieval', 'problem_solving',
    'data_analysis', 'financial_modeling', 'report_generation',
    'information_gathering', 'source_verification', 'synthesis',
    'planning', 'scheduling', 'tracking', 'communication',
    'writing', 'editing', 'seo_optimization', 'content_strategy',
    'data_processing', 'statistical_analysis', 'visualization'
  ];

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    updateAgent.mutate({ id: agent.id, data: formData });
  };

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <div className="bg-white rounded-lg p-6 w-full max-w-2xl max-h-[90vh] overflow-y-auto">
        <div className="flex justify-between items-center mb-6">
          <h2 className="text-xl font-semibold text-gray-900">Edit Agent: {agent.name}</h2>
          <button onClick={onClose} className="text-gray-400 hover:text-gray-600">
            <XMarkIcon className="w-6 h-6" />
          </button>
        </div>

        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Agent Name *
            </label>
            <input
              type="text"
              required
              value={formData.name}
              onChange={(e) => setFormData({ ...formData, name: e.target.value })}
              className="input-field"
              placeholder="Enter agent name"
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Description *
            </label>
            <textarea
              required
              value={formData.description}
              onChange={(e) => setFormData({ ...formData, description: e.target.value })}
              className="input-field"
              rows={3}
              placeholder="Describe what this agent does"
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Agent Type *
            </label>
            <select
              required
              value={formData.agent_type}
              onChange={(e) => setFormData({ ...formData, agent_type: e.target.value })}
              className="input-field"
            >
              <option value="general">General Assistant</option>
              <option value="customer_service">Customer Service</option>
              <option value="research">Research Assistant</option>
              <option value="financial">Financial Advisor</option>
              <option value="content">Content Creator</option>
              <option value="data_analysis">Data Analyst</option>
            </select>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              System Prompt *
            </label>
            <textarea
              required
              value={formData.system_prompt}
              onChange={(e) => setFormData({ ...formData, system_prompt: e.target.value })}
              className="input-field"
              rows={4}
              placeholder="Define the agent's role and behavior"
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Personality
            </label>
            <input
              type="text"
              value={formData.personality}
              onChange={(e) => setFormData({ ...formData, personality: e.target.value })}
              className="input-field"
              placeholder="e.g., Professional, Friendly, Analytical"
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Special Instructions
            </label>
            <textarea
              value={formData.instructions}
              onChange={(e) => setFormData({ ...formData, instructions: e.target.value })}
              className="input-field"
              rows={3}
              placeholder="Any specific instructions or guidelines"
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Tools
            </label>
            <div className="grid grid-cols-2 gap-2 max-h-32 overflow-y-auto border border-gray-200 rounded p-2">
              {availableTools.map((tool) => (
                <label key={tool} className="flex items-center space-x-2">
                  <input
                    type="checkbox"
                    checked={formData.tools_config.enabled_tools.includes(tool)}
                    onChange={(e) => {
                      const tools = e.target.checked
                        ? [...formData.tools_config.enabled_tools, tool]
                        : formData.tools_config.enabled_tools.filter(t => t !== tool);
                      setFormData({
                        ...formData,
                        tools_config: { ...formData.tools_config, enabled_tools: tools }
                      });
                    }}
                    className="rounded border-gray-300"
                  />
                  <span className="text-sm">{tool.replace('_', ' ')}</span>
                </label>
              ))}
            </div>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Capabilities
            </label>
            <div className="grid grid-cols-2 gap-2 max-h-32 overflow-y-auto border border-gray-200 rounded p-2">
              {availableCapabilities.map((capability) => (
                <label key={capability} className="flex items-center space-x-2">
                  <input
                    type="checkbox"
                    checked={formData.capabilities.includes(capability)}
                    onChange={(e) => {
                      const capabilities = e.target.checked
                        ? [...formData.capabilities, capability]
                        : formData.capabilities.filter(c => c !== capability);
                      setFormData({ ...formData, capabilities });
                    }}
                    className="rounded border-gray-300"
                  />
                  <span className="text-sm">{capability.replace('_', ' ')}</span>
                </label>
              ))}
            </div>
          </div>

          {/* LLM Configuration */}
          <div className="border-t pt-4">
            <h3 className="text-lg font-medium text-gray-900 mb-4">LLM Configuration</h3>

            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  LLM Provider *
                </label>
                <select
                  required
                  value={formData.llm_provider}
                  onChange={(e) => setFormData({ ...formData, llm_provider: e.target.value })}
                  className="input-field"
                >
                  <option value="openai">OpenAI</option>
                  <option value="anthropic">Anthropic</option>
                  <option value="azure">Azure OpenAI</option>
                  <option value="local">Local Model</option>
                </select>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Model *
                </label>
                <select
                  required
                  value={formData.llm_model}
                  onChange={(e) => setFormData({ ...formData, llm_model: e.target.value })}
                  className="input-field"
                >
                  {formData.llm_provider === 'openai' && (
                    <>
                      <option value="gpt-4">GPT-4</option>
                      <option value="gpt-4-turbo">GPT-4 Turbo</option>
                      <option value="gpt-3.5-turbo">GPT-3.5 Turbo</option>
                    </>
                  )}
                  {formData.llm_provider === 'anthropic' && (
                    <>
                      <option value="claude-3-opus">Claude 3 Opus</option>
                      <option value="claude-3-sonnet">Claude 3 Sonnet</option>
                      <option value="claude-3-haiku">Claude 3 Haiku</option>
                    </>
                  )}
                  {formData.llm_provider === 'azure' && (
                    <>
                      <option value="gpt-4">Azure GPT-4</option>
                      <option value="gpt-35-turbo">Azure GPT-3.5 Turbo</option>
                    </>
                  )}
                  {formData.llm_provider === 'local' && (
                    <>
                      <option value="llama-2">Llama 2</option>
                      <option value="mistral">Mistral</option>
                    </>
                  )}
                </select>
              </div>
            </div>

            <div className="grid grid-cols-2 gap-4 mt-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Temperature
                </label>
                <input
                  type="number"
                  min="0"
                  max="2"
                  step="0.1"
                  value={formData.temperature}
                  onChange={(e) => setFormData({ ...formData, temperature: parseFloat(e.target.value) })}
                  className="input-field"
                  placeholder="0.7"
                />
                <p className="text-xs text-gray-500 mt-1">Controls randomness (0.0 = deterministic, 2.0 = very random)</p>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Max Tokens
                </label>
                <input
                  type="number"
                  min="1"
                  max="4000"
                  value={formData.max_tokens}
                  onChange={(e) => setFormData({ ...formData, max_tokens: parseInt(e.target.value) })}
                  className="input-field"
                  placeholder="1000"
                />
                <p className="text-xs text-gray-500 mt-1">Maximum number of tokens in the response</p>
              </div>
            </div>
          </div>

          <div className="flex justify-end space-x-3 pt-4">
            <button
              type="button"
              onClick={onClose}
              className="px-4 py-2 text-sm font-medium text-gray-700 bg-gray-100 border border-gray-300 rounded-md hover:bg-gray-200"
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={updateAgent.isPending}
              className="px-4 py-2 text-sm font-medium text-white bg-primary-600 border border-transparent rounded-md hover:bg-primary-700 disabled:opacity-50"
            >
              {updateAgent.isPending ? 'Updating...' : 'Update Agent'}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};

export default AgentsPage;
