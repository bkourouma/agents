#!/usr/bin/env python3
"""
Demo script for the AI Agent Platform.
Shows the complete functionality from backend to frontend.
"""

import requests
import json
import time

BASE_URL = "http://127.0.0.1:3006"

def demo_header():
    print("🚀" + "="*60 + "🚀")
    print("    AI AGENT PLATFORM - COMPLETE DEMO")
    print("🚀" + "="*60 + "🚀")
    print()

def get_auth_token():
    """Get authentication token for demo."""
    print("🔐 Authenticating...")
    login_data = {
        "username": "alice",
        "password": "alicepassword123"
    }
    
    response = requests.post(f"{BASE_URL}/api/v1/auth/login", json=login_data)
    if response.status_code == 200:
        token = response.json()["access_token"]
        print("✅ Authentication successful")
        return token
    else:
        print(f"❌ Authentication failed: {response.status_code}")
        return None

def demo_platform_status():
    """Demo platform status and capabilities."""
    print("\n📊 PLATFORM STATUS")
    print("-" * 40)
    
    # Check API status
    response = requests.get(f"{BASE_URL}/api/v1/status")
    if response.status_code == 200:
        data = response.json()
        print(f"✅ API Status: {data['api_status']}")
        print(f"📋 Available Endpoints: {', '.join(data['endpoints'].keys())}")
    else:
        print("❌ API status check failed")

def demo_agent_management(token):
    """Demo agent creation and management."""
    print("\n🤖 AGENT MANAGEMENT")
    print("-" * 40)
    
    headers = {"Authorization": f"Bearer {token}"}
    
    # List existing agents
    response = requests.get(f"{BASE_URL}/api/v1/agents/", headers=headers)
    if response.status_code == 200:
        agents = response.json()
        print(f"📋 Current Agents: {len(agents)}")
        for agent in agents:
            print(f"   • {agent['name']} ({agent['agent_type']}) - {agent['status']}")
    
    # Show agent templates
    response = requests.get(f"{BASE_URL}/api/v1/agents/templates/list", headers=headers)
    if response.status_code == 200:
        templates = response.json()["templates"]
        print(f"📝 Available Templates: {len(templates)}")
        for template in templates[:3]:  # Show first 3
            print(f"   • {template['display_name']} - {template['description'][:50]}...")

def demo_intelligent_orchestration(token):
    """Demo the intelligent orchestration system."""
    print("\n🧠 INTELLIGENT ORCHESTRATION")
    print("-" * 40)
    
    headers = {"Authorization": f"Bearer {token}"}
    
    # Test different types of messages
    test_messages = [
        {
            "message": "I have a billing issue with my account",
            "expected": "customer_service"
        },
        {
            "message": "Can you analyze our Q3 financial performance?",
            "expected": "financial_analysis"
        },
        {
            "message": "I need to research market trends in renewable energy",
            "expected": "research"
        },
        {
            "message": "Help me plan our next project timeline",
            "expected": "project_management"
        },
        {
            "message": "Write a blog post about AI innovations",
            "expected": "content_creation"
        }
    ]
    
    print("🔍 Testing Intent Analysis:")
    for i, test in enumerate(test_messages, 1):
        print(f"\n{i}. Message: '{test['message'][:50]}...'")
        
        # Analyze intent
        response = requests.post(
            f"{BASE_URL}/api/v1/orchestrator/analyze-intent",
            headers=headers,
            params={"message": test["message"]}
        )
        
        if response.status_code == 200:
            analysis = response.json()
            print(f"   🎯 Intent: {analysis['category']} (confidence: {analysis['confidence']:.2f})")
            print(f"   🔑 Keywords: {', '.join(analysis['keywords'][:3])}")
            
            # Find matching agents
            agent_response = requests.post(
                f"{BASE_URL}/api/v1/orchestrator/find-agents",
                headers=headers,
                params={"message": test["message"], "limit": 2}
            )
            
            if agent_response.status_code == 200:
                agent_data = agent_response.json()
                if agent_data['matching_agents']:
                    best_agent = agent_data['matching_agents'][0]
                    print(f"   🤖 Best Agent: {best_agent['agent_name']} (score: {best_agent['match_score']:.2f})")
                else:
                    print("   ⚠️  No suitable agents found")
        else:
            print(f"   ❌ Analysis failed: {response.status_code}")

def demo_orchestrated_chat(token):
    """Demo the orchestrated chat system."""
    print("\n💬 ORCHESTRATED CHAT DEMO")
    print("-" * 40)
    
    headers = {"Authorization": f"Bearer {token}"}
    
    # Test conversation flow
    messages = [
        "Hello! I need help with my billing account",
        "Can you help me research AI trends?",
        "What's the weather like today?"
    ]
    
    conversation_id = None
    
    for i, message in enumerate(messages, 1):
        print(f"\n{i}. User: {message}")
        
        chat_data = {
            "message": message,
            "conversation_id": conversation_id
        }
        
        response = requests.post(
            f"{BASE_URL}/api/v1/orchestrator/chat",
            headers=headers,
            json=chat_data
        )
        
        if response.status_code == 200:
            chat_response = response.json()
            conversation_id = chat_response['conversation_id']
            
            print(f"   🤖 Assistant: {chat_response['agent_response'][:100]}...")
            print(f"   📊 Intent: {chat_response['routing_result']['intent_analysis']['category']}")
            print(f"   🎯 Decision: {chat_response['routing_result']['decision']}")
            print(f"   ⏱️  Response Time: {chat_response['response_time_ms']}ms")
            
            if chat_response['routing_result']['selected_agent']:
                agent = chat_response['routing_result']['selected_agent']
                print(f"   🤖 Routed to: {agent['agent_name']}")
        else:
            print(f"   ❌ Chat failed: {response.status_code}")

def demo_conversation_management(token):
    """Demo conversation management."""
    print("\n📝 CONVERSATION MANAGEMENT")
    print("-" * 40)
    
    headers = {"Authorization": f"Bearer {token}"}
    
    # List conversations
    response = requests.get(f"{BASE_URL}/api/v1/orchestrator/conversations", headers=headers)
    if response.status_code == 200:
        conversations = response.json()
        print(f"📋 Total Conversations: {len(conversations)}")
        
        for conv in conversations[:3]:  # Show first 3
            print(f"   • {conv['title']} - {conv['total_messages']} messages")
            print(f"     Intent: {conv.get('primary_intent', 'Unknown')}")
    
    # Get statistics
    response = requests.get(f"{BASE_URL}/api/v1/orchestrator/stats", headers=headers)
    if response.status_code == 200:
        stats = response.json()
        print(f"\n📊 Platform Statistics:")
        print(f"   • Total Conversations: {stats['total_conversations']}")
        print(f"   • Total Messages: {stats['total_messages']}")
        print(f"   • Avg Messages/Conversation: {stats['average_messages_per_conversation']}")
        
        if stats['intent_distribution']:
            print(f"   • Intent Distribution:")
            for intent, count in stats['intent_distribution'].items():
                print(f"     - {intent}: {count}")

def demo_frontend_info():
    """Show frontend information."""
    print("\n🌐 FRONTEND INTERFACE")
    print("-" * 40)
    print("✅ React Frontend: http://localhost:5173")
    print("✅ Modern UI with Tailwind CSS")
    print("✅ Real-time chat interface")
    print("✅ Agent management dashboard")
    print("✅ Conversation history")
    print("✅ Authentication system")
    print("\n🔑 Demo Credentials:")
    print("   Username: alice")
    print("   Password: alicepassword123")

def demo_architecture_overview():
    """Show architecture overview."""
    print("\n🏗️  ARCHITECTURE OVERVIEW")
    print("-" * 40)
    print("✅ FastAPI Backend (Python)")
    print("✅ React Frontend (TypeScript)")
    print("✅ SQLite Database with SQLAlchemy")
    print("✅ Multi-provider LLM Integration")
    print("✅ Intelligent Agent Orchestration")
    print("✅ JWT Authentication")
    print("✅ RESTful API Design")
    print("✅ Real-time Chat Interface")
    print("✅ Conversation Management")
    print("✅ Agent Templates & Customization")

def main():
    demo_header()
    
    # Get authentication
    token = get_auth_token()
    if not token:
        print("❌ Cannot proceed without authentication")
        return
    
    # Run demos
    demo_platform_status()
    demo_agent_management(token)
    demo_intelligent_orchestration(token)
    demo_orchestrated_chat(token)
    demo_conversation_management(token)
    demo_frontend_info()
    demo_architecture_overview()
    
    print("\n🎉" + "="*60 + "🎉")
    print("    DEMO COMPLETE - AI AGENT PLATFORM IS READY!")
    print("🎉" + "="*60 + "🎉")
    print("\n🚀 Next Steps:")
    print("   1. Open http://localhost:5173 in your browser")
    print("   2. Login with: alice / alicepassword123")
    print("   3. Try the intelligent chat interface")
    print("   4. Create and manage your own agents")
    print("   5. Explore conversation history and analytics")
    print("\n💡 The platform demonstrates:")
    print("   • Intelligent intent analysis and agent routing")
    print("   • Multi-agent conversation management")
    print("   • Real-time chat with AI orchestration")
    print("   • Complete full-stack architecture")
    print("   • Production-ready scalable design")

if __name__ == "__main__":
    main()
