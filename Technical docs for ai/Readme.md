# AI Agent Platform - Project Context

## Project Overview
Building a conversational AI platform where business users create specialized AI agents with tools, and an intelligent orchestrator routes user questions to the appropriate agents.

**Core Concept**: Users chat naturally → Orchestrator analyzes intent → Routes to relevant agent(s) → Agent uses tools → Returns formatted response

## Architecture
```
User Chat Interface
       ↓
   Orchestrator (Intent Analysis & Routing)
       ↓
   Agent Library (Financial, Research, Customer Service, etc.)
       ↓
   Tool Integration Layer (APIs, Databases, File Systems)
```

## Azure Deployment Architecture
```
GitHub Repository
       ↓ (GitHub Actions CI/CD)
Azure Container Registry
       ↓
Azure Web App (Frontend Container)
Azure Web App (Backend Container)
       ↓
Azure Database for PostgreSQL
Azure Cache for Redis
Azure Blob Storage
Azure Key Vault (Secrets)
Azure Application Insights (Monitoring)
```

## Tech Stack
- **Development Environment**: Augment Code
- **Backend**: Python 3.11+ with FastAPI
- **AI Framework**: LangChain + PydanticAI
- **LLM Providers**: OpenAI, Anthropic, multi-provider support
- **Database**: PostgreSQL (Azure Database for PostgreSQL)
- **Caching**: Redis (Azure Cache for Redis)
- **Storage**: Azure Blob Storage for files and documents
- **Integration**: Model Context Protocol (MCP) for tool standardization
- **Frontend**: React 18+ with TypeScript, Vite, Tailwind CSS
- **Container**: Docker for Azure Web Apps
- **Cloud**: Azure (Web Apps, Container Registry, Key Vault)
- **CI/CD**: GitHub Actions with Azure CLI

## Core Components

### 1. Agent Management System
- **Agent Creation**: Visual interface for business users
- **Agent Configuration**: Tools, personality, access permissions
- **Agent Types**: Customer Service, Financial Analysis, Research, etc.
- **Tool Assignment**: Database connections, APIs, file access, web search

### 2. Intelligent Orchestrator
- **Intent Analysis**: Understand user request context and domain
- **Agent Selection**: Route to single agent or coordinate multiple agents
- **Response Synthesis**: Combine multi-agent outputs into coherent response
- **Context Management**: Maintain conversation state and history

### 3. Tool Integration Framework
- **MCP Implementation**: Standardized tool connections
- **Database Connectors**: PostgreSQL, MySQL, SQL Server
- **API Integrations**: REST APIs, OAuth 2.0, API keys
- **File Handling**: PDF, Word, Excel, CSV processing (Azure Blob Storage)
- **Web Tools**: Search, scraping, real-time data

### 4. Business User Interface
- **Agent Builder**: Drag-and-drop agent configuration
- **Tool Library**: Visual tool selection and setup
- **Testing Environment**: Safe agent testing before deployment
- **Analytics Dashboard**: Usage, performance, cost tracking

## Key Features

### Agent Creation
- Template-based setup (Customer Service, Research, Finance)
- Natural language agent personality definition
- Visual tool assignment and configuration
- Permission and access control management

### Orchestrator Intelligence
- Multi-domain intent recognition
- Context-aware agent routing
- Multi-agent coordination for complex requests
- Fallback handling and error management

### Enterprise Security
- Role-based access controls
- Audit logging and compliance
- Data encryption and privacy
- Multi-tenant isolation

## Implementation Steps

### Phase 1: Foundation (Months 1-3)
1. **Core Infrastructure**
   - FastAPI backend with user management
   - Basic agent creation interface
   - Simple LLM integration (OpenAI/Anthropic)
   - Azure Database for PostgreSQL setup
   - Azure Cache for Redis integration
   - Docker containerization for Azure Web Apps

2. **Basic Orchestrator**
   - Simple intent classification
   - Single-agent routing
   - Basic response formatting

3. **Essential Tools**
   - Database query tool
   - File upload/processing tool (Azure Blob Storage)
   - Simple API connector

4. **CI/CD Setup**
   - GitHub Actions workflow
   - Azure Container Registry integration
   - Automated deployment to Azure Web Apps

### Phase 2: Intelligence (Months 4-6)
1. **Advanced Orchestrator**
   - Multi-agent coordination
   - Complex intent analysis
   - Response synthesis from multiple agents

2. **Tool Expansion**
   - MCP protocol implementation
   - Web search and scraping
   - Advanced file processing

3. **User Experience**
   - Visual agent builder
   - Drag-and-drop tool configuration
   - Real-time testing environment

### Phase 3: Enterprise (Months 7-9)
1. **Security & Compliance**
   - Enterprise authentication (Azure AD/SSO)
   - Role-based permissions
   - Audit logging
   - Azure Key Vault integration

2. **Scalability**
   - Multi-tenant architecture
   - Azure Web Apps auto-scaling
   - Performance optimization
   - Cost management and monitoring

3. **Advanced Features**
   - Azure Application Insights monitoring
   - Custom tool development
   - API for external integrations
   - Advanced analytics dashboard

## File Structure
```
/src
  /agents          # Agent management logic
  /orchestrator    # Intent analysis and routing
  /tools           # Tool integration framework
  /api             # FastAPI endpoints
  /ui              # React TypeScript frontend
  /core            # Shared utilities
  /models          # Pydantic models
/docs             # API and user documentation
/tests            # Test suites
/deployment       # Docker configs for Azure Web Apps
/.github
  /workflows       # GitHub Actions CI/CD
```

## Development Guidelines
- Use Pydantic for all data models
- Implement comprehensive error handling
- Follow async/await patterns
- Maintain 90%+ test coverage
- Document all public APIs
- Use type hints throughout
- Docker best practices for Azure Web Apps
- Azure-native services integration
- GitHub Actions for automated testing and deployment

## Context Engineering Notes
- This platform requires sophisticated context management
- Each agent needs isolated context while sharing relevant information
- Orchestrator must maintain conversation state across agent interactions
- Tool outputs must be formatted consistently for agent consumption
- Security contexts must be preserved through the entire request chain