import { Database, FileText, Send, Zap } from 'lucide-react';
import React, { useState } from 'react';
import ReactMarkdown from 'react-markdown';
import rehypeHighlight from 'rehype-highlight';
import remarkGfm from 'remark-gfm';
import { apiService } from '../../services/api';
import type { RAGQueryRequest, RAGQueryResponse } from '../../types/rag';

interface RAGChatProps {
    collectionName: string;
    provider?: string;
    model?: string;
}

export const RAGChat: React.FC<RAGChatProps> = ({
    collectionName,
    provider = 'groq',
    model = 'llama-3.3-70b-versatile',
}) => {
    const [question, setQuestion] = useState('');
    const [response, setResponse] = useState<RAGQueryResponse | null>(null);
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState('');
    const [showSources, setShowSources] = useState(true);

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault();
        if (!question.trim() || loading) return;

        setLoading(true);
        setError('');
        setResponse(null);

        try {
            const request: RAGQueryRequest = {
                question: question.trim(),
                collection_name: collectionName,
                provider,
                model,
                n_context_docs: 5,
                include_sources: true,
            };

            const result = await apiService.ragQuery(request);
            setResponse(result);
        } catch (err: any) {
            setError(err.response?.data?.detail || 'Failed to get response');
        } finally {
            setLoading(false);
        }
    };

    return (
        <div className="flex flex-col h-full">
            {/* Header */}
            <div className="bg-gradient-to-r from-purple-500 to-indigo-500 text-white px-6 py-4">
                <div className="flex items-center gap-2 mb-2">
                    <Database className="w-5 h-5" />
                    <h2 className="text-xl font-bold">RAG-Powered Chat</h2>
                </div>
                <p className="text-sm text-white/80">
                    Collection: <span className="font-mono">{collectionName}</span>
                </p>
            </div>

            {/* Response Area */}
            <div className="flex-1 p-6 space-y-4">
                {response && (
                    <div>
                        {/* Answer */}
                        <div className="bg-white border border-gray-200 rounded-lg p-6 shadow-sm">
                            <div className="flex items-start gap-3">
                                <div className="p-2 bg-purple-50 rounded-lg">
                                    <FileText className="w-5 h-5 text-purple-600" />
                                </div>
                                <div className="flex-1">
                                    <h3 className="font-semibold text-gray-900 mb-2">Answer</h3>
                                    <div className="prose prose-sm max-w-none text-gray-700 leading-relaxed">
                                        <ReactMarkdown
                                            remarkPlugins={[remarkGfm]}
                                            rehypePlugins={[rehypeHighlight]}
                                            components={{
                                                p: ({ children }) => <p className="mb-4 last:mb-0">{children}</p>,
                                                // Style bullet points for better scannability
                                                ul: ({ children }) => <ul className="list-disc pl-5 mb-4 space-y-2">{children}</ul>,
                                                ol: ({ children }) => <ol className="list-decimal pl-5 mb-4 space-y-2">{children}</ol>,
                                                // Improve Heading hierarchy
                                                h3: ({ children }) => <h3 className="text-lg font-bold text-gray-900 mt-6 mb-2 border-b border-gray-100 pb-1">{children}</h3>,
                                                // Custom styling for code blocks
                                                code({ node, inline, className, children, ...props }: any) {
                                                    return (
                                                        <code
                                                            className={`${className} rounded bg-gray-100 px-1 py-0.5 font-mono text-sm`}
                                                            {...props}
                                                        >
                                                            {children}
                                                        </code>
                                                    );
                                                },
                                                // Interactive Source Linking
                                                text: ({ children }) => {
                                                    const text = children?.toString();
                                                    if (!text) return null;

                                                    const parts = text.split(/(\[\d+\])/g);
                                                    return (
                                                        <>
                                                            {parts.map((part, i) => {
                                                                const match = part.match(/\[(\d+)\]/);
                                                                if (match) {
                                                                    const sourceNum = match[1];
                                                                    return (
                                                                        <a
                                                                            key={i}
                                                                            href={`#source-${sourceNum}`}
                                                                            className="font-bold text-indigo-600 hover:text-indigo-800 transition-colors cursor-pointer px-0.5"
                                                                            onClick={(e) => {
                                                                                e.preventDefault();
                                                                                document.getElementById(`source-${sourceNum}`)?.scrollIntoView({ behavior: 'smooth' });
                                                                            }}
                                                                        >
                                                                            {part}
                                                                        </a>
                                                                    );
                                                                }
                                                                return part;
                                                            })}
                                                        </>
                                                    );
                                                }
                                            }}
                                        >
                                            {response.answer}
                                        </ReactMarkdown>
                                    </div>
                                </div>
                            </div>

                            {/* Stats */}
                            <div className="flex items-center gap-4 mt-4 pt-4 border-t border-gray-100 text-xs text-gray-500">
                                {!!response.tokens_used && (
                                    <div className="flex items-center gap-1">
                                        <Zap className="w-3 h-3" />
                                        {response.tokens_used.toLocaleString()} tokens
                                    </div>
                                )}
                            </div>
                        </div>

                        {/* Sources */}
                        {response.sources && response.sources.length > 0 && (
                            <div className="bg-gray-50 border border-gray-200 rounded-lg p-6">
                                <div className="flex items-center justify-between mb-4">
                                    <h3 className="font-semibold text-gray-900">
                                        Sources ({response.sources.length})
                                    </h3>
                                    <button
                                        onClick={() => setShowSources(!showSources)}
                                        className="text-sm text-purple-600 hover:text-purple-700"
                                    >
                                        {showSources ? 'Hide' : 'Show'}
                                    </button>
                                </div>

                                {showSources && (
                                    <div className="space-y-3">
                                        {response.sources.map((source) => (
                                            <div
                                                id={`source-${source.source_number}`} // This matches the href above
                                                key={source.source_number}
                                                className="bg-white border border-gray-200 rounded-lg p-4 scroll-mt-20 shadow-sm"
                                            >
                                                <div className="flex items-start gap-3">
                                                    <div className="flex-shrink-0 w-8 h-8 bg-purple-100 text-purple-600 rounded-full flex items-center justify-center text-sm font-bold">
                                                        {source.source_number}
                                                    </div>
                                                    <div className="flex-1 min-w-0">
                                                        <div className="font-medium text-gray-900 truncate">
                                                            {source.filename}
                                                        </div>
                                                        <div className="text-xs text-gray-500 mt-1 truncate">
                                                            {source.source}
                                                        </div>
                                                        <div className="flex items-center gap-3 mt-2 text-xs text-gray-500">
                                                            <span>
                                                                Chunk {source.chunk_index + 1}
                                                            </span>
                                                            <span>•</span>
                                                            <span>
                                                                Relevance:{' '}
                                                                {(
                                                                    (1 - source.distance) *
                                                                    100
                                                                ).toFixed(1)}
                                                                %
                                                            </span>
                                                        </div>
                                                    </div>
                                                </div>
                                            </div>
                                        ))}
                                    </div>
                                )}
                            </div>
                        )}
                    </div>
                )}

                {error && (
                    <div className="bg-red-50 border border-red-200 rounded-lg p-4 text-red-700">
                        {error}
                    </div>
                )}

                {!response && !error && !loading && (
                    <div className="text-center text-gray-500 py-12">
                        <Database className="w-12 h-12 mx-auto mb-3 text-gray-400" />
                        <p>Ask a question about your documents</p>
                        <p className="text-sm mt-1">
                            The AI will search the knowledge base and provide context-aware answers
                        </p>
                    </div>
                )}
            </div>

            {/* Input */}
            <div className="border-t border-gray-200 p-4 bg-white">
                <form onSubmit={handleSubmit} className="flex gap-2">
                    <input
                        type="text"
                        value={question}
                        onChange={(e) => setQuestion(e.target.value)}
                        placeholder="Ask a question about your documents..."
                        disabled={loading}
                        className="flex-1 input"
                    />
                    <button
                        type="submit"
                        disabled={loading || !question.trim()}
                        className="btn btn-primary flex items-center gap-2"
                    >
                        {loading ? (
                            <>
                                <div className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin" />
                                Searching...
                            </>
                        ) : (
                            <>
                                <Send className="w-4 h-4" />
                                Ask
                            </>
                        )}
                    </button>
                </form>
            </div>
        </div>
    );
};