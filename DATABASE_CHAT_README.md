# Database Chat Feature

## Overview

The Database Chat feature provides a comprehensive database management and natural language querying system powered by Vanna AI. Users can design database schemas, manage data, train AI models, and query their data using natural language.

## Features

### 1. Schema Designer
- **Visual Table Creation**: Create database tables with an intuitive form-based interface
- **Column Management**: Add, edit, and configure columns with various data types
- **Schema Visualization**: View your complete database schema at a glance
- **Data Type Support**: INTEGER, VARCHAR, TEXT, BOOLEAN, DATETIME, DATE, TIME, DECIMAL, FLOAT, JSON

### 2. Data Manager
- **CRUD Operations**: Full create, read, update, delete functionality
- **Excel Import/Export**: Upload Excel files to populate tables
- **Template Generation**: Download Excel templates based on table schema
- **Bulk Operations**: Efficient handling of large datasets
- **Data Validation**: Automatic validation during import

### 3. Vanna AI Training
- **Selective Training**: Choose which tables to include in AI training
- **Model Management**: Create and manage multiple trained models
- **Training Status**: Real-time training progress monitoring
- **Schema Learning**: AI learns table relationships and column types

### 4. Natural Language Query
- **Plain English Queries**: Ask questions in natural language
- **Multiple Output Formats**: Table, JSON, or text output
- **Query History**: Save and manage previous queries
- **Favorites**: Mark frequently used queries
- **SQL Generation**: View the generated SQL for learning

## API Endpoints

### Schema Management
```
POST   /api/v1/database/tables              # Create table
GET    /api/v1/database/tables              # List tables
GET    /api/v1/database/tables/{id}         # Get table details
PUT    /api/v1/database/tables/{id}         # Update table
DELETE /api/v1/database/tables/{id}         # Delete table
POST   /api/v1/database/tables/{id}/columns # Add column
GET    /api/v1/database/tables/{id}/columns # List columns
GET    /api/v1/database/schema              # Get full schema
```

### Data Management
```
GET    /api/v1/database/tables/{id}/data           # Get table data
POST   /api/v1/database/tables/{id}/data           # Insert data
GET    /api/v1/database/tables/{id}/template       # Download template
POST   /api/v1/database/tables/{id}/import         # Import Excel data
```

### Natural Language Queries
```
POST   /api/v1/database/query/natural              # Execute NL query
GET    /api/v1/database/query/history              # Get query history
PUT    /api/v1/database/query/history/{id}/favorite # Toggle favorite
```

### Vanna AI Training
```
POST   /api/v1/database/vanna/train                # Start training
GET    /api/v1/database/vanna/status/{id}          # Get training status
```

## Data Models

### DatabaseTable
- `id`: Unique identifier
- `name`: Database table name (lowercase, alphanumeric + underscores)
- `display_name`: Human-readable name
- `description`: Optional description
- `user_id`: Owner user ID
- `is_active`: Soft delete flag
- `metadata_config`: Additional configuration

### DatabaseColumn
- `id`: Unique identifier
- `table_id`: Parent table ID
- `name`: Column name (lowercase, alphanumeric + underscores)
- `display_name`: Human-readable name
- `data_type`: Column data type (enum)
- `max_length`: For VARCHAR types
- `precision`/`scale`: For DECIMAL types
- `is_nullable`: NULL constraint
- `is_primary_key`: Primary key flag
- `is_unique`: Unique constraint
- `default_value`: Default value
- `order_index`: Display order

## Frontend Components

### DatabaseChatPage
Main container component with tabbed interface:
- Schema Designer tab
- Data Manager tab
- AI Training tab
- Natural Language Query tab
- Analytics tab (placeholder)

### SchemaDesigner
- Table list with search and filtering
- Table details view with column management
- TableCreator modal for creating/editing tables
- ColumnEditor modal for adding columns
- SchemaVisualizer for overview

### DataManager
- Table selection
- Data grid with pagination
- Import/export functionality
- CRUD operations

### VannaTraining
- Table selection for training
- Model configuration
- Training progress monitoring
- Training history

### NaturalLanguageQuery
- Query input with suggestions
- Multiple output format options
- Results display (table/JSON/text)
- Query history sidebar
- Favorite queries

## Installation & Setup

### Backend Dependencies
```bash
pip install vanna xlsxwriter aiosqlite
```

### Environment Variables
```bash
VANNA_API_KEY=your_vanna_api_key
VANNA_MODEL_NAME=your_model_name
```

### Database Migration
The database tables are automatically created when the application starts.

## Usage Examples

### Creating a Table
1. Navigate to Database Chat → Schema Designer
2. Click "New Table"
3. Enter table name and description
4. Add columns with appropriate data types
5. Set constraints (primary key, unique, not null)

### Training Vanna AI
1. Go to AI Training tab
2. Select tables to include in training
3. Enter a model name
4. Click "Start Training"
5. Monitor progress in training history

### Natural Language Queries
```
"Show me all customers from New York"
"What's the total revenue this month?"
"List the top 10 products by sales"
"How many orders were placed yesterday?"
```

## Security Considerations

- All API endpoints require authentication
- User isolation - users can only access their own tables
- SQL injection prevention in generated queries
- File upload validation for Excel imports
- Audit logging for all database operations

## Performance Optimization

- Pagination for large datasets
- Connection pooling for database operations
- Caching for schema information
- Background processing for imports
- Query result limiting

## Troubleshooting

### Common Issues

1. **Vanna AI not available**
   - Check VANNA_API_KEY environment variable
   - Verify Vanna package installation
   - Check network connectivity

2. **Training fails**
   - Ensure tables have sufficient data
   - Check table schema complexity
   - Verify model name uniqueness

3. **Import errors**
   - Validate Excel file format
   - Check column mapping
   - Verify data types match schema

4. **Query generation issues**
   - Ensure model is trained on relevant tables
   - Use clear, specific language
   - Check table and column names

## Future Enhancements

- Visual query builder
- Advanced data visualization
- Real-time collaboration
- API integration capabilities
- Advanced analytics dashboard
- Custom function support
- Multi-database connections

## Contributing

When contributing to the Database Chat feature:

1. Follow existing code patterns
2. Add comprehensive tests
3. Update documentation
4. Consider security implications
5. Test with various data types and sizes

## License

This feature is part of the AI Agent Platform and follows the same licensing terms.
