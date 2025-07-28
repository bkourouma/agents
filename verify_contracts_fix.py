#!/usr/bin/env python3
"""
Verify that the contracts fix works
"""

import requests
import json

BASE_URL = "http://localhost:3006"

def verify_contracts_fix():
    """Verify that the contracts data structure is correct"""
    
    print("🔧 Verifying Contracts Fix")
    print("=" * 25)
    
    # Test API data structure
    print(f"\n📋 Testing API Data Structure...")
    
    try:
        contracts_response = requests.get(f"{BASE_URL}/api/insurance/contrats")
        
        if contracts_response.status_code == 200:
            contracts_data = contracts_response.json()
            if contracts_data.get('success'):
                contracts = contracts_data.get('data', [])
                print(f"   ✅ Found {len(contracts)} contracts")
                
                if contracts:
                    sample_contract = contracts[0]
                    print(f"   📊 Sample contract:")
                    print(f"      policy_number: {sample_contract.get('policy_number')}")
                    print(f"      contract_status: {sample_contract.get('contract_status')}")
                    print(f"      coverage_amount: {sample_contract.get('coverage_amount')} ({type(sample_contract.get('coverage_amount')).__name__})")
                    print(f"      premium_amount: {sample_contract.get('premium_amount')} ({type(sample_contract.get('premium_amount')).__name__})")
                    
                    # Test that numeric fields are not None
                    coverage = sample_contract.get('coverage_amount')
                    premium = sample_contract.get('premium_amount')
                    
                    if coverage is not None and premium is not None:
                        print(f"   ✅ Numeric fields are not None")
                        print(f"   ✅ Frontend should work correctly now")
                    else:
                        print(f"   ❌ Some numeric fields are None")
                        print(f"      coverage_amount: {coverage}")
                        print(f"      premium_amount: {premium}")
                else:
                    print(f"   ⚠️ No contracts found")
            else:
                print(f"   ❌ API returned success=false: {contracts_data}")
        else:
            print(f"   ❌ API error: {contracts_response.status_code}")
            
    except Exception as e:
        print(f"   ❌ Exception: {e}")
    
    print(f"\n🌐 Frontend Testing:")
    print(f"   1. Go to: http://localhost:5174/assurance")
    print(f"   2. Click 'Contrats' tab")
    print(f"   3. Should load without errors now")
    
    print(f"\n" + "=" * 25)
    print("🎉 Verification Complete!")

if __name__ == "__main__":
    verify_contracts_fix()
