"""
Migration to create insurance system tables adapted for SQLite.
Adapted from PostgreSQL schema to SQLite with UUID replaced by TEXT.
"""

from sqlalchemy import Column, String, Text, Integer, Float, Boolean, DateTime, Date, ForeignKey, Index, JSON
from sqlalchemy.sql import func
from src.core.database import Base
import uuid


class Customer(Base):
    __tablename__ = "customers"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    customer_number = Column(String(20), unique=True, nullable=False)
    first_name = Column(String(100), nullable=False)
    last_name = Column(String(100), nullable=False)
    email = Column(String(255), unique=True, nullable=False)
    phone = Column(String(20))
    date_of_birth = Column(Date)
    gender = Column(String(10))
    occupation = Column(String(100))
    annual_income = Column(Float)
    marital_status = Column(String(20))
    address_line1 = Column(String(255))
    address_line2 = Column(String(255))
    city = Column(String(100))
    state = Column(String(100))
    postal_code = Column(String(20))
    country = Column(String(100))
    customer_type = Column(String(20), default='individual')  # individual, business
    risk_profile = Column(String(20), default='medium')  # low, medium, high
    preferred_language = Column(String(10), default='fr')
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    is_active = Column(Boolean, default=True)
    kyc_status = Column(String(20), default='pending')  # pending, verified, rejected
    customer_notes = Column(Text)


class ProductCategory(Base):
    __tablename__ = "product_categories"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String(100), nullable=False)
    description = Column(Text)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=func.now())


class InsuranceProduct(Base):
    __tablename__ = "insurance_products"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    product_code = Column(String(50), unique=True, nullable=False)
    name = Column(String(200), nullable=False)
    category_id = Column(String(36), ForeignKey('product_categories.id'))
    description = Column(Text)
    product_type = Column(String(50), nullable=False)  # life, health, auto, home, business
    coverage_type = Column(String(50))  # term, whole, universal, liability, comprehensive
    min_coverage_amount = Column(Float)
    max_coverage_amount = Column(Float)
    min_age = Column(Integer)
    max_age = Column(Integer)
    waiting_period_days = Column(Integer, default=0)
    policy_term_years = Column(Integer)
    renewable = Column(Boolean, default=True)
    is_active = Column(Boolean, default=True)
    requires_medical_exam = Column(Boolean, default=False)
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())


class ProductFeature(Base):
    __tablename__ = "product_features"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    product_id = Column(String(36), ForeignKey('insurance_products.id'))
    feature_name = Column(String(200), nullable=False)
    description = Column(Text)
    feature_type = Column(String(50))  # coverage, benefit, exclusion, condition
    is_standard = Column(Boolean, default=True)  # true for standard, false for optional
    additional_premium_percentage = Column(Float, default=0)
    created_at = Column(DateTime, default=func.now())


class PricingFactor(Base):
    __tablename__ = "pricing_factors"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    product_id = Column(String(36), ForeignKey('insurance_products.id'))
    factor_name = Column(String(100), nullable=False)  # age, gender, health, location, etc.
    factor_type = Column(String(50))  # age_group, gender, health_condition, location
    factor_value = Column(String(100))  # 25-35, male, smoker, urban, etc.
    multiplier = Column(Float, default=1.0)  # pricing multiplier
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=func.now())


class PricingTier(Base):
    __tablename__ = "pricing_tiers"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    product_id = Column(String(36), ForeignKey('insurance_products.id'))
    tier_name = Column(String(100), nullable=False)
    coverage_amount = Column(Float, nullable=False)
    base_premium = Column(Float, nullable=False)
    premium_frequency = Column(String(20), default='monthly')  # monthly, quarterly, semi-annual, annual
    currency = Column(String(10), default='XOF')
    effective_date = Column(Date, default=func.current_date())
    expiry_date = Column(Date)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=func.now())


class InsuranceQuote(Base):
    """Modèle pour les devis d'assurance."""
    __tablename__ = "insurance_quotes"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    quote_number = Column(String(50), unique=True, nullable=False)
    customer_id = Column(String(36), ForeignKey('customers.id'), nullable=False)
    product_id = Column(String(36), ForeignKey('insurance_products.id'), nullable=False)
    quote_status = Column(String(30), default='active')  # active, expired, converted, cancelled
    coverage_amount = Column(Float, nullable=False)
    premium_frequency = Column(String(20), default='monthly')
    base_premium = Column(Float, nullable=False)
    adjusted_premium = Column(Float, nullable=False)
    additional_premium = Column(Float, default=0)
    final_premium = Column(Float, nullable=False)
    annual_premium = Column(Float, nullable=False)
    pricing_factors = Column(JSON)  # Store pricing factors as JSON
    selected_features = Column(JSON)  # Store selected features as JSON
    quote_date = Column(Date, default=func.current_date())
    expiry_date = Column(Date, nullable=False)
    eligible = Column(Boolean, default=True)
    conditions = Column(JSON)  # Store conditions as JSON array
    medical_exam_required = Column(Boolean, default=False)
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    is_active = Column(Boolean, default=True)


class InsuranceOrder(Base):
    __tablename__ = "insurance_orders"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    order_number = Column(String(50), unique=True, nullable=False)
    quote_id = Column(String(36), ForeignKey('insurance_quotes.id'))  # Link to quote
    customer_id = Column(String(36), ForeignKey('customers.id'))
    product_id = Column(String(36), ForeignKey('insurance_products.id'))
    order_status = Column(String(30), default='draft')  # draft, submitted, under_review, approved, rejected, cancelled
    coverage_amount = Column(Float, nullable=False)
    premium_amount = Column(Float, nullable=False)
    premium_frequency = Column(String(20), default='monthly')
    payment_method = Column(String(50))
    application_date = Column(Date, default=func.current_date())
    effective_date = Column(Date)
    expiry_date = Column(Date)
    assigned_agent_id = Column(String(36))  # customer service agent handling the order
    underwriter_id = Column(String(36))  # underwriter assigned
    medical_exam_required = Column(Boolean, default=False)
    medical_exam_completed = Column(Boolean, default=False)
    medical_exam_date = Column(Date)
    documents_received = Column(Boolean, default=False)
    approval_date = Column(Date)
    rejection_reason = Column(Text)
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    notes = Column(Text)  # internal notes for customer service


class OrderStatusHistory(Base):
    __tablename__ = "order_status_history"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    order_id = Column(String(36), ForeignKey('insurance_orders.id'))
    previous_status = Column(String(30))
    new_status = Column(String(30))
    changed_by = Column(String(36))  # user who made the change
    changed_at = Column(DateTime, default=func.now())
    reason = Column(Text)
    notes = Column(Text)


class OrderRider(Base):
    __tablename__ = "order_riders"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    order_id = Column(String(36), ForeignKey('insurance_orders.id'))
    rider_name = Column(String(200), nullable=False)
    rider_type = Column(String(50))  # accidental_death, disability, critical_illness
    coverage_amount = Column(Float)
    additional_premium = Column(Float)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=func.now())


class InsuranceContract(Base):
    __tablename__ = "insurance_contracts"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    policy_number = Column(String(50), unique=True, nullable=False)
    order_id = Column(String(36), ForeignKey('insurance_orders.id'))
    customer_id = Column(String(36), ForeignKey('customers.id'))
    product_id = Column(String(36), ForeignKey('insurance_products.id'))
    contract_status = Column(String(30), default='active')  # active, suspended, lapsed, cancelled, expired, claimed
    coverage_amount = Column(Float, nullable=False)
    premium_amount = Column(Float, nullable=False)
    premium_frequency = Column(String(20))
    issue_date = Column(Date, nullable=False)
    effective_date = Column(Date, nullable=False)
    expiry_date = Column(Date)
    next_renewal_date = Column(Date)
    cash_value = Column(Float, default=0)  # for whole life policies
    surrender_value = Column(Float, default=0)
    loan_value = Column(Float, default=0)
    auto_renewal = Column(Boolean, default=True)
    grace_period_days = Column(Integer, default=30)
    last_premium_paid_date = Column(Date)
    next_premium_due_date = Column(Date)
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())


class ContractBeneficiary(Base):
    __tablename__ = "contract_beneficiaries"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    contract_id = Column(String(36), ForeignKey('insurance_contracts.id'))
    beneficiary_type = Column(String(20), default='primary')  # primary, contingent
    first_name = Column(String(100), nullable=False)
    last_name = Column(String(100), nullable=False)
    relationship = Column(String(50))
    percentage = Column(Float, default=100.00)
    date_of_birth = Column(Date)
    address = Column(Text)
    phone = Column(String(20))
    email = Column(String(255))
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=func.now())


class PremiumPayment(Base):
    __tablename__ = "premium_payments"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    contract_id = Column(String(36), ForeignKey('insurance_contracts.id'))
    payment_date = Column(Date, nullable=True)
    due_date = Column(Date, nullable=False)
    amount = Column(Float, nullable=False)
    payment_method = Column(String(50))
    payment_status = Column(String(20), default='pending')  # pending, completed, failed, refunded
    transaction_id = Column(String(100))
    late_fee = Column(Float, default=0)
    grace_period_used = Column(Boolean, default=False)
    processed_by = Column(String(36))  # staff member who processed
    created_at = Column(DateTime, default=func.now())


class InsuranceClaim(Base):
    __tablename__ = "insurance_claims"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    claim_number = Column(String(50), unique=True, nullable=False)
    contract_id = Column(String(36), ForeignKey('insurance_contracts.id'))
    customer_id = Column(String(36), ForeignKey('customers.id'))
    claim_type = Column(String(50))  # death, disability, health, accident, etc.
    claim_amount = Column(Float, nullable=False)
    claim_status = Column(String(30), default='submitted')  # submitted, investigating, approved, rejected, paid, closed
    incident_date = Column(Date, nullable=False)
    report_date = Column(Date, default=func.current_date())
    description = Column(Text)
    assigned_adjuster_id = Column(String(36))
    investigation_notes = Column(Text)
    approval_amount = Column(Float)
    rejection_reason = Column(Text)
    payment_date = Column(Date)
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())


class CustomerInteraction(Base):
    __tablename__ = "customer_interactions"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    customer_id = Column(String(36), ForeignKey('customers.id'))
    agent_id = Column(String(36))  # customer service agent
    interaction_type = Column(String(50))  # call, email, chat, visit
    interaction_date = Column(DateTime, default=func.now())
    subject = Column(String(200))
    description = Column(Text)
    resolution = Column(Text)
    status = Column(String(20), default='open')  # open, resolved, escalated
    priority = Column(String(20), default='medium')  # low, medium, high, urgent
    related_contract_id = Column(String(36), ForeignKey('insurance_contracts.id'))
    related_order_id = Column(String(36), ForeignKey('insurance_orders.id'))
    related_claim_id = Column(String(36), ForeignKey('insurance_claims.id'))
    follow_up_required = Column(Boolean, default=False)
    follow_up_date = Column(Date)
    satisfaction_rating = Column(Integer)  # 1-5 rating
    created_at = Column(DateTime, default=func.now())


class CustomerDocument(Base):
    __tablename__ = "customer_documents"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    customer_id = Column(String(36), ForeignKey('customers.id'))
    contract_id = Column(String(36), ForeignKey('insurance_contracts.id'))
    order_id = Column(String(36), ForeignKey('insurance_orders.id'))
    document_type = Column(String(50))  # application, medical_report, id_proof, income_proof, claim_form
    document_name = Column(String(200))
    file_path = Column(String(500))
    file_size = Column(Integer)
    mime_type = Column(String(100))
    uploaded_by = Column(String(36))
    upload_date = Column(DateTime, default=func.now())
    is_verified = Column(Boolean, default=False)
    verified_by = Column(String(36))
    verification_date = Column(DateTime)
    expiry_date = Column(Date)  # for documents that expire
    notes = Column(Text)


class RenewalNotification(Base):
    __tablename__ = "renewal_notifications"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    contract_id = Column(String(36), ForeignKey('insurance_contracts.id'))
    customer_id = Column(String(36), ForeignKey('customers.id'))
    notification_type = Column(String(50))  # renewal_reminder, payment_due, policy_expiry
    notification_method = Column(String(20))  # email, sms, mail, call
    scheduled_date = Column(Date, nullable=False)
    sent_date = Column(DateTime)
    status = Column(String(20), default='pending')  # pending, sent, failed, cancelled
    message_content = Column(Text)
    created_at = Column(DateTime, default=func.now())


class ProductComparison(Base):
    __tablename__ = "product_comparisons"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    customer_id = Column(String(36), ForeignKey('customers.id'))
    agent_id = Column(String(36))
    comparison_date = Column(DateTime, default=func.now())
    products_compared = Column(Text)  # JSON array of product IDs
    notes = Column(Text)
    recommendation = Column(Text)
    result = Column(String(50))  # quote_provided, order_created, no_action, follow_up


class SystemUser(Base):
    __tablename__ = "system_users"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    username = Column(String(50), unique=True, nullable=False)
    email = Column(String(255), unique=True, nullable=False)
    first_name = Column(String(100))
    last_name = Column(String(100))
    role = Column(String(50), nullable=False)  # agent, underwriter, manager, admin
    department = Column(String(100))
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=func.now())
    last_login = Column(DateTime)


# Create indexes for performance
def create_indexes():
    """Create indexes for better query performance."""
    indexes = [
        # Customer indexes
        Index('idx_customers_email', Customer.email),
        Index('idx_customers_phone', Customer.phone),
        Index('idx_customers_customer_number', Customer.customer_number),

        # Product indexes
        Index('idx_insurance_products_product_code', InsuranceProduct.product_code),
        Index('idx_insurance_products_category', InsuranceProduct.category_id),
        Index('idx_insurance_products_type', InsuranceProduct.product_type),

        # Order indexes
        Index('idx_insurance_orders_customer', InsuranceOrder.customer_id),
        Index('idx_insurance_orders_status', InsuranceOrder.order_status),
        Index('idx_insurance_orders_number', InsuranceOrder.order_number),
        Index('idx_insurance_orders_date', InsuranceOrder.application_date),

        # Contract indexes
        Index('idx_insurance_contracts_policy_number', InsuranceContract.policy_number),
        Index('idx_insurance_contracts_customer', InsuranceContract.customer_id),
        Index('idx_insurance_contracts_status', InsuranceContract.contract_status),
        Index('idx_insurance_contracts_expiry', InsuranceContract.expiry_date),
        Index('idx_insurance_contracts_renewal', InsuranceContract.next_renewal_date),

        # Payment indexes
        Index('idx_premium_payments_contract', PremiumPayment.contract_id),
        Index('idx_premium_payments_due_date', PremiumPayment.due_date),
        Index('idx_premium_payments_status', PremiumPayment.payment_status),

        # Claims indexes
        Index('idx_insurance_claims_contract', InsuranceClaim.contract_id),
        Index('idx_insurance_claims_customer', InsuranceClaim.customer_id),
        Index('idx_insurance_claims_status', InsuranceClaim.claim_status),
        Index('idx_insurance_claims_number', InsuranceClaim.claim_number),

        # Interaction indexes
        Index('idx_customer_interactions_customer', CustomerInteraction.customer_id),
        Index('idx_customer_interactions_agent', CustomerInteraction.agent_id),
        Index('idx_customer_interactions_date', CustomerInteraction.interaction_date),
        Index('idx_customer_interactions_status', CustomerInteraction.status),
    ]
    return indexes
