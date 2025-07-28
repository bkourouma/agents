#!/usr/bin/env python3
"""Get the last 100 transactions from the correct table"""

import requests
import json

print("🔍 Getting the last 100 transactions from transactionsmobiles table...")

try:
    # Use the table data endpoint (table_id=3 for transactionsmobiles)
    # Get 100 records with larger page size
    response = requests.get(
        "http://localhost:3006/api/v1/database/tables/3/data?page=1&page_size=100"
    )
    
    print(f"📡 Response status: {response.status_code}")
    
    if response.status_code == 200:
        result = response.json()
        
        if 'data' in result and result['data']:
            transactions = result['data']
            print(f"✅ Found {len(transactions)} transactions")
            print("\n📊 Last 100 Transactions:")
            print("=" * 80)
            
            # Print header
            print(f"{'ID':<15} {'Network':<12} {'Type':<15} {'Timestamp':<20} {'Amount':<10}")
            print("-" * 80)
            
            # Print transactions
            for i, tx in enumerate(transactions[:20]):  # Show first 20 for readability
                tx_id = str(tx.get('transactionid', 'N/A'))[:14]
                network = str(tx.get('network', 'N/A'))[:11]
                tx_type = str(tx.get('transactiontype', 'N/A'))[:14]
                timestamp = str(tx.get('timestamp', 'N/A'))[:19]
                amount = str(tx.get('amount', 'N/A'))[:9]
                
                print(f"{tx_id:<15} {network:<12} {tx_type:<15} {timestamp:<20} {amount:<10}")
            
            if len(transactions) > 20:
                print(f"\n... and {len(transactions) - 20} more transactions")
                
            # Show summary statistics
            print(f"\n📈 Summary:")
            print(f"  Total transactions: {len(transactions)}")
            
            # Count by network
            networks = {}
            transaction_types = {}
            total_amount = 0
            
            for tx in transactions:
                network = tx.get('network', 'Unknown')
                tx_type = tx.get('transactiontype', 'Unknown')
                amount = tx.get('amount', 0)
                
                networks[network] = networks.get(network, 0) + 1
                transaction_types[tx_type] = transaction_types.get(tx_type, 0) + 1
                
                if isinstance(amount, (int, float)):
                    total_amount += amount
            
            print(f"  Total amount: {total_amount}")
            print(f"  Networks: {dict(networks)}")
            print(f"  Transaction types: {dict(transaction_types)}")
            
        else:
            print("❌ No transactions found in the table")
            print(f"📄 Response: {json.dumps(result, indent=2)}")
            
    else:
        print(f"❌ Query failed with status {response.status_code}")
        print(f"📄 Error response: {response.text}")
        
except Exception as e:
    print(f"❌ Error getting transactions: {e}")
