import React, { useState } from 'react';
import {
  DocumentDuplicateIcon,
  CheckIcon,
  MagnifyingGlassIcon,
  DocumentTextIcon
} from '@heroicons/react/24/outline';
import ReactMarkdown from 'react-markdown';

interface FormattedTextArtifactProps {
  content: string;
  title?: string;
  maxHeight?: number;
  enableMarkdown?: boolean;
}

const FormattedTextArtifact: React.FC<FormattedTextArtifactProps> = ({
  content,
  title,
  maxHeight = 400,
  enableMarkdown = true
}) => {
  const [copied, setCopied] = useState(false);
  const [searchTerm, setSearchTerm] = useState('');
  const [viewMode, setViewMode] = useState<'formatted' | 'raw'>('formatted');

  const handleCopy = async () => {
    try {
      await navigator.clipboard.writeText(content);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    } catch (error) {
      console.error('Failed to copy content:', error);
    }
  };

  const highlightSearchTerm = (text: string, term: string) => {
    if (!term) return text;
    
    const regex = new RegExp(`(${term})`, 'gi');
    return text.replace(regex, '<mark class="bg-yellow-200">$1</mark>');
  };

  const getContentStats = () => {
    const lines = content.split('\n').length;
    const words = content.split(/\s+/).filter(word => word.length > 0).length;
    const characters = content.length;
    
    return { lines, words, characters };
  };

  const { lines, words, characters } = getContentStats();

  const isMarkdownContent = () => {
    // Simple heuristics to detect markdown
    const markdownPatterns = [
      /^#{1,6}\s/m,           // Headers
      /\*\*.*\*\*/,           // Bold
      /\*.*\*/,               // Italic
      /\[.*\]\(.*\)/,         // Links
      /^[-*+]\s/m,            // Lists
      /```[\s\S]*```/,        // Code blocks
      /`.*`/,                 // Inline code
      /^\|.*\|/m              // Tables
    ];
    
    return markdownPatterns.some(pattern => pattern.test(content));
  };

  const shouldShowMarkdown = enableMarkdown && isMarkdownContent();

  const renderContent = () => {
    let displayContent = content;
    
    if (searchTerm) {
      displayContent = highlightSearchTerm(content, searchTerm);
    }

    if (viewMode === 'formatted' && shouldShowMarkdown) {
      return (
        <div className="prose prose-sm max-w-none">
          <ReactMarkdown>{content}</ReactMarkdown>
        </div>
      );
    }

    return (
      <pre 
        className="whitespace-pre-wrap text-sm leading-relaxed text-gray-900 font-sans"
        dangerouslySetInnerHTML={searchTerm ? { __html: displayContent } : undefined}
      >
        {!searchTerm && displayContent}
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
          <span className="inline-flex items-center px-2 py-0.5 rounded text-xs font-medium bg-green-100 text-green-800">
            <DocumentTextIcon className="h-3 w-3 mr-1" />
            Text
          </span>
          {shouldShowMarkdown && (
            <span className="inline-flex items-center px-2 py-0.5 rounded text-xs font-medium bg-blue-100 text-blue-800">
              Markdown
            </span>
          )}
        </div>

        <div className="flex items-center space-x-2">
          {shouldShowMarkdown && (
            <div className="flex rounded-md shadow-sm">
              <button
                onClick={() => setViewMode('formatted')}
                className={`px-3 py-1 text-xs font-medium rounded-l-md border ${
                  viewMode === 'formatted'
                    ? 'bg-blue-600 text-white border-blue-600'
                    : 'bg-white text-gray-700 border-gray-300 hover:bg-gray-50'
                }`}
              >
                Formatted
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
          )}

          <button
            onClick={handleCopy}
            className="inline-flex items-center px-2 py-1 border border-gray-300 rounded text-xs font-medium text-gray-700 bg-white hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-blue-500"
            title="Copy content"
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

      {/* Search */}
      {content.length > 500 && (
        <div className="mb-3">
          <div className="relative">
            <MagnifyingGlassIcon className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-gray-400" />
            <input
              type="text"
              placeholder="Search in content..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className="w-full pl-10 pr-4 py-2 border border-gray-300 rounded-md text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
            />
          </div>
        </div>
      )}

      {/* Content */}
      <div 
        className="bg-gray-50 rounded-lg border overflow-auto"
        style={{ maxHeight: `${maxHeight}px` }}
      >
        <div className="p-4">
          {renderContent()}
        </div>
      </div>

      {/* Stats */}
      <div className="mt-2 text-xs text-gray-500 flex items-center space-x-4">
        <span>{lines} lines</span>
        <span>{words} words</span>
        <span>{characters} characters</span>
        {shouldShowMarkdown && (
          <span>{viewMode === 'formatted' ? 'Markdown rendered' : 'Raw markdown'}</span>
        )}
        {searchTerm && (
          <span className="text-blue-600">
            Searching for "{searchTerm}"
          </span>
        )}
      </div>
    </div>
  );
};

export default FormattedTextArtifact;
