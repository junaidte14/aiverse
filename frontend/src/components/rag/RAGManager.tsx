import {
    AlertCircle,
    Database,
    Plus,
    Trash2,
    Upload,
} from 'lucide-react';
import React, { useEffect, useState } from 'react';
import { apiService } from '../../services/api';
import { useRagStore } from '../../store/useRagStore';
import type { RAGCollection } from '../../types/rag';
import { SourceManager } from './SourceManager';

export const RAGManager: React.FC = () => {
    const [collectionStats, setCollectionStats] = useState<RAGCollection | null>(null);
    const [newCollectionName, setNewCollectionName] = useState('');
    const [loading, setLoading] = useState(false);
    const [uploading, setUploading] = useState(false);
    const [message, setMessage] = useState<{ type: 'success' | 'error'; text: string } | null>(
        null
    );
    const [activeTab, setActiveTab] = useState<'sources' | 'upload'>('sources');
    const { collections, selectedCollection, setSelectedCollection, fetchCollections } = useRagStore();

    useEffect(() => {
        fetchCollections();
    }, []);

    useEffect(() => {
        if (selectedCollection) {
            loadCollectionStats(selectedCollection);
        }
    }, [selectedCollection]);

    const loadCollections = async () => {
        setLoading(true);
        try {
            const data = await apiService.ragListCollections();
            if (data.length > 0 && !selectedCollection) {
                setSelectedCollection(data[0]);
            }
        } catch (error) {
            console.error('Failed to load collections:', error);
        } finally {
            setLoading(false);
        }
    };

    const loadCollectionStats = async (name: string) => {
        try {
            const stats = await apiService.ragGetCollectionStats(name);
            setCollectionStats(stats);
        } catch (error) {
            console.error('Failed to load stats:', error);
            // Initialize empty stats for new collection
            setCollectionStats({
                collection_name: name,
                document_count: 0,
                status: 'empty',
            });
        }
    };

    const handleCreateCollection = async (e: React.FormEvent) => {
        e.preventDefault();
        if (!newCollectionName.trim()) return;

        const collectionName = newCollectionName.trim();

        // Check if collection already exists
        if (collections.includes(collectionName)) {
            setMessage({ type: 'error', text: 'Collection already exists' });
            return;
        }
        await fetchCollections(); // Refresh store list
        setSelectedCollection(newCollectionName);
        setNewCollectionName('');
        setMessage({
            type: 'success',
            text: `Collection "${collectionName}" created. You can now add sources or upload files.`,
        });
    };

    const handleFileUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
        const files = e.target.files;
        if (!files || files.length === 0 || !selectedCollection) return;

        setUploading(true);
        setMessage(null);

        try {
            const file = files[0];
            const result = await apiService.ragIngestFile(file, selectedCollection);

            setMessage({
                type: 'success',
                text: `Successfully ingested ${result.filename}. Created ${result.chunks_created} chunks.`,
            });

            // Reload stats
            await loadCollectionStats(selectedCollection);
        } catch (error: any) {
            setMessage({
                type: 'error',
                text: error.response?.data?.detail || 'Failed to upload file',
            });
        } finally {
            setUploading(false);
            e.target.value = '';
        }
    };

    const handleDeleteCollection = async (name: string) => {
        if (!confirm(`Delete collection "${name}" and all its documents?`)) return;

        try {
            await apiService.ragDeleteCollection(name);
            setMessage({
                type: 'success',
                text: `Collection "${name}" deleted successfully`,
            });

            if (selectedCollection === name) {
                setSelectedCollection(null);
                setCollectionStats(null);
            }

            await loadCollections();
        } catch (error: any) {
            setMessage({
                type: 'error',
                text: error.response?.data?.detail || 'Failed to delete collection',
            });
        }
    };

    return (
        <div className="max-w-6xl mx-auto p-6">
            <div className="mb-6">
                <h1 className="text-2xl font-bold text-gray-900 mb-2">RAG Collections</h1>
                <p className="text-gray-600">
                    Manage your document collections for retrieval-augmented generation
                </p>
            </div>

            {message && (
                <div
                    className={`mb-6 p-4 rounded-lg flex items-start gap-3 ${message.type === 'success'
                        ? 'bg-green-50 text-green-800 border border-green-200'
                        : 'bg-red-50 text-red-800 border border-red-200'
                        }`}
                >
                    <AlertCircle className="w-5 h-5 flex-shrink-0 mt-0.5" />
                    <span>{message.text}</span>
                </div>
            )}

            <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
                {/* Collections Sidebar */}
                <div className="lg:col-span-1 space-y-4">
                    {/* Create Collection */}
                    <div className="card p-4">
                        <h2 className="font-semibold text-gray-900 mb-3">Create Collection</h2>
                        <form onSubmit={handleCreateCollection} className="flex gap-2">
                            <input
                                type="text"
                                value={newCollectionName}
                                onChange={(e) => setNewCollectionName(e.target.value)}
                                placeholder="Collection name..."
                                className="flex-1 px-3 py-2 border border-gray-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-purple-500"
                            />
                            <button
                                type="submit"
                                disabled={!newCollectionName.trim()}
                                className="p-2 bg-purple-600 text-white rounded-lg hover:bg-purple-700 disabled:opacity-50"
                            >
                                <Plus className="w-4 h-4" />
                            </button>
                        </form>
                    </div>

                    {/* Collections List */}
                    <div className="card p-4">
                        <div className="flex items-center justify-between mb-4">
                            <h2 className="font-semibold text-gray-900">Collections</h2>
                            <button
                                onClick={loadCollections}
                                className="p-2 hover:bg-gray-100 rounded"
                                title="Refresh"
                            >
                                <Database className="w-4 h-4 text-gray-600" />
                            </button>
                        </div>

                        {loading ? (
                            <div className="text-center py-8 text-gray-500 text-sm">
                                Loading...
                            </div>
                        ) : collections.length === 0 ? (
                            <div className="text-center py-8 text-gray-500">
                                <Database className="w-12 h-12 mx-auto mb-2 text-gray-400" />
                                <p className="text-sm">No collections yet</p>
                                <p className="text-xs mt-1">Create one above to start</p>
                            </div>
                        ) : (
                            <div className="space-y-2">
                                {collections.map((collection) => (
                                    <div
                                        key={collection}
                                        className={`p-3 rounded-lg transition-colors border ${selectedCollection === collection
                                            ? 'bg-purple-50 text-purple-700 border-purple-200'
                                            : 'hover:bg-gray-50 border-transparent'
                                            }`}
                                    >
                                        <div className="flex items-center justify-between">
                                            <button
                                                onClick={() => setSelectedCollection(collection)}
                                                className="flex-1 text-left font-medium truncate"
                                            >
                                                {collection}
                                            </button>
                                            <button
                                                onClick={(e) => {
                                                    e.stopPropagation();
                                                    handleDeleteCollection(collection);
                                                }}
                                                className="p-1 hover:bg-red-100 rounded"
                                                title="Delete collection"
                                            >
                                                <Trash2 className="w-4 h-4 text-red-600" />
                                            </button>
                                        </div>
                                    </div>
                                ))}
                            </div>
                        )}
                    </div>
                </div>

                {/* Main Content */}
                <div className="lg:col-span-2">
                    {selectedCollection ? (
                        <div className="space-y-6">
                            {/* Tabs */}
                            <div className="flex gap-2 border-b border-gray-200">
                                <button
                                    onClick={() => setActiveTab('sources')}
                                    className={`px-4 py-2 font-medium transition-colors ${activeTab === 'sources'
                                        ? 'text-purple-600 border-b-2 border-purple-600'
                                        : 'text-gray-600 hover:text-gray-900'
                                        }`}
                                >
                                    Connected Sources
                                </button>
                                <button
                                    onClick={() => setActiveTab('upload')}
                                    className={`px-4 py-2 font-medium transition-colors ${activeTab === 'upload'
                                        ? 'text-purple-600 border-b-2 border-purple-600'
                                        : 'text-gray-600 hover:text-gray-900'
                                        }`}
                                >
                                    Manual Upload
                                </button>
                            </div>

                            {/* Stats */}
                            {collectionStats && (
                                <div className="card p-6">
                                    <h3 className="font-semibold text-gray-900 mb-4">
                                        Collection Stats
                                    </h3>
                                    <div className="grid grid-cols-3 gap-4">
                                        <div className="bg-gray-50 p-3 rounded-lg">
                                            <div className="text-xs text-gray-600 mb-1">Name</div>
                                            <div className="font-mono text-sm font-semibold truncate">
                                                {collectionStats.collection_name}
                                            </div>
                                        </div>
                                        <div className="bg-gray-50 p-3 rounded-lg">
                                            <div className="text-xs text-gray-600 mb-1">
                                                Documents
                                            </div>
                                            <div className="text-lg font-semibold">
                                                {collectionStats.document_count.toLocaleString()}
                                            </div>
                                        </div>
                                        <div className="bg-gray-50 p-3 rounded-lg">
                                            <div className="text-xs text-gray-600 mb-1">Status</div>
                                            <div>
                                                <span
                                                    className={`px-2 py-1 text-xs rounded-full ${collectionStats.status === 'active'
                                                        ? 'bg-green-100 text-green-800'
                                                        : 'bg-gray-100 text-gray-800'
                                                        }`}
                                                >
                                                    {collectionStats.status}
                                                </span>
                                            </div>
                                        </div>
                                    </div>
                                </div>
                            )}

                            {/* Content */}
                            {activeTab === 'sources' ? (
                                <SourceManager
                                    collectionName={selectedCollection}
                                    onSourcesChange={() => loadCollectionStats(selectedCollection)}
                                />
                            ) : (
                                <div className="card p-6">
                                    <h3 className="font-semibold text-gray-900 mb-4">
                                        Upload Documents
                                    </h3>

                                    <label className="w-full border-2 border-dashed border-gray-300 rounded-lg p-12 flex flex-col items-center justify-center cursor-pointer hover:border-purple-400 hover:bg-purple-50 transition-colors">
                                        <Upload
                                            className={`w-12 h-12 mb-3 ${uploading ? 'text-purple-600' : 'text-gray-400'
                                                }`}
                                        />
                                        <span className="text-sm font-medium text-gray-700 mb-1">
                                            {uploading ? 'Processing file...' : 'Click to upload a file'}
                                        </span>
                                        <span className="text-xs text-gray-500">
                                            Supported: PDF, DOCX, Markdown, Code files, Text files
                                        </span>
                                        <input
                                            type="file"
                                            onChange={handleFileUpload}
                                            disabled={uploading}
                                            className="hidden"
                                            accept=".pdf,.docx,.md,.txt,.py,.js,.jsx,.ts,.tsx,.php,.json,.xml,.html,.css,.java,.cpp,.c,.go,.rs,.rb"
                                        />
                                    </label>
                                </div>
                            )}
                        </div>
                    ) : (
                        <div className="card p-12 text-center border-2 border-dashed border-gray-300">
                            <Database className="w-16 h-16 mx-auto mb-4 text-gray-400" />
                            <h3 className="text-lg font-semibold text-gray-900 mb-2">
                                No Collection Selected
                            </h3>
                            <p className="text-gray-600 max-w-sm mx-auto">
                                Create a new collection or select an existing one from the sidebar to
                                manage sources and upload documents.
                            </p>
                        </div>
                    )}
                </div>
            </div>
        </div>
    );
};