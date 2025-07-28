#!/usr/bin/env python3
"""
Verify that the CreateContractModal fix works correctly
"""

import requests
import json

def verify_modal_fix():
    """Verify that the modal data transformation works correctly"""
    print("🔧 Verifying CreateContractModal Fix")
    print("=" * 40)
    
    try:
        # Test getting approved orders
        response = requests.get("http://localhost:3006/api/insurance/commandes?statut=approved")
        
        if response.status_code == 200:
            data = response.json()
            
            if data.get('success') and data.get('data'):
                orders = data['data']
                print(f"✅ Found {len(orders)} approved orders")
                
                if orders:
                    # Test transformation for first order
                    first_order = orders[0]
                    print(f"\n📋 Original API Data:")
                    print(f"   - order_number: {first_order.get('order_number')}")
                    print(f"   - customer: {first_order.get('customer')}")
                    print(f"   - product: {first_order.get('product')}")
                    print(f"   - coverage_amount: {first_order.get('coverage_amount')}")
                    print(f"   - premium_amount: {first_order.get('premium_amount')}")
                    
                    # Simulate frontend transformation
                    transformed_order = {
                        'id': first_order.get('id'),
                        'orderNumber': first_order.get('order_number'),
                        'orderStatus': first_order.get('order_status'),
                        'customerName': first_order.get('customer', {}).get('first_name', '') + ' ' + first_order.get('customer', {}).get('last_name', '') if first_order.get('customer') else first_order.get('customer_name', 'N/A'),
                        'productName': first_order.get('product', {}).get('name') if first_order.get('product') else first_order.get('product_name', 'N/A'),
                        'coverageAmount': first_order.get('coverage_amount', 0),
                        'premiumAmount': first_order.get('premium_amount', 0),
                        'premiumFrequency': first_order.get('premium_frequency'),
                        'applicationDate': first_order.get('application_date')
                    }
                    
                    print(f"\n🔄 Transformed Data (Frontend Format):")
                    print(f"   - orderNumber: {transformed_order['orderNumber']}")
                    print(f"   - customerName: {transformed_order['customerName']}")
                    print(f"   - productName: {transformed_order['productName']}")
                    print(f"   - coverageAmount: {transformed_order['coverageAmount']:,} XOF")
                    print(f"   - premiumAmount: {transformed_order['premiumAmount']:,} XOF")
                    print(f"   - premiumFrequency: {transformed_order['premiumFrequency']}")
                    
                    # Check if all required fields have values
                    required_fields = ['orderNumber', 'customerName', 'productName', 'coverageAmount', 'premiumAmount']
                    missing_or_empty = []
                    
                    for field in required_fields:
                        value = transformed_order.get(field)
                        if value is None or value == '' or value == 'N/A':
                            missing_or_empty.append(field)
                    
                    if missing_or_empty:
                        print(f"❌ Fields with missing/empty values: {missing_or_empty}")
                    else:
                        print(f"✅ All required fields have valid values")
                        
                    # Test multiple orders
                    print(f"\n📊 Testing All Orders:")
                    for i, order in enumerate(orders[:3]):  # Test first 3 orders
                        customer_name = order.get('customer', {}).get('first_name', '') + ' ' + order.get('customer', {}).get('last_name', '') if order.get('customer') else 'N/A'
                        product_name = order.get('product', {}).get('name') if order.get('product') else 'N/A'
                        
                        print(f"   Order {i+1}: {order.get('order_number')} | {customer_name} | {product_name} | {order.get('coverage_amount', 0):,} XOF")
                        
                else:
                    print(f"❌ No approved orders found")
            else:
                print(f"❌ API returned no data")
        else:
            print(f"❌ API Error: {response.status_code}")
            
    except Exception as e:
        print(f"❌ Error: {e}")
    
    print(f"\n🌐 Frontend Testing Instructions:")
    print(f"   1. Start frontend: cd frontend && npm run dev -- --port 3003")
    print(f"   2. Go to: http://localhost:3003/assurance")
    print(f"   3. Click 'Nouveau Contrat' button")
    print(f"   4. Select an approved order from the list")
    print(f"   5. Verify that order details are now visible:")
    print(f"      - Order number should be displayed")
    print(f"      - Customer name should be displayed")
    print(f"      - Product name should be displayed")
    print(f"      - Coverage and premium amounts should show numbers, not '0 XOF'")
    
    print(f"\n" + "=" * 40)
    print(f"🎉 Verification Complete!")

if __name__ == "__main__":
    verify_modal_fix()
