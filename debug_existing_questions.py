#!/usr/bin/env python3
"""Debug existing questions in database"""

import requests
import json

def debug_existing_questions():
    """Check what existing questions are causing conflicts"""
    
    base_url = "http://localhost:3006/api/v1/database"
    
    print("🔍 Debugging existing questions...")
    
    # Get all existing training data
    try:
        response = requests.get(f"{base_url}/training-data", timeout=30)
        if response.status_code == 200:
            existing_data = response.json()
            print(f"📊 Found {len(existing_data)} existing training records")
            
            # Group by model name
            by_model = {}
            for item in existing_data:
                model = item.get('model_name', 'unknown')
                if model not in by_model:
                    by_model[model] = []
                by_model[model].append(item)
            
            print(f"\n📋 Training data by model:")
            for model, items in by_model.items():
                print(f"   {model}: {len(items)} questions")
                for i, item in enumerate(items[:3], 1):
                    print(f"     {i}. {item['question'][:60]}...")
            
            # Check for questions that might conflict with fallback questions
            print(f"\n🔍 Looking for potential conflicts with fallback questions...")
            
            fallback_patterns = [
                "show all records",
                "count records", 
                "show first 10 records",
                "highest amounts",
                "high amounts",
                "biggest transactions",
                "largest transactions"
            ]
            
            conflicts = []
            for item in existing_data:
                question_lower = item['question'].lower()
                for pattern in fallback_patterns:
                    if pattern in question_lower:
                        conflicts.append((item['question'], pattern))
                        break
            
            if conflicts:
                print(f"   ⚠️  Found {len(conflicts)} potential conflicts:")
                for question, pattern in conflicts[:10]:
                    print(f"     - '{question}' (matches '{pattern}')")
            else:
                print(f"   ✅ No obvious conflicts found")
                
        else:
            print(f"❌ Failed to get existing data: {response.status_code}")
            print(f"Response: {response.text}")
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    debug_existing_questions()
