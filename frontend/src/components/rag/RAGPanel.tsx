import { Database, MessageSquare, Settings } from 'lucide-react';
import React, { useEffect, useState } from 'react';
import { apiService } from '../../services/api';
import { RAGChat } from './RAGChat';
import { RAGManager } from './RAGManager';

export const RAGPanel: React.FC = () => {
    const [activeTab, setActiveTab] = useState<'chat' | 'manage'>('chat');
    const [collections, setCollections] = useState<string[]>([]);
    const [selectedCollection, setSelectedCollection] = useState<string>('versana-ecosystem');

    useEffect(() => {
        loadCollections();
    }, []);

    const loadCollections = async () => {
        try {
            const data = await apiService.ragListCollections();
            setCollections(data);
            if (data.length > 0 && !data.includes(selectedCollection)) {
                setSelectedCollection(data[0]);
            }
        } catch (error) {
            console.error('Failed to load collections:', error);
        }
    };

    return (
        <div className="h-screen flex flex-col">
            {/* Header */}
            <div className="bg-gradient-to-r from-purple-500 to-indigo-500 text-white px-6 py-4">
                <div className="flex items-center justify-between">
                    <div>
                        <h1 className="text-2xl font-bold flex items-center gap-2">
                            <Database className="w-6 h-6" />
                            RAG Assistant
                        </h1>
                        <p className="text-sm text-white/80 mt-1">
                            Retrieval-Augmented Generation for specialized knowledge. Select the specialized knowledge source below.
                        </p>
                    </div>

                </div>

                {/* Tabs */}
                <div className="flex gap-2 mt-4">
                    <button
                        onClick={() => setActiveTab('chat')}
                        className={`flex items-center gap-2 px-4 py-2 rounded-lg transition-colors ${activeTab === 'chat'
                            ? 'bg-white/20 text-white'
                            : 'text-white/70 hover:text-white hover:bg-white/10'
                            }`}
                    >
                        <MessageSquare className="w-4 h-4" />
                        Chat
                    </button>
                    <button
                        onClick={() => setActiveTab('manage')}
                        className={`flex items-center gap-2 px-4 py-2 rounded-lg transition-colors ${activeTab === 'manage'
                            ? 'bg-white/20 text-white'
                            : 'text-white/70 hover:text-white hover:bg-white/10'
                            }`}
                    >
                        <Settings className="w-4 h-4" />
                        Manage
                    </button>
                    <select
                        value={selectedCollection}
                        onChange={(e) => setSelectedCollection(e.target.value)}
                        className="border border-gray-300 rounded-lg px-4 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-purple-500"
                    >
                        {collections.map((collection) => (
                            <option key={collection} value={collection} className="text-gray-900">
                                {collection}
                            </option>
                        ))}
                    </select>
                </div>
            </div>

            {/* Content */}
            <div className="flex-1 overflow-y-auto custom-scrollbar">
                {activeTab === 'chat' ? (
                    <div className="flex-1">
                        <RAGChat collectionName={selectedCollection} />
                    </div>
                ) : (
                    <div className="h-full overflow-y-auto">
                        <RAGManager />
                    </div>
                )}
            </div>
        </div>
    );
};