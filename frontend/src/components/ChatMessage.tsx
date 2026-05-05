import { Bot, ChevronDown, FileText, User } from 'lucide-react';
import React, { useState } from 'react';
import ReactMarkdown from 'react-markdown';
import { Prism as SyntaxHighlighter } from 'react-syntax-highlighter';
import { oneDark as codeTheme } from 'react-syntax-highlighter/dist/esm/styles/prism';
import remarkGfm from 'remark-gfm';
import type { Message } from '../types/chat';

interface ChatMessageProps {
    message: Message;
}

export const ChatMessage: React.FC<ChatMessageProps> = React.memo(({ message }) => {
    const isUser = message.role === 'user';
    const [showSources, setShowSources] = useState(false);

    return (
        <div className={`flex gap-3 animate-in fade-in slide-in-from-bottom-2 duration-300 ${isUser ? 'justify-end' : 'justify-start'}`}>
            {!isUser && (
                <div className="flex-shrink-0 w-8 h-8 rounded-full flex items-center justify-center bg-gray-100 dark:bg-gray-800">
                    <Bot className="w-5 h-5 text-primary-500" />
                </div>
            )}

            <div className={`max-w-[70%] rounded-2xl px-4 py-3 shadow-md ${isUser
                ? 'bg-gradient-to-br from-primary-500 to-secondary-500 text-white'
                : 'bg-white dark:bg-gray-900 text-gray-800 dark:text-gray-100'
                }`}>
                <div className="prose prose-sm dark:prose-invert max-w-none break-words prose-p:leading-relaxed">
                    <ReactMarkdown
                        remarkPlugins={[remarkGfm]}
                        components={{
                            code({ inline, className, children }: any) {
                                const match = /language-(\w+)/.exec(className || '');
                                if (!inline && match && !message.isStreaming) {
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
                        {message.content}
                    </ReactMarkdown>
                    {/* RAG Sources Section */}
                    {message.sources && message.sources.length > 0 && (
                        <div className="mt-2 border-t border-gray-100 dark:border-gray-800 pt-3">
                            <button
                                onClick={() => setShowSources(!showSources)}
                                className="flex items-center gap-2 text-xs font-semibold text-gray-500 hover:text-primary-600 transition-colors"
                            >
                                <FileText className="w-3.5 h-3.5" />
                                <span>SOURCES ({message.sources.length})</span>
                                <ChevronDown className={`w-3 h-3 transition-transform ${showSources ? 'rotate-180' : ''}`} />
                            </button>

                            {showSources && (
                                <div className="mt-3 grid grid-cols-1 sm:grid-cols-2 gap-2 animate-in fade-in slide-in-from-top-1">
                                    {message.sources.map((source: any, idx: number) => (
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

                    {message.isStreaming && (
                        <span className="inline-block w-1.5 h-4 ml-1 animate-pulse align-middle bg-primary-500" />
                    )}
                </div>

                <div className={`text-[10px] mt-2 opacity-50 ${isUser ? 'text-white/70 text-right' : 'text-gray-500 dark:text-gray-400 text-left'}`}>
                    {message.timestamp instanceof Date
                        ? message.timestamp.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
                        : ''}
                </div>
            </div>

            {isUser && (
                <div className="flex-shrink-0 w-8 h-8 rounded-full flex items-center justify-center bg-gray-200 dark:bg-gray-800">
                    <User className="w-5 h-5 text-gray-600 dark:text-gray-400" />
                </div>
            )}
        </div>
    );
});