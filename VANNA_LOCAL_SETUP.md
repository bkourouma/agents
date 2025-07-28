# Local Vanna AI Setup Guide

This guide will help you set up Vanna AI locally with ChromaDB and OpenAI for the Database Chat feature.

## Prerequisites

1. **OpenAI API Key**: Get your API key from [OpenAI Platform](https://platform.openai.com/api-keys)
2. **Python Environment**: Ensure you have Python 3.8+ with the virtual environment activated

## Installation Steps

### 1. Install Vanna AI with ChromaDB and OpenAI Support

```bash
# Activate your virtual environment
venv\Scripts\activate  # Windows
# or
source venv/bin/activate  # Linux/Mac

# Install Vanna with required extras
pip install "vanna[chromadb,openai]"
```

### 2. Set Environment Variables

Create a `.env` file in your project root or set environment variables:

```bash
# Required: Your OpenAI API key
OPENAI_API_KEY=your_openai_api_key_here

# Optional: Specify the model (default: gpt-4)
VANNA_MODEL_NAME=gpt-4

# Optional: ChromaDB storage path (default: ./vanna_chromadb)
VANNA_CHROMA_PATH=./vanna_chromadb

# Optional: Enable debug logging
VANNA_DEBUG=false
```

**Windows (Command Prompt):**
```cmd
set OPENAI_API_KEY=your_openai_api_key_here
set VANNA_MODEL_NAME=gpt-4
```

**Windows (PowerShell):**
```powershell
$env:OPENAI_API_KEY="your_openai_api_key_here"
$env:VANNA_MODEL_NAME="gpt-4"
```

**Linux/Mac:**
```bash
export OPENAI_API_KEY=your_openai_api_key_here
export VANNA_MODEL_NAME=gpt-4
```

### 3. Test the Setup

Run the setup verification script:

```bash
python vanna_setup.py
```

Or run the test script:

```bash
python test_vanna_local.py
```

### 4. Start the Application

```bash
python main.py
```

The application will start on `http://localhost:3006`

## How It Works

### Local Architecture

```
Your Application
       ↓
Local Vanna Service
       ↓
┌─────────────────┐    ┌──────────────────┐
│   ChromaDB      │    │   OpenAI API     │
│   (Vector DB)   │    │   (LLM)          │
│   - Stores      │    │   - Generates    │
│   - Schema      │    │   - SQL queries  │
│   - Examples    │    │   - Explanations │
└─────────────────┘    └──────────────────┘
```

### What Happens During Training

1. **Schema Analysis**: Vanna analyzes your database table structures
2. **Vector Storage**: Table schemas and relationships are stored in ChromaDB
3. **Example Generation**: Sample questions and SQL pairs are created
4. **Model Training**: The local vector database is populated with your data context

### What Happens During Querying

1. **Question Processing**: Your natural language question is analyzed
2. **Context Retrieval**: Relevant schema information is retrieved from ChromaDB
3. **SQL Generation**: OpenAI generates SQL based on the question and context
4. **Query Execution**: The generated SQL is executed against your database

## Usage Examples

### Basic Training

```python
# The system automatically trains when you:
# 1. Create tables in the Schema Designer
# 2. Use the AI Training tab to train on selected tables

# Manual training example:
from src.services.vanna_service import vanna_service

# Train on DDL
await vanna_service.train_on_tables(
    db=db_session,
    table_ids=[1, 2, 3],
    user_id=1,
    model_name="my_database_model"
)
```

### Natural Language Queries

Once trained, you can ask questions like:

- "How many customers do we have?"
- "Show me all orders from last month"
- "What's the total revenue by product category?"
- "List customers who haven't placed orders recently"

## Configuration Options

### Model Selection

You can use different OpenAI models:

```bash
# For faster, cheaper queries
VANNA_MODEL_NAME=gpt-3.5-turbo

# For better accuracy (default)
VANNA_MODEL_NAME=gpt-4

# For latest model
VANNA_MODEL_NAME=gpt-4-turbo
```

### ChromaDB Configuration

```bash
# Store ChromaDB in a specific location
VANNA_CHROMA_PATH=/path/to/your/chromadb

# For development (default)
VANNA_CHROMA_PATH=./vanna_chromadb
```

## Troubleshooting

### Common Issues

1. **"Vanna AI not available" Error**
   ```bash
   # Solution: Install the correct package
   pip install "vanna[chromadb,openai]"
   ```

2. **"OpenAI API key not found" Error**
   ```bash
   # Solution: Set the environment variable
   export OPENAI_API_KEY=your_actual_api_key
   ```

3. **ChromaDB Permission Errors**
   ```bash
   # Solution: Ensure the directory is writable
   mkdir -p ./vanna_chromadb
   chmod 755 ./vanna_chromadb
   ```

4. **Import Errors**
   ```bash
   # Solution: Reinstall with all dependencies
   pip uninstall vanna
   pip install "vanna[chromadb,openai]"
   ```

### Debug Mode

Enable debug logging to see what's happening:

```bash
VANNA_DEBUG=true
```

### Testing Connection

```python
# Test script to verify everything works
python test_vanna_local.py
```

## Performance Tips

1. **Model Selection**: Use `gpt-3.5-turbo` for faster responses, `gpt-4` for better accuracy
2. **Training Data**: Provide good examples of questions and SQL pairs
3. **Schema Documentation**: Add descriptions to your tables and columns
4. **Incremental Training**: Train on new tables as you add them

## Security Considerations

1. **API Key Security**: Never commit your OpenAI API key to version control
2. **Local Storage**: ChromaDB data is stored locally and not sent to external services
3. **Query Validation**: Always review generated SQL before execution in production
4. **Access Control**: Use the application's built-in user authentication

## Cost Management

- **Model Choice**: `gpt-3.5-turbo` is ~10x cheaper than `gpt-4`
- **Query Optimization**: Cache common queries to reduce API calls
- **Training Efficiency**: Train incrementally rather than retraining everything

## Next Steps

1. **Create Tables**: Use the Schema Designer to create your database tables
2. **Train the Model**: Use the AI Training tab to train Vanna on your schema
3. **Start Querying**: Use the Natural Language Query interface to ask questions
4. **Iterate**: Add more examples and refine your schema for better results

## Support

If you encounter issues:

1. Check the application logs for error messages
2. Verify your OpenAI API key is valid and has credits
3. Ensure all dependencies are installed correctly
4. Review the troubleshooting section above

For more advanced usage, see the [Vanna AI documentation](https://vanna.ai/docs/).
