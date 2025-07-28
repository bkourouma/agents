import React, { useState } from 'react';
import {
  ChevronRightIcon,
  ChevronDownIcon,
  DocumentDuplicateIcon,
  CheckIcon
} from '@heroicons/react/24/outline';

interface JsonArtifactProps {
  data: any;
  title?: string;
  maxHeight?: number;
}

interface JsonNodeProps {
  data: any;
  keyName?: string;
  level?: number;
  isLast?: boolean;
}

const JsonNode: React.FC<JsonNodeProps> = ({ data, keyName, level = 0, isLast = true }) => {
  const [isExpanded, setIsExpanded] = useState(level < 2); // Auto-expand first 2 levels

  const getValueType = (value: any): string => {
    if (value === null) return 'null';
    if (Array.isArray(value)) return 'array';
    return typeof value;
  };

  const getValueColor = (value: any): string => {
    const type = getValueType(value);
    switch (type) {
      case 'string': return 'text-green-600';
      case 'number': return 'text-blue-600';
      case 'boolean': return 'text-purple-600';
      case 'null': return 'text-gray-500';
      default: return 'text-gray-900';
    }
  };

  const renderValue = (value: any) => {
    const type = getValueType(value);
    
    if (type === 'string') {
      return <span className={getValueColor(value)}>"{value}"</span>;
    }
    
    if (type === 'null') {
      return <span className={getValueColor(value)}>null</span>;
    }
    
    if (type === 'boolean') {
      return <span className={getValueColor(value)}>{String(value)}</span>;
    }
    
    if (type === 'number') {
      return <span className={getValueColor(value)}>{value}</span>;
    }
    
    return <span className={getValueColor(value)}>{String(value)}</span>;
  };

  const isExpandable = (value: any) => {
    return typeof value === 'object' && value !== null && Object.keys(value).length > 0;
  };

  const getPreview = (value: any) => {
    if (Array.isArray(value)) {
      return `Array(${value.length})`;
    }
    if (typeof value === 'object' && value !== null) {
      const keys = Object.keys(value);
      return `Object(${keys.length})`;
    }
    return '';
  };

  const indent = level * 20;

  if (!isExpandable(data)) {
    return (
      <div style={{ marginLeft: `${indent}px` }} className="py-0.5">
        {keyName && (
          <span className="text-blue-800 font-medium">"{keyName}": </span>
        )}
        {renderValue(data)}
        {!isLast && <span className="text-gray-600">,</span>}
      </div>
    );
  }

  const entries = Array.isArray(data) 
    ? data.map((item, index) => [index, item])
    : Object.entries(data);

  return (
    <div style={{ marginLeft: `${indent}px` }}>
      <div className="py-0.5 flex items-center">
        <button
          onClick={() => setIsExpanded(!isExpanded)}
          className="flex items-center text-gray-600 hover:text-gray-800 mr-1"
        >
          {isExpanded ? (
            <ChevronDownIcon className="h-3 w-3" />
          ) : (
            <ChevronRightIcon className="h-3 w-3" />
          )}
        </button>
        
        {keyName && (
          <span className="text-blue-800 font-medium">"{keyName}": </span>
        )}
        
        <span className="text-gray-600">
          {Array.isArray(data) ? '[' : '{'}
        </span>
        
        {!isExpanded && (
          <span className="text-gray-500 ml-1">
            {getPreview(data)}
          </span>
        )}
        
        {!isExpanded && (
          <span className="text-gray-600 ml-1">
            {Array.isArray(data) ? ']' : '}'}
          </span>
        )}
        
        {!isExpanded && !isLast && <span className="text-gray-600">,</span>}
      </div>

      {isExpanded && (
        <>
          {entries.map(([key, value], index) => (
            <JsonNode
              key={key}
              data={value}
              keyName={Array.isArray(data) ? undefined : String(key)}
              level={level + 1}
              isLast={index === entries.length - 1}
            />
          ))}
          <div style={{ marginLeft: `${indent}px` }} className="py-0.5">
            <span className="text-gray-600">
              {Array.isArray(data) ? ']' : '}'}
            </span>
            {!isLast && <span className="text-gray-600">,</span>}
          </div>
        </>
      )}
    </div>
  );
};

const JsonArtifact: React.FC<JsonArtifactProps> = ({
  data,
  title,
  maxHeight = 400
}) => {
  const [copied, setCopied] = useState(false);
  const [viewMode, setViewMode] = useState<'tree' | 'raw'>('tree');

  const handleCopy = async () => {
    try {
      const jsonString = JSON.stringify(data, null, 2);
      await navigator.clipboard.writeText(jsonString);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    } catch (error) {
      console.error('Failed to copy JSON:', error);
    }
  };

  const getDataStats = () => {
    const jsonString = JSON.stringify(data);
    const size = new Blob([jsonString]).size;
    
    let itemCount = 0;
    if (Array.isArray(data)) {
      itemCount = data.length;
    } else if (typeof data === 'object' && data !== null) {
      itemCount = Object.keys(data).length;
    }

    return { size, itemCount };
  };

  const { size, itemCount } = getDataStats();

  return (
    <div className="p-4">
      {/* Header */}
      <div className="flex items-center justify-between mb-3">
        <div className="flex items-center space-x-2">
          {title && (
            <h4 className="text-sm font-medium text-gray-900">{title}</h4>
          )}
          <span className="inline-flex items-center px-2 py-0.5 rounded text-xs font-medium bg-yellow-100 text-yellow-800">
            JSON
          </span>
        </div>

        <div className="flex items-center space-x-2">
          <div className="flex rounded-md shadow-sm">
            <button
              onClick={() => setViewMode('tree')}
              className={`px-3 py-1 text-xs font-medium rounded-l-md border ${
                viewMode === 'tree'
                  ? 'bg-blue-600 text-white border-blue-600'
                  : 'bg-white text-gray-700 border-gray-300 hover:bg-gray-50'
              }`}
            >
              Tree
            </button>
            <button
              onClick={() => setViewMode('raw')}
              className={`px-3 py-1 text-xs font-medium rounded-r-md border-t border-r border-b ${
                viewMode === 'raw'
                  ? 'bg-blue-600 text-white border-blue-600'
                  : 'bg-white text-gray-700 border-gray-300 hover:bg-gray-50'
              }`}
            >
              Raw
            </button>
          </div>

          <button
            onClick={handleCopy}
            className="inline-flex items-center px-2 py-1 border border-gray-300 rounded text-xs font-medium text-gray-700 bg-white hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-blue-500"
            title="Copy JSON"
          >
            {copied ? (
              <>
                <CheckIcon className="h-3 w-3 mr-1 text-green-600" />
                Copied
              </>
            ) : (
              <>
                <DocumentDuplicateIcon className="h-3 w-3 mr-1" />
                Copy
              </>
            )}
          </button>
        </div>
      </div>

      {/* Content */}
      <div 
        className="bg-gray-50 rounded-lg border overflow-auto font-mono text-sm"
        style={{ maxHeight: `${maxHeight}px` }}
      >
        <div className="p-4">
          {viewMode === 'tree' ? (
            <JsonNode data={data} />
          ) : (
            <pre className="whitespace-pre-wrap text-gray-900">
              {JSON.stringify(data, null, 2)}
            </pre>
          )}
        </div>
      </div>

      {/* Stats */}
      <div className="mt-2 text-xs text-gray-500 flex items-center space-x-4">
        <span>{itemCount} {Array.isArray(data) ? 'items' : 'properties'}</span>
        <span>{(size / 1024).toFixed(1)} KB</span>
        <span>{viewMode === 'tree' ? 'Tree view' : 'Raw JSON'}</span>
      </div>
    </div>
  );
};

export default JsonArtifact;
