// API Types for AI Agent Platform

export interface User {
  id: number;
  tenant_id: string;
  email: string;
  username: string;
  full_name?: string;
  bio?: string;
  is_active: boolean;
  is_superuser: boolean;
  is_tenant_admin: boolean;
  created_at: string;
  updated_at?: string;
  last_login?: string;
  avatar_url?: string;
}

export interface Tenant {
  id: string;
  name: string;
  slug: string;
  domain?: string;
  contact_email?: string;
  contact_name?: string;
  status: string;
  plan: string;
  settings: Record<string, any>;
  features: string[];
  tenant_metadata: Record<string, any>;
  max_users: number;
  max_agents: number;
  max_storage_mb: number;
  created_at: string;
  updated_at?: string;
  is_active: boolean;
}

export interface LoginRequest {
  username: string;
  password: string;
}

export interface RegisterRequest {
  email: string;
  username: string;
  password: string;
  full_name?: string;
  bio?: string;
}

export interface AuthResponse {
  access_token: string;
  token_type: string;
  expires_in: number;
}

export type AgentType = 
  | 'customer_service'
  | 'financial_analysis'
  | 'research'
  | 'project_management'
  | 'content_creation'
  | 'data_analysis'
  | 'general';

export type AgentStatus = 'draft' | 'active' | 'inactive' | 'archived';

export interface Agent {
  id: number;
  name: string;
  description?: string;
  agent_type: AgentType;
  status: AgentStatus;
  owner_id: number;
  system_prompt: string;
  personality?: string;
  instructions?: string;
  llm_provider: string;
  llm_model: string;
  temperature: number;
  max_tokens: number;
  tools_config?: Record<string, any>;
  capabilities?: string[];
  is_public: boolean;
  is_template: boolean;
  created_at: string;
  updated_at?: string;
  last_used?: string;
  usage_count: number;
}

export interface AgentCreate {
  name: string;
  description?: string;
  agent_type: AgentType;
  system_prompt: string;
  personality?: string;
  instructions?: string;
  llm_provider?: string;
  llm_model?: string;
  temperature?: number;
  max_tokens?: number;
  tools_config?: Record<string, any>;
  capabilities?: string[];
  is_public?: boolean;
}

export interface AgentTemplate {
  name: string;
  display_name: string;
  description: string;
  agent_type: AgentType;
  default_tools?: string[];
  default_capabilities?: string[];
}

export type IntentCategory = 
  | 'customer_service'
  | 'financial_analysis'
  | 'research'
  | 'project_management'
  | 'content_creation'
  | 'data_analysis'
  | 'technical_support'
  | 'sales'
  | 'general'
  | 'unknown';

export interface IntentAnalysis {
  category: IntentCategory;
  confidence: number;
  keywords: string[];
  reasoning: string;
  suggested_agents: number[];
}

export interface AgentMatch {
  agent_id: number;
  agent_name: string;
  agent_type: string;
  match_score: number;
  match_reasoning: string;
}

export type RoutingDecision = 
  | 'single_agent'
  | 'multi_agent'
  | 'no_suitable_agent'
  | 'escalate_to_human';

export interface RoutingResult {
  decision: RoutingDecision;
  intent_analysis: IntentAnalysis;
  selected_agent?: AgentMatch;
  alternative_agents: AgentMatch[];
  reasoning: string;
  confidence: number;
}

export interface OrchestratorRequest {
  message: string;
  conversation_id?: string;
  context?: Record<string, any>;
  user_preferences?: Record<string, any>;
}

export interface OrchestratorResponse {
  conversation_id: string;
  message_index: number;
  user_message: string;
  agent_response: string;
  routing_result: RoutingResult;
  response_time_ms: number;
  usage?: Record<string, any>;
  debug_info?: string;
}

export interface ConversationSummary {
  id: string;
  title?: string;
  created_at: string;
  last_activity: string;
  total_messages: number;
  primary_intent?: string;
  agents_used: number[];
}

export interface MessageHistory {
  message_index: number;
  user_message: string;
  agent_response?: string;
  intent_category?: string;
  confidence_score?: number;
  selected_agent_id?: number;
  created_at: string;
}

export interface ConversationDetail {
  conversation: ConversationSummary;
  messages: MessageHistory[];
}

export interface ChatMessage {
  id: string;
  type: 'user' | 'assistant' | 'system';
  content: string;
  timestamp: string;
  agent_name?: string;
  intent_category?: string;
  confidence?: number;
  debug_info?: string;
  metadata?: {
    database_result?: any;
    artifacts?: any[];
    tool_used?: string;
    execution_time?: number;
    [key: string]: any;
  };
}

export interface ApiError {
  detail: string;
  status_code?: number;
}

// Explicit exports to ensure module resolution
export type {
  User,
  LoginRequest,
  RegisterRequest,
  AuthResponse,
  Agent,
  AgentCreate,
  AgentTemplate,
  AgentType,
  AgentStatus,
  IntentCategory,
  IntentAnalysis,
  AgentMatch,
  RoutingDecision,
  RoutingResult,
  OrchestratorRequest,
  OrchestratorResponse,
  ConversationSummary,
  MessageHistory,
  ConversationDetail,
  ChatMessage
};
