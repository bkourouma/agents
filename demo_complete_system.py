#!/usr/bin/env python3
"""
Démonstration complète du système d'assurance pour la Côte d'Ivoire
"""

import requests
import json
import time

BASE_URL = "http://localhost:3006"

def demo_complete_system():
    """Démonstration complète du système"""
    
    print("🇨🇮 DÉMONSTRATION SYSTÈME D'ASSURANCE - CÔTE D'IVOIRE")
    print("=" * 60)
    print("💰 Devise: XOF (Franc CFA)")
    print("🌍 Marché: Côte d'Ivoire")
    print("🏢 Compagnie: AssuranceCI")
    print("=" * 60)
    
    # 1. Afficher les clients disponibles
    print("\n👥 1. CLIENTS DISPONIBLES")
    print("-" * 30)
    
    customers_response = requests.get(f"{BASE_URL}/api/insurance/clients")
    if customers_response.status_code == 200:
        customers_data = customers_response.json()
        if customers_data.get('success') and customers_data.get('data'):
            for customer in customers_data['data']:
                print(f"   👤 {customer['first_name']} {customer['last_name']}")
                print(f"      📧 {customer['email']}")
                print(f"      🎂 Âge: {2025 - int(customer['date_of_birth'][:4])} ans")
                print(f"      📊 Profil de risque: {customer['risk_profile']}")
                print(f"      ✅ KYC: {customer['kyc_status']}")
                print()
    
    # 2. Afficher les produits disponibles
    print("\n📦 2. PRODUITS D'ASSURANCE DISPONIBLES")
    print("-" * 40)
    
    products_response = requests.get(f"{BASE_URL}/api/insurance/produits")
    if products_response.status_code == 200:
        products_data = products_response.json()
        if products_data.get('success') and products_data.get('data'):
            for product in products_data['data']:
                print(f"   📋 {product['name']} ({product['product_code']})")
                print(f"      🏷️ Type: {product['product_type']}")
                print(f"      💰 Couverture: {product['min_coverage_amount']:,.0f} - {product['max_coverage_amount']:,.0f} XOF")
                print(f"      👥 Âge: {product['min_age']} - {product['max_age']} ans")
                print(f"      📅 Durée: {product['policy_term_years']} an(s)")
                print()
    
    # 3. Générer un devis
    print("\n📋 3. GÉNÉRATION DE DEVIS")
    print("-" * 30)
    
    # Utiliser le premier client et produit disponibles
    customer = customers_data['data'][0]
    life_product = None
    for p in products_data['data']:
        if p['product_type'] == 'life':
            life_product = p
            break
    
    if not life_product:
        life_product = products_data['data'][0]
    
    print(f"   👤 Client: {customer['first_name']} {customer['last_name']}")
    print(f"   📦 Produit: {life_product['name']}")
    
    # Générer le devis
    quote_request = {
        "customer_id": customer['id'],
        "product_id": life_product['id'],
        "coverage_amount": 50000000,  # 50M XOF
        "premium_frequency": "monthly",
        "additional_features": []
    }
    
    print(f"   💰 Couverture demandée: {quote_request['coverage_amount']:,} XOF")
    
    quote_response = requests.post(
        f"{BASE_URL}/api/insurance/devis/generer",
        json=quote_request,
        headers={"Content-Type": "application/json"}
    )
    
    if quote_response.status_code == 200:
        quote_data = quote_response.json()
        if quote_data.get('success'):
            quote = quote_data['data']
            
            print(f"\n   ✅ DEVIS GÉNÉRÉ: {quote['quote_number']}")
            print(f"   💰 Couverture: {quote['coverage_amount']:,} XOF")
            print(f"   💳 Prime mensuelle: {quote['final_premium']:,.0f} XOF")
            print(f"   📅 Prime annuelle: {quote['annual_premium']:,.0f} XOF")
            print(f"   ✅ Éligible: {'Oui' if quote['eligible'] else 'Non'}")
            print(f"   📅 Valable jusqu'au: {quote['expiry_date']}")
            
            if quote.get('pricing_factors'):
                print(f"   📊 Facteurs appliqués:")
                for factor in quote['pricing_factors']:
                    print(f"      - {factor.get('factor_name', 'Inconnu')}: ×{factor.get('multiplier', 1)}")
            
            # 4. Créer une commande
            print(f"\n🛒 4. CRÉATION DE COMMANDE")
            print("-" * 30)
            
            order_response = requests.post(
                f"{BASE_URL}/api/insurance/devis/{quote['id']}/commander?payment_method=bank_transfer&send_email=false",
                headers={"Content-Type": "application/json"}
            )
            
            if order_response.status_code == 200:
                order_data = order_response.json()
                if order_data.get('success'):
                    order = order_data['data']['order']
                    
                    print(f"   ✅ COMMANDE CRÉÉE: {order['order_number']}")
                    print(f"   📅 Date: {order['application_date']}")
                    print(f"   📊 Statut: {order['order_status']}")
                    print(f"   💰 Prime: {order['premium_amount']:,.0f} XOF/{quote['premium_frequency']}")
                    print(f"   💳 Paiement: {order['payment_method']}")
                    
                    # 5. Résumé final
                    print(f"\n🎉 5. RÉSUMÉ DE LA TRANSACTION")
                    print("-" * 40)
                    print(f"   👤 Client: {customer['first_name']} {customer['last_name']}")
                    print(f"   📧 Email: {customer['email']}")
                    print(f"   📋 Devis: {quote['quote_number']}")
                    print(f"   🛒 Commande: {order['order_number']}")
                    print(f"   💰 Couverture: {quote['coverage_amount']:,} XOF")
                    print(f"   💳 Prime mensuelle: {quote['final_premium']:,.0f} XOF")
                    print(f"   📅 Prime annuelle: {quote['annual_premium']:,.0f} XOF")
                    
                    # Conversion approximative en EUR (1 EUR ≈ 656 XOF)
                    eur_coverage = quote['coverage_amount'] / 656
                    eur_monthly = quote['final_premium'] / 656
                    eur_annual = quote['annual_premium'] / 656
                    
                    print(f"\n   💱 ÉQUIVALENT APPROXIMATIF EN EUR:")
                    print(f"   💰 Couverture: ~{eur_coverage:,.0f} EUR")
                    print(f"   💳 Prime mensuelle: ~{eur_monthly:.0f} EUR")
                    print(f"   📅 Prime annuelle: ~{eur_annual:.0f} EUR")
                    
                else:
                    print(f"   ❌ Erreur création commande: {order_data.get('message')}")
            else:
                print(f"   ❌ Erreur API commande: {order_response.status_code}")
                
        else:
            print(f"   ❌ Erreur génération devis: {quote_data.get('message')}")
    else:
        print(f"   ❌ Erreur API devis: {quote_response.status_code}")
    
    print(f"\n" + "=" * 60)
    print("🎯 DÉMONSTRATION TERMINÉE")
    print("✅ Système opérationnel pour la Côte d'Ivoire")
    print("💰 Montants en XOF (Franc CFA)")
    print("🌐 Interface disponible: http://localhost:5174/devis")
    print("=" * 60)

if __name__ == "__main__":
    demo_complete_system()
