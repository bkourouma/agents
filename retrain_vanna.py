#!/usr/bin/env python3
"""Retrain Vanna AI with correct schema for transactionsmobiles table"""

import requests
import json

print("🔄 Retraining Vanna AI with correct schema...")

try:
    # Call the retrain endpoint for table_id=3 (transactionsmobiles)
    response = requests.post(
        "http://localhost:3006/api/v1/database/vanna/retrain/3"
    )
    
    print(f"📡 Response status: {response.status_code}")
    
    if response.status_code == 200:
        result = response.json()
        print("✅ Vanna retrained successfully!")
        print(f"📄 Response: {json.dumps(result, indent=2)}")
    else:
        print(f"❌ Retrain failed with status {response.status_code}")
        print(f"📄 Error response: {response.text}")
        
except Exception as e:
    print(f"❌ Error retraining Vanna: {e}")

print("\n🧪 Now testing the query again...")

try:
    # Test the same query that was failing
    test_query = {
        "query": "give me the list of 100 last transactions",
        "output_format": "table"
    }
    
    response = requests.post(
        "http://localhost:3006/api/v1/database/query/natural",
        json=test_query
    )
    
    print(f"📡 Query response status: {response.status_code}")
    
    if response.status_code == 200:
        result = response.json()
        print("✅ Query executed successfully!")
        print(f"📄 SQL Generated: {result.get('sql', 'N/A')}")
        print(f"📊 Result count: {result.get('result_count', 'N/A')}")
        if result.get('error'):
            print(f"❌ Query error: {result['error']}")
    else:
        print(f"❌ Query failed with status {response.status_code}")
        print(f"📄 Error response: {response.text}")
        
except Exception as e:
    print(f"❌ Error testing query: {e}")
