#!/usr/bin/env python3
"""
Create an eligible customer for testing quotes
"""

import requests
import json

BASE_URL = "http://localhost:3006"

def create_eligible_customer():
    """Create a customer eligible for insurance"""
    customer_data = {
        "first_name": "Jean",
        "last_name": "Dupont",
        "email": "jean.dupont@example.com",
        "phone": "+33 1 23 45 67 89",
        "date_of_birth": "1985-05-15",  # 38 years old, eligible
        "city": "Paris",
        "customer_type": "individual",
        "risk_profile": "low",
        "kyc_status": "verified"
    }
    
    response = requests.post(
        f"{BASE_URL}/api/insurance/clients",
        json=customer_data,
        headers={"Content-Type": "application/json"}
    )
    
    print(f"CREATE Customer Response:")
    print(f"Status: {response.status_code}")
    print(f"Response: {response.json()}")
    
    if response.status_code == 200:
        data = response.json()
        if data.get('success') and data.get('data'):
            return data['data']
    return None

def test_quote_with_eligible_customer(customer):
    """Test generating a quote with the eligible customer"""
    # Get products
    products_response = requests.get(f"{BASE_URL}/api/insurance/produits")
    
    if products_response.status_code != 200:
        print("Failed to get products")
        return None
    
    products_data = products_response.json()
    if not (products_data.get('success') and products_data.get('data')):
        print("No products available")
        return None
    
    # Find a suitable product (life insurance)
    product = None
    for p in products_data['data']:
        if p['product_type'] == 'life':
            product = p
            break
    
    if not product:
        product = products_data['data'][0]  # Fallback to first product
    
    quote_request = {
        "customer_id": customer['id'],
        "product_id": product['id'],
        "coverage_amount": 50000,
        "premium_frequency": "monthly",
        "additional_features": []
    }
    
    response = requests.post(
        f"{BASE_URL}/api/insurance/devis/generer",
        json=quote_request,
        headers={"Content-Type": "application/json"}
    )
    
    print(f"\nGENERATE Quote Response:")
    print(f"Status: {response.status_code}")
    print(f"Response: {response.json()}")
    
    if response.status_code == 200:
        data = response.json()
        if data.get('success') and data.get('data'):
            quote_data = data['data']
            if quote_data.get('eligible', True) and 'id' in quote_data:
                return quote_data['id']
            else:
                print(f"Quote not eligible: {quote_data.get('reason', 'Unknown reason')}")
    return None

if __name__ == "__main__":
    print("Creating eligible customer...")
    customer = create_eligible_customer()
    
    if customer:
        print(f"\nCustomer created: {customer['first_name']} {customer['last_name']} (ID: {customer['id']})")
        
        print("\nTesting quote generation...")
        quote_id = test_quote_with_eligible_customer(customer)
        
        if quote_id:
            print(f"\nQuote created successfully with ID: {quote_id}")
        else:
            print("\nFailed to create quote")
    else:
        print("Failed to create customer")
