import React, { useState } from 'react';
import ChatArtifact from '../components/Chat/ChatArtifact';

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

const ArtifactTestPage: React.FC = () => {
  const [selectedArtifact, setSelectedArtifact] = useState<string>('database');

  // Sample database artifact
  const databaseArtifact: ArtifactData = {
    id: 'test-db-1',
    type: 'database-table',
    title: 'Sample Transaction Data (5 rows)',
    content: {
      data: [
        { id: 1, amount: 1000.50, date: '2024-01-15', type: 'mobile_money', customer: 'John Doe' },
        { id: 2, amount: 850.25, date: '2024-01-15', type: 'bank_transfer', customer: 'Jane Smith' },
        { id: 3, amount: 750.00, date: '2024-01-14', type: 'mobile_money', customer: 'Bob Johnson' },
        { id: 4, amount: 650.75, date: '2024-01-14', type: 'cash', customer: 'Alice Brown' },
        { id: 5, amount: 500.00, date: '2024-01-13', type: 'mobile_money', customer: 'Charlie Wilson' }
      ],
      columns: ['id', 'amount', 'date', 'type', 'customer'],
      sql: 'SELECT * FROM transactionsmobiles ORDER BY amount DESC LIMIT 5;',
      execution_time_ms: 125,
      row_count: 5
    },
    metadata: {
      tool_used: 'vanna_database',
      execution_time: 125
    }
  };

  // Sample code artifact
  const codeArtifact: ArtifactData = {
    id: 'test-code-1',
    type: 'code-snippet',
    title: 'SQL Query Example',
    content: `-- Get top 10 transactions by amount
SELECT 
    id,
    amount,
    date,
    type,
    customer
FROM transactionsmobiles 
WHERE amount > 500
ORDER BY amount DESC 
LIMIT 10;`,
    metadata: {
      language: 'sql'
    }
  };

  // Sample JSON artifact
  const jsonArtifact: ArtifactData = {
    id: 'test-json-1',
    type: 'json-data',
    title: 'API Response Data',
    content: {
      status: 'success',
      data: {
        transactions: [
          { id: 1, amount: 1000.50, status: 'completed' },
          { id: 2, amount: 850.25, status: 'pending' }
        ],
        summary: {
          total_amount: 1850.75,
          total_count: 2,
          avg_amount: 925.375
        }
      },
      metadata: {
        timestamp: '2024-01-15T10:30:00Z',
        version: '1.0'
      }
    }
  };

  // Sample text artifact
  const textArtifact: ArtifactData = {
    id: 'test-text-1',
    type: 'formatted-text',
    title: 'Transaction Analysis Report',
    content: `# Transaction Analysis Report

## Summary
This report provides an overview of recent transaction activity.

### Key Findings
- **Total Transactions**: 1,250
- **Total Volume**: $125,000
- **Average Transaction**: $100

### Transaction Types
1. **Mobile Money**: 45% of all transactions
2. **Bank Transfer**: 30% of all transactions  
3. **Cash**: 25% of all transactions

### Recommendations
- Increase mobile money promotion
- Optimize bank transfer fees
- Maintain cash handling capacity

*Report generated on January 15, 2024*`
  };

  const artifacts = {
    database: databaseArtifact,
    code: codeArtifact,
    json: jsonArtifact,
    text: textArtifact
  };

  const handleRerun = (sql: string) => {
    console.log('Re-running query:', sql);
    alert(`Would re-run query: ${sql}`);
  };

  return (
    <div className="min-h-screen bg-gray-50 py-8">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="mb-8">
          <h1 className="text-3xl font-bold text-gray-900">Artifact System Test</h1>
          <p className="mt-2 text-gray-600">
            Test the different types of artifacts that can be displayed in the chat interface.
          </p>
        </div>

        {/* Artifact Type Selector */}
        <div className="mb-6">
          <div className="flex space-x-4">
            {Object.keys(artifacts).map((type) => (
              <button
                key={type}
                onClick={() => setSelectedArtifact(type)}
                className={`px-4 py-2 rounded-lg font-medium ${
                  selectedArtifact === type
                    ? 'bg-blue-600 text-white'
                    : 'bg-white text-gray-700 border border-gray-300 hover:bg-gray-50'
                }`}
              >
                {type.charAt(0).toUpperCase() + type.slice(1)} Artifact
              </button>
            ))}
          </div>
        </div>

        {/* Artifact Display */}
        <div className="bg-white rounded-lg shadow-sm p-6">
          <h2 className="text-xl font-semibold text-gray-900 mb-4">
            {selectedArtifact.charAt(0).toUpperCase() + selectedArtifact.slice(1)} Artifact Demo
          </h2>
          
          <div className="border-l-4 border-blue-500 pl-4 mb-6">
            <p className="text-gray-700">
              This demonstrates how {selectedArtifact} artifacts appear in the chat interface.
              {selectedArtifact === 'database' && ' Try sorting columns, searching data, or exporting to CSV.'}
              {selectedArtifact === 'code' && ' The SQL code is syntax highlighted with copy and run functionality.'}
              {selectedArtifact === 'json' && ' Switch between tree view and raw JSON, and explore the collapsible structure.'}
              {selectedArtifact === 'text' && ' Markdown is rendered with search functionality for long content.'}
            </p>
          </div>

          <ChatArtifact
            artifact={artifacts[selectedArtifact as keyof typeof artifacts]}
            onRerun={handleRerun}
            isExpandable={true}
          />
        </div>

        {/* Feature List */}
        <div className="mt-8 bg-white rounded-lg shadow-sm p-6">
          <h3 className="text-lg font-semibold text-gray-900 mb-4">Artifact Features</h3>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <div>
              <h4 className="font-medium text-gray-900 mb-2">Database Table Artifacts</h4>
              <ul className="text-sm text-gray-600 space-y-1">
                <li>• Sortable columns (click headers)</li>
                <li>• Real-time search across all data</li>
                <li>• Pagination for large datasets</li>
                <li>• Export to CSV functionality</li>
                <li>• SQL query display with syntax highlighting</li>
                <li>• Re-run query capability</li>
              </ul>
            </div>
            <div>
              <h4 className="font-medium text-gray-900 mb-2">Code Artifacts</h4>
              <ul className="text-sm text-gray-600 space-y-1">
                <li>• Syntax highlighting for SQL</li>
                <li>• Copy to clipboard functionality</li>
                <li>• Run query directly from code</li>
                <li>• Language detection and labeling</li>
                <li>• Line and character counts</li>
              </ul>
            </div>
            <div>
              <h4 className="font-medium text-gray-900 mb-2">JSON Artifacts</h4>
              <ul className="text-sm text-gray-600 space-y-1">
                <li>• Collapsible tree view</li>
                <li>• Switch between tree and raw JSON</li>
                <li>• Copy entire JSON or specific nodes</li>
                <li>• Object size and item count display</li>
                <li>• Expandable nested structures</li>
              </ul>
            </div>
            <div>
              <h4 className="font-medium text-gray-900 mb-2">Text Artifacts</h4>
              <ul className="text-sm text-gray-600 space-y-1">
                <li>• Markdown rendering support</li>
                <li>• Search functionality for long content</li>
                <li>• Switch between formatted and raw view</li>
                <li>• Word and character counts</li>
                <li>• Copy content functionality</li>
              </ul>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default ArtifactTestPage;
