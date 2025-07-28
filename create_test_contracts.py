#!/usr/bin/env python3
"""
Create multiple test contracts for testing the interface
"""

import requests
import json

BASE_URL = "http://localhost:3006"

def create_test_contracts():
    """Create multiple test contracts"""
    
    print("🏗️ Creating Test Contracts")
    print("=" * 30)
    
    # 1. Get available orders
    print(f"\n📋 1. Getting Available Orders...")
    
    orders_response = requests.get(f"{BASE_URL}/api/insurance/commandes")
    
    if orders_response.status_code != 200:
        print(f"   ❌ Failed to get orders")
        return
    
    orders_data = orders_response.json()
    if not orders_data.get('success'):
        print(f"   ❌ Orders API failed")
        return
    
    orders = orders_data.get('data', [])
    print(f"   Found {len(orders)} orders")
    
    # Find orders that can be converted to contracts
    convertible_orders = []
    for order in orders:
        status = order.get('order_status')
        if status in ['draft', 'submitted', 'under_review']:
            convertible_orders.append(order)
    
    print(f"   Found {len(convertible_orders)} convertible orders")
    
    if len(convertible_orders) < 3:
        print(f"   ⚠️ Need at least 3 orders to create diverse contracts")
        print(f"   Creating additional orders first...")
        
        # Create additional orders if needed
        await_create_additional_orders()
        
        # Refresh orders list
        orders_response = requests.get(f"{BASE_URL}/api/insurance/commandes")
        if orders_response.status_code == 200:
            orders_data = orders_response.json()
            if orders_data.get('success'):
                orders = orders_data.get('data', [])
                convertible_orders = [o for o in orders if o.get('order_status') in ['draft', 'submitted', 'under_review']]
    
    # 2. Create contracts with different statuses
    print(f"\n🏗️ 2. Creating Contracts with Different Statuses...")
    
    contracts_created = []
    
    # Take up to 5 orders for testing
    test_orders = convertible_orders[:5]
    
    for i, order in enumerate(test_orders):
        order_id = order['id']
        order_number = order['order_number']
        
        print(f"\n   Creating contract {i+1} from order {order_number}...")
        
        # First approve the order
        approve_response = requests.put(
            f"{BASE_URL}/api/insurance/commandes/{order_id}",
            json={"order_status": "approved"},
            headers={"Content-Type": "application/json"}
        )
        
        if approve_response.status_code == 200:
            print(f"      ✅ Order approved")
            
            # Create contract
            contract_response = requests.post(
                f"{BASE_URL}/api/insurance/contrats/from-order",
                json={"order_id": order_id},
                headers={"Content-Type": "application/json"}
            )
            
            if contract_response.status_code == 200:
                contract_data = contract_response.json()
                if contract_data.get('success'):
                    contract = contract_data['data']
                    policy_number = contract['policy_number']
                    contracts_created.append(contract)
                    
                    print(f"      ✅ Contract created: {policy_number}")
                    print(f"      Coverage: {contract['coverage_amount']:,} XOF")
                    print(f"      Premium: {contract['premium_amount']:,} XOF")
                    
                    # Set different statuses for variety
                    if i == 1:  # Second contract - suspend it
                        print(f"      🔄 Setting to suspended...")
                        status_response = requests.put(
                            f"{BASE_URL}/api/insurance/contrats/{policy_number}/status",
                            json={"status": "suspended", "reason": "Test suspension"},
                            headers={"Content-Type": "application/json"}
                        )
                        if status_response.status_code == 200:
                            print(f"      ✅ Status set to suspended")
                    
                    elif i == 2:  # Third contract - set to lapsed
                        print(f"      🔄 Setting to lapsed...")
                        status_response = requests.put(
                            f"{BASE_URL}/api/insurance/contrats/{policy_number}/status",
                            json={"status": "lapsed", "reason": "Test lapse"},
                            headers={"Content-Type": "application/json"}
                        )
                        if status_response.status_code == 200:
                            print(f"      ✅ Status set to lapsed")
                    
                    elif i == 3:  # Fourth contract - cancel it
                        print(f"      🔄 Setting to cancelled...")
                        status_response = requests.put(
                            f"{BASE_URL}/api/insurance/contrats/{policy_number}/status",
                            json={"status": "cancelled", "reason": "Test cancellation"},
                            headers={"Content-Type": "application/json"}
                        )
                        if status_response.status_code == 200:
                            print(f"      ✅ Status set to cancelled")
                    
                    # Keep others as active
                else:
                    print(f"      ❌ Contract creation failed: {contract_data}")
            else:
                print(f"      ❌ Contract creation HTTP error: {contract_response.status_code}")
        else:
            print(f"      ❌ Order approval failed: {approve_response.status_code}")
    
    # 3. Summary
    print(f"\n📊 3. Summary of Created Contracts...")
    
    # Get all contracts to show final state
    final_response = requests.get(f"{BASE_URL}/api/insurance/contrats")
    if final_response.status_code == 200:
        final_data = final_response.json()
        if final_data.get('success'):
            all_contracts = final_data.get('data', [])
            
            print(f"   Total contracts: {len(all_contracts)}")
            
            # Group by status
            status_counts = {}
            for contract in all_contracts:
                status = contract.get('contract_status', 'unknown')
                status_counts[status] = status_counts.get(status, 0) + 1
            
            print(f"   Status breakdown:")
            for status, count in status_counts.items():
                print(f"      {status.capitalize()}: {count}")
            
            print(f"\n   📋 Contract List:")
            for contract in all_contracts:
                print(f"      {contract['policy_number']} - {contract['contract_status']} - {contract['coverage_amount']:,} XOF")
    
    # 4. Frontend testing instructions
    print(f"\n🌐 4. Frontend Testing Ready!")
    print(f"   ")
    print(f"   You now have multiple contracts to test with:")
    print(f"   1. Go to: http://localhost:5174/assurance")
    print(f"   2. Click 'Contrats' tab")
    print(f"   3. You should see:")
    print(f"      - Statistics showing different status counts")
    print(f"      - Multiple contracts in the list")
    print(f"      - Different status badges (Active, Suspended, Lapsed, Cancelled)")
    print(f"   4. Test features:")
    print(f"      - Search by policy number")
    print(f"      - Filter by status")
    print(f"      - Click contracts to see details")
    print(f"      - Use action buttons")
    
    print(f"\n" + "=" * 30)
    print("🎉 Test Contracts Creation Complete!")
    print(f"✅ {len(contracts_created)} contracts created")
    print("🌐 Ready for comprehensive frontend testing!")

def await_create_additional_orders():
    """Create additional orders if needed"""
    print(f"      Creating additional orders...")
    
    # Get customers and products
    customers_response = requests.get(f"{BASE_URL}/api/insurance/clients")
    products_response = requests.get(f"{BASE_URL}/api/insurance/produits")
    
    if customers_response.status_code == 200 and products_response.status_code == 200:
        customers_data = customers_response.json()
        products_data = products_response.json()
        
        if customers_data.get('success') and products_data.get('success'):
            customers = customers_data['data']
            products = products_data['data']
            
            # Create 3 additional quotes and orders
            for i in range(3):
                customer = customers[i % len(customers)]
                product = products[i % len(products)]
                
                # Generate quote
                quote_request = {
                    "customer_id": customer['id'],
                    "product_id": product['id'],
                    "coverage_amount": 15000000 + (i * 5000000),  # Varying coverage
                    "premium_frequency": ["monthly", "quarterly", "annual"][i % 3],
                    "additional_features": []
                }
                
                quote_response = requests.post(
                    f"{BASE_URL}/api/insurance/devis/generer",
                    json=quote_request,
                    headers={"Content-Type": "application/json"}
                )
                
                if quote_response.status_code == 200:
                    quote_data = quote_response.json()
                    if quote_data.get('success'):
                        quote = quote_data['data']
                        
                        # Create order from quote
                        order_response = requests.post(
                            f"{BASE_URL}/api/insurance/devis/{quote['id']}/commander?payment_method=bank_transfer&send_email=false",
                            headers={"Content-Type": "application/json"}
                        )
                        
                        if order_response.status_code == 200:
                            print(f"         ✅ Additional order created")

if __name__ == "__main__":
    create_test_contracts()
