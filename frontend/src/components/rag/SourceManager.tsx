import {
    AlertCircle,
    Folder,
    Loader,
    Plus,
    RefreshCw,
    Trash2
} from 'lucide-react';
import React, { useEffect, useState } from 'react';
import { apiService } from '../../services/api';

interface RAGSource {
    id: number;
    source_type: string;
    source_identifier: string;
    display_name: string;
    collection_name: string;
    last_sync_status: string;
    last_sync_at: string | null;
    last_sync_error: string | null;
    total_files: number;
    total_chunks: number;
    auto_sync: boolean;
}

interface SyncProgress {
    operationId: string;
    step: number;
    totalSteps: number;
    message: string;
    percentage: number;
    data?: any;
    status: 'idle' | 'connecting' | 'syncing' | 'completed' | 'failed';
    error?: string;
}

export const SourceManager: React.FC = () => {
    const [sources, setSources] = useState<RAGSource[]>([]);
    const [loading, setLoading] = useState(true);
    const [showAddForm, setShowAddForm] = useState(false);
    const [syncProgress, setSyncProgress] = useState<Map<number, SyncProgress>>(new Map());

    // Form state
    const [formData, setFormData] = useState({
        repo_url: '',
        collection_name: '',
        display_name: '',
        branch: '',
        auto_sync: false,
        sync_interval_hours: 24,
    });

    useEffect(() => {
        loadSources();
    }, []);

    const loadSources = async () => {
        try {
            setLoading(true);
            const data = await apiService.ragListSources();
            setSources(data);
        } catch (error) {
            console.error('Failed to load sources:', error);
        } finally {
            setLoading(false);
        }
    };

    const handleAddSource = async (e: React.FormEvent) => {
        e.preventDefault();

        try {
            await apiService.ragAddGitHubSource(formData);
            setShowAddForm(false);
            setFormData({
                repo_url: '',
                collection_name: '',
                display_name: '',
                branch: '',
                auto_sync: false,
                sync_interval_hours: 24,
            });
            await loadSources();
        } catch (error: any) {
            alert(`Failed to add source: ${error.message}`);
        }
    };

    const handleSync = async (sourceId: number) => {
        try {
            // Initialize progress state
            setSyncProgress(prev => new Map(prev).set(sourceId, {
                operationId: '',
                step: 0,
                totalSteps: 100,
                message: 'Initializing sync...',
                percentage: 0,
                status: 'connecting'
            }));

            // Start sync and get operation ID
            const response: any = await apiService.ragSyncSource(sourceId);
            const operationId = response.operation_id;

            // Update with operation ID
            setSyncProgress(prev => new Map(prev).set(sourceId, {
                operationId,
                step: 0,
                totalSteps: 100,
                message: 'Connecting to progress stream...',
                percentage: 0,
                status: 'connecting'
            }));

            // Connect to SSE for progress update
            const eventSource = apiService.ragSyncProgressStream(sourceId, operationId);

            eventSource.onmessage = (event) => {
                const data = JSON.parse(event.data);

                console.log('SSE Event:', data);

                if (data.type === 'connected') {
                    setSyncProgress(prev => new Map(prev).set(sourceId, {
                        operationId: data.operation_id,
                        step: 0,
                        totalSteps: 100,
                        message: 'Connected to sync stream',
                        percentage: 0,
                        status: 'syncing'
                    }));
                }
                else if (data.type === 'progress') {
                    const percentage = data.data?.percentage ||
                        Math.round((data.step / data.total_steps) * 100);

                    setSyncProgress(prev => new Map(prev).set(sourceId, {
                        operationId: data.operation_id,
                        step: data.step,
                        totalSteps: data.total_steps,
                        message: data.message,
                        percentage,
                        data: data.data,
                        status: 'syncing'
                    }));
                }
                else if (data.type === 'complete') {
                    setSyncProgress(prev => new Map(prev).set(sourceId, {
                        operationId: data.operation_id,
                        step: 100,
                        totalSteps: 100,
                        message: 'Sync completed successfully!',
                        percentage: 100,
                        status: 'completed'
                    }));

                    eventSource.close();

                    // Reload sources after a short delay
                    setTimeout(() => {
                        loadSources();
                        // Clear progress after 3 seconds
                        setTimeout(() => {
                            setSyncProgress(prev => {
                                const newMap = new Map(prev);
                                newMap.delete(sourceId);
                                return newMap;
                            });
                        }, 3000);
                    }, 1000);
                }
                else if (data.type === 'error') {
                    setSyncProgress(prev => new Map(prev).set(sourceId, {
                        operationId: data.operation_id,
                        step: 0,
                        totalSteps: 100,
                        message: 'Sync failed',
                        percentage: 0,
                        status: 'failed',
                        error: data.error || 'Unknown error'
                    }));

                    eventSource.close();

                    // Clear error after 5 seconds
                    setTimeout(() => {
                        setSyncProgress(prev => {
                            const newMap = new Map(prev);
                            newMap.delete(sourceId);
                            return newMap;
                        });
                        loadSources();
                    }, 5000);
                }
            };

            eventSource.onerror = (error) => {
                console.error('SSE Error:', error);
                setSyncProgress(prev => new Map(prev).set(sourceId, {
                    operationId,
                    step: 0,
                    totalSteps: 100,
                    message: 'Connection error',
                    percentage: 0,
                    status: 'failed',
                    error: 'Failed to connect to progress stream'
                }));
                eventSource.close();
            };

        } catch (error: any) {
            console.error('Sync error:', error);
            setSyncProgress(prev => new Map(prev).set(sourceId, {
                operationId: '',
                step: 0,
                totalSteps: 100,
                message: 'Failed to start sync',
                percentage: 0,
                status: 'failed',
                error: error.message
            }));
        }
    };

    const handleDelete = async (sourceId: number, sourceName: string) => {
        if (!window.confirm(`Are you sure you want to delete "${sourceName}"? This will remove all associated embeddings.`)) {
            return;
        }

        try {
            await apiService.ragDeleteSource(sourceId);
            await loadSources();
        } catch (error: any) {
            alert(`Failed to delete source: ${error.message}`);
        }
    };

    const getStatusColor = (status: string) => {
        switch (status) {
            case 'completed':
                return 'bg-green-100 text-green-800';
            case 'failed':
                return 'bg-red-100 text-red-800';
            case 'in_progress':
                return 'bg-blue-100 text-blue-800';
            default:
                return 'bg-gray-100 text-gray-800';
        }
    };

    if (loading) {
        return (
            <div className="flex items-center justify-center h-64">
                <Loader className="w-8 h-8 animate-spin text-purple-500" />
            </div>
        );
    }

    return (
        <div className="p-6 max-w-6xl mx-auto">
            {/* Header */}
            <div className="flex justify-between items-center mb-6">
                <div>
                    <h2 className="text-2xl font-bold text-gray-900">Knowledge Sources</h2>
                    <p className="text-sm text-gray-600 mt-1">
                        Manage GitHub repositories and other knowledge sources for RAG
                    </p>
                </div>
                <button
                    onClick={() => setShowAddForm(true)}
                    className="flex items-center gap-2 px-4 py-2 bg-purple-600 text-white rounded-lg hover:bg-purple-700 transition-colors"
                >
                    <Plus className="w-4 h-4" />
                    Add Source
                </button>
            </div>

            {/* Add Source Form */}
            {showAddForm && (
                <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
                    <div className="bg-white rounded-lg max-w-2xl w-full max-h-[90vh] overflow-y-auto">
                        <div className="p-6">
                            <h3 className="text-xl font-bold mb-4">Add GitHub Repository</h3>
                            <form onSubmit={handleAddSource} className="space-y-4">
                                <div>
                                    <label className="block text-sm font-medium text-gray-700 mb-1">
                                        Repository URL *
                                    </label>
                                    <input
                                        type="text"
                                        value={formData.repo_url}
                                        onChange={(e) => setFormData({ ...formData, repo_url: e.target.value })}
                                        placeholder="https://github.com/username/repo"
                                        className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-transparent"
                                        required
                                    />
                                </div>

                                <div>
                                    <label className="block text-sm font-medium text-gray-700 mb-1">
                                        Collection Name *
                                    </label>
                                    <input
                                        type="text"
                                        value={formData.collection_name}
                                        onChange={(e) => setFormData({ ...formData, collection_name: e.target.value })}
                                        placeholder="my-knowledge-base"
                                        className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-transparent"
                                        required
                                    />
                                </div>

                                <div>
                                    <label className="block text-sm font-medium text-gray-700 mb-1">
                                        Display Name (optional)
                                    </label>
                                    <input
                                        type="text"
                                        value={formData.display_name}
                                        onChange={(e) => setFormData({ ...formData, display_name: e.target.value })}
                                        placeholder="My Project Docs"
                                        className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-transparent"
                                    />
                                </div>

                                <div>
                                    <label className="block text-sm font-medium text-gray-700 mb-1">
                                        Branch (optional)
                                    </label>
                                    <input
                                        type="text"
                                        value={formData.branch}
                                        onChange={(e) => setFormData({ ...formData, branch: e.target.value })}
                                        placeholder="main"
                                        className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-transparent"
                                    />
                                </div>

                                <div className="flex items-center gap-2">
                                    <input
                                        type="checkbox"
                                        id="auto_sync"
                                        checked={formData.auto_sync}
                                        onChange={(e) => setFormData({ ...formData, auto_sync: e.target.checked })}
                                        className="rounded border-gray-300 text-purple-600 focus:ring-purple-500"
                                    />
                                    <label htmlFor="auto_sync" className="text-sm text-gray-700">
                                        Enable automatic sync
                                    </label>
                                </div>

                                {formData.auto_sync && (
                                    <div>
                                        <label className="block text-sm font-medium text-gray-700 mb-1">
                                            Sync Interval (hours)
                                        </label>
                                        <input
                                            type="number"
                                            value={formData.sync_interval_hours}
                                            onChange={(e) => setFormData({ ...formData, sync_interval_hours: parseInt(e.target.value) })}
                                            min="1"
                                            className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-transparent"
                                        />
                                    </div>
                                )}

                                <div className="flex gap-3 pt-4">
                                    <button
                                        type="submit"
                                        className="flex-1 px-4 py-2 bg-purple-600 text-white rounded-lg hover:bg-purple-700 transition-colors"
                                    >
                                        Add Source
                                    </button>
                                    <button
                                        type="button"
                                        onClick={() => setShowAddForm(false)}
                                        className="flex-1 px-4 py-2 bg-gray-200 text-gray-700 rounded-lg hover:bg-gray-300 transition-colors"
                                    >
                                        Cancel
                                    </button>
                                </div>
                            </form>
                        </div>
                    </div>
                </div>
            )}

            {/* Sources List */}
            <div className="space-y-4">
                {sources.length === 0 ? (
                    <div className="text-center py-12 bg-gray-50 rounded-lg">
                        <Folder className="w-12 h-12 text-gray-400 mx-auto mb-3" />
                        <p className="text-gray-600">No sources added yet</p>
                        <p className="text-sm text-gray-500 mt-1">
                            Add your first GitHub repository to get started
                        </p>
                    </div>
                ) : (
                    sources.map((source) => {
                        const progress = syncProgress.get(source.id);
                        const isInProgress = source.last_sync_status === 'in_progress' ||
                            progress?.status === 'syncing' ||
                            progress?.status === 'connecting';

                        return (
                            <div
                                key={source.id}
                                className="bg-white border border-gray-200 rounded-lg p-4 hover:shadow-md transition-shadow"
                            >
                                <div className="flex items-start justify-between">
                                    <div className="flex-1">
                                        <div className="flex items-center gap-3 mb-2">
                                            <Folder className="w-5 h-5 text-gray-600" />
                                            <h3 className="font-semibold text-gray-900">
                                                {source.display_name}
                                            </h3>
                                            <span className={`px-2 py-1 text-xs rounded-full ${getStatusColor(source.last_sync_status)}`}>
                                                {source.last_sync_status}
                                            </span>
                                        </div>

                                        <p className="text-sm text-gray-600 mb-1">
                                            {source.source_identifier}
                                        </p>

                                        <p className="text-xs text-gray-500">
                                            Collection: <span className="font-medium">{source.collection_name}</span>
                                            {' • '}
                                            {source.total_chunks > 0 && (
                                                <>
                                                    {source.total_files} files • {source.total_chunks} chunks
                                                    {source.last_sync_at && (
                                                        <> • Last synced: {new Date(source.last_sync_at).toLocaleString()}</>
                                                    )}
                                                </>
                                            )}
                                        </p>

                                        {/* Progress Bar */}
                                        {progress && (
                                            <div className="mt-3">
                                                <div className="flex items-center justify-between mb-1">
                                                    <span className="text-xs font-medium text-gray-700">
                                                        {progress.message}
                                                    </span>
                                                    <span className="text-xs text-gray-600">
                                                        {progress.percentage}%
                                                    </span>
                                                </div>
                                                <div className="w-full bg-gray-200 rounded-full h-2">
                                                    <div
                                                        className={`h-2 rounded-full transition-all duration-300 ${progress.status === 'failed'
                                                            ? 'bg-red-500'
                                                            : progress.status === 'completed'
                                                                ? 'bg-green-500'
                                                                : 'bg-purple-600'
                                                            }`}
                                                        style={{ width: `${progress.percentage}%` }}
                                                    />
                                                </div>
                                                {progress.error && (
                                                    <div className="mt-2 p-2 bg-red-50 border border-red-200 rounded text-xs text-red-700 flex items-start gap-2">
                                                        <AlertCircle className="w-4 h-4 flex-shrink-0 mt-0.5" />
                                                        <span>{progress.error}</span>
                                                    </div>
                                                )}
                                            </div>
                                        )}

                                        {source.last_sync_error && !progress && (
                                            <div className="mt-2 p-2 bg-red-50 border border-red-200 rounded text-xs text-red-700">
                                                <strong>Error:</strong> {source.last_sync_error}
                                            </div>
                                        )}
                                    </div>

                                    <div className="flex gap-2 ml-4">
                                        <button
                                            onClick={() => handleSync(source.id)}
                                            disabled={isInProgress}
                                            className={`p-2 rounded-lg transition-colors ${isInProgress
                                                ? 'bg-gray-100 text-gray-400 cursor-not-allowed'
                                                : 'bg-blue-50 text-blue-600 hover:bg-blue-100'
                                                }`}
                                            title="Sync now"
                                        >
                                            <RefreshCw className={`w-4 h-4 ${isInProgress ? 'animate-spin' : ''}`} />
                                        </button>
                                        <button
                                            onClick={() => handleDelete(source.id, source.display_name)}
                                            disabled={isInProgress}
                                            className="p-2 bg-red-50 text-red-600 rounded-lg hover:bg-red-100 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
                                            title="Delete source"
                                        >
                                            <Trash2 className="w-4 h-4" />
                                        </button>
                                    </div>
                                </div>
                            </div>
                        );
                    })
                )}
            </div>
        </div>
    );
};