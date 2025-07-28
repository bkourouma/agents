import React, { useState, useEffect } from 'react';
import ReactMarkdown from 'react-markdown';
import { api } from '../lib/simple-api';
import ChatArtifact from '../components/Chat/ChatArtifact';

type ArtifactType =
  | 'database-table'
  | 'data-visualization'
  | 'code-snippet'
  | 'formatted-text'
  | 'json-data'
  | 'report';

interface ArtifactData {
  id: string;
  type: ArtifactType;
  title: string;
  content: any;
  metadata?: Record<string, any>;
}

interface ChatMessage {
  id: string;
  content: string;
  type: 'user' | 'assistant' | 'system';
  timestamp: string;
  agent_name?: string;
  intent_category?: string;
  confidence?: number;
  debug_info?: string;
  metadata?: {
    database_result?: any;
    artifacts?: ArtifactData[];
    tool_used?: string;
    execution_time?: number;
    [key: string]: any;
  };
}

// Modern Debug Info Component
const DebugInfoSection: React.FC<{ debug_info: string }> = ({ debug_info }) => {
  const [isExpanded, setIsExpanded] = useState(false);

  return (
    <div className="mt-3 border-t border-gray-200/50 pt-3">
      <button
        onClick={() => setIsExpanded(!isExpanded)}
        className="flex items-center gap-2 text-xs text-gray-500 hover:text-gray-700 transition-colors duration-300 group"
      >
        <div className="w-4 h-4 bg-gray-100 rounded-full flex items-center justify-center group-hover:bg-gray-200 transition-colors">
          <svg
            className={`w-2.5 h-2.5 transition-transform duration-300 ${isExpanded ? 'rotate-90' : ''}`}
            fill="none"
            stroke="currentColor"
            viewBox="0 0 24 24"
          >
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
          </svg>
        </div>
        <span className="font-medium">Informations de débogage</span>
      </button>
      {isExpanded && (
        <div className="mt-3 p-3 bg-gradient-to-br from-gray-50 to-gray-100 rounded-lg border border-gray-200/50 shadow-sm animate-slideUp">
          <div className="text-xs text-gray-600 font-mono whitespace-pre-wrap leading-relaxed">
            {debug_info}
          </div>
        </div>
      )}
    </div>
  );
};



interface Agent {
  id: number;
  name: string;
  description: string;
  agent_type: string;
  status: string;
}

const ChatPage: React.FC = () => {
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [inputMessage, setInputMessage] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [conversationId, setConversationId] = useState<string | undefined>();
  const [selectedAgent, setSelectedAgent] = useState<number | null>(null);
  const [agents, setAgents] = useState<Agent[]>([]);
  const [loadingAgents, setLoadingAgents] = useState(true);
  const [artifactHistory, setArtifactHistory] = useState<ArtifactData[]>([]);
  const [currentArtifact, setCurrentArtifact] = useState<ArtifactData | null>(null);
  const [showArtifactPanel, setShowArtifactPanel] = useState(false);

  // Utility function to detect if content should create an artifact
  const shouldCreateArtifact = (content: string, metadata?: any): boolean => {
    if (metadata?.database_result?.data?.length > 0) return true;
    if (content.length > 1000) return true;
    const hasTablePattern = /\|.*\|.*\|/.test(content);
    const hasJsonPattern = /^\s*[\{\[]/.test(content.trim());
    const hasCodePattern = /```/.test(content);
    return hasTablePattern || hasJsonPattern || hasCodePattern;
  };

  // Utility function to detect artifact type
  const detectArtifactType = (content: string, metadata?: any): ArtifactType => {
    if (metadata?.database_result) return 'database-table';
    if (metadata?.tool_used === 'vanna_database') return 'database-table';
    if (content.includes('```sql') || content.includes('SELECT ')) return 'code-snippet';
    if (content.includes('```')) return 'code-snippet';
    const trimmed = content.trim();
    if ((trimmed.startsWith('{') && trimmed.endsWith('}')) ||
        (trimmed.startsWith('[') && trimmed.endsWith(']'))) return 'json-data';
    if (/\|.*\|.*\|/.test(content)) return 'database-table';
    return 'formatted-text';
  };

  // Create artifact from message
  const createArtifactFromMessage = (message: ChatMessage): ArtifactData | null => {
    if (!shouldCreateArtifact(message.content, message.metadata)) return null;

    const type = detectArtifactType(message.content, message.metadata);
    let content: any = message.content;
    let title = `${type.replace('-', ' ').replace(/\b\w/g, l => l.toUpperCase())}`;

    if (message.metadata?.database_result) {
      const dbResult = message.metadata.database_result;
      content = {
        data: dbResult.data,
        columns: dbResult.columns,
        sql: dbResult.sql,
        execution_time_ms: dbResult.execution_time_ms,
        row_count: dbResult.row_count
      };
      title = `Query Results (${dbResult.row_count || 0} rows)`;
    }

    if (type === 'json-data') {
      try {
        content = JSON.parse(message.content);
        title = 'JSON Data';
      } catch (e) {
        // Keep as text if parsing fails
      }
    }

    return {
      id: `artifact-${message.id}-${Date.now()}`,
      type,
      title,
      content,
      metadata: message.metadata
    };
  };

  // Handle new messages with artifact detection
  const handleNewMessage = (message: ChatMessage) => {
    // Add message to chat
    setMessages(prev => [...prev, message]);

    // Extract and store artifacts
    if (message.metadata?.artifacts) {
      setArtifactHistory(prev => [...prev, ...message.metadata.artifacts]);
      // Show the first artifact in the side panel
      const firstArtifact = message.metadata.artifacts[0];
      if (firstArtifact) {
        setCurrentArtifact(firstArtifact);
        setShowArtifactPanel(true);
      }
    } else {
      // Try to create artifact from message content
      const artifact = createArtifactFromMessage(message);
      if (artifact) {
        setArtifactHistory(prev => [...prev, artifact]);
        setCurrentArtifact(artifact);
        setShowArtifactPanel(true);
        // Update message with artifact reference
        message.metadata = {
          ...message.metadata,
          artifacts: [artifact]
        };
      }
    }
  };

  const handleRerunQuery = async (sql: string) => {
    if (!selectedAgent) return;

    try {
      setIsLoading(true);
      const response = await api.chatWithAgent(selectedAgent, sql, conversationId);

      const assistantMessage: ChatMessage = {
        id: Date.now().toString(),
        type: 'assistant',
        content: response.response,
        timestamp: new Date().toISOString(),
        agent_name: agents.find(a => a.id === selectedAgent)?.name,
        metadata: response.metadata
      };

      handleNewMessage(assistantMessage);
    } catch (error) {
      console.error('Failed to rerun query:', error);
    } finally {
      setIsLoading(false);
    }
  };

  const handleArtifactClick = (artifact: ArtifactData) => {
    setCurrentArtifact(artifact);
    setShowArtifactPanel(true);
  };

  const handleCloseArtifactPanel = () => {
    setShowArtifactPanel(false);
    setCurrentArtifact(null);
  };

  // Load agents on component mount
  useEffect(() => {
    const loadAgents = async () => {
      try {
        const agentsData = await api.getAgents();
        setAgents(agentsData.filter((agent: Agent) => agent.status === 'active'));
      } catch (error) {
        console.error('Failed to load agents:', error);
      } finally {
        setLoadingAgents(false);
      }
    };
    loadAgents();
  }, []);

  const handleSendMessage = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!inputMessage.trim() || isLoading) return;

    const userMessage: ChatMessage = {
      id: Date.now().toString(),
      type: 'user',
      content: inputMessage,
      timestamp: new Date().toISOString(),
    };

    setMessages(prev => [...prev, userMessage]);
    setInputMessage('');
    setIsLoading(true);

    try {
      let response;

      if (selectedAgent) {
        // Direct chat with selected agent
        response = await api.chatWithAgent(selectedAgent, inputMessage, conversationId);

        const assistantMessage: ChatMessage = {
          id: (Date.now() + 1).toString(),
          type: 'assistant',
          content: response.response,
          timestamp: new Date().toISOString(),
          agent_name: agents.find(a => a.id === selectedAgent)?.name,
          metadata: response.metadata
        };

        handleNewMessage(assistantMessage);
        setConversationId(response.conversation_id);
      } else {
        // Use orchestrated chat
        response = await api.orchestratedChat({
          message: inputMessage,
          conversation_id: conversationId,
        });

        const assistantMessage: ChatMessage = {
          id: (Date.now() + 1).toString(),
          type: 'assistant',
          content: response.agent_response,
          timestamp: new Date().toISOString(),
          agent_name: response.routing_result.selected_agent?.agent_name,
          intent_category: response.routing_result.intent_analysis.category,
          confidence: response.routing_result.confidence,
          debug_info: response.debug_info,
          metadata: response.metadata
        };

        handleNewMessage(assistantMessage);
        setConversationId(response.conversation_id);
      }

    } catch (error) {
      console.error('Chat error:', error);
      const errorMessage: ChatMessage = {
        id: (Date.now() + 1).toString(),
        type: 'system',
        content: 'Désolé, j\'ai rencontré une erreur. Veuillez réessayer.',
        timestamp: new Date().toISOString(),
      };
      setMessages(prev => [...prev, errorMessage]);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 via-blue-50 to-indigo-50 flex flex-col">
      {/* Modern Header */}
      <div className="relative bg-white/80 backdrop-blur-sm shadow-lg border-b border-gray-200/50 flex-shrink-0">
        <div className="absolute inset-0 bg-gradient-to-r from-blue-600/5 via-purple-600/5 to-indigo-600/5"></div>
        <div className="relative p-4 sm:p-6">
          <div className="max-w-7xl mx-auto">
            <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4 mb-6">
              <div className="flex items-center space-x-4">
                <div className="flex-shrink-0">
                  <div className="w-12 h-12 bg-gradient-to-br from-blue-500 to-indigo-600 rounded-xl flex items-center justify-center shadow-lg">
                    <svg className="w-6 h-6 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 12h.01M12 12h.01M16 12h.01M21 12c0 4.418-4.03 8-9 8a9.863 9.863 0 01-4.255-.949L3 20l1.395-3.72C3.512 15.042 3 13.574 3 12c0-4.418 4.03-8 9-8s9 3.582 9 8z" />
                    </svg>
                  </div>
                </div>
                <div>
                  <h1 className="text-2xl sm:text-3xl font-bold bg-gradient-to-r from-gray-900 via-blue-800 to-indigo-800 bg-clip-text text-transparent">
                    Chat Agent IA
                  </h1>
                  <p className="mt-1 text-sm sm:text-base text-gray-600">
                    {selectedAgent
                      ? `Discussion directe avec ${agents.find(a => a.id === selectedAgent)?.name || 'agent sélectionné'}`
                      : 'Discutez naturellement - notre orchestrateur vous dirigera vers le bon agent'
                    }
                  </p>
                </div>
              </div>

              {/* Status Indicator */}
              <div className="flex items-center space-x-2">
                <div className="flex items-center space-x-2 bg-white/60 backdrop-blur-sm rounded-lg px-3 py-2 border border-gray-200/50 shadow-sm">
                  <div className="w-2 h-2 bg-green-500 rounded-full animate-pulse"></div>
                  <span className="text-sm font-medium text-gray-700">En ligne</span>
                </div>
              </div>
            </div>

            {/* Modern Agent Selection */}
            <div className="bg-white/60 backdrop-blur-sm rounded-xl p-4 border border-gray-200/50 shadow-sm">
              <div className="flex flex-col sm:flex-row sm:items-center gap-4">
                <div className="flex items-center space-x-3">
                  <div className="w-8 h-8 bg-gradient-to-br from-purple-500 to-indigo-600 rounded-lg flex items-center justify-center">
                    <svg className="w-4 h-4 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9.663 17h4.673M12 3v1m6.364 1.636l-.707.707M21 12h-1M4 12H3m3.343-5.657l-.707-.707m2.828 9.9a5 5 0 117.072 0l-.548.547A3.374 3.374 0 0014 18.469V19a2 2 0 11-4 0v-.531c0-.895-.356-1.754-.988-2.386l-.548-.547z" />
                    </svg>
                  </div>
                  <label className="text-sm font-medium text-gray-700">
                    Choisir un agent :
                  </label>
                </div>
                <select
                  value={selectedAgent || ''}
                  onChange={(e) => setSelectedAgent(e.target.value ? Number(e.target.value) : null)}
                  className="flex-1 sm:max-w-md bg-white/80 backdrop-blur-sm border border-gray-300/50 rounded-lg px-4 py-2 text-sm focus:ring-2 focus:ring-blue-500 focus:border-blue-500 transition-all duration-300"
                  disabled={loadingAgents}
                >
                  <option value="">🤖 Routage automatique (Sélection intelligente)</option>
                  {agents.map((agent) => (
                    <option key={agent.id} value={agent.id}>
                      {agent.name} - {agent.description}
                    </option>
                  ))}
                </select>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Modern Main Content Area */}
      <div className="flex-1 flex overflow-hidden relative">
        <div className="absolute inset-0 bg-white/30 backdrop-blur-sm"></div>

        {/* Chat Panel */}
        <div className={`${showArtifactPanel ? 'w-1/2' : 'w-full'} flex flex-col transition-all duration-500 ease-in-out relative z-10`}>
          <div className="h-full bg-white/50 backdrop-blur-sm rounded-t-2xl shadow-xl border border-gray-200/50 overflow-hidden mx-4 mb-4">

            {/* Messages Area */}
            <div className="flex-1 overflow-y-auto p-4 sm:p-6 space-y-4"
                 style={{
                   background: 'linear-gradient(135deg, rgba(255,255,255,0.1) 0%, rgba(255,255,255,0.05) 100%)'
                 }}>
            {messages.length === 0 ? (
              <div className="flex flex-col items-center justify-center h-full text-center animate-fadeIn">
                <div className="relative mb-8">
                  <div className="w-24 h-24 bg-gradient-to-br from-blue-500 to-indigo-600 rounded-full flex items-center justify-center shadow-2xl animate-scaleIn">
                    <svg className="w-12 h-12 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 12h.01M12 12h.01M16 12h.01M21 12c0 4.418-4.03 8-9 8a9.863 9.863 0 01-4.255-.949L3 20l1.395-3.72C3.512 15.042 3 13.574 3 12c0-4.418 4.03-8 9-8s9 3.582 9 8z" />
                    </svg>
                  </div>
                  <div className="absolute -top-2 -right-2 w-6 h-6 bg-green-500 rounded-full border-2 border-white animate-pulse"></div>
                </div>

                <div className="max-w-md space-y-4">
                  {selectedAgent ? (
                    <div className="space-y-3">
                      <h3 className="text-xl font-bold text-gray-900">
                        Prêt à discuter avec {agents.find(a => a.id === selectedAgent)?.name} !
                      </h3>
                      <p className="text-gray-600">
                        Cet agent a accès à des connaissances et capacités spécifiques.
                      </p>
                      <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
                        <p className="text-sm text-blue-700">
                          💡 <strong>Conseil :</strong> Posez des questions spécifiques liées à l'expertise de cet agent pour de meilleurs résultats.
                        </p>
                      </div>
                    </div>
                  ) : (
                    <div className="space-y-3">
                      <h3 className="text-xl font-bold text-gray-900">
                        Démarrez une conversation !
                      </h3>
                      <p className="text-gray-600">
                        Je vous dirigerai intelligemment vers le meilleur agent pour vos besoins.
                      </p>
                      <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 mt-6">
                        <div className="bg-gradient-to-br from-blue-50 to-indigo-50 border border-blue-200 rounded-lg p-3">
                          <p className="text-sm text-blue-700 font-medium">💼 Affaires</p>
                          <p className="text-xs text-blue-600 mt-1">"J'ai besoin d'aide avec la facturation"</p>
                        </div>
                        <div className="bg-gradient-to-br from-purple-50 to-pink-50 border border-purple-200 rounded-lg p-3">
                          <p className="text-sm text-purple-700 font-medium">🔬 Recherche</p>
                          <p className="text-xs text-purple-600 mt-1">"Rechercher les tendances IA"</p>
                        </div>
                      </div>
                    </div>
                  )}
                </div>
              </div>
            ) : (
            messages.map((message, index) => (
              <div
                key={message.id}
                className={`flex ${message.type === 'user' ? 'justify-end' : 'justify-start'} animate-slideUp`}
                style={{ animationDelay: `${index * 100}ms` }}
              >
                <div className={`${message.type === 'user' ? 'max-w-xs lg:max-w-md' : 'max-w-2xl'} group`}>
                  {/* Avatar for assistant messages */}
                  {message.type === 'assistant' && (
                    <div className="flex items-start space-x-3">
                      <div className="flex-shrink-0">
                        <div className="w-8 h-8 bg-gradient-to-br from-blue-500 to-indigo-600 rounded-full flex items-center justify-center shadow-lg">
                          <svg className="w-4 h-4 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9.663 17h4.673M12 3v1m6.364 1.636l-.707.707M21 12h-1M4 12H3m3.343-5.657l-.707-.707m2.828 9.9a5 5 0 117.072 0l-.548.547A3.374 3.374 0 0014 18.469V19a2 2 0 11-4 0v-.531c0-.895-.356-1.754-.988-2.386l-.548-.547z" />
                          </svg>
                        </div>
                      </div>
                      <div className="flex-1">
                        <div
                          className={`px-4 py-3 rounded-2xl shadow-lg backdrop-blur-sm transition-all duration-300 group-hover:shadow-xl ${
                            message.type === 'user'
                              ? 'bg-gradient-to-r from-blue-500 to-indigo-600 text-white ml-auto'
                              : message.type === 'system'
                              ? 'bg-gradient-to-r from-red-100 to-rose-100 text-red-800 border border-red-200'
                              : 'bg-white/80 text-gray-900 border border-gray-200/50'
                          }`}
                        >
                          <div className="text-sm prose prose-sm max-w-none">
                            <ReactMarkdown>{message.content}</ReactMarkdown>
                          </div>
                          {message.agent_name && (
                            <div className="flex items-center space-x-2 mt-2 pt-2 border-t border-gray-200/50">
                              <div className="w-1.5 h-1.5 bg-blue-500 rounded-full"></div>
                              <p className="text-xs text-gray-600">
                                via <span className="font-medium">{message.agent_name}</span>
                                {message.intent_category && (
                                  <>
                                    <span className="mx-1">•</span>
                                    <span className="text-blue-600">{message.intent_category}</span>
                                  </>
                                )}
                              </p>
                            </div>
                          )}
                          {message.debug_info && (
                            <DebugInfoSection debug_info={message.debug_info} />
                          )}
                        </div>
                      </div>
                    </div>
                  )}

                  {/* User messages */}
                  {message.type === 'user' && (
                    <div
                      className="px-4 py-3 rounded-2xl shadow-lg backdrop-blur-sm transition-all duration-300 group-hover:shadow-xl bg-gradient-to-r from-blue-500 to-indigo-600 text-white ml-auto"
                    >
                      <div className="text-sm prose prose-sm max-w-none prose-invert">
                        <ReactMarkdown>{message.content}</ReactMarkdown>
                      </div>
                    </div>
                  )}

                  {/* System messages */}
                  {message.type === 'system' && (
                    <div
                      className="px-4 py-3 rounded-2xl shadow-lg backdrop-blur-sm transition-all duration-300 group-hover:shadow-xl bg-gradient-to-r from-red-100 to-rose-100 text-red-800 border border-red-200"
                    >
                      <div className="text-sm prose prose-sm max-w-none">
                        <ReactMarkdown>{message.content}</ReactMarkdown>
                      </div>
                    </div>
                  )}

                  {/* Modern Artifact Indicators */}
                  {message.metadata?.artifacts && message.metadata.artifacts.length > 0 && (
                    <div className="mt-3 space-y-2">
                      {message.metadata.artifacts.map((artifact, index) => (
                        <button
                          key={`${message.id}-artifact-${index}`}
                          onClick={() => handleArtifactClick(artifact)}
                          className="group flex items-center space-x-3 px-4 py-3 bg-gradient-to-r from-blue-50 to-indigo-50 hover:from-blue-100 hover:to-indigo-100 border border-blue-200/50 rounded-xl text-sm transition-all duration-300 w-full text-left shadow-sm hover:shadow-md transform hover:scale-[1.02]"
                        >
                          <div className="flex-shrink-0 w-8 h-8 bg-gradient-to-br from-blue-500 to-indigo-600 rounded-lg flex items-center justify-center shadow-sm">
                            <span className="text-white text-sm">
                              {artifact.type === 'database-table' && '📊'}
                              {artifact.type === 'code-snippet' && '💻'}
                              {artifact.type === 'json-data' && '📋'}
                              {artifact.type === 'formatted-text' && '📄'}
                            </span>
                          </div>
                          <div className="flex-1 min-w-0">
                            <p className="font-medium text-gray-900 truncate">{artifact.title}</p>
                            <p className="text-xs text-gray-500 capitalize">{artifact.type.replace('-', ' ')}</p>
                          </div>
                          <div className="flex-shrink-0">
                            <svg className="w-4 h-4 text-blue-500 group-hover:text-blue-600 transition-colors" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
                            </svg>
                          </div>
                        </button>
                      ))}
                    </div>
                  )}
                </div>
              </div>
            ))
          )}

          {/* Modern Loading State */}
          {isLoading && (
            <div className="flex justify-start animate-slideUp">
              <div className="flex items-start space-x-3">
                <div className="flex-shrink-0">
                  <div className="w-8 h-8 bg-gradient-to-br from-gray-400 to-gray-500 rounded-full flex items-center justify-center shadow-lg">
                    <svg className="w-4 h-4 text-white animate-spin" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
                    </svg>
                  </div>
                </div>
                <div className="bg-white/80 backdrop-blur-sm text-gray-900 max-w-xs lg:max-w-md px-4 py-3 rounded-2xl shadow-lg border border-gray-200/50">
                  <div className="flex items-center space-x-3">
                    <div className="flex space-x-1">
                      <div className="w-2 h-2 bg-blue-500 rounded-full animate-bounce"></div>
                      <div className="w-2 h-2 bg-indigo-500 rounded-full animate-bounce" style={{ animationDelay: '0.1s' }}></div>
                      <div className="w-2 h-2 bg-purple-500 rounded-full animate-bounce" style={{ animationDelay: '0.2s' }}></div>
                    </div>
                    <span className="text-sm font-medium">L'IA réfléchit...</span>
                  </div>
                </div>
              </div>
            </div>
          )}
            </div>

            {/* Modern Input Area */}
            <div className="border-t border-gray-200/50 p-4 bg-white/80 backdrop-blur-sm">
              <form onSubmit={handleSendMessage} className="flex space-x-3">
                <div className="flex-1 relative">
                  <input
                    type="text"
                    value={inputMessage}
                    onChange={(e) => setInputMessage(e.target.value)}
                    placeholder="Tapez votre message..."
                    className="w-full px-4 py-3 bg-white/80 backdrop-blur-sm border border-gray-300/50 rounded-xl text-sm focus:ring-2 focus:ring-blue-500 focus:border-blue-500 transition-all duration-300 pr-12"
                    disabled={isLoading}
                  />
                  <div className="absolute right-3 top-1/2 transform -translate-y-1/2">
                    <svg className="w-5 h-5 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 12h.01M12 12h.01M16 12h.01M21 12c0 4.418-4.03 8-9 8a9.863 9.863 0 01-4.255-.949L3 20l1.395-3.72C3.512 15.042 3 13.574 3 12c0-4.418 4.03-8 9-8s9 3.582 9 8z" />
                    </svg>
                  </div>
                </div>
                <button
                  type="submit"
                  disabled={!inputMessage.trim() || isLoading}
                  className="px-6 py-3 bg-gradient-to-r from-blue-500 to-indigo-600 text-white rounded-xl font-medium hover:from-blue-600 hover:to-indigo-700 focus:ring-2 focus:ring-blue-500 focus:ring-offset-2 disabled:opacity-50 disabled:cursor-not-allowed transition-all duration-300 transform hover:scale-105 shadow-lg disabled:transform-none"
                >
                  {isLoading ? (
                    <svg className="w-5 h-5 animate-spin" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
                    </svg>
                  ) : (
                    <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 19l9 2-9-18-9 18 9-2zm0 0v-8" />
                    </svg>
                  )}
                </button>
              </form>
            </div>
          </div>
        </div>

        {/* Modern Artifact Side Panel */}
        {showArtifactPanel && currentArtifact && (
          <div className="w-1/2 relative z-10 animate-slideUp">
            <div className="h-full bg-white/50 backdrop-blur-sm rounded-t-2xl shadow-xl border border-gray-200/50 overflow-hidden mx-4 mb-4 flex flex-col">
              {/* Modern Artifact Panel Header */}
              <div className="relative bg-gradient-to-r from-blue-50 to-indigo-50 border-b border-gray-200/50 p-4">
                <div className="absolute inset-0 bg-gradient-to-r from-blue-600/5 to-indigo-600/5"></div>
                <div className="relative flex items-center justify-between">
                  <div className="flex items-center space-x-3">
                    <div className="w-10 h-10 bg-gradient-to-br from-blue-500 to-indigo-600 rounded-xl flex items-center justify-center shadow-lg">
                      <span className="text-white text-lg">
                        {currentArtifact.type === 'database-table' && '📊'}
                        {currentArtifact.type === 'code-snippet' && '💻'}
                        {currentArtifact.type === 'json-data' && '📋'}
                        {currentArtifact.type === 'formatted-text' && '📄'}
                      </span>
                    </div>
                    <div>
                      <h2 className="text-lg font-bold text-gray-900">
                        {currentArtifact.title}
                      </h2>
                      <p className="text-sm text-gray-600">
                        {currentArtifact.type.replace('-', ' ').replace(/\b\w/g, l => l.toUpperCase())}
                        {currentArtifact.metadata?.tool_used && (
                          <>
                            <span className="mx-2">•</span>
                            <span className="text-blue-600 font-medium">via {currentArtifact.metadata.tool_used}</span>
                          </>
                        )}
                      </p>
                    </div>
                  </div>
                  <button
                    onClick={handleCloseArtifactPanel}
                    className="p-2 text-gray-400 hover:text-gray-600 hover:bg-white/60 rounded-lg transition-all duration-300 transform hover:scale-110"
                  >
                    <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                    </svg>
                  </button>
                </div>
              </div>

              {/* Artifact Content */}
              <div className="flex-1 overflow-auto bg-white/30 backdrop-blur-sm">
                <ChatArtifact
                  artifact={currentArtifact}
                  onRerun={handleRerunQuery}
                  isExpandable={false}
                />
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default ChatPage;
