// src/components/Sidebar.tsx

import {
    Check,
    MessageSquare,
    Moon,
    MoreVertical,
    PanelLeftClose,
    PanelLeftOpen,
    Pencil,
    Plus,
    Sun,
    Trash2,
    X
} from 'lucide-react';
import React, { useEffect, useRef, useState } from 'react';
import { apiService } from '../services/api';
import { useConversationStore } from '../store/useConversationStore';
import { useStore } from '../store/useStore';

export const Sidebar: React.FC = () => {
    const {
        activeConversationId,
        setActiveConversationId,
        isSidebarOpen,
        toggleSidebar,
        theme,
        setTheme,
        setMessages,
    } = useStore();

    const { conversations, fetchConversations, updateConversationTitle,
        removeConversation } = useConversationStore();
    const [isLoading] = useState(false);
    const [hoveredId, setHoveredId] = useState<string | null>(null);
    const [menuOpenId, setMenuOpenId] = useState<string | null>(null);
    const [editingId, setEditingId] = useState<string | null>(null);
    const [editTitle, setEditTitle] = useState('');
    const [deletingId, setDeletingId] = useState<string | null>(null);

    const menuRef = useRef<HTMLDivElement>(null);
    const inputRef = useRef<HTMLInputElement>(null);

    useEffect(() => {
        fetchConversations();
    }, []);

    useEffect(() => {
        const handleClickOutside = (event: MouseEvent) => {
            if (menuRef.current && !menuRef.current.contains(event.target as Node)) {
                setMenuOpenId(null);
            }
        };

        document.addEventListener('mousedown', handleClickOutside);
        return () => document.removeEventListener('mousedown', handleClickOutside);
    }, []);

    useEffect(() => {
        if (editingId && inputRef.current) {
            inputRef.current.focus();
            inputRef.current.select();
        }
    }, [editingId]);

    // ✅ Load messages when selecting a conversation
    const handleSelectConversation = async (id: string) => {
        try {
            setActiveConversationId(id);
            const messages = await apiService.getMessages(id);
            setMessages(
                messages.map((m: any) => ({
                    id: m.id,
                    role: m.role,
                    content: m.content,
                    sources: m.metadata_json?.sources || [],
                    timestamp: new Date(m.created_at),
                }))
            );
        } catch (error) {
            console.error("Failed to load messages", error);
        }
    };

    // ✅ New chat
    const handleNewChat = () => {
        setActiveConversationId(null);
        setMessages([]); // clear UI
    };

    const handleRename = (chat: any) => {
        setEditingId(chat.id);
        setEditTitle(chat.title || `Chat ${chat.id}`);
        setMenuOpenId(null);
    };

    const handleSaveRename = async (id: string) => {
        if (!editTitle.trim()) {
            setEditingId(null);
            return;
        }

        try {
            await apiService.updateConversation(id, editTitle.trim());
            updateConversationTitle(id, editTitle.trim());
            setEditingId(null);
        } catch (error) {
            console.error('Failed to rename conversation:', error);
            alert('Failed to rename conversation');
        }
    };

    const handleCancelRename = () => {
        setEditingId(null);
        setEditTitle('');
    };

    const handleDelete = async (id: string) => {
        if (!confirm('Are you sure you want to delete this conversation?')) {
            setMenuOpenId(null);
            return;
        }

        setDeletingId(id);
        try {
            await apiService.deleteConversation(id);
            removeConversation(id);

            // If we deleted the active conversation, clear messages
            if (activeConversationId === id) {
                setActiveConversationId(null);
                setMessages([]);
            }
        } catch (error) {
            console.error('Failed to delete conversation:', error);
            alert('Failed to delete conversation');
        } finally {
            setDeletingId(null);
            setMenuOpenId(null);
        }
    };

    return (
        <aside className={`${isSidebarOpen ? 'w-72' : 'w-20'} flex flex-col h-screen transition-all duration-300 border-r border-gray-200 dark:border-gray-800 bg-white dark:bg-gray-900 overflow-hidden`}>

            {/* Header */}
            <div className="p-4 flex items-center justify-between">
                {isSidebarOpen && (
                    <h2 className="font-bold text-gray-800 dark:text-white">
                        Chat History
                    </h2>
                )}
                <button
                    onClick={toggleSidebar}
                    className="p-2 hover:bg-gray-100 dark:hover:bg-gray-800 rounded-lg text-gray-500"
                >
                    {isSidebarOpen ? <PanelLeftClose size={20} /> : <PanelLeftOpen size={20} />}
                </button>
            </div>

            {/* New Chat */}
            <div className="px-3 mb-4">
                <button
                    onClick={handleNewChat}
                    className="w-full flex items-center gap-2 p-3 bg-primary-500 hover:bg-primary-600 text-white rounded-xl transition-all shadow-md"
                >
                    <Plus size={20} />
                    {isSidebarOpen && <span className="font-medium">New Chat</span>}
                </button>
            </div>

            {/* History */}
            <div className="flex-1 overflow-y-auto px-2 space-y-1 custom-scrollbar">
                {isLoading && (
                    <div className="text-center text-sm text-gray-400 mt-4">
                        Loading...
                    </div>
                )}

                {conversations.map((chat) => (
                    <div
                        key={chat.id}
                        className={`relative group rounded-xl transition-all ${activeConversationId === chat.id
                            ? 'bg-gray-100 dark:bg-gray-800'
                            : 'hover:bg-gray-50 dark:hover:bg-gray-800/50'
                            }`}
                        onMouseEnter={() => setHoveredId(chat.id)}
                        onMouseLeave={() => setHoveredId(null)}
                    >
                        {editingId === chat.id ? (
                            // Rename Input
                            <div className="flex items-center gap-2 p-3">
                                <MessageSquare size={18} className="flex-shrink-0 text-gray-400" />
                                <input
                                    ref={inputRef}
                                    type="text"
                                    value={editTitle}
                                    onChange={(e) => setEditTitle(e.target.value)}
                                    onKeyDown={(e) => {
                                        if (e.key === 'Enter') {
                                            handleSaveRename(chat.id);
                                        } else if (e.key === 'Escape') {
                                            handleCancelRename();
                                        }
                                    }}
                                    className="flex-1 bg-white dark:bg-gray-700 border border-gray-300 dark:border-gray-600 rounded px-2 py-1 text-sm focus:outline-none focus:ring-2 focus:ring-primary-500"
                                />
                                <button
                                    onClick={() => handleSaveRename(chat.id)}
                                    className="p-1 hover:bg-gray-200 dark:hover:bg-gray-700 rounded"
                                    title="Save"
                                >
                                    <Check size={16} className="text-green-600" />
                                </button>
                                <button
                                    onClick={handleCancelRename}
                                    className="p-1 hover:bg-gray-200 dark:hover:bg-gray-700 rounded"
                                    title="Cancel"
                                >
                                    <X size={16} className="text-red-600" />
                                </button>
                            </div>
                        ) : (
                            // Normal Display
                            <div
                                onClick={() => handleSelectConversation(chat.id)}
                                role="button"
                                tabIndex={0}
                                className={`w-full flex items-center gap-3 p-3 transition-all ${activeConversationId === chat.id
                                    ? 'text-primary-500'
                                    : 'text-gray-600 dark:text-gray-400'
                                    } ${deletingId === chat.id ? 'opacity-50 cursor-not-allowed' : ''}`}
                            >
                                <MessageSquare size={18} className="flex-shrink-0" />

                                {isSidebarOpen && (
                                    <>
                                        <span className="truncate text-sm text-left flex-1">
                                            {chat.title || `Chat ${chat.id}`}
                                        </span>

                                        {/* Menu Button - Only show when hovered */}
                                        {hoveredId === chat.id && deletingId !== chat.id && (
                                            <div className="relative" ref={menuRef}>
                                                <button
                                                    onClick={(e) => {
                                                        e.stopPropagation();
                                                        setMenuOpenId(menuOpenId === chat.id ? null : chat.id);
                                                    }}
                                                    className="p-1 hover:bg-gray-200 dark:hover:bg-gray-700 rounded transition-colors"
                                                >
                                                    <MoreVertical size={16} />
                                                </button>

                                                {/* Dropdown Menu */}
                                                {menuOpenId === chat.id && (
                                                    <div className="absolute right-0 mt-1 w-40 bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg shadow-lg z-10">
                                                        <button
                                                            onClick={(e) => {
                                                                e.stopPropagation();
                                                                handleRename(chat);
                                                            }}
                                                            className="w-full flex items-center gap-2 px-4 py-2 text-sm text-gray-700 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-700 transition-colors rounded-t-lg"
                                                        >
                                                            <Pencil size={14} />
                                                            Rename
                                                        </button>
                                                        <button
                                                            onClick={(e) => {
                                                                e.stopPropagation();
                                                                handleDelete(chat.id);
                                                            }}
                                                            className="w-full flex items-center gap-2 px-4 py-2 text-sm text-red-600 dark:text-red-400 hover:bg-red-50 dark:hover:bg-red-900/20 transition-colors rounded-b-lg"
                                                        >
                                                            <Trash2 size={14} />
                                                            Delete
                                                        </button>
                                                    </div>
                                                )}
                                            </div>
                                        )}

                                        {/* Loading indicator when deleting */}
                                        {deletingId === chat.id && (
                                            <div className="w-4 h-4 border-2 border-gray-300 border-t-primary-500 rounded-full animate-spin" />
                                        )}
                                    </>
                                )}
                            </div>
                        )}
                    </div>
                ))}
            </div>

            {/* Footer */}
            <div className="p-4 border-t border-gray-100 dark:border-gray-800">
                <button
                    onClick={() => setTheme(theme === 'light' ? 'dark' : 'light')}
                    className="w-full flex items-center gap-3 p-2 hover:bg-gray-100 dark:hover:bg-gray-800 rounded-lg text-gray-500 transition-colors"
                >
                    {theme === 'light' ? <Moon size={20} /> : <Sun size={20} />}
                    {isSidebarOpen && (
                        <span className="text-sm font-medium">
                            {theme === 'light' ? 'Dark Mode' : 'Light Mode'}
                        </span>
                    )}
                </button>
            </div>
        </aside>
    );
};