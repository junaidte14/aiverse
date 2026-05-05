/**
 * Main chat container component
 */

import { AlertCircle } from 'lucide-react';
import React, { useEffect, useState } from 'react';
import { useChat } from '../hooks/useChat';
import { apiService } from '../services/api';
import { ChatHeader } from './ChatHeader';
import { ChatInput } from './ChatInput';
import { ChatMessages } from './ChatMessages';

interface ChatContainerProps {
    isAdmin?: boolean;
    onOpenAdmin?: () => void;
    onOpenRAG?: () => void;
}

export const ChatContainer: React.FC<ChatContainerProps> = ({
    isAdmin = false,
    onOpenAdmin,
}) => {
    const { messages, isLoading, error, sendMessage } =
        useChat();
    const [showError, setShowError] = useState(true);
    const [connectionStatus, setConnectionStatus] = useState<'connected' | 'disconnected' | 'connecting'>('connecting');
    const isStreaming = messages.some(m => m.isStreaming);

    useEffect(() => {
        checkConnection();
    }, []);

    const checkConnection = async () => {
        try {
            await apiService.listProviders();
            setConnectionStatus('connected');
        } catch (error) {
            setConnectionStatus('disconnected');
        }
    };

    return (
        <div className="h-screen flex items-center justify-center">
            <div className="card w-full h-[100vh] flex flex-col overflow-hidden">
                {/* Header */}
                <ChatHeader
                    isLoading={isLoading}
                    isAdmin={isAdmin}
                    onOpenAdmin={onOpenAdmin}
                />

                {/* Error Display */}
                {error && showError && (
                    <div className="bg-red-50 border-l-4 border-red-500 p-4 m-4">
                        <div className="flex items-start">
                            <AlertCircle className="w-5 h-5 text-red-500 mt-0.5 mr-3 flex-shrink-0" />
                            <div className="flex-1">
                                <h3 className="text-sm font-medium text-red-800">Error</h3>
                                <p className="text-sm text-red-700 mt-1">{error}</p>
                            </div>
                            <button
                                onClick={() => setShowError(false)}
                                className="text-red-500 hover:text-red-700"
                            >
                                ×
                            </button>
                        </div>
                    </div>
                )}

                {/* Messages */}
                <ChatMessages messages={messages} />

                {/* Input */}
                <ChatInput
                    onSend={sendMessage}
                    disabled={isStreaming || connectionStatus === 'disconnected'}
                    placeholder={
                        connectionStatus === 'disconnected'
                            ? 'Cannot connect to server...'
                            : isStreaming
                                ? 'Waiting for response...'
                                : 'Type your message...'
                    }
                />
            </div>
        </div>
    );
};