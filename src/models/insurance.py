"""
Pydantic models for the insurance system.
All user-visible text fields are in French.
"""

from pydantic import BaseModel, Field, EmailStr
from typing import Optional, List, Dict, Any
from datetime import datetime, date
from enum import Enum


# Enums for better type safety
class CustomerType(str, Enum):
    INDIVIDUAL = "individual"
    BUSINESS = "business"


class RiskProfile(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


class KYCStatus(str, Enum):
    PENDING = "pending"
    VERIFIED = "verified"
    REJECTED = "rejected"


class ProductType(str, Enum):
    LIFE = "life"
    HEALTH = "health"
    AUTO = "auto"
    HOME = "home"
    BUSINESS = "business"


class OrderStatus(str, Enum):
    DRAFT = "draft"
    SUBMITTED = "submitted"
    UNDER_REVIEW = "under_review"
    APPROVED = "approved"
    REJECTED = "rejected"
    CANCELLED = "cancelled"


class ContractStatus(str, Enum):
    ACTIVE = "active"
    SUSPENDED = "suspended"
    LAPSED = "lapsed"
    CANCELLED = "cancelled"
    EXPIRED = "expired"
    CLAIMED = "claimed"


class ClaimStatus(str, Enum):
    SUBMITTED = "submitted"
    INVESTIGATING = "investigating"
    APPROVED = "approved"
    REJECTED = "rejected"
    PAID = "paid"
    CLOSED = "closed"


class InteractionType(str, Enum):
    CALL = "call"
    EMAIL = "email"
    CHAT = "chat"
    VISIT = "visit"


class InteractionStatus(str, Enum):
    OPEN = "open"
    RESOLVED = "resolved"
    ESCALATED = "escalated"


class Priority(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    URGENT = "urgent"


class PremiumFrequency(str, Enum):
    MONTHLY = "monthly"
    QUARTERLY = "quarterly"
    SEMI_ANNUAL = "semi-annual"
    ANNUAL = "annual"


# Base models
class CustomerBase(BaseModel):
    customer_number: str = Field(..., description="Numéro client")
    first_name: str = Field(..., description="Prénom")
    last_name: str = Field(..., description="Nom de famille")
    email: EmailStr = Field(..., description="Adresse e-mail")
    phone: Optional[str] = Field(None, description="Téléphone")
    date_of_birth: Optional[date] = Field(None, description="Date de naissance")
    gender: Optional[str] = Field(None, description="Genre")
    occupation: Optional[str] = Field(None, description="Profession")
    annual_income: Optional[float] = Field(None, description="Revenu annuel")
    marital_status: Optional[str] = Field(None, description="État civil")
    address_line1: Optional[str] = Field(None, description="Adresse ligne 1")
    address_line2: Optional[str] = Field(None, description="Adresse ligne 2")
    city: Optional[str] = Field(None, description="Ville")
    state: Optional[str] = Field(None, description="État/Province")
    postal_code: Optional[str] = Field(None, description="Code postal")
    country: Optional[str] = Field(None, description="Pays")
    customer_type: CustomerType = Field(CustomerType.INDIVIDUAL, description="Type de client")
    risk_profile: RiskProfile = Field(RiskProfile.MEDIUM, description="Profil de risque")
    preferred_language: str = Field("fr", description="Langue préférée")
    kyc_status: KYCStatus = Field(KYCStatus.PENDING, description="Statut KYC")
    customer_notes: Optional[str] = Field(None, description="Notes client")


class CustomerCreate(BaseModel):
    first_name: str = Field(..., description="Prénom")
    last_name: str = Field(..., description="Nom de famille")
    email: EmailStr = Field(..., description="Adresse e-mail")
    phone: Optional[str] = Field(None, description="Téléphone")
    date_of_birth: Optional[date] = Field(None, description="Date de naissance")
    gender: Optional[str] = Field(None, description="Genre")
    occupation: Optional[str] = Field(None, description="Profession")
    annual_income: Optional[float] = Field(None, description="Revenu annuel")
    marital_status: Optional[str] = Field(None, description="État civil")
    address_line1: Optional[str] = Field(None, description="Adresse ligne 1")
    address_line2: Optional[str] = Field(None, description="Adresse ligne 2")
    city: Optional[str] = Field(None, description="Ville")
    state: Optional[str] = Field(None, description="État/Province")
    postal_code: Optional[str] = Field(None, description="Code postal")
    country: Optional[str] = Field(None, description="Pays")
    customer_type: CustomerType = Field(CustomerType.INDIVIDUAL, description="Type de client")
    risk_profile: RiskProfile = Field(RiskProfile.MEDIUM, description="Profil de risque")
    preferred_language: str = Field("fr", description="Langue préférée")
    kyc_status: KYCStatus = Field(KYCStatus.PENDING, description="Statut KYC")
    customer_notes: Optional[str] = Field(None, description="Notes client")


class CustomerUpdate(BaseModel):
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    email: Optional[EmailStr] = None
    phone: Optional[str] = None
    date_of_birth: Optional[date] = None
    gender: Optional[str] = None
    occupation: Optional[str] = None
    annual_income: Optional[float] = None
    marital_status: Optional[str] = None
    address_line1: Optional[str] = None
    address_line2: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    postal_code: Optional[str] = None
    country: Optional[str] = None
    customer_type: Optional[CustomerType] = None
    risk_profile: Optional[RiskProfile] = None
    preferred_language: Optional[str] = None
    kyc_status: Optional[KYCStatus] = None
    customer_notes: Optional[str] = None


class Customer(CustomerBase):
    id: str
    is_active: bool = True
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class ProductCategoryBase(BaseModel):
    name: str = Field(..., description="Nom de la catégorie")
    description: Optional[str] = Field(None, description="Description")


class ProductCategoryCreate(ProductCategoryBase):
    pass


class ProductCategory(ProductCategoryBase):
    id: str
    is_active: bool = True
    created_at: datetime

    class Config:
        from_attributes = True


class InsuranceProductBase(BaseModel):
    product_code: str = Field(..., description="Code produit")
    name: str = Field(..., description="Nom du produit")
    category_id: Optional[str] = Field(None, description="ID catégorie")
    description: Optional[str] = Field(None, description="Description")
    product_type: ProductType = Field(..., description="Type de produit")
    coverage_type: Optional[str] = Field(None, description="Type de couverture")
    min_coverage_amount: Optional[float] = Field(None, description="Montant minimum de couverture")
    max_coverage_amount: Optional[float] = Field(None, description="Montant maximum de couverture")
    min_age: Optional[int] = Field(None, description="Âge minimum")
    max_age: Optional[int] = Field(None, description="Âge maximum")
    waiting_period_days: int = Field(0, description="Période d'attente (jours)")
    policy_term_years: Optional[int] = Field(None, description="Durée de la police (années)")
    renewable: bool = Field(True, description="Renouvelable")
    requires_medical_exam: bool = Field(False, description="Examen médical requis")


class InsuranceProductCreate(InsuranceProductBase):
    pass


class InsuranceProductUpdate(BaseModel):
    product_code: Optional[str] = None
    name: Optional[str] = None
    category_id: Optional[str] = None
    description: Optional[str] = None
    product_type: Optional[ProductType] = None
    coverage_type: Optional[str] = None
    min_coverage_amount: Optional[float] = None
    max_coverage_amount: Optional[float] = None
    min_age: Optional[int] = None
    max_age: Optional[int] = None
    waiting_period_days: Optional[int] = None
    policy_term_years: Optional[int] = None
    renewable: Optional[bool] = None
    requires_medical_exam: Optional[bool] = None


class InsuranceProduct(InsuranceProductBase):
    id: str
    is_active: bool = True
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class ProductFeatureBase(BaseModel):
    product_id: str = Field(..., description="ID produit")
    feature_name: str = Field(..., description="Nom de la fonctionnalité")
    description: Optional[str] = Field(None, description="Description")
    feature_type: str = Field(..., description="Type de fonctionnalité")
    is_standard: bool = Field(True, description="Standard")
    additional_premium_percentage: float = Field(0, description="Pourcentage de prime supplémentaire")


class ProductFeatureCreate(ProductFeatureBase):
    pass


class ProductFeature(ProductFeatureBase):
    id: str
    created_at: datetime

    class Config:
        from_attributes = True


class PricingTierBase(BaseModel):
    product_id: str = Field(..., description="ID produit")
    tier_name: str = Field(..., description="Nom du niveau")
    coverage_amount: float = Field(..., description="Montant de couverture")
    base_premium: float = Field(..., description="Prime de base")
    premium_frequency: PremiumFrequency = Field(PremiumFrequency.MONTHLY, description="Fréquence de prime")
    currency: str = Field("EUR", description="Devise")
    effective_date: date = Field(..., description="Date d'entrée en vigueur")
    expiry_date: Optional[date] = Field(None, description="Date d'expiration")


class PricingTierCreate(PricingTierBase):
    pass


class PricingTier(PricingTierBase):
    id: str
    is_active: bool = True
    created_at: datetime

    class Config:
        from_attributes = True


class InsuranceOrderBase(BaseModel):
    order_number: str = Field(..., description="Numéro de commande")
    customer_id: str = Field(..., description="ID client")
    product_id: str = Field(..., description="ID produit")
    coverage_amount: float = Field(..., description="Montant de couverture")
    premium_amount: float = Field(..., description="Montant de la prime")
    premium_frequency: PremiumFrequency = Field(PremiumFrequency.MONTHLY, description="Fréquence de prime")
    payment_method: Optional[str] = Field(None, description="Méthode de paiement")
    effective_date: Optional[date] = Field(None, description="Date d'entrée en vigueur")
    expiry_date: Optional[date] = Field(None, description="Date d'expiration")
    assigned_agent_id: Optional[str] = Field(None, description="ID agent assigné")
    underwriter_id: Optional[str] = Field(None, description="ID souscripteur")
    medical_exam_required: bool = Field(False, description="Examen médical requis")
    medical_exam_completed: bool = Field(False, description="Examen médical terminé")
    medical_exam_date: Optional[date] = Field(None, description="Date examen médical")
    documents_received: bool = Field(False, description="Documents reçus")
    approval_date: Optional[date] = Field(None, description="Date d'approbation")
    rejection_reason: Optional[str] = Field(None, description="Raison du rejet")
    notes: Optional[str] = Field(None, description="Notes")


class InsuranceOrderCreate(InsuranceOrderBase):
    order_status: OrderStatus = Field(OrderStatus.DRAFT, description="Statut de la commande")


class InsuranceOrderUpdate(BaseModel):
    order_status: Optional[OrderStatus] = None
    coverage_amount: Optional[float] = None
    premium_amount: Optional[float] = None
    effective_date: Optional[date] = None
    medical_exam_completed: Optional[bool] = None
    documents_received: Optional[bool] = None
    notes: Optional[str] = None


class InsuranceOrder(InsuranceOrderBase):
    id: str
    order_status: OrderStatus
    application_date: date
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class InsuranceContractBase(BaseModel):
    policy_number: str = Field(..., description="Numéro de police")
    order_id: str = Field(..., description="ID commande")
    customer_id: str = Field(..., description="ID client")
    product_id: str = Field(..., description="ID produit")
    coverage_amount: float = Field(..., description="Montant de couverture")
    premium_amount: float = Field(..., description="Montant de la prime")
    premium_frequency: PremiumFrequency = Field(..., description="Fréquence de prime")
    issue_date: date = Field(..., description="Date d'émission")
    effective_date: date = Field(..., description="Date d'entrée en vigueur")
    expiry_date: Optional[date] = Field(None, description="Date d'expiration")
    next_renewal_date: Optional[date] = Field(None, description="Date de renouvellement")
    cash_value: float = Field(0, description="Valeur de rachat")
    surrender_value: float = Field(0, description="Valeur de rachat")
    loan_value: float = Field(0, description="Valeur de prêt")
    auto_renewal: bool = Field(True, description="Renouvellement automatique")
    grace_period_days: int = Field(30, description="Période de grâce (jours)")
    last_premium_paid_date: Optional[date] = Field(None, description="Date dernier paiement")
    next_premium_due_date: Optional[date] = Field(None, description="Date prochaine échéance")


class InsuranceContractCreate(InsuranceContractBase):
    contract_status: ContractStatus = Field(ContractStatus.ACTIVE, description="Statut du contrat")


class InsuranceContract(InsuranceContractBase):
    id: str
    contract_status: ContractStatus
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class InsuranceClaimBase(BaseModel):
    claim_number: str = Field(..., description="Numéro de réclamation")
    contract_id: str = Field(..., description="ID contrat")
    customer_id: str = Field(..., description="ID client")
    claim_type: str = Field(..., description="Type de réclamation")
    claim_amount: float = Field(..., description="Montant réclamé")
    incident_date: date = Field(..., description="Date de l'incident")
    description: str = Field(..., description="Description")
    assigned_adjuster_id: Optional[str] = Field(None, description="ID expert assigné")
    investigation_notes: Optional[str] = Field(None, description="Notes d'enquête")
    approval_amount: Optional[float] = Field(None, description="Montant approuvé")
    rejection_reason: Optional[str] = Field(None, description="Raison du rejet")
    payment_date: Optional[date] = Field(None, description="Date de paiement")


class InsuranceClaimCreate(InsuranceClaimBase):
    claim_status: ClaimStatus = Field(ClaimStatus.SUBMITTED, description="Statut de la réclamation")


class InsuranceClaim(InsuranceClaimBase):
    id: str
    claim_status: ClaimStatus
    report_date: date
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# =============================================
# PAYMENT MODELS
# =============================================

class PaymentStatus(str, Enum):
    PENDING = "pending"
    COMPLETED = "completed"
    FAILED = "failed"
    REFUNDED = "refunded"


class PremiumPaymentBase(BaseModel):
    contract_id: str = Field(..., description="ID contrat")
    due_date: date = Field(..., description="Date d'échéance")
    amount: float = Field(..., description="Montant")
    payment_method: Optional[str] = Field(None, description="Méthode de paiement")


class PremiumPaymentCreate(PremiumPaymentBase):
    pass


class PremiumPayment(PremiumPaymentBase):
    id: str
    payment_date: Optional[date] = Field(None, description="Date de paiement")
    payment_status: PaymentStatus = Field(PaymentStatus.PENDING, description="Statut du paiement")
    transaction_id: Optional[str] = Field(None, description="ID de transaction")
    late_fee: float = Field(0, description="Frais de retard")
    grace_period_used: bool = Field(False, description="Période de grâce utilisée")
    processed_by: Optional[str] = Field(None, description="Traité par")
    created_at: datetime

    class Config:
        from_attributes = True


class ProcessPaymentRequest(BaseModel):
    payment_date: date = Field(..., description="Date de paiement")
    payment_method: str = Field(..., description="Méthode de paiement")
    transaction_id: Optional[str] = Field(None, description="ID de transaction")
    processed_by: Optional[str] = Field(None, description="Traité par")


class CustomerInteractionBase(BaseModel):
    customer_id: str = Field(..., description="ID client")
    agent_id: Optional[str] = Field(None, description="ID agent")
    interaction_type: InteractionType = Field(..., description="Type d'interaction")
    subject: str = Field(..., description="Sujet")
    description: str = Field(..., description="Description")
    resolution: Optional[str] = Field(None, description="Résolution")
    status: InteractionStatus = Field(InteractionStatus.OPEN, description="Statut")
    priority: Priority = Field(Priority.MEDIUM, description="Priorité")
    related_contract_id: Optional[str] = Field(None, description="ID contrat lié")
    related_order_id: Optional[str] = Field(None, description="ID commande liée")
    related_claim_id: Optional[str] = Field(None, description="ID réclamation liée")
    follow_up_required: bool = Field(False, description="Suivi requis")
    follow_up_date: Optional[date] = Field(None, description="Date de suivi")
    satisfaction_rating: Optional[int] = Field(None, description="Note de satisfaction")


class CustomerInteractionCreate(CustomerInteractionBase):
    pass


class CustomerInteraction(CustomerInteractionBase):
    id: str
    interaction_date: datetime
    created_at: datetime

    class Config:
        from_attributes = True


# Response models for API
class ApiResponse(BaseModel):
    success: bool = Field(..., description="Succès")
    data: Optional[Any] = Field(None, description="Données")
    error: Optional[str] = Field(None, description="Erreur")
    message: Optional[str] = Field(None, description="Message")


class PaginatedResponse(BaseModel):
    data: List[Any] = Field(..., description="Données")
    total_count: int = Field(..., description="Nombre total")
    page: int = Field(..., description="Page")
    page_size: int = Field(..., description="Taille de page")
    total_pages: int = Field(..., description="Nombre total de pages")


# Request models
class CreateOrderRequest(BaseModel):
    customer_id: str = Field(..., description="ID client")
    product_id: str = Field(..., description="ID produit")
    coverage_amount: float = Field(..., description="Montant de couverture")
    premium_frequency: PremiumFrequency = Field(..., description="Fréquence de prime")
    effective_date: date = Field(..., description="Date d'entrée en vigueur")
    riders: Optional[List[Dict[str, Any]]] = Field(None, description="Avenants")
    notes: Optional[str] = Field(None, description="Notes")


class UpdateOrderRequest(BaseModel):
    order_status: Optional[OrderStatus] = Field(None, description="Statut de la commande")
    coverage_amount: Optional[float] = Field(None, description="Montant de couverture")
    premium_amount: Optional[float] = Field(None, description="Montant de la prime")
    effective_date: Optional[date] = Field(None, description="Date d'entrée en vigueur")
    medical_exam_completed: Optional[bool] = Field(None, description="Examen médical terminé")
    documents_received: Optional[bool] = Field(None, description="Documents reçus")
    notes: Optional[str] = Field(None, description="Notes")


class PricingRequest(BaseModel):
    product_id: str = Field(..., description="ID produit")
    coverage_amount: float = Field(..., description="Montant de couverture")
    customer_id: str = Field(..., description="ID client")
    premium_frequency: PremiumFrequency = Field(..., description="Fréquence de prime")
    additional_riders: Optional[List[str]] = Field(None, description="Avenants supplémentaires")


class ContractSearchParams(BaseModel):
    customer_id: Optional[str] = Field(None, description="ID client")
    policy_number: Optional[str] = Field(None, description="Numéro de police")
    product_type: Optional[ProductType] = Field(None, description="Type de produit")
    contract_status: Optional[ContractStatus] = Field(None, description="Statut du contrat")
    expiry_date_from: Optional[date] = Field(None, description="Date d'expiration de")
    expiry_date_to: Optional[date] = Field(None, description="Date d'expiration à")
    next_renewal_date_from: Optional[date] = Field(None, description="Date de renouvellement de")
    next_renewal_date_to: Optional[date] = Field(None, description="Date de renouvellement à")
    page: int = Field(1, description="Page")
    page_size: int = Field(20, description="Taille de page")


# Complex response models
class CustomerDetailsResponse(BaseModel):
    customer: Customer
    active_contracts: List[InsuranceContract]
    recent_orders: List[InsuranceOrder]
    recent_interactions: List[CustomerInteraction]


class ProductDetailsResponse(BaseModel):
    product: InsuranceProduct
    features: List[ProductFeature]
    pricing_tiers: List[PricingTier]


class PricingResponse(BaseModel):
    base_premium: float = Field(..., description="Prime de base")
    final_premium: float = Field(..., description="Prime finale")
    pricing_factors: List[Dict[str, Any]] = Field(..., description="Facteurs de tarification")
    rider_premiums: List[Dict[str, Any]] = Field(..., description="Primes des avenants")


# =============================================
# QUOTE MODELS
# =============================================

class QuoteStatus(str, Enum):
    ACTIVE = "active"
    EXPIRED = "expired"
    CONVERTED = "converted"
    CANCELLED = "cancelled"


class InsuranceQuoteBase(BaseModel):
    customer_id: str = Field(..., description="ID du client")
    product_id: str = Field(..., description="ID du produit")
    coverage_amount: float = Field(..., description="Montant de couverture")
    premium_frequency: PremiumFrequency = Field(PremiumFrequency.MONTHLY, description="Fréquence de prime")
    base_premium: float = Field(..., description="Prime de base")
    adjusted_premium: float = Field(..., description="Prime ajustée")
    additional_premium: float = Field(0, description="Prime additionnelle")
    final_premium: float = Field(..., description="Prime finale")
    annual_premium: float = Field(..., description="Prime annuelle")
    pricing_factors: Optional[List[Dict[str, Any]]] = Field(None, description="Facteurs de tarification")
    selected_features: Optional[List[Dict[str, Any]]] = Field(None, description="Fonctionnalités sélectionnées")
    quote_date: date = Field(..., description="Date du devis")
    expiry_date: date = Field(..., description="Date d'expiration")
    eligible: bool = Field(True, description="Éligible")
    conditions: Optional[List[str]] = Field(None, description="Conditions")
    medical_exam_required: bool = Field(False, description="Examen médical requis")


class InsuranceQuoteCreate(BaseModel):
    customer_id: str = Field(..., description="ID du client")
    product_id: str = Field(..., description="ID du produit")
    coverage_amount: float = Field(..., description="Montant de couverture")
    premium_frequency: PremiumFrequency = Field(PremiumFrequency.MONTHLY, description="Fréquence de prime")
    additional_features: Optional[List[str]] = Field(None, description="Fonctionnalités additionnelles")


class InsuranceQuoteUpdate(BaseModel):
    coverage_amount: Optional[float] = None
    premium_frequency: Optional[PremiumFrequency] = None
    additional_features: Optional[List[str]] = None
    quote_status: Optional[QuoteStatus] = None


class InsuranceQuote(InsuranceQuoteBase):
    id: str
    quote_number: str = Field(..., description="Numéro de devis")
    quote_status: QuoteStatus = Field(QuoteStatus.ACTIVE, description="Statut du devis")
    is_active: bool = True
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class OrderStatusResponse(BaseModel):
    order: InsuranceOrder
    status_history: List[Dict[str, Any]]


class ContractDetailsResponse(BaseModel):
    contract: InsuranceContract
    customer: Customer
    product: InsuranceProduct
    beneficiaries: List[Dict[str, Any]]
    payment_history: List[Dict[str, Any]]


class ClaimDetailsResponse(BaseModel):
    claim: InsuranceClaim
    contract: InsuranceContract
    customer: Customer
    documents: List[Dict[str, Any]]


class CustomerSummaryResponse(BaseModel):
    customer: Customer
    total_coverage_amount: float = Field(..., description="Montant total de couverture")
    total_premium_amount: float = Field(..., description="Montant total des primes")
    active_contracts: int = Field(..., description="Contrats actifs")
    pending_orders: int = Field(..., description="Commandes en attente")
    open_claims: int = Field(..., description="Réclamations ouvertes")
    recent_interactions: int = Field(..., description="Interactions récentes")
    payment_status: str = Field(..., description="Statut de paiement")


# Search and filter models
class CustomerSearchParams(BaseModel):
    query: str = Field(..., description="Requête de recherche")
    customer_type: Optional[CustomerType] = Field(None, description="Type de client")
    risk_profile: Optional[RiskProfile] = Field(None, description="Profil de risque")
    kyc_status: Optional[KYCStatus] = Field(None, description="Statut KYC")
    limit: int = Field(10, description="Limite")


class ProductSearchParams(BaseModel):
    product_type: Optional[ProductType] = Field(None, description="Type de produit")
    category_id: Optional[str] = Field(None, description="ID catégorie")
    is_active: bool = Field(True, description="Actif")
    min_coverage: Optional[float] = Field(None, description="Couverture minimum")
    max_coverage: Optional[float] = Field(None, description="Couverture maximum")
