import React, { useState, useRef, useEffect } from 'react';
import { Upload, File, CheckCircle, XCircle, AlertCircle, Trash2 } from 'lucide-react';
import toast from 'react-hot-toast';

interface UploadedFile {
  id: number;
  title: string;
  content_type: string;
  created_at: string;
  file_path?: string;
}

interface UploadResponse {
  id: number;
  title: string;
  content_type: string;
  created_at: string;
  file_path?: string;
}

const FileUpload: React.FC = () => {
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [uploading, setUploading] = useState(false);
  const [uploadedFiles, setUploadedFiles] = useState<UploadedFile[]>([]);
  const [loading, setLoading] = useState(false);
  const [agentId, setAgentId] = useState<number>(1); // Default to agent 1
  const [customTitle, setCustomTitle] = useState<string>('');
  const fileInputRef = useRef<HTMLInputElement>(null);

  // API Configuration - Use relative URLs to leverage Vite proxy
  const API_BASE_URL = '';
  const getAuthToken = () => localStorage.getItem('auth_token');

  // Read agent ID from URL parameters
  useEffect(() => {
    const urlParams = new URLSearchParams(window.location.search);
    const agentParam = urlParams.get('agent');
    if (agentParam) {
      const agentIdFromUrl = parseInt(agentParam, 10);
      if (!isNaN(agentIdFromUrl)) {
        setAgentId(agentIdFromUrl);
      }
    }
  }, []);

  // Login function for testing
  const handleLogin = async () => {
    try {
      const formData = new FormData();
      formData.append('username', 'alice');
      formData.append('password', 'password123');

      const response = await fetch(`${API_BASE_URL}/api/v1/auth/login`, {
        method: 'POST',
        body: formData
      });

      if (response.ok) {
        const data = await response.json();
        localStorage.setItem('auth_token', data.access_token);
        toast.success('Connexion réussie !');
        loadUploadedFiles();
      } else {
        toast.error('Échec de la connexion');
      }
    } catch (error) {
      toast.error('Erreur de connexion');
      console.error('Login error:', error);
    }
  };

  // Load uploaded files
  const loadUploadedFiles = async () => {
    const token = getAuthToken();
    if (!token) {
      toast.error('Veuillez vous connecter d\'abord');
      return;
    }

    setLoading(true);
    try {
      const response = await fetch(`${API_BASE_URL}/api/v1/agents/${agentId}/knowledge-base/documents`, {
        headers: {
          'Authorization': `Bearer ${token}`
        }
      });

      if (response.ok) {
        const files = await response.json();
        setUploadedFiles(files);
      } else if (response.status === 401) {
        toast.error('Authentification expirée. Veuillez vous reconnecter.');
        localStorage.removeItem('auth_token');
      } else {
        toast.error('Échec du chargement des fichiers');
      }
    } catch (error) {
      toast.error('Erreur lors du chargement des fichiers');
      console.error('Load files error:', error);
    } finally {
      setLoading(false);
    }
  };

  // Handle file selection
  const handleFileSelect = (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (file) {
      setSelectedFile(file);
      setCustomTitle(file.name);
    }
  };

  // Handle file upload
  const handleUpload = async () => {
    if (!selectedFile) {
      toast.error('Veuillez d\'abord sélectionner un fichier');
      return;
    }

    const token = getAuthToken();
    if (!token) {
      toast.error('Veuillez vous connecter d\'abord');
      return;
    }

    setUploading(true);
    try {
      const formData = new FormData();
      formData.append('file', selectedFile);
      if (customTitle.trim()) {
        formData.append('title', customTitle.trim());
      }

      console.log('Uploading file:', selectedFile.name, 'to agent:', agentId);

      const response = await fetch(`${API_BASE_URL}/api/v1/agents/${agentId}/knowledge-base/documents/upload`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`
        },
        body: formData
      });

      if (response.ok) {
        const result: UploadResponse = await response.json();
        toast.success('Fichier téléchargé avec succès !');
        setSelectedFile(null);
        setCustomTitle('');
        if (fileInputRef.current) {
          fileInputRef.current.value = '';
        }
        loadUploadedFiles(); // Refresh the list
      } else {
        const errorText = await response.text();
        console.error('Upload failed:', response.status, errorText);
        
        if (response.status === 401) {
          toast.error('Authentication expired. Please login again.');
          localStorage.removeItem('auth_token');
        } else if (response.status === 400) {
          toast.error('Invalid file format. Please upload supported files (.txt, .md, .csv, .pdf)');
        } else {
          toast.error(`Upload failed: ${response.status}`);
        }
      }
    } catch (error) {
      toast.error('Upload error occurred');
      console.error('Upload error:', error);
    } finally {
      setUploading(false);
    }
  };

  // Handle file deletion
  const handleDelete = async (fileId: number) => {
    const token = getAuthToken();
    if (!token) {
      toast.error('Please login first');
      return;
    }

    try {
      const response = await fetch(`${API_BASE_URL}/api/v1/agents/${agentId}/knowledge-base/documents/${fileId}`, {
        method: 'DELETE',
        headers: {
          'Authorization': `Bearer ${token}`
        }
      });

      if (response.ok) {
        toast.success('File deleted successfully!');
        loadUploadedFiles(); // Refresh the list
      } else {
        toast.error('Failed to delete file');
      }
    } catch (error) {
      toast.error('Delete error occurred');
      console.error('Delete error:', error);
    }
  };

  // Check if user is logged in
  const isLoggedIn = !!getAuthToken();

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-900 via-gray-900 to-slate-800 py-8">
      <div className="max-w-6xl mx-auto px-4">
        {/* Header Section */}
        <div className="text-center mb-8">
          <div className="inline-flex items-center justify-center w-16 h-16 bg-gradient-to-br from-blue-500 to-blue-600 rounded-2xl mb-4 shadow-lg shadow-blue-500/25">
            <Upload className="w-8 h-8 text-white" />
          </div>
          <h1 className="text-3xl font-bold text-white mb-2">Gestion des Fichiers</h1>
          <p className="text-slate-400 text-lg">Téléchargez et gérez vos documents de base de connaissances</p>
        </div>

        {/* Login Section */}
        {!isLoggedIn && (
          <div className="mb-8 p-6 bg-gradient-to-r from-amber-500/10 to-orange-500/10 border border-amber-500/20 rounded-2xl backdrop-blur-sm">
            <div className="flex items-center justify-between">
              <div className="flex items-center">
                <div className="w-10 h-10 bg-amber-500/20 rounded-full flex items-center justify-center mr-4">
                  <AlertCircle className="text-amber-400 w-5 h-5" />
                </div>
                <div>
                  <h3 className="text-amber-300 font-semibold">Connexion requise</h3>
                  <p className="text-amber-200/80 text-sm">Veuillez vous connecter pour télécharger des fichiers</p>
                </div>
              </div>
              <button
                onClick={handleLogin}
                className="px-6 py-3 bg-gradient-to-r from-blue-500 to-blue-600 text-white rounded-xl font-medium hover:from-blue-600 hover:to-blue-700 transition-all duration-300 shadow-lg shadow-blue-500/25"
              >
                Se connecter en tant qu'Alice
              </button>
            </div>
          </div>
        )}

        <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
          {/* Upload Section */}
          <div className="bg-slate-800/50 backdrop-blur-sm border border-slate-700/50 rounded-2xl p-6">
            <div className="flex items-center mb-6">
              <div className="w-8 h-8 bg-blue-500/20 rounded-lg flex items-center justify-center mr-3">
                <Upload className="w-4 h-4 text-blue-400" />
              </div>
              <h2 className="text-xl font-bold text-white">Nouveau Fichier</h2>
            </div>

            {/* Agent Selection */}
            <div className="mb-6">
              <label className="block text-sm font-medium text-slate-300 mb-3">
                Sélectionner un agent
                {new URLSearchParams(window.location.search).get('agent') && (
                  <span className="ml-2 text-xs text-blue-400 bg-blue-500/20 px-2 py-1 rounded-lg">
                    Pré-sélectionné depuis la page agent
                  </span>
                )}
              </label>
              <select
                value={agentId}
                onChange={(e) => setAgentId(Number(e.target.value))}
                className="w-full px-4 py-3 bg-slate-700/50 border border-slate-600/50 rounded-xl text-white focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              >
                <option value={1}>Agent 1 - Customer Service</option>
                <option value={2}>Agent 2 - General Assistant</option>
              </select>
            </div>

            {/* File Drop Zone */}
            <div className="mb-6">
              <label className="block text-sm font-medium text-slate-300 mb-3">
                Fichier (Formats supportés: .txt, .md, .csv, .pdf)
              </label>
              <div
                className="relative border-2 border-dashed border-slate-600/50 rounded-xl p-8 text-center hover:border-blue-500/50 transition-all duration-300 cursor-pointer group"
                onClick={() => fileInputRef.current?.click()}
              >
                <input
                  ref={fileInputRef}
                  type="file"
                  onChange={handleFileSelect}
                  accept=".txt,.md,.csv,.pdf,.text"
                  className="hidden"
                />
                <div className="flex flex-col items-center">
                  <div className="w-12 h-12 bg-slate-700/50 rounded-xl flex items-center justify-center mb-4 group-hover:bg-blue-500/20 transition-all duration-300">
                    <Upload className="w-6 h-6 text-slate-400 group-hover:text-blue-400" />
                  </div>
                  <p className="text-slate-300 font-medium mb-1">Cliquez pour sélectionner un fichier</p>
                  <p className="text-slate-500 text-sm">ou glissez-déposez votre document ici</p>
                </div>
              </div>
            </div>

            {/* Custom Title */}
            <div className="mb-6">
              <label className="block text-sm font-medium text-slate-300 mb-3">
                Titre du document (optionnel)
              </label>
              <input
                type="text"
                value={customTitle}
                onChange={(e) => setCustomTitle(e.target.value)}
                placeholder="Entrez un titre personnalisé ou laissez vide pour utiliser le nom du fichier"
                className="w-full px-4 py-3 bg-slate-700/50 border border-slate-600/50 rounded-xl text-white placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              />
            </div>

            {/* Selected File Info */}
            {selectedFile && (
              <div className="mb-6 p-4 bg-gradient-to-r from-blue-500/10 to-blue-600/10 border border-blue-500/20 rounded-xl">
                <div className="flex items-center">
                  <div className="w-8 h-8 bg-blue-500/20 rounded-lg flex items-center justify-center mr-3">
                    <File className="w-4 h-4 text-blue-400" />
                  </div>
                  <div>
                    <p className="text-blue-300 font-medium">{selectedFile.name}</p>
                    <p className="text-blue-400/80 text-sm">{(selectedFile.size / 1024).toFixed(1)} KB</p>
                  </div>
                </div>
              </div>
            )}

            {/* Upload Button */}
            <button
              onClick={handleUpload}
              disabled={!selectedFile || uploading || !isLoggedIn}
              className="w-full px-6 py-4 bg-gradient-to-r from-blue-500 to-blue-600 text-white rounded-xl font-medium hover:from-blue-600 hover:to-blue-700 disabled:from-slate-600 disabled:to-slate-700 disabled:cursor-not-allowed transition-all duration-300 flex items-center justify-center shadow-lg shadow-blue-500/25"
            >
              {uploading ? (
                <>
                  <div className="animate-spin rounded-full h-5 w-5 border-b-2 border-white mr-3"></div>
                  Téléchargement en cours...
                </>
              ) : (
                <>
                  <Upload className="mr-3 w-5 h-5" />
                  Télécharger le fichier
                </>
              )}
            </button>
          </div>

          {/* Uploaded Files Section */}
          <div className="bg-slate-800/50 backdrop-blur-sm border border-slate-700/50 rounded-2xl p-6">
            <div className="flex items-center justify-between mb-6">
              <div className="flex items-center">
                <div className="w-8 h-8 bg-green-500/20 rounded-lg flex items-center justify-center mr-3">
                  <CheckCircle className="w-4 h-4 text-green-400" />
                </div>
                <h2 className="text-xl font-bold text-white">Fichiers Téléchargés</h2>
              </div>
              <button
                onClick={loadUploadedFiles}
                disabled={loading || !isLoggedIn}
                className="px-4 py-2 bg-slate-700/50 text-slate-300 rounded-xl text-sm font-medium hover:bg-green-500 hover:text-white disabled:bg-slate-600 disabled:text-slate-500 transition-all duration-300"
              >
                {loading ? 'Chargement...' : 'Actualiser'}
              </button>
            </div>

            {loading ? (
              <div className="text-center py-12">
                <div className="animate-spin rounded-full h-10 w-10 border-b-2 border-blue-500 mx-auto mb-4"></div>
                <p className="text-slate-400">Chargement des fichiers...</p>
              </div>
            ) : uploadedFiles.length > 0 ? (
              <div className="space-y-3 max-h-96 overflow-y-auto">
                {uploadedFiles.map((file) => (
                  <div key={file.id} className="flex items-center justify-between p-4 bg-slate-700/30 border border-slate-600/30 rounded-xl hover:bg-slate-700/50 transition-all duration-300">
                    <div className="flex items-center flex-1">
                      <div className="w-10 h-10 bg-green-500/20 rounded-lg flex items-center justify-center mr-4">
                        <CheckCircle className="w-5 h-5 text-green-400" />
                      </div>
                      <div className="flex-1">
                        <h3 className="font-medium text-white mb-1">{file.title}</h3>
                        <p className="text-sm text-slate-400">
                          {file.content_type} • Téléchargé le {new Date(file.created_at).toLocaleDateString('fr-FR')}
                        </p>
                      </div>
                    </div>
                    <button
                      onClick={() => handleDelete(file.id)}
                      className="p-2 text-red-400 hover:bg-red-500/20 rounded-lg transition-all duration-300 ml-4"
                      title="Supprimer le fichier"
                    >
                      <Trash2 size={18} />
                    </button>
                  </div>
                ))}
              </div>
            ) : (
              <div className="text-center py-12">
                <div className="w-16 h-16 bg-slate-700/50 rounded-2xl flex items-center justify-center mx-auto mb-4">
                  <File className="w-8 h-8 text-slate-400" />
                </div>
                <p className="text-slate-400 text-lg">Aucun fichier téléchargé</p>
                <p className="text-slate-500 text-sm mt-1">Commencez par télécharger votre premier document</p>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};

export default FileUpload;
