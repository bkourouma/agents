import React, { useState } from 'react';
import {
  DocumentDuplicateIcon,
  PlayIcon,
  CheckIcon
} from '@heroicons/react/24/outline';

interface CodeArtifactProps {
  code: string;
  language: string;
  title?: string;
  onCopy?: () => void;
  onRun?: (code: string) => void;
}

const CodeArtifact: React.FC<CodeArtifactProps> = ({
  code,
  language,
  title,
  onCopy,
  onRun
}) => {
  const [copied, setCopied] = useState(false);

  const handleCopy = async () => {
    try {
      await navigator.clipboard.writeText(code);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
      onCopy?.();
    } catch (error) {
      console.error('Failed to copy code:', error);
    }
  };

  const handleRun = () => {
    if (onRun) {
      onRun(code);
    }
  };

  // Simple syntax highlighting for SQL
  const highlightSql = (sqlCode: string) => {
    const keywords = [
      'SELECT', 'FROM', 'WHERE', 'JOIN', 'INNER', 'LEFT', 'RIGHT', 'OUTER',
      'ON', 'GROUP', 'BY', 'ORDER', 'HAVING', 'LIMIT', 'OFFSET', 'INSERT',
      'UPDATE', 'DELETE', 'CREATE', 'TABLE', 'ALTER', 'DROP', 'INDEX',
      'PRIMARY', 'KEY', 'FOREIGN', 'REFERENCES', 'NOT', 'NULL', 'UNIQUE',
      'DEFAULT', 'AUTO_INCREMENT', 'COUNT', 'SUM', 'AVG', 'MAX', 'MIN',
      'DISTINCT', 'AS', 'AND', 'OR', 'IN', 'LIKE', 'BETWEEN', 'IS'
    ];

    let highlighted = sqlCode;

    // Highlight keywords
    keywords.forEach(keyword => {
      const regex = new RegExp(`\\b${keyword}\\b`, 'gi');
      highlighted = highlighted.replace(regex, `<span class="text-blue-400 font-semibold">${keyword}</span>`);
    });

    // Highlight strings
    highlighted = highlighted.replace(/'([^']*)'/g, '<span class="text-green-400">\'$1\'</span>');
    highlighted = highlighted.replace(/"([^"]*)"/g, '<span class="text-green-400">"$1"</span>');

    // Highlight numbers
    highlighted = highlighted.replace(/\b\d+\.?\d*\b/g, '<span class="text-yellow-400">$&</span>');

    // Highlight comments
    highlighted = highlighted.replace(/--.*$/gm, '<span class="text-gray-500 italic">$&</span>');
    highlighted = highlighted.replace(/\/\*[\s\S]*?\*\//g, '<span class="text-gray-500 italic">$&</span>');

    return highlighted;
  };

  const getLanguageLabel = (lang: string) => {
    const labels: Record<string, string> = {
      sql: 'SQL',
      javascript: 'JavaScript',
      typescript: 'TypeScript',
      python: 'Python',
      json: 'JSON',
      html: 'HTML',
      css: 'CSS'
    };
    return labels[lang.toLowerCase()] || lang.toUpperCase();
  };

  const renderHighlightedCode = () => {
    if (language.toLowerCase() === 'sql') {
      return (
        <pre 
          className="whitespace-pre-wrap text-sm leading-relaxed"
          dangerouslySetInnerHTML={{ __html: highlightSql(code) }}
        />
      );
    }

    // For other languages, just display as plain text for now
    // In a real implementation, you might want to use a library like Prism.js or highlight.js
    return (
      <pre className="whitespace-pre-wrap text-sm leading-relaxed text-gray-100">
        {code}
      </pre>
    );
  };

  return (
    <div className="p-4">
      {/* Header */}
      <div className="flex items-center justify-between mb-3">
        <div className="flex items-center space-x-2">
          {title && (
            <h4 className="text-sm font-medium text-gray-900">{title}</h4>
          )}
          <span className="inline-flex items-center px-2 py-0.5 rounded text-xs font-medium bg-gray-100 text-gray-800">
            {getLanguageLabel(language)}
          </span>
        </div>

        <div className="flex items-center space-x-2">
          <button
            onClick={handleCopy}
            className="inline-flex items-center px-2 py-1 border border-gray-300 rounded text-xs font-medium text-gray-700 bg-white hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-blue-500"
            title="Copy code"
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

          {onRun && language.toLowerCase() === 'sql' && (
            <button
              onClick={handleRun}
              className="inline-flex items-center px-2 py-1 border border-transparent rounded text-xs font-medium text-white bg-blue-600 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-500"
              title="Run query"
            >
              <PlayIcon className="h-3 w-3 mr-1" />
              Run
            </button>
          )}
        </div>
      </div>

      {/* Code Block */}
      <div className="bg-gray-900 rounded-lg overflow-hidden">
        <div className="p-4 overflow-x-auto">
          {renderHighlightedCode()}
        </div>
      </div>

      {/* Code Stats */}
      <div className="mt-2 text-xs text-gray-500">
        {code.split('\n').length} lines • {code.length} characters
      </div>
    </div>
  );
};

export default CodeArtifact;
