/**
 * Chat input component with send button
 */

import { Check, ChevronUp, Cpu, Database, Plus, Send } from 'lucide-react';
import React, { type KeyboardEvent, useEffect, useRef, useState } from 'react';
import { useRagStore } from '../store/useRagStore';
import { useStore } from '../store/useStore';
import { ProviderSelector } from './ProviderSelector';

interface ChatInputProps {
    onSend: (message: string) => void;
    disabled?: boolean;
    placeholder?: string;
}

export const ChatInput: React.FC<ChatInputProps> = ({
    onSend,
    disabled = false,
    placeholder = 'Type your message...'
}) => {
    const [input, setInput] = useState('');
    const textareaRef = useRef<HTMLTextAreaElement>(null);
    const [showModelPicker, setShowModelPicker] = useState(false);
    const { settings, updateSettings } = useStore();
    const [showRagPicker, setShowRagPicker] = useState(false);
    const { collections, selectedCollection, setSelectedCollection, fetchCollections } = useRagStore();

    // Auto-resize textarea
    useEffect(() => {
        if (textareaRef.current) {
            textareaRef.current.style.height = 'auto';
            textareaRef.current.style.height = `${Math.min(textareaRef.current.scrollHeight, 200)}px`; // Set a maximum height of 200px
        }
    }, [input]);

    const handleSend = () => {
        if (input.trim() && !disabled) {
            onSend(input);
            setInput('');
        }
    };

    const handleKeyDown = (e: KeyboardEvent<HTMLTextAreaElement>) => {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            handleSend();
        }
    };

    const toggleRagPicker = () => {
        if (!showRagPicker && collections.length === 0) fetchCollections();
        setShowRagPicker(!showRagPicker);
    };

    return (
        <div className="p-4 bg-gradient-to-t from-background via-background to-transparent">
            <div className="border rounded-xl bg-card shadow-lg focus-within:ring-2 focus-within:ring-primary/20 transition-all">

                {/* Textarea Area */}
                <textarea
                    ref={textareaRef}
                    value={input}
                    onChange={(e) => setInput(e.target.value)}
                    placeholder={placeholder}
                    onKeyDown={handleKeyDown}
                    disabled={disabled}
                    rows={2}
                    className="w-full p-4 bg-transparent resize-none outline-none border-none custom-scrollbar min-h-[10px] overflow-y-auto"
                />

                {/* Bottom Action Bar */}
                <div className="flex items-center justify-between px-4 py-2 border-t bg-muted/30">

                    <div className="flex items-center gap-1 relative">
                        {/* Collection Popover */}
                        {showRagPicker && (
                            <>
                                <div className="fixed inset-0 z-10" onClick={() => setShowRagPicker(false)} />
                                <div className="absolute bottom-full left-0 mb-3 w-64 bg-white dark:bg-gray-900 border border-gray-200 dark:border-gray-800 rounded-xl shadow-2xl z-20 p-2 animate-in fade-in zoom-in-95">
                                    <div className="px-3 py-2 border-b border-gray-100 dark:border-gray-800 mb-1">
                                        <span className="text-[10px] font-bold uppercase tracking-widest text-gray-400">RAG Knowledge Base</span>
                                    </div>

                                    <div className="max-h-48 overflow-y-auto">
                                        <button
                                            onClick={() => { setSelectedCollection(null); setShowRagPicker(false); }}
                                            className={`w-full text-left px-3 py-2 rounded-lg text-sm mb-1 ${!selectedCollection ? 'bg-primary-50 text-primary-600' : 'hover:bg-gray-100 text-gray-700'}`}
                                        >
                                            None (Standard Chat)
                                        </button>

                                        {collections.map((name) => (
                                            <button
                                                key={name}
                                                onClick={() => {
                                                    setSelectedCollection(name);
                                                    setShowRagPicker(false);
                                                }}
                                                className={`w-full flex items-center justify-between px-3 py-2 rounded-lg text-sm transition-colors ${selectedCollection === name
                                                    ? 'bg-primary-50 dark:bg-primary-900/30 text-primary-600'
                                                    : 'hover:bg-gray-100 dark:hover:bg-gray-800 text-gray-700 dark:text-gray-300'
                                                    }`}
                                            >
                                                <span className="truncate">{name}</span>
                                                {selectedCollection === name && <Check className="w-3.5 h-3.5" />}
                                            </button>
                                        ))}
                                    </div>
                                </div>
                            </>
                        )}

                        <button
                            onClick={toggleRagPicker}
                            className={`p-2 rounded-lg transition-colors ${selectedCollection ? 'text-primary-500 bg-primary-50' : 'text-gray-500 hover:bg-gray-200'}`}
                        >
                            <Plus className={`w-5 h-5 transition-transform ${showRagPicker ? 'rotate-45' : ''}`} />
                        </button>

                        {selectedCollection && (
                            <div className="flex items-center gap-2 px-2 py-1 text-xs font-medium text-primary-600 bg-primary-50 dark:bg-primary-900/20 rounded-md">
                                <Database className="w-3.5 h-3.5" />
                                <span className="max-w-[100px] truncate">{selectedCollection}</span>
                            </div>
                        )}
                    </div>

                    {/* Right Side: Model Selector & Send */}
                    <div className="flex items-center gap-3">
                        {/* Model Dropdown (Simplified implementation) */}
                        <div className="relative group">
                            {/* Model Selector Popover */}
                            {showModelPicker && (
                                <>
                                    <div className="fixed inset-0 z-10" onClick={() => setShowModelPicker(false)} />
                                    <div className="absolute bottom-full right-0 mb-2 w-72 p-4 bg-white dark:bg-gray-900 border border-gray-200 dark:border-gray-800 rounded-xl shadow-2xl z-20 animate-in fade-in slide-in-from-bottom-2">
                                        <div className="flex items-center gap-2 mb-3 text-gray-500">
                                            <Cpu className="w-4 h-4" />
                                            <span className="text-[10px] font-bold uppercase tracking-widest">Switch Model</span>
                                        </div>
                                        <ProviderSelector
                                            variant="list"
                                            selectedProvider={settings.provider}
                                            selectedModel={settings.model}
                                            onProviderChange={(p) => updateSettings({ provider: p })}
                                            onModelChange={(m) => {
                                                updateSettings({ model: m });
                                                setShowModelPicker(false); // Close menu after selection
                                            }}
                                        />
                                    </div>
                                </>
                            )}

                            <button
                                onClick={() => setShowModelPicker(!showModelPicker)}
                                className="flex items-center gap-2 px-3 py-1.5 text-xs font-semibold border border-gray-200 dark:border-gray-700 rounded-lg bg-white dark:bg-gray-800 text-gray-700 dark:text-gray-300 hover:border-primary-500 transition-all"
                            >
                                <Cpu className="w-3.5 h-3.5 text-primary-500" />
                                <span className="max-w-[100px] truncate">{settings.model}</span>
                                <ChevronUp className={`w-3 h-3 transition-transform ${showModelPicker ? 'rotate-180' : ''}`} />
                            </button>
                        </div>

                        {/* Minimal Send Icon */}
                        <button
                            onClick={handleSend}
                            disabled={disabled || !input.trim()}
                            className="p-2 rounded-full bg-primary text-primary-foreground hover:opacity-90 disabled:opacity-30 disabled:grayscale transition-all"
                        >
                            <Send className="w-5 h-5 fill-current" />
                        </button>
                    </div>
                </div>
            </div>
            <div className="text-xs mt-2">
                Press Enter to send, Shift + Enter for new line
            </div>
        </div>
    );
};