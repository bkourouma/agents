# Complete Source Code Files for SQL Server Connection (CORRECTED)

## **Backend Files (Python/FastAPI)**

### **1. Core Database Services**
```
📁 src/services/
├── database_providers.py                   # ⭐ MAIN: SQL Server provider implementation
├── vanna_service.py                        # Database query service using Vanna AI
└── tenant_vanna_service.py                 # Multi-tenant database service
```

### **2. API Endpoints**
```
📁 src/api/
├── database_chat.py                        # ⭐ MAIN: Database connection API endpoints
└── __init__.py                             # API module initialization
```

### **3. Data Models & Schemas**
```
📁 src/models/
├── database_chat.py                        # ⭐ MAIN: Database connection data models
├── database_chat_schemas.py               # Pydantic schemas for API
└── __init__.py                             # Models module initialization
```

### **4. Core Configuration**
```
📁 src/core/
├── config.py                              # Main application configuration
├── database.py                            # Database setup and connection
└── auth.py                                # Authentication configuration
```

### **5. Config Files**
```
📁 src/config/
├── knowledge_base.py                       # Knowledge base configuration
└── document_processing.py                  # Document processing configuration
```

### **6. Main Application**
```
📁 Root Directory
├── main.py                                 # ⭐ MAIN: FastAPI application entry point
└── requirements.txt                        # Python dependencies
```

## **Frontend Files (React/TypeScript)**

### **6. Database Setup Components (ACTUAL FILES)**
```
📁 frontend/src/components/DatabaseChat/
├── DatabaseSetupWizard.tsx                 # ⭐ MAIN: Database setup wizard UI
├── ConnectionStringBuilder.tsx             # Connection configuration form
├── TableColumnSelector.tsx                 # Table selection interface
├── VannaTraining.tsx                       # Training setup interface
├── NaturalLanguageQuery.tsx               # Natural language query interface
├── SchemaDesigner.tsx                      # Schema design interface
├── DataManager.tsx                         # Data management interface
└── ColumnEditor.tsx                        # Column editing interface
```

### **7. API Services**
```
📁 frontend/src/lib/
├── api.ts                                  # ⭐ MAIN: Main API client
├── simple-api.ts                          # Simplified API calls
└── insurance-api.ts                        # Insurance-specific APIs
```

### **8. Pages**
```
📁 frontend/src/pages/
├── DatabaseChatPage.tsx                    # ⭐ MAIN: Database chat page
└── DashboardPage.tsx                       # Main dashboard
```

### **9. Types & Interfaces**
```
📁 frontend/src/types/
├── index.ts                                # ⭐ MAIN: Type definitions
└── artifacts.ts                            # Artifact type definitions
```

### **10. Context & State Management**
```
📁 frontend/src/contexts/
├── AuthContext.tsx                         # Authentication context
└── TenantContext.tsx                       # Multi-tenant context
```

## **Configuration Files**

### **11. Environment & Setup**
```
📁 Root Directory
├── .env                                    # Environment variables
├── pyproject.toml                          # Python project configuration
└── pytest.ini                             # Test configuration
```

### **12. Frontend Configuration**
```
📁 frontend/
├── package.json                            # Node.js dependencies
├── tsconfig.json                           # TypeScript configuration
├── vite.config.ts                          # Vite build configuration
└── tailwind.config.js                     # Tailwind CSS configuration
```

## **Test Files**
```
📁 Root Directory
├── test_database_chat.py                   # Database connection tests
├── test_sql_server_connection.py          # SQL Server specific tests
├── check_odbc_drivers.py                  # ODBC driver detection
└── check_sql_server.py                    # SQL Server connectivity check
```

## **Key Files Priority:**

### **🔥 Critical (Must Include):**
1. `src/services/database_providers.py` - Core SQL Server implementation
2. `src/api/database_chat.py` - API endpoints for connections
3. `src/models/database_chat.py` - Data models
4. `main.py` - Application entry point
5. `frontend/src/components/DatabaseChat/DatabaseSetup.tsx` - UI component

### **⚡ Important (Should Include):**
6. `frontend/src/lib/api.ts` - Frontend API client
7. `src/models/database_chat_schemas.py` - API schemas
8. `frontend/src/pages/DatabaseChatPage.tsx` - Main page
9. `frontend/src/types/index.ts` - Type definitions

### **📋 Supporting (Nice to Have):**
10. Configuration files (package.json, requirements.txt)
11. Test files
12. Environment setup files
