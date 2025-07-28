#!/usr/bin/env python3
"""Train Vanna with high amount transaction examples"""

import asyncio
import requests

async def train_high_amount_examples():
    print("🎯 Training Vanna with high amount examples...")
    
    # High amount training examples
    training_examples = [
        {
            "question": "the 10 transactions with high amount transactions",
            "sql": "SELECT * FROM transactionsmobiles ORDER BY amount DESC LIMIT 10;"
        },
        {
            "question": "show me transactions with high amounts",
            "sql": "SELECT * FROM transactionsmobiles ORDER BY amount DESC LIMIT 10;"
        },
        {
            "question": "top 10 highest transactions",
            "sql": "SELECT * FROM transactionsmobiles ORDER BY amount DESC LIMIT 10;"
        },
        {
            "question": "largest transactions",
            "sql": "SELECT * FROM transactionsmobiles ORDER BY amount DESC LIMIT 20;"
        },
        {
            "question": "highest amount transactions",
            "sql": "SELECT * FROM transactionsmobiles ORDER BY amount DESC LIMIT 10;"
        },
        {
            "question": "transactions sorted by amount",
            "sql": "SELECT * FROM transactionsmobiles ORDER BY amount DESC;"
        },
        {
            "question": "biggest transactions",
            "sql": "SELECT * FROM transactionsmobiles ORDER BY amount DESC LIMIT 10;"
        }
    ]
    
    base_url = "http://localhost:3006"
    
    for example in training_examples:
        print(f"📚 Training: '{example['question']}'")
        
        response = requests.post(f"{base_url}/api/database-chat/train", json={
            "question": example['question'],
            "sql": example['sql']
        })
        
        if response.status_code == 200:
            print(f"✅ Trained successfully")
        else:
            print(f"❌ Training failed: {response.status_code}")
    
    print("\n🧪 Testing the trained query...")
    
    # Test the specific query
    test_response = requests.post(f"{base_url}/api/database-chat/query", json={
        "query": "the 10 transactions with high amount transactions",
        "output_format": "table"
    })
    
    if test_response.status_code == 200:
        result = test_response.json()
        print(f"✅ Test successful!")
        print(f"📄 Generated SQL: {result.get('sql', 'N/A')}")
    else:
        print(f"❌ Test failed: {test_response.status_code}")

if __name__ == "__main__":
    asyncio.run(train_high_amount_examples())
