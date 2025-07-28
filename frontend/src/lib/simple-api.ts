import axios from 'axios';

const API_BASE_URL = import.meta.env.VITE_API_URL || '';

// Create axios instance
const client = axios.create({
  baseURL: `${API_BASE_URL}/api/v1`,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Add auth token to requests
client.interceptors.request.use((config) => {
  const token = localStorage.getItem('auth_token');
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

// Handle auth errors
client.interceptors.response.use(
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

// Simple API functions
export const api = {
  // Auth
  async login(credentials: { username: string; password: string }) {
    const response = await client.post('/auth/login', credentials);
    return response.data;
  },

  async register(userData: { email: string; username: string; password: string; full_name?: string }) {
    const response = await client.post('/auth/register', userData);
    return response.data;
  },

  async getCurrentUser() {
    const response = await client.get('/auth/me');
    return response.data;
  },

  // Tenants
  async getTenant(tenantId: string) {
    const response = await client.get(`/tenants/${tenantId}`);
    return response.data;
  },

  async updateTenant(tenantId: string, data: any) {
    const response = await client.put(`/tenants/${tenantId}`, data);
    return response.data;
  },

  async getTenantStats(tenantId: string) {
    const response = await client.get(`/tenants/${tenantId}/stats`);
    return response.data;
  },

  async getTenantUsage(tenantId: string) {
    const response = await client.get(`/tenants/${tenantId}/usage`);
    return response.data;
  },

  // Orchestrator
  async orchestratedChat(request: { message: string; conversation_id?: string; context?: any }) {
    const response = await client.post('/orchestrator/chat', request);
    return response.data;
  },

  async analyzeIntent(message: string, context?: any) {
    const response = await client.post('/orchestrator/analyze-intent', null, {
      params: { message, context: context ? JSON.stringify(context) : undefined },
    });
    return response.data;
  },

  async findMatchingAgents(message: string, context?: any, limit?: number) {
    const response = await client.post('/orchestrator/find-agents', null, {
      params: { 
        message, 
        context: context ? JSON.stringify(context) : undefined,
        limit 
      },
    });
    return response.data;
  },

  async getConversations(params?: { skip?: number; limit?: number }) {
    const response = await client.get('/orchestrator/conversations', { params });
    return response.data;
  },

  async getConversation(id: string) {
    const response = await client.get(`/orchestrator/conversations/${id}`);
    return response.data;
  },

  async deleteConversation(id: string) {
    await client.delete(`/orchestrator/conversations/${id}`);
  },

  async getOrchestratorStats() {
    const response = await client.get('/orchestrator/stats');
    return response.data;
  },

  // Agents
  async getAgents(params?: { skip?: number; limit?: number; agent_type?: string; status?: string }) {
    const response = await client.get('/agents/', { params });
    return response.data;
  },

  async getPublicAgents(params?: { skip?: number; limit?: number; agent_type?: string }) {
    const response = await client.get('/agents/public', { params });
    return response.data;
  },

  async getAgent(id: number) {
    const response = await client.get(`/agents/${id}`);
    return response.data;
  },

  async createAgent(agentData: any) {
    const response = await client.post('/agents/', agentData);
    return response.data;
  },

  async updateAgent(id: number, updates: any) {
    const response = await client.put(`/agents/${id}`, updates);
    return response.data;
  },

  async deleteAgent(id: number) {
    await client.delete(`/agents/${id}`);
  },

  async activateAgent(id: number) {
    const response = await client.post(`/agents/${id}/activate`);
    return response.data;
  },

  async deactivateAgent(id: number) {
    const response = await client.post(`/agents/${id}/deactivate`);
    return response.data;
  },

  async chatWithAgent(id: number, message: string, conversationId?: string) {
    const response = await client.post(`/agents/${id}/chat`, {
      message,
      conversation_id: conversationId,
    });
    return response.data;
  },

  async getAgentTemplates() {
    const response = await client.get('/agents/templates/list');
    return response.data;
  },

  async getAgentTemplate(name: string) {
    const response = await client.get(`/agents/templates/${name}`);
    return response.data;
  },

  async createAgentFromTemplate(templateName: string, agentName: string, customizations?: any) {
    const response = await client.post(
      `/agents/from-template/${templateName}`,
      customizations,
      { params: { agent_name: agentName } }
    );
    return response.data;
  },

  // LLM
  async getLLMProviders() {
    const response = await client.get('/llm/providers');
    return response.data;
  },

  async testLLM(provider?: string) {
    const response = await client.post('/llm/test', null, {
      params: { provider },
    });
    return response.data;
  }
};

export default api;
