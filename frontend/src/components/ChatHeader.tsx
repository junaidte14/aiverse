// src/components/ChatHeader.tsx
import { ChevronDown, Home, Layout, LogOut, Shield, User as UserIcon } from 'lucide-react';
import React, { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { apiService } from '../services/api';
import { useStore } from '../store/useStore';

interface ChatHeaderProps {
    isLoading?: boolean;
    isAdmin?: boolean;
    onOpenAdmin?: () => void;
}

export const ChatHeader: React.FC<ChatHeaderProps> = ({
    isAdmin = false,
    onOpenAdmin,
}) => {
    const { user, logout } = useStore();
    const [showUserMenu, setShowUserMenu] = useState(false);
    const [isDropdownOpen, setIsDropdownOpen] = useState(false);
    const navigate = useNavigate();

    useEffect(() => {
        checkConnection();
    }, []);

    const checkConnection = async () => {
        try {
            await apiService.listProviders();
        } catch (error) {
        }
    };

    return (
        <div className="px-6 py-4 shadow-lg bg-white dark:bg-gray-900 border-b border-gray-100 dark:border-gray-800 transition-colors duration-300">
            <div className="flex items-center justify-between">
                <div>
                    <h1 className="text-2xl font-bold flex items-center gap-2 text-gray-800 dark:text-white">
                        🤖 AIVerse Chat
                    </h1>
                </div>

                <div className="flex items-center gap-2">
                    {isAdmin && (
                        <button
                            onClick={onOpenAdmin}
                            className="p-2 hover:bg-white/20 rounded-lg transition-colors"
                            title="Admin Panel"
                        >
                            <Shield className="w-5 h-5" />
                        </button>
                    )}

                    <div className="relative">
                        <button
                            onClick={() => {
                                navigate('/');
                                setIsDropdownOpen(false);
                            }}
                            className="flex items-center gap-2 px-3 py-2 hover:bg-white/20 rounded-lg transition-colors text-sm font-medium"
                            title="Home"
                        >
                            <Home className="w-5 h-5" />
                            <span>Home</span>
                        </button>
                    </div>
                    <div className="relative">
                        <button
                            onClick={() => setIsDropdownOpen(!isDropdownOpen)}
                            className="flex items-center gap-2 px-3 py-2 hover:bg-white/20 rounded-lg transition-colors text-sm font-medium"
                            title="Specialized Widgets"
                        >
                            <Layout className="w-5 h-5" />
                            <span>Demos</span>
                            <ChevronDown className={`w-4 h-4 transition-transform ${isDropdownOpen ? 'rotate-180' : ''}`} />
                        </button>

                        {/* Dropdown Menu */}
                        {isDropdownOpen && (
                            <div className="absolute top-full mt-2 w-48 bg-white rounded-xl shadow-xl border border-gray-100 py-1 z-50 pointer-events-auto">
                                <button
                                    onClick={() => {
                                        navigate('/demos?collection=versana');
                                        setIsDropdownOpen(false);
                                    }}
                                    className="w-full text-left px-4 py-2 text-sm text-gray-700 hover:bg-purple-50 hover:text-purple-700 transition-colors flex items-center gap-2"
                                >
                                    <div className="w-2 h-2 rounded-full bg-purple-500" />
                                    Versana
                                </button>
                            </div>
                        )}
                    </div>

                    <div className="relative">
                        {/* Dropdown Container */}
                        <button
                            onClick={() => setShowUserMenu(!showUserMenu)}
                            className="flex items-center gap-2 px-3 py-1.5 rounded-full transition-all border border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-800 hover:border-primary-300 dark:hover:border-primary-700"
                        >
                            <div className="w-6 h-6 rounded-full flex items-center justify-center bg-gray-100 dark:bg-gray-700">
                                <UserIcon className="w-4 h-4 text-gray-600 dark:text-gray-300" />
                            </div>
                            <span className="text-sm font-medium hidden sm:inline text-gray-700 dark:text-gray-200">
                                {user?.username || 'User'}
                            </span>
                            <ChevronDown className={`w-4 h-4 text-gray-400 transition-transform ${showUserMenu ? 'rotate-180' : ''}`} />
                        </button>

                        {showUserMenu && (
                            <>
                                <div className="fixed inset-0 z-40" onClick={() => setShowUserMenu(false)} />
                                <div className="absolute right-0 mt-2 w-56 rounded-xl shadow-2xl border border-gray-100 dark:border-gray-800 bg-white dark:bg-gray-900 py-2 z-50 animate-in fade-in zoom-in duration-150">
                                    <div className="px-4 py-3 border-b border-gray-50 dark:border-gray-800 mb-1">
                                        <p className="text-xs font-semibold uppercase tracking-wider text-gray-400">Account</p>
                                        <p className="text-sm font-medium truncate text-gray-900 dark:text-gray-100">{user?.email}</p>
                                    </div>

                                    <button
                                        onClick={() => {
                                            setShowUserMenu(false);
                                            logout();
                                        }}
                                        className="w-full flex items-center gap-3 px-4 py-2.5 text-sm text-red-600 hover:bg-red-50 dark:hover:bg-red-900/20 transition-colors"
                                    >
                                        <LogOut className="w-4 h-4" />
                                        Sign Out
                                    </button>
                                </div>
                            </>
                        )}
                    </div>
                </div>
            </div>

        </div>
    );
};