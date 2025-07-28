"""
Setup script for local Vanna AI with ChromaDB and OpenAI.
Run this script to initialize the local Vanna environment.
"""

import os
import sys
from pathlib import Path

def setup_vanna_environment():
    """Set up the local Vanna environment."""
    
    print("🚀 Setting up Local Vanna AI Environment")
    print("=" * 50)
    
    # Check if required packages are installed
    try:
        from vanna.openai.openai_chat import OpenAI_Chat
        from vanna.chromadb.chromadb_vector import ChromaDB_VectorStore
        print("✅ Vanna AI packages are installed")
    except ImportError as e:
        print("❌ Vanna AI packages not found")
        print("Please install with: pip install 'vanna[chromadb,openai]'")
        return False
    
    # Check for OpenAI API key
    openai_key = os.getenv("OPENAI_API_KEY")
    if not openai_key:
        print("❌ OPENAI_API_KEY environment variable not found")
        print("\nTo set up your OpenAI API key:")
        print("1. Get your API key from: https://platform.openai.com/api-keys")
        print("2. Set the environment variable:")
        print("   Windows: set OPENAI_API_KEY=your_api_key_here")
        print("   Linux/Mac: export OPENAI_API_KEY=your_api_key_here")
        print("3. Or create a .env file in your project root with:")
        print("   OPENAI_API_KEY=your_api_key_here")
        return False
    else:
        print(f"✅ OpenAI API key found: {openai_key[:8]}...")
    
    # Create ChromaDB directory
    chroma_path = os.getenv("VANNA_CHROMA_PATH", "./vanna_chromadb")
    Path(chroma_path).mkdir(exist_ok=True)
    print(f"✅ ChromaDB directory created: {chroma_path}")
    
    # Test Vanna initialization
    try:
        class TestVanna(ChromaDB_VectorStore, OpenAI_Chat):
            def __init__(self, config=None):
                ChromaDB_VectorStore.__init__(self, config=config)
                OpenAI_Chat.__init__(self, config=config)
        
        config = {
            'api_key': openai_key,
            'model': os.getenv("VANNA_MODEL_NAME", "gpt-4"),
            'path': chroma_path
        }
        
        vn = TestVanna(config=config)
        print("✅ Vanna AI client initialized successfully")
        
        # Test basic functionality
        print("\n🧪 Testing basic functionality...")
        
        # Test DDL training
        test_ddl = """
        CREATE TABLE customers (
            id INTEGER PRIMARY KEY,
            name VARCHAR(255) NOT NULL,
            email VARCHAR(255) UNIQUE,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        );
        """
        
        vn.train(ddl=test_ddl)
        print("✅ DDL training test successful")
        
        # Test question-SQL training
        vn.train(
            question="How many customers do we have?",
            sql="SELECT COUNT(*) FROM customers;"
        )
        print("✅ Question-SQL training test successful")
        
        print("\n🎉 Local Vanna AI setup completed successfully!")
        print("\nYour local setup is ready with:")
        print(f"- Model: {config['model']}")
        print(f"- ChromaDB path: {chroma_path}")
        print("- OpenAI API integration")
        
        return True
        
    except Exception as e:
        print(f"❌ Failed to initialize Vanna AI: {e}")
        return False


def create_env_file():
    """Create a sample .env file with Vanna configuration."""
    
    env_content = """# Vanna AI Configuration
# Get your OpenAI API key from: https://platform.openai.com/api-keys
OPENAI_API_KEY=your_openai_api_key_here

# Optional: Specify the OpenAI model to use
VANNA_MODEL_NAME=gpt-4

# Optional: Specify the ChromaDB storage path
VANNA_CHROMA_PATH=./vanna_chromadb

# Optional: Enable debug logging
VANNA_DEBUG=false
"""
    
    env_file = Path(".env.vanna.example")
    with open(env_file, "w") as f:
        f.write(env_content)
    
    print(f"✅ Sample environment file created: {env_file}")
    print("Copy this to .env and update with your actual API key")


def show_usage_examples():
    """Show usage examples for the local Vanna setup."""
    
    print("\n📚 Usage Examples")
    print("=" * 30)
    
    examples = """
# Basic setup in your application:
from vanna.openai.openai_chat import OpenAI_Chat
from vanna.chromadb.chromadb_vector import ChromaDB_VectorStore

class MyVanna(ChromaDB_VectorStore, OpenAI_Chat):
    def __init__(self, config=None):
        ChromaDB_VectorStore.__init__(self, config=config)
        OpenAI_Chat.__init__(self, config=config)

# Initialize
vn = MyVanna(config={
    'api_key': 'your-openai-api-key',
    'model': 'gpt-4',
    'path': './vanna_chromadb'
})

# Train on your database schema
vn.train(ddl="CREATE TABLE users (id INT, name VARCHAR(255));")

# Train with question-SQL pairs
vn.train(
    question="How many users are there?",
    sql="SELECT COUNT(*) FROM users;"
)

# Generate SQL from natural language
sql = vn.generate_sql("Show me all users")
print(sql)

# Connect to your database and run queries
# vn.connect_to_sqlite('your_database.db')
# result = vn.ask("How many users do we have?")
"""
    
    print(examples)


if __name__ == "__main__":
    print("Vanna AI Local Setup")
    print("Choose an option:")
    print("1. Setup Vanna environment")
    print("2. Create sample .env file")
    print("3. Show usage examples")
    print("4. All of the above")
    
    choice = input("\nEnter your choice (1-4): ").strip()
    
    if choice == "1":
        setup_vanna_environment()
    elif choice == "2":
        create_env_file()
    elif choice == "3":
        show_usage_examples()
    elif choice == "4":
        create_env_file()
        print()
        if setup_vanna_environment():
            show_usage_examples()
    else:
        print("Invalid choice. Please run the script again.")
