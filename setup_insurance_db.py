"""
Script pour configurer la base de données d'assurance.
Crée les tables et insère des données de test.
"""

import asyncio
import sqlite3
from datetime import datetime, date, timedelta
import uuid

async def create_insurance_tables():
    """Crée les tables du système d'assurance."""
    
    # Connexion à la base de données SQLite
    conn = sqlite3.connect('ai_agent_platform.db')
    cursor = conn.cursor()
    
    # Créer les tables
    tables = [
        """
        CREATE TABLE IF NOT EXISTS customers (
            id TEXT PRIMARY KEY,
            customer_number TEXT UNIQUE NOT NULL,
            first_name TEXT NOT NULL,
            last_name TEXT NOT NULL,
            email TEXT UNIQUE NOT NULL,
            phone TEXT,
            date_of_birth DATE,
            gender TEXT,
            occupation TEXT,
            annual_income REAL,
            marital_status TEXT,
            address_line1 TEXT,
            address_line2 TEXT,
            city TEXT,
            state TEXT,
            postal_code TEXT,
            country TEXT,
            customer_type TEXT DEFAULT 'individual',
            risk_profile TEXT DEFAULT 'medium',
            preferred_language TEXT DEFAULT 'fr',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            is_active BOOLEAN DEFAULT 1,
            kyc_status TEXT DEFAULT 'pending',
            customer_notes TEXT
        )
        """,
        """
        CREATE TABLE IF NOT EXISTS product_categories (
            id TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            description TEXT,
            is_active BOOLEAN DEFAULT 1,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """,
        """
        CREATE TABLE IF NOT EXISTS insurance_products (
            id TEXT PRIMARY KEY,
            product_code TEXT UNIQUE NOT NULL,
            name TEXT NOT NULL,
            category_id TEXT REFERENCES product_categories(id),
            description TEXT,
            product_type TEXT NOT NULL,
            coverage_type TEXT,
            min_coverage_amount REAL,
            max_coverage_amount REAL,
            min_age INTEGER,
            max_age INTEGER,
            waiting_period_days INTEGER DEFAULT 0,
            policy_term_years INTEGER,
            renewable BOOLEAN DEFAULT 1,
            is_active BOOLEAN DEFAULT 1,
            requires_medical_exam BOOLEAN DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """,
        """
        CREATE TABLE IF NOT EXISTS pricing_tiers (
            id TEXT PRIMARY KEY,
            product_id TEXT REFERENCES insurance_products(id),
            tier_name TEXT NOT NULL,
            coverage_amount REAL NOT NULL,
            base_premium REAL NOT NULL,
            premium_frequency TEXT DEFAULT 'monthly',
            currency TEXT DEFAULT 'EUR',
            effective_date DATE DEFAULT CURRENT_DATE,
            expiry_date DATE,
            is_active BOOLEAN DEFAULT 1,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """,
        """
        CREATE TABLE IF NOT EXISTS pricing_factors (
            id TEXT PRIMARY KEY,
            product_id TEXT REFERENCES insurance_products(id),
            factor_name TEXT NOT NULL,
            factor_type TEXT,
            factor_value TEXT,
            multiplier REAL DEFAULT 1.0,
            is_active BOOLEAN DEFAULT 1,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """,
        """
        CREATE TABLE IF NOT EXISTS insurance_orders (
            id TEXT PRIMARY KEY,
            order_number TEXT UNIQUE NOT NULL,
            customer_id TEXT REFERENCES customers(id),
            product_id TEXT REFERENCES insurance_products(id),
            order_status TEXT DEFAULT 'draft',
            coverage_amount REAL NOT NULL,
            premium_amount REAL NOT NULL,
            premium_frequency TEXT DEFAULT 'monthly',
            payment_method TEXT,
            application_date DATE DEFAULT CURRENT_DATE,
            effective_date DATE,
            expiry_date DATE,
            assigned_agent_id TEXT,
            underwriter_id TEXT,
            medical_exam_required BOOLEAN DEFAULT 0,
            medical_exam_completed BOOLEAN DEFAULT 0,
            medical_exam_date DATE,
            documents_received BOOLEAN DEFAULT 0,
            approval_date DATE,
            rejection_reason TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            notes TEXT
        )
        """,
        """
        CREATE TABLE IF NOT EXISTS insurance_contracts (
            id TEXT PRIMARY KEY,
            policy_number TEXT UNIQUE NOT NULL,
            order_id TEXT REFERENCES insurance_orders(id),
            customer_id TEXT REFERENCES customers(id),
            product_id TEXT REFERENCES insurance_products(id),
            contract_status TEXT DEFAULT 'active',
            coverage_amount REAL NOT NULL,
            premium_amount REAL NOT NULL,
            premium_frequency TEXT,
            issue_date DATE NOT NULL,
            effective_date DATE NOT NULL,
            expiry_date DATE,
            next_renewal_date DATE,
            cash_value REAL DEFAULT 0,
            surrender_value REAL DEFAULT 0,
            loan_value REAL DEFAULT 0,
            auto_renewal BOOLEAN DEFAULT 1,
            grace_period_days INTEGER DEFAULT 30,
            last_premium_paid_date DATE,
            next_premium_due_date DATE,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """,
        """
        CREATE TABLE IF NOT EXISTS premium_payments (
            id TEXT PRIMARY KEY,
            contract_id TEXT REFERENCES insurance_contracts(id),
            payment_date DATE,
            due_date DATE NOT NULL,
            amount REAL NOT NULL,
            payment_method TEXT,
            payment_status TEXT DEFAULT 'pending',
            transaction_id TEXT,
            late_fee REAL DEFAULT 0,
            grace_period_used BOOLEAN DEFAULT 0,
            processed_by TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """
    ]
    
    for table_sql in tables:
        cursor.execute(table_sql)
    
    # Insérer des données de test
    
    # Catégories de produits
    categories = [
        (str(uuid.uuid4()), 'Assurance Vie', 'Produits d\'assurance vie et décès'),
        (str(uuid.uuid4()), 'Assurance Santé', 'Complémentaires santé et mutuelles'),
        (str(uuid.uuid4()), 'Assurance Auto', 'Assurance automobile tous risques'),
        (str(uuid.uuid4()), 'Assurance Habitation', 'Assurance logement et biens')
    ]
    
    cursor.executemany(
        "INSERT OR IGNORE INTO product_categories (id, name, description) VALUES (?, ?, ?)",
        categories
    )
    
    # Produits d'assurance
    products = [
        (str(uuid.uuid4()), 'VIE-001', 'Assurance Vie Essentielle', categories[0][0], 
         'Assurance vie avec capital garanti', 'life', 'term', 10000, 500000, 18, 75, 0, 20),
        (str(uuid.uuid4()), 'SANTE-001', 'Mutuelle Famille', categories[1][0],
         'Complémentaire santé pour toute la famille', 'health', 'comprehensive', 0, 0, 0, 99, 0, 1),
        (str(uuid.uuid4()), 'AUTO-001', 'Auto Tous Risques', categories[2][0],
         'Assurance automobile tous risques', 'auto', 'comprehensive', 5000, 100000, 18, 99, 0, 1),
        (str(uuid.uuid4()), 'HAB-001', 'Habitation Confort', categories[3][0],
         'Assurance habitation multirisques', 'home', 'comprehensive', 10000, 1000000, 18, 99, 0, 1)
    ]
    
    cursor.executemany(
        """INSERT OR IGNORE INTO insurance_products 
           (id, product_code, name, category_id, description, product_type, coverage_type, 
            min_coverage_amount, max_coverage_amount, min_age, max_age, waiting_period_days, policy_term_years) 
           VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
        products
    )
    
    # Clients de test
    customers = [
        (str(uuid.uuid4()), 'CUST-20240115-0001', 'Marie', 'Dubois', 'marie.dubois@email.com', 
         '+33 1 23 45 67 89', '1985-03-15', 'female', 'Ingénieure', 55000, 'married',
         '123 Rue de la Paix', '', 'Paris', 'Île-de-France', '75001', 'France', 
         'individual', 'medium', 'fr', 1, 'verified'),
        (str(uuid.uuid4()), 'CUST-20240115-0002', 'Jean', 'Martin', 'jean.martin@email.com',
         '+33 1 98 76 54 32', '1978-07-22', 'male', 'Professeur', 48000, 'single',
         '456 Avenue des Champs', '', 'Lyon', 'Auvergne-Rhône-Alpes', '69000', 'France',
         'individual', 'low', 'fr', 1, 'verified'),
        (str(uuid.uuid4()), 'CUST-20240115-0003', 'Sophie', 'Bernard', 'sophie.bernard@email.com',
         '+33 1 11 22 33 44', '1990-12-08', 'female', 'Médecin', 75000, 'married',
         '789 Boulevard du Prado', '', 'Marseille', 'Provence-Alpes-Côte d\'Azur', '13000', 'France',
         'individual', 'high', 'fr', 1, 'pending')
    ]
    
    cursor.executemany(
        """INSERT OR IGNORE INTO customers 
           (id, customer_number, first_name, last_name, email, phone, date_of_birth, gender, 
            occupation, annual_income, marital_status, address_line1, address_line2, city, 
            state, postal_code, country, customer_type, risk_profile, preferred_language, 
            is_active, kyc_status) 
           VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
        customers
    )
    
    # Niveaux de prix
    pricing_tiers = [
        (str(uuid.uuid4()), products[0][0], 'Essentiel', 50000, 25.50, 'monthly'),
        (str(uuid.uuid4()), products[0][0], 'Confort', 100000, 45.00, 'monthly'),
        (str(uuid.uuid4()), products[0][0], 'Premium', 250000, 95.00, 'monthly'),
        (str(uuid.uuid4()), products[1][0], 'Famille', 0, 89.90, 'monthly'),
        (str(uuid.uuid4()), products[2][0], 'Tous Risques', 15000, 65.00, 'monthly'),
        (str(uuid.uuid4()), products[3][0], 'Multirisques', 50000, 35.00, 'monthly')
    ]
    
    cursor.executemany(
        """INSERT OR IGNORE INTO pricing_tiers 
           (id, product_id, tier_name, coverage_amount, base_premium, premium_frequency) 
           VALUES (?, ?, ?, ?, ?, ?)""",
        pricing_tiers
    )
    
    # Facteurs de tarification
    pricing_factors = [
        # Facteurs d'âge pour l'assurance vie
        (str(uuid.uuid4()), products[0][0], 'Âge 18-30', 'age_group', '18-30', 0.8),
        (str(uuid.uuid4()), products[0][0], 'Âge 31-45', 'age_group', '31-45', 1.0),
        (str(uuid.uuid4()), products[0][0], 'Âge 46-60', 'age_group', '46-60', 1.3),
        (str(uuid.uuid4()), products[0][0], 'Âge 61-75', 'age_group', '61-75', 1.8),
        # Facteurs de genre
        (str(uuid.uuid4()), products[0][0], 'Homme', 'gender', 'male', 1.1),
        (str(uuid.uuid4()), products[0][0], 'Femme', 'gender', 'female', 0.95),
        # Facteurs de risque
        (str(uuid.uuid4()), products[0][0], 'Risque faible', 'risk_profile', 'low', 0.9),
        (str(uuid.uuid4()), products[0][0], 'Risque moyen', 'risk_profile', 'medium', 1.0),
        (str(uuid.uuid4()), products[0][0], 'Risque élevé', 'risk_profile', 'high', 1.4)
    ]
    
    cursor.executemany(
        """INSERT OR IGNORE INTO pricing_factors 
           (id, product_id, factor_name, factor_type, factor_value, multiplier) 
           VALUES (?, ?, ?, ?, ?, ?)""",
        pricing_factors
    )
    
    conn.commit()
    conn.close()
    
    print("✅ Tables d'assurance créées avec succès!")
    print("✅ Données de test insérées!")
    print("\nDonnées créées:")
    print(f"- {len(categories)} catégories de produits")
    print(f"- {len(products)} produits d'assurance")
    print(f"- {len(customers)} clients de test")
    print(f"- {len(pricing_tiers)} niveaux de prix")
    print(f"- {len(pricing_factors)} facteurs de tarification")


if __name__ == "__main__":
    asyncio.run(create_insurance_tables())
