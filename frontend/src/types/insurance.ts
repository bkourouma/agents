// Types pour le système d'assurance
export interface Customer {
  id: string;
  customer_number: string;
  first_name: string;
  last_name: string;
  email: string;
  phone: string;
  date_of_birth: string;
  gender?: string;
  occupation?: string;
  annual_income?: number;
  marital_status?: string;
  address_line1?: string;
  address_line2?: string;
  city?: string;
  state?: string;
  postal_code?: string;
  country?: string;
  customer_type: 'individual' | 'business';
  risk_profile: 'low' | 'medium' | 'high';
  preferred_language: string;
  kyc_status: 'pending' | 'verified' | 'rejected';
  customer_notes?: string;
  is_active: boolean;
  created_at: string;
  updated_at: string;
}

export interface InsuranceProduct {
  id: string;
  product_code: string;
  name: string;
  category_id?: string;
  description?: string;
  product_type: 'life' | 'health' | 'auto' | 'home' | 'business';
  coverage_type?: string;
  min_coverage_amount?: number;
  max_coverage_amount?: number;
  min_age?: number;
  max_age?: number;
  waiting_period_days?: number;
  policy_term_years?: number;
  renewable: boolean;
  requires_medical_exam: boolean;
  is_active: boolean;
  created_at: string;
  updated_at: string;
}

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
  customer?: Customer;
  product?: InsuranceProduct;
}

export interface ApiResponse<T = any> {
  success: boolean;
  data?: T;
  error?: string;
  message?: string;
}
