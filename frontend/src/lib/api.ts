import axios from 'axios';
import type * as Types from '../types/index';

const API_BASE_URL = import.meta.env.VITE_API_URL || '';

class ApiClient {
  private client: typeof axios;

  constructor() {
    this.client = axios.create({
      baseURL: `${API_BASE_URL}/api/v1`,
      headers: {
        'Content-Type': 'application/json',
      },
    });

    // Add auth token to requests
    this.client.interceptors.request.use((config) => {
      const token = localStorage.getItem('auth_token');
      if (token) {
        config.headers.Authorization = `Bearer ${token}`;
      }
      return config;
    });

    // Handle auth errors
    this.client.interceptors.response.use(
      (response) => response,
      (error) => {
        if (error.response?.status === 401) {
          localStorage.removeItem('auth_token');
          localStorage.removeItem('user');
          window.location.href = '/login';
        }
        return Promise.reject(error);
      }
    );
  }

  // Auth endpoints
  async login(credentials: Types.LoginRequest): Promise<Types.AuthResponse> {
    const response = await this.client.post<Types.AuthResponse>('/auth/login', credentials);
    return response.data;
  }

  async register(userData: Types.RegisterRequest): Promise<Types.User> {
    const response = await this.client.post<Types.User>('/auth/register', userData);
    return response.data;
  }

  async getCurrentUser(): Promise<Types.User> {
    const response = await this.client.get<Types.User>('/auth/me');
    return response.data;
  }

  // Agent endpoints
  async getAgents(params?: {
    skip?: number;
    limit?: number;
    agent_type?: string;
    status?: string;
  }): Promise<Types.Agent[]> {
    const response = await this.client.get<Types.Agent[]>('/agents/', { params });
    return response.data;
  }

  async getPublicAgents(params?: {
    skip?: number;
    limit?: number;
    agent_type?: string;
  }): Promise<Types.Agent[]> {
    const response = await this.client.get<Types.Agent[]>('/agents/public', { params });
    return response.data;
  }

  async getAgent(id: number): Promise<Types.Agent> {
    const response = await this.client.get<Types.Agent>(`/agents/${id}`);
    return response.data;
  }

  async createAgent(agentData: Types.AgentCreate): Promise<Types.Agent> {
    const response = await this.client.post<Types.Agent>('/agents/', agentData);
    return response.data;
  }

  async createAgentFromTemplate(
    templateName: string,
    agentName: string,
    customizations?: Record<string, any>
  ): Promise<Types.Agent> {
    const response = await this.client.post<Types.Agent>(
      `/agents/from-template/${templateName}`,
      customizations,
      { params: { agent_name: agentName } }
    );
    return response.data;
  }

  async updateAgent(id: number, updates: Partial<Types.AgentCreate>): Promise<Types.Agent> {
    const response = await this.client.put<Types.Agent>(`/agents/${id}`, updates);
    return response.data;
  }

  async deleteAgent(id: number): Promise<void> {
    await this.client.delete(`/agents/${id}`);
  }

  async activateAgent(id: number): Promise<Types.Agent> {
    const response = await this.client.post<Types.Agent>(`/agents/${id}/activate`);
    return response.data;
  }

  async deactivateAgent(id: number): Promise<Types.Agent> {
    const response = await this.client.post<Types.Agent>(`/agents/${id}/deactivate`);
    return response.data;
  }

  async chatWithAgent(
    id: number,
    message: string,
    conversationId?: string
  ): Promise<any> {
    const response = await this.client.post(`/agents/${id}/chat`, {
      message,
      conversation_id: conversationId,
    });
    return response.data;
  }

  async getAgentTemplates(): Promise<{ templates: Types.AgentTemplate[] }> {
    const response = await this.client.get('/agents/templates/list');
    return response.data;
  }

  async getAgentTemplate(name: string): Promise<{ name: string; template: any }> {
    const response = await this.client.get(`/agents/templates/${name}`);
    return response.data;
  }

  // Orchestrator endpoints
  async orchestratedChat(request: OrchestratorRequest): Promise<OrchestratorResponse> {
    const response = await this.client.post<OrchestratorResponse>('/orchestrator/chat', request);
    return response.data;
  }

  async analyzeIntent(message: string, context?: Record<string, any>): Promise<IntentAnalysis> {
    const response = await this.client.post<IntentAnalysis>('/orchestrator/analyze-intent', null, {
      params: { message, context: context ? JSON.stringify(context) : undefined },
    });
    return response.data;
  }

  async findMatchingAgents(
    message: string,
    context?: Record<string, any>,
    limit?: number
  ): Promise<{
    intent_analysis: IntentAnalysis;
    matching_agents: AgentMatch[];
    total_matches: number;
  }> {
    const response = await this.client.post('/orchestrator/find-agents', null, {
      params: { 
        message, 
        context: context ? JSON.stringify(context) : undefined,
        limit 
      },
    });
    return response.data;
  }

  async getConversations(params?: {
    skip?: number;
    limit?: number;
  }): Promise<ConversationSummary[]> {
    const response = await this.client.get<ConversationSummary[]>('/orchestrator/conversations', { params });
    return response.data;
  }

  async getConversation(id: string): Promise<ConversationDetail> {
    const response = await this.client.get<ConversationDetail>(`/orchestrator/conversations/${id}`);
    return response.data;
  }

  async deleteConversation(id: string): Promise<void> {
    await this.client.delete(`/orchestrator/conversations/${id}`);
  }

  async getOrchestratorStats(): Promise<{
    total_conversations: number;
    total_messages: number;
    intent_distribution: Record<string, number>;
    average_messages_per_conversation: number;
  }> {
    const response = await this.client.get('/orchestrator/stats');
    return response.data;
  }

  // LLM endpoints
  async getLLMProviders(): Promise<{
    providers: string[];
    default_provider: string;
    total_providers: number;
  }> {
    const response = await this.client.get('/llm/providers');
    return response.data;
  }

  async testLLM(provider?: string): Promise<{
    status: string;
    provider: string;
    model: string;
    response: string;
    usage?: Record<string, any>;
  }> {
    const response = await this.client.post('/llm/test', null, {
      params: { provider },
    });
    return response.data;
  }

  // Database endpoints
  async getDatabaseTables(): Promise<any[]> {
    const response = await this.client.get('/database/tables');
    return response.data;
  }

  async createDatabaseTable(tableData: any): Promise<any> {
    const response = await this.client.post('/database/tables', tableData);
    return response.data;
  }

  async updateDatabaseTable(id: number, tableData: any): Promise<any> {
    const response = await this.client.put(`/database/tables/${id}`, tableData);
    return response.data;
  }

  async deleteDatabaseTable(id: number): Promise<void> {
    await this.client.delete(`/database/tables/${id}`);
  }

  async getDatabaseSchema(): Promise<any> {
    const response = await this.client.get('/database/schema');
    return response.data;
  }

  async processNaturalLanguageQuery(queryData: any): Promise<any> {
    const response = await this.client.post('/database/query/natural', queryData);
    return response.data;
  }

  // Vanna AI endpoints
  async startVannaTraining(data: { table_ids: number[]; model_name: string }): Promise<any> {
    console.log('📡 API Client: Starting Vanna training with data:', data);
    console.log('📡 API Client: Making request to /database/vanna/train');
    try {
      const response = await this.client.post('/database/vanna/train', data);
      console.log('📡 API Client: Training response:', response.data);
      return response.data;
    } catch (error) {
      console.error('📡 API Client: Training request failed:', error);
      throw error;
    }
  }

  async getVannaTrainingStatus(trainingId: number): Promise<any> {
    const response = await this.client.get(`/database/vanna/status/${trainingId}`);
    return response.data;
  }

  async getVannaTrainingSessions(): Promise<any[]> {
    console.log('📡 API Client: Fetching training sessions');
    try {
      const response = await this.client.get('/database/vanna/sessions');
      console.log('📡 API Client: Training sessions response:', response.data);
      return response.data;
    } catch (error) {
      console.error('📡 API Client: Failed to fetch training sessions:', error);
      throw error;
    }
  }

  // Training Data endpoints
  async getTrainingData(params?: {
    table_id?: number;
    model_name?: string;
    is_active?: boolean;
    page?: number;
    page_size?: number;
  }): Promise<any[]> {
    const response = await this.client.get('/database/training-data', { params });
    return response.data;
  }

  async createTrainingData(data: {
    table_id: number;
    model_name: string;
    question: string;
    sql: string;
    is_generated?: boolean;
    confidence_score?: number;
    generation_model?: string;
  }): Promise<any> {
    const response = await this.client.post('/database/training-data', data);
    return response.data;
  }

  async updateTrainingData(id: number, data: {
    question?: string;
    sql?: string;
    is_active?: boolean;
    confidence_score?: number;
    validation_status?: string;
  }): Promise<any> {
    const response = await this.client.put(`/database/training-data/${id}`, data);
    return response.data;
  }

  async deleteTrainingData(id: number): Promise<any> {
    const response = await this.client.delete(`/database/training-data/${id}`);
    return response.data;
  }

  async generateTrainingData(data: {
    table_ids: number[];
    model_name: string;
    llm_model?: string;
    num_questions?: number;
    avoid_duplicates?: boolean;
    prompt?: string;
  }): Promise<any> {
    const response = await this.client.post('/database/training-data/generate', data);
    return response.data;
  }

  async batchTrainQuestions(questions: Array<{
    table_id: number;
    model_name: string;
    question: string;
    sql: string;
    is_generated?: boolean;
    confidence_score?: number;
    generation_model?: string;
  }>): Promise<any> {
    const response = await this.client.post('/database/training-data/batch-train', questions);
    return response.data;
  }

  // Query history endpoints
  async getQueryHistory(page: number = 1, pageSize: number = 10): Promise<any> {
    const response = await this.client.get(`/database/query/history?page=${page}&page_size=${pageSize}`);
    return response.data;
  }

  async toggleQueryFavorite(queryId: number): Promise<any> {
    const response = await this.client.put(`/database/query/history/${queryId}/favorite`);
    return response.data;
  }

  // Table data management endpoints
  async getTableData(tableId: number, page: number = 1, pageSize: number = 50): Promise<any> {
    const response = await this.client.get(`/database/tables/${tableId}/data?page=${page}&page_size=${pageSize}`);
    return response.data;
  }

  async importTableData(tableId: number, file: File, importConfig: any = {}): Promise<any> {
    const formData = new FormData();
    formData.append('file', file);
    formData.append('import_config', JSON.stringify(importConfig));

    const response = await this.client.post(`/database/tables/${tableId}/import`, formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    });
    return response.data;
  }

  async getTableTemplate(tableId: number): Promise<void> {
    const response = await this.client.get(`/database/tables/${tableId}/template`, {
      responseType: 'blob'
    });

    // Create blob and download link
    const blob = new Blob([response.data], {
      type: 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    });

    // Create download link
    const url = window.URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;

    // Extract filename from response headers or use default
    const contentDisposition = response.headers['content-disposition'];
    let filename = 'template.xlsx';
    if (contentDisposition) {
      const filenameMatch = contentDisposition.match(/filename=(.+)/);
      if (filenameMatch) {
        filename = filenameMatch[1].replace(/"/g, '');
      }
    }

    link.download = filename;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    window.URL.revokeObjectURL(url);
  }

  // Column management endpoints
  async createTableColumn(tableId: number, columnData: any): Promise<any> {
    const response = await this.client.post(`/database/tables/${tableId}/columns`, columnData);
    return response.data;
  }

  // Database Connection endpoints
  async getDatabaseConnections(): Promise<any[]> {
    const response = await this.client.get('/database/connections');
    return response.data;
  }

  async createDatabaseConnection(connectionData: any): Promise<any> {
    const response = await this.client.post('/database/connections', connectionData);
    return response.data;
  }

  async getDatabaseConnection(connectionId: number): Promise<any> {
    const response = await this.client.get(`/database/connections/${connectionId}`);
    return response.data;
  }

  async updateDatabaseConnection(connectionId: number, updateData: any): Promise<any> {
    const response = await this.client.put(`/database/connections/${connectionId}`, updateData);
    return response.data;
  }

  async deleteDatabaseConnection(connectionId: number): Promise<void> {
    await this.client.delete(`/database/connections/${connectionId}`);
  }

  async testDatabaseConnection(connectionId: number): Promise<any> {
    const response = await this.client.post(`/database/connections/${connectionId}/test`);
    return response.data;
  }

  async getExternalDatabaseSchema(connectionId: number): Promise<any> {
    const response = await this.client.get(`/database/connections/${connectionId}/schema`);
    return response.data;
  }

  async importTablesFromExternalDatabase(connectionId: number, importData: any): Promise<any> {
    const response = await this.client.post(`/database/connections/${connectionId}/import-tables`, importData);
    return response.data;
  }

  // Enhanced Database Connection endpoints
  async getDatabaseProviders(): Promise<any[]> {
    const response = await this.client.get('/database/providers');
    return response.data;
  }

  async getConnectionStringTemplate(provider: string): Promise<any> {
    const response = await this.client.get(`/database/providers/${provider}/template`);
    return response.data;
  }

  async testConnectionString(provider: string, connectionString: string): Promise<any> {
    const formData = new FormData();
    formData.append('connection_string', connectionString);

    const response = await this.client.post(`/database/connections/test-string?provider=${provider}`, formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    });
    return response.data;
  }
}

export const apiClient = new ApiClient();
export default apiClient;
