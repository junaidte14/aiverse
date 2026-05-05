import { BarChart3, Cog, Menu, MessageCircleCheckIcon, Settings, Users, X } from 'lucide-react';
import React, { useState } from 'react';

interface AdminLayoutProps {
    children: React.ReactNode;
    activeTab: string;
    onTabChange: (tab: string) => void;
}

export const AdminLayout: React.FC<AdminLayoutProps> = ({
    children,
    activeTab,
    onTabChange,
}) => {
    const [sidebarOpen, setSidebarOpen] = useState(true);

    const tabs = [
        { id: 'dashboard', label: 'Analytics', icon: BarChart3 },
        { id: 'users', label: 'Users', icon: Users },
        { id: 'rag', label: 'RAG', icon: Cog },
        { id: 'convs', label: 'Conversations', icon: MessageCircleCheckIcon },
        { id: 'settings', label: 'Settings', icon: Settings },
    ];

    return (
        <div className="flex h-screen bg-gray-100">
            {/* Sidebar */}
            <div
                className={`${sidebarOpen ? 'w-64' : 'w-0'
                    } transition-all duration-300 bg-white border-r border-gray-200 overflow-hidden`}
            >
                <div className="p-4 border-b border-gray-200 flex items-center justify-between">
                    <h2 className="text-lg font-bold text-gray-900">Admin Panel</h2>
                    <button
                        onClick={() => setSidebarOpen(false)}
                        className="lg:hidden p-1 hover:bg-gray-100 rounded"
                    >
                        <X className="w-5 h-5" />
                    </button>
                </div>
                <nav className="p-4 space-y-2">
                    {tabs.map((tab) => {
                        const Icon = tab.icon;
                        return (
                            <button
                                key={tab.id}
                                onClick={() => onTabChange(tab.id)}
                                className={`w-full flex items-center gap-3 px-4 py-3 rounded-lg transition-colors ${activeTab === tab.id
                                    ? 'bg-primary-50 text-primary-600'
                                    : 'text-gray-700 hover:bg-gray-100'
                                    }`}
                            >
                                <Icon className="w-5 h-5" />
                                <span className="font-medium">{tab.label}</span>
                            </button>
                        );
                    })}
                </nav>
            </div>

            {/* Main Content */}
            <div className="flex-1 overflow-auto">
                <div className="p-6">
                    {!sidebarOpen && (
                        <button
                            onClick={() => setSidebarOpen(true)}
                            className="mb-4 p-2 bg-white border border-gray-200 rounded-lg hover:bg-gray-50"
                        >
                            <Menu className="w-5 h-5" />
                        </button>
                    )}
                    {children}
                </div>
            </div>
        </div>
    );
};