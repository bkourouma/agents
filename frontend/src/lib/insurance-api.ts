/**
 * API client pour le système d'assurance
 * Toutes les fonctions communiquent avec le backend en français
 */

const API_BASE_URL = 'http://localhost:3006';

export interface Customer {
  id: string;
  customer_number: string;
  first_name: string;
  last_name: string;
  email: string;
  phone: string;
  date_of_birth: string;
  risk_profile: 'low' | 'medium' | 'high';
  customer_type: 'individual' | 'business';
  kyc_status: 'pending' | 'verified' | 'rejected';
  is_active: boolean;
  city: string;
  created_at: string;
  updated_at: string;
  // Optional fields from backend
  gender?: string;
  occupation?: string;
  annual_income?: number;
  marital_status?: string;
  address_line1?: string;
  address_line2?: string;
  state?: string;
  postal_code?: string;
  country?: string;
  preferred_language?: string;
  customer_notes?: string;
  // Computed fields
  totalCoverage?: number;
  activeContracts?: number;
}

export interface CustomerSummary {
  customer: Customer;
  totalCoverageAmount: number;
  totalPremiumAmount: number;
  activeContracts: number;
  pendingOrders: number;
  openClaims: number;
  recentInteractions: number;
  paymentStatus: string;
}

export interface InsuranceProduct {
  id: string;
  product_code: string;
  name: string;
  category_id: string;
  description: string;
  product_type: 'life' | 'health' | 'auto' | 'home' | 'business';
  coverage_type: string;
  min_coverage_amount: number;
  max_coverage_amount: number;
  min_age: number;
  max_age: number;
  waiting_period_days: number;
  policy_term_years: number;
  renewable: boolean;
  requires_medical_exam: boolean;
  is_active: boolean;
  created_at: string;
  updated_at: string;
}

// Interface pour les devis d'assurance
export interface InsuranceQuote {
  id: string;
  quote_number: string;
  customer_id: string;
  product_id: string;
  quote_status: 'active' | 'expired' | 'converted' | 'cancelled';
  coverage_amount: number;
  premium_frequency: 'monthly' | 'quarterly' | 'semi-annual' | 'annual';
  base_premium: number;
  adjusted_premium: number;
  additional_premium: number;
  final_premium: number;
  annual_premium: number;
  pricing_factors: any[];
  selected_features: any[];
  quote_date: string;
  expiry_date: string;
  eligible: boolean;
  conditions: string[];
  medical_exam_required: boolean;
  is_active: boolean;
  created_at: string;
  updated_at: string;
}

export interface ApiResponse<T> {
  success: boolean;
  data?: T;
  error?: string;
  message?: string;
}

class InsuranceApiService {
  private async request<T>(endpoint: string, options: RequestInit = {}): Promise<ApiResponse<T>> {
    const url = `${API_BASE_URL}${endpoint}`;
    const config = {
      headers: {
        'Content-Type': 'application/json',
        ...options.headers,
      },
      ...options,
    };

    console.log('Making API request:', { url, config });

    try {
      const response = await fetch(url, config);
      console.log('API response status:', response.status);

      if (!response.ok) {
        const errorText = await response.text();
        console.error('API error response:', errorText);
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const data = await response.json();
      console.log('API response data:', data);
      return data;
    } catch (error) {
      console.error('API request failed:', error);
      return {
        success: false,
        error: error instanceof Error ? error.message : 'Une erreur est survenue'
      };
    }
  }

  // =============================================
  // CLIENTS
  // =============================================

  async searchCustomers(query: string, limit: number = 10): Promise<ApiResponse<Customer[]>> {
    const params = new URLSearchParams({
      q: query,
      limite: limit.toString()
    });
    
    return this.request<Customer[]>(`/api/insurance/clients/recherche?${params}`);
  }

  async getCustomer(customerId: string): Promise<ApiResponse<Customer>> {
    return this.request<Customer>(`/api/insurance/clients/${customerId}`);
  }

  async getCustomerDetails(customerId: string): Promise<ApiResponse<any>> {
    return this.request<any>(`/api/insurance/clients/${customerId}/details`);
  }

  async getCustomerSummary(customerId: string): Promise<ApiResponse<CustomerSummary>> {
    return this.request<CustomerSummary>(`/api/insurance/clients/${customerId}/resume`);
  }

  async createCustomer(customerData: Partial<Customer>): Promise<ApiResponse<Customer>> {
    console.log('API createCustomer called with:', customerData);
    return this.request<Customer>('/api/insurance/clients', {
      method: 'POST',
      body: JSON.stringify(customerData)
    });
  }

  async updateCustomer(customerId: string, customerData: Partial<Customer>): Promise<ApiResponse<Customer>> {
    return this.request<Customer>(`/api/insurance/clients/${customerId}`, {
      method: 'PUT',
      body: JSON.stringify(customerData)
    });
  }

  async deleteCustomer(customerId: string): Promise<ApiResponse<null>> {
    return this.request<null>(`/api/insurance/clients/${customerId}`, {
      method: 'DELETE'
    });
  }

  // =============================================
  // PRODUITS
  // =============================================

  async getProducts(filters?: {
    type_produit?: string;
    categorie_id?: string;
    actif?: boolean;
  }): Promise<ApiResponse<InsuranceProduct[]>> {
    const params = new URLSearchParams();
    
    if (filters?.type_produit) params.append('type_produit', filters.type_produit);
    if (filters?.categorie_id) params.append('categorie_id', filters.categorie_id);
    if (filters?.actif !== undefined) params.append('actif', filters.actif.toString());
    
    return this.request<InsuranceProduct[]>(`/api/insurance/produits?${params}`);
  }

  async getProductDetails(productId: string): Promise<ApiResponse<any>> {
    return this.request<any>(`/api/insurance/produits/${productId}/details`);
  }

  async createProduct(productData: Partial<InsuranceProduct>): Promise<ApiResponse<InsuranceProduct>> {
    return this.request<InsuranceProduct>('/api/insurance/produits', {
      method: 'POST',
      body: JSON.stringify(productData)
    });
  }

  async updateProduct(productId: string, productData: Partial<InsuranceProduct>): Promise<ApiResponse<InsuranceProduct>> {
    return this.request<InsuranceProduct>(`/api/insurance/produits/${productId}`, {
      method: 'PUT',
      body: JSON.stringify(productData)
    });
  }

  async deleteProduct(productId: string): Promise<ApiResponse<null>> {
    return this.request<null>(`/api/insurance/produits/${productId}`, {
      method: 'DELETE'
    });
  }

  // =============================================
  // QUOTES API METHODS
  // =============================================

  async getQuotes(skip: number = 0, limit: number = 50, status?: string): Promise<ApiResponse<InsuranceQuote[]>> {
    const params = new URLSearchParams({
      skip: skip.toString(),
      limit: limit.toString()
    });

    if (status) {
      params.append('statut', status);
    }

    return this.request<InsuranceQuote[]>(`/api/insurance/devis?${params}`);
  }

  async getQuoteById(quoteId: string): Promise<ApiResponse<InsuranceQuote>> {
    return this.request<InsuranceQuote>(`/api/insurance/devis/${quoteId}`);
  }

  async createQuote(quoteData: Partial<InsuranceQuote>): Promise<ApiResponse<any>> {
    return this.request<any>('/api/insurance/devis', {
      method: 'POST',
      body: JSON.stringify(quoteData)
    });
  }



  async updateQuote(quoteId: string, quoteData: Partial<InsuranceQuote>): Promise<ApiResponse<InsuranceQuote>> {
    return this.request<InsuranceQuote>(`/api/insurance/devis/${quoteId}`, {
      method: 'PUT',
      body: JSON.stringify(quoteData)
    });
  }

  async deleteQuote(quoteId: string): Promise<ApiResponse<null>> {
    return this.request<null>(`/api/insurance/devis/${quoteId}`, {
      method: 'DELETE'
    });
  }

  async getCustomerQuotes(customerId: string, skip: number = 0, limit: number = 20): Promise<ApiResponse<InsuranceQuote[]>> {
    const params = new URLSearchParams({
      skip: skip.toString(),
      limit: limit.toString()
    });

    return this.request<InsuranceQuote[]>(`/api/insurance/clients/${customerId}/devis?${params}`);
  }

  // =============================================
  // ORDER CREATION FROM QUOTES
  // =============================================

  async createOrderFromQuote(quoteId: string, paymentMethod: string = 'bank_transfer', sendEmail: boolean = true): Promise<ApiResponse<any>> {
    const params = new URLSearchParams({
      payment_method: paymentMethod,
      send_email: sendEmail.toString()
    });

    return this.request<any>(`/api/insurance/devis/${quoteId}/commander?${params}`, {
      method: 'POST'
    });
  }

  async sendQuoteByEmail(quoteId: string): Promise<ApiResponse<any>> {
    return this.request<any>(`/api/insurance/devis/${quoteId}/envoyer-email`, {
      method: 'POST'
    });
  }

  async calculatePricing(request: {
    product_id: string;
    coverage_amount: number;
    customer_id: string;
    premium_frequency: string;
  }): Promise<ApiResponse<any>> {
    return this.request<any>('/api/insurance/produits/tarification', {
      method: 'POST',
      body: JSON.stringify(request)
    });
  }

  async checkEligibility(productId: string, customerId: string): Promise<ApiResponse<any>> {
    return this.request<any>(`/api/insurance/produits/${productId}/eligibilite/${customerId}`);
  }

  // =============================================
  // COMMANDES
  // =============================================

  async createOrder(orderData: {
    customer_id: string;
    product_id: string;
    coverage_amount: number;
    premium_frequency: string;
    effective_date: string;
    notes?: string;
  }): Promise<ApiResponse<any>> {
    return this.request<any>('/api/insurance/commandes', {
      method: 'POST',
      body: JSON.stringify(orderData)
    });
  }

  async getOrderStatus(orderNumber: string): Promise<ApiResponse<any>> {
    return this.request<any>(`/api/insurance/commandes/${orderNumber}/statut`);
  }

  async updateOrder(orderId: string, updates: any): Promise<ApiResponse<any>> {
    return this.request<any>(`/api/insurance/commandes/${orderId}`, {
      method: 'PUT',
      body: JSON.stringify(updates)
    });
  }

  async getCustomerOrders(customerId: string, status?: string): Promise<ApiResponse<any[]>> {
    const params = status ? `?statut=${status}` : '';
    return this.request<any[]>(`/api/insurance/clients/${customerId}/commandes${params}`);
  }

  async getAllOrders(status?: string, skip: number = 0, limit: number = 50): Promise<ApiResponse<any[]>> {
    const params = new URLSearchParams();
    if (status) params.append('statut', status);
    params.append('skip', skip.toString());
    params.append('limit', limit.toString());

    return this.request<any[]>(`/api/insurance/commandes?${params}`);
  }

  // =============================================
  // CONTRATS
  // =============================================

  async getAllContracts(status?: string): Promise<ApiResponse<any[]>> {
    const params = status && status !== 'all' ? `?status=${status}` : '';
    return this.request<any[]>(`/api/insurance/contrats${params}`);
  }

  async getContractDetails(policyNumber: string): Promise<ApiResponse<any>> {
    return this.request<any>(`/api/insurance/contrats/${policyNumber}/details`);
  }

  async createContractFromOrder(orderId: string): Promise<ApiResponse<any>> {
    return this.request<any>('/api/insurance/contrats/from-order', {
      method: 'POST',
      body: JSON.stringify({ order_id: orderId })
    });
  }

  async updateContractStatus(policyNumber: string, status: string, reason?: string): Promise<ApiResponse<any>> {
    return this.request<any>(`/api/insurance/contrats/${policyNumber}/status`, {
      method: 'PUT',
      body: JSON.stringify({ status, reason })
    });
  }

  async renewContract(policyNumber: string, renewalData: any): Promise<ApiResponse<any>> {
    return this.request<any>(`/api/insurance/contrats/${policyNumber}/renew`, {
      method: 'POST',
      body: JSON.stringify(renewalData)
    });
  }

  async getContractPaymentHistory(policyNumber: string): Promise<ApiResponse<any[]>> {
    return this.request<any[]>(`/api/insurance/contrats/${policyNumber}/payments`);
  }

  async addContractBeneficiary(policyNumber: string, beneficiaryData: any): Promise<ApiResponse<any>> {
    return this.request<any>(`/api/insurance/contrats/${policyNumber}/beneficiaries`, {
      method: 'POST',
      body: JSON.stringify(beneficiaryData)
    });
  }

  // =============================================
  // DEVIS
  // =============================================

  async generateQuote(quoteRequest: {
    customer_id: string;
    product_id: string;
    coverage_amount: number;
    premium_frequency: string;
    additional_features?: string[];
  }): Promise<ApiResponse<any>> {
    return this.request<any>('/api/insurance/devis/generer', {
      method: 'POST',
      body: JSON.stringify(quoteRequest)
    });
  }

  // =============================================
  // RÉCLAMATIONS
  // =============================================

  async getClaims(filters?: {
    client_id?: string;
    statut?: string;
  }): Promise<ApiResponse<any[]>> {
    const params = new URLSearchParams();

    if (filters?.client_id) params.append('client_id', filters.client_id);
    if (filters?.statut) params.append('statut', filters.statut);

    return this.request<any[]>(`/api/insurance/reclamations?${params}`);
  }

  async createClaim(claimData: {
    contract_id: string;
    customer_id: string;
    claim_type: string;
    claim_amount: number;
    incident_date: string;
    description: string;
  }): Promise<ApiResponse<any>> {
    return this.request<any>('/api/insurance/reclamations', {
      method: 'POST',
      body: JSON.stringify(claimData)
    });
  }

  async getClaimByNumber(claimNumber: string): Promise<ApiResponse<any>> {
    return this.request<any>(`/api/insurance/reclamations/${claimNumber}`);
  }

  async updateClaimStatus(claimId: string, statusData: {
    new_status: string;
    notes?: string;
    approval_amount?: number;
    rejection_reason?: string;
  }): Promise<ApiResponse<any>> {
    return this.request<any>(`/api/insurance/reclamations/${claimId}/statut`, {
      method: 'PUT',
      body: JSON.stringify(statusData)
    });
  }

  async getClaimsStatistics(): Promise<ApiResponse<any>> {
    return this.request<any>('/api/insurance/reclamations/statistiques');
  }

  // =============================================
  // PAIEMENTS
  // =============================================

  async getPayments(filters?: {
    statut?: string;
    contrat_id?: string;
  }): Promise<ApiResponse<any[]>> {
    const params = new URLSearchParams();

    if (filters?.statut) params.append('statut', filters.statut);
    if (filters?.contrat_id) params.append('contrat_id', filters.contrat_id);

    return this.request<any[]>(`/api/insurance/paiements?${params}`);
  }

  async createPayment(paymentData: {
    contract_id: string;
    due_date: string;
    amount: number;
    payment_method?: string;
  }): Promise<ApiResponse<any>> {
    return this.request<any>('/api/insurance/paiements', {
      method: 'POST',
      body: JSON.stringify(paymentData)
    });
  }

  async processPayment(paymentId: string, paymentData: {
    payment_date: string;
    payment_method: string;
    transaction_id?: string;
    processed_by?: string;
  }): Promise<ApiResponse<any>> {
    return this.request<any>(`/api/insurance/paiements/${paymentId}/traiter`, {
      method: 'PUT',
      body: JSON.stringify(paymentData)
    });
  }

  async generateUpcomingPayments(contractId: string, monthsAhead: number = 12): Promise<ApiResponse<any[]>> {
    return this.request<any[]>(`/api/insurance/contrats/${contractId}/generer-paiements?mois_avance=${monthsAhead}`, {
      method: 'POST'
    });
  }

  async getPaymentStatistics(): Promise<ApiResponse<any>> {
    return this.request<any>('/api/insurance/paiements/statistiques');
  }

  // =============================================
  // UTILITAIRES
  // =============================================

  async testConnection(): Promise<boolean> {
    try {
      const response = await fetch(`${API_BASE_URL}/health`);
      return response.ok;
    } catch {
      return false;
    }
  }
}

// Export singleton instance
export const insuranceApi = new InsuranceApiService();

// Export types and service class
export default InsuranceApiService;
