/**
 * Artifact types and interfaces for chat interface
 */

export type ArtifactType = 
  | 'database-table'     // Database query results
  | 'data-visualization' // Charts and graphs  
  | 'code-snippet'       // SQL queries and code
  | 'formatted-text'     // Long text content
  | 'json-data'          // Structured JSON
  | 'report'             // Business reports

export interface ArtifactData {
  id: string;
  type: ArtifactType;
  title: string;
  content: any;
  metadata?: Record<string, any>;
}

export interface DatabaseResult {
  data: Array<Record<string, any>>;
  columns: string[];
  sql?: string;
  execution_time_ms?: number;
  row_count?: number;
  success: boolean;
  error?: string;
}

export interface ChatMessage {
  id: string;
  content: string;
  type: 'user' | 'assistant' | 'system';
  timestamp: string;
  agent_name?: string;
  intent_category?: string;
  confidence?: number;
  debug_info?: string;
  metadata?: {
    database_result?: DatabaseResult;
    artifacts?: ArtifactData[];
    tool_used?: string;
    execution_time?: number;
  };
}

export interface ArtifactProps {
  artifact: ArtifactData;
  onClose?: () => void;
  isExpandable?: boolean;
  onRerun?: (sql: string) => void;
}

export interface DatabaseTableArtifactProps {
  data: Array<Record<string, any>>;
  columns: string[];
  sql?: string;
  executionTime?: number;
  rowCount?: number;
  onRerun?: (sql: string) => void;
  title?: string;
}

export interface CodeArtifactProps {
  code: string;
  language: string;
  title?: string;
  onCopy?: () => void;
  onRun?: (code: string) => void;
}

export interface JsonArtifactProps {
  data: any;
  title?: string;
  maxHeight?: number;
}

// Utility functions for artifact detection
export const shouldCreateArtifact = (content: string, metadata?: any): boolean => {
  // Check for database results
  if (metadata?.database_result?.data?.length > 0) {
    return true;
  }
  
  // Check for long content
  if (content.length > 1000) {
    return true;
  }
  
  // Check for structured data patterns
  const hasTablePattern = /\|.*\|.*\|/.test(content);
  const hasJsonPattern = /^\s*[\{\[]/.test(content.trim());
  const hasCodePattern = /```/.test(content);
  
  return hasTablePattern || hasJsonPattern || hasCodePattern;
};

export const detectArtifactType = (content: string, metadata?: any): ArtifactType => {
  if (metadata?.database_result) {
    return 'database-table';
  }
  
  if (metadata?.tool_used === 'vanna_database') {
    return 'database-table';
  }
  
  if (content.includes('```sql') || content.includes('SELECT ') || content.includes('INSERT ')) {
    return 'code-snippet';
  }
  
  if (content.includes('```')) {
    return 'code-snippet';
  }
  
  const trimmed = content.trim();
  if ((trimmed.startsWith('{') && trimmed.endsWith('}')) || 
      (trimmed.startsWith('[') && trimmed.endsWith(']'))) {
    return 'json-data';
  }
  
  if (/\|.*\|.*\|/.test(content)) {
    return 'database-table';
  }
  
  return 'formatted-text';
};

export const createArtifactFromMessage = (message: ChatMessage): ArtifactData | null => {
  if (!shouldCreateArtifact(message.content, message.metadata)) {
    return null;
  }

  const type = detectArtifactType(message.content, message.metadata);

  let content: any = message.content;
  let title = `${type.replace('-', ' ').replace(/\b\w/g, l => l.toUpperCase())}`;

  // Handle database results
  if (message.metadata?.database_result) {
    const dbResult = message.metadata.database_result;
    content = {
      data: dbResult.data,
      columns: dbResult.columns,
      sql: dbResult.sql,
      execution_time_ms: dbResult.execution_time_ms,
      row_count: dbResult.row_count
    };
    title = `Query Results (${dbResult.row_count || 0} rows)`;
  }

  // Handle JSON data
  if (type === 'json-data') {
    try {
      content = JSON.parse(message.content);
      title = 'JSON Data';
    } catch (e) {
      // Keep as text if parsing fails
    }
  }

  return {
    id: `artifact-${message.id}-${Date.now()}`,
    type,
    title,
    content,
    metadata: message.metadata
  };
};

// Re-export types to ensure they're available
export type { ArtifactData, ArtifactType, DatabaseResult, ChatMessage };
