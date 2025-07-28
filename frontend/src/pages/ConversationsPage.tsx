import React, { useState, useMemo, useEffect, useRef } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { useNavigate } from 'react-router-dom';
import toast from 'react-hot-toast';
import {
  ChatBubbleLeftRightIcon,
  TrashIcon,
  EyeIcon,
  ClockIcon,
  UserIcon,
  SparklesIcon,
  MagnifyingGlassIcon,
  FunnelIcon,
  ChevronRightIcon,
  ExclamationTriangleIcon,
  XMarkIcon
} from '@heroicons/react/24/outline';
import { api } from '../lib/simple-api';
// Local type definitions to avoid import issues
interface ConversationSummary {
  id: string;
  title?: string;
  created_at: string;
  last_activity: string;
  total_messages: number;
  primary_intent?: string;
  agents_used: number[];
}

interface MessageHistory {
  message_index: number;
  user_message: string;
  agent_response?: string;
  intent_category?: string;
  confidence_score?: number;
  selected_agent_id?: number;
  created_at: string;
}

interface ConversationDetail {
  conversation: ConversationSummary;
  messages: MessageHistory[];
}

const ConversationsPage: React.FC = () => {
  const [selectedConversation, setSelectedConversation] = useState<ConversationSummary | null>(null);
  const [showConversationDetail, setShowConversationDetail] = useState(false);
  const [searchTerm, setSearchTerm] = useState('');
  const [filterIntent, setFilterIntent] = useState<string>('all');
  const navigate = useNavigate();
  const queryClient = useQueryClient();
  const searchInputRef = useRef<HTMLInputElement>(null);

  // Keyboard shortcuts
  useEffect(() => {
    const handleKeyDown = (event: KeyboardEvent) => {
      // Ctrl/Cmd + K to focus search
      if ((event.ctrlKey || event.metaKey) && event.key === 'k') {
        event.preventDefault();
        searchInputRef.current?.focus();
      }
      // Escape to clear search
      if (event.key === 'Escape' && searchTerm) {
        setSearchTerm('');
        searchInputRef.current?.blur();
      }
    };

    document.addEventListener('keydown', handleKeyDown);
    return () => document.removeEventListener('keydown', handleKeyDown);
  }, [searchTerm]);

  // Fetch conversations
  const { data: conversations = [], isLoading, error } = useQuery({
    queryKey: ['conversations'],
    queryFn: () => api.getConversations({ limit: 100 }),
  });

  // Fetch conversation detail
  const { data: conversationDetail, isLoading: detailLoading } = useQuery({
    queryKey: ['conversation-detail', selectedConversation?.id],
    queryFn: () => selectedConversation ? api.getConversation(selectedConversation.id) : null,
    enabled: !!selectedConversation && showConversationDetail,
  });

  // Delete conversation mutation
  const deleteConversation = useMutation({
    mutationFn: (conversationId: string) => api.deleteConversation(conversationId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['conversations'] });
      toast.success('Conversation supprimée avec succès');
      if (selectedConversation && showConversationDetail) {
        setShowConversationDetail(false);
        setSelectedConversation(null);
      }
    },
    onError: () => {
      toast.error('Erreur lors de la suppression de la conversation');
    },
  });

  // Filter conversations based on search and intent with memoization for performance
  const filteredConversations = useMemo(() => {
    if (!conversations || conversations.length === 0) return [];

    return conversations.filter((conv: ConversationSummary) => {
      // Enhanced search functionality
      const searchLower = searchTerm.toLowerCase().trim();
      const matchesSearch = !searchTerm ||
        // Search in title
        (conv.title && conv.title.toLowerCase().includes(searchLower)) ||
        // Search in conversation ID (full and partial)
        conv.id.toLowerCase().includes(searchLower) ||
        // Search in primary intent
        (conv.primary_intent && conv.primary_intent.toLowerCase().includes(searchLower)) ||
        // Search in formatted date
        formatDate(conv.last_activity).toLowerCase().includes(searchLower) ||
        formatDate(conv.created_at).toLowerCase().includes(searchLower) ||
        // Search by message count
        conv.total_messages.toString().includes(searchLower);

      const matchesIntent = filterIntent === 'all' || conv.primary_intent === filterIntent;

      return matchesSearch && matchesIntent;
    });
  }, [conversations, searchTerm, filterIntent]);

  // Get unique intents for filter
  const uniqueIntents = Array.from(new Set(
    conversations
      .map((conv: ConversationSummary) => conv.primary_intent)
      .filter((intent: string | undefined): intent is string => Boolean(intent))
  ));

  const handleViewConversation = (conversation: ConversationSummary) => {
    setSelectedConversation(conversation);
    setShowConversationDetail(true);
  };

  const handleDeleteConversation = (conversationId: string, event: React.MouseEvent) => {
    event.stopPropagation();
    if (confirm('Êtes-vous sûr de vouloir supprimer cette conversation ?')) {
      deleteConversation.mutate(conversationId);
    }
  };

  const handleContinueConversation = (conversationId: string) => {
    navigate(`/chat?conversation=${conversationId}`);
  };

  const formatDate = (dateString: string) => {
    const date = new Date(dateString);
    const now = new Date();
    const diffInHours = (now.getTime() - date.getTime()) / (1000 * 60 * 60);

    if (diffInHours < 1) {
      return 'Il y a moins d\'une heure';
    } else if (diffInHours < 24) {
      return `Il y a ${Math.floor(diffInHours)} heure${Math.floor(diffInHours) > 1 ? 's' : ''}`;
    } else if (diffInHours < 168) { // 7 days
      const days = Math.floor(diffInHours / 24);
      return `Il y a ${days} jour${days > 1 ? 's' : ''}`;
    } else {
      return date.toLocaleDateString('fr-FR', {
        year: 'numeric',
        month: 'short',
        day: 'numeric'
      });
    }
  };

  const getIntentIcon = (intent?: string) => {
    switch (intent) {
      case 'research':
        return '🔬';
      case 'customer_service':
        return '🎧';
      case 'financial_analysis':
        return '📊';
      case 'data_analysis':
        return '📈';
      case 'general':
        return '💬';
      default:
        return '🤖';
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-900 via-gray-900 to-slate-800">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Header Section */}
        <div className="text-center mb-8">
          <div className="inline-flex items-center justify-center w-16 h-16 bg-gradient-to-br from-purple-500 to-purple-600 rounded-2xl mb-4 shadow-lg shadow-purple-500/25">
            <ChatBubbleLeftRightIcon className="w-8 h-8 text-white" />
          </div>
          <h1 className="text-3xl font-bold text-white mb-2">Conversations</h1>
          <p className="text-slate-400 text-lg">Consultez et gérez votre historique de conversations</p>
        </div>

        {/* Search and Filter Bar */}
        <div className="bg-white rounded-2xl shadow-lg p-6 mb-8">
          <div className="flex flex-col sm:flex-row gap-4">
            <div className="flex-1 relative">
              <MagnifyingGlassIcon className="w-5 h-5 text-gray-400 absolute left-3 top-1/2 transform -translate-y-1/2" />
              <input
                ref={searchInputRef}
                type="text"
                placeholder="Rechercher par titre, ID, type, date... (Ctrl+K)"
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                className="w-full pl-10 pr-12 py-3 border border-gray-200 rounded-xl focus:ring-2 focus:ring-purple-500 focus:border-transparent transition-all duration-200"
              />
              {searchTerm && (
                <button
                  onClick={() => setSearchTerm('')}
                  className="absolute right-3 top-1/2 transform -translate-y-1/2 text-gray-400 hover:text-gray-600 transition-colors"
                  title="Effacer la recherche"
                >
                  <XMarkIcon className="w-5 h-5" />
                </button>
              )}
            </div>
            <div className="relative">
              <FunnelIcon className="w-5 h-5 text-gray-400 absolute left-3 top-1/2 transform -translate-y-1/2" />
              <select
                value={filterIntent}
                onChange={(e) => setFilterIntent(e.target.value)}
                className="pl-10 pr-8 py-3 border border-gray-200 rounded-xl focus:ring-2 focus:ring-purple-500 focus:border-transparent bg-white"
              >
                <option value="all">Tous les types</option>
                {uniqueIntents.map((intent) => (
                  <option key={intent} value={intent}>
                    {intent?.replace('_', ' ') || 'Non défini'}
                  </option>
                ))}
              </select>
            </div>
          </div>

          {/* Search Results Indicator */}
          {(searchTerm || filterIntent !== 'all') && (
            <div className="mt-4 pt-4 border-t border-gray-200">
              <div className="flex items-center justify-between">
                <div className="flex items-center space-x-2 text-sm text-gray-600">
                  <span>
                    {filteredConversations.length} résultat{filteredConversations.length !== 1 ? 's' : ''} trouvé{filteredConversations.length !== 1 ? 's' : ''}
                  </span>
                  {searchTerm && (
                    <span className="bg-purple-100 text-purple-700 px-2 py-1 rounded-lg">
                      "{searchTerm}"
                    </span>
                  )}
                  {filterIntent !== 'all' && (
                    <span className="bg-blue-100 text-blue-700 px-2 py-1 rounded-lg">
                      {filterIntent.replace('_', ' ')}
                    </span>
                  )}
                </div>
                <button
                  onClick={() => {
                    setSearchTerm('');
                    setFilterIntent('all');
                  }}
                  className="text-sm text-gray-500 hover:text-gray-700 transition-colors"
                >
                  Effacer les filtres
                </button>
              </div>
            </div>
          )}
        </div>

        {/* Main Content */}
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
          {/* Conversations List */}
          <div className="lg:col-span-2">
            <div className="bg-white rounded-2xl shadow-lg">
              <div className="p-6 border-b border-gray-200">
                <div className="flex items-center justify-between">
                  <div className="flex items-center">
                    <div className="w-8 h-8 bg-purple-100 rounded-lg flex items-center justify-center mr-3">
                      <ChatBubbleLeftRightIcon className="w-4 h-4 text-purple-600" />
                    </div>
                    <div>
                      <h3 className="text-xl font-bold text-gray-900">Historique des Conversations</h3>
                      <p className="text-gray-600 mt-1">
                        {filteredConversations.length} conversation{filteredConversations.length !== 1 ? 's' : ''} trouvée{filteredConversations.length !== 1 ? 's' : ''}
                      </p>
                    </div>
                  </div>
                </div>
              </div>

              <div className="p-6">
                {isLoading ? (
                  <div className="text-center py-12">
                    <div className="animate-spin rounded-full h-10 w-10 border-b-2 border-purple-500 mx-auto mb-4"></div>
                    <p className="text-gray-600">Chargement des conversations...</p>
                  </div>
                ) : error ? (
                  <div className="text-center py-12">
                    <div className="w-16 h-16 bg-red-100 rounded-2xl flex items-center justify-center mx-auto mb-4">
                      <ExclamationTriangleIcon className="w-8 h-8 text-red-600" />
                    </div>
                    <p className="text-red-600 text-lg">Erreur lors du chargement des conversations.</p>
                    <p className="text-gray-500 mt-1">Veuillez réessayer.</p>
                  </div>
                ) : filteredConversations.length === 0 ? (
                  <div className="text-center py-16">
                    <div className="w-20 h-20 bg-gray-100 rounded-2xl flex items-center justify-center mx-auto mb-6">
                      <ChatBubbleLeftRightIcon className="w-10 h-10 text-gray-400" />
                    </div>
                    <h3 className="text-2xl font-bold text-gray-900 mb-3">
                      {searchTerm || filterIntent !== 'all' ? 'Aucune conversation trouvée' : 'Aucune conversation pour le moment'}
                    </h3>
                    <p className="text-gray-600 text-lg mb-8 max-w-md mx-auto">
                      {searchTerm || filterIntent !== 'all'
                        ? 'Essayez de modifier vos critères de recherche'
                        : 'Commencez une nouvelle conversation pour voir votre historique ici'
                      }
                    </p>
                    {!searchTerm && filterIntent === 'all' && (
                      <button
                        onClick={() => navigate('/chat')}
                        className="px-8 py-4 bg-gradient-to-r from-purple-500 to-purple-600 text-white rounded-xl font-medium hover:from-purple-600 hover:to-purple-700 transition-all duration-300 shadow-lg shadow-purple-500/25"
                      >
                        Commencer une Conversation
                      </button>
                    )}
                  </div>
                ) : (
                  <div className="space-y-4">
                    {filteredConversations.map((conversation: ConversationSummary) => (
                      <ConversationCard
                        key={conversation.id}
                        conversation={conversation}
                        onView={() => handleViewConversation(conversation)}
                        onDelete={(e) => handleDeleteConversation(conversation.id, e)}
                        onContinue={() => handleContinueConversation(conversation.id)}
                        formatDate={formatDate}
                        getIntentIcon={getIntentIcon}
                        isDeleting={deleteConversation.isPending}
                        searchTerm={searchTerm}
                      />
                    ))}
                  </div>
                )}
              </div>
            </div>
          </div>

          {/* Conversation Detail Panel */}
          <div className="lg:col-span-1">
            <div className="bg-white rounded-2xl shadow-lg sticky top-8">
              <div className="p-6 border-b border-gray-200">
                <h3 className="text-xl font-bold text-gray-900">Détails de la Conversation</h3>
              </div>
              <div className="p-6">
                {!selectedConversation ? (
                  <div className="text-center py-12">
                    <div className="w-16 h-16 bg-gray-100 rounded-2xl flex items-center justify-center mx-auto mb-4">
                      <EyeIcon className="w-8 h-8 text-gray-400" />
                    </div>
                    <p className="text-gray-500">Sélectionnez une conversation pour voir les détails</p>
                  </div>
                ) : detailLoading ? (
                  <div className="text-center py-12">
                    <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-purple-500 mx-auto mb-4"></div>
                    <p className="text-gray-600">Chargement des détails...</p>
                  </div>
                ) : conversationDetail ? (
                  <ConversationDetailView
                    detail={conversationDetail}
                    formatDate={formatDate}
                    getIntentIcon={getIntentIcon}
                  />
                ) : (
                  <div className="text-center py-12">
                    <p className="text-red-500">Erreur lors du chargement des détails</p>
                  </div>
                )}
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

// Conversation Card Component
interface ConversationCardProps {
  conversation: ConversationSummary;
  onView: () => void;
  onDelete: (e: React.MouseEvent) => void;
  onContinue: () => void;
  formatDate: (date: string) => string;
  getIntentIcon: (intent?: string) => string;
  isDeleting: boolean;
  searchTerm?: string;
}

const ConversationCard: React.FC<ConversationCardProps> = ({
  conversation,
  onView,
  onDelete,
  onContinue,
  formatDate,
  getIntentIcon,
  isDeleting,
  searchTerm = ''
}) => {
  // Helper function to highlight search terms
  const highlightText = (text: string, search: string) => {
    if (!search.trim()) return text;

    const regex = new RegExp(`(${search.replace(/[.*+?^${}()|[\]\\]/g, '\\$&')})`, 'gi');
    const parts = text.split(regex);

    return parts.map((part, index) =>
      regex.test(part) ? (
        <mark key={index} className="bg-yellow-200 text-yellow-900 px-1 rounded">
          {part}
        </mark>
      ) : part
    );
  };
  return (
    <div className="bg-gray-50 border border-gray-200 rounded-xl p-6 hover:bg-gray-100 transition-all duration-300 cursor-pointer group">
      <div onClick={onView}>
        <div className="flex items-start justify-between mb-4">
          <div className="flex items-center space-x-3">
            <div className="w-12 h-12 bg-purple-100 rounded-xl flex items-center justify-center text-2xl">
              {getIntentIcon(conversation.primary_intent)}
            </div>
            <div>
              <h4 className="font-bold text-gray-900 text-lg">
                {highlightText(
                  conversation.title || `Conversation ${conversation.id.slice(0, 8)}`,
                  searchTerm
                )}
              </h4>
              <div className="flex items-center space-x-2 text-sm text-gray-600">
                <ClockIcon className="w-4 h-4" />
                <span>{formatDate(conversation.last_activity)}</span>
              </div>
            </div>
          </div>
          <ChevronRightIcon className="w-5 h-5 text-gray-400 group-hover:text-gray-600 transition-colors" />
        </div>

        <div className="flex items-center justify-between text-sm text-gray-600 mb-4">
          <div className="flex items-center space-x-4">
            <div className="flex items-center space-x-1">
              <ChatBubbleLeftRightIcon className="w-4 h-4" />
              <span>{conversation.total_messages} message{conversation.total_messages !== 1 ? 's' : ''}</span>
            </div>
            {conversation.primary_intent && (
              <div className="flex items-center space-x-1">
                <SparklesIcon className="w-4 h-4" />
                <span className="capitalize">
                  {highlightText(conversation.primary_intent.replace('_', ' '), searchTerm)}
                </span>
              </div>
            )}
          </div>
        </div>

        {conversation.agents_used && conversation.agents_used.length > 0 && (
          <div className="mb-4">
            <p className="text-xs font-medium text-gray-600 mb-2">Agents utilisés:</p>
            <div className="flex flex-wrap gap-2">
              {conversation.agents_used.slice(0, 3).map((agentId: number, idx: number) => (
                <span key={idx} className="text-xs bg-blue-100 text-blue-700 px-2 py-1 rounded-lg">
                  Agent {agentId}
                </span>
              ))}
              {conversation.agents_used.length > 3 && (
                <span className="text-xs text-gray-500 bg-gray-200 px-2 py-1 rounded-lg">
                  +{conversation.agents_used.length - 3} autres
                </span>
              )}
            </div>
          </div>
        )}
      </div>

      {/* Action Buttons */}
      <div className="flex items-center justify-between pt-4 border-t border-gray-200">
        <button
          onClick={onView}
          className="flex items-center space-x-2 px-4 py-2 bg-purple-100 text-purple-700 rounded-lg hover:bg-purple-200 transition-all duration-300 text-sm font-medium"
        >
          <EyeIcon className="w-4 h-4" />
          <span>Voir Détails</span>
        </button>

        <div className="flex items-center space-x-2">
          <button
            onClick={onContinue}
            className="flex items-center space-x-2 px-4 py-2 bg-green-100 text-green-700 rounded-lg hover:bg-green-200 transition-all duration-300 text-sm font-medium"
          >
            <ChatBubbleLeftRightIcon className="w-4 h-4" />
            <span>Continuer</span>
          </button>

          <button
            onClick={onDelete}
            disabled={isDeleting}
            className="flex items-center space-x-2 px-4 py-2 bg-red-100 text-red-700 rounded-lg hover:bg-red-200 transition-all duration-300 text-sm font-medium disabled:opacity-50"
          >
            <TrashIcon className="w-4 h-4" />
            <span>Supprimer</span>
          </button>
        </div>
      </div>
    </div>
  );
};

// Conversation Detail View Component
interface ConversationDetailViewProps {
  detail: ConversationDetail;
  formatDate: (date: string) => string;
  getIntentIcon: (intent?: string) => string;
}

const ConversationDetailView: React.FC<ConversationDetailViewProps> = ({
  detail,
  formatDate,
  getIntentIcon
}) => {
  const { conversation, messages } = detail;

  return (
    <div className="space-y-6">
      {/* Conversation Info */}
      <div>
        <h4 className="font-bold text-gray-900 mb-3">
          {conversation.title || `Conversation ${conversation.id.slice(0, 8)}`}
        </h4>

        <div className="space-y-3">
          <div className="flex items-center justify-between text-sm">
            <span className="text-gray-600">Créée:</span>
            <span className="text-gray-900">{formatDate(conversation.created_at)}</span>
          </div>

          <div className="flex items-center justify-between text-sm">
            <span className="text-gray-600">Dernière activité:</span>
            <span className="text-gray-900">{formatDate(conversation.last_activity)}</span>
          </div>

          <div className="flex items-center justify-between text-sm">
            <span className="text-gray-600">Messages:</span>
            <span className="text-gray-900">{conversation.total_messages}</span>
          </div>

          {conversation.primary_intent && (
            <div className="flex items-center justify-between text-sm">
              <span className="text-gray-600">Type principal:</span>
              <div className="flex items-center space-x-1">
                <span>{getIntentIcon(conversation.primary_intent)}</span>
                <span className="text-gray-900 capitalize">
                  {conversation.primary_intent.replace('_', ' ')}
                </span>
              </div>
            </div>
          )}
        </div>
      </div>

      {/* Messages Preview */}
      <div>
        <h5 className="font-medium text-gray-900 mb-3">Aperçu des Messages</h5>
        <div className="space-y-3 max-h-96 overflow-y-auto">
          {messages.slice(0, 5).map((message, index) => (
            <div key={index} className="border border-gray-200 rounded-lg p-3">
              <div className="flex items-center space-x-2 mb-2">
                <UserIcon className="w-4 h-4 text-blue-600" />
                <span className="text-sm font-medium text-gray-900">Utilisateur</span>
                <span className="text-xs text-gray-500">
                  {formatDate(message.created_at)}
                </span>
              </div>
              <p className="text-sm text-gray-700 mb-2 line-clamp-2">
                {message.user_message}
              </p>

              {message.agent_response && (
                <>
                  <div className="flex items-center space-x-2 mb-2">
                    <div className="w-4 h-4 bg-purple-100 rounded flex items-center justify-center">
                      <span className="text-xs">🤖</span>
                    </div>
                    <span className="text-sm font-medium text-gray-900">Assistant</span>
                    {message.confidence_score && (
                      <span className="text-xs text-gray-500">
                        ({Math.round(message.confidence_score * 100)}% confiance)
                      </span>
                    )}
                  </div>
                  <p className="text-sm text-gray-700 line-clamp-3">
                    {message.agent_response}
                  </p>
                </>
              )}
            </div>
          ))}

          {messages.length > 5 && (
            <div className="text-center py-2">
              <span className="text-sm text-gray-500">
                ... et {messages.length - 5} message{messages.length - 5 !== 1 ? 's' : ''} de plus
              </span>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default ConversationsPage;
