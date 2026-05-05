import {
    ChevronDown,
    Database,
    FileText,
    Loader2,
    Lock,
    Maximize2, MessageCircle, Minimize2, Send, X
} from 'lucide-react';
import React, { useEffect, useRef, useState } from 'react';
import ReactMarkdown from 'react-markdown';
import { Prism as SyntaxHighlighter } from 'react-syntax-highlighter';
import { oneDark as codeTheme } from 'react-syntax-highlighter/dist/esm/styles/prism';
import remarkGfm from 'remark-gfm';
import { useChat } from '../../hooks/useChat';
import { apiService } from '../../services/api';
import { useRagStore } from '../../store/useRagStore';
import { useStore } from '../../store/useStore';
import { Login } from '../Login'; // Ensure these are imported
import { Register } from '../Register';

interface ChatWidgetProps {
    collection?: string;
    provider?: string;
    model?: string;
    guestAllowed?: string;
    initialMessage?: string;
    primaryColor?: string;
    position?: 'bottom-right' | 'bottom-left';
    title?: string;
    testUserDetails?: {
        username: string;
        password: string;
    };
}

export const ChatWidget: React.FC<ChatWidgetProps> = ({
    collection = '',
    provider = 'groq',
    model = 'llama-3.3-70b-versatile',
    guestAllowed = 'true',
    initialMessage = 'How can I help you today?',
    primaryColor = '#0A2540',
    position = 'bottom-right',
    title = 'Support Assistant',
    testUserDetails
}) => {
    const {
        messages,
        sendMessage,
        isLoading,
        conversationId,
        settings,
        updateSettings
    } = useChat();

    const [isOpen, setIsOpen] = useState(true);
    const [isMinimized, setIsMinimized] = useState(false);
    const [isRegistering, setIsRegistering] = useState(false); // Toggle between Login/Register
    const [inputValue, setInputValue] = useState('');
    const { isAuthenticated, setUser } = useStore();
    const messagesEndRef = useRef<HTMLDivElement>(null);
    const [showSources, setShowSources] = useState(false);

    useEffect(() => {
        updateSettings({
            provider: provider,
            model: model,
            guest_allowed: guestAllowed
        });

        if (collection) {
            useRagStore.getState().setSelectedCollection(collection);
        }
    }, [provider, model, collection, updateSettings, guestAllowed]);

    useEffect(() => {
        // Determine dimensions based on state
        let dimensions = { width: '80px', height: '80px' }; // Default closed state (the bubble)

        if (isOpen) {
            if (isMinimized) {
                dimensions = { width: '300px', height: '80px' };
            } else {
                dimensions = { width: '440px', height: '620px' }; // Expanded state
            }
        }

        // Send the message to the parent window
        window.parent.postMessage({
            type: 'WIDGET_RESIZE',
            ...dimensions
        }, '*');
    }, [isOpen, isMinimized]);

    useEffect(() => {
        messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
    }, [messages, isLoading]);

    useEffect(() => {
        const performAutoLogin = async () => {
            // Only auto-login if details are provided and user isn't logged in
            if (testUserDetails && !isAuthenticated) {
                try {
                    // Option A: If you have a specific login method in your apiService
                    await apiService.login(testUserDetails);

                    // Trigger the existing success handler to fetch user data and update store
                    //await handleAuthSuccess();
                } catch (error) {
                    console.error("Auto-login failed:", error);
                }
            }
        };

        performAutoLogin();
    }, [testUserDetails]);

    const handleAuthSuccess = async () => {
        const user = await apiService.getCurrentUser();
        setUser(user);
    };

    const handleFormSubmit = async (e: React.FormEvent) => {
        e.preventDefault();
        if (!guestAllowed && !isAuthenticated) return;
        if (!inputValue.trim() || isLoading) return;

        const text = inputValue.trim();
        setInputValue('');
        await sendMessage(text);
    };

    const positionClasses = position === 'bottom-right' ? 'bottom-6 right-6' : 'bottom-6 left-6';

    return (
        <div className={`fixed ${positionClasses} z-50 font-sans pointer-events-auto`}>
            {!isOpen && (
                <button
                    onClick={() => setIsOpen(true)}
                    className="w-14 h-14 rounded-full shadow-2xl hover:scale-105 active:scale-95 transition-all flex items-center justify-center text-white"
                    style={{ backgroundColor: primaryColor }}
                >
                    <MessageCircle className="w-7 h-7" />
                </button>
            )}

            {isOpen && (
                <div className={`flex flex-col bg-white rounded-2xl shadow-2xl border border-gray-200 transition-all duration-300 overflow-hidden ${isMinimized ? 'h-16 w-72' : 'h-[600px] w-[420px]'}`}>

                    {/* FIXED HEADER */}
                    <div className="flex items-center justify-between px-4 py-4 text-white shrink-0" style={{ backgroundColor: primaryColor }}>
                        <div className="flex items-center gap-2">
                            <div className="w-2 h-2 bg-green-400 rounded-full animate-pulse" />
                            <span className="font-bold text-sm">{title}</span>
                        </div>
                        <div className="flex gap-1">
                            <button onClick={() => setIsMinimized(!isMinimized)} className="p-1 hover:bg-white/20 rounded">
                                {isMinimized ? <Maximize2 size={16} /> : <Minimize2 size={16} />}
                            </button>
                            <button onClick={() => setIsOpen(false)} className="p-1 hover:bg-white/20 rounded">
                                <X size={16} />
                            </button>
                        </div>
                    </div>

                    {!isMinimized && (
                        <>
                            {/* UNIFIED SCROLLABLE AREA */}
                            <div className="flex-1 overflow-y-auto p-4 space-y-4 bg-gray-50/50 scroll-smooth">
                                {/* Initial Welcome Message */}
                                {messages.length === 0 && (
                                    <div className="text-center py-6">
                                        <p className="text-gray-400 text-sm italic">{initialMessage}</p>
                                    </div>
                                )}

                                {/* AUTHENTICATION SECTION (Injected into Scroll Stream) */}
                                {!isAuthenticated && (
                                    <div className="flex flex-col gap-4 mx-auto max-w-[320px] py-4 animate-in fade-in slide-in-from-bottom-4 duration-500">
                                        <div className="flex items-center justify-center gap-2 text-gray-400 mb-2">
                                            <Lock size={14} />
                                            <span className="text-[10px] uppercase tracking-widest font-bold">
                                                Secure Access Required
                                            </span>
                                        </div>

                                        {isRegistering ? (
                                            <Register
                                                onRegisterSuccess={handleAuthSuccess}
                                                onSwitchToLogin={() => setIsRegistering(false)}
                                            />
                                        ) : (
                                            <Login
                                                onLoginSuccess={handleAuthSuccess}
                                                onSwitchToRegister={() => setIsRegistering(true)}
                                            />
                                        )}
                                    </div>
                                )}

                                {/* CHAT MESSAGES */}
                                {messages.map((msg: any) => (
                                    <div key={msg.id} className={`flex ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}>
                                        <div className={`max-w-[85%] rounded-2xl px-4 py-2.5 shadow-sm ${msg.role === 'user' ? 'text-white' : 'bg-white text-gray-800 border border-gray-100'}`}
                                            style={{ backgroundColor: msg.role === 'user' ? primaryColor : undefined }}>
                                            <div className="prose prose-sm max-w-none break-words">
                                                <ReactMarkdown
                                                    remarkPlugins={[remarkGfm]}
                                                    components={{
                                                        code({ inline, className, children }: any) {
                                                            const match = /language-(\w+)/.exec(className || '');
                                                            if (!inline && match && !msg.isStreaming) {
                                                                return (
                                                                    <SyntaxHighlighter
                                                                        style={codeTheme}
                                                                        language={match[1]}
                                                                        PreTag="div"
                                                                        customStyle={{
                                                                            borderRadius: '0.5rem',
                                                                            margin: '0.5rem 0',
                                                                            fontSize: '0.85rem',
                                                                        }}
                                                                    >
                                                                        {String(children).replace(/\n$/, '')}
                                                                    </SyntaxHighlighter>
                                                                );
                                                            }

                                                            return (
                                                                <code className={`${inline
                                                                    ? 'px-1 py-0.5 rounded bg-gray-100 dark:bg-gray-800 text-primary-600 dark:text-primary-400'
                                                                    : 'block p-3 rounded-lg my-2 whitespace-pre-wrap bg-gray-950 text-gray-100'
                                                                    }`}>
                                                                    {children}
                                                                </code>
                                                            );
                                                        },
                                                    }}
                                                >
                                                    {msg.content}
                                                </ReactMarkdown>
                                                {/* RAG Sources Section */}
                                                {msg.sources && msg.sources.length > 0 && (
                                                    <div className="mt-2 border-t border-gray-100 dark:border-gray-800 pt-3">
                                                        <button
                                                            onClick={() => setShowSources(!showSources)}
                                                            className="flex items-center gap-2 text-xs font-semibold text-gray-500 hover:text-primary-600 transition-colors"
                                                        >
                                                            <FileText className="w-3.5 h-3.5" />
                                                            <span>SOURCES ({msg.sources.length})</span>
                                                            <ChevronDown className={`w-3 h-3 transition-transform ${showSources ? 'rotate-180' : ''}`} />
                                                        </button>

                                                        {showSources && (
                                                            <div className="mt-3 grid grid-cols-1 sm:grid-cols-2 gap-2 animate-in fade-in slide-in-from-top-1">
                                                                {msg.sources.map((source: any, idx: number) => (
                                                                    <div
                                                                        key={idx}
                                                                        className="flex flex-col p-2 rounded-lg bg-gray-50 dark:bg-gray-800/50 border border-gray-100 dark:border-gray-700 hover:border-primary-200 transition-all"
                                                                    >
                                                                        <div className="flex items-center justify-between mb-1">
                                                                            <span className="text-[10px] font-medium text-primary-600 dark:text-primary-400 bg-primary-50 dark:bg-primary-900/30 px-1.5 py-0.5 rounded">
                                                                                Source {idx + 1}
                                                                            </span>
                                                                            <span className="text-[10px] text-gray-400">
                                                                                Chunk {source.chunk_index}
                                                                            </span>
                                                                        </div>
                                                                        <p className="text-[11px] font-medium text-gray-700 dark:text-gray-300 truncate">
                                                                            {source.filename}
                                                                        </p>
                                                                        {source.score && (
                                                                            <div className="mt-1 w-full bg-gray-200 dark:bg-gray-700 h-1 rounded-full overflow-hidden">
                                                                                <div
                                                                                    className="bg-primary-500 h-full"
                                                                                    style={{ width: `${Math.round(source.score * 100)}%` }}
                                                                                />
                                                                            </div>
                                                                        )}
                                                                    </div>
                                                                ))}
                                                            </div>
                                                        )}
                                                    </div>
                                                )}
                                            </div>
                                        </div>
                                    </div>
                                ))}

                                {isLoading && (
                                    <div className="flex justify-start">
                                        <div className="bg-white border border-gray-100 rounded-2xl px-4 py-2 shadow-sm">
                                            <Loader2 className="w-4 h-4 animate-spin text-gray-400" />
                                        </div>
                                    </div>
                                )}
                                <div ref={messagesEndRef} />
                            </div>

                            {/* FIXED FOOTER (Input or KB Info) */}
                            <div className="p-4 bg-white border-t border-gray-100 shrink-0">
                                {(!isAuthenticated) ? (
                                    <div className="text-center py-2 text-gray-400 text-[10px] font-bold uppercase tracking-widest">
                                        Please authenticate to continue
                                    </div>
                                ) : (
                                    <form onSubmit={handleFormSubmit} className="relative">
                                        <input
                                            type="text"
                                            value={inputValue}
                                            onChange={(e) => setInputValue(e.target.value)}
                                            placeholder="Message..."
                                            disabled={isLoading}
                                            className="w-full pl-4 pr-10 py-3 bg-gray-100 border-none rounded-xl text-sm focus:ring-2 outline-none disabled:opacity-50 transition-all"
                                            style={{ '--tw-ring-color': primaryColor } as any}
                                        />
                                        <button
                                            type="submit"
                                            disabled={isLoading || !inputValue.trim()}
                                            className="absolute right-2 top-1/2 -translate-y-1/2 p-1.5 rounded-lg text-white disabled:opacity-10 transition-all"
                                            style={{ backgroundColor: primaryColor }}
                                        >
                                            <Send size={16} />
                                        </button>
                                    </form>
                                )}

                                <div className="mt-3 flex items-center justify-between text-[10px] text-gray-400 font-bold uppercase tracking-widest">
                                    <div className="flex items-center gap-1.5">
                                        {collection && <Database size={10} />}
                                        {collection ? `KB: ${collection}` : settings.model}
                                    </div>
                                    {conversationId && <span>#{conversationId}</span>}
                                </div>
                            </div>
                        </>
                    )}
                </div>
            )}
        </div>
    );
};