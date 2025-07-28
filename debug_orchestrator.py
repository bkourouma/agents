#!/usr/bin/env python3
"""
Debug script for orchestrator issues.
"""

import asyncio
import requests
import json

# Configuration
BASE_URL = "http://localhost:3006"  # Adjust to your server
API_PREFIX = "/api/v1"

# Test messages
TEST_MESSAGES = [
    "C'est quoi DocuPro",
    "What is DocuPro",
    "I need help with billing",
    "Can you research AI trends",
    "Help me with my project",
    "Analyze this data"
]

def get_auth_token():
    """Get authentication token."""
    try:
        login_url = f"{BASE_URL}{API_PREFIX}/auth/login"
        login_data = {
            "username": "alice",  # Default test user
            "password": "alicepassword123"
        }

        response = requests.post(login_url, json=login_data)
        if response.status_code == 200:
            token = response.json()["access_token"]
            print(f"✅ Authentication successful")
            return token
        else:
            print(f"❌ Authentication failed: {response.status_code}")
            print(f"Error: {response.text}")
            return None
    except Exception as e:
        print(f"❌ Authentication exception: {e}")
        return None

def test_api_endpoint(endpoint, method="GET", data=None, headers=None):
    """Test an API endpoint and return result."""
    url = f"{BASE_URL}{API_PREFIX}{endpoint}"

    try:
        if method == "GET":
            response = requests.get(url, headers=headers)
        elif method == "POST":
            response = requests.post(url, json=data, headers=headers)

        print(f"\n{'='*60}")
        print(f"Testing: {method} {endpoint}")
        print(f"URL: {url}")
        print(f"Status: {response.status_code}")

        if response.status_code == 200:
            result = response.json()
            print(f"✅ Success!")
            print(f"Response: {json.dumps(result, indent=2)}")
            return result
        else:
            print(f"❌ Failed!")
            print(f"Error: {response.text}")
            return None

    except Exception as e:
        print(f"❌ Exception: {e}")
        return None

def test_intent_analysis(headers):
    """Test intent analysis for each test message."""
    print("\n🎯 TESTING INTENT ANALYSIS")
    print("="*60)

    for message in TEST_MESSAGES:
        endpoint = f"/orchestrator/analyze-intent?message={message}"
        result = test_api_endpoint(endpoint, "POST", headers=headers)

        if result:
            print(f"Message: '{message}'")
            print(f"Intent: {result.get('category')}")
            print(f"Confidence: {result.get('confidence')}")
            print(f"Keywords: {result.get('keywords')}")

def test_agent_matching(headers):
    """Test agent matching for each test message."""
    print("\n🤖 TESTING AGENT MATCHING")
    print("="*60)

    for message in TEST_MESSAGES:
        endpoint = f"/orchestrator/find-agents?message={message}"
        result = test_api_endpoint(endpoint, "POST", headers=headers)

        if result:
            print(f"Message: '{message}'")
            print(f"Intent: {result.get('intent_analysis', {}).get('category')}")
            agents = result.get('matching_agents', [])
            print(f"Found {len(agents)} agents:")
            for i, agent in enumerate(agents):
                print(f"  {i+1}. {agent.get('agent_name')} (score: {agent.get('match_score'):.2f})")

def test_orchestrated_chat(headers):
    """Test full orchestrated chat."""
    print("\n💬 TESTING ORCHESTRATED CHAT")
    print("="*60)

    for message in TEST_MESSAGES:
        endpoint = "/orchestrator/chat"
        data = {
            "message": message,
            "conversation_id": None,
            "context": None
        }

        result = test_api_endpoint(endpoint, "POST", data, headers=headers)

        if result:
            print(f"Message: '{message}'")
            print(f"Response: {result.get('agent_response')}")
            routing = result.get('routing_result', {})
            selected_agent = routing.get('selected_agent')
            agent_name = selected_agent.get('agent_name') if selected_agent else 'None'
            print(f"Selected Agent: {agent_name}")
            print(f"Decision: {routing.get('decision')}")
            print(f"Confidence: {routing.get('confidence')}")

def test_basic_endpoints():
    """Test basic API endpoints."""
    print("\n🏥 TESTING BASIC ENDPOINTS")
    print("="*60)
    
    # Test root endpoint
    try:
        response = requests.get(f"{BASE_URL}/")
        print(f"Root endpoint: {response.status_code}")
        if response.status_code == 200:
            print(f"✅ Server is running: {response.json()}")
        else:
            print(f"❌ Server issue: {response.text}")
    except Exception as e:
        print(f"❌ Cannot connect to server: {e}")
        return False
    
    # Test health endpoint
    try:
        response = requests.get(f"{BASE_URL}/health")
        print(f"Health endpoint: {response.status_code}")
    except Exception as e:
        print(f"❌ Health check failed: {e}")
    
    return True

def main():
    """Run all tests."""
    print("🔧 ORCHESTRATOR DEBUG SCRIPT")
    print("="*60)

    # Test basic connectivity first
    if not test_basic_endpoints():
        print("❌ Cannot connect to server. Please check if it's running.")
        return

    # Get authentication token
    print("\n🔐 AUTHENTICATION")
    print("="*60)
    token = get_auth_token()
    if not token:
        print("❌ Cannot authenticate. Please check credentials.")
        return

    headers = {"Authorization": f"Bearer {token}"}

    # Test individual components with authentication
    test_intent_analysis(headers)
    test_agent_matching(headers)
    test_orchestrated_chat(headers)

    print("\n✅ Debug tests completed!")
    print("\nNext steps:")
    print("1. Check server logs for detailed error messages")
    print("2. Verify database contains active agents")
    print("3. Check agent configuration (tools_config, etc.)")
    print("4. Test direct agent chat to isolate issues")

if __name__ == "__main__":
    main()
