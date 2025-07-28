#!/usr/bin/env python3
"""Debug what tables exist and their IDs"""

import requests
import json

def debug_tables():
    """Check what tables exist and their IDs"""
    
    base_url = "http://localhost:3006/api/v1/database"
    
    print("🔍 Checking available tables...")
    
    try:
        response = requests.get(f"{base_url}/tables", timeout=30)
        
        print(f"📡 Response status: {response.status_code}")
        
        if response.status_code == 200:
            tables = response.json()
            print(f"✅ Found {len(tables)} tables:")
            
            for table in tables:
                print(f"  ID: {table['id']}")
                print(f"  Name: {table['name']}")
                print(f"  Display Name: {table['display_name']}")
                print(f"  User ID: {table['user_id']}")
                print(f"  Active: {table['is_active']}")
                print(f"  Columns: {len(table.get('columns', []))}")
                print()
                
        else:
            print(f"❌ Failed with status {response.status_code}")
            print(f"📄 Error response: {response.text}")
            
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    debug_tables()
