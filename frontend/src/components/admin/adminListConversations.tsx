import {
    Calendar,
    ChevronLeft,
    ChevronRight,
    Cpu,
    MessageSquare,
    Search,
    User
} from 'lucide-react';
import React, { useEffect, useState } from 'react';
import { apiService } from '../../services/api';

export const AdminConversations: React.FC = () => {
    const [conversations, setConversations] = useState<any[]>([]);
    const [loading, setLoading] = useState(true);
    const [page, setPage] = useState(0);
    const limit = 20;

    // Filter states
    const [userId, setUserId] = useState<string>('');
    const [provider, setProvider] = useState<string>('');

    const fetchConversations = async () => {
        setLoading(true);
        try {
            const data = await apiService.adminListConversations(
                page * limit,
                limit,
                userId ? parseInt(userId) : undefined,
                provider || undefined
            );
            setConversations(data);
            console.log(data);
        } catch (error) {
            console.error("Failed to fetch admin conversations:", error);
        } finally {
            setLoading(false);
        }
    };

    useEffect(() => {
        fetchConversations();
    }, [page, provider]); // Re-fetch on page or provider change

    const handleSearch = (e: React.FormEvent) => {
        e.preventDefault();
        setPage(0);
        fetchConversations();
    };

    return (
        <div className="p-6 max-w-7xl mx-auto space-y-6">
            <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
                <div>
                    <h1 className="text-2xl font-bold text-gray-900 flex items-center gap-2">
                        <MessageSquare className="text-purple-600" />
                        Global Conversations
                    </h1>
                    <p className="text-gray-500 text-sm">Monitor and manage all AI interactions across the system.</p>
                </div>

                {/* Filters */}
                <form onSubmit={handleSearch} className="flex flex-wrap gap-2">
                    <div className="relative">
                        <User className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-400" size={16} />
                        <input
                            type="number"
                            placeholder="User ID..."
                            className="pl-9 pr-4 py-2 bg-white border border-gray-200 rounded-lg text-sm focus:ring-2 focus:ring-purple-500 outline-none w-32"
                            value={userId}
                            onChange={(e) => setUserId(e.target.value)}
                        />
                    </div>
                    <select
                        className="px-4 py-2 bg-white border border-gray-200 rounded-lg text-sm focus:ring-2 focus:ring-purple-500 outline-none"
                        value={provider}
                        onChange={(e) => setProvider(e.target.value)}
                    >
                        <option value="">All Providers</option>
                        <option value="groq">Groq</option>
                    </select>
                    <button
                        type="submit"
                        className="bg-purple-600 text-white px-4 py-2 rounded-lg text-sm font-medium hover:bg-purple-700 transition-colors flex items-center gap-2"
                    >
                        <Search size={16} />
                        Filter
                    </button>
                </form>
            </div>

            {/* Table Area */}
            <div className="bg-white border border-gray-200 rounded-xl overflow-hidden shadow-sm">
                <div className="overflow-x-auto">
                    <table className="w-full text-left border-collapse">
                        <thead>
                            <tr className="bg-gray-50 border-b border-gray-200">
                                <th className="px-6 py-4 text-xs font-bold uppercase tracking-wider text-gray-500">User</th>
                                <th className="px-6 py-4 text-xs font-bold uppercase tracking-wider text-gray-500">Model</th>
                                <th className="px-6 py-4 text-xs font-bold uppercase tracking-wider text-gray-500">Title</th>
                            </tr>
                        </thead>
                        <tbody className="divide-y divide-gray-100">
                            {loading ? (
                                Array(5).fill(0).map((_, i) => (
                                    <tr key={i} className="animate-pulse">
                                        <td colSpan={5} className="px-6 py-8 h-16 bg-gray-50/30"></td>
                                    </tr>
                                ))
                            ) : conversations.length === 0 ? (
                                <tr>
                                    <td colSpan={5} className="px-6 py-12 text-center text-gray-500">
                                        No conversations found.
                                    </td>
                                </tr>
                            ) : (
                                conversations.map((conv) => (
                                    <tr key={conv.id} className="hover:bg-gray-50 transition-colors">
                                        <td className="px-6 py-4">
                                            <div className="flex items-center gap-2">
                                                <div className="w-8 h-8 rounded-full bg-purple-100 text-purple-600 flex items-center justify-center text-xs font-bold">
                                                    {conv.user_id}
                                                </div>
                                                <span className="text-sm font-medium text-gray-700">User {conv.user_id}</span>
                                            </div>
                                        </td>
                                        <td className="px-6 py-4">
                                            <div className="flex flex-col gap-1">
                                                <div className="flex items-center gap-1.5 text-sm text-gray-800">
                                                    <Cpu size={14} className="text-gray-400" />
                                                    {conv.model_name}
                                                </div>
                                            </div>
                                        </td>
                                        <td className="px-6 py-4">
                                            <div className="flex items-center gap-1.5 text-sm text-gray-600">
                                                <Calendar size={14} className="text-gray-400" />
                                                {conv.title}
                                            </div>
                                        </td>
                                    </tr>
                                ))
                            )}
                        </tbody>
                    </table>
                </div>

                {/* Pagination Footer */}
                <div className="px-6 py-4 bg-gray-50 border-t border-gray-200 flex items-center justify-between">
                    <span className="text-xs text-gray-500 font-medium">
                        Showing Page {page + 1}
                    </span>
                    <div className="flex gap-2">
                        <button
                            disabled={page === 0 || loading}
                            onClick={() => setPage(p => p - 1)}
                            className="p-2 border border-gray-200 rounded-lg hover:bg-white disabled:opacity-50 transition-all shadow-sm"
                        >
                            <ChevronLeft size={16} />
                        </button>
                        <button
                            disabled={conversations.length < limit || loading}
                            onClick={() => setPage(p => p + 1)}
                            className="p-2 border border-gray-200 rounded-lg hover:bg-white disabled:opacity-50 transition-all shadow-sm"
                        >
                            <ChevronRight size={16} />
                        </button>
                    </div>
                </div>
            </div>
        </div>
    );
};