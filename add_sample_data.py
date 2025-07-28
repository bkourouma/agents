"""
Script pour ajouter des données d'exemple supplémentaires au système d'assurance.
"""

import sqlite3
from datetime import datetime, date, timedelta
import uuid

def add_sample_data():
    """Ajoute des données d'exemple pour tester le système."""
    
    conn = sqlite3.connect('ai_agent_platform.db')
    cursor = conn.cursor()
    
    # Ajouter des commandes d'exemple
    orders = [
        (str(uuid.uuid4()), 'ORD-20240115-000001', 
         'CUST-20240115-0001', 'VIE-001', 'approved', 100000, 45.00, 'monthly',
         '2024-01-10', '2024-02-01', '2024-02-01', True, True, '2024-01-12'),
        (str(uuid.uuid4()), 'ORD-20240115-000002', 
         'CUST-20240115-0002', 'SANTE-001', 'submitted', 0, 89.90, 'monthly',
         '2024-01-12', '2024-02-01', None, False, False, None),
        (str(uuid.uuid4()), 'ORD-20240115-000003', 
         'CUST-20240115-0003', 'AUTO-001', 'under_review', 15000, 65.00, 'monthly',
         '2024-01-14', '2024-02-01', None, False, True, None)
    ]
    
    # Insérer les commandes en utilisant les IDs des clients et produits existants
    cursor.execute("SELECT id FROM customers WHERE customer_number = 'CUST-20240115-0001'")
    customer1_id = cursor.fetchone()
    cursor.execute("SELECT id FROM customers WHERE customer_number = 'CUST-20240115-0002'")
    customer2_id = cursor.fetchone()
    cursor.execute("SELECT id FROM customers WHERE customer_number = 'CUST-20240115-0003'")
    customer3_id = cursor.fetchone()
    
    cursor.execute("SELECT id FROM insurance_products WHERE product_code = 'VIE-001'")
    product1_id = cursor.fetchone()
    cursor.execute("SELECT id FROM insurance_products WHERE product_code = 'SANTE-001'")
    product2_id = cursor.fetchone()
    cursor.execute("SELECT id FROM insurance_products WHERE product_code = 'AUTO-001'")
    product3_id = cursor.fetchone()
    
    if all([customer1_id, customer2_id, customer3_id, product1_id, product2_id, product3_id]):
        orders_with_real_ids = [
            (str(uuid.uuid4()), 'ORD-20240115-000001', 
             customer1_id[0], product1_id[0], 'approved', 100000, 45.00, 'monthly',
             '2024-01-10', '2024-02-01', '2024-02-01', True, True, '2024-01-12'),
            (str(uuid.uuid4()), 'ORD-20240115-000002', 
             customer2_id[0], product2_id[0], 'submitted', 0, 89.90, 'monthly',
             '2024-01-12', '2024-02-01', None, False, False, None),
            (str(uuid.uuid4()), 'ORD-20240115-000003', 
             customer3_id[0], product3_id[0], 'under_review', 15000, 65.00, 'monthly',
             '2024-01-14', '2024-02-01', None, False, True, None)
        ]
        
        cursor.executemany(
            """INSERT OR IGNORE INTO insurance_orders 
               (id, order_number, customer_id, product_id, order_status, coverage_amount, 
                premium_amount, premium_frequency, application_date, effective_date, 
                expiry_date, medical_exam_required, documents_received, approval_date) 
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            orders_with_real_ids
        )
    
    # Ajouter des contrats d'exemple
    if customer1_id and product1_id:
        contract_id = str(uuid.uuid4())
        cursor.execute(
            """INSERT OR IGNORE INTO insurance_contracts 
               (id, policy_number, customer_id, product_id, contract_status, coverage_amount, 
                premium_amount, premium_frequency, issue_date, effective_date, expiry_date, 
                next_renewal_date, next_premium_due_date) 
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (contract_id, 'POL-20240115-000001', customer1_id[0], product1_id[0], 'active', 
             100000, 45.00, 'monthly', '2024-01-15', '2024-02-01', '2025-02-01', 
             '2025-01-01', '2024-03-01')
        )
    
    # Ajouter des réclamations d'exemple
    if customer1_id and contract_id:
        claims = [
            (str(uuid.uuid4()), 'REC-20240115-000001', contract_id, customer1_id[0], 
             'health', 'submitted', 2500.00, '2024-01-05', '2024-01-10', 
             'Consultation médicale d\'urgence suite à un accident'),
            (str(uuid.uuid4()), 'REC-20240115-000002', contract_id, customer1_id[0], 
             'accident', 'investigating', 5000.00, '2024-01-08', '2024-01-12', 
             'Accident de voiture avec dommages matériels')
        ]
        
        cursor.executemany(
            """INSERT OR IGNORE INTO insurance_claims 
               (id, claim_number, contract_id, customer_id, claim_type, claim_status, 
                claim_amount, incident_date, report_date, description) 
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            claims
        )
    
    # Ajouter des interactions client d'exemple
    if customer1_id:
        interactions = [
            (str(uuid.uuid4()), customer1_id[0], 'call', '2024-01-15 14:30:00', 
             'Demande d\'information sur les garanties', 
             'Information fournie sur les garanties du contrat', 'resolved', 'medium'),
            (str(uuid.uuid4()), customer2_id[0], 'email', '2024-01-14 10:15:00', 
             'Question sur le délai de traitement', 
             'Explication du processus de souscription', 'resolved', 'low'),
            (str(uuid.uuid4()), customer3_id[0], 'chat', '2024-01-16 16:45:00', 
             'Problème avec les documents', 
             'Aide fournie pour l\'upload des documents', 'open', 'high')
        ]
        
        cursor.executemany(
            """INSERT OR IGNORE INTO customer_interactions 
               (id, customer_id, interaction_type, interaction_date, subject, 
                description, status, priority) 
               VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
            interactions
        )
    
    # Ajouter des documents client d'exemple
    if customer1_id:
        documents = [
            (str(uuid.uuid4()), customer1_id[0], None, None, 'id_proof', 
             'Carte d\'identité', '/uploads/id_card_marie.pdf', 245760, 'application/pdf', 
             'agent_001', '2024-01-10 09:30:00', True, 'agent_002', '2024-01-10 14:20:00'),
            (str(uuid.uuid4()), customer2_id[0], None, None, 'income_proof', 
             'Bulletin de salaire', '/uploads/payslip_jean.pdf', 189432, 'application/pdf', 
             'agent_001', '2024-01-12 11:15:00', False, None, None),
            (str(uuid.uuid4()), customer3_id[0], None, None, 'medical_report', 
             'Rapport médical', '/uploads/medical_sophie.pdf', 567890, 'application/pdf', 
             'agent_003', '2024-01-14 16:00:00', False, None, None)
        ]
        
        cursor.executemany(
            """INSERT OR IGNORE INTO customer_documents 
               (id, customer_id, contract_id, order_id, document_type, document_name, 
                file_path, file_size, mime_type, uploaded_by, upload_date, 
                is_verified, verified_by, verification_date) 
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            documents
        )
    
    conn.commit()
    conn.close()
    
    print("✅ Données d'exemple ajoutées avec succès!")
    print("\nDonnées ajoutées:")
    print("- 3 commandes d'assurance")
    print("- 1 contrat actif")
    print("- 2 réclamations")
    print("- 3 interactions client")
    print("- 3 documents client")


if __name__ == "__main__":
    add_sample_data()
