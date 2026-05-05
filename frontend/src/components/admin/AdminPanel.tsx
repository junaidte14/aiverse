import React, { useState } from 'react';
import { RAGManager } from '../rag/RAGManager';
import { AdminLayout } from './AdminLayout';
import { AdminConversations } from './adminListConversations';
import { AnalyticsDashboardComp } from './AnalyticsDashboard';
import { Settings } from './Settings';
import { UserManagement } from './UserManagement';

export const AdminPanel: React.FC = () => {
    const [activeTab, setActiveTab] = useState('dashboard');

    return (
        <AdminLayout activeTab={activeTab} onTabChange={setActiveTab}>
            {activeTab === 'dashboard' && <AnalyticsDashboardComp />}
            {activeTab === 'users' && <UserManagement />}
            {activeTab === 'rag' && <RAGManager />}
            {activeTab === 'convs' && <AdminConversations />}
            {activeTab === 'settings' && <Settings />}
        </AdminLayout>
    );
};