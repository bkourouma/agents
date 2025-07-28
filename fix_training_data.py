#!/usr/bin/env python3
import requests
import json

# First, clear existing bad training data
print("1. Clearing existing training data...")
response = requests.get("http://localhost:3006/api/v1/database/training-data")
if response.status_code == 200:
    training_data = response.json()
    for record in training_data:
        delete_response = requests.delete(f"http://localhost:3006/api/v1/database/training-data/{record['id']}")
        if delete_response.status_code == 200:
            print(f"   ✅ Deleted training data ID {record['id']}")
        else:
            print(f"   ❌ Failed to delete training data ID {record['id']}")

# Add correct training data with proper table name and high amount examples
print("\n2. Adding correct training data...")

correct_training_data = [
    {
        "table_id": 1,
        "model_name": "test_model",
        "question": "What are the 10 transactions with highest amounts?",
        "sql": "SELECT * FROM transactionsmobiles ORDER BY amount DESC LIMIT 10;",
        "is_generated": True,
        "is_active": True,
        "confidence_score": 1.0,
        "generation_model": "manual",
        "validation_status": "validated"
    },
    {
        "table_id": 1,
        "model_name": "test_model",
        "question": "Show me transactions with high amounts",
        "sql": "SELECT * FROM transactionsmobiles ORDER BY amount DESC;",
        "is_generated": True,
        "is_active": True,
        "confidence_score": 1.0,
        "generation_model": "manual",
        "validation_status": "validated"
    },
    {
        "table_id": 1,
        "model_name": "test_model",
        "question": "Find the biggest transactions",
        "sql": "SELECT * FROM transactionsmobiles ORDER BY amount DESC LIMIT 20;",
        "is_generated": True,
        "is_active": True,
        "confidence_score": 1.0,
        "generation_model": "manual",
        "validation_status": "validated"
    },
    {
        "table_id": 1,
        "model_name": "test_model",
        "question": "Get top 5 highest amount transactions",
        "sql": "SELECT * FROM transactionsmobiles ORDER BY amount DESC LIMIT 5;",
        "is_generated": True,
        "is_active": True,
        "confidence_score": 1.0,
        "generation_model": "manual",
        "validation_status": "validated"
    },
    {
        "table_id": 1,
        "model_name": "test_model",
        "question": "Show transactions by amount descending",
        "sql": "SELECT * FROM transactionsmobiles ORDER BY amount DESC;",
        "is_generated": True,
        "is_active": True,
        "confidence_score": 1.0,
        "generation_model": "manual",
        "validation_status": "validated"
    },
    {
        "table_id": 1,
        "model_name": "test_model",
        "question": "les 10 transactions avec les montants élevés",
        "sql": "SELECT * FROM transactionsmobiles ORDER BY amount DESC LIMIT 10;",
        "is_generated": True,
        "is_active": True,
        "confidence_score": 1.0,
        "generation_model": "manual",
        "validation_status": "validated"
    },
    {
        "table_id": 1,
        "model_name": "test_model",
        "question": "montants élevés",
        "sql": "SELECT * FROM transactionsmobiles ORDER BY amount DESC;",
        "is_generated": True,
        "is_active": True,
        "confidence_score": 1.0,
        "generation_model": "manual",
        "validation_status": "validated"
    },
    {
        "table_id": 1,
        "model_name": "test_model",
        "question": "transactions avec montants élevés",
        "sql": "SELECT * FROM transactionsmobiles ORDER BY amount DESC;",
        "is_generated": True,
        "is_active": True,
        "confidence_score": 1.0,
        "generation_model": "manual",
        "validation_status": "validated"
    },
    {
        "table_id": 1,
        "model_name": "test_model",
        "question": "the 10 transactions with high amount",
        "sql": "SELECT * FROM transactionsmobiles ORDER BY amount DESC LIMIT 10;",
        "is_generated": True,
        "is_active": True,
        "confidence_score": 1.0,
        "generation_model": "manual",
        "validation_status": "validated"
    },
    {
        "table_id": 1,
        "model_name": "test_model",
        "question": "Show all records from transactionsmobiles",
        "sql": "SELECT * FROM transactionsmobiles;",
        "is_generated": True,
        "is_active": True,
        "confidence_score": 1.0,
        "generation_model": "manual",
        "validation_status": "validated"
    }
]

for i, training_item in enumerate(correct_training_data):
    response = requests.post(
        "http://localhost:3006/api/v1/database/training-data",
        json=training_item
    )
    if response.status_code == 200:
        print(f"   ✅ Added training data {i+1}: {training_item['question']}")
    else:
        print(f"   ❌ Failed to add training data {i+1}: {response.text}")

print("\n3. Verifying training data...")
response = requests.get("http://localhost:3006/api/v1/database/training-data")
if response.status_code == 200:
    training_data = response.json()
    print(f"Total training records: {len(training_data)}")
    for record in training_data:
        print(f"   - {record['question']} -> {record['sql']}")

print("\n✅ Training data fix completed!")
print("Now test the query again to see if it uses ORDER BY amount DESC")
