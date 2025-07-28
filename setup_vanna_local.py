"""
Quick setup script for local Vanna AI with ChromaDB and OpenAI.
"""

import os
import sys
from pathlib import Path

def main():
    print("🚀 Local Vanna AI Setup for Database Chat")
    print("=" * 50)
    
    # Check if we're in a virtual environment
    if not hasattr(sys, 'real_prefix') and not (hasattr(sys, 'base_prefix') and sys.base_prefix != sys.prefix):
        print("⚠️  Warning: You don't appear to be in a virtual environment.")
        print("It's recommended to use a virtual environment.")
        print("Run: python -m venv venv && venv\\Scripts\\activate")
        print()
    
    # Check if Vanna is installed
    try:
        from vanna.openai.openai_chat import OpenAI_Chat
        from vanna.chromadb.chromadb_vector import ChromaDB_VectorStore
        print("✅ Vanna AI packages are installed")
    except ImportError:
        print("❌ Vanna AI not installed")
        print("Installing Vanna AI with ChromaDB and OpenAI support...")
        os.system('pip install "vanna[chromadb,openai]"')
        print("✅ Vanna AI installed")
    
    # Check for OpenAI API key
    openai_key = os.getenv("OPENAI_API_KEY")
    if not openai_key:
        print("\n🔑 OpenAI API Key Setup")
        print("You need an OpenAI API key to use Vanna AI.")
        print("1. Get your API key from: https://platform.openai.com/api-keys")
        print("2. Set it as an environment variable:")
        print("   Windows: set OPENAI_API_KEY=your_api_key_here")
        print("   Linux/Mac: export OPENAI_API_KEY=your_api_key_here")
        print()
        
        # Ask if user wants to set it now
        key = input("Enter your OpenAI API key (or press Enter to skip): ").strip()
        if key:
            os.environ["OPENAI_API_KEY"] = key
            print("✅ API key set for this session")
        else:
            print("⚠️  You'll need to set OPENAI_API_KEY before using the feature")
    else:
        print(f"✅ OpenAI API key found: {openai_key[:8]}...")
    
    # Create ChromaDB directory
    chroma_path = "./vanna_chromadb"
    Path(chroma_path).mkdir(exist_ok=True)
    print(f"✅ ChromaDB directory ready: {chroma_path}")
    
    # Test the setup
    print("\n🧪 Testing setup...")
    try:
        from src.services.vanna_service import vanna_service
        print("✅ Vanna service imported successfully")
        
        # Test basic functionality
        class TestVanna(ChromaDB_VectorStore, OpenAI_Chat):
            def __init__(self, config=None):
                ChromaDB_VectorStore.__init__(self, config=config)
                OpenAI_Chat.__init__(self, config=config)
        
        if openai_key or os.getenv("OPENAI_API_KEY"):
            config = {
                'api_key': openai_key or os.getenv("OPENAI_API_KEY"),
                'model': 'gpt-4',
                'path': chroma_path
            }
            vn = TestVanna(config=config)
            print("✅ Local Vanna client initialized successfully")
        else:
            print("⚠️  Skipping client test (no API key)")
        
    except Exception as e:
        print(f"❌ Error testing setup: {e}")
        return
    
    print("\n🎉 Setup completed successfully!")
    print("\nNext steps:")
    print("1. Start the application: python main.py")
    print("2. Open http://localhost:3006 in your browser")
    print("3. Navigate to 'Database Chat' in the sidebar")
    print("4. Create tables in the Schema Designer")
    print("5. Train Vanna AI on your tables")
    print("6. Start querying with natural language!")
    
    print("\n📚 Documentation:")
    print("- Local setup guide: VANNA_LOCAL_SETUP.md")
    print("- Database chat docs: DATABASE_CHAT_README.md")
    
    # Create a sample .env file if it doesn't exist
    env_file = Path(".env")
    if not env_file.exists():
        print("\n📝 Creating sample .env file...")
        with open(env_file, "w") as f:
            f.write(f"""# AI Agent Platform Environment Configuration

# Database Configuration
DATABASE_URL=sqlite+aiosqlite:///./ai_agent_platform.db

# API Configuration
API_HOST=127.0.0.1
API_PORT=3006
DEBUG=true

# CORS Origins
CORS_ORIGINS=http://localhost:3000,http://localhost:3003,http://localhost:5173,http://localhost:3006

# OpenAI Configuration (for Vanna AI and other features)
OPENAI_API_KEY={openai_key or 'your_openai_api_key_here'}

# Vanna AI Configuration
VANNA_MODEL_NAME=gpt-4
VANNA_CHROMA_PATH=./vanna_chromadb
VANNA_DEBUG=false

# Other LLM Configuration
LLM_PROVIDER=openai
LLM_MODEL=gpt-4
LLM_API_KEY={openai_key or 'your_openai_api_key_here'}

# Knowledge Base Configuration
KNOWLEDGE_BASE_PROVIDER=chromadb
CHROMA_PERSIST_DIRECTORY=./chroma_db

# Security
SECRET_KEY=your-secret-key-here
JWT_SECRET_KEY=your-jwt-secret-key-here
""")
        print("✅ Sample .env file created")
        if not openai_key:
            print("⚠️  Remember to update OPENAI_API_KEY in .env file")


if __name__ == "__main__":
    main()
