import React, { useState } from 'react';
import { useSearchParams } from 'react-router-dom';
import { ChatHeader } from '../components/ChatHeader';
import { ChatWidget } from '../components/widget/ChatWidget';

export const DocsPage: React.FC = () => {
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
    });

    return (
        <div className="overflow-hidden">
            <ChatHeader />
            <div className="bg-transparent pointer-events-none">
                {/* Demo Explanation Overlay */}
                <div className="pointer-events-auto inset-0 overflow-y-auto p-8 pb-32">
                    <div className="max-w-3xl mx-auto space-y-8">
                        <section className="bg-white p-8 rounded-xl shadow-lg border border-gray-100">
                            <h1 className="text-3xl font-bold text-purple-600 mb-4">🤖 AIVerse Chat Widget Demo</h1>
                            <p className="text-gray-600">This page demonstrates how to embed the AIVerse chat widget on any website using <strong>widget-demo.html</strong> as a reference.</p>
                        </section>

                        <section className="bg-white p-8 rounded-xl shadow-lg border border-gray-100">
                            <h2 className="text-xl font-semibold mb-4 text-gray-800">📋 Basic Usage</h2>
                            <div className="bg-gray-900 rounded-lg p-4 overflow-x-auto">
                                <pre className="text-sm text-gray-300">
                                    <code>{`<script src="https://aiverse-pi.vercel.app/widget-loader.js"></script>
    <script>
        new AIVerseWidget({
            collection: '${config.collection || 'my-docs'}',
            guestAllowed: '${config.guestAllowed}',
            title: '${config.title}'
        });
    </script>`}</code>
                                </pre>
                            </div>
                        </section>

                        <section className="bg-white p-8 rounded-xl shadow-lg border border-gray-100">
                            <h2 className="text-xl font-semibold mb-4 text-gray-800">⚙️ Configuration Options</h2>
                            <div className="grid gap-4">
                                {[
                                    { label: 'collection', desc: 'RAG collection name for document search', val: config.collection },
                                    { label: 'provider', desc: 'AI provider (groq, openai, anthropic)', val: config.provider },
                                    { label: 'model', desc: 'AI model name', val: config.model },
                                    { label: 'guestAllowed', desc: 'Allow unauthenticated users', val: config.guestAllowed },
                                ].map((opt) => (
                                    <div key={opt.label} className="p-4 bg-gray-50 border-l-4 border-purple-500 rounded-r">
                                        <span className="font-bold text-gray-700">{opt.label}</span>: {opt.desc}
                                        <div className="mt-1 font-mono text-sm text-purple-700">{opt.label}: '{opt.val}'</div>
                                    </div>
                                ))}
                            </div>
                        </section>
                    </div>
                </div>
                <ChatWidget {...config} />
            </div>
        </div>
    );
};