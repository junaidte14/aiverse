import React, { useState } from 'react';
import { useSearchParams } from 'react-router-dom';
import { ChatWidget } from '../components/widget/ChatWidget';

export const WidgetPage: React.FC = () => {
    const [searchParams] = useSearchParams();

    // Parse configuration once on mount
    const [config] = useState({
        collection: searchParams.get('collection') || '',
        provider: searchParams.get('provider') || 'groq',
        model: searchParams.get('model') || 'llama-3.3-70b-versatile',
        guestAllowed: searchParams.get('guestAllowed') || 'false',
        initialMessage: searchParams.get('initialMessage') || 'How can I help you today?',
        primaryColor: searchParams.get('primaryColor') || '#9333ea',
        position: (searchParams.get('position') as any) || 'bottom-right',
        title: searchParams.get('title') || 'AI Assistant',
        testUserDetails: {
            username: 'test_user',
            password: 'Test@1234'
        }
    });

    return (
        <div className="bg-transparent h-screen w-screen overflow-hidden pointer-events-none">
            <ChatWidget {...config} />
        </div>
    );
};