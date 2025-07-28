#!/usr/bin/env python3
"""
Create a test order for testing the buttons
"""

import requests
import json

BASE_URL = "http://localhost:3006"

def create_test_order():
    """Create a test order quickly"""
    
    print("🛒 Creating Test Order for Button Testing")
    print("=" * 45)
    
    # Get customer and product
    customers_response = requests.get(f"{BASE_URL}/api/insurance/clients")
    products_response = requests.get(f"{BASE_URL}/api/insurance/produits")
    
    if customers_response.status_code != 200 or products_response.status_code != 200:
        print("   ❌ Failed to get customers or products")
        return
    
    customers_data = customers_response.json()
    products_data = products_response.json()
    
    customer = customers_data['data'][0]
    product = products_data['data'][0]
    
    print(f"   Customer: {customer['first_name']} {customer['last_name']}")
    print(f"   Product: {product['name']}")
    
    # Generate quote
    quote_request = {
        "customer_id": customer['id'],
        "product_id": product['id'],
        "coverage_amount": 30000000,  # 30M XOF
        "premium_frequency": "monthly",
        "additional_features": []
    }
    
    quote_response = requests.post(
        f"{BASE_URL}/api/insurance/devis/generer",
        json=quote_request,
        headers={"Content-Type": "application/json"}
    )
    
    if quote_response.status_code != 200:
        print(f"   ❌ Quote generation failed")
        return
    
    quote_data = quote_response.json()
    if not quote_data.get('success'):
        print(f"   ❌ Quote generation failed")
        return
    
    quote = quote_data['data']
    print(f"   ✅ Quote generated: {quote['quote_number']}")
    
    # Create order from quote
    order_response = requests.post(
        f"{BASE_URL}/api/insurance/devis/{quote['id']}/commander?payment_method=credit_card&send_email=false",
        headers={"Content-Type": "application/json"}
    )
    
    if order_response.status_code != 200:
        print(f"   ❌ Order creation failed")
        return
    
    order_data = order_response.json()
    if not order_data.get('success'):
        print(f"   ❌ Order creation failed")
        return
    
    order = order_data['data']['order']
    order_number = order['order_number']
    
    print(f"   ✅ Order created: {order_number}")
    print(f"   Status: {order['order_status']}")
    print(f"   Coverage: {order['coverage_amount']:,} XOF")
    print(f"   Premium: {order['premium_amount']:,} XOF")
    print(f"   Payment: {order['payment_method']}")
    
    print(f"\n🌐 Frontend Test Instructions:")
    print(f"   1. Go to: http://localhost:5174/assurance")
    print(f"   2. Click on 'Commandes' tab")
    print(f"   3. Click on order: {order_number}")
    print(f"   4. Test the buttons:")
    print(f"      - 'Voir Plus' button should load status history")
    print(f"      - 'Modifier' button should show edit alert")
    print(f"      - Blue info message should disappear after 'Voir Plus'")
    print(f"      - 'Voir Plus' should change to 'Actualiser' after first click")
    
    print(f"\n" + "=" * 45)
    print("🎯 Test Order Created Successfully!")
    print(f"✅ Ready to test buttons with order: {order_number}")

if __name__ == "__main__":
    create_test_order()
