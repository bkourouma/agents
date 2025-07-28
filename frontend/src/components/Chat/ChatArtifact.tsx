import React, { useState } from 'react';
import {
  ChevronUpIcon,
  ChevronDownIcon,
  ArrowsPointingOutIcon,
  XMarkIcon,
  DocumentDuplicateIcon
} from '@heroicons/react/24/outline';
import DatabaseTableArtifact from './DatabaseTableArtifact';
import CodeArtifact from './CodeArtifact';
import JsonArtifact from './JsonArtifact';
import FormattedTextArtifact from './FormattedTextArtifact';

type ArtifactType =
  | 'database-table'
  | 'data-visualization'
  | 'code-snippet'
  | 'formatted-text'
  | 'json-data'
  | 'report';

interface ArtifactData {
  id: string;
  type: ArtifactType;
  title: string;
  content: any;
  metadata?: Record<string, any>;
}

interface ArtifactProps {
  artifact: ArtifactData;
  onClose?: () => void;
  isExpandable?: boolean;
  onRerun?: (sql: string) => void;
}

const ChatArtifact: React.FC<ArtifactProps> = ({
  artifact,
  onClose,
  isExpandable = true,
  onRerun
}) => {
  const [isExpanded, setIsExpanded] = useState(true);
  const [isFullscreen, setIsFullscreen] = useState(false);

  const handleToggleExpand = () => {
    setIsExpanded(!isExpanded);
  };

  const handleFullscreen = () => {
    setIsFullscreen(!isFullscreen);
  };

  const handleCopyContent = async () => {
    try {
      let textToCopy = '';
      
      if (artifact.type === 'database-table' && artifact.content.data) {
        // Convert table data to CSV format
        const headers = artifact.content.columns.join(',');
        const rows = artifact.content.data.map((row: any) => 
          artifact.content.columns.map((col: string) => 
            JSON.stringify(row[col] || '')
          ).join(',')
        );
        textToCopy = [headers, ...rows].join('\n');
      } else if (artifact.type === 'json-data') {
        textToCopy = JSON.stringify(artifact.content, null, 2);
      } else if (artifact.type === 'code-snippet') {
        textToCopy = artifact.content;
      } else {
        textToCopy = typeof artifact.content === 'string' 
          ? artifact.content 
          : JSON.stringify(artifact.content);
      }
      
      await navigator.clipboard.writeText(textToCopy);
      // You could add a toast notification here
    } catch (error) {
      console.error('Failed to copy content:', error);
    }
  };

  const renderArtifactContent = () => {
    switch (artifact.type) {
      case 'database-table':
        return (
          <DatabaseTableArtifact
            data={artifact.content.data || []}
            columns={artifact.content.columns || []}
            sql={artifact.content.sql}
            executionTime={artifact.content.execution_time_ms}
            rowCount={artifact.content.row_count}
            onRerun={onRerun}
            title={artifact.title}
          />
        );
      
      case 'code-snippet':
        return (
          <CodeArtifact
            code={artifact.content}
            language={artifact.metadata?.language || 'sql'}
            title={artifact.title}
            onRun={onRerun}
          />
        );
      
      case 'json-data':
        return (
          <JsonArtifact
            data={artifact.content}
            title={artifact.title}
          />
        );
      
      case 'formatted-text':
        return (
          <FormattedTextArtifact
            content={artifact.content}
            title={artifact.title}
          />
        );
      
      default:
        return (
          <div className="p-4 text-gray-600">
            <p>Unsupported artifact type: {artifact.type}</p>
            <pre className="mt-2 text-sm bg-gray-100 p-2 rounded">
              {JSON.stringify(artifact.content, null, 2)}
            </pre>
          </div>
        );
    }
  };

  const containerClasses = isFullscreen
    ? "fixed inset-0 z-50 bg-white flex flex-col"
    : "bg-white max-w-full overflow-hidden h-full flex flex-col";

  return (
    <div className={containerClasses}>
      {/* Artifact Header - Only show if not in side panel */}
      {isExpandable && (
        <div className="bg-gray-50 px-4 py-3 border-b border-gray-200 flex items-center justify-between flex-shrink-0">
          <div className="flex items-center space-x-2">
            <button
              onClick={handleToggleExpand}
              className="text-gray-500 hover:text-gray-700 p-1"
              title={isExpanded ? "Collapse" : "Expand"}
            >
              {isExpanded ? (
                <ChevronUpIcon className="h-4 w-4" />
              ) : (
                <ChevronDownIcon className="h-4 w-4" />
              )}
            </button>

            <h3 className="text-sm font-medium text-gray-900">
              {artifact.title}
            </h3>

            {artifact.metadata?.tool_used && (
              <span className="inline-flex items-center px-2 py-0.5 rounded text-xs font-medium bg-blue-100 text-blue-800">
                {artifact.metadata.tool_used}
              </span>
            )}
          </div>

          <div className="flex items-center space-x-2">
            <button
              onClick={handleCopyContent}
              className="text-gray-500 hover:text-gray-700 p-1"
              title="Copy content"
            >
              <DocumentDuplicateIcon className="h-4 w-4" />
            </button>

            <button
              onClick={handleFullscreen}
              className="text-gray-500 hover:text-gray-700 p-1"
              title={isFullscreen ? "Exit fullscreen" : "Fullscreen"}
            >
              <ArrowsPointingOutIcon className="h-4 w-4" />
            </button>

            {onClose && (
              <button
                onClick={onClose}
                className="text-gray-500 hover:text-gray-700 p-1"
                title="Close"
              >
                <XMarkIcon className="h-4 w-4" />
              </button>
            )}
          </div>
        </div>
      )}

      {/* Artifact Content */}
      {isExpanded && (
        <div className={`artifact-content ${isFullscreen ? 'flex-1 overflow-auto' : isExpandable ? 'max-h-96 overflow-auto' : 'flex-1 overflow-auto'}`}>
          {renderArtifactContent()}
        </div>
      )}
    </div>
  );
};

export default ChatArtifact;
