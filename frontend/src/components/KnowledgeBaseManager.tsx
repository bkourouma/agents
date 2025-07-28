import React, { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { toast } from 'react-hot-toast';
import { 
  DocumentTextIcon, 
  PlusIcon, 
  MagnifyingGlassIcon,
  TrashIcon,
  CloudArrowUpIcon
} from '@heroicons/react/24/outline';

interface KnowledgeBaseDocument {
  id: number;
  agent_id: number;
  title: string;
  content: string;
  content_type: string;
  file_path?: string;
  content_hash: string;
  metadata?: any;
  is_active: boolean;
  created_at: string;
  updated_at?: string;
}

interface KnowledgeBaseManagerProps {
  agentId: number;
  isOpen: boolean;
  onClose: () => void;
}

const KnowledgeBaseManager: React.FC<KnowledgeBaseManagerProps> = ({
  agentId,
  isOpen,
  onClose
}) => {
  const [searchQuery, setSearchQuery] = useState('');
  const [showAddForm, setShowAddForm] = useState(false);
  const [newDocument, setNewDocument] = useState({
    title: '',
    content: ''
  });
  const [uploadFile, setUploadFile] = useState<File | null>(null);

  const queryClient = useQueryClient();

  // API Configuration
  const API_BASE_URL = 'http://localhost:3006';

  // Fetch documents
  const { data: documents, isLoading } = useQuery({
    queryKey: ['knowledge-base', agentId],
    queryFn: async () => {
      const response = await fetch(`${API_BASE_URL}/api/v1/agents/${agentId}/knowledge-base/documents`, {
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('auth_token')}`
        }
      });
      if (!response.ok) throw new Error('Failed to fetch documents');
      return response.json();
    },
    enabled: isOpen
  });

  // Add document mutation
  const addDocumentMutation = useMutation({
    mutationFn: async (document: { title: string; content: string }) => {
      const response = await fetch(`${API_BASE_URL}/api/v1/agents/${agentId}/knowledge-base/documents`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${localStorage.getItem('auth_token')}`
        },
        body: JSON.stringify(document)
      });
      if (!response.ok) throw new Error('Failed to add document');
      return response.json();
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['knowledge-base', agentId] });
      setNewDocument({ title: '', content: '' });
      setShowAddForm(false);
      toast.success('Document added successfully');
    },
    onError: (error: any) => {
      toast.error(error.message || 'Failed to add document');
    }
  });

  // Upload file mutation
  const uploadFileMutation = useMutation({
    mutationFn: async (file: File) => {
      const formData = new FormData();
      formData.append('file', file);
      formData.append('title', file.name);

      const response = await fetch(`${API_BASE_URL}/api/v1/agents/${agentId}/knowledge-base/documents/upload`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('auth_token')}`
        },
        body: formData
      });
      if (!response.ok) throw new Error('Failed to upload file');
      return response.json();
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['knowledge-base', agentId] });
      setUploadFile(null);
      toast.success('File uploaded successfully');
    },
    onError: (error: any) => {
      toast.error(error.message || 'Failed to upload file');
    }
  });

  // Delete document mutation
  const deleteDocumentMutation = useMutation({
    mutationFn: async (documentId: number) => {
      const response = await fetch(`${API_BASE_URL}/api/v1/agents/${agentId}/knowledge-base/documents/${documentId}`, {
        method: 'DELETE',
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('auth_token')}`
        }
      });
      if (!response.ok) throw new Error('Failed to delete document');
      return response.json();
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['knowledge-base', agentId] });
      toast.success('Document deleted successfully');
    },
    onError: (error: any) => {
      toast.error(error.message || 'Failed to delete document');
    }
  });

  const handleAddDocument = () => {
    if (!newDocument.title.trim() || !newDocument.content.trim()) {
      toast.error('Please fill in both title and content');
      return;
    }
    addDocumentMutation.mutate(newDocument);
  };

  const handleFileUpload = () => {
    if (!uploadFile) {
      toast.error('Please select a file');
      return;
    }
    uploadFileMutation.mutate(uploadFile);
  };

  const filteredDocuments = documents?.filter((doc: KnowledgeBaseDocument) =>
    doc.title.toLowerCase().includes(searchQuery.toLowerCase()) ||
    doc.content.toLowerCase().includes(searchQuery.toLowerCase())
  ) || [];

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <div className="bg-white rounded-lg shadow-xl w-full max-w-4xl h-5/6 flex flex-col">
        {/* Header */}
        <div className="flex items-center justify-between p-6 border-b">
          <h2 className="text-xl font-semibold text-gray-900">Gestionnaire de base de connaissances</h2>
          <button
            onClick={onClose}
            className="text-gray-400 hover:text-gray-600"
          >
            ✕
          </button>
        </div>

        {/* Search and Actions */}
        <div className="p-6 border-b space-y-4">
          <div className="flex items-center space-x-4">
            <div className="flex-1 relative">
              <MagnifyingGlassIcon className="absolute left-3 top-1/2 transform -translate-y-1/2 h-5 w-5 text-gray-400" />
              <input
                type="text"
                placeholder="Rechercher des documents..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                className="w-full pl-10 pr-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              />
            </div>
            <button
              onClick={() => setShowAddForm(!showAddForm)}
              className="flex items-center space-x-2 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700"
            >
              <PlusIcon className="h-5 w-5" />
              <span>Ajouter un document</span>
            </button>
          </div>

          {/* Add Document Form */}
          {showAddForm && (
            <div className="bg-gray-50 p-4 rounded-lg space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Titre</label>
                <input
                  type="text"
                  value={newDocument.title}
                  onChange={(e) => setNewDocument({ ...newDocument, title: e.target.value })}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                  placeholder="Titre du document..."
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Content</label>
                <textarea
                  value={newDocument.content}
                  onChange={(e) => setNewDocument({ ...newDocument, content: e.target.value })}
                  rows={4}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                  placeholder="Document content..."
                />
              </div>
              <div className="flex items-center space-x-2">
                <button
                  onClick={handleAddDocument}
                  disabled={addDocumentMutation.isPending}
                  className="px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 disabled:opacity-50"
                >
                  {addDocumentMutation.isPending ? 'Adding...' : 'Add Document'}
                </button>
                <button
                  onClick={() => setShowAddForm(false)}
                  className="px-4 py-2 bg-gray-300 text-gray-700 rounded-lg hover:bg-gray-400"
                >
                  Cancel
                </button>
              </div>

              {/* File Upload Section */}
              <div className="border-t pt-4">
                <label className="block text-sm font-medium text-gray-700 mb-2">Or upload a file</label>
                <div className="flex items-center space-x-2">
                  <input
                    type="file"
                    accept=".txt,.md,.csv,.pdf"
                    onChange={(e) => setUploadFile(e.target.files?.[0] || null)}
                    className="flex-1 text-sm text-gray-500 file:mr-4 file:py-2 file:px-4 file:rounded-lg file:border-0 file:text-sm file:font-semibold file:bg-blue-50 file:text-blue-700 hover:file:bg-blue-100"
                  />
                  <button
                    onClick={handleFileUpload}
                    disabled={!uploadFile || uploadFileMutation.isPending}
                    className="flex items-center space-x-2 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50"
                  >
                    <CloudArrowUpIcon className="h-5 w-5" />
                    <span>{uploadFileMutation.isPending ? 'Uploading...' : 'Upload'}</span>
                  </button>
                </div>
                <p className="text-xs text-gray-500 mt-1">
                  Supported formats: Text (.txt), Markdown (.md), CSV (.csv), PDF (.pdf)
                </p>
              </div>
            </div>
          )}
        </div>

        {/* Documents List */}
        <div className="flex-1 overflow-y-auto p-6">
          {isLoading ? (
            <div className="flex items-center justify-center h-32">
              <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
            </div>
          ) : filteredDocuments.length === 0 ? (
            <div className="text-center py-12">
              <DocumentTextIcon className="mx-auto h-12 w-12 text-gray-400" />
              <h3 className="mt-2 text-sm font-medium text-gray-900">No documents</h3>
              <p className="mt-1 text-sm text-gray-500">
                {searchQuery ? 'No documents match your search.' : 'Get started by adding your first document.'}
              </p>
            </div>
          ) : (
            <div className="space-y-4">
              {filteredDocuments.map((doc: KnowledgeBaseDocument) => (
                <div key={doc.id} className="bg-white border border-gray-200 rounded-lg p-4 hover:shadow-md transition-shadow">
                  <div className="flex items-start justify-between">
                    <div className="flex-1">
                      <h3 className="text-lg font-medium text-gray-900">{doc.title}</h3>
                      <p className="text-sm text-gray-500 mt-1">
                        {doc.content_type} • {new Date(doc.created_at).toLocaleDateString()}
                      </p>
                      <p className="text-gray-700 mt-2 line-clamp-3">
                        {doc.content.substring(0, 200)}
                        {doc.content.length > 200 && '...'}
                      </p>
                    </div>
                    <button
                      onClick={() => deleteDocumentMutation.mutate(doc.id)}
                      disabled={deleteDocumentMutation.isPending}
                      className="ml-4 p-2 text-red-600 hover:bg-red-50 rounded-lg disabled:opacity-50"
                    >
                      <TrashIcon className="h-5 w-5" />
                    </button>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default KnowledgeBaseManager;
