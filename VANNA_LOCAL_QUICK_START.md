# Vanna AI Local Setup - Quick Start Guide

## 🚀 Quick Setup (5 minutes)

### 1. Install Vanna AI
```bash
# Activate your virtual environment
venv\Scripts\activate  # Windows
# or
source venv/bin/activate  # Linux/Mac

# Install Vanna with ChromaDB and OpenAI support
pip install "vanna[chromadb,openai]"
```

### 2. Get OpenAI API Key
1. Visit [OpenAI Platform](https://platform.openai.com/api-keys)
2. Create a new API key
3. Set it as environment variable:

**Windows:**
```cmd
set OPENAI_API_KEY=your_api_key_here
```

**Linux/Mac:**
```bash
export OPENAI_API_KEY=your_api_key_here
```

### 3. Run Setup Script
```bash
python setup_vanna_local.py
```

### 4. Start the Application
```bash
python main.py
```

### 5. Access Database Chat
1. Open http://localhost:3006
2. Navigate to "Database Chat" in the sidebar
3. Start creating tables and querying with natural language!

## ✅ Verification

Test that everything is working:

```bash
# Test imports
python -c "from vanna.openai.openai_chat import OpenAI_Chat; from vanna.chromadb.chromadb_vector import ChromaDB_VectorStore; print('✅ Vanna imports successful')"

# Test service
python -c "from src.services.vanna_service import vanna_service; print('✅ Vanna service ready')"

# Test main app
python -c "from main import app; print('✅ Application ready')"
```

## 🎯 What You Get

### Local Architecture
- **ChromaDB**: Local vector database for storing schema information
- **OpenAI API**: For natural language to SQL conversion
- **No External Dependencies**: Everything runs locally except OpenAI API calls

### Features Ready to Use
1. **Schema Designer**: Create database tables visually
2. **Data Manager**: Import/export data via Excel
3. **AI Training**: Train Vanna on your database schema
4. **Natural Language Queries**: Ask questions in plain English

## 📝 Example Usage

### 1. Create a Table
```
Table Name: customers
Columns:
- id (INTEGER, Primary Key)
- name (VARCHAR(255), Not Null)
- email (VARCHAR(255), Unique)
- created_at (DATETIME)
```

### 2. Train Vanna AI
- Go to "AI Training" tab
- Select your tables
- Click "Start Training"
- Wait for completion

### 3. Query with Natural Language
```
"How many customers do we have?"
"Show me all customers created this month"
"What's the most common email domain?"
```

## 🔧 Configuration

### Environment Variables
```bash
# Required
OPENAI_API_KEY=your_api_key_here

# Optional (with defaults)
VANNA_MODEL_NAME=gpt-4                    # OpenAI model to use
VANNA_CHROMA_PATH=./vanna_chromadb        # ChromaDB storage path
VANNA_DEBUG=false                         # Enable debug logging
```

### Model Options
- `gpt-3.5-turbo`: Faster, cheaper
- `gpt-4`: Better accuracy (recommended)
- `gpt-4-turbo`: Latest model

## 🐛 Troubleshooting

### Common Issues

**"Vanna AI not available"**
```bash
pip install "vanna[chromadb,openai]"
```

**"OpenAI API key not found"**
```bash
export OPENAI_API_KEY=your_actual_key
```

**Import errors**
```bash
# Reinstall with all dependencies
pip uninstall vanna
pip install "vanna[chromadb,openai]"
```

**ChromaDB permission errors**
```bash
mkdir -p ./vanna_chromadb
chmod 755 ./vanna_chromadb
```

### Debug Mode
```bash
VANNA_DEBUG=true python main.py
```

## 💰 Cost Considerations

### OpenAI API Costs
- **Training**: ~$0.01-0.10 per table (one-time)
- **Queries**: ~$0.01-0.05 per query
- **Model choice**: gpt-3.5-turbo is ~10x cheaper than gpt-4

### Cost Optimization
1. Use `gpt-3.5-turbo` for development
2. Cache common queries
3. Train incrementally
4. Use specific questions rather than broad ones

## 🔒 Security

### Local Data
- Schema information stored locally in ChromaDB
- No data sent to external services except OpenAI API calls
- Database content stays on your machine

### API Key Security
- Never commit API keys to version control
- Use environment variables or .env files
- Rotate keys regularly

## 📚 Next Steps

1. **Read Full Documentation**: `DATABASE_CHAT_README.md`
2. **Advanced Setup**: `VANNA_LOCAL_SETUP.md`
3. **Create Your First Database**: Use the Schema Designer
4. **Train and Query**: Follow the in-app workflow

## 🆘 Support

If you encounter issues:
1. Check the troubleshooting section above
2. Verify your OpenAI API key is valid
3. Ensure all dependencies are installed
4. Check application logs for error messages

---

**Ready to start?** Run `python setup_vanna_local.py` and follow the prompts!
