/**
 * Container for chat messages with auto-scroll
 */

import { Atom, LineChart, MessageCircleCode, Rocket, ShieldCheck } from 'lucide-react';
import React, { useEffect, useRef } from 'react';
import type { Message } from '../types/chat';
import { ChatMessage } from './ChatMessage';

interface ChatMessagesProps {
    messages: Message[];
}

export const ChatMessages: React.FC<ChatMessagesProps> = ({ messages }) => {
    const messagesEndRef = useRef<HTMLDivElement>(null);
    const containerRef = useRef<HTMLDivElement>(null);

    // Auto-scroll to bottom when new messages arrive
    useEffect(() => {
        messagesEndRef.current?.scrollIntoView({ behavior: 'auto' });
    }, [messages]);

    return (
        <div
            ref={containerRef}
            className="flex-1 overflow-y-auto px-6 py-4 space-y-4 custom-scrollbar"
        >
            {messages.length === 0 ? (
                <div className="max-w-5xl mx-auto">
                    {/* Hero Section */}
                    <div className="text-center mt-6 mb-4 animate-fade-in">
                        <h2 className="text-3xl font-bold mb-2">Welcome to AIVerse</h2>
                        <p className="max-w-md mx-auto">
                            Experience the power of a full-stack AI platform built with modern architecture.
                            Select a provider to start chatting.
                        </p>
                    </div>

                    {/* Feature Grid */}
                    <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-5 gap-4 w-full">
                        {[
                            { icon: <LineChart className="w-3 h-3" />, title: "RAG Integration", desc: "Advanced Retrieval-Augmented Generation to connect LLMs with your custom data." },
                            { icon: <MessageCircleCode className="w-3 h-3" />, title: "Smart Chat", desc: "Interactive customer support widget with real-time streaming capabilities." },
                            { icon: <Atom className="w-3 h-3" />, title: "React & FastAPI", desc: "High-performance backend paired with a responsive, modern frontend and Postgres storage." },
                            { icon: <ShieldCheck className="w-3 h-3" />, title: "Secure & Scalable", desc: "Production-ready JWT authentication and robust data protection protocols." },
                            { icon: <Rocket className="w-3 h-3" />, title: "Docker & K8s", desc: "Fully containerized deployment with CI/CD automation for flexible multi-cloud hosting." }
                        ].map((feature, idx) => (
                            <div
                                key={idx}
                                className="group flex flex-col items-center p-4 bg-white border border-gray-100 rounded-xl shadow-sm hover:shadow-md hover:border-primary-200 transition-all duration-200"
                            >
                                <div className="p-2 bg-gray-50 rounded-lg text-primary-500 group-hover:bg-primary-500 group-hover:text-white transition-colors duration-200 mb-3">
                                    {feature.icon}
                                </div>
                                <h3 className="text-sm font-semibold text-gray-900">{feature.title}</h3>
                                <p className="text-[11px] text-gray-400 text-center mt-1 leading-tight">
                                    {feature.desc}
                                </p>
                            </div>
                        ))}
                    </div>

                    <div className="mt-6 text-xs text-center font-medium uppercase tracking-widest animate-bounce">
                        Start a conversation below
                    </div>
                </div>
            ) : (
                <>
                    {messages.map((message) => (
                        <ChatMessage key={message.id} message={message} />
                    ))}
                    <div ref={messagesEndRef} />
                </>
            )}
        </div>
    );
};